#!/bin/bash

# Start Celery Worker Script
# Production-ready startup with logging and monitoring

set -e

echo "🚀 Starting Celery Worker for bet-intel..."

# Create logs directory if it doesn't exist
mkdir -p logs

# Set default values
CONCURRENCY=${CELERY_CONCURRENCY:-2}
LOG_LEVEL=${CELERY_LOG_LEVEL:-info}
MAX_TASKS_PER_CHILD=${CELERY_MAX_TASKS_PER_CHILD:-100}

echo "Configuration:"
echo "  Concurrency: $CONCURRENCY"
echo "  Log Level: $LOG_LEVEL"
echo "  Max Tasks Per Child: $MAX_TASKS_PER_CHILD"
echo "  Redis URL: $REDIS_URL"

# Start Celery worker with production settings
exec celery -A services.celery_app.celery_app worker \
    --loglevel=$LOG_LEVEL \
    --concurrency=$CONCURRENCY \
    --max-tasks-per-child=$MAX_TASKS_PER_CHILD \
    --time-limit=1800 \
    --soft-time-limit=1500 \
    --prefetch-multiplier=1 \
    --without-gossip \
    --without-mingle \
    --without-heartbeat 