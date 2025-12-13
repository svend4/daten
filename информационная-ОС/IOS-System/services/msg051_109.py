"""
FastAPI application - UPDATED with semantic search
"""

# ... (existing imports)
from .routes import semantic_search
from ios_core.tasks.embedding_tasks import embedding_task_manager

# ... (existing code)

# Include semantic search router
app.include_router(
    semantic_search.router,
    prefix="/api/semantic",
    tags=["Semantic Search"]
)

# ... (existing code)

@app.on_event("startup")
async def startup_event():
    """Initialize on startup - UPDATED"""
    logger.info("Starting IOS API Server v1.1.0...")
    
    # ... (existing startup code)
    
    # Start embedding task manager
    import asyncio
    asyncio.create_task(embedding_task_manager.start())
    logger.info("✓ Embedding task manager started")
    
    logger.info(f"✓ IOS API Server started on {settings.api_prefix}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown - UPDATED"""
    logger.info("Shutting down IOS API Server...")
    
    # Stop embedding tasks
    embedding_task_manager.stop()
    
    # ... (existing shutdown code)