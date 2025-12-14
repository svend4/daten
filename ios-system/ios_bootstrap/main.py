"""
Main FastAPI Application - Bootstrap Entry Point

Этот файл импортирует и использует СУЩЕСТВУЮЩИЙ код из IOS-System/
Не переписываем - только интегрируем!
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import sys
from pathlib import Path

# Добавить IOS-System в Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "IOS-System"))

from ios_bootstrap.config import settings

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Information Operating System - Incremental Bootstrap",
    version=settings.version,
    docs_url=f"{settings.api_prefix}/docs",
    redoc_url=f"{settings.api_prefix}/redoc",
    openapi_url=f"{settings.api_prefix}/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info(f"Starting {settings.app_name} v{settings.version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")

    # TODO: Initialize database connection
    # TODO: Initialize Redis connection
    # TODO: Initialize Whoosh index

    logger.info("✓ Startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down...")

    # TODO: Close database connection
    # TODO: Close Redis connection

    logger.info("✓ Shutdown complete")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.version,
        "environment": settings.environment,
        "features": {
            "elasticsearch": settings.enable_elasticsearch,
            "ml": settings.enable_ml,
            "gpt": settings.enable_gpt,
            "monitoring": settings.enable_monitoring,
        }
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"{settings.app_name} v{settings.version}",
        "status": "running",
        "docs": f"{settings.api_prefix}/docs",
        "health": "/health"
    }


@app.get(f"{settings.api_prefix}/status")
async def api_status():
    """API status endpoint"""
    return {
        "api_version": settings.version,
        "endpoints": {
            "health": "/health",
            "docs": f"{settings.api_prefix}/docs",
            "redoc": f"{settings.api_prefix}/redoc",
        },
        "database": {
            "connected": False,  # TODO: Check database connection
            "url": settings.database_url.split("@")[-1] if "@" in settings.database_url else "not configured"
        },
        "redis": {
            "connected": False,  # TODO: Check Redis connection
            "url": settings.redis_url
        }
    }


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc) if settings.debug else "An error occurred",
            "type": type(exc).__name__
        }
    )


# ============================================================================
# PHASE 1: Basic Endpoints (Uncomment when ready)
# ============================================================================

# TODO: Import and include existing routers from IOS-System/
# from IOS-System.api import ...
# app.include_router(...)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
