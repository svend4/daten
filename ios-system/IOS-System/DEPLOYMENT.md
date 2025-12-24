# 🚀 Деплой IOS System на Render.com

Полное руководство по развёртыванию IOS System на платформе Render.com с использованием Docker.

## 📋 Содержание

1. [Предварительные требования](#предварительные-требования)
2. [Подготовка к деплою](#подготовка-к-деплою)
3. [Деплой через Blueprint](#деплой-через-blueprint)
4. [Ручной деплой](#ручной-деплой)
5. [Настройка переменных окружения](#настройка-переменных-окружения)
6. [Мониторинг и логи](#мониторинг-и-логи)
7. [Troubleshooting](#troubleshooting)

---

## Предварительные требования

- Аккаунт на [Render.com](https://render.com)
- Git репозиторий с кодом проекта
- Базовое понимание Docker и Git

## Подготовка к деплою

### 1. Структура проекта

Убедитесь, что в корне проекта есть:

```
IOS-System/
├── render.yaml                    # Blueprint конфигурация
├── Dockerfile.production          # Backend Dockerfile
├── docker-compose.yml            # Для локальной разработки
├── .dockerignore                 # Backend игнор-файл
├── frontend/
│   ├── Dockerfile                # Frontend Dockerfile
│   ├── nginx.conf               # Nginx конфигурация
│   └── .dockerignore            # Frontend игнор-файл
├── main_production.py           # Точка входа для FastAPI
└── requirements.txt             # Python зависимости
```

### 2. Проверка конфигураций

**Backend Dockerfile** (`Dockerfile.production`):
- Multi-stage build для оптимизации
- Python 3.11
- Non-root пользователь
- Health check

**Frontend Dockerfile** (`frontend/Dockerfile`):
- Node 18 для сборки
- Nginx Alpine для production
- Оптимизация кэширования

### 3. Создание requirements файлов

Убедитесь, что все зависимости указаны:

```bash
# requirements.txt
pip freeze > requirements.txt

# requirements-db.txt (для PostgreSQL)
psycopg2-binary==2.9.9
sqlalchemy==2.0.23
alembic==1.13.1
```

---

## Деплой через Blueprint

### Автоматический деплой (рекомендуется)

1. **Коммит и пуш кода**:
   ```bash
   git add .
   git commit -m "Add Render deployment configuration"
   git push origin main
   ```

2. **Создание Blueprint на Render**:
   - Зайдите на [dashboard.render.com](https://dashboard.render.com)
   - Нажмите **"New"** → **"Blueprint"**
   - Подключите ваш Git репозиторий
   - Render автоматически обнаружит `render.yaml`

3. **Настройка Blueprint**:
   - Укажите название группы сервисов: `ios-system`
   - Выберите регион: **Frankfurt** (EU)
   - Нажмите **"Apply"**

4. **Ожидание деплоя**:
   - Render создаст все сервисы из `render.yaml`:
     - PostgreSQL база данных
     - Redis кэш
     - Backend API
     - Frontend приложение

5. **Проверка**:
   - Frontend: `https://ios-system-frontend.onrender.com`
   - Backend API: `https://ios-system-backend.onrender.com/docs`

---

## Ручной деплой

### 1. Создание базы данных

1. Dashboard → **"New"** → **"PostgreSQL"**
2. Настройки:
   - Name: `ios-system-db`
   - Database: `ios_db`
   - User: `ios_user`
   - Region: Frankfurt
   - Plan: Starter (Free)
3. Нажмите **"Create Database"**
4. Скопируйте **Internal Database URL**

### 2. Создание Redis

1. Dashboard → **"New"** → **"Redis"**
2. Настройки:
   - Name: `ios-system-redis`
   - Region: Frankfurt
   - Plan: Starter (Free)
   - Max Memory Policy: `allkeys-lru`
3. Нажмите **"Create Redis"**

### 3. Деплой Backend

1. Dashboard → **"New"** → **"Web Service"**
2. Подключите Git репозиторий
3. Настройки:
   - Name: `ios-system-backend`
   - Environment: **Docker**
   - Region: Frankfurt
   - Branch: `main`
   - Dockerfile Path: `./Dockerfile.production`
   - Docker Context: `./`

4. **Переменные окружения**:
   ```
   ENVIRONMENT=production
   PORT=8000
   WORKERS=4
   DATABASE_URL=[Internal Database URL from step 1]
   REDIS_URL=[Redis Connection String from step 2]
   SECRET_KEY=[Сгенерировать случайный ключ]
   CORS_ORIGINS=https://ios-system-frontend.onrender.com
   LOG_LEVEL=INFO
   ```

5. **Advanced Settings**:
   - Health Check Path: `/health`
   - Auto-Deploy: Yes

6. Нажмите **"Create Web Service"**

### 4. Деплой Frontend

1. Dashboard → **"New"** → **"Web Service"**
2. Подключите Git репозиторий
3. Настройки:
   - Name: `ios-system-frontend`
   - Environment: **Docker**
   - Region: Frankfurt
   - Branch: `main`
   - Dockerfile Path: `./frontend/Dockerfile`
   - Docker Context: `./frontend`

4. **Переменные окружения**:
   ```
   NODE_ENV=production
   VITE_API_URL=https://ios-system-backend.onrender.com
   ```

5. Нажмите **"Create Web Service"**

---

## Настройка переменных окружения

### Backend переменные

| Переменная | Описание | Пример |
|-----------|----------|--------|
| `ENVIRONMENT` | Окружение | `production` |
| `PORT` | Порт сервера | `8000` |
| `WORKERS` | Количество workers | `4` |
| `DATABASE_URL` | PostgreSQL URL | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL` | Redis URL | `redis://host:6379/0` |
| `SECRET_KEY` | Секретный ключ | Случайная строка 32+ символов |
| `CORS_ORIGINS` | Разрешённые origins | `https://example.com` |
| `LOG_LEVEL` | Уровень логирования | `INFO`, `DEBUG`, `WARNING` |

### Frontend переменные

| Переменная | Описание | Пример |
|-----------|----------|--------|
| `NODE_ENV` | Node окружение | `production` |
| `VITE_API_URL` | Backend API URL | `https://backend.onrender.com` |

### Генерация SECRET_KEY

```python
import secrets
print(secrets.token_urlsafe(32))
```

или

```bash
openssl rand -base64 32
```

---

## Мониторинг и логи

### Просмотр логов

1. Зайдите в сервис на Render Dashboard
2. Вкладка **"Logs"**
3. Фильтры:
   - Live logs (реальное время)
   - Historical logs (история)

### Метрики

1. Вкладка **"Metrics"**
2. Доступно:
   - CPU usage
   - Memory usage
   - Request count
   - Response time

### Health Checks

Backend health check: `GET /health`

Ответ:
```json
{
  "status": "healthy",
  "timestamp": "2024-12-16T10:00:00Z"
}
```

---

## Локальная разработка с Docker

### Запуск всех сервисов

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down

# Остановка с удалением volumes
docker-compose down -v
```

### Только база данных и Redis

```bash
docker-compose up -d postgres redis
```

### Frontend разработка

```bash
cd frontend
npm install
npm run dev
```

Backend разработка через uvicorn:

```bash
uvicorn main_production:app --reload --host 0.0.0.0 --port 8000
```

---

## Troubleshooting

### Проблема: Build fails - "No such file or directory"

**Решение**: Проверьте пути в Dockerfile и убедитесь, что все файлы существуют.

```bash
# Проверка структуры
tree -L 2 -I 'node_modules|__pycache__|.git'
```

### Проблема: Backend не подключается к базе

**Решение**:
1. Проверьте DATABASE_URL
2. Используйте **Internal Database URL** (не External)
3. Убедитесь, что база создана

### Проблема: CORS ошибки

**Решение**: Добавьте frontend URL в CORS_ORIGINS:

```python
CORS_ORIGINS="https://ios-system-frontend.onrender.com,https://custom-domain.com"
```

### Проблема: Frontend не может достучаться до API

**Решение**: Проверьте VITE_API_URL в frontend переменных окружения.

### Проблема: Out of memory

**Решение**:
1. Увеличьте план на Render (Starter → Standard)
2. Оптимизируйте Dockerfile (multi-stage build)
3. Уменьшите количество workers

### Проблема: Slow builds

**Решение**:
1. Используйте `.dockerignore` для исключения ненужных файлов
2. Кэшируйте зависимости в Dockerfile
3. Используйте multi-stage builds

---

## Дополнительные настройки

### Custom Domain

1. Зайдите в сервис → **"Settings"** → **"Custom Domains"**
2. Добавьте ваш домен
3. Настройте DNS записи:
   - Frontend: `CNAME` → `ios-system-frontend.onrender.com`
   - Backend: `CNAME` → `ios-system-backend.onrender.com`

### SSL/TLS

Render автоматически предоставляет SSL сертификаты от Let's Encrypt.

### Environment Groups

Создайте Environment Group для переиспользования переменных:
1. Dashboard → **"Environment Groups"**
2. **"New Environment Group"**
3. Добавьте переменные
4. Подключите к сервисам

---

## Полезные ссылки

- [Render Documentation](https://render.com/docs)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Vite Production Build](https://vitejs.dev/guide/build.html)

---

## Поддержка

При возникновении проблем:
1. Проверьте логи на Render Dashboard
2. Изучите документацию Render
3. Создайте issue в репозитории проекта

---

**Автор**: IOS System Team
**Последнее обновление**: Декабрь 2024
