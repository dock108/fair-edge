#!/bin/bash

# Stop Development Environment Script for Bet Intel

# Change to project root directory
cd "$(dirname "$0")/.."

echo "🛑 Stopping Bet Intel Development Environment..."

# Stop Docker Compose services
echo "🔌 Stopping Docker services..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down --remove-orphans

# Stop any local processes that might still be running
echo "🧹 Cleaning up local processes..."
pkill -f "redis-server" 2>/dev/null || true
pkill -f "celery worker" 2>/dev/null || true
pkill -f "celery beat" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true

# Remove orphaned containers
echo "🗑️ Cleaning up orphaned containers..."
docker container prune -f 2>/dev/null || true

echo ""
echo "✅ Development environment stopped successfully!"
echo ""
echo "💡 To start again, run:"
echo "   ./scripts/start_dev_full.sh"
echo "" 