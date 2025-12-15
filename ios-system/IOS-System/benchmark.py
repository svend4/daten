#!/usr/bin/env python3
"""
Benchmark Script для IOS System
Измеряет производительность ключевых компонентов
"""
import time
import asyncio
import statistics
from typing import List, Dict, Any, Callable
from datetime import datetime
import json


class BenchmarkResult:
    """Результат benchmark теста"""
    
    def __init__(self, name: str):
        self.name = name
        self.execution_times: List[float] = []
        self.errors: List[str] = []
        self.start_time = None
        self.end_time = None
        
    def add_execution_time(self, time_ms: float):
        """Добавить время выполнения"""
        self.execution_times.append(time_ms)
        
    def add_error(self, error: str):
        """Добавить ошибку"""
        self.errors.append(error)
        
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику"""
        if not self.execution_times:
            return {
                "name": self.name,
                "error": "No execution times recorded"
            }
            
        times = sorted(self.execution_times)
        
        return {
            "name": self.name,
            "iterations": len(times),
            "errors": len(self.errors),
            "total_time_ms": sum(times),
            "avg_time_ms": statistics.mean(times),
            "median_time_ms": statistics.median(times),
            "min_time_ms": min(times),
            "max_time_ms": max(times),
            "p50_ms": times[int(len(times) * 0.50)],
            "p90_ms": times[int(len(times) * 0.90)],
            "p95_ms": times[int(len(times) * 0.95)],
            "p99_ms": times[int(len(times) * 0.99)],
            "stddev_ms": statistics.stdev(times) if len(times) > 1 else 0,
            "ops_per_sec": 1000 / statistics.mean(times) if statistics.mean(times) > 0 else 0
        }
        
    def print_summary(self):
        """Вывести summary"""
        stats = self.get_statistics()
        
        print(f"\n{'=' * 60}")
        print(f"Benchmark: {stats['name']}")
        print(f"{'=' * 60}")
        print(f"Iterations:    {stats['iterations']}")
        print(f"Errors:        {stats['errors']}")
        print(f"Avg time:      {stats['avg_time_ms']:.2f} ms")
        print(f"Median time:   {stats['median_time_ms']:.2f} ms")
        print(f"Min time:      {stats['min_time_ms']:.2f} ms")
        print(f"Max time:      {stats['max_time_ms']:.2f} ms")
        print(f"P50:           {stats['p50_ms']:.2f} ms")
        print(f"P90:           {stats['p90_ms']:.2f} ms")
        print(f"P95:           {stats['p95_ms']:.2f} ms")
        print(f"P99:           {stats['p99_ms']:.2f} ms")
        print(f"Ops/sec:       {stats['ops_per_sec']:.2f}")
        print(f"{'=' * 60}\n")


class BenchmarkRunner:
    """Запускает benchmark тесты"""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        
    def run_sync_benchmark(
        self,
        name: str,
        func: Callable,
        iterations: int = 1000,
        warmup: int = 100
    ) -> BenchmarkResult:
        """
        Запустить синхронный benchmark
        
        Args:
            name: Название теста
            func: Функция для тестирования
            iterations: Количество итераций
            warmup: Количество warmup итераций
        """
        result = BenchmarkResult(name)
        
        # Warmup
        print(f"Warming up {name}... ({warmup} iterations)")
        for _ in range(warmup):
            try:
                func()
            except Exception as e:
                pass
                
        # Основной benchmark
        print(f"Running {name}... ({iterations} iterations)")
        result.start_time = datetime.now()
        
        for i in range(iterations):
            start = time.perf_counter()
            try:
                func()
                elapsed = (time.perf_counter() - start) * 1000  # в миллисекундах
                result.add_execution_time(elapsed)
            except Exception as e:
                result.add_error(str(e))
                
            # Progress indicator
            if (i + 1) % 100 == 0:
                print(f"  Progress: {i + 1}/{iterations}")
                
        result.end_time = datetime.now()
        self.results.append(result)
        
        return result
        
    async def run_async_benchmark(
        self,
        name: str,
        func: Callable,
        iterations: int = 1000,
        warmup: int = 100
    ) -> BenchmarkResult:
        """Запустить асинхронный benchmark"""
        result = BenchmarkResult(name)
        
        # Warmup
        print(f"Warming up {name}... ({warmup} iterations)")
        for _ in range(warmup):
            try:
                await func()
            except Exception:
                pass
                
        # Основной benchmark
        print(f"Running {name}... ({iterations} iterations)")
        result.start_time = datetime.now()
        
        for i in range(iterations):
            start = time.perf_counter()
            try:
                await func()
                elapsed = (time.perf_counter() - start) * 1000
                result.add_execution_time(elapsed)
            except Exception as e:
                result.add_error(str(e))
                
            if (i + 1) % 100 == 0:
                print(f"  Progress: {i + 1}/{iterations}")
                
        result.end_time = datetime.now()
        self.results.append(result)
        
        return result
        
    def save_results(self, filename: str = "benchmark_results.json"):
        """Сохранить результаты в JSON"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "results": [r.get_statistics() for r in self.results]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"\nResults saved to: {filename}")
        
    def print_summary(self):
        """Вывести summary всех тестов"""
        print("\n" + "=" * 60)
        print("BENCHMARK SUMMARY")
        print("=" * 60)
        
        for result in self.results:
            result.print_summary()


