# 1. Поднять все сервисы
docker-compose up -d

# 2. Проверить статус
docker-compose ps

# 3. Проверить логи
docker-compose logs -f

# 4. Проверить доступность
curl http://localhost:9200  # Elasticsearch
curl http://localhost:6333  # Qdrant
redis-cli ping              # Redis
psql -h localhost -U ios_user -d ios_db  # PostgreSQL