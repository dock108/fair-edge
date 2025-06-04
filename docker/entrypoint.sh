#!/bin/bash
set -e

# Production entrypoint for bet-intel FastAPI application
# Uses Gunicorn with Uvicorn workers for optimal performance

# Calculate optimal worker count: 2 * CPU_cores + 1
: "${WEB_CONCURRENCY:=$((2 * $(nproc) + 1))}"

echo "🚀 Starting bet-intel with $WEB_CONCURRENCY workers on $(nproc) CPU cores"

# Wait for dependencies (Redis, DB) if needed
if [ "$WAIT_FOR_DEPS" = "true" ]; then
    echo "⏳ Waiting for dependencies..."
    sleep 5
fi

# Run database migrations if requested
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "🔧 Running database migrations..."
    alembic upgrade head
fi

# Start Gunicorn with Uvicorn workers
exec gunicorn \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers "$WEB_CONCURRENCY" \
    --bind "0.0.0.0:8000" \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload \
    app:app 