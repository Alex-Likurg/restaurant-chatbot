from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import random
import os
import psycopg2
import telebot
from dotenv import load_dotenv
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
import re  # Добавили для работы с телефоном

# Загружаем переменные окружения
load_dotenv()

# Настройки бота
telegram_key = os.getenv("telegram_key")
bot = telebot.TeleBot(telegram_key)

# Подключение к PostgreSQL
DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "restaurant")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "ZX060688")

conn = psycopg2.connect(
    dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST
)
cursor = conn.cursor()

# Загружаем сервисный аккаунт
SERVICE_ACCOUNT_FILE = "credentials.json"  # Укажи путь к своему JSON-файлу
SCOPES = ["https://www.googleapis.com/auth/calendar"]

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

# Подключаем Google Calendar API
service = build("calendar", "v3", credentials=credentials)

# ID календаря, куда будем добавлять бронирования (из Google Calendar)
CALENDAR_ID = "25638c3e183fb6eb5d35b39fdbe87d60fb6566092590f6c4a9e7737566eb3fd1@group.calendar.google.com"

# Функция очистки телефона

def sanitize_phone(phone):
    phone = phone.strip()
    if phone.startswith("+"):
        phone = "+" + re.sub(r"\D", "", phone[1:])
    else:
        phone = re.sub(r"\D", "", phone)
    return phone

def is_valid_phone(phone):
    return re.fullmatch(r"\+?\d{5,15}", phone) is not None

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


# Инициализация Flask
app = Flask(__name__, static_folder="static")
CORS(app)

def gain_reservations(message):    
    cursor.execute("SELECT date, time, guests, name FROM reservations WHERE user_id=%s", (message.chat.id,))
    reservations = cursor.fetchall()
    if reservations:
        response = "Ваши текущие бронирования:\n"
        for res in reservations:
            response += f"📅 {res[0]}, ⏰ {res[1]}, 👥 {res[2]} чел., Имя: {res[3]}\n"
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, "У вас пока нет активных бронирований.")



@app.route("/")
def serve_index():
    return send_from_directory("static", "index.html")

@app.route("/reservations")
def serve_reservations():
    """Выдает страницу с акциями"""
    return send_from_directory("static", "reservations.html")

@app.route("/menu")
def serve_menu():
    """Выдает страницу с акциями"""
    return send_from_directory("static", "menu.html")

@app.route("/specials")
def serve_specials():
    """Выдает страницу с акциями"""
    return send_from_directory("static", "specials.html")

@app.route("/delete")
def serve_delete():
    """Выдает страницу для удаления бронирования"""
    return send_from_directory("static", "delete.html")

@app.route("/", methods=["GET"])
def home():
    return "✅ Telegram Web App API работает!"

