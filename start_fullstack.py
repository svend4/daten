#!/usr/bin/env python3
"""
Start Full IOS System (WITHOUT bootstrap)
Tests complete architecture with all services
"""
import os
import sys
from pathlib import Path

# Add IOS-System to Python path
ios_system_path = Path(__file__).parent / "IOS-System"
sys.path.insert(0, str(ios_system_path))

# Set environment defaults if not provided
os.environ.setdefault("ENVIRONMENT", "production")
os.environ.setdefault("LOG_LEVEL", "INFO")
os.environ.setdefault("API_PREFIX", "/api")
os.environ.setdefault("FRONTEND_DIST", "/app/frontend-dist")

# Optional services (disabled by default for minimal startup)
os.environ.setdefault("ENABLE_ELASTICSEARCH", "false")
os.environ.setdefault("ENABLE_ML", "false")
os.environ.setdefault("ENABLE_GPT", "false")
os.environ.setdefault("ENABLE_MONITORING", "false")

# Database (use Railway provided URL or fallback)
if "DATABASE_URL" not in os.environ:
    print("⚠️  WARNING: DATABASE_URL not set, using default")
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://ios_user:ios_password@localhost:5432/ios_db"

# Redis (use Railway provided URL or fallback)
if "REDIS_URL" not in os.environ:
    print("⚠️  WARNING: REDIS_URL not set, using default")
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"

print("=" * 60)
print("Starting IOS System - Full Architecture")
print("=" * 60)
print(f"Environment: {os.getenv('ENVIRONMENT')}")
print(f"Database: {os.getenv('DATABASE_URL', 'N/A').split('@')[-1]}")
print(f"Redis: {os.getenv('REDIS_URL', 'N/A')}")
print(f"Frontend: {os.getenv('FRONTEND_DIST')}")
print(f"Features:")
print(f"  - Elasticsearch: {os.getenv('ENABLE_ELASTICSEARCH')}")
print(f"  - ML: {os.getenv('ENABLE_ML')}")
print(f"  - GPT: {os.getenv('ENABLE_GPT')}")
print(f"  - Monitoring: {os.getenv('ENABLE_MONITORING')}")
print("=" * 60)

# Import and run
try:
    print("✓ Importing main_production app...")

    # Import the app directly (sys.path is already configured)
    from main_production import app

    print("✓ Starting uvicorn...")
    import uvicorn

    # Get port from environment (Railway sets PORT)
    port = int(os.environ.get("PORT", 8080))

    # Run uvicorn with the app object directly
    # We import the app ourselves so sys.path modifications are preserved
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
        access_log=True,
        reload=False
    )

except Exception as e:
    print(f"✗ Startup error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
