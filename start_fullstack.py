#!/usr/bin/env python3
"""
Start Full IOS System (WITHOUT bootstrap)
Tests complete architecture with all services
"""
import os
import sys
from pathlib import Path

# Add IOS-System to Python path
ios_system_path = Path(__file__).parent / "ios-system"
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
    from IOS_System.main_production import create_app

    print("✓ Imports successful")
    print("Starting uvicorn...")

    import uvicorn

    # Get port from environment (Railway sets PORT)
    port = int(os.environ.get("PORT", 8080))

    uvicorn.run(
        "IOS_System.main_production:app",
        host="0.0.0.0",
        port=port,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
        access_log=True
    )

except ImportError as e:
    print(f"✗ Import error: {e}")
    print("\nTrying fallback with modified PYTHONPATH...")

    # Fallback - this means relative imports won't work, need to fix them
    print("This requires fixing relative imports in main_production.py")
    print("Consider using absolute imports or creating proper package structure")
    sys.exit(1)

except Exception as e:
    print(f"✗ Startup error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
