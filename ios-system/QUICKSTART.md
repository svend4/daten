# IOS Search System - Быстрый старт

> **Стратегия:** Использовать существующий код, постепенно активируя компоненты

**Дата:** 2025-12-13

---

## 🚀 ЗАПУСК ЗА 5 МИНУТ

### 1. Установить зависимости

```bash
cd информационная-ОС
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Настроить окружение

```bash
cp .env.example .env
# Отредактируйте .env при необходимости
```

### 3. Запустить сервисы

```bash
docker-compose up -d postgres redis
```

### 4. Запустить приложение

```bash
python -m uvicorn ios_bootstrap.main:app --reload
```

### 5. Проверить

```bash
curl http://localhost:8000/health
# Откройте http://localhost:8000/api/docs в браузере
```

### 6. Запустить тесты

```bash
pytest ios_bootstrap/test_basic.py -v
```

---

## ✅ ЧТО РАБОТАЕТ СЕЙЧАС

- ✅ FastAPI приложение
- ✅ `/health` - health check
- ✅ `/api/status` - API status
- ✅ `/api/docs` - Swagger документация
- ✅ PostgreSQL в Docker
- ✅ Redis в Docker
- ✅ Integration tests

---

## 📈 УРОВНИ ГОТОВНОСТИ

### Level 0 (Infrastructure): 100% ✅
- FastAPI entry point
- Docker compose
- Basic endpoints
- Tests

### Level 1 (Database): 0% ⏳
**Следующий шаг:**
```python
# Добавить в ios_bootstrap/database.py
from sqlalchemy.ext.asyncio import create_async_engine
from ios_bootstrap.config import settings

engine = create_async_engine(settings.database_url)
```

### Level 2 (Search): 0% ⏳
**Использовать существующий код:**
```python
# Импортировать из IOS-System
from IOS-System.services.msg012_013 import FullTextSearch
```

### Level 3 (Auth): 0% ⏳
### Level 4 (Caching): 0% ⏳

---

## 🔧 КАК ДОБАВЛЯТЬ ФУНКЦИИ

### Принцип: Импортировать, не переписывать!

```python
# ios_bootstrap/main.py

import sys
from pathlib import Path

# Добавить IOS-System в path
sys.path.insert(0, str(Path(__file__).parent.parent / "IOS-System"))

# Импортировать существующий код
from services.msg012_013 import FullTextSearch
from core.msg003_003 import IOSRoot

# Использовать!
@app.post("/api/search")
async def search(query: str):
    searcher = FullTextSearch(indexer)
    return searcher.search(query)
```

---

## 📊 СТРУКТУРА

```
информационная-ОС/
├── IOS-System/           # Существующий код (НЕ ТРОГАТЬ!)
│   └── 1118 файлов
│
├── ios_bootstrap/        # Новая обвязка (ДОБАВЛЯТЬ СЮДА)
│   ├── main.py          # Entry point
│   ├── config.py        # Settings
│   └── test_basic.py    # Tests
│
├── requirements.txt      # Зависимости
├── docker-compose.yml    # Сервисы
└── Dockerfile           # App image
```

---

## 📝 СЛЕДУЮЩИЕ ШАГИ

1. **Сейчас:** Подключить database (Level 1)
2. **Затем:** Добавить search endpoints (Level 2)
3. **Потом:** Authentication (Level 3)
4. **Далее:** Caching (Level 4)

---

## 🆘 ПОМОЩЬ

### Не запускается?

```bash
# Проверить сервисы
docker-compose ps

# Логи
docker-compose logs postgres

# Перезапустить
docker-compose restart
```

### Тесты падают?

```bash
# Проверить подключение
curl http://localhost:8000/health

# Debug mode
pytest -vv --tb=short
```

---

**Статус:** Ready to start Level 1 🚀

См. также:
- `AUDIT_ANALYSIS.md` - анализ текущего состояния
- `IMPLEMENTATION_PLAN.md` - план доработки до MVP
- `BOOTSTRAP_GUIDE.md` - детальное руководство
