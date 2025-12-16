# Тестирование полной архитектуры IOS System (без Bootstrap)

## 🎯 Цель

Временно отключить bootstrap-обёртку и запустить полное приложение `main_production.py` со всеми сервисами для тестирования архитектуры.

---

## 📋 Два режима работы

### Режим 1: Bootstrap (текущий, минимальный)
**Файлы:**
- `Dockerfile` - минимальный билд (frontend + bootstrap)
- `railway.json` - конфиг для bootstrap
- Запуск: `uvicorn ios_bootstrap.main:app`

**Что работает:**
- ✅ Frontend (React UI)
- ✅ Базовый API (/health, /api/status)
- ✅ Быстрый старт без зависимостей
- ❌ Whoosh search
- ❌ ML classification
- ❌ Knowledge graph

**Используется для:**
- Быстрое тестирование frontend
- Проверка деплоя на Railway
- Минимальная конфигурация

---

### Режим 2: Full Stack (тестирование архитектуры)
**Файлы:**
- `Dockerfile.fullstack` - полный билд со всеми сервисами
- `railway.fullstack.json` - конфиг для полной архитектуры
- `start_fullstack.py` - wrapper для запуска
- Запуск: `python start_fullstack.py` → `IOS_System.main_production:app`

**Что работает:**
- ✅ Frontend (React UI)
- ✅ Полный API (auth, documents, search, graph, admin, AI)
- ✅ IOSRoot, EventBus, ServiceRegistry
- ✅ DocumentService, SearchService, KnowledgeGraphService
- ✅ ClassifierService, ContextService
- ✅ Database (PostgreSQL)
- ✅ Cache (Redis)
- ✅ Middleware (error handler, rate limiter, logger)
- ✅ Monitoring (metrics, health checks)
- ⚙️ Elasticsearch (опционально, env var)
- ⚙️ ML models (опционально, env var)
- ⚙️ GPT integration (опционально, env var)

**Используется для:**
- Тестирование полной архитектуры
- Проверка всех сервисов
- Load testing
- Production-like environment

---

## 🔄 Как переключиться на Full Stack

### Вариант A: На Railway (временно)

1. **Переименовать конфиги:**
```bash
# Бэкап текущего
mv railway.json railway.bootstrap.json

# Активировать fullstack
mv railway.fullstack.json railway.json
```

2. **Закоммитить и запушить:**
```bash
git add railway.json railway.bootstrap.json Dockerfile.fullstack start_fullstack.py ios-system/IOS-System/__init__.py
git commit -m "Switch to fullstack mode for architecture testing"
git push
```

3. **Railway автоматически:**
   - Использует `Dockerfile.fullstack`
   - Запустит `python start_fullstack.py`
   - Загрузит все сервисы из `main_production.py`

4. **Проверить логи:**
```
Railway Dashboard → Deployments → View Logs

Ожидаемый вывод:
=============================================================
Starting IOS System - Full Architecture
=============================================================
Environment: production
Database: ...
Redis: ...
Frontend: /app/frontend-dist
Features:
  - Elasticsearch: false
  - ML: false
  - GPT: false
  - Monitoring: false
=============================================================
✓ Imports successful
Starting uvicorn...
INFO: Starting IOS System initialization...
INFO: Initializing core components...
INFO: EventBus initialized
INFO: ServiceRegistry initialized
INFO: IOSRoot created at /data/ios-root
...
```

### Вариант B: Локально (Docker)

```bash
# Build fullstack image
docker build -f Dockerfile.fullstack -t ios-fullstack .

# Run with minimal services
docker run -p 8080:8080 \
  -e DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db" \
  -e REDIS_URL="redis://host:6379/0" \
  -e ENABLE_ELASTICSEARCH=false \
  -e ENABLE_ML=false \
  ios-fullstack

# Run with all services
docker run -p 8080:8080 \
  -e DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db" \
  -e REDIS_URL="redis://host:6379/0" \
  -e ELASTICSEARCH_URL="http://elasticsearch:9200" \
  -e ENABLE_ELASTICSEARCH=true \
  -e ENABLE_ML=true \
  -e ENABLE_GPT=true \
  -e ENABLE_MONITORING=true \
  ios-fullstack
```

### Вариант C: Локально (Python)

```bash
cd /home/user/daten

# Set environment
export DATABASE_URL="postgresql+asyncpg://localhost:5432/ios_db"
export REDIS_URL="redis://localhost:6379/0"
export ENABLE_ELASTICSEARCH=false
export ENABLE_ML=false

# Run
python start_fullstack.py
```

---

## 🧪 Тестирование

После запуска fullstack режима:

### 1. Health Check
```bash
curl http://localhost:8080/health
```

Ожидается:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "database": "connected",
    "redis": "connected",
    "ios_root": "initialized",
    "search_service": "ready",
    "classifier_service": "ready"
  }
}
```

### 2. API Documentation
```
http://localhost:8080/api/docs
```

Должны быть эндпоинты:
- `/api/auth/*` - Authentication
- `/api/documents/*` - Document management
- `/api/search/*` - Search operations
- `/api/graph/*` - Knowledge graph
- `/api/admin/*` - Admin operations
- `/api/ai/*` - AI services

### 3. Frontend
```
http://localhost:8080/
```

React UI должен загрузиться и подключиться к полному API.

---

## 🔙 Как вернуться к Bootstrap

```bash
# Restore bootstrap config
mv railway.bootstrap.json railway.json

git add railway.json
git commit -m "Revert to bootstrap mode"
git push
```

---

## ⚠️ Требования для Full Stack

### Обязательно:
- ✅ `DATABASE_URL` - PostgreSQL connection
- ✅ `REDIS_URL` - Redis connection
- ✅ `SECRET_KEY` - для JWT tokens

### Опционально:
- `ELASTICSEARCH_URL` + `ENABLE_ELASTICSEARCH=true`
- `ENABLE_ML=true` (требует scikit-learn, sentence-transformers)
- `ENABLE_GPT=true` + `OPENAI_API_KEY`
- `ENABLE_MONITORING=true` (Prometheus)

### Railway Variables:
В Railway Dashboard → Variables добавить:
```
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
SECRET_KEY=<сгенерировать случайный ключ>
ENABLE_ELASTICSEARCH=false
ENABLE_ML=false
ENABLE_GPT=false
ENABLE_MONITORING=false
```

---

## 📊 Сравнение

| Характеристика | Bootstrap | Full Stack |
|---------------|-----------|------------|
| Startup time | ~5s | ~30-60s |
| Memory usage | ~100MB | ~500MB+ |
| Services | Frontend + basic API | All services |
| Database | Optional | Required |
| Redis | Optional | Required |
| Production ready | No | Yes |
| Testing | Frontend only | Complete architecture |

---

## 🎯 Рекомендация

**Для разработки frontend:** используйте Bootstrap режим (быстро, легко)

**Для тестирования архитектуры:** переключайтесь на Full Stack (полная функциональность)

**Для production:** Full Stack с включенными нужными сервисами через env vars
