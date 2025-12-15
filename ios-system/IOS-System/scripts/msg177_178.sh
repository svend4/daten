# 1. Добавить в docker-compose.yml
# Скопировать из ФАЙЛА 19, секция "Monitoring Docker Compose"

# 2. Создать конфигурацию Prometheus
mkdir -p monitoring/prometheus
# Скопировать prometheus.yml из ФАЙЛА 19

# 3. Создать Grafana dashboards
mkdir -p monitoring/grafana/dashboards
# Скопировать dashboards из ФАЙЛА 19

# 4. Запустить
docker-compose up -d prometheus grafana

# 5. Открыть Grafana
# http://localhost:3000
# Login: admin / admin