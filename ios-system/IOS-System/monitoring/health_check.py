"""
Health Checker - Мониторинг состояния системы и всех компонентов
"""
import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ComponentHealth:
    """Состояние здоровья компонента"""
    
    def __init__(self, name: str):
        self.name = name
        self.healthy = True
        self.status = "healthy"
        self.message: Optional[str] = None
        self.last_check: Optional[datetime] = None
        self.response_time_ms: Optional[float] = None
        
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "healthy": self.healthy,
            "status": self.status,
            "message": self.message,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "response_time_ms": self.response_time_ms
        }


class HealthChecker:
    """
    Централизованная проверка состояния всех компонентов системы
    """
    
    def __init__(
        self,
        db_manager: Any = None,
        redis_cache: Any = None,
        services: Optional[Dict[str, Any]] = None
    ):
        self.db_manager = db_manager
        self.redis_cache = redis_cache
        self.services = services or {}
        
        self.checks: Dict[str, ComponentHealth] = {}
        self.overall_healthy = True
        self.last_full_check: Optional[datetime] = None
        
    async def check(self) -> Dict[str, Any]:
        """
        Полная проверка состояния системы
        
        Returns:
            Словарь со статусом системы и всех компонентов
        """
        start_time = time.time()
        
        checks_results = []
        
        # Check database
        db_health = await self._check_database()
        checks_results.append(db_health)
        
        # Check Redis cache
        cache_health = await self._check_cache()
        checks_results.append(cache_health)
        
        # Check services
        for service_name, service in self.services.items():
            service_health = await self._check_service(service_name, service)
            checks_results.append(service_health)
            
        # Calculate overall health
        self.overall_healthy = all(check.healthy for check in checks_results)
        self.last_full_check = datetime.now()
        
        # Store results
        for check in checks_results:
            self.checks[check.name] = check
            
        total_time = (time.time() - start_time) * 1000
        
        return {
            "status": "healthy" if self.overall_healthy else "unhealthy",
            "healthy": self.overall_healthy,
            "timestamp": self.last_full_check.isoformat(),
            "response_time_ms": round(total_time, 2),
            "components": [check.to_dict() for check in checks_results],
            "summary": {
                "total_components": len(checks_results),
                "healthy_components": sum(1 for c in checks_results if c.healthy),
                "unhealthy_components": sum(1 for c in checks_results if not c.healthy)
            }
        }
        
    async def _check_database(self) -> ComponentHealth:
        """Проверка состояния базы данных"""
        health = ComponentHealth("database")
        
        if not self.db_manager:
            health.healthy = False
            health.status = "not_configured"
            health.message = "Database manager not configured"
            return health
            
        start_time = time.time()
        
        try:
            # Простой запрос для проверки соединения
            if hasattr(self.db_manager, 'ping'):
                await self.db_manager.ping()
            elif hasattr(self.db_manager, 'execute'):
                await self.db_manager.execute("SELECT 1")
            else:
                # Fallback - проверяем что connection есть
                if not self.db_manager.is_connected():
                    raise Exception("Database not connected")
                    
            health.response_time_ms = round((time.time() - start_time) * 1000, 2)
            health.status = "healthy"
            health.message = "Database connection OK"
            
        except Exception as e:
            health.healthy = False
            health.status = "error"
            health.message = f"Database check failed: {str(e)}"
            logger.error(f"Database health check failed: {e}")
            
        health.last_check = datetime.now()
        return health
        
    async def _check_cache(self) -> ComponentHealth:
        """Проверка состояния Redis cache"""
        health = ComponentHealth("cache")
        
        if not self.redis_cache:
            health.healthy = False
            health.status = "not_configured"
            health.message = "Redis cache not configured"
            return health
            
        start_time = time.time()
        
        try:
            # Ping Redis
            if hasattr(self.redis_cache, 'ping'):
                await self.redis_cache.ping()
            elif hasattr(self.redis_cache, 'get'):
                # Fallback - пробуем get
                await self.redis_cache.get("__health_check__")
            else:
                # Проверяем connection
                if not self.redis_cache.is_connected():
                    raise Exception("Redis not connected")
                    
            health.response_time_ms = round((time.time() - start_time) * 1000, 2)
            health.status = "healthy"
            health.message = "Redis connection OK"
            
        except Exception as e:
            health.healthy = False
            health.status = "error"
            health.message = f"Redis check failed: {str(e)}"
            logger.error(f"Redis health check failed: {e}")
            
        health.last_check = datetime.now()
        return health
        
    async def _check_service(self, name: str, service: Any) -> ComponentHealth:
        """Проверка состояния сервиса"""
        health = ComponentHealth(name)
        
        start_time = time.time()
        
        try:
            # Если у сервиса есть метод health_check, используем его
            if hasattr(service, 'health_check'):
                if asyncio.iscoroutinefunction(service.health_check):
                    result = await service.health_check()
                else:
                    result = service.health_check()
                    
                if isinstance(result, dict):
                    health.healthy = result.get('healthy', True)
                    health.status = result.get('status', 'healthy')
                    health.message = result.get('message')
                elif isinstance(result, bool):
                    health.healthy = result
                    health.status = "healthy" if result else "unhealthy"
                    
            # Если метода нет, считаем что сервис здоров если он существует
            else:
                health.healthy = True
                health.status = "healthy"
                health.message = "Service running (no health check method)"
                
            health.response_time_ms = round((time.time() - start_time) * 1000, 2)
            
        except Exception as e:
            health.healthy = False
            health.status = "error"
            health.message = f"Service check failed: {str(e)}"
            logger.error(f"Service '{name}' health check failed: {e}")
            
        health.last_check = datetime.now()
        return health
        
    async def check_quick(self) -> Dict[str, Any]:
        """
        Быстрая проверка (только критичные компоненты)
        
        Returns:
            Упрощенный статус системы
        """
        checks = []
        
        # Только database и cache
        if self.db_manager:
            db_health = await self._check_database()
            checks.append(db_health)
            
        if self.redis_cache:
            cache_health = await self._check_cache()
            checks.append(cache_health)
            
        overall_healthy = all(check.healthy for check in checks)
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "healthy": overall_healthy,
            "timestamp": datetime.now().isoformat(),
            "components_checked": len(checks)
        }
        
    def get_last_check(self) -> Optional[Dict[str, Any]]:
        """
        Получение результатов последней проверки без повторного выполнения
        
        Returns:
            Результаты последней проверки или None
        """
        if not self.last_full_check:
            return None
            
        return {
            "status": "healthy" if self.overall_healthy else "unhealthy",
            "healthy": self.overall_healthy,
            "timestamp": self.last_full_check.isoformat(),
            "components": [check.to_dict() for check in self.checks.values()],
            "cached": True
        }
        
    async def check_component(self, component_name: str) -> Optional[Dict[str, Any]]:
        """
        Проверка конкретного компонента
        
        Args:
            component_name: Имя компонента для проверки
            
        Returns:
            Статус компонента или None если не найден
        """
        if component_name == "database":
            health = await self._check_database()
            self.checks[component_name] = health
            return health.to_dict()
            
        elif component_name == "cache":
            health = await self._check_cache()
            self.checks[component_name] = health
            return health.to_dict()
            
        elif component_name in self.services:
            service = self.services[component_name]
            health = await self._check_service(component_name, service)
            self.checks[component_name] = health
            return health.to_dict()
            
        return None
        
    def is_healthy(self) -> bool:
        """
        Простая проверка общего состояния системы
        
        Returns:
            True если система здорова
        """
        return self.overall_healthy
        
    def get_unhealthy_components(self) -> List[str]:
        """
        Получение списка нездоровых компонентов
        
        Returns:
            Список имен нездоровых компонентов
        """
        return [
            name for name, check in self.checks.items()
            if not check.healthy
        ]
