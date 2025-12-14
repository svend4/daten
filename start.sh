#!/bin/sh
# Railway startup script for IOS System

# Use PORT from Railway, or default to 8000
PORT=${PORT:-8000}

echo "Starting uvicorn on port $PORT"
cd /app/ios-system
exec uvicorn ios_bootstrap.main:app --host 0.0.0.0 --port "$PORT"
