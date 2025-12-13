"""
FastAPI application - FINAL VERSION
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from ios_core.config import settings
from ios_core.observability import setup_tracing, setup_logging, setup_metrics
from ios_core.security.monitoring import security_monitor
from ios_core.tasks.embedding_tasks import embedding_task_manager
from ios_core.optimization.cache_manager import cache_manager

# Import all routes
from .routes import (
    documents, search, domains, knowledge_graph, contexts,
    auth, auth_enhanced, audit, compliance, metrics,
    semantic_search, neural_search, gpt_api, i18n_api
)
from .middleware.observability import ObservabilityMiddleware
from .middleware.audit_middleware import AuditMiddleware
from ..database import engine, Base

# Setup observability
setup_logging(log_level="INFO", json_format=True)
setup_tracing("ios-api")
setup_metrics()

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="IOS System API",
    description="Information Operating System - AI-Powered Document Management",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware
app.add_middleware(AuditMiddleware)
app.add_middleware(ObservabilityMiddleware)

# Include all routers
routers = [
    (auth.router, "/api/auth", ["Authentication"]),
    (auth_enhanced.router, "/api/auth", ["Authentication - Enhanced"]),
    (audit.router, "/api/audit", ["Audit Logs"]),
    (compliance.router, "/api/compliance", ["Compliance"]),
    (documents.router, "/api/documents", ["Documents"]),
    (search.router, "/api/search", ["Search"]),
    (semantic_search.router, "/api/semantic", ["Semantic Search"]),
    (neural_search.router, "/api/search/neural", ["Neural Search"]),
    (gpt_api.router, "/api/gpt", ["GPT / AI Generation"]),
    (i18n_api.router, "/api/i18n", ["Internationalization"]),
    (domains.router, "/api/domains", ["Domains"]),
    (knowledge_graph.router, "/api/graph", ["Knowledge Graph"]),
    (contexts.router, "/api/contexts", ["Contexts"]),
    (metrics.router, "/api", ["Metrics"]),
]

for router, prefix, tags in routers:
    app.include_router(router, prefix=prefix, tags=tags)


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("Starting IOS API Server v2.0.0...")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("✓ Database initialized")
    
    # Initialize cache
    await cache_manager.initialize()
    logger.info("✓ Cache manager initialized")
    
    # Start background tasks
    import asyncio
    asyncio.create_task(security_monitor.start_monitoring())
    asyncio.create_task(embedding_task_manager.start())
    
    logger.info("✓ Background tasks started")
    logger.info(f"✓ IOS API Server v2.0.0 ready on {settings.api_prefix}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down IOS API Server...")
    
    # Stop background tasks
    security_monitor.stop_monitoring()
    embedding_task_manager.stop()
    
    await engine.dispose()
    logger.info("✓ Shutdown complete")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "features": {
            "neural_search": True,
            "gpt_generation": True,
            "multi_language": True,
            "audit_logging": True,
            "mfa": True,
            "security_monitoring": True
        },
        "cache_stats": cache_manager.get_stats()
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "IOS System API v2.0.0 - AI-Powered",
        "version": "2.0.0",
        "docs": "/api/docs",
        "features": [
            "BERT Semantic Search",
            "GPT-4 Document Generation",
            "Multi-language Support (de/ru/en)",
            "Neural Search with Hybrid Ranking",
            "RAG-based Q&A System"
        ]
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An error occurred"
        }
    )