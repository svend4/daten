# Индекс файлов IOS System

Автоматически извлечено из конверсации (182 сообщения, 1118 файлов кода).

## Статистика по категориям


### api/ (163 files)

- `.sh`: 57 files
- `.txt`: 46 files
- `.py`: 35 files
- `.md`: 9 files
- `.yaml`: 8 files
- `.json`: 4 files
- `.ts`: 2 files
- `.Dockerfile`: 2 files

### config/ (48 files)

- `.txt`: 33 files
- `.sh`: 5 files
- `.yaml`: 4 files
- `.json`: 3 files
- `.py`: 3 files

### core/ (49 files)

- `.py`: 25 files
- `.txt`: 10 files
- `.md`: 4 files
- `.kt`: 3 files
- `.sh`: 2 files
- `.yaml`: 2 files
- `.ts`: 2 files
- `.js`: 1 files

### docs/ (20 files)

- `.md`: 15 files
- `.txt`: 5 files

### domains/ (0 files)


### scripts/ (187 files)

- `.txt`: 94 files
- `.sh`: 77 files
- `.py`: 8 files
- `.md`: 7 files
- `.Dockerfile`: 1 files

### services/ (375 files)

- `.txt`: 119 files
- `.py`: 117 files
- `.sh`: 62 files
- `.md`: 35 files
- `.yaml`: 28 files
- `.json`: 6 files
- `.ts`: 5 files
- `.sql`: 1 files
- `.js`: 1 files
- `.kt`: 1 files

### tests/ (61 files)

- `.txt`: 42 files
- `.py`: 14 files
- `.md`: 5 files

### ui/ (1 files)

- `.sh`: 1 files

### utils/ (214 files)

- `.txt`: 175 files
- `.py`: 39 files


## Структура IOS

```
IOS-System/
├── core/         # Ядро системы (классы IOS, Domain, Knowledge Graph)
├── services/     # Системные службы (поиск, индексация, аналитика)
├── api/          # REST API, эндпоинты, роутеры
├── ui/           # Веб-интерфейс
├── utils/        # Утилиты и вспомогательные функции
├── config/       # Конфигурационные файлы (YAML, JSON)
├── docs/         # Документация
├── tests/        # Тесты
└── scripts/      # Скрипты для развертывания
```

## Навигация

Файлы именованы по схеме: `msg{номер_сообщения}_{порядковый_номер}.{расширение}`

Например: `msg003_001.py` - первый файл из 3-го сообщения конверсации.

## Основные компоненты (из сообщений)

- **IOSRoot** - главный интерфейс системы
- **Domain** - тематический домен знаний
- **EntityRecognizer** - распознавание сущностей
- **KnowledgeGraph** - граф знаний
- **ContextManager** - управление контекстами
- **SearchEngine** - поисковый движок
- **DocumentIndexer** - индексация документов

