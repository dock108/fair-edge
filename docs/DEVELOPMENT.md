# Development Guide

Complete guide for local development setup and best practices for Fair-Edge SaaS platform.

## 🚀 Quick Start

```bash
# One-time setup
./scripts/setup-dev.sh

# Start development
docker compose up -d

# Access
# Frontend: http://localhost:5173
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## 🛠️ Development Setup

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for frontend development)
- Git
- Code editor (VS Code recommended)
- API keys for The Odds API and Supabase

### Environment Configuration

The application uses **Supabase** for authentication and database, **Stripe** for payments, and Redis for caching.

After running `setup-dev.sh`, edit your `environments/development.env`:

```bash
# Supabase Configuration (Required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-key
SUPABASE_JWT_SECRET=your-jwt-secret

# External APIs
ODDS_API_KEY=your-odds-api-key

# Stripe Configuration (Test Keys)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_BASIC_PRICE=price_...
STRIPE_PREMIUM_PRICE=price_...

# Redis (Docker internal)
REDIS_URL=redis://redis:6379/0

# Frontend Variables (auto-populated)
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

### Initial Supabase Setup

1. Create a Supabase project at https://supabase.com
2. Run the SQL schema (check `/alembic/versions/` for latest schema)
3. Set up Row Level Security policies
4. Configure authentication settings

### Stripe Setup for Testing

```bash
# Setup Stripe test environment
./scripts/setup-stripe-testing.sh

# Start webhook forwarding for local development
./scripts/start-webhook-forwarding.sh
```

## 🏗️ Architecture Overview

**Current Stack:**
- **Frontend**: React 19 + TypeScript + Vite (port 5173)
- **Backend**: FastAPI + Supabase REST API (port 8000)
- **Database**: Supabase (PostgreSQL + REST API + Auth)
- **Payments**: Stripe with webhook integration
- **Cache**: Redis for caching and Celery broker (port 6379)
- **Background**: Celery worker and beat scheduler

**Key Components:**
- `app.py` - Main FastAPI application with modular routes
- `routes/` - API endpoints (opportunities, auth, billing, etc.)
- `core/auth.py` - Supabase JWT authentication
- `routes/billing.py` - Stripe subscription management
- `frontend/src/` - React application with TypeScript
- `db.py` - Supabase REST API client wrapper

## 🧪 Testing

### Quick Testing Commands

```bash
# Backend smoke tests (2 minutes)
./scripts/run_tests.sh smoke

# Frontend E2E tests (Playwright)
cd frontend && npm run test:e2e

# Stripe subscription testing
./scripts/run-subscription-tests.sh

# Full test suite (10 minutes)
./scripts/run_tests.sh integration
```

### Playwright E2E Testing

Our E2E tests cover the complete subscription flow using pre-configured test users:

```bash
# Install Playwright browsers
cd frontend && npx playwright install

# Run subscription flow tests
npm run test:e2e

# Debug tests with UI
npx playwright test --debug

# Generate test report
npx playwright show-report
```

**Test Users (pre-confirmed in Supabase):**
- Free: `test-free@fairedge.com` / `TestPassword123!`
- Basic: `test-basic@fairedge.com` / `TestPassword123!`
- Premium: `test-premium@fairedge.com` / `TestPassword123!`

### Stripe Testing

```bash
# Setup Stripe test environment
./scripts/setup-stripe-testing.sh

# Start webhook forwarding
./scripts/start-webhook-forwarding.sh

# Test webhook integration
curl -X POST http://localhost:8000/api/billing/stripe/webhook \
  -H "Content-Type: application/json" \
  -d '{"type": "checkout.session.completed"}'

# Use test card numbers:
# Success: 4242 4242 4242 4242
# Decline: 4000 0000 0000 0002
```

### Load Testing

```bash
# Performance tests with Locust
./scripts/run_tests.sh load

# Custom load test
locust -f tests/locustfile.py --host=http://localhost:8000
```

## 🔄 Development Workflow

### 1. Making Changes

```bash
# Create feature branch
git checkout -b feature/billing-improvements

# Start development environment
docker compose up -d

# Watch logs
docker compose logs -f api

# Make changes and test
./scripts/run_tests.sh smoke
```

### 2. Supabase Schema Changes

**Note:** We use Supabase directly, not Alembic migrations.

```bash
# Option 1: Use Supabase Dashboard
# Go to https://supabase.com/dashboard > SQL Editor
# Run your schema changes

# Option 2: Use Supabase CLI
supabase db reset --local
supabase db push
```

### 3. Frontend Development

```bash
# Frontend has hot reload enabled
# Make changes in frontend/src/ and see them instantly

# Test subscription flows
cd frontend && npm run test:e2e

# Build for production
npm run build
```

### 4. Stripe Development

```bash
# Test webhook locally
./scripts/start-webhook-forwarding.sh

# Check webhook logs
tail -f stripe-webhook.log

# Verify subscription status
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/billing/subscription-status
```

## 🐛 Debugging

### Backend Debugging

```python
# Add logging in code
import logging
logger = logging.getLogger(__name__)
logger.info(f"Debug info: {variable}")

# Check Supabase connections
from db import get_supabase
client = get_supabase()
response = client.table('profiles').select('*').limit(1).execute()
```

### Authentication Debugging

```bash
# Test JWT token validation
curl -H "Authorization: Bearer <jwt_token>" \
  http://localhost:8000/api/user-info

# Check user profile sync
curl -H "Authorization: Bearer <jwt_token>" \
  http://localhost:8000/api/billing/subscription-status
```

### Common Issues

**Supabase connection issues:**
```bash
# Check environment variables
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_ROLE_KEY

# Test connection
python -c "from db import get_supabase; print(get_supabase().table('profiles').select('*').limit(1).execute())"
```

**Stripe webhook issues:**
```bash
# Check webhook secret
echo $STRIPE_WEBHOOK_SECRET

# Verify webhook endpoint
curl -X POST http://localhost:8000/api/billing/stripe/webhook \
  -H "stripe-signature: test"
```

**Frontend auth issues:**
```bash
# Clear browser storage
# Check Network tab for 401/403 errors
# Verify Supabase configuration in browser dev tools
```

## 📋 Quick Reference

### Essential Commands

```bash
# Development lifecycle
./scripts/setup-dev.sh              # Initial setup
docker compose up -d                # Start all services
docker compose logs -f api          # Watch API logs
docker compose down                 # Stop all services

# Testing
./scripts/run_tests.sh smoke        # Quick tests (2 min)
cd frontend && npm run test:e2e     # E2E tests
./scripts/run-subscription-tests.sh # Stripe tests

# Stripe development
./scripts/setup-stripe-testing.sh   # Setup Stripe test env
./scripts/start-webhook-forwarding.sh # Start webhook forwarding

# Cache management
docker compose exec redis redis-cli # Redis CLI
docker compose exec redis redis-cli FLUSHALL # Clear cache

# Container access
docker compose exec api bash        # API container shell
docker compose exec frontend sh     # Frontend container shell
```

### Environment Quick Setup

```bash
# Copy template
cp environments/development.env environments/development.env.local

# Edit with your values
nano environments/development.env.local

# Restart to pick up changes
docker compose restart
```

### Useful Development URLs

- **Frontend**: http://localhost:5173
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Supabase Dashboard**: https://supabase.com/dashboard
- **Stripe Dashboard**: https://dashboard.stripe.com

## 🎨 Code Style

### Python (Backend)
- Follow PEP 8
- Use type hints for all functions
- Format with Black: `black .`
- Use structured logging: `logger.info("Message", extra={"key": "value"})`

### TypeScript (Frontend)
- Use strict mode
- Implement proper interfaces for API responses
- Follow React best practices
- Use proper error boundaries

### API Design
- RESTful endpoints with proper HTTP methods
- Consistent error response format
- Comprehensive OpenAPI documentation
- Proper authentication on all protected routes

## 📝 Commit Guidelines

```bash
# Format: <type>(<scope>): <subject>

feat(billing): add subscription upgrade flow
fix(auth): resolve token refresh race condition
docs(api): update billing endpoint documentation
test(e2e): add subscription cancellation test
refactor(auth): optimize Supabase client usage
```

## 📚 Additional Resources

- [API Reference](API.md) - Complete endpoint documentation
- [Deployment Guide](DEPLOYMENT.md) - Production deployment
- [Operations Guide](OPERATIONS.md) - Monitoring and maintenance
- [Claude Instructions](CLAUDE.md) - AI assistant integration
- [Phase 3 Testing](PHASE3_MANUAL_TESTING_CHECKLIST.md) - Manual test procedures

**External Documentation:**
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Supabase Documentation](https://supabase.com/docs)
- [Stripe API Reference](https://stripe.com/docs/api)
- [Playwright Testing](https://playwright.dev/)
- [React Documentation](https://react.dev/)
