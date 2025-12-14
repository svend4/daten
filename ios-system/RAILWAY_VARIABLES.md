# 🔌 Подключение баз данных к переменным окружения на Railway

**Пошаговая инструкция: PostgreSQL + Redis → Variables**

---

## 📖 КАК ЭТО РАБОТАЕТ

### Railway делает это АВТОМАТИЧЕСКИ! 🎉

Когда вы добавляете PostgreSQL или Redis к проекту:

1. Railway **создает сервис** базы данных
2. Railway **автоматически генерирует** переменные подключения
3. Railway **автоматически добавляет** эти переменные в ваше приложение
4. Ваш код **сразу видит** эти переменные

**Вам не нужно ничего делать вручную!** ✨

---

## 🐘 POSTGRESQL - Автоматическое подключение

### Шаг 1: Добавить PostgreSQL

```
1. В вашем проекте на Railway
2. Нажать "+ New"
3. Выбрать "Database"
4. Выбрать "Add PostgreSQL"
5. ✅ Готово!
```

### Шаг 2: Railway автоматически создает переменные

Railway **автоматически** создаст эти переменные:

```bash
# В PostgreSQL сервисе:
DATABASE_URL=postgresql://postgres:PASSWORD@HOST:PORT/railway
PGHOST=containers-us-west-123.railway.app
PGPORT=5432
PGUSER=postgres
PGPASSWORD=R4nD0mP@ssw0rd
PGDATABASE=railway
```

### Шаг 3: Railway автоматически передает в ваше приложение

Railway **автоматически** добавит в ваше приложение:

```bash
# В вашем приложении (daten):
DATABASE_URL=postgresql://postgres:PASSWORD@postgres.railway.internal:5432/railway
         ↑
    Автоматически связано!
```

### Как проверить:

1. **В PostgreSQL сервисе:**
   - Кликнуть на PostgreSQL
   - Вкладка "Variables"
   - Увидите переменные PostgreSQL

2. **В вашем приложении:**
   - Кликнуть на ваше приложение (daten)
   - Вкладка "Variables"
   - Увидите `DATABASE_URL` - это ссылка на PostgreSQL!

---

## 🔴 REDIS - Автоматическое подключение

### Шаг 1: Добавить Redis

```
1. В вашем проекте на Railway
2. Нажать "+ New"
3. Выбрать "Database"
4. Выбрать "Add Redis"
5. ✅ Готово!
```

### Шаг 2: Railway автоматически создает переменные

Railway **автоматически** создаст:

```bash
# В Redis сервисе:
REDIS_URL=redis://default:PASSWORD@HOST:PORT
REDIS_HOST=containers-us-west-456.railway.app
REDIS_PORT=6379
REDIS_PASSWORD=An0th3rR4nd0m
```

### Шаг 3: Railway автоматически передает в приложение

```bash
# В вашем приложении (daten):
REDIS_URL=redis://default:PASSWORD@redis.railway.internal:6379
      ↑
  Автоматически связано!
```

---

## 🔗 MAGIC: Внутренняя сеть Railway

### Что такое `.railway.internal`?

Railway создает **частную сеть** между вашими сервисами:

```
┌─────────────────────────────────────────────┐
│  Railway Private Network                    │
│                                             │
│  ┌─────────────┐      ┌──────────────┐     │
│  │   daten     │─────→│  PostgreSQL  │     │
│  │  (your app) │      │  postgres... │     │
│  └─────────────┘      │  .internal   │     │
│         │             └──────────────┘     │
│         │                                   │
│         ↓                                   │
│  ┌──────────────┐                          │
│  │    Redis     │                          │
│  │  redis...    │                          │
│  │  .internal   │                          │
│  └──────────────┘                          │
│                                             │
└─────────────────────────────────────────────┘
```

**Преимущества:**
- ✅ **Быстрее** - внутренняя сеть
- ✅ **Безопаснее** - не доступно из интернета
- ✅ **Бесплатно** - нет трафика наружу

---

## 🎯 КАК ПРОВЕРИТЬ ЧТО ВСЁ ПОДКЛЮЧЕНО

### Вариант 1: Через Railway Dashboard

