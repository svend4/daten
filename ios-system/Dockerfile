# Multi-stage Dockerfile for Railway - Backend + Frontend
# Stage 1: Build Frontend
FROM node:18-alpine as frontend-build

WORKDIR /app/frontend

# Copy frontend package files
COPY IOS-System/frontend/package*.json ./
RUN npm install

# Copy frontend source
COPY IOS-System/frontend/ ./

# Build frontend
RUN npm run build

# Stage 2: Python Backend
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY IOS-System/ /app/IOS-System/
COPY ios_bootstrap/ /app/ios_bootstrap/

# Copy built frontend from stage 1
COPY --from=frontend-build /app/frontend/dist /app/frontend-dist

# Create directories
RUN mkdir -p /data/ios-root \
    /data/uploads \
    /data/exports \
    /data/whoosh-index

# Environment variables
ENV PYTHONPATH=/app:$PYTHONPATH \
    PYTHONUNBUFFERED=1 \
    IOS_ROOT_PATH=/data/ios-root \
    FRONTEND_DIST=/app/frontend-dist

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Expose port
EXPOSE 8080

# Start command - will be overridden by Railway
CMD uvicorn ios_bootstrap.main:app --host 0.0.0.0 --port ${PORT:-8080}
