FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies including Gunicorn
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn uvicorn[standard] \
    prometheus-fastapi-instrumentator \
    "sentry-sdk[celery]" \
    structlog

# Copy application code
COPY . .

# Copy and set permissions for entrypoint
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create non-root user and setup directories
RUN useradd --create-home --shell /bin/bash app && \
    mkdir -p /app/celery-data && \
    chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use entrypoint script for production
ENTRYPOINT ["/entrypoint.sh"] 