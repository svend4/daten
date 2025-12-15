"""
Service Registry - Централизованное управление сервисами
"""
from typing import Dict, Any, Optional, List
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Статусы сервиса"""
    INITIALIZED = "initialized"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class ServiceInfo:
    """Информация о сервисе"""
    
    def __init__(self, name: str, service: Any, version: str = "1.0.0"):
        self.name = name
        self.service = service
        self.version = version
        self.status = ServiceStatus.INITIALIZED
        self.error: Optional[str] = None
        
    def set_status(self, status: ServiceStatus, error: Optional[str] = None):
        self.status = status
        self.error = error
        
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "version": self.version,
            "status": self.status.value,
            "error": self.error,
            "type": type(self.service).__name__
        }


class ServiceRegistry:
    """
    Реестр всех сервисов системы
    Управляет жизненным циклом и взаимодействием сервисов
    """
    
    def __init__(self):
        self._services: Dict[str, ServiceInfo] = {}
        self._dependencies: Dict[str, List[str]] = {}
        logger.info("Service Registry initialized")
        
    def register(
        self,
        name: str,
        service: Any,
        version: str = "1.0.0",
        depends_on: Optional[List[str]] = None
    ) -> None:
        """
        Регистрация сервиса
        
        Args:
            name: Уникальное имя сервиса
            service: Экземпляр сервиса
            version: Версия сервиса
            depends_on: Список зависимостей (имена других сервисов)
        """
        if name in self._services:
            logger.warning(f"Service '{name}' already registered, updating...")
            
        service_info = ServiceInfo(name, service, version)
        self._services[name] = service_info
        
        if depends_on:
            self._dependencies[name] = depends_on
            
        logger.info(f"✅ Service registered: {name} v{version}")
        
    def unregister(self, name: str) -> bool:
        """
        Удаление сервиса из реестра
        
        Args:
            name: Имя сервиса
            
        Returns:
            True если сервис был удален, False если не найден
        """
        if name in self._services:
            del self._services[name]
            if name in self._dependencies:
                del self._dependencies[name]
            logger.info(f"Service unregistered: {name}")
            return True
        return False
        
    def get(self, name: str) -> Optional[Any]:
        """
        Получение сервиса по имени
        
        Args:
            name: Имя сервиса
            
        Returns:
            Экземпляр сервиса или None
        """
        service_info = self._services.get(name)
        return service_info.service if service_info else None
        
    def get_info(self, name: str) -> Optional[ServiceInfo]:
        """
        Получение информации о сервисе
        
        Args:
            name: Имя сервиса
            
        Returns:
            ServiceInfo или None
        """
        return self._services.get(name)
        
    def get_all_services(self) -> Dict[str, Any]:
        """
        Получение всех зарегистрированных сервисов
        
        Returns:
            Словарь {имя: сервис}
        """
        return {name: info.service for name, info in self._services.items()}
        
    def get_all_info(self) -> Dict[str, Dict]:
        """
        Получение информации о всех сервисах
        
        Returns:
            Словарь {имя: информация}
        """
        return {name: info.to_dict() for name, info in self._services.items()}
        
    def list_services(self) -> List[str]:
        """
        Список имен всех зарегистрированных сервисов
        
        Returns:
            Список имен сервисов
        """
        return list(self._services.keys())
        
    def update_status(self, name: str, status: ServiceStatus, error: Optional[str] = None):
        """
        Обновление статуса сервиса
        
        Args:
            name: Имя сервиса
            status: Новый статус
            error: Сообщение об ошибке (если есть)
        """
        if name in self._services:
            self._services[name].set_status(status, error)
            logger.info(f"Service '{name}' status updated: {status.value}")
        else:
            logger.warning(f"Cannot update status: service '{name}' not found")
            
    def check_dependencies(self, name: str) -> bool:
        """
        Проверка доступности всех зависимостей сервиса
        
        Args:
            name: Имя сервиса
            
        Returns:
            True если все зависимости доступны
        """
        if name not in self._dependencies:
            return True
            
        dependencies = self._dependencies[name]
        for dep in dependencies:
            if dep not in self._services:
                logger.error(f"Service '{name}' dependency '{dep}' not found")
                return False
                
            dep_info = self._services[dep]
            if dep_info.status == ServiceStatus.ERROR:
                logger.error(f"Service '{name}' dependency '{dep}' is in error state")
                return False
                
        return True
        
    def get_service_health(self) -> Dict[str, Dict]:
        """
        Получение статуса здоровья всех сервисов
        
        Returns:
            Словарь со статусами всех сервисов
        """
        health = {}
        for name, info in self._services.items():
            health[name] = {
                "status": info.status.value,
                "healthy": info.status != ServiceStatus.ERROR,
                "error": info.error,
                "dependencies_ok": self.check_dependencies(name)
            }
        return health
        
    async def initialize_all(self) -> bool:
        """
        Инициализация всех сервисов в правильном порядке
        (с учетом зависимостей)
        
        Returns:
            True если все сервисы инициализированы успешно
        """
        logger.info("Initializing all services...")
        
        # Топологическая сортировка для правильного порядка инициализации
        initialized = set()
        success = True
        
        def can_initialize(service_name: str) -> bool:
            """Проверка возможности инициализации сервиса"""
            if service_name not in self._dependencies:
                return True
            return all(dep in initialized for dep in self._dependencies[service_name])
            
        while len(initialized) < len(self._services):
            progress_made = False
            
            for name, info in self._services.items():
                if name in initialized:
                    continue
                    
                if can_initialize(name):
                    try:
                        logger.info(f"Initializing service: {name}")
                        
                        # Если у сервиса есть метод initialize, вызываем его
                        if hasattr(info.service, 'initialize'):
                            if asyncio.iscoroutinefunction(info.service.initialize):
                                await info.service.initialize()
                            else:
                                info.service.initialize()
                                
                        self.update_status(name, ServiceStatus.RUNNING)
                        initialized.add(name)
                        progress_made = True
                        logger.info(f"✅ Service initialized: {name}")
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to initialize service '{name}': {e}")
                        self.update_status(name, ServiceStatus.ERROR, str(e))
                        success = False
                        
            if not progress_made:
                # Циклические зависимости или ошибки
                remaining = set(self._services.keys()) - initialized
                logger.error(f"Cannot initialize services (circular dependency?): {remaining}")
                success = False
                break
                
        return success
        
    async def shutdown_all(self):
        """
        Graceful shutdown всех сервисов
        """
        logger.info("Shutting down all services...")
        
        # Останавливаем в обратном порядке
        for name in reversed(self.list_services()):
            try:
                info = self._services[name]
                logger.info(f"Shutting down service: {name}")
                
                # Если у сервиса есть метод shutdown, вызываем его
                if hasattr(info.service, 'shutdown'):
                    if asyncio.iscoroutinefunction(info.service.shutdown):
                        await info.service.shutdown()
                    else:
                        info.service.shutdown()
                        
                self.update_status(name, ServiceStatus.STOPPED)
                logger.info(f"✅ Service stopped: {name}")
                
            except Exception as e:
                logger.error(f"❌ Error shutting down service '{name}': {e}")
                
    def __contains__(self, name: str) -> bool:
        """Проверка наличия сервиса"""
        return name in self._services
        
    def __len__(self) -> int:
        """Количество зарегистрированных сервисов"""
        return len(self._services)
        
    def __repr__(self) -> str:
        return f"ServiceRegistry(services={len(self._services)})"
