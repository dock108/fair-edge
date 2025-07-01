#!/bin/bash
set -e

# FairEdge Deployment Script
# Supports both development and production deployments

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-development}
COMPOSE_FILE=""
ENV_FILE=""

# Functions
print_header() {
    echo -e "${BLUE}"
    echo "=============================================="
    echo "  FairEdge Sports Betting Platform Deployment"
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
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if we're in the right directory
    if [ ! -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        print_error "Not in FairEdge project directory"
        exit 1
    fi
    
    print_status "Requirements check passed"
}

setup_environment() {
    print_status "Setting up $ENVIRONMENT environment..."
    
    case $ENVIRONMENT in
        "development"|"dev")
            COMPOSE_FILE="docker-compose.yml"
            ENV_FILE=".env"
            print_status "Using development configuration"
            ;;
        "production"|"prod")
            COMPOSE_FILE="docker-compose.prod.yml"
            ENV_FILE=".env.production"
            print_status "Using production configuration"
            ;;
        *)
            print_error "Invalid environment: $ENVIRONMENT (use: development, production)"
            exit 1
            ;;
    esac
    
    # Check if environment file exists
    if [ ! -f "$PROJECT_ROOT/$ENV_FILE" ]; then
        print_warning "Environment file $ENV_FILE not found"
        if [ "$ENVIRONMENT" = "production" ]; then
            print_error "Production environment file is required"
            exit 1
        else
            print_status "Using default development environment"
        fi
    fi
}

validate_environment() {
    print_status "Validating environment configuration..."
    
    if [ -f "$PROJECT_ROOT/$ENV_FILE" ]; then
        # Check for required variables
        required_vars=("SUPABASE_URL" "SUPABASE_ANON_KEY" "ODDS_API_KEY")
        
        for var in "${required_vars[@]}"; do
            if ! grep -q "^$var=" "$PROJECT_ROOT/$ENV_FILE" || grep -q "^$var=CHANGE_ME" "$PROJECT_ROOT/$ENV_FILE"; then
                print_warning "Required variable $var not configured in $ENV_FILE"
            fi
        done
    fi
}

setup_directories() {
    print_status "Setting up directories..."
    
    # Create log directories
    mkdir -p "$PROJECT_ROOT/logs/api"
    mkdir -p "$PROJECT_ROOT/logs/celery"
    mkdir -p "$PROJECT_ROOT/logs/nginx"
    
    # Create data directories
    mkdir -p "$PROJECT_ROOT/data/redis"
    mkdir -p "$PROJECT_ROOT/data/celery"
    
    # Set permissions (if running as root/sudo)
    if [ "$EUID" -eq 0 ]; then
        chown -R 1000:1000 "$PROJECT_ROOT/logs"
        chown -R 1000:1000 "$PROJECT_ROOT/data"
    fi
}

build_images() {
    print_status "Building Docker images..."
    
    cd "$PROJECT_ROOT"
    
    if [ "$COMPOSE_FILE" = "docker-compose.prod.yml" ]; then
        # Production build with no cache for clean builds
        docker-compose -f "$COMPOSE_FILE" build --no-cache --parallel
    else
        # Development build
        docker-compose -f "$COMPOSE_FILE" build --parallel
    fi
}

deploy_services() {
    print_status "Deploying services..."
    
    cd "$PROJECT_ROOT"
    
    # Stop existing services
    docker-compose -f "$COMPOSE_FILE" down --remove-orphans
    
    # Start services
    if [ "$ENVIRONMENT" = "production" ]; then
        docker-compose -f "$COMPOSE_FILE" up -d --force-recreate
        
        # Start monitoring services if requested
        if [ "$2" = "--monitoring" ]; then
            print_status "Starting monitoring services..."
            docker-compose -f "$COMPOSE_FILE" --profile monitoring up -d
        fi
    else
        docker-compose -f "$COMPOSE_FILE" up -d
    fi
}

wait_for_services() {
    print_status "Waiting for services to be ready..."
    
    # Wait for API
    echo -n "Waiting for API service"
    while ! curl -sf http://localhost:8000/health > /dev/null 2>&1; do
        echo -n "."
        sleep 2
    done
    echo " ✓"
    
    # Wait for Frontend (if not production with separate nginx)
    if [ "$ENVIRONMENT" != "production" ]; then
        echo -n "Waiting for Frontend service"
        while ! curl -sf http://localhost:5173 > /dev/null 2>&1; do
            echo -n "."
            sleep 2
        done
        echo " ✓"
    fi
    
    print_status "All services are ready!"
}

show_status() {
    print_status "Service Status:"
    cd "$PROJECT_ROOT"
    docker-compose -f "$COMPOSE_FILE" ps
    
    echo ""
    print_status "Service URLs:"
    if [ "$ENVIRONMENT" = "production" ]; then
        echo "  Frontend: http://localhost"
        echo "  API: http://localhost:8000"
        echo "  API Docs: http://localhost:8000/docs"
        if [ "$2" = "--monitoring" ]; then
            echo "  Prometheus: http://localhost:9090"
            echo "  Grafana: http://localhost:3000"
        fi
    else
        echo "  Frontend: http://localhost:5173"
        echo "  API: http://localhost:8000"
        echo "  API Docs: http://localhost:8000/docs"
    fi
}

cleanup_old_images() {
    print_status "Cleaning up old Docker images..."
    docker image prune -f
    docker volume prune -f
}

main() {
    print_header
    
    case "${1:-help}" in
        "development"|"dev")
            check_requirements
            setup_environment
            validate_environment
            setup_directories
            build_images
            deploy_services
            wait_for_services
            show_status
            ;;
        "production"|"prod")
            check_requirements
            setup_environment
            validate_environment
            setup_directories
            build_images
            deploy_services "$@"
            wait_for_services
            show_status "$@"
            cleanup_old_images
            ;;
        "stop")
            print_status "Stopping services..."
            docker-compose down --remove-orphans
            docker-compose -f docker-compose.prod.yml down --remove-orphans 2>/dev/null || true
            ;;
        "clean")
            print_status "Cleaning up all containers, images, and volumes..."
            docker-compose down -v --remove-orphans
            docker-compose -f docker-compose.prod.yml down -v --remove-orphans 2>/dev/null || true
            docker system prune -af --volumes
            ;;
        "logs")
            ENVIRONMENT=${2:-development}
            setup_environment
            docker-compose -f "$COMPOSE_FILE" logs -f
            ;;
        "status")
            ENVIRONMENT=${2:-development}
            setup_environment
            show_status
            ;;
        *)
            echo "Usage: $0 {development|production|stop|clean|logs|status} [options]"
            echo ""
            echo "Commands:"
            echo "  development     Deploy in development mode"
            echo "  production      Deploy in production mode"
            echo "                  Add --monitoring to include Prometheus/Grafana"
            echo "  stop           Stop all services"
            echo "  clean          Clean up all containers and volumes"
            echo "  logs [env]     Show logs for specified environment"
            echo "  status [env]   Show status for specified environment"
            echo ""
            echo "Examples:"
            echo "  $0 development"
            echo "  $0 production --monitoring"
            echo "  $0 logs production"
            exit 1
            ;;
    esac
}

# Run main function
main "$@" 