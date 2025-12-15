# 📈 SCALABILITY TESTING GUIDE
## IOS System - Load & Performance Testing

**Цель:** Проверить масштабируемость системы под различными нагрузками

---

## 📋 СОДЕРЖАНИЕ

- [Установка](#установка)
- [Load Testing (Locust)](#load-testing)
- [Performance Benchmarks](#performance-benchmarks)
- [Сценарии тестирования](#сценарии-тестирования)
- [Анализ результатов](#анализ-результатов)
- [Рекомендации](#рекомендации)

---

## 🚀 УСТАНОВКА

### Установка зависимостей

```bash
pip install locust==2.20.0
pip install fastapi httpx
```

---

## 🔥 LOAD TESTING (Locust)

### Быстрый старт

```bash
# Запуск интерактивного меню
./run_load_tests.sh
```

### Сценарии тестирования

#### 1. Light Load Test
```bash
locust -f tests/locustfile.py \
    --host=http://localhost:8000 \
    --users=10 \
    --spawn-rate=2 \
    --run-time=5m \
    --headless
```
**Цель:** Базовая проверка функциональности  
**Пользователей:** 10  
**Длительность:** 5 минут

#### 2. Normal Load Test
```bash
locust -f tests/locustfile.py \
    --host=http://localhost:8000 \
    --users=50 \
    --spawn-rate=5 \
    --run-time=10m \
    --headless \
    --html=report.html
```
**Цель:** Типичная нагрузка  
**Пользователей:** 50  
**Длительность:** 10 минут

#### 3. Heavy Load Test
```bash
locust -f tests/locustfile.py \
    --host=http://localhost:8000 \
    --users=100 \
    --spawn-rate=10 \
    --run-time=10m \
    --headless
```
**Цель:** Высокая нагрузка  
**Пользователей:** 100  
**Длительность:** 10 минут

#### 4. Stress Test
```bash
locust -f tests/locustfile.py \
    --host=http://localhost:8000 \
    --users=200 \
    --spawn-rate=20 \
    --run-time=15m \
    --headless
```
**Цель:** Найти предел системы  
**Пользователей:** 200  
**Длительность:** 15 минут

#### 5. Spike Test
```bash
locust -f tests/locustfile.py \
    --host=http://localhost:8000 \
    --users=500 \
    --spawn-rate=50 \
    --run-time=5m \
    --headless
```
**Цель:** Резкий всплеск нагрузки  
**Пользователей:** 500  
**Длительность:** 5 минут

#### 6. Endurance Test
```bash
locust -f tests/locustfile.py \
    --host=http://localhost:8000 \
    --users=50 \
    --spawn-rate=5 \
    --run-time=1h \
    --headless
```
**Цель:** Длительная стабильность  
**Пользователей:** 50  
**Длительность:** 1 час

### Web UI Mode

```bash
locust -f tests/locustfile.py --host=http://localhost:8000
```

Затем откройте: http://localhost:8089

---

## ⚡ PERFORMANCE BENCHMARKS

### Запуск benchmarks

```bash
python benchmark.py
```

### Что тестируется

**Service Registry:**
- Register operation (10,000 iterations)
- Get operation (100,000 iterations)

**Encryption:**
- Encrypt small data (10,000 iterations)
- Encrypt medium data (5,000 iterations)
- Encrypt large data (1,000 iterations)
- Decrypt operation (5,000 iterations)
- Password hashing (100 iterations)

**Configuration:**
- Settings creation (1,000 iterations)
- Model dump (10,000 iterations)

**Health Checker:**
- Quick health check (1,000 iterations)

### Результаты

Benchmark выдает:
- Average time (среднее)
- Median time (медиана)
- Min/Max time
- P50, P90, P95, P99 percentiles
- Operations per second
- Standard deviation

---

## 📊 ТИПЫ ПОЛЬЗОВАТЕЛЕЙ (Locust)

### 1. IOSSystemUser
**Профиль:** Обычный пользователь системы  
**Действия:**
- View dashboard (10x)
- Search documents (8x)
- View document (5x)
- Create document (3x)
- Update document (2x)
- Delete document (1x)
- Semantic search (4x)
- Knowledge graph query (2x)
- AI summarization (1x)

**Wait time:** 1-3 секунды между запросами

### 2. HeavyUser
**Профиль:** "Тяжелый" пользователь  
**Действия:**
- Bulk operations (массовое создание документов)

**Wait time:** 0.5-1.5 секунды

### 3. ReadOnlyUser
**Профиль:** Пользователь только для чтения  
**Действия:**
- Browse documents (5x)
- View document details (3x)
- Search (2x)

**Wait time:** 2-5 секунд

### 4. APIUser
**Профиль:** API клиент  
**Действия:**
- Batch API requests

**Wait time:** 0.1-0.5 секунды

---

## 📈 ЦЕЛЕВЫЕ МЕТРИКИ

### Response Time

| Endpoint | P50 | P95 | P99 | Max |
|----------|-----|-----|-----|-----|
| /api/dashboard | < 50ms | < 100ms | < 200ms | < 500ms |
| /api/search | < 100ms | < 200ms | < 500ms | < 1s |
| /api/documents/[id] | < 50ms | < 100ms | < 200ms | < 500ms |
| /api/documents (POST) | < 200ms | < 500ms | < 1s | < 2s |
| /api/search/semantic | < 500ms | < 1s | < 2s | < 5s |
| /api/ai/summarize | < 2s | < 5s | < 10s | < 30s |

### Throughput

- **Минимум:** 100 requests/sec
- **Цель:** 500 requests/sec
- **Отлично:** 1000+ requests/sec

### Error Rate

- **Допустимо:** < 1%
- **Цель:** < 0.1%
- **Отлично:** < 0.01%

### Concurrency

- **Минимум:** 50 concurrent users
- **Цель:** 200 concurrent users
- **Отлично:** 500+ concurrent users

---

## 🔍 АНАЛИЗ РЕЗУЛЬТАТОВ

### Locust Reports

После теста генерируются:

1. **HTML Report** - визуальный отчет
   - Graphs (RPS, Response time)
   - Statistics table
   - Failures table
   - Distribution charts

2. **CSV Files:**
   - `*_stats.csv` - Statistics per endpoint
   - `*_stats_history.csv` - Time series data
   - `*_failures.csv` - Failed requests

### Ключевые показатели

**В HTML отчете смотрите:**

1. **Request Statistics:**
   - Total Requests
   - Failures
   - Median Response Time
   - Average Response Time
   - Min/Max Response Time
   - RPS (Requests per Second)

2. **Response Time Charts:**
   - Median Response Time over time
   - P95/P99 Response Time

3. **User Count:**
   - Number of users over time
   - Spawn rate effectiveness

4. **Failure Analysis:**
   - Types of errors
   - Failed endpoints
   - Error messages

### Benchmark Results

Файл `benchmark_results.json` содержит:

```json
{
  "timestamp": "2024-12-15T...",
  "results": [
    {
      "name": "ServiceRegistry.register",
      "iterations": 10000,
      "avg_time_ms": 0.05,
      "p95_ms": 0.10,
      "ops_per_sec": 20000
    }
  ]
}
```

---

## 🎯 ИНТЕРПРЕТАЦИЯ РЕЗУЛЬТАТОВ

### Хорошие показатели ✅

```
✓ Response time P95 < 200ms
✓ Error rate < 1%
✓ RPS > 100
✓ No timeouts
✓ Stable performance over time
```

### Проблемные показатели ⚠️

```
⚠ Response time P95 > 500ms
⚠ Error rate > 5%
⚠ RPS < 50
⚠ Frequent timeouts
⚠ Degrading performance over time
⚠ Memory leaks
```

### Критические проблемы ❌

```
❌ Response time > 5s
❌ Error rate > 20%
❌ System crashes
❌ Database connection exhaustion
❌ Out of memory errors
```

---

## 🔧 ОПТИМИЗАЦИЯ

### Если Response Time высокий:

1. **Database:**
   - Добавить индексы
   - Optimize queries
   - Increase connection pool

2. **Caching:**
   - Включить Redis caching
   - Cache часто используемые данные
   - Implement CDN для статики

3. **Code:**
   - Profile slow endpoints
   - Optimize N+1 queries
   - Асинхронная обработка

### Если много ошибок:

1. **Rate Limiting:**
   - Настроить правильные лимиты
   - Implement backoff strategy

2. **Resource Limits:**
   - Увеличить database connections
   - Увеличить memory limits
   - Scale horizontally

3. **Error Handling:**
   - Improve error handling
   - Add circuit breakers
   - Implement retries

---

## 🚀 SCALABILITY STRATEGIES

### Вертикальное масштабирование

```
✓ Увеличить CPU
✓ Увеличить RAM
✓ Faster disks (SSD)
✓ Better network
```

### Горизонтальное масштабирование

```
✓ Multiple app instances
✓ Load balancer
✓ Database read replicas
✓ Redis cluster
✓ CDN для статики
```

### Architecture Improvements

```
✓ Async processing (Celery)
✓ Message queue (RabbitMQ)
✓ Microservices
✓ Event-driven architecture
```

---

## 📝 CHECKLIST

Перед production deployment:

- [ ] Normal load test passed (50 users, 10 min)
- [ ] Heavy load test passed (100 users, 10 min)
- [ ] Stress test completed (найден предел)
- [ ] Endurance test passed (1 hour stable)
- [ ] Response time targets met
- [ ] Error rate < 1%
- [ ] No memory leaks
- [ ] Database connections stable
- [ ] Redis performance good
- [ ] All benchmarks within targets

---

## 🎓 BEST PRACTICES

1. **Test in production-like environment**
2. **Monitor during tests** (CPU, Memory, DB)
3. **Test gradually** (start small, increase load)
4. **Analyze failures** (not just success metrics)
5. **Test regularly** (before each release)
6. **Document results** (track improvements)
7. **Test edge cases** (spike, long duration)

---

## 📞 TROUBLESHOOTING

### Locust не может подключиться

```bash
# Проверьте что сервер запущен
curl http://localhost:8000/health

# Проверьте правильность host
locust -f tests/locustfile.py --host=http://localhost:8000
```

### Слишком много ошибок 5xx

```
1. Проверьте логи сервера
2. Проверьте database connections
3. Уменьшите нагрузку
4. Увеличьте resources
```

### Benchmark выдает errors

```
1. Убедитесь что все зависимости установлены
2. Проверьте что компоненты инициализированы
3. Запустите unit tests сначала
```

---

*Автор: Claude*  
*Дата: 15 декабря 2024*  
*Версия: 1.0*
