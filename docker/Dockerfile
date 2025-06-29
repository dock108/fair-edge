# Fair-Edge Unified Dockerfile
# Supports both development and production environments

FROM python:3.11-slim as backend-base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entrypoint scripts and make executable
COPY docker/entrypoints/ /entrypoints/
RUN chmod +x /entrypoints/*.sh

# Create necessary directories
RUN mkdir -p /app/logs /app/celery-data

# Copy application code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command for production
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

# Development stage - adds dev tools and auto-reload
FROM backend-base as development
RUN pip install --no-cache-dir \
    watchdog \
    ipdb \
    pytest-cov \
    black \
    flake8
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage - optimized for deployment
FROM backend-base as production
# Remove dev packages and optimize for size
RUN pip uninstall -y pip && \
    apt-get autoremove -y && \
    apt-get clean
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Frontend build stage
FROM node:18-alpine as frontend-build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci --production
COPY frontend/ .
RUN npm run build

# Frontend development stage  
FROM node:18-alpine as frontend-dev
WORKDIR /app

# Install curl for health checks
RUN apk add --no-cache curl

# Copy package files
COPY frontend/package*.json ./

# Install all dependencies (including dev dependencies for vite)
RUN npm ci

# Copy frontend source
COPY frontend/ .

# Expose port
EXPOSE 5173

# Start dev server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]