"""
FastAPI application - UPDATED with security features
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging

from ios_core.config import settings
from ios_core.observability import setup_tracing, setup_logging, setup_metrics
from ios_core.security.monitoring import security_monitor

# Import enhanced routes
from .routes import (
    documents, search, domains, knowledge_graph, contexts,
    auth, auth_enhanced, audit, compliance, metrics
)
from .middleware.observability import ObservabilityMiddleware
from .middleware.audit_middleware import AuditMiddleware
from .database import engine, Base

# Setup observability
setup_logging(log_level="INFO", json_format=True)
setup_tracing("ios-api")
setup_metrics()

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="IOS System API",
    description="Information Operating System - Enhanced Security",
    version="1.1.0",
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

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(auth_enhanced.router, prefix="/api/auth", tags=["Authentication - Enhanced"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit Logs"])
app.include_router(compliance.router, prefix="/api/compliance", tags=["Compliance"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(domains.router, prefix="/api/domains", tags=["Domains"])
app.include_router(knowledge_graph.router, prefix="/api/graph", tags=["Knowledge Graph"])
app.include_router(contexts.router, prefix="/api/contexts", tags=["Contexts"])
app.include_router(metrics.router, prefix="/api", tags=["Metrics"])


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("Starting IOS API Server v1.1.0...")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("✓ Database initialized")
    
    # Start security monitoring
    import asyncio
    asyncio.create_task(security_monitor.start_monitoring())
    logger.info("✓ Security monitoring started")
    
    logger.info(f"✓ IOS API Server started on {settings.api_prefix}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down IOS API Server...")
    
    # Stop security monitoring
    security_monitor.stop_monitoring()
    
    await engine.dispose()
    logger.info("✓ Shutdown complete")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.1.0",
        "features": {
            "audit_logging": True,
            "mfa": True,
            "security_monitoring": True,
            "compliance_reporting": True
        }
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "IOS System API v1.1.0",
        "version": "1.1.0",
        "docs": "/api/docs",
        "security": "Enhanced"
    }