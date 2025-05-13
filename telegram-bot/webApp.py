import os
import telebot
from telebot import types
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Инициализация бота
telegram_key = os.getenv("telegram_key")
bot = telebot.TeleBot(telegram_key)

# Загружаем переменные окружения
load_dotenv()

# Инициализация бота
telegram_key = os.getenv("telegram_key")
bot = telebot.TeleBot(telegram_key)


@bot.message_handler(commands=["start"])
def handle_start(message):
    """Отправляет кнопки в один столбец без текста"""
    keyboard = types.InlineKeyboardMarkup()

    # Создаём кнопки
    buttons = [
        ("📲 Забронировать столик", "https://krasnayazvezda.store/"),
        ("🔥 Открыть акции", "https://krasnayazvezda.store/specials"),
        ("📋 Актуальные резервации", "https://krasnayazvezda.store/reservations"),
        ("❌ Удалить бронирование", "https://krasnayazvezda.store/delete"),
        ("🍽 Смотреть меню", "https://krasnayazvezda.store/menu"),
    ]

    # Добавляем кнопки по одной в строке
    for text, url in buttons:
        keyboard.add(types.InlineKeyboardButton(text, web_app=types.WebAppInfo(url=url)))

    # Отправляем кнопки без текста
    bot.send_message(message.chat.id, "Выберете желаемое действие:", reply_markup=keyboard)


print("✅ Бот запущен")

# Запускаем бота
bot.polling(none_stop=True)



