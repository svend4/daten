# Запустить миграцию
python scripts/migrate_to_elasticsearch.py

# Процесс:
# 1. Подтверждение
# 2. Миграция по батчам
# 3. Верификация
# 4. Статистика

# Expected output:
# ✓ Migration successful!
# Database count: 1000
# Elasticsearch count: 1000
# Match: ✓ Yes