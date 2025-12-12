FROM python:3.8-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование проекта
COPY insecure/ /app/insecure/
WORKDIR /app/insecure

# Создаём непривилегированного пользователя
RUN useradd --system --user-group --no-log-init appuser \
    && chown -R appuser:appuser /app

# Создание миграций и применение их
RUN python manage.py makemigrations
RUN python manage.py migrate

# Непривилегированный запуск
USER appuser
# Открытие порта
EXPOSE 8000

# HEALTHCHECK
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/ || exit 1

# Запуск сервера
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]