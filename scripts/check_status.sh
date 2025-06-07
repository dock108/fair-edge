#!/bin/bash

# Status Check Script for FairEdge Local Development

echo "📊 FairEdge System Status Check"
echo "================================="
echo ""

# Check Redis
echo "🔴 Redis Status:"
if redis-cli ping >/dev/null 2>&1; then
    echo "   ✅ Redis is running"
    echo "   📊 Keys: $(redis-cli dbsize | cut -d: -f2 2>/dev/null || echo 'unknown')"
    echo "   🕒 Last update: $(redis-cli get last_update 2>/dev/null || echo 'No data')"
else
    echo "   ❌ Redis is not running"
fi
echo ""

# Check Celery processes
echo "👷 Celery Status:"
WORKER_COUNT=$(ps aux | grep -c "celery.*worker" | awk '{print $1-1}')
BEAT_COUNT=$(ps aux | grep -c "celery.*beat" | awk '{print $1-1}')

if [ "$WORKER_COUNT" -gt 0 ]; then
    echo "   ✅ Celery Worker: $WORKER_COUNT process(es) running"
else
    echo "   ❌ Celery Worker: Not running"
fi

if [ "$BEAT_COUNT" -gt 0 ]; then
    echo "   ✅ Celery Beat: $BEAT_COUNT process(es) running"
else
    echo "   ❌ Celery Beat: Not running"
fi
echo ""

# Check FastAPI backend
echo "🌐 Backend Status:"
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo "   ✅ FastAPI backend is running"
else
    echo "   ❌ FastAPI backend is not running"
fi
echo ""

# Check Celery task statistics
echo "📈 Task Statistics:"
if [ "$WORKER_COUNT" -gt 0 ]; then
    echo "   📋 Active tasks:"
    celery -A services.celery_app inspect active 2>/dev/null | grep -A5 "refresh_odds_data\|health_check" || echo "      No active tasks"
    
    echo "   📊 Task stats:"
    celery -A services.celery_app inspect stats 2>/dev/null | grep -E "(total|pool)" | head -5 || echo "      Could not retrieve stats"
else
    echo "   ⚠️  Cannot check task stats - no worker running"
fi
echo ""

# Check log files
echo "📁 Log Files:"
if [ -f "celery_worker.log" ]; then
    WORKER_LINES=$(wc -l < celery_worker.log 2>/dev/null || echo 0)
    echo "   📝 celery_worker.log: $WORKER_LINES lines"
    if [ "$WORKER_LINES" -gt 0 ]; then
        echo "      Last 3 lines:"
        tail -3 celery_worker.log | sed 's/^/         /'
    fi
else
    echo "   📝 celery_worker.log: Not found"
fi

if [ -f "celery_beat.log" ]; then
    BEAT_LINES=$(wc -l < celery_beat.log 2>/dev/null || echo 0)
    echo "   📝 celery_beat.log: $BEAT_LINES lines"
    if [ "$BEAT_LINES" -gt 0 ]; then
        echo "      Last 3 lines:"
        tail -3 celery_beat.log | sed 's/^/         /'
    fi
else
    echo "   📝 celery_beat.log: Not found"
fi
echo ""

# Overall status
echo "📋 Overall Status:"
if redis-cli ping >/dev/null 2>&1 && [ "$WORKER_COUNT" -gt 0 ] && [ "$BEAT_COUNT" -gt 0 ] && curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo "   ✅ All systems operational"
    echo ""
    echo "🚀 Next data refresh expected in $(python -c "
import os
from datetime import datetime, timedelta
refresh_interval = int(os.getenv('REFRESH_INTERVAL_MINUTES', '5'))
now = datetime.now()
next_refresh = now.replace(second=0, microsecond=0) + timedelta(minutes=refresh_interval - (now.minute % refresh_interval))
diff = next_refresh - now
print(f'{diff.seconds // 60}m {diff.seconds % 60}s')
" 2>/dev/null || echo "unknown")"
else
    echo "   ⚠️  Some services are not running"
    echo ""
    echo "🔧 To start services: ./start_local_dev.sh"
    echo "🛑 To stop services:  ./stop_local_dev.sh"
fi 