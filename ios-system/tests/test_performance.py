"""
Performance Tests для IOS System
Тесты производительности и нагрузки
"""
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import statistics


class TestPerformance:
    """Тесты производительности"""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_service_registry_performance(self):
        """Тест производительности Service Registry"""
        from ios_system.core.service_registry import ServiceRegistry
        from unittest.mock import Mock
        
        registry = ServiceRegistry()
        
        # Регистрируем много сервисов
        start_time = time.time()
        
        for i in range(1000):
            service = Mock()
            registry.register(f'service_{i}', service)
            
        registration_time = time.time() - start_time
        
        # Проверяем что регистрация быстрая
        assert registration_time < 1.0  # Должно занять < 1 секунды
        assert len(registry) == 1000
        
        # Тест производительности получения сервисов
        start_time = time.time()
        
        for i in range(1000):
            service = registry.get(f'service_{i}')
            assert service is not None
            
        lookup_time = time.time() - start_time
        
        assert lookup_time < 0.5  # Lookup должен быть очень быстрым
        
    def test_encryption_performance(self):
        """Тест производительности шифрования"""
        from ios_system.security.encryption_service import EncryptionService
        
        service = EncryptionService()
        test_data = "sensitive data" * 100  # ~1.5KB
        
        # Тест производительности шифрования
        encrypt_times = []
        for _ in range(100):
            start = time.time()
            encrypted = service.encrypt(test_data)
            encrypt_times.append(time.time() - start)
            
        avg_encrypt_time = statistics.mean(encrypt_times)
        
        # Шифрование должно быть быстрым
        assert avg_encrypt_time < 0.01  # < 10ms в среднем
        
        # Тест производительности дешифрования
        encrypted = service.encrypt(test_data)
        decrypt_times = []
        
        for _ in range(100):
            start = time.time()
            decrypted = service.decrypt(encrypted)
            decrypt_times.append(time.time() - start)
            
        avg_decrypt_time = statistics.mean(decrypt_times)
        
        assert avg_decrypt_time < 0.01  # < 10ms в среднем
        
    def test_password_hashing_performance(self):
        """Тест производительности хеширования паролей"""
        from ios_system.security.encryption_service import EncryptionService
        
        password = "testpassword123"
        
        # Хеширование должно быть медленным (защита от brute force)
        start = time.time()
        password_hash, salt = EncryptionService.hash_password(password)
        hash_time = time.time() - start
        
        # PBKDF2 с 100k iterations должен занимать заметное время
        assert hash_time > 0.01  # > 10ms (защита от brute force)
        assert hash_time < 1.0   # но < 1 секунды (чтобы не тормозить UX)
        
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_health_check_performance(self):
        """Тест производительности health check"""
        from ios_system.monitoring.health_check import HealthChecker
        from unittest.mock import AsyncMock, Mock
        
        # Mock быстрых компонентов
        db_mock = AsyncMock()
        db_mock.is_connected = Mock(return_value=True)
        db_mock.ping = AsyncMock()
        
        redis_mock = AsyncMock()
        redis_mock.is_connected = Mock(return_value=True)
        redis_mock.ping = AsyncMock()
        
        service1 = Mock()
        service1.health_check = AsyncMock(return_value={"healthy": True})
        
        services = {'service1': service1}
        
        checker = HealthChecker(
            db_manager=db_mock,
            redis_cache=redis_mock,
            services=services
        )
        
        # Измеряем время health check
        start = time.time()
        result = await checker.check()
        check_time = time.time() - start
        
        # Health check должен быть очень быстрым
        assert check_time < 0.1  # < 100ms
        assert result['healthy'] is True


class TestConcurrency:
    """Тесты конкурентности"""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_service_access(self):
        """Тест конкурентного доступа к сервисам"""
        from ios_system.core.service_registry import ServiceRegistry
        from unittest.mock import Mock
        
        registry = ServiceRegistry()
        service = Mock()
        service.process = Mock(return_value="result")
        registry.register('test_service', service)
        
        async def access_service():
            s = registry.get('test_service')
            return s.process() if s else None
            
        # Запускаем 100 конкурентных операций
        tasks = [access_service() for _ in range(100)]
        results = await asyncio.gather(*tasks)
        
        # Все должны получить результат
        assert len(results) == 100
        assert all(r == "result" for r in results)
        
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_health_checks(self):
        """Тест конкурентных health checks"""
        from ios_system.monitoring.health_check import HealthChecker
        from unittest.mock import AsyncMock, Mock
        
        db_mock = AsyncMock()
        db_mock.is_connected = Mock(return_value=True)
        db_mock.ping = AsyncMock()
        
        checker = HealthChecker(db_manager=db_mock)
        
        # Запускаем 50 конкурентных health checks
        tasks = [checker.check_quick() for _ in range(50)]
        
        start = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start
        
        # Все должны успешно завершиться
        assert len(results) == 50
        assert all('status' in r for r in results)
        
        # Должно выполниться быстро даже при конкуренции
        assert total_time < 2.0  # < 2 секунд для 50 проверок


