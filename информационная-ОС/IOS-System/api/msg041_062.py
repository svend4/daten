# Обновить api/main.py

from ios_core.observability import setup_tracing, setup_logging, setup_metrics
from api.middleware.observability import ObservabilityMiddleware

# Setup observability
setup_logging(log_level="INFO", json_format=True)
setup_tracing("ios-api")
setup_metrics()

# Add middleware
app.add_middleware(ObservabilityMiddleware)

# Add metrics endpoint
from api.routes.metrics import router as metrics_router
app.include_router(metrics_router)

# Sentry integration (optional)
if settings.sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=0.1,
        integrations=[FastApiIntegration()]
    )