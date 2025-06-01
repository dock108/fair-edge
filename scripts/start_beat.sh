#!/bin/bash

# Start Celery Beat Script  
# Production-ready scheduler startup

set -e

echo "📅 Starting Celery Beat Scheduler for bet-intel..."

# Create logs directory if it doesn't exist
mkdir -p logs

# Set default values
LOG_LEVEL=${CELERY_LOG_LEVEL:-info}
SCHEDULE_FILE=${CELERY_SCHEDULE_FILE:-/tmp/celerybeat-schedule}

echo "Configuration:"
echo "  Log Level: $LOG_LEVEL"
echo "  Schedule File: $SCHEDULE_FILE"
echo "  Refresh Interval: ${REFRESH_INTERVAL_MINUTES:-60} minutes"
echo "  Redis URL: $REDIS_URL"

# Remove old schedule file if it exists (ensures clean start)
if [ -f "$SCHEDULE_FILE" ]; then
    echo "Removing old schedule file: $SCHEDULE_FILE"
    rm "$SCHEDULE_FILE"
fi

# Start Celery beat with production settings
exec celery -A services.celery_app.celery_app beat \
    --loglevel=$LOG_LEVEL \
    --schedule="$SCHEDULE_FILE" \
    --pidfile=/tmp/celerybeat.pid 