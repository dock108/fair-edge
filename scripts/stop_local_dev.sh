#!/bin/bash

# Stop Local Development Services Script for Bet Intel

echo "🛑 Stopping Bet Intel Local Development Environment..."
echo ""

# Function to kill processes on a port
kill_port() {
    if lsof -i :$1 >/dev/null 2>&1; then
        echo "🔄 Stopping processes on port $1..."
        lsof -ti :$1 | xargs kill -9 2>/dev/null || true
        sleep 1
        echo "✅ Port $1 cleared"
    else
        echo "ℹ️  No processes running on port $1"
    fi
}

# Stop Celery processes
echo "👷 Stopping Celery workers and beat scheduler..."
pkill -f "celery.*worker" 2>/dev/null && echo "✅ Celery workers stopped" || echo "ℹ️  No Celery workers running"
pkill -f "celery.*beat" 2>/dev/null && echo "✅ Celery beat stopped" || echo "ℹ️  No Celery beat running"

# Additional cleanup for stubborn processes
pkill -f "services.celery_app" 2>/dev/null || true
sleep 2
echo ""

# Stop FastAPI backend
echo "🌐 Stopping FastAPI backend..."
kill_port 8000
echo ""

# Stop Redis
echo "🔴 Stopping Redis server..."
if redis-cli ping >/dev/null 2>&1; then
    redis-cli shutdown 2>/dev/null
    echo "✅ Redis stopped"
else
    echo "ℹ️  Redis not running"
fi
kill_port 6379
echo ""

# Clean up any remaining processes
echo "🧹 Final cleanup..."
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "redis-server" 2>/dev/null || true
sleep 1

# Clean up log files
echo "📁 Cleaning up log files..."
rm -f celery_worker.log celery_beat.log 2>/dev/null && echo "✅ Log files cleaned" || echo "ℹ️  No log files to clean"
echo ""

echo "✅ All services stopped successfully!"
echo ""
echo "🎯 To restart services:"
echo "   ./start_local_dev.sh" 