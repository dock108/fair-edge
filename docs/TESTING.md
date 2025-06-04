# Testing Guide for bet-intel

This document describes the comprehensive testing infrastructure implemented for the bet-intel FastAPI application.

## Overview

The testing infrastructure includes:
- **Smoke Tests**: Quick health checks and critical functionality verification
- **Load Tests**: Performance testing with realistic user traffic patterns
- **Integration Tests**: Full test suite including database and external service interactions
- **CI/CD Pipeline**: Automated testing on GitHub Actions
- **Docker Testing**: Containerized test environments for consistency

## Quick Start

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- Redis (for local testing)
- curl (for health checks)

### Run Tests Locally

```bash
# Install test dependencies
./scripts/run_tests.sh install-deps

# Run smoke tests (quick, 2-3 minutes)
./scripts/run_tests.sh smoke

# Run load tests (5-10 minutes)
./scripts/run_tests.sh load

# Run full integration tests (10-15 minutes)
./scripts/run_tests.sh integration

# Run full CI simulation (20-30 minutes)
./scripts/run_tests.sh ci-simulation
```

### Run Tests in Docker

```bash
# Docker smoke tests
./scripts/run_tests.sh docker-smoke

# Docker load tests
./scripts/run_tests.sh docker-load

# Manual Docker commands
docker-compose --profile smoke-test -f docker-compose.test.yml up --build --abort-on-container-exit
```

## Test Types

### 1. Smoke Tests (`tests/test_smoke_ci.py`)

Fast, critical functionality checks that verify:
- Health endpoint responds correctly
- API documentation is accessible
- Prometheus metrics are available
- Rate limiting headers are present
- CORS headers are configured
- Basic error handling works
- Response times are acceptable
- Application handles concurrent requests

**When to run**: Before every commit, in CI pipeline
**Duration**: 30-60 seconds
**Dependencies**: Redis

### 2. Load Tests (`tests/locustfile.py`)

Performance testing with realistic user scenarios:
- **BetIntelUser**: Typical users browsing opportunities
- **AuthenticatedUser**: Active subscribers with frequent API calls
- **AdminUser**: Administrative users with monitoring access

**Load Test Configuration**:
- Default: 10 concurrent users
- Test duration: 60 seconds
- Spawn rate: 2 users/second
- Error threshold: <5% failure rate

**Metrics Tracked**:
- Request/response times
- Error rates by endpoint
- Concurrent request handling
- Rate limiting behavior

### 3. Integration Tests

Comprehensive test suite including:
- Database enum type verification
- Index performance readiness
- Redis connectivity
- Application startup/shutdown
- End-to-end API functionality

## CI/CD Pipeline (`.github/workflows/ci-tests.yml`)

The GitHub Actions workflow includes 5 jobs:

### 1. `smoke-tests`
- Runs on every push/PR
- Sets up PostgreSQL and Redis services
- Starts application and runs smoke tests
- Fast feedback (5-10 minutes)

### 2. `load-tests`
- Runs after smoke tests pass
- Tests performance under load
- Validates error rates and response times
- Uploads test reports as artifacts

### 3. `integration-tests`
- Runs existing test suite
- Verifies database integration
- Tests with full service stack

### 4. `docker-build-test`
- Builds Docker image
- Tests container startup and health
- Validates production deployment readiness

### 5. `performance-benchmark`
- Runs only on main branch pushes
- Benchmarks critical endpoints
- Tracks performance regression

## Configuration

### Environment Variables

**Local Testing**:
```bash
TEST_TIMEOUT=300           # Test timeout in seconds
LOAD_TEST_USERS=10         # Concurrent users for load test
LOAD_TEST_TIME=60s         # Load test duration
VERBOSE=true               # Enable verbose output
```

**CI Environment**:
```bash
REDIS_URL=redis://localhost:6379/0
TEST_BASE_URL=http://localhost:8000
DEBUG_MODE=true
APP_ENV=test
```

### Test Files

```
tests/
├── test_smoke_ci.py           # Smoke tests for CI
├── locustfile.py              # Load testing configuration
├── test_enum_types.py         # Database enum verification
├── test_event_time_index.py   # Index performance tests
└── ... (existing tests)
```

## Test Results and Reports

### Load Test Reports
- HTML report: `test-results/load_test_report.html`
- CSV data: `test-results/load_test_results_*.csv`
- Performance charts and statistics

### CI Artifacts
- Load test reports uploaded as GitHub Actions artifacts
- Performance benchmark results (JSON format)
- Test coverage reports

## Advanced Usage

### Custom Load Test Scenarios

Modify `tests/locustfile.py` to add custom user behaviors:

```python
class CustomUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(5)
    def custom_behavior(self):
        # Your custom test scenario
        pass
```

### Running Specific Test Categories

```bash
# Only database tests
pytest tests/test_enum_types.py tests/test_event_time_index.py -v

# Only smoke tests with coverage
pytest tests/test_smoke_ci.py --cov=app --cov-report=html

# Parallel test execution
pytest tests/ -n auto --maxfail=3
```

### Docker Compose Profiles

```bash
# Test services only
docker-compose --profile test up

# Load testing
docker-compose --profile load-test up --abort-on-container-exit

# Full test suite
docker-compose --profile test --profile smoke-test --profile load-test up
```

## Troubleshooting

### Common Issues

**1. Redis Connection Failed**
```bash
# Check if Redis is running
redis-cli ping

# Start Redis
redis-server --daemonize yes
```

**2. Application Won't Start**
```bash
# Check environment variables
cat .env.test

# Check if port is available
lsof -i :8000
```

**3. Load Tests Failing**
```bash
# Reduce load for resource-constrained environments
LOAD_TEST_USERS=5 LOAD_TEST_TIME=30s ./scripts/run_tests.sh load
```

**4. Docker Tests Failing**
```bash
# Clean up Docker resources
docker-compose -f docker-compose.test.yml down -v --remove-orphans
docker system prune -f
```

### Debug Mode

Enable verbose output for detailed debugging:

```bash
./scripts/run_tests.sh smoke --verbose
```

Check application logs during test failures:
```bash
# View recent logs
tail -f logs/app.log

# Check container logs
docker logs <container_name>
```

## Performance Expectations

### Smoke Tests
- Health endpoint: <1 second
- API opportunities: <3 seconds  
- Metrics endpoint: <2 seconds
- Total test time: <2 minutes

### Load Tests
- 95th percentile response time: <5 seconds
- Error rate: <5%
- Concurrent users: 10+ supported
- Memory usage: <512MB

### Integration Tests
- Database operations: <5 seconds
- Full test suite: <15 minutes
- CI pipeline total: <25 minutes

## Contributing

When adding new tests:

1. **Smoke tests**: Add to `test_smoke_ci.py` for critical functionality
2. **Load tests**: Extend `locustfile.py` for new user scenarios  
3. **Integration tests**: Create separate test files for complex features
4. **Update documentation**: Document new test scenarios and expectations

### Test Guidelines

- **Fast feedback**: Smoke tests should complete in <2 minutes
- **Realistic scenarios**: Load tests should simulate actual user behavior
- **Independent tests**: Tests should not depend on external state
- **Clear assertions**: Test failures should provide actionable error messages
- **Resource cleanup**: Always clean up test resources

## Monitoring and Alerts

### CI Monitoring
- GitHub Actions status badges
- Failure notifications via GitHub
- Performance regression detection

### Production Monitoring
- Prometheus metrics collection
- Sentry error tracking
- Structured logging with JSON output
- Health check endpoints for load balancers

The testing infrastructure ensures production readiness through comprehensive validation of performance, reliability, and functionality. 