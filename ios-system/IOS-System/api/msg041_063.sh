# 1. Jaeger UI
open http://localhost:16686
# Выбрать сервис "ios-api" и искать traces

# 2. Kibana
open http://localhost:5601
# Перейти в Discover, выбрать index pattern "ios-logs-*"

# 3. Metrics
curl http://localhost:8000/metrics
# Должны увидеть Prometheus metrics

# 4. Sentry
open http://localhost:9000
# Создать аккаунт и проект

# 5. Тестовые запросы
curl -X POST "http://localhost:8000/api/auth/token" \
  -d "username=admin&password=admin"

# Проверить traces в Jaeger
# Проверить logs в Kibana