@app.route("/api/book_table", methods=["POST"])
def book_table():
    """Обработчик бронирования столика из Web App"""
    data = request.json
    print("📩 Получены данные от Web App:", data)  # Логируем запрос

    if not data:
        print("❌ Ошибка: Данные отсутствуют!")
        return jsonify({"status": "error", "message": "Нет данных"}), 400

    # Проверяем, какие ключи пришли в JSON
    print("🔍 Ключи в запросе:", list(data.keys()))

    # Проверка наличия всех ключей
    required_keys = ["user_id", "date", "time", "guests", "name", "surname", "phone"]
    for key in required_keys:
        if key not in data:
            return jsonify({"status": "error", "message": f"Отсутствует {key}"}), 400

    try:
        raw_phone = data["phone"]
        clean_phone = sanitize_phone(raw_phone)

        if not is_valid_phone(clean_phone):
            return jsonify({"status": "error", "message": "Номер телефона должен содержать от 5 до 15 цифр."}), 400
        # ✅ Проверка на лимит гостей
        if int(data["guests"]) > 4:
            return jsonify({"status": "error", "message": "Стол рассчитан максимум на 4 человек. Уменьшите количество гостей."}), 400

        # ✅ Проверка рабочего времени
        time_obj = datetime.strptime(data["time"], "%H:%M").time()
        if not (datetime.strptime("08:00", "%H:%M").time() <= time_obj <= datetime.strptime("23:00", "%H:%M").time()):
            return jsonify({"status": "error", "message": "Ресторан работает с 08:00 до 23:00. Выберите время в этом диапазоне."}), 400

        # ✅ Проверка на доступность столиков (±20 минут от выбранного времени)
        date = data["date"]
        time = datetime.strptime(data["time"], "%H:%M")
        time_start = (time - timedelta(minutes=20)).time()
        time_end = (time + timedelta(minutes=20)).time()

        cursor.execute("""
            SELECT COUNT(*) FROM reservations
            WHERE date = %s
            AND time BETWEEN %s AND %s
        """, (date, time_start, time_end))
        count = cursor.fetchone()[0]

        if count >= 12:
            suggested_time = find_available_time(date, data["time"])
            if suggested_time:
                return jsonify({
                    "status": "error",
                    "message": f"❌ Все столики заняты на выбранное время.\n💡 Свободное ближайшее время: {suggested_time}"
                }), 400
            else:
                return jsonify({
                    "status": "error",
                    "message": "❌ Все столики заняты. Рядом нет доступного времени. Попробуйте выбрать другую дату."
                }), 400

        # ✅ Вставка в БД
        cursor.execute(
            "INSERT INTO reservations (user_id, date, time, guests, name, surname, phone) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (data["user_id"], data["date"], data["time"], data["guests"],
            data["name"], data["surname"], data["phone"])
        )

        result = cursor.fetchone()
        if result is None:
            return jsonify({"status": "error", "message": "Ошибка при бронировании (не получен ID)"}), 500
        reservation_id = result[0]


        cursor.execute("""
            SELECT COUNT(*) FROM reservations
            WHERE date = %s
            AND time BETWEEN %s AND %s
        """, (data["date"], time_start, time_end))
        updated_count = cursor.fetchone()[0]
        tables_left = max(0, 12 - updated_count)
        
        conn.commit()

        # Добавляем в календарь
        user_data = {
            "user_id": data["user_id"],
            "date": data["date"],
            "time": data["time"],
            "guests": data["guests"],
            "name": data["name"],
            "surname": data["surname"],
            "phone": clean_phone
        }
        add_booking_to_calendar(user_data)

        # Отправляем подтверждение пользователю
        
        bot.send_message(
            data["user_id"],
            f"✅ Столик забронирован!\n📅 Дата: {data['date']}\n⏰ Время: {data['time']}\n"
            f"👥 Количество гостей: {data['guests']}\n🆔 Номер резервации: {reservation_id}\n"
            f"🪑 Осталось доступных столиков в это время: {tables_left}"
        )

        return jsonify({"status": "success", "message": "Бронирование успешно добавлено!"})

    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

def find_available_time(date, preferred_time, interval=20, max_tables=12):
    """Ищет ближайшее время, где есть свободные столики (±interval мин)."""
    time_obj = datetime.strptime(preferred_time, "%H:%M")
    for minutes_offset in range(10, 121, 10):  # Проверяем в пределах ±2 часа с шагом 10 мин
        for direction in [-1, 1]:
            new_time = (time_obj + timedelta(minutes=minutes_offset * direction)).time()
            if datetime.strptime("08:00", "%H:%M").time() <= new_time <= datetime.strptime("23:00", "%H:%M").time():
                cursor.execute("""
                    SELECT COUNT(*) FROM reservations
                    WHERE date = %s
                    AND time BETWEEN %s AND %s
                """, (
                    date,
                    (datetime.combine(datetime.today(), new_time) - timedelta(minutes=interval)).time(),
                    (datetime.combine(datetime.today(), new_time) + timedelta(minutes=interval)).time()
                ))
                count = cursor.fetchone()[0]
                if count < max_tables:
                    return new_time.strftime("%H:%M")
    return None


@app.route("/api/delete_table", methods=["POST"])
def delete_reservation():
    """Удаляет бронирование по ID из базы данных"""
    data = request.json
    print("📩 Получены данные от Web App:", data)  # Логируем запрос

    if not data:
        print("❌ Ошибка: Данные отсутствуют!")
        return jsonify({"status": "error", "message": "Нет данных"}), 400

    # Проверяем, какие ключи пришли в JSON
    required_keys = ["user_id", "number"]
    for key in required_keys:
        if key not in data:
            print(f"❌ Отсутствует ключ: {key}")
            return jsonify({"status": "error", "message": f"Отсутствует {key}"}), 400

    try:
        user_id = int(data["user_id"])
        reservation_id = int(data["number"])

        # Проверяем, существует ли бронирование
        cursor.execute("SELECT date, time FROM reservations WHERE id = %s AND user_id = %s", (reservation_id, user_id))
        reservation = cursor.fetchone()

        if not reservation:
            return jsonify({"status": "error", "message": "Бронирование с таким номером не найдено"}), 404

        date, time = reservation

        # Удаляем бронирование из базы данных
        cursor.execute("DELETE FROM reservations WHERE id = %s AND user_id = %s", (reservation_id, user_id))
        conn.commit()

        # Удаляем запись из Google Календаря
        delete_booking_from_calendar(date, time)

        print(f"✅ Бронирование №{reservation_id} удалено!")
        return jsonify({"status": "success", "message": f"Бронирование №{reservation_id} успешно отменено."})

    except ValueError:
        print("❌ Ошибка: Номер бронирования или user_id должны быть числами!")
        return jsonify({"status": "error", "message": "Некорректный формат данных"}), 400

    except Exception as e:
        print("❌ Ошибка в SQL-запросе:", str(e))
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


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


