# Сделать скрипт исполняемым
chmod +x scripts/setup_observability.sh

# Запустить установку
./scripts/setup_observability.sh

# Проверить статус
docker-compose -f docker-compose.observability.yml ps

# Все сервисы должны быть в состоянии "Up"