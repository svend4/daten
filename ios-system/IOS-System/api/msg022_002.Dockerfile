# Dockerfile
# Dockerfile для IOS API сервера

FROM python:3.11-slim

# Установить системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копировать requirements
COPY requirements.txt .

# Установить Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копировать код приложения
COPY . .

# Создать директории для данных
RUN mkdir -p /data/ios-root \
    /data/uploads \
    /data/exports

# Переменные окружения
ENV IOS_ROOT_PATH=/data/ios-root \
    PYTHONUNBUFFERED=1 \
    SECRET_KEY=change-this-in-production

# Открыть порт
EXPOSE 8000

# Команда запуска
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]