# 🍽️ Telegram Restaurant Chatbot

A Telegram bot with integrated web interface for booking tables in a restaurant. Includes Google Calendar integration, PostgreSQL database, and Docker support.

---

## 📌 Features

- 📅 Table reservation via Telegram and Flask WebApp
- 🗓️ Google Calendar sync for storing reservations
- 🧾 HTML/CSS interface for menu and booking
- 🛠️ Admin-side reservation management via `server.py`
- 🧩 Modular architecture with separation between WebApp and core logic
- 🐳 Docker & docker-compose for deployment

---

## 🛠️ Tech Stack

- **Language & Frameworks:** Python, Flask
- **Bot Platform:** Telegram Bot API
- **Database:** PostgreSQL
- **API:** Google Calendar API
- **Frontend:** HTML, JavaScript (in `/static`)
- **Containerization:** Docker, Docker Compose

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Alex-Likurg/restaurant-chatbot.git
cd restaurant-chatbot

### 2. Set up environment variables

Create a .env file based on the example:

BOT_TOKEN=your_telegram_token
GOOGLE_PROJECT_ID=your_project_id
GOOGLE_CREDENTIALS_JSON=credentials.json
DATABASE_URL=postgresql://user:password@db:5432/restaurant

Also, place your credentials.json file for Google API access in the root directory.

### 3. Run the bot locally

python webApp.py

### 4. Run with Docker

docker-compose up --build

## 📁 Project Structure

restaurant-chatbot/
├── telegram-bot/            # Bot logic
│   └── webApp.py            # Flask app entry point
├── server.py                # Server-side reservation logic
├── static/                  # HTML, JS, CSS
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md

## 📝 License

This project is licensed under the MIT License.
