"""
Configuration Settings - Настройки IOS System
"""
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """
    Настройки приложения
    Загружаются из переменных окружения или .env файла
    """
    
    # Application
    app_name: str = Field(default="IOS System", description="Название приложения")
    version: str = Field(default="1.0.0", description="Версия")
    debug: bool = Field(default=False, description="Debug режим")
    environment: str = Field(default="production", description="Окружение: development, staging, production")
    
    # Server
    host: str = Field(default="0.0.0.0", description="Host для сервера")
    port: int = Field(default=8000, description="Port для сервера")
    workers: int = Field(default=4, description="Количество worker процессов")
    log_level: str = Field(default="INFO", description="Уровень логирования")
    
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://ios_user:ios_password@localhost:5432/ios_db",
        description="URL подключения к PostgreSQL"
    )
    database_pool_size: int = Field(default=20, description="Размер connection pool")
    database_max_overflow: int = Field(default=10, description="Максимальное переполнение pool")
    database_pool_timeout: int = Field(default=30, description="Timeout для pool")
    
    # Redis Cache
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    redis_max_connections: int = Field(default=50, description="Max Redis connections")
    
    # Elasticsearch
    elasticsearch_url: str = Field(
        default="http://localhost:9200",
        description="Elasticsearch URL"
    )
    elasticsearch_username: Optional[str] = Field(default=None, description="ES username")
    elasticsearch_password: Optional[str] = Field(default=None, description="ES password")
    elasticsearch_index_prefix: str = Field(default="ios", description="Префикс для индексов")
    
    # Qdrant Vector Database
    qdrant_url: str = Field(
        default="http://localhost:6333",
        description="Qdrant URL"
    )
    qdrant_collection_name: str = Field(default="ios_documents", description="Имя коллекции")
    qdrant_vector_size: int = Field(default=384, description="Размер векторов")
    
    # Security
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key для JWT и шифрования"
    )
    algorithm: str = Field(default="HS256", description="Алгоритм JWT")
    access_token_expire_minutes: int = Field(default=30, description="Время жизни access token (минуты)")
    refresh_token_expire_days: int = Field(default=7, description="Время жизни refresh token (дни)")
    
    # CORS
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Разрешенные origins для CORS"
    )
    allow_credentials: bool = Field(default=True, description="Allow credentials")
    allowed_methods: List[str] = Field(default=["*"], description="Allowed HTTP methods")
    allowed_headers: List[str] = Field(default=["*"], description="Allowed headers")
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, description="Включить rate limiting")
    rate_limit_requests: int = Field(default=100, description="Количество запросов")
    rate_limit_window_seconds: int = Field(default=60, description="Окно времени (секунды)")
    
    # ML Models
    classifier_model_path: str = Field(
        default="models/classifier",
        description="Путь к модели классификатора"
    )
    embedding_model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Название embedding модели"
    )
    ner_model_name: str = Field(
        default="dbmdz/bert-large-cased-finetuned-conll03-english",
        description="Название NER модели"
    )
    
    # File Storage
    upload_dir: Path = Field(default=Path("uploads"), description="Директория для загрузок")
    max_upload_size_mb: int = Field(default=100, description="Максимальный размер файла (MB)")
    allowed_extensions: List[str] = Field(
        default=[".pdf", ".docx", ".txt", ".md", ".html"],
        description="Разрешенные расширения файлов"
    )
    
    # Monitoring
    prometheus_enabled: bool = Field(default=True, description="Включить Prometheus metrics")
    prometheus_port: int = Field(default=9090, description="Prometheus metrics port")
    
    # Logging
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Формат логов"
    )
    log_file: Optional[str] = Field(default=None, description="Файл для логов")
    log_rotation: str = Field(default="1 day", description="Ротация логов")
    log_retention: str = Field(default="30 days", description="Хранение логов")
    
    # Background Tasks
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        description="Celery broker URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2",
        description="Celery result backend"
    )
    
    # AI Services
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    
    # Features Flags
    feature_knowledge_graph: bool = Field(default=True, description="Включить Knowledge Graph")
    feature_ai_summarization: bool = Field(default=True, description="Включить AI суммаризацию")
    feature_semantic_search: bool = Field(default=True, description="Включить semantic search")
    feature_multi_language: bool = Field(default=True, description="Включить мультиязычность")
    
    @validator('upload_dir')
    def create_upload_dir(cls, v):
        """Создание директории для загрузок если не существует"""
        if not v.exists():
            v.mkdir(parents=True, exist_ok=True)
        return v
        
    @validator('environment')
    def validate_environment(cls, v):
        """Валидация environment"""
        allowed = ['development', 'staging', 'production']
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v
        
    @validator('log_level')
    def validate_log_level(cls, v):
        """Валидация log level"""
        allowed = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v = v.upper()
        if v not in allowed:
            raise ValueError(f"Log level must be one of {allowed}")
        return v
        
    def is_development(self) -> bool:
        """Проверка development режима"""
        return self.environment == 'development' or self.debug
        
    def is_production(self) -> bool:
        """Проверка production режима"""
        return self.environment == 'production' and not self.debug
        
    def get_database_url(self, hide_password: bool = False) -> str:
        """
        Получение database URL
        
        Args:
            hide_password: Скрыть пароль в URL
            
        Returns:
            Database URL
        """
        if hide_password and '://' in self.database_url:
            parts = self.database_url.split('://')
            if '@' in parts[1]:
                user_pass, rest = parts[1].split('@')
                if ':' in user_pass:
                    user = user_pass.split(':')[0]
                    return f"{parts[0]}://{user}:****@{rest}"
        return self.database_url
        
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = False
        
    def model_dump_safe(self) -> dict:
        """
        Dump настроек без чувствительной информации
        
        Returns:
            Словарь с настройками
        """
        data = self.model_dump()
        
        # Скрываем чувствительные данные
        sensitive_fields = [
            'secret_key',
            'database_url',
            'redis_password',
            'elasticsearch_password',
            'openai_api_key',
            'anthropic_api_key'
        ]
        
        for field in sensitive_fields:
            if field in data and data[field]:
                data[field] = '****'
                
        return data
        
    def __repr__(self) -> str:
        return f"Settings(environment={self.environment}, debug={self.debug})"


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Получение экземпляра настроек (singleton)
    
    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """
    Перезагрузка настроек
    
    Returns:
        Новый Settings instance
    """
    global _settings
    _settings = Settings()
    return _settings