**Для PostgreSQL:**
```
1. Railway Dashboard → ваш проект
2. Кликнуть на PostgreSQL сервис
3. Вкладка "Variables"
4. Увидите:
   ✅ DATABASE_URL
   ✅ PGHOST
   ✅ PGPORT
   ✅ PGUSER
   ✅ PGPASSWORD
   ✅ PGDATABASE

5. Кликнуть на ваше приложение (daten)
6. Вкладка "Variables"
7. Должны увидеть:
   ✅ DATABASE_URL = postgresql://...railway.internal...
```

**Для Redis:**
```
1. Кликнуть на Redis сервис
2. Вкладка "Variables"
3. Увидите:
   ✅ REDIS_URL
   ✅ REDIS_HOST
   ✅ REDIS_PORT
   ✅ REDIS_PASSWORD

4. Кликнуть на ваше приложение
5. Вкладка "Variables"
6. Должны увидеть:
   ✅ REDIS_URL = redis://...railway.internal...
```

### Вариант 2: Через логи приложения

```
1. Ваше приложение → Deployments → View Logs
2. Найти строки:
   INFO: Database URL: postgresql://...
   INFO: Redis URL: redis://...
3. ✅ Если видите - подключено!
```

### Вариант 3: Через код (тест endpoint)

Ваш код уже проверяет подключения в `/api/status`:

```python
# ios_bootstrap/main.py уже есть:

@app.get("/api/status")
async def api_status():
    return {
        "database": {
            "connected": False,  # TODO: будет True после подключения
            "url": settings.database_url.split("@")[-1]
        },
        "redis": {
            "connected": False,  # TODO: будет True после подключения
            "url": settings.redis_url
        }
    }
```

Открыть: `https://ваш-домен.up.railway.app/api/status`

---

## 🔧 РУЧНАЯ НАСТРОЙКА (если нужно)

### Когда нужна ручная настройка?

Обычно **НЕ нужна**! Railway делает всё автоматически.

Но иногда нужно:
- 📝 Изменить имя переменной
- 🔗 Добавить внешнюю базу данных
- ⚙️ Специфичная конфигурация

### Как добавить переменную вручную:

```
1. Ваше приложение → Variables
2. + New Variable
3. Variable Name: CUSTOM_DB_URL
4. Value: postgresql://user:pass@external-host:5432/db
5. Add
```

### Как использовать переменную из другого сервиса:

Railway поддерживает **Reference** (ссылки):

```
1. Ваше приложение → Variables
2. + Reference
3. Выбрать сервис: PostgreSQL
4. Выбрать переменную: DATABASE_URL
5. Новое имя (опционально): DB_CONNECTION
6. Add
```

---

## 💻 КАК ИСПОЛЬЗОВАТЬ В КОДЕ

### Ваш код УЖЕ настроен! ✅

```python
# ios_bootstrap/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Railway автоматически передаст эти переменные!

    database_url: str = Field(
        default="postgresql://...",
        env="DATABASE_URL"  # ← Читает из Railway!
    )

    redis_url: str = Field(
        default="redis://...",
        env="REDIS_URL"  # ← Читает из Railway!
    )

    secret_key: str = Field(
        default="change-me",
        env="SECRET_KEY"  # ← Вы добавили вручную
    )

# Создать instance
settings = Settings()

# Использовать:
print(settings.database_url)  # postgresql://...railway.internal...
print(settings.redis_url)     # redis://...railway.internal...
```

### Подключение к PostgreSQL:

```python
# ios_bootstrap/database.py (создадим позже)

from sqlalchemy.ext.asyncio import create_async_engine
from ios_bootstrap.config import settings

# Railway переменная автоматически используется!
engine = create_async_engine(
    settings.database_url,  # ← Из Railway
    echo=True
)
```

### Подключение к Redis:

```python
# ios_bootstrap/cache.py (создадим позже)

import redis
from ios_bootstrap.config import settings

# Railway переменная автоматически используется!
redis_client = redis.from_url(
    settings.redis_url,  # ← Из Railway
    decode_responses=True
)
```

---

## ✅ CHECKLIST - Что должно быть

После добавления PostgreSQL и Redis на Railway:

