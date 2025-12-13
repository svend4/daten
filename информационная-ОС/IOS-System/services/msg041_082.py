# Добавить в ios_core/config.py

class Settings(BaseSettings):
    # ... existing settings ...
    
    # Observability
    jaeger_agent_host: str = "localhost"
    jaeger_agent_port: int = 6831
    sentry_dsn: Optional[str] = None
    service_name: str = "ios-system"
    environment: str = "production"
    version: str = "1.1.0"