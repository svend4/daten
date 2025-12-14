# Создать директории
mkdir -p elasticsearch/config

# Копировать конфиги
cp elasticsearch/config/elasticsearch.yml elasticsearch/config/
cp elasticsearch/config/synonyms.txt elasticsearch/config/

# Запустить кластер
docker-compose -f docker-compose.elasticsearch.yml up -d

# Проверить статус
docker-compose -f docker-compose.elasticsearch.yml ps

# Проверить health
curl -u elastic:changeme http://localhost:9200/_cluster/health?pretty

# Expected: status "green" or "yellow"