class TestScalability:
    """Тесты масштабируемости"""
    
    @pytest.mark.performance
    def test_service_registry_scalability(self):
        """Тест масштабируемости Service Registry"""
        from ios_system.core.service_registry import ServiceRegistry
        from unittest.mock import Mock
        
        sizes = [10, 100, 1000, 5000]
        registration_times = []
        lookup_times = []
        
        for size in sizes:
            registry = ServiceRegistry()
            
            # Измеряем время регистрации
            start = time.time()
            for i in range(size):
                service = Mock()
                registry.register(f'service_{i}', service)
            registration_times.append(time.time() - start)
            
            # Измеряем время lookup
            start = time.time()
            for i in range(size):
                registry.get(f'service_{i}')
            lookup_times.append(time.time() - start)
            
        # Проверяем что производительность линейно масштабируется
        # (не квадратично)
        for i in range(len(sizes) - 1):
            ratio = sizes[i + 1] / sizes[i]
            time_ratio = registration_times[i + 1] / registration_times[i]
            
            # Время должно расти примерно линейно
            assert time_ratio < ratio * 2  # Допускаем некоторую нелинейность
            
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_encryption_scalability(self):
        """Тест масштабируемости шифрования"""
        from ios_system.security.encryption_service import EncryptionService
        
        service = EncryptionService()
        data_sizes = [100, 1000, 10000, 100000]  # bytes
        encrypt_times = []
        
        for size in data_sizes:
            data = "x" * size
            
            start = time.time()
            encrypted = service.encrypt(data)
            encrypt_times.append(time.time() - start)
            
        # Проверяем что шифрование масштабируется линейно
        for i in range(len(data_sizes) - 1):
            size_ratio = data_sizes[i + 1] / data_sizes[i]
            time_ratio = encrypt_times[i + 1] / encrypt_times[i]
            
            # Должна быть примерно линейная зависимость
            assert time_ratio < size_ratio * 2


class TestMemoryUsage:
    """Тесты использования памяти"""
    
    @pytest.mark.performance
    def test_service_registry_memory(self):
        """Тест использования памяти Service Registry"""
        import sys
        from ios_system.core.service_registry import ServiceRegistry
        from unittest.mock import Mock
        
        registry = ServiceRegistry()
        
        # Получаем базовый размер
        base_size = sys.getsizeof(registry)
        
        # Добавляем сервисы
        for i in range(1000):
            service = Mock()
            registry.register(f'service_{i}', service)
            
        # Размер не должен расти чрезмерно
        # (проверяем что нет memory leaks)
        final_size = sys.getsizeof(registry)
        
        # Примерная оценка разумного размера
        assert final_size < base_size + (1000 * 1000)  # < 1MB для 1000 сервисов


class TestResponseTimes:
    """Тесты времени отклика"""
    
    @pytest.mark.performance
    def test_api_response_time_target(self):
        """Тест что API отвечает в пределах целевого времени"""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from ios_system.middleware.request_logger import RequestLoggerMiddleware
        
        app = FastAPI()
        app.add_middleware(RequestLoggerMiddleware)
        
        @app.get("/api/fast")
        async def fast_endpoint():
            return {"status": "ok"}
            
        client = TestClient(app)
        
        # Измеряем 100 запросов
        response_times = []
        
        for _ in range(100):
            start = time.time()
            response = client.get("/api/fast")
            response_times.append((time.time() - start) * 1000)  # в миллисекундах
            assert response.status_code == 200
            
        # Вычисляем статистику
        avg_time = statistics.mean(response_times)
        p95_time = sorted(response_times)[int(len(response_times) * 0.95)]
        p99_time = sorted(response_times)[int(len(response_times) * 0.99)]
        
        # Проверяем целевые значения
        assert avg_time < 100  # средний < 100ms
        assert p95_time < 200  # P95 < 200ms
        assert p99_time < 300  # P99 < 300ms
        
        print(f"\nResponse time stats:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  P95: {p95_time:.2f}ms")
        print(f"  P99: {p99_time:.2f}ms")


# Benchmark utilities
def run_benchmark(func, iterations=1000):
    """Утилита для бенчмарков"""
    times = []
    
    for _ in range(iterations):
        start = time.time()
        func()
        times.append(time.time() - start)
        
    return {
        'iterations': iterations,
        'total_time': sum(times),
        'avg_time': statistics.mean(times),
        'min_time': min(times),
        'max_time': max(times),
        'median_time': statistics.median(times)
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance"])
