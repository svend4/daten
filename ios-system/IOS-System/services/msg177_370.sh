# 1. Подключиться к production server
ssh user@your-server.com

# 2. Клонировать репозиторий
git clone https://github.com/YOUR_USERNAME/ios-search.git
cd ios-search

# 3. Настроить .env.production
cp .env.example .env.production
# Отредактировать с production значениями

# 4. Запустить deployment
./scripts/deploy.sh

# 5. Проверить health
curl https://ios-search.com/api/health/

# 6. Мониторить
# Открыть Grafana dashboards
# Следить за метриками