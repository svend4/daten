"""
Configuration management for IOS System
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn, RedisDsn


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application
    app_name: str = "IOS System"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Paths
    ios_root_path: str = Field(default="/data/ios-root")
    upload_dir: str = Field(default="/data/uploads")
    export_dir: str = Field(default="/data/exports")
    
    # Database
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://ios_user:ios_password@localhost:5432/ios_db"
    )
    
    # Redis
    redis_url: RedisDsn = Field(default="redis://localhost:6379/0")
    
    # Security
    secret_key: str = Field(default="change-this-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    
    # API
    api_prefix: str = "/api"
    cors_origins: list[str] = ["*"]
    
    # Limits
    max_upload_size: int = 100 * 1024 * 1024  # 100MB
    rate_limit_per_minute: int = 60
    
    # Search
    search_index_path: str = Field(default="/data/search-indexes")
    
    # Features
    enable_websocket: bool = True
    enable_analytics: bool = True
    
    class Config:
        env_prefix = "IOS_"


# Global settings instance
settings = Settings()