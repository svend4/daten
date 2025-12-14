# ⚠️ ПРОБЛЕМА: Нет защиты от cascading failures

# ✅ РЕШЕНИЕ: Circuit breaker для внешних сервисов
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def call_external_service():
    ...