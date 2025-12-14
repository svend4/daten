"""
FastAPI application - main entry point
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time

from ios_core.config import settings
from .routes import documents, search, domains, knowledge_graph, contexts, auth
from .middleware.logging import LoggingMiddleware
from .middleware.rate_limit import RateLimitMiddleware
from .database import engine, Base

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="IOS System API",
    description="Information Operating System - Knowledge Management API",
    version="0.1.0",
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

# Custom middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(domains.router, prefix="/api/domains", tags=["Domains"])
app.include_router(knowledge_graph.router, prefix="/api/graph", tags=["Knowledge Graph"])
app.include_router(contexts.router, prefix="/api/contexts", tags=["Contexts"])


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("Starting IOS API Server...")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("✓ Database initialized")
    logger.info(f"✓ IOS API Server started on {settings.api_prefix}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down IOS API Server...")
    await engine.dispose()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": time.time()
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "IOS System API",
        "version": "0.1.0",
        "docs": "/api/docs"
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