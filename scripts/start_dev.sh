#!/bin/bash

# Full Development Environment Startup Script for Bet Intel
# Starts both frontend and backend in Docker with hot reloading

# Change to project root directory
cd "$(dirname "$0")/.."

echo "🚀 Starting Full Bet Intel Development Environment"
echo "📊 Frontend: http://localhost:5173"
echo "📊 Backend: http://localhost:8000"
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

# Check if Docker daemon is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker daemon is not running. Please start Docker Desktop"
    exit 1
fi

echo "✅ All dependencies found and Docker is running"
echo ""

# Check environment variables
echo "🔧 Checking environment variables..."
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found"
    echo "   Create one based on .env.example for full functionality"
    echo ""
fi

# Clean up any existing containers
echo "🧹 Cleaning up existing containers..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down --remove-orphans

# Pull latest images
echo "📦 Pulling latest base images..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml pull --ignore-pull-failures

# Build and start services
echo "🏗️ Building and starting services..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build --detach

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 5

# Function to check service health
check_service() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=0
    
    echo -n "Checking $service"
    while [ $attempt -lt $max_attempts ]; do
        if curl -f -s "$url" >/dev/null 2>&1; then
            echo " ✅"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    echo " ❌ (timeout)"
    return 1
}

# Check each service
check_service "Redis" "http://localhost:6379" || echo "Redis may still be starting..."
check_service "Backend API" "http://localhost:8000/health"
check_service "Frontend" "http://localhost:5173"

echo ""
echo "🎉 Development environment is ready!"
echo ""
echo "📱 Frontend Application: http://localhost:5173"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo ""
echo "📊 Real-time logs:"
echo "   docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f"
echo ""
echo "🛑 To stop all services:"
echo "   docker-compose -f docker-compose.yml -f docker-compose.dev.yml down"
echo ""
echo "🔄 Hot reloading is enabled for both frontend and backend!"

# Follow logs (optional)
read -p "Show live logs? (y/N): " -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "📊 Following logs (Ctrl+C to stop)..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f
fi 