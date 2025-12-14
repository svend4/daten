# 1. Создать locustfile.py
# Скопировать из ФАЙЛА 19, секция "Task 7.1: Load Testing"

# 2. Запустить load tests
locust -f tests/load/locustfile.py \
  --headless \
  --users 50 \
  --spawn-rate 5 \
  --run-time 5m \
  --host http://localhost:8000

# Цели:
# - P95 < 500ms
# - P99 < 1000ms
# - Error rate < 0.1%