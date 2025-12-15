# Запустить все установки
chmod +x scripts/setup_security.sh
./scripts/setup_security.sh

# Тесты
pytest tests/security/ -v

# Запустить API
uvicorn api.main:app --reload

# Тестовый скрипт
chmod +x scripts/test_security.sh
./scripts/test_security.sh