# Benchmark тесты для различных компонентов

def benchmark_service_registry():
    """Benchmark для Service Registry"""
    from ios_system.core.service_registry import ServiceRegistry
    from unittest.mock import Mock
    
    runner = BenchmarkRunner()
    
    # Test 1: Register service
    def test_register():
        registry = ServiceRegistry()
        service = Mock()
        registry.register('test_service', service)
        
    result = runner.run_sync_benchmark(
        "ServiceRegistry.register",
        test_register,
        iterations=10000
    )
    result.print_summary()
    
    # Test 2: Get service
    registry = ServiceRegistry()
    for i in range(100):
        registry.register(f'service_{i}', Mock())
        
    def test_get():
        registry.get('service_50')
        
    result = runner.run_sync_benchmark(
        "ServiceRegistry.get",
        test_get,
        iterations=100000
    )
    result.print_summary()
    
    return runner


def benchmark_encryption():
    """Benchmark для Encryption Service"""
    from ios_system.security.encryption_service import EncryptionService
    
    runner = BenchmarkRunner()
    service = EncryptionService()
    
    # Test 1: Encrypt small data
    small_data = "sensitive data"
    
    def test_encrypt_small():
        service.encrypt(small_data)
        
    result = runner.run_sync_benchmark(
        "Encryption.encrypt (small)",
        test_encrypt_small,
        iterations=10000
    )
    result.print_summary()
    
    # Test 2: Encrypt medium data
    medium_data = "x" * 1000
    
    def test_encrypt_medium():
        service.encrypt(medium_data)
        
    result = runner.run_sync_benchmark(
        "Encryption.encrypt (medium)",
        test_encrypt_medium,
        iterations=5000
    )
    result.print_summary()
    
    # Test 3: Encrypt large data
    large_data = "x" * 10000
    
    def test_encrypt_large():
        service.encrypt(large_data)
        
    result = runner.run_sync_benchmark(
        "Encryption.encrypt (large)",
        test_encrypt_large,
        iterations=1000
    )
    result.print_summary()
    
    # Test 4: Decrypt
    encrypted = service.encrypt(medium_data)
    
    def test_decrypt():
        service.decrypt(encrypted)
        
    result = runner.run_sync_benchmark(
        "Encryption.decrypt",
        test_decrypt,
        iterations=5000
    )
    result.print_summary()
    
    # Test 5: Password hashing
    def test_hash_password():
        EncryptionService.hash_password("testpassword123")
        
    result = runner.run_sync_benchmark(
        "Encryption.hash_password",
        test_hash_password,
        iterations=100  # Медленная операция
    )
    result.print_summary()
    
    return runner


def benchmark_configuration():
    """Benchmark для Configuration"""
    from ios_system.core.config import Settings
    
    runner = BenchmarkRunner()
    
    # Test 1: Create settings
    def test_create_settings():
        Settings()
        
    result = runner.run_sync_benchmark(
        "Settings.create",
        test_create_settings,
        iterations=1000
    )
    result.print_summary()
    
    # Test 2: Model dump
    settings = Settings()
    
    def test_model_dump():
        settings.model_dump_safe()
        
    result = runner.run_sync_benchmark(
        "Settings.model_dump_safe",
        test_model_dump,
        iterations=10000
    )
    result.print_summary()
    
    return runner


async def benchmark_health_checker():
    """Benchmark для Health Checker"""
    from ios_system.monitoring.health_check import HealthChecker
    from unittest.mock import AsyncMock, Mock
    
    runner = BenchmarkRunner()
    
    # Mock components
    db_mock = AsyncMock()
    db_mock.is_connected = Mock(return_value=True)
    db_mock.ping = AsyncMock()
    
    redis_mock = AsyncMock()
    redis_mock.is_connected = Mock(return_value=True)
    redis_mock.ping = AsyncMock()
    
    checker = HealthChecker(db_manager=db_mock, redis_cache=redis_mock)
    
    # Test: Health check
    async def test_health_check():
        await checker.check_quick()
        
    result = await runner.run_async_benchmark(
        "HealthChecker.check_quick",
        test_health_check,
        iterations=1000
    )
    result.print_summary()
    
    return runner


def main():
    """Основная функция"""
    print("=" * 60)
    print("IOS SYSTEM - BENCHMARK SUITE")
    print("=" * 60)
    print()
    
    # Запускаем все benchmarks
    runners = []
    
    print("\n[1/4] Benchmarking Service Registry...")
    runners.append(benchmark_service_registry())
    
    print("\n[2/4] Benchmarking Encryption...")
    runners.append(benchmark_encryption())
    
    print("\n[3/4] Benchmarking Configuration...")
    runners.append(benchmark_configuration())
    
    print("\n[4/4] Benchmarking Health Checker...")
    runner = asyncio.run(benchmark_health_checker())
    runners.append(runner)
    
    # Сохраняем все результаты
    all_results = []
    for runner in runners:
        all_results.extend(runner.results)
        
    # Создаем финальный отчет
    final_runner = BenchmarkRunner()
    final_runner.results = all_results
    final_runner.save_results("benchmark_results.json")
    
    print("\n" + "=" * 60)
    print("ALL BENCHMARKS COMPLETED")
    print("=" * 60)
    print(f"Total tests: {len(all_results)}")
    print("Results saved to: benchmark_results.json")


if __name__ == "__main__":
    main()
