"""
FastAPI application - UPDATED with GPT routes
"""

# ... (existing imports)
from .routes import gpt_api

# ... (existing code)

# Include GPT router
app.include_router(
    gpt_api.router,
    prefix="/api/gpt",
    tags=["GPT / AI Generation"]
)

# ... (rest of existing code)