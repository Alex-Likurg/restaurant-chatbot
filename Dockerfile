# Используем официальный Python
FROM python:3.13-slim

# Устанавливаем зависимости
WORKDIR /app
COPY requirements.txt ./
COPY credentials.json ./
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы проекта
COPY . .

# Порт для Flask
EXPOSE 5000

# Запуск Flask
CMD ["python", "server.py"]
