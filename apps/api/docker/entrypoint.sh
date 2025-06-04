#!/bin/bash
set -e

# Production entrypoint for bet-intel FastAPI application
# Uses Gunicorn with Uvicorn workers for optimal performance
# Phase 3 updates: uvicorn-worker package + recycle + graceful shutdown

# Calculate optimal worker count: 2 * CPU_cores + 1
: "${WEB_CONCURRENCY:=$((2 * $(nproc) + 1))}"

# Phase 3.4: Configurable max requests for worker recycling
: "${MAX_REQUESTS:=2000}"
: "${MAX_REQUESTS_JITTER:=200}"
: "${GRACEFUL_TIMEOUT:=15}"

echo "🚀 Starting bet-intel with $WEB_CONCURRENCY workers on $(nproc) CPU cores"
echo "📊 Worker recycle: $MAX_REQUESTS ± $MAX_REQUESTS_JITTER requests"
echo "⏱️  Graceful timeout: ${GRACEFUL_TIMEOUT}s"

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

# Start Gunicorn with new uvicorn-worker and Phase 3.4 settings
exec gunicorn \
    --worker-class uvicorn_worker.UvicornWorker \
    --workers "$WEB_CONCURRENCY" \
    --bind "0.0.0.0:8000" \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests "$MAX_REQUESTS" \
    --max-requests-jitter "$MAX_REQUESTS_JITTER" \
    --graceful-timeout "$GRACEFUL_TIMEOUT" \
    --preload \
    app:app 