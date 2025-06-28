#!/bin/bash
set -e

# Comprehensive test runner for bet-intel application
# Supports smoke tests, load tests, integration tests, and full CI simulation

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
🧪 Bet-Intel Test Runner

USAGE:
    $0 [COMMAND] [OPTIONS]

COMMANDS:
    smoke           Run smoke tests (quick health checks)
    load            Run load tests with Locust
    integration     Run full integration test suite
    sprint6         Run Sprint 6 specific feature tests
    docker-smoke    Run smoke tests in Docker containers
    docker-load     Run load tests in Docker containers
    ci-simulation   Simulate full CI pipeline locally
    cleanup         Clean up test resources and containers
    install-deps    Install test dependencies
    
OPTIONS:
    --verbose, -v   Enable verbose output
    --help, -h      Show this help message

EXAMPLES:
    $0 smoke                    # Run smoke tests locally
    $0 load --verbose           # Run load tests with verbose output
    $0 docker-smoke             # Run smoke tests in Docker
    $0 ci-simulation            # Full CI pipeline simulation
    $0 cleanup                  # Clean up test resources

ENVIRONMENT VARIABLES:
    TEST_TIMEOUT    Test timeout in seconds (default: 300)
    LOAD_TEST_USERS Number of concurrent users for load test (default: 10)
    LOAD_TEST_TIME  Load test duration (default: 60s)
EOF
}

# Configuration
TEST_TIMEOUT=${TEST_TIMEOUT:-300}
LOAD_TEST_USERS=${LOAD_TEST_USERS:-10}
LOAD_TEST_TIME=${LOAD_TEST_TIME:-60s}
VERBOSE=${VERBOSE:-false}

# Parse arguments
COMMAND=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        smoke|load|integration|sprint6|docker-smoke|docker-load|ci-simulation|cleanup|install-deps)
            COMMAND=$1
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

if [[ -z "$COMMAND" ]]; then
    log_error "No command specified"
    show_help
    exit 1
fi

# Utility functions
check_dependencies() {
    log_info "Checking dependencies..."
    
    local missing_deps=()
    
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    if ! command -v pip &> /dev/null; then
        missing_deps+=("pip")
    fi
    
    if ! command -v docker &> /dev/null; then
        missing_deps+=("docker")
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        missing_deps+=("docker-compose")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        exit 1
    fi
    
    log_success "All dependencies available"
}

setup_test_env() {
    log_info "Setting up test environment..."
    
    # Create test environment file
    cat > .env.test << EOF
DEBUG_MODE=true
APP_ENV=test
REDIS_URL=redis://localhost:6379/0
SUPABASE_URL=https://test.supabase.co
SUPABASE_ANON_KEY=test_key
SUPABASE_JWT_SECRET=test_secret
THE_ODDS_API_KEY=test_api_key
WEB_CONCURRENCY=2
TEST_BASE_URL=http://localhost:8000
EOF
    
    # Create test results directory
    mkdir -p test-results
    
    log_success "Test environment ready"
}

install_deps() {
    log_info "Installing test dependencies..."
    pip install -r requirements.txt
    pip install pytest-cov pytest-xdist pytest-asyncio
    log_success "Dependencies installed"
}

start_background_services() {
    log_info "Starting background services..."
    
    # Start Redis for testing
    if ! pgrep redis-server > /dev/null; then
        log_info "Starting Redis..."
        redis-server --daemonize yes --port 6379 --loglevel warning
        sleep 2
    fi
    
    # Wait for Redis
    timeout 30 bash -c 'until redis-cli ping > /dev/null 2>&1; do sleep 1; done' || {
        log_error "Redis failed to start"
        exit 1
    }
    
    log_success "Background services started"
}

stop_background_services() {
    log_info "Stopping background services..."
    
    # Stop Redis if we started it
    if pgrep redis-server > /dev/null; then
        pkill redis-server || true
    fi
    
    log_success "Background services stopped"
}

