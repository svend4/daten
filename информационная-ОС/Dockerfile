# Dockerfile для IOS System
# Использует существующий код из IOS-System/

FROM python:3.11-slim

# Системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копировать requirements
COPY requirements.txt .

# Установить Python зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копировать код
COPY IOS-System/ /app/IOS-System/
COPY ios_bootstrap/ /app/ios_bootstrap/

# Создать директории для данных
RUN mkdir -p /data/ios-root \
    /data/uploads \
    /data/exports \
    /data/whoosh-index

# Переменные окружения
ENV PYTHONPATH=/app:$PYTHONPATH \
    PYTHONUNBUFFERED=1 \
    IOS_ROOT_PATH=/data/ios-root

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Открыть порт
EXPOSE 8000

# Команда запуска
CMD ["uvicorn", "ios_bootstrap.main:app", "--host", "0.0.0.0", "--port", "8000"]
