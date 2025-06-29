#!/bin/bash
set -e

# FastAPI Application Entrypoint
echo "Starting FairEdge API server..."

# Wait for dependencies
if [ "$WAIT_FOR_DEPS" = "true" ]; then
    echo "Waiting for Redis..."
    while ! redis-cli -h "${REDIS_HOST:-redis}" -p "${REDIS_PORT:-6379}" ping > /dev/null 2>&1; do
        echo "Redis is unavailable - sleeping"
        sleep 2
    done
    echo "Redis is ready!"
fi

# Run database migrations if requested
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running database migrations..."
    alembic upgrade head
else
    echo "Skipping database migrations (RUN_MIGRATIONS=${RUN_MIGRATIONS:-false})"
fi

# Set default values
export WEB_CONCURRENCY=${WEB_CONCURRENCY:-4}
export BIND_HOST=${BIND_HOST:-0.0.0.0}
export BIND_PORT=${BIND_PORT:-8000}

# Start the application
if [ "$ENVIRONMENT" = "development" ]; then
    echo "Starting in development mode with hot reload..."
    exec uvicorn app:app \
        --host "$BIND_HOST" \
        --port "$BIND_PORT" \
        --reload \
        --log-level debug
else
    echo "Starting in production mode..."
    exec gunicorn app:app \
        -w "$WEB_CONCURRENCY" \
        -k uvicorn.workers.UvicornWorker \
        -b "$BIND_HOST:$BIND_PORT" \
        --access-logfile - \
        --error-logfile - \
        --log-level info \
        --timeout 120 \
        --keep-alive 2 \
        --max-requests 1000 \
        --max-requests-jitter 100 \
        --preload
fi