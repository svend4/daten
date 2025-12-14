# Руководство по запуску IOS-System (Существующий код)

**Цель:** Запустить СУЩЕСТВУЮЩИЙ код без переписывания, постепенно добавляя интеграцию

**Дата:** 2025-12-13

---

## 📊 Что у нас есть

### Backend (Python)
- **241 Python файлов** в структуре:
  - `core/` - 49 файлов (IOSRoot, FastAPI app, database)
  - `services/` - 375 файлов (search, classification, GPT, BERT)
  - `api/` - 163 файла (endpoints, middleware)
  - `utils/` - 214 файлов (helpers, integrations)
  - `tests/` - 61 файл (unit, integration tests)
  - `scripts/` - 187 файлов (deployment, backup)

- **Главный entry point:** `core/msg047_043.py` (FastAPI app)
- **Структура модулей:** `ios_core.*`

### Frontend (TypeScript/JavaScript)
- **11 JS/TS файлов:**
  - TypeScript SDK client (`core/msg077_047.ts`)
  - Resources (documents, search, webhooks, users)
  - Axios-based HTTP client

### Конфигурации
- **Dockerfile:** `api/msg022_002.Dockerfile`
- **CI/CD:** `api/msg024_004.yaml` (GitHub Actions)
- **Нет requirements.txt** - нужно создать

---

## 🎯 СТРАТЕГИЯ: Инкрементальная интеграция

### Принципы:
1. ✅ **Не переписывать** - использовать существующий код
2. ✅ **Минимальная обвязка** - создать только связующие файлы
3. ✅ **Постепенная активация** - включать компоненты по одному
4. ✅ **Тестирование на каждом шаге** - проверять что работает

---

## 📋 ПЛАН ДЕЙСТВИЙ

## ШАГ 1: Подготовка окружения (30 минут)

### 1.1 Создать структуру проекта

```bash
cd информационная-ОС

# Создать основную структуру (НЕ трогая IOS-System/)
mkdir -p ios_bootstrap/{ios_core,api,tests,config}

# ios_core будет импортировать модули из IOS-System/
```

### 1.2 Создать requirements.txt

На основе найденных импортов:

```python
# Core Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.23
asyncpg==0.29.0
psycopg2-binary==2.9.9
alembic==1.12.1

# Caching & Queue
redis==5.0.1
celery==5.3.4

# Search & ML
whoosh==2.7.4
elasticsearch==8.11.0
qdrant-client==1.7.0
sentence-transformers==2.2.2
scikit-learn==1.3.2
numpy==1.24.3

# GPT/OpenAI (optional)
openai==1.3.7

# Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
pyotp==2.9.0

# Monitoring
prometheus-client==0.19.0
sentry-sdk==1.38.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2

# Utilities
python-dotenv==1.0.0
click==8.1.7
locust==2.18.0

# Integrations
httpx==0.25.2
requests==2.31.0
