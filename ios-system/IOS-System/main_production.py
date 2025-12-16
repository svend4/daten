"""
IOS System - Main Entry Point
Главный файл системы, объединяющий все компоненты
"""
import asyncio
import logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Core components
from core.ios_root import IOSRoot
from core.event_bus import EventBus
from core.service_registry import ServiceRegistry
from core.config import Settings

# Services
from services.document_service import DocumentService
from services.search_service import SearchService
from services.knowledge_graph_service import KnowledgeGraphService
from services.classifier_service import ClassifierService
from services.context_service import ContextService

# API routers
from api.routes import (
    auth_router,
    documents_router,
    search_router,
    graph_router,
    admin_router,
    ai_router,
)

# Middleware
from middleware.error_handler import ErrorHandlerMiddleware
from middleware.request_logger import RequestLoggerMiddleware
from middleware.rate_limiter import RateLimiterMiddleware
from middleware.security_headers import SecurityHeadersMiddleware

# Monitoring
from monitoring.metrics import MetricsCollector
from monitoring.health_check import HealthChecker

# Database
from database.connection import DatabaseManager

# Cache
from cache.redis_client import RedisCache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IOSApplication:
    """
    Главное приложение IOS System
    Управляет жизненным циклом всех компонентов
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.app: Optional[FastAPI] = None
        
        # Core components
        self.ios_root: Optional[IOSRoot] = None
        self.event_bus: Optional[EventBus] = None
        self.service_registry: Optional[ServiceRegistry] = None
        
        # Infrastructure
        self.db_manager: Optional[DatabaseManager] = None
        self.redis_cache: Optional[RedisCache] = None
        
        # Services
        self.document_service: Optional[DocumentService] = None
        self.search_service: Optional[SearchService] = None
        self.knowledge_graph_service: Optional[KnowledgeGraphService] = None
        self.classifier_service: Optional[ClassifierService] = None
        self.context_service: Optional[ContextService] = None
        
        # Monitoring
        self.metrics: Optional[MetricsCollector] = None
        self.health_checker: Optional[HealthChecker] = None
        
    async def initialize(self):
        """Инициализация всех компонентов системы"""
        logger.info("Starting IOS System initialization...")
        
        try:
            # 1. Initialize core components
            logger.info("Initializing core components...")
            self.event_bus = EventBus()
            self.service_registry = ServiceRegistry()
            
            # 2. Initialize infrastructure
            logger.info("Initializing infrastructure...")
            self.db_manager = DatabaseManager(self.settings.database_url)
            await self.db_manager.connect()
            
            self.redis_cache = RedisCache(
                host=self.settings.redis_host,
                port=self.settings.redis_port,
                db=self.settings.redis_db
            )
            await self.redis_cache.connect()
            
            # 3. Initialize IOS Root
            logger.info("Initializing IOS Root...")
            self.ios_root = IOSRoot(
                event_bus=self.event_bus,
                db_manager=self.db_manager,
                cache=self.redis_cache
            )
            await self.ios_root.initialize()
            
            # 4. Initialize services
            logger.info("Initializing services...")
            await self._initialize_services()
            
            # 5. Register services
            logger.info("Registering services...")
            self._register_services()
            
            # 6. Initialize monitoring
            logger.info("Initializing monitoring...")
            self.metrics = MetricsCollector()
            self.health_checker = HealthChecker(
                db_manager=self.db_manager,
                redis_cache=self.redis_cache,
                services=self.service_registry.get_all_services()
            )
            
            # 7. Subscribe to events
            logger.info("Setting up event subscriptions...")
            self._setup_event_subscriptions()
            
            logger.info("✅ IOS System initialization completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize IOS System: {e}")
            await self.shutdown()
            raise
            
    async def _initialize_services(self):
        """Инициализация всех сервисов"""
        # Document Service
        self.document_service = DocumentService(
            db_manager=self.db_manager,
            cache=self.redis_cache,
            event_bus=self.event_bus
        )
        await self.document_service.initialize()
        
        # Search Service
        self.search_service = SearchService(
            elasticsearch_url=self.settings.elasticsearch_url,
            qdrant_url=self.settings.qdrant_url,
            cache=self.redis_cache,
            event_bus=self.event_bus
        )
        await self.search_service.initialize()
        
        # Knowledge Graph Service
        self.knowledge_graph_service = KnowledgeGraphService(
            db_manager=self.db_manager,
            event_bus=self.event_bus
        )
        await self.knowledge_graph_service.initialize()
        
        # Classifier Service
        self.classifier_service = ClassifierService(
            model_path=self.settings.classifier_model_path,
            cache=self.redis_cache,
            event_bus=self.event_bus
        )
        await self.classifier_service.initialize()
        
        # Context Service
        self.context_service = ContextService(
            db_manager=self.db_manager,
            cache=self.redis_cache,
            event_bus=self.event_bus
        )
        await self.context_service.initialize()
        
    def _register_services(self):
        """Регистрация всех сервисов в Service Registry"""
        self.service_registry.register('document_service', self.document_service)
        self.service_registry.register('search_service', self.search_service)
        self.service_registry.register('knowledge_graph_service', self.knowledge_graph_service)
        self.service_registry.register('classifier_service', self.classifier_service)
        self.service_registry.register('context_service', self.context_service)
        
    def _setup_event_subscriptions(self):
        """Настройка подписок на события между сервисами"""
        # Document events
        self.event_bus.subscribe('document.created', self.search_service.on_document_created)
        self.event_bus.subscribe('document.created', self.classifier_service.on_document_created)
        self.event_bus.subscribe('document.created', self.knowledge_graph_service.on_document_created)
        
        self.event_bus.subscribe('document.updated', self.search_service.on_document_updated)
        self.event_bus.subscribe('document.deleted', self.search_service.on_document_deleted)
        
        # Search events
        self.event_bus.subscribe('search.performed', self.metrics.on_search_performed)
        self.event_bus.subscribe('search.failed', self.metrics.on_search_failed)
        
        # Classification events
        self.event_bus.subscribe('classification.completed', self.metrics.on_classification_completed)
        
        # Knowledge graph events
        self.event_bus.subscribe('entity.extracted', self.metrics.on_entity_extracted)
        self.event_bus.subscribe('relation.extracted', self.metrics.on_relation_extracted)
        
    def create_app(self) -> FastAPI:
        """Создание FastAPI приложения"""
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            await self.initialize()
            yield
            # Shutdown
            await self.shutdown()
        
        self.app = FastAPI(
            title="IOS System API",
            description="Information Operating System - API для работы с документами и знаниями",
            version="1.0.0",
            lifespan=lifespan
        )
        
        # Add middleware
        self._setup_middleware()
        
        # Add routers
        self._setup_routers()
        
        # Add exception handlers
        self._setup_exception_handlers()
        
        return self.app
        
    def _setup_middleware(self):
        """Настройка middleware"""
        # CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.settings.allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Custom middleware
        self.app.add_middleware(SecurityHeadersMiddleware)
        self.app.add_middleware(RateLimiterMiddleware, redis_cache=self.redis_cache)
        self.app.add_middleware(RequestLoggerMiddleware)
        self.app.add_middleware(ErrorHandlerMiddleware)
        
    def _setup_routers(self):
        """Настройка роутеров API"""
        # Inject dependencies into routers
        self.app.include_router(
            auth_router,
            prefix="/api/v1/auth",
            tags=["Authentication"]
        )
        
        self.app.include_router(
            documents_router,
            prefix="/api/v1/documents",
            tags=["Documents"],
            dependencies=[self.document_service]
        )
        
        self.app.include_router(
            search_router,
            prefix="/api/v1/search",
            tags=["Search"],
            dependencies=[self.search_service]
        )
        
        self.app.include_router(
            graph_router,
            prefix="/api/v1/graph",
            tags=["Knowledge Graph"],
            dependencies=[self.knowledge_graph_service]
        )
        
        self.app.include_router(
            ai_router,
            prefix="/api/v1/ai",
            tags=["AI/ML"]
        )
        
        self.app.include_router(
            admin_router,
            prefix="/api/v1/admin",
            tags=["Admin"]
        )
        
        # Health check endpoint
        @self.app.get("/health")
        async def health_check():
            return await self.health_checker.check()
            
        # Metrics endpoint
        @self.app.get("/metrics")
        async def metrics():
            return self.metrics.get_metrics()
            
        # Root endpoint
        @self.app.get("/")
        async def root():
            return {
                "name": "IOS System",
                "version": "1.0.0",
                "status": "running",
                "docs_url": "/docs",
                "health_url": "/health"
            }
            
    def _setup_exception_handlers(self):
        """Настройка обработчиков исключений"""
        
        @self.app.exception_handler(Exception)
        async def global_exception_handler(request: Request, exc: Exception):
            logger.error(f"Unhandled exception: {exc}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": str(exc) if self.settings.debug else "An error occurred"
                }
            )
            
    async def shutdown(self):
        """Graceful shutdown всех компонентов"""
        logger.info("Shutting down IOS System...")
        
        try:
            # Shutdown services
            if self.document_service:
                await self.document_service.shutdown()
            if self.search_service:
                await self.search_service.shutdown()
            if self.knowledge_graph_service:
                await self.knowledge_graph_service.shutdown()
            if self.classifier_service:
                await self.classifier_service.shutdown()
            if self.context_service:
                await self.context_service.shutdown()
                
            # Shutdown infrastructure
            if self.redis_cache:
                await self.redis_cache.disconnect()
            if self.db_manager:
                await self.db_manager.disconnect()
                
            logger.info("✅ IOS System shutdown completed")
            
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")
            raise


def create_application(settings: Optional[Settings] = None) -> FastAPI:
    """
    Factory function для создания приложения
    """
    ios_app = IOSApplication(settings)
    return ios_app.create_app()


def main():
    """
    Main entry point для запуска приложения
    """
    settings = Settings()
    app = create_application(settings)
    
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        access_log=True,
        reload=settings.debug
    )


if __name__ == "__main__":
    main()