@app.route("/api/get_specials", methods=["GET"])
def get_specials():
    """Возвращает список акций и предложений"""
    specials = [
        {"title": "Дневной бонус", "description": "Скидка 15% на обеденное меню с 12:00 до 15:00"},
        {"title": "Персональный бонус", "description": "10% скидка при первом бронировании"},
        {"title": "Счастливые часы", "description": "С 18:00 до 20:00 коктейли по 299₽!"},
    ]
    return jsonify(specials)

@app.route("/api/specials/day_bonus", methods=["GET"])
def day_bonus():
    """Возвращает информацию о дневном бонусе"""
    special_photo = "static/menu/akcii.png"
    
    if not os.path.exists(special_photo):
        return jsonify({"status": "error", "message": "Ошибка! Файл с акциями не найден"}), 404

    return jsonify({"status": "success", "image_url": f"/{special_photo}"})

@app.route("/api/specials/personal_bonus", methods=["POST"])
def get_personal_bonus():
    """Возвращает информацию о персональном бонусе"""
    data = request.json
    if "user_id" not in data:
        return jsonify({"status": "error", "message": "user_id отсутствует"}), 400

    cursor.execute("SELECT COUNT(*) FROM reservations WHERE user_id = %s", (data["user_id"],))
    result = cursor.fetchone()
    reservation_count = result[0] if result else 0

    if reservation_count == 0:
        message = "У вас пока нет бронирований в нашем ресторане! Скидка составляет 0%."
    elif reservation_count < 3:
        message = f"После первого бронирования вы получаете скидку 10%. Ваше текущее количество бронирований: {reservation_count}."
    else:
        message = f"После третьего бронирования скидка 15%. Ваше текущее количество бронирований: {reservation_count}."

    return jsonify({"status": "success", "message": message})



@app.route("/api/specials/back_to_menu", methods=["GET"])
def back_to_menu():
    """Возвращает пользователя в главное меню"""
    return jsonify({"status": "success", "message": "Возвращаем в главное меню..."})


@app.route("/api/get_menu", methods=["GET"])
def get_menu():
    menu_photos = [
        "static/menu/main.jpg",
        "static/menu/salat.jpg",
        "static/menu/desert.jpg"
    ]  # Пути к файлам относительно директории static

    random.shuffle(menu_photos)
    selected_photo = menu_photos[0]  # Выбираем случайное изображение

    return jsonify({"status": "success", "image_url": f"/{selected_photo}"})


@app.route("/api/get_reservations", methods=["POST"])
def get_reservations():
    """Возвращает список активных резерваций пользователя."""
    data = request.json
    if "user_id" not in data:
        return jsonify({"status": "error", "message": "user_id отсутствует"}), 400

    cursor.execute("SELECT date, time, guests, name FROM reservations WHERE user_id=%s", (data["user_id"],))
    reservations = cursor.fetchall()

    if reservations:
        reservations_list = [
            {
                "date": str(res[0]),  # Преобразуем дату в строку
                "time": res[1].strftime("%H:%M"),  # Преобразуем время в строку
                "guests": res[2],
                "name": res[3]
            }
            for res in reservations
        ]
        return jsonify({"status": "success", "reservations": reservations_list})
    else:
        return jsonify({"status": "error", "message": "Нет активных бронирований"}), 404



@app.route("/routes", methods=["GET"])
def list_routes():
    """Вывод всех доступных маршрутов Flask"""
    import urllib
    output = []
    for rule in app.url_map.iter_rules():
        methods = ",".join(rule.methods)
        line = urllib.parse.unquote(f"{rule.endpoint}: {rule.rule} ({methods})")
        output.append(line)
    return "<br>".join(output)

if __name__ == "__main__":
    print("🚀 Flask-сервер запущен на порту 5000")
    app.run(host="0.0.0.0", port=5000)


