# Создать pyproject.toml
cat > pyproject.toml << 'EOF'
[tool.poetry]
name = "ios-search"
version = "1.0.0"
description = "Information Operating System - Search Engine"
authors = ["Max <your-email@example.com>"]

[tool.poetry.dependencies]
python = "^3.11"
Django = "^5.0"
djangorestframework = "^3.14"
django-cors-headers = "^4.3"
django-filter = "^23.5"
psycopg2-binary = "^2.9"
elasticsearch = "^8.11"
qdrant-client = "^1.7"
sentence-transformers = "^2.2"
redis = "^5.0"
celery = "^5.3"
gunicorn = "^21.2"
python-dotenv = "^1.0"
drf-yasg = "^1.21"
prometheus-client = "^0.19"
sentry-sdk = "^1.39"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4"
pytest-django = "^4.7"
pytest-cov = "^4.1"
black = "^23.12"
flake8 = "^7.0"
mypy = "^1.8"
locust = "^2.20"
bandit = "^1.7"
safety = "^2.3"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
EOF

# Установить зависимости
poetry install