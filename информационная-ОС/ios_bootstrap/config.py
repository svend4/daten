"""
Configuration module - wrapper around existing IOS-System settings
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""

    # Application
    app_name: str = "IOS Search System"
    version: str = "0.1.0"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    api_prefix: str = Field(default="/api", env="API_PREFIX")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://ios_user:ios_password_change_me@localhost:5432/ios_db",
        env="DATABASE_URL"
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )

    # Elasticsearch (Optional)
    elasticsearch_url: str | None = Field(
        default=None,
        env="ELASTICSEARCH_URL"
    )

    # Security
    secret_key: str = Field(
        default="change-this-in-production",
        env="SECRET_KEY"
    )
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )

    # File paths
    ios_root_path: str = Field(default="/data/ios-root", env="IOS_ROOT_PATH")
    upload_dir: str = Field(default="/data/uploads", env="UPLOAD_DIR")
    export_dir: str = Field(default="/data/exports", env="EXPORT_DIR")
    whoosh_index_dir: str = Field(default="/data/whoosh-index", env="WHOOSH_INDEX_DIR")

    # Features (enable/disable components)
    enable_elasticsearch: bool = Field(default=False, env="ENABLE_ELASTICSEARCH")
    enable_ml: bool = Field(default=False, env="ENABLE_ML")
    enable_gpt: bool = Field(default=False, env="ENABLE_GPT")
    enable_monitoring: bool = Field(default=False, env="ENABLE_MONITORING")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance"""
    return settings
