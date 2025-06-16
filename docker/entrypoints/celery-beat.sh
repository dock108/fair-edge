#!/bin/bash
set -e

# Celery Beat Scheduler Entrypoint
echo "Starting FairEdge Celery beat scheduler..."

# Wait for dependencies
echo "Waiting for Redis..."
while ! redis-cli -h "${REDIS_HOST:-redis}" -p "${REDIS_PORT:-6379}" ping > /dev/null 2>&1; do
    echo "Redis is unavailable - sleeping"
    sleep 2
done
echo "Redis is ready!"

# Set default values
export CELERY_LOGLEVEL=${CELERY_LOGLEVEL:-info}

# Create celery directories and ensure permissions
mkdir -p /app/celery-data /app/logs
chown -R app:app /app/celery-data /app/logs 2>/dev/null || true

# Remove any existing beat database to prevent conflicts
rm -f /app/celery-data/beat.db

echo "Starting Celery beat scheduler..."

# Start Celery beat
exec celery -A services.celery_app.celery_app beat \
    --loglevel="$CELERY_LOGLEVEL" \
    --schedule=/app/celery-data/beat.db \
    --pidfile=/app/celery-data/beat.pid 