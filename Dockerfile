FROM python:3.8-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование проекта
COPY insecure/ /app/insecure/

WORKDIR /app/insecure

# Создание миграций и применение их
RUN python manage.py makemigrations
RUN python manage.py migrate

# Открытие порта
EXPOSE 8000

# Запуск сервера
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

