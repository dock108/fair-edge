#!/bin/bash
set -e

# FairEdge Production Deployment Script
# Simple one-command deployment for production

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}"
    echo "=============================================="
    echo "  FairEdge Production Deployment"
    echo "=============================================="
    echo -e "${NC}"
}

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    print_status "Checking requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not available"
        exit 1
    fi
    
    # Check if we're in the right directory
    if [ ! -f "$PROJECT_ROOT/docker-compose.production.yml" ]; then
        print_error "Production compose file not found"
        exit 1
    fi
    
    print_status "Requirements check passed"
}

setup_environment() {
    print_status "Setting up production environment..."
    
    cd "$PROJECT_ROOT"
    
    # Copy production env file if it doesn't exist
    if [ ! -f ".env.production" ]; then
        if [ -f "environments/production.env" ]; then
            cp environments/production.env .env.production
            print_status "Copied production environment file"
        else
            print_error "Production environment file not found at environments/production.env"
            exit 1
        fi
    fi
    
    # Validate required environment variables
    required_vars=("SUPABASE_URL" "SUPABASE_ANON_KEY" "ODDS_API_KEY")
    for var in "${required_vars[@]}"; do
        if ! grep -q "^$var=" .env.production; then
            print_error "Required variable $var not found in .env.production"
            exit 1
        fi
    done
    
    print_status "Environment validation passed"
}

clean_deployment() {
    print_status "Cleaning up previous deployment..."
    
    cd "$PROJECT_ROOT"
    
    # Stop and remove existing containers
    docker compose -f docker-compose.production.yml down --remove-orphans 2>/dev/null || true
    
    # Clean up old images and build cache for fresh deployment
    docker system prune -f
    
    print_status "Cleanup completed"
}

build_and_deploy() {
    print_status "Building and deploying services..."
    
    cd "$PROJECT_ROOT"
    
    # Build with no cache to ensure fresh deployment
    print_status "Building Docker images (this may take a few minutes)..."
    docker compose -f docker-compose.production.yml build --no-cache --parallel
    
    # Deploy services
    print_status "Starting services..."
    docker compose -f docker-compose.production.yml up -d
    
    print_status "Services deployed successfully"
}

wait_for_services() {
    print_status "Waiting for services to be ready..."
    
    # Wait for API
    echo -n "Waiting for API service"
    max_attempts=60
    attempt=0
    while ! curl -sf http://localhost:8000/health > /dev/null 2>&1 && [ $attempt -lt $max_attempts ]; do
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    if [ $attempt -eq $max_attempts ]; then
        echo " ✗"
        print_error "API service failed to start within timeout"
        exit 1
    fi
    echo " ✓"
    
    # Wait for Frontend
    echo -n "Waiting for Frontend service"
    attempt=0
    while ! curl -sf http://localhost/ > /dev/null 2>&1 && [ $attempt -lt $max_attempts ]; do
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    if [ $attempt -eq $max_attempts ]; then
        echo " ✗"
        print_error "Frontend service failed to start within timeout"
        exit 1
    fi
    echo " ✓"
    
    print_status "All services are ready!"
}

show_status() {
    print_status "Deployment Status:"
    cd "$PROJECT_ROOT"
    docker compose -f docker-compose.production.yml ps
    
    echo ""
    print_status "Service URLs:"
    echo "  Frontend: http://localhost"
    echo "  API: http://localhost:8000"
    echo "  API Docs: http://localhost:8000/docs"
    echo ""
    print_status "Logs: docker compose -f docker-compose.production.yml logs -f"
    echo ""
    print_status "🎉 Production deployment completed successfully!"
}

main() {
    print_header
    
    # Handle command line arguments
    case "${1:-deploy}" in
        "deploy"|"")
            check_requirements
            setup_environment
            clean_deployment
            build_and_deploy
            wait_for_services
            show_status
            ;;
        "status")
            cd "$PROJECT_ROOT"
            docker compose -f docker-compose.production.yml ps
            ;;
        "logs")
            cd "$PROJECT_ROOT"
            docker compose -f docker-compose.production.yml logs -f "${2:-}"
            ;;
        "stop")
            cd "$PROJECT_ROOT"
            print_status "Stopping production services..."
            docker compose -f docker-compose.production.yml down
            ;;
        "clean")
            cd "$PROJECT_ROOT"
            print_status "Cleaning up production deployment..."
            docker compose -f docker-compose.production.yml down -v --remove-orphans
            docker system prune -af --volumes
            ;;
        *)
            echo "Usage: $0 [deploy|status|logs|stop|clean]"
            echo ""
            echo "Commands:"
            echo "  deploy (default)  Deploy production environment"
            echo "  status           Show service status"
            echo "  logs [service]   Show logs (optionally for specific service)"
            echo "  stop             Stop all services"
            echo "  clean            Clean up all containers and volumes"
            echo ""
            echo "Examples:"
            echo "  $0              # Deploy production"
            echo "  $0 deploy       # Deploy production"
            echo "  $0 logs api     # Show API logs"
            echo "  $0 stop         # Stop services"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"