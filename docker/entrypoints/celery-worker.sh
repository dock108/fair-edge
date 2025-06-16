#!/bin/bash
set -e

# Celery Worker Entrypoint
echo "Starting FairEdge Celery worker..."

# Wait for dependencies
echo "Waiting for Redis..."
while ! redis-cli -h "${REDIS_HOST:-redis}" -p "${REDIS_PORT:-6379}" ping > /dev/null 2>&1; do
    echo "Redis is unavailable - sleeping"
    sleep 2
done
echo "Redis is ready!"

# Set default values
export CELERY_CONCURRENCY=${CELERY_CONCURRENCY:-2}
export CELERY_LOGLEVEL=${CELERY_LOGLEVEL:-info}
export CELERY_MAX_TASKS_PER_CHILD=${CELERY_MAX_TASKS_PER_CHILD:-1000}
export CELERY_MAX_MEMORY_PER_CHILD=${CELERY_MAX_MEMORY_PER_CHILD:-200000}

# Create celery directories
mkdir -p /app/celery-data /app/logs

echo "Starting Celery worker with concurrency: $CELERY_CONCURRENCY"

# Start Celery worker
exec celery -A services.celery_app.celery_app worker \
    --loglevel="$CELERY_LOGLEVEL" \
    --concurrency="$CELERY_CONCURRENCY" \
    --max-tasks-per-child="$CELERY_MAX_TASKS_PER_CHILD" \
    --max-memory-per-child="$CELERY_MAX_MEMORY_PER_CHILD" \
    --time-limit=300 \
    --soft-time-limit=240 \
    --without-gossip \
    --without-mingle \
    --without-heartbeat 