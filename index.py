import random
import telebot
from telebot import types
import psycopg2
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
import re
from dotenv import load_dotenv
from datetime import datetime

# Загружаем переменные из .env
load_dotenv()

# Telegram Bot Token из .env
telegram_key = os.getenv("telegram_key")

# Подключение к базе данных PostgreSQL
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "restaurant")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "ZX060688")

conn = psycopg2.connect(
    dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST
)
cursor = conn.cursor()

print(f"Подключение к базе выполнено") # отладочное сообщение

# Создание таблицы бронирований, если ее нет
cursor.execute('''
    CREATE TABLE IF NOT EXISTS reservations (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        date DATE,
        time TIME,
        guests INTEGER,
        name TEXT,
        surname TEXT,
        phone INTEGER
    )
''')
conn.commit()

# Инициализация бота
bot = telebot.TeleBot(telegram_key)

# Загружаем сервисный аккаунт
SERVICE_ACCOUNT_FILE = "E:/nodejs_project/RestorauntChat_Bot/credentials.json"  # Укажи путь к своему JSON-файлу
SCOPES = ["https://www.googleapis.com/auth/calendar"]

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

# Подключаем Google Calendar API
service = build("calendar", "v3", credentials=credentials)

# ID календаря, куда будем добавлять бронирования (из Google Calendar)
CALENDAR_ID = "25638c3e183fb6eb5d35b39fdbe87d60fb6566092590f6c4a9e7737566eb3fd1@group.calendar.google.com"

def add_booking_to_calendar(user_data):
    """Добавляет бронирование в Google Календарь."""
    event = {
        "summary": f"Бронирование столика для {user_data['guests']} чел.",
        "description": f"Имя: {user_data['name']} {user_data['surname']}, Тел: {user_data['phone']}",
        "start": {"dateTime": f"{user_data['date']}T{user_data['time']}:00", "timeZone": "Europe/Moscow"},
        "end": {"dateTime": f"{user_data['date']}T{user_data['time']}:30", "timeZone": "Europe/Moscow"},
    }

    event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    print(f"✅ Бронирование добавлено: {event.get('htmlLink')}")

def hello(message):
    """Отправляет приветственное сообщение с именем пользователя."""
    user_first_name = message.from_user.first_name or ""
    user_last_name = message.from_user.last_name or ""
    
    full_name = f"{user_first_name} {user_last_name}".strip()  # Убираем лишние пробелы, если нет фамилии

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Смотреть меню ресторана')
    btn2 = types.KeyboardButton('Резервация Столика')
    btn3 = types.KeyboardButton('Акции и Предложения')
    btn4 = types.KeyboardButton('Актуальные Резервации')
    btn5 = types.KeyboardButton('Отмена Бронирования')

    keyboard.add(btn1)  # Каждая кнопка в новом ряду
    keyboard.add(btn2)
    keyboard.add(btn3)
    keyboard.add(btn4)
    keyboard.add(btn5)
    
    
    welcome_message = f"{full_name}, ресторан 'Красная Звезда' приветствует Вас. Выберите желаемое действие:"
    
    bot.send_message(message.chat.id, welcome_message, reply_markup=keyboard)

@bot.message_handler(commands=['start'])
def handle_start(message):
    hello(message)


@bot.message_handler(func=lambda message: message.text in ['Смотреть меню ресторана',
                                                           'Резервация Столика',
                                                           'Акции и Предложения',
                                                           'Актуальные Резервации',
                                                           'Отмена Бронирования'])
def on_click(message):
    if message.text == 'Смотреть меню ресторана':
        menu_photos = ["E:/nodejs_project/RestorauntChat_Bot/Menu/main.jpg",
                       "E:/nodejs_project/RestorauntChat_Bot/Menu/salat.jpg",
                       "E:/nodejs_project/RestorauntChat_Bot/Menu/desert.jpg"]  # Пути к картинкам меню
        random.shuffle(menu_photos)
        bot.send_photo(message.chat.id, open(menu_photos[0], "rb"))
    
    elif message.text == 'Резервация Столика':
        bot.send_message(message.chat.id, 'Введите дату бронирования (ГГГГ-ММ-ДД):')
        bot.register_next_step_handler(message, get_date)
    
    elif message.text == 'Акции и Предложения':
        specials(message)        
    
    elif message.text == 'Актуальные Резервации':
        cursor.execute("SELECT date, time, guests, name FROM reservations WHERE user_id=%s", (message.chat.id,))
        reservations = cursor.fetchall()
        if reservations:
            response = "Ваши текущие бронирования:\n"
            for res in reservations:
                response += f"📅 {res[0]}, ⏰ {res[1]}, 👥 {res[2]} чел., Имя: {res[3]}\n"
            bot.send_message(message.chat.id, response)
        else:
            bot.send_message(message.chat.id, "У вас пока нет активных бронирований.")
    elif message.text == 'Отмена Бронирования':
        bot.send_message(message.chat.id, 'Введите номер резервации:')
        bot.register_next_step_handler(message, process_cancellation)

# Обработчики для сбора данных о бронировании
def get_date(message):
    user_data = {"user_id": message.chat.id, "date": message.text}

    # Проверка корректности формата даты и сравнение с текущей датой
    try:
        input_date = datetime.strptime(user_data["date"], '%Y-%m-%d').date()
        today = datetime.today().date()

        if input_date < today:
            bot.send_message(message.chat.id, "Вы не можете забронировать столик на прошедшую дату. Введите дату в формате ГГГГ-ММ-ДД (не ранее сегодняшнего дня):")
            bot.register_next_step_handler(message, get_date)
            return

    except ValueError:
        bot.send_message(message.chat.id, "Некорректный формат даты. Введите дату в формате ГГГГ-ММ-ДД:")
        bot.register_next_step_handler(message, get_date)
        return

    bot.send_message(message.chat.id, 'Введите время бронирования (ЧЧ:ММ):')
    bot.register_next_step_handler(message, get_time, user_data)

def get_time(message, user_data):
    time_pattern = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")  # Формат ЧЧ:ММ (например, 13:20)
    if not time_pattern.match(message.text):
        bot.send_message(message.chat.id, "⏰ Введите корректное время в формате ЧЧ:ММ (например, 13:20):")
        bot.register_next_step_handler(message, get_time, user_data)
        return
    
    user_data["time"] = message.text
    bot.send_message(message.chat.id, 'Введите количество гостей:')
    bot.register_next_step_handler(message, get_guests, user_data)


def get_guests(message, user_data):
    # Проверяем, что введённое значение состоит только из цифр
    if not message.text.isdigit():
        bot.send_message(message.chat.id, "Пожалуйста, введите корректное число гостей (только цифры):")
        bot.register_next_step_handler(message, get_guests, user_data)
        return
    user_data["guests"] = int(message.text)
    bot.send_message(message.chat.id, 'Введите ваше имя:')
    bot.register_next_step_handler(message, get_name, user_data)

def get_name(message, user_data):
    user_data["name"] = message.text
    bot.send_message(message.chat.id, 'Введите вашу фамилию:')
    bot.register_next_step_handler(message, get_surname, user_data)

def get_surname(message, user_data):
    user_data["surname"] = message.text
    bot.send_message(message.chat.id, 'Введите телефон для связи:')
    bot.register_next_step_handler(message, save_reservation, user_data)

def get_guests(message, user_data):
    # Проверяем, что введённое значение состоит только из цифр
    if not message.text.isdigit():
        bot.send_message(message.chat.id, "Пожалуйста, введите корректное число гостей (только цифры):")
        bot.register_next_step_handler(message, get_guests, user_data)
        return
    user_data["guests"] = int(message.text)
    bot.send_message(message.chat.id, 'Введите ваше имя:')
    bot.register_next_step_handler(message, get_name, user_data)

def save_reservation(message, user_data):
    if not message.text.isdigit():
        bot.send_message(message.chat.id, "Введите корректный телефон. Только цифры")
        bot.register_next_step_handler(message, save_reservation, user_data)
        return
    user_data["phone"] = int(message.text)
    
    try:
        # Проверяем доступность столиков
        if not is_reservation_available(user_data["date"], user_data["time"]):
            bot.send_message(message.chat.id, "Все столики заняты на выбранное время. Выберите другое.")
            return

        # Сохраняем бронирование и получаем ID записи
        cursor.execute(
            "INSERT INTO reservations (user_id, date, time, guests, name, surname, phone) "
            "VALUES (%s, %s, %s::TIME, %s, %s, %s, %s) RETURNING id",
            (user_data["user_id"], user_data["date"], user_data["time"], user_data["guests"], 
             user_data["name"], user_data["surname"], user_data["phone"])
        )
        reservation_id = cursor.fetchone()  # Получаем ID вставленной брони
        
        if reservation_id:
            conn.commit()

            # Добавляем в Google Календарь
            add_booking_to_calendar(user_data)
            
            bot.send_message(
                message.chat.id,
                f"✅ Ваш столик забронирован! Спасибо! Ваш номер резервации: {reservation_id[0]}"
            )
        else:
            bot.send_message(message.chat.id, "⚠ Ошибка: не удалось получить номер брони.")

    except Exception as e:
        conn.rollback()  # ОТМЕНЯЕМ транзакцию при ошибке
        bot.send_message(message.chat.id, f"❌ Ошибка при бронировании: {e}")




def is_reservation_available(date, time):
    """Проверяет, есть ли свободные столики на выбранное время."""
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM reservations 
            WHERE date = %s 
            AND time BETWEEN %s AND (%s::TIME + INTERVAL '30 minutes')
        """, (date, time, time))
        
        count = cursor.fetchone()[0]
        return count < 10  # В ресторане 10 столиков

    except Exception as e:
        conn.rollback()  # ОТМЕНЯЕМ транзакцию при ошибке
        print(f"Ошибка при проверке доступности бронирования: {e}")
        return False

def process_cancellation(message):
    reservation_id = message.text.strip()
    
    if not reservation_id.isdigit():
        bot.send_message(message.chat.id, "Ошибка: номер брони должен быть числом. Попробуйте ещё раз.")
        return

    reservation_id = int(reservation_id)

    # Получаем данные о бронировании, включая дату и время
    cursor.execute("SELECT date, time FROM reservations WHERE id = %s AND user_id = %s", 
                   (reservation_id, message.chat.id))
    reservation = cursor.fetchone()

    if not reservation:
        bot.send_message(message.chat.id, "Ошибка: бронирование с таким номером не найдено.")
        return

    date, time = reservation

    # Удаляем из базы данных
    cursor.execute("DELETE FROM reservations WHERE id = %s AND user_id = %s", 
                   (reservation_id, message.chat.id))
    conn.commit()

    # Удаляем из Google Календаря
    delete_booking_from_calendar(date, time)

    bot.send_message(message.chat.id, f"✅ Бронирование №{reservation_id} успешно отменено.")

def delete_booking_from_calendar(date, time):
    """Удаляет бронирование из Google Календаря."""
    events_result = service.events().list(calendarId=CALENDAR_ID, q=str(date), singleEvents=True).execute()
    events = events_result.get("items", [])

    for event in events:
        event_start = event.get("start", {}).get("dateTime", "")
        if event_start.startswith(f"{date}T{time}"):
            service.events().delete(calendarId=CALENDAR_ID, eventId=event["id"]).execute()
            print(f"✅ Бронирование {event['summary']} удалено из Google Календаря")
            break


def specials(message):
    """Обработчик раздела акций и предложений."""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Дневной бонус')        
    btn2 = types.KeyboardButton('Персональный бонус')
    btn3 = types.KeyboardButton('Получить Персональный бонус')
    btn4 = types.KeyboardButton('Назад в главное меню')
    
    keyboard.add(btn1)  # Каждая кнопка в новом ряду
    keyboard.add(btn2)
    keyboard.add(btn3)
    keyboard.add(btn4)
    
    bot.send_message(message.chat.id, "Выберите предложение:", reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text in [
 'Дневной бонус',
 'Персональный бонус', 
 'Получить Персональный бонус', 
 'Назад в главное меню'])
def day_offer(message):
    if message.text == 'Дневной бонус':
        special_photo = "E:/nodejs_project/RestorauntChat_Bot/Menu/akcii.png"
        try:
            with open(special_photo, "rb") as photo:
                bot.send_photo(message.chat.id, photo)
        except FileNotFoundError:
            bot.send_message(message.chat.id, "Ошибка: файл с акциями не найден.")
    elif message.text == 'Персональный бонус':
        get_personal_bonus(message)
    elif message.text == 'Получить Персональный бонус':
        bot.send_message(message.chat.id, "Чтобы получить персональный бонус необходимо забронировать столик. Скидка на последующее бронирование 10%")
    elif message.text == 'Назад в главное меню':
        hello(message)        

def get_personal_bonus(message):
    # Подсчитываем количество бронирований для данного пользователя
    cursor.execute("SELECT COUNT(*) FROM reservations WHERE user_id = %s", (message.chat.id,))
    result = cursor.fetchone()
    reservation_count = result[0] if result is not None else 0

    if reservation_count == 0:
        bot.send_message(message.chat.id, "У вас пока нет бронирований. Забронируйте столик, чтобы получить персональную скидку!")
    elif reservation_count < 3:
        bot.send_message(message.chat.id, f"Поздравляем! После первого бронирования вы получаете скидку 10%. Ваше текущее количество бронирований: {reservation_count}.")
    else:
        bot.send_message(message.chat.id, f"Поздравляем! После третьего бронирования ваша скидка составляет 15%. Ваше текущее количество бронирований: {reservation_count}.")

print(f"Работаю на износ") # отладочное сообщение

bot.polling(none_stop=True)