run_smoke_tests() {
    log_info "Running smoke tests..."
    
    setup_test_env
    start_background_services
    
    # Start application in background
    export $(cat .env.test | xargs)
    python -m uvicorn app:app --host 0.0.0.0 --port 8000 &
    APP_PID=$!
    echo $APP_PID > app.pid
    
    # Wait for app to start
    log_info "Waiting for application to start..."
    timeout 60 bash -c 'until curl -s http://localhost:8000/health > /dev/null; do sleep 2; done' || {
        log_error "Application failed to start"
        kill $APP_PID 2>/dev/null || true
        stop_background_services
        exit 1
    }
    
    # Run smoke tests
    log_info "Executing smoke tests..."
    if [[ "$VERBOSE" == "true" ]]; then
        pytest tests/test_smoke_ci.py -v --tb=short --durations=10
    else
        pytest tests/test_smoke_ci.py -v --tb=short
    fi
    
    SMOKE_EXIT_CODE=$?
    
    # Cleanup
    kill $APP_PID 2>/dev/null || true
    rm -f app.pid
    stop_background_services
    
    if [[ $SMOKE_EXIT_CODE -eq 0 ]]; then
        log_success "Smoke tests passed"
    else
        log_error "Smoke tests failed"
        exit $SMOKE_EXIT_CODE
    fi
}

run_load_tests() {
    log_info "Running load tests..."
    
    setup_test_env
    start_background_services
    
    # Start application in background
    export $(cat .env.test | xargs)
    python -m uvicorn app:app --host 0.0.0.0 --port 8000 --workers 2 &
    APP_PID=$!
    echo $APP_PID > app.pid
    
    # Wait for app to start
    log_info "Waiting for application to start..."
    timeout 60 bash -c 'until curl -s http://localhost:8000/health > /dev/null; do sleep 2; done' || {
        log_error "Application failed to start"
        kill $APP_PID 2>/dev/null || true
        stop_background_services
        exit 1
    }
    
    # Run load tests
    log_info "Executing load tests with $LOAD_TEST_USERS users for $LOAD_TEST_TIME..."
    python -m locust \
        -f tests/locustfile.py \
        --host http://localhost:8000 \
        --users $LOAD_TEST_USERS \
        --spawn-rate 2 \
        --run-time $LOAD_TEST_TIME \
        --headless \
        --html test-results/load_test_report.html \
        --csv test-results/load_test_results
    
    LOAD_EXIT_CODE=$?
    
    # Analyze results
    if [[ -f test-results/load_test_results_stats.csv ]]; then
        log_info "Load test results:"
        cat test-results/load_test_results_stats.csv
        
        # Check failure rate
        total_requests=$(tail -n 1 test-results/load_test_results_stats.csv | cut -d',' -f3)
        total_failures=$(tail -n 1 test-results/load_test_results_stats.csv | cut -d',' -f4)
        
        if [[ "$total_requests" -gt 0 ]]; then
            error_rate=$(( total_failures * 100 / total_requests ))
            log_info "Error rate: ${error_rate}%"
            
            if [[ "$error_rate" -gt 5 ]]; then
                log_error "Error rate too high: ${error_rate}%"
                LOAD_EXIT_CODE=1
            else
                log_success "Error rate acceptable: ${error_rate}%"
            fi
        fi
    fi
    
    # Cleanup
    kill $APP_PID 2>/dev/null || true
    rm -f app.pid
    stop_background_services
    
    if [[ $LOAD_EXIT_CODE -eq 0 ]]; then
        log_success "Load tests passed"
        log_info "Report available at: test-results/load_test_report.html"
    else
        log_error "Load tests failed"
        exit $LOAD_EXIT_CODE
    fi
}

run_integration_tests() {
    log_info "Running integration tests..."
    
    setup_test_env
    start_background_services
    
    # Run existing test suite
    export $(cat .env.test | xargs)
    
    if [[ "$VERBOSE" == "true" ]]; then
        pytest tests/ -v --tb=short --ignore=tests/test_smoke_ci.py --maxfail=5 --durations=10
    else
        pytest tests/ -v --tb=short --ignore=tests/test_smoke_ci.py --maxfail=5
    fi
    
    INTEGRATION_EXIT_CODE=$?
    
    stop_background_services
    
    if [[ $INTEGRATION_EXIT_CODE -eq 0 ]]; then
        log_success "Integration tests passed"
    else
        log_error "Integration tests failed"
        exit $INTEGRATION_EXIT_CODE
    fi
}

