"""
FastAPI application - UPDATED with neural search
"""

# ... (existing imports)
from .routes import neural_search

# ... (existing code)

# Include neural search router
app.include_router(
    neural_search.router,
    prefix="/api/search/neural",
    tags=["Neural Search"]
)

# ... (rest of existing code)