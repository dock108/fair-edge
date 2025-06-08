#!/bin/bash

# Local Development Startup Script for Bet Intel
# This script starts all necessary services for local development with 5-minute odds API pulls

# Change to project root directory (parent of scripts/)
cd "$(dirname "$0")/.."

echo "🚀 Starting Bet Intel Local Development Environment..."
echo "📊 Configured for 5-minute odds API refresh interval"
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to kill processes on a port
kill_port() {
    echo "🔄 Killing processes on port $1..."
    lsof -ti :$1 | xargs kill -9 2>/dev/null || true
    sleep 2
}

# Check dependencies
echo "🔍 Checking dependencies..."

if ! command_exists redis-server; then
    echo "❌ Redis not found. Please install Redis:"
    echo "   brew install redis"
    exit 1
fi

if ! command_exists celery; then
    echo "❌ Celery not found. Please install:"
    echo "   pip install celery[redis]"
    exit 1
fi

echo "✅ All dependencies found"
echo ""

# Clean up any existing processes
echo "🧹 Cleaning up existing processes..."
kill_port 8000  # FastAPI backend
kill_port 6379  # Redis
pkill -f "celery worker" 2>/dev/null || true
pkill -f "celery beat" 2>/dev/null || true
echo ""

# Start Redis
echo "🔴 Starting Redis server..."
redis-server --daemonize yes --port 6379
sleep 2

if ! port_in_use 6379; then
    echo "❌ Failed to start Redis"
    exit 1
fi
echo "✅ Redis started on port 6379"
echo ""

# Create logs directory if it doesn't exist
mkdir -p logs

# Start Celery Worker (background task processor)
echo "👷 Starting Celery worker..."
nohup celery -A services.celery_app worker --loglevel=info --concurrency=2 > logs/celery_worker.log 2>&1 &
CELERY_WORKER_PID=$!
sleep 5

# Verify worker started
if ps -p $CELERY_WORKER_PID > /dev/null; then
    echo "✅ Celery worker started (PID: $CELERY_WORKER_PID)"
else
    echo "❌ Failed to start Celery worker"
    echo "📋 Check logs/celery_worker.log for errors"
    exit 1
fi
echo ""

# Start Celery Beat (task scheduler)
echo "⏰ Starting Celery beat scheduler..."
nohup celery -A services.celery_app beat --loglevel=info > logs/celery_beat.log 2>&1 &
CELERY_BEAT_PID=$!
sleep 5

# Verify beat started
if ps -p $CELERY_BEAT_PID > /dev/null; then
    echo "✅ Celery beat started (PID: $CELERY_BEAT_PID)"
else
    echo "❌ Failed to start Celery beat"
    echo "📋 Check logs/celery_beat.log for errors"
    exit 1
fi
echo "📅 Scheduled tasks:"
echo "   - Odds refresh: Every 5 minutes"
echo "   - Health check: Every 5 minutes"
echo ""

# Start FastAPI Backend
echo "🌐 Starting FastAPI backend..."
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
BACKEND_PID=$!
sleep 5

if ! port_in_use 8000; then
    echo "❌ Failed to start FastAPI backend"
    echo "📋 Check logs/backend.log for errors"
    kill $CELERY_WORKER_PID $CELERY_BEAT_PID 2>/dev/null || true
    exit 1
fi
echo "✅ FastAPI backend started on http://localhost:8000"
echo ""

# Test Celery connection and trigger initial data fetch
echo "🧪 Testing Celery setup..."
sleep 2

# Verify Celery can see the tasks
echo "📋 Registered Celery tasks:"
celery -A services.celery_app inspect registered 2>/dev/null | grep -E "(refresh_odds_data|health_check)" || echo "   ⚠️  Could not verify registered tasks"

# Trigger an immediate data refresh to test the system
echo "🚀 Triggering initial data refresh..."
python -c "
from services.tasks import refresh_odds_data
try:
    result = refresh_odds_data.delay()
    print(f'   ✅ Task queued: {result.id}')
except Exception as e:
    print(f'   ❌ Failed to queue task: {e}')
"
echo ""

# Display status
echo "🎉 All services started successfully!"
echo ""
echo "📋 Service Status:"
echo "   🔴 Redis:        http://localhost:6379"
echo "   🌐 Backend:      http://localhost:8000"
echo "   👷 Celery Worker: Running (PID: $CELERY_WORKER_PID)"
echo "   ⏰ Celery Beat:   Running (PID: $CELERY_BEAT_PID)"
echo ""
echo "📁 Log Files:"
echo "   📝 FastAPI Backend: logs/backend.log"
echo "   📝 Celery Worker:   logs/celery_worker.log"
echo "   📝 Celery Beat:     logs/celery_beat.log"
echo ""
echo "📊 Odds API Configuration:"
echo "   🔄 Refresh Interval: 5 minutes"
echo "   🔑 API Key: $(echo $ODDS_API_KEY | cut -c1-8)..."
echo ""
echo "🎯 Next Steps:"
echo "   1. Start your frontend: cd frontend && npm run dev"
echo "   2. Visit: http://localhost:3000"
echo "   3. Watch logs for odds updates every 5 minutes"
echo ""
echo "🛑 To stop all services:"
echo "   ./stop_local_dev.sh"
echo ""

# Function to handle cleanup on script exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $CELERY_WORKER_PID $CELERY_BEAT_PID $BACKEND_PID $TAIL_PID 2>/dev/null || true
    redis-cli shutdown 2>/dev/null || true
    echo "✅ All services stopped"
}

# Set up signal handlers
trap cleanup EXIT INT TERM

# Keep script running and show logs
echo "📝 Showing backend logs (Ctrl+C to stop all services):"
echo "----------------------------------------"
# Show logs in real-time
tail -f logs/backend.log &
TAIL_PID=$!

# Wait for backend process and clean up tail when done
wait $BACKEND_PID
kill $TAIL_PID 2>/dev/null || true 