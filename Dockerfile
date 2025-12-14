# Dockerfile for Railway deployment
# This file forces Railway to use correct paths with ios-system folder

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY ios-system/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . /app/

# Copy and make startup script executable
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Set working directory to ios-system
WORKDIR /app/ios-system

# Expose port (Railway sets PORT env variable)
EXPOSE 8000

# Start command - use startup script
CMD ["/app/start.sh"]
