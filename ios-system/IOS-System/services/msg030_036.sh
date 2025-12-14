# 1. Создать структуру проекта
ios-system/
├── .github/
│   └── workflows/
│       └── ci.yml
├── ios_core/              # Core system
│   ├── __init__.py
│   ├── system.py          # Main orchestrator
│   ├── config.py          # Configuration
│   ├── models/            # SQLAlchemy models
│   ├── repositories/      # Repository pattern
│   ├── services/          # Business logic
│   └── exceptions.py      # Custom exceptions
├── api/                   # FastAPI application
│   ├── __init__.py
│   ├── main.py
│   ├── dependencies.py
│   ├── routes/
│   └── middleware/
├── tests/                 # Tests
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── scripts/               # Utility scripts
├── docs/                  # Documentation
├── docker/                # Docker files
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
└── README.md