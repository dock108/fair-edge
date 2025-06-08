#!/bin/bash

# Docker-based Local Development Startup Script for Bet Intel
# This script uses Docker Compose for all services (consistent and reliable)

# Change to project root directory (parent of scripts/)
cd "$(dirname "$0")/.."

echo "🚀 Starting Bet Intel Local Development Environment (Docker)"
echo "📊 Configured for 5-minute odds API refresh interval"
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check dependencies
echo "🔍 Checking dependencies..."

if ! command_exists docker; then
    echo "❌ Docker not found. Please install Docker Desktop"
    echo "   Download from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! command_exists docker-compose; then
    echo "❌ Docker Compose not found. Please install Docker Compose"
    exit 1
fi

# Set correct Docker context for Docker Desktop
docker context use desktop-linux >/dev/null 2>&1 || true

# Check if Docker daemon is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker daemon is not running. Please start Docker Desktop"
    echo "   - On macOS: Open Docker Desktop app"
    echo "   - On Linux: sudo systemctl start docker"
    echo "   - On Windows: Start Docker Desktop"
    exit 1
fi

echo "✅ All dependencies found and Docker is running"
echo ""

# Check important environment variables
echo "🔧 Checking environment variables..."
missing_vars=()

if [ -z "$ODDS_API_KEY" ]; then
    missing_vars+=("ODDS_API_KEY")
fi

if [ -z "$SUPABASE_URL" ]; then
    missing_vars+=("SUPABASE_URL")
fi

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo "⚠️  Warning: Missing environment variables:"
    for var in "${missing_vars[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "💡 Create a .env file with these variables or set them in your environment"
    echo "   Example: echo 'ODDS_API_KEY=your_key_here' >> .env"
    echo ""
    echo "ℹ️  Continuing anyway (some features may not work)..."
else
    echo "✅ Required environment variables are set"
fi
echo ""

# Clean up any existing local processes that might conflict
echo "🧹 Cleaning up potential conflicts..."
pkill -f "redis-server" 2>/dev/null || true
pkill -f "celery worker" 2>/dev/null || true
pkill -f "celery beat" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "fastapi" 2>/dev/null || true
pkill -f "python.*app.py" 2>/dev/null || true

# Kill any processes on ports we need
if lsof -i :8000 >/dev/null 2>&1; then
    echo "🔄 Freeing up port 8000..."
    lsof -ti :8000 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

if lsof -i :6379 >/dev/null 2>&1; then
    echo "🔄 Freeing up port 6379..."
    lsof -ti :6379 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# Stop any existing Docker containers
echo "🐳 Stopping existing Docker containers..."
docker-compose down 2>/dev/null || true
echo ""

# Start all services with Docker Compose
echo "🐳 Starting all services with Docker Compose..."
docker-compose up -d redis
echo "⏳ Waiting for Redis to be ready..."
sleep 5

docker-compose up -d celery_worker celery_beat
echo "⏳ Waiting for Celery services to be ready..."
sleep 10

docker-compose up -d api
echo "⏳ Waiting for API to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
echo ""

# Redis health
if docker-compose exec redis redis-cli ping | grep -q PONG; then
    echo "✅ Redis: Ready"
else
    echo "❌ Redis: Not responding"
fi

# API health
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ API: Ready at http://localhost:8000"
else
    echo "❌ API: Not responding"
fi

# Celery worker health
if docker-compose exec celery_worker celery -A services.celery_app.celery_app inspect ping >/dev/null 2>&1; then
    echo "✅ Celery Worker: Ready"
else
    echo "❌ Celery Worker: Not responding"
fi

echo ""

# Show container status
echo "📋 Container Status:"
docker-compose ps

echo ""
echo "🎉 All services started successfully!"
echo ""
echo "📋 Service Endpoints:"
echo "   🔴 Redis:        localhost:6379"
echo "   🌐 API:          http://localhost:8000"
echo "   📊 Health Check: http://localhost:8000/health"
echo "   🌸 Flower (opt): http://localhost:5555"
echo ""
echo "📁 View Logs:"
echo "   docker-compose logs -f api"
echo "   docker-compose logs -f celery_worker"
echo "   docker-compose logs -f celery_beat"
echo "   docker-compose logs -f redis"
echo ""
echo "📊 Odds API Configuration:"
echo "   🔄 Refresh Interval: 5 minutes"
echo "   📅 Scheduled tasks: odds refresh + health checks"
echo ""
echo "🎯 Next Steps:"
echo "   1. Start your frontend: cd frontend && npm run dev"
echo "   2. Visit: http://localhost:3000"
echo "   3. Monitor with: docker-compose logs -f"
echo ""
echo "🛑 To stop all services:"
echo "   docker-compose down"
echo ""
echo "📝 To follow logs:"
echo "   docker-compose logs -f" 