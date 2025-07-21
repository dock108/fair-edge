# Fair-Edge - Sports Betting EV Analyzer

A professional sports betting analysis platform that identifies positive expected value (+EV) opportunities across multiple sportsbooks.

## 🚀 Quick Start

```bash
# Development
./scripts/setup-dev.sh              # One-time setup
docker compose up -d                # Start services

# Production  
./scripts/setup-prod.sh             # One-time setup
docker compose -f docker-compose.production.yml up -d
```

**Access Points:**
- Frontend: http://localhost:5173 (dev) / http://localhost (prod)
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📋 Requirements

- Docker & Docker Compose
- Git
- API Keys: The Odds API, Supabase

## 🏗️ Architecture

**Stack:** React + TypeScript • FastAPI • Supabase • Redis • Celery

**Key Features:**
- Real-time +EV opportunity detection across 10+ sportsbooks
- Role-based access control (Free/Basic/Premium/Admin)
- Stripe subscription billing with webhook integration
- Sub-100ms response times with intelligent caching
- Automated data refresh with smart scheduling

## 📚 Documentation

- **[Development Guide](docs/DEVELOPMENT.md)** - Setup, configuration, troubleshooting
- **[API Reference](docs/API.md)** - Endpoints, authentication, examples
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment procedures
- **[Claude Instructions](docs/CLAUDE.md)** - AI assistant integration guide

## 🧪 Testing

### **Comprehensive Testing Infrastructure**

Fair-Edge maintains 460+ tests across backend and iOS platforms with automated CI/CD integration.

#### **Backend Testing (85% Coverage)**
```bash
# Full test suite with coverage
pytest tests/unit/ --cov=. --cov-report=term-missing

# Quick health checks
./scripts/run_tests.sh smoke        # Quick health checks (2 min)
./scripts/run_tests.sh integration  # Full test suite (10 min)

# Specific test categories
pytest tests/unit/test_core/        # Business logic tests
pytest tests/unit/test_routes/      # API endpoint tests
pytest tests/unit/test_auth/        # Authentication tests
```

#### **iOS Testing (75% Coverage)**
```bash
# Navigate to iOS project
cd ios/FairEdge

# Run all iOS tests with coverage
xcodebuild test -scheme FairEdge \
  -destination "platform=iOS Simulator,name=iPhone 15,OS=17.0" \
  -enableCodeCoverage YES

# Run specific test suites
xcodebuild test -only-testing:FairEdgeTests/PushNotificationServiceTests
xcodebuild test -testPlan FairEdgeUITests  # UI tests only
```

#### **Quality Assurance**
```bash
# Code quality checks (matches CI exactly)
pre-commit run --all-files

# iOS code quality
cd ios/FairEdge && swiftlint lint --strict
```

#### **Frontend E2E Testing**
```bash
# Frontend E2E testing (Playwright)
cd frontend && npm run test:e2e     # Subscription flow tests
```

#### **Payment Testing**
```bash
# Stripe testing
./scripts/setup-stripe-testing.sh   # Setup test environment
./scripts/start-webhook-forwarding.sh  # Local webhook testing
```

### **Testing Documentation**
- **[Backend Testing Guide](TEST_COVERAGE_SUMMARY.md)** - Python testing infrastructure details
- **[iOS Testing Guide](ios/iOS_TESTING_GUIDE.md)** - Swift testing patterns and best practices
- **[CI/CD Pipeline](.github/workflows/ci.yml)** - Automated testing workflow

## 📄 License

Proprietary software. All rights reserved.