run_sprint6_tests() {
    log_info "Running Sprint 6 feature tests..."
    
    setup_test_env
    start_background_services
    
    # Start application in background
    export $(cat .env.test | xargs)
    python -m uvicorn app:app --host 0.0.0.0 --port 8000 &
    APP_PID=$!
    echo $APP_PID > app.pid
    
    # Wait for app to start
    log_info "Waiting for application to start..."
    timeout 60 bash -c 'until curl -s http://localhost:8000/health > /dev/null; do sleep 2; done' || {
        log_error "Application failed to start"
        kill $APP_PID 2>/dev/null || true
        stop_background_services
        exit 1
    }
    
    # Run Sprint 6 specific tests
    log_info "Executing Sprint 6 feature tests..."
    if [[ "$VERBOSE" == "true" ]]; then
        pytest tests/test_stripe_webhooks.py tests/test_route_protection.py tests/test_sprint6_integration.py -v --tb=short --durations=10
    else
        pytest tests/test_stripe_webhooks.py tests/test_route_protection.py tests/test_sprint6_integration.py -v --tb=short
    fi
    
    SPRINT6_EXIT_CODE=$?
    
    # Cleanup
    kill $APP_PID 2>/dev/null || true
    rm -f app.pid
    stop_background_services
    
    if [[ $SPRINT6_EXIT_CODE -eq 0 ]]; then
        log_success "Sprint 6 tests passed"
    else
        log_error "Sprint 6 tests failed"
        exit $SPRINT6_EXIT_CODE
    fi
}

run_docker_smoke() {
    log_info "Running smoke tests in Docker..."
    
    # Clean up any existing containers
    docker-compose -f docker-compose.test.yml down -v --remove-orphans 2>/dev/null || true
    
    # Run smoke tests in Docker
    docker-compose --profile test --profile smoke-test -f docker-compose.test.yml up --build --abort-on-container-exit
    DOCKER_EXIT_CODE=$?
    
    # Cleanup
    docker-compose -f docker-compose.test.yml down -v --remove-orphans
    
    if [[ $DOCKER_EXIT_CODE -eq 0 ]]; then
        log_success "Docker smoke tests passed"
    else
        log_error "Docker smoke tests failed"
        exit $DOCKER_EXIT_CODE
    fi
}

run_docker_load() {
    log_info "Running load tests in Docker..."
    
    # Clean up any existing containers
    docker-compose -f docker-compose.test.yml down -v --remove-orphans 2>/dev/null || true
    
    # Create test results directory
    mkdir -p test-results
    
    # Run load tests in Docker
    docker-compose --profile test --profile load-test -f docker-compose.test.yml up --build --abort-on-container-exit
    DOCKER_EXIT_CODE=$?
    
    # Cleanup
    docker-compose -f docker-compose.test.yml down -v --remove-orphans
    
    if [[ $DOCKER_EXIT_CODE -eq 0 ]]; then
        log_success "Docker load tests passed"
        log_info "Results should be in test-results/"
    else
        log_error "Docker load tests failed"
        exit $DOCKER_EXIT_CODE
    fi
}

run_ci_simulation() {
    log_info "Running full CI simulation..."
    
    log_info "Step 1: Smoke tests"
    run_smoke_tests
    
    log_info "Step 2: Sprint 6 feature tests"
    run_sprint6_tests
    
    log_info "Step 3: Load tests"
    run_load_tests
    
    log_info "Step 4: Integration tests"
    run_integration_tests
    
    log_info "Step 5: Docker smoke tests"
    run_docker_smoke
    
    log_success "🎉 Full CI simulation completed successfully!"
}

cleanup() {
    log_info "Cleaning up test resources..."
    
    # Kill any running app processes
    if [[ -f app.pid ]]; then
        kill $(cat app.pid) 2>/dev/null || true
        rm -f app.pid
    fi
    
    # Stop background services
    stop_background_services
    
    # Clean up Docker resources
    docker-compose -f docker-compose.test.yml down -v --remove-orphans 2>/dev/null || true
    
    # Clean up test files
    rm -f .env.test
    
    log_success "Cleanup completed"
}

# Main execution
case $COMMAND in
    smoke)
        check_dependencies
        run_smoke_tests
        ;;
    load)
        check_dependencies
        run_load_tests
        ;;
    integration)
        check_dependencies
        run_integration_tests
        ;;
    sprint6)
        check_dependencies
        run_sprint6_tests
        ;;
    docker-smoke)
        check_dependencies
        run_docker_smoke
        ;;
    docker-load)
        check_dependencies
        run_docker_load
        ;;
    ci-simulation)
        check_dependencies
        run_ci_simulation
        ;;
    cleanup)
        cleanup
        ;;
    install-deps)
        install_deps
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac 