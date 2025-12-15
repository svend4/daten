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

# Copy and make startup scripts executable
COPY start.py /app/start.py
RUN chmod +x /app/start.py

# Set working directory to ios-system
WORKDIR /app/ios-system

# Expose port (Railway sets PORT env variable)
EXPOSE 8080

# Start command - use Python startup script that handles PORT correctly
CMD ["python3", "/app/start.py"]
