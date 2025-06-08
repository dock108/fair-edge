#!/bin/bash

# Stop Local Development Services Script for Bet Intel

# Change to project root directory (parent of scripts/)
cd "$(dirname "$0")/.."

echo "🛑 Stopping Bet Intel Local Development Environment..."
echo ""

# Stop Docker services (primary method)
echo "🐳 Stopping Docker containers..."
docker-compose down
echo "✅ Docker containers stopped"
echo ""

# Clean up any local processes that might still be running
echo "🧹 Cleaning up any remaining local processes..."
pkill -f "redis-server" 2>/dev/null && echo "✅ Local Redis stopped" || echo "ℹ️  No local Redis running"
pkill -f "celery.*worker" 2>/dev/null && echo "✅ Local Celery workers stopped" || echo "ℹ️  No local Celery workers running"
pkill -f "celery.*beat" 2>/dev/null && echo "✅ Local Celery beat stopped" || echo "ℹ️  No local Celery beat running"
pkill -f "uvicorn" 2>/dev/null && echo "✅ Local FastAPI stopped" || echo "ℹ️  No local FastAPI running"
pkill -f "services.celery_app" 2>/dev/null || true
sleep 1

echo ""
echo "✅ All services stopped successfully!"
echo ""
echo "💡 Note: Docker volumes are preserved (Redis data, logs, etc.)"
echo ""
echo "🎯 To restart services:"
echo "   ./scripts/start_local_dev.sh"
echo ""
echo "🧹 To clean up everything (including data volumes):"
echo "   docker-compose down -v" 