### В PostgreSQL сервисе:
- [ ] ✅ Сервис запущен (Status: Running)
- [ ] ✅ Variables есть: DATABASE_URL, PGHOST, PGPORT, PGUSER, PGPASSWORD

### В Redis сервисе:
- [ ] ✅ Сервис запущен (Status: Running)
- [ ] ✅ Variables есть: REDIS_URL, REDIS_HOST, REDIS_PORT

### В вашем приложении (daten):
- [ ] ✅ Variable: DATABASE_URL (автоматически от PostgreSQL)
- [ ] ✅ Variable: REDIS_URL (автоматически от Redis)
- [ ] ✅ Variable: SECRET_KEY (добавили вручную)
- [ ] ✅ Variable: ENVIRONMENT = production (опционально)

### Проверка работы:
- [ ] ✅ Деплой успешен (зеленый ✓)
- [ ] ✅ `/health` возвращает `{"status": "healthy"}`
- [ ] ✅ Логи без ошибок подключения

---

## 🐛 TROUBLESHOOTING

### Проблема: "DATABASE_URL not found"

**Причина:** PostgreSQL не добавлен или не связан

**Решение:**
1. Проверить что PostgreSQL сервис Running
2. В вашем приложении → Variables → должна быть DATABASE_URL
3. Если нет - удалить и заново добавить PostgreSQL
4. Или добавить Reference вручную

### Проблема: "Cannot connect to database"

**Причина:** Неправильный URL или база не готова

**Решение:**
1. Посмотреть логи PostgreSQL сервиса
2. Проверить что DATABASE_URL содержит `.railway.internal`
3. Подождать 1-2 минуты после создания
4. Проверить что приложение в той же Railway project

### Проблема: "REDIS_URL not found"

**Решение:**
1. Аналогично PostgreSQL
2. Проверить что Redis сервис Running
3. Проверить Variables в приложении

---

## 📊 СХЕМА СВЯЗЕЙ

```
Railway Project: svend4/daten
─────────────────────────────────────────────

┌──────────────────┐
│  PostgreSQL      │
│                  │
│  Variables:      │
│  • DATABASE_URL  │────────┐
│  • PGHOST        │        │
│  • PGPORT        │        │
│  • PGUSER        │        │
│  • PGPASSWORD    │        │
└──────────────────┘        │
                            │ Автоматическая
┌──────────────────┐        │ связь
│  Redis           │        │
│                  │        │
│  Variables:      │        │
│  • REDIS_URL     │────────┤
│  • REDIS_HOST    │        │
│  • REDIS_PORT    │        │
└──────────────────┘        │
                            ↓
                   ┌─────────────────┐
                   │  Ваше приложение│
                   │  (daten)        │
                   │                 │
                   │  Variables:     │
                   │  • DATABASE_URL │←─┐
                   │  • REDIS_URL    │←─┤ Автоматически
                   │  • SECRET_KEY   │  │ добавлено!
                   │  • ENVIRONMENT  │  │
                   └─────────────────┘  │
                            │            │
                            └────────────┘
```

---

## 🎯 БЫСТРАЯ ШПАРГАЛКА

### Добавить PostgreSQL:
```
+ New → Database → PostgreSQL
✅ DATABASE_URL автоматически в вашем приложении
```

### Добавить Redis:
```
+ New → Database → Redis
✅ REDIS_URL автоматически в вашем приложении
```

### Проверить переменные:
```
Ваше приложение → Variables
Должны видеть:
✅ DATABASE_URL = postgresql://...railway.internal...
✅ REDIS_URL = redis://...railway.internal...
```

### Использовать в коде:
```python
from ios_bootstrap.config import settings

# Автоматически получаете из Railway:
settings.database_url  # PostgreSQL
settings.redis_url     # Redis
settings.secret_key    # Ваш SECRET_KEY
```

---

## ✨ ГОТОВО!

После выполнения:

✅ **PostgreSQL подключен** через `DATABASE_URL`
✅ **Redis подключен** через `REDIS_URL`
✅ **Переменные автоматически** в вашем приложении
✅ **Код сразу использует** их через `settings`
✅ **Безопасная внутренняя сеть** Railway

**Ничего не нужно настраивать вручную - Railway делает всё сам!** 🎉

---

Нужна помощь с подключением к базам в коде или другие вопросы?
