# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Quick Start Commands

```bash
# Start development environment
docker compose up -d

# View logs
docker compose logs -f api

# Run tests
./scripts/run_tests.sh smoke        # Quick health checks (2 min)
cd frontend && npm run test:e2e     # Playwright E2E tests
./scripts/run-subscription-tests.sh # Stripe subscription tests

# Stripe testing
./scripts/setup-stripe-testing.sh   # Setup test environment
./scripts/start-webhook-forwarding.sh # Start webhook forwarding
```

## Architecture Overview

**Tech Stack:**
- **Frontend**: React 19 + TypeScript + Vite + TailwindCSS (port 5173)
- **Backend**: FastAPI + Supabase REST API (port 8000)
- **Database**: Supabase (PostgreSQL + REST API + Authentication)
- **Payments**: Stripe with webhook integration
- **Cache**: Redis for caching and Celery broker (port 6379)
- **Background**: Celery worker and beat scheduler
- **Deployment**: Docker + Docker Compose

**Key Components:**
- `app.py` - Main FastAPI application (modular, 311 lines)
- `routes/` - Modular API endpoints (opportunities, auth, billing, etc.)
- `routes/billing.py` - Stripe subscription management with webhook processing
- `core/auth.py` - Supabase JWT authentication and authorization
- `db.py` - Supabase REST API client wrapper
- `frontend/src/` - React SPA with TypeScript
- `frontend/tests/e2e/` - Playwright E2E subscription flow tests

## Environment Configuration

**Environment Files:**
- `environments/development.env` - Development settings template
- `environments/production.env` - Production settings template
- Create local copies with `.local` suffix (gitignored)

**Key Variables:**
```bash
# Supabase (Required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-key  
SUPABASE_JWT_SECRET=your-jwt-secret

# Stripe (Required for billing)
STRIPE_SECRET_KEY=sk_test_... (or sk_live_...)
STRIPE_PUBLISHABLE_KEY=pk_test_... (or pk_live_...)
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_BASIC_PRICE=price_...
STRIPE_PREMIUM_PRICE=price_...

# External APIs
ODDS_API_KEY=your-odds-api-key

# Infrastructure  
REDIS_URL=redis://redis:6379/0

# Frontend (VITE_* prefix)
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

## Database Architecture

**Important:** This application uses **Supabase REST API directly**, not SQLAlchemy or direct PostgreSQL connections.

**Database Operations:**
```python
# Correct approach (Supabase REST API)
from db import get_supabase
supabase = get_supabase()
result = supabase.table('profiles').select('*').eq('id', user_id).execute()

# Incorrect approach (PostgreSQL direct)
# from sqlalchemy import text
# await session.execute(text("SELECT * FROM profiles WHERE id = :id"), {"id": user_id})
```

**Schema Management:**
- Use Supabase Dashboard > SQL Editor for schema changes
- Alembic migrations exist but are **not used** - they're legacy
- Row Level Security (RLS) policies are configured in Supabase

## Authentication System

**Supabase JWT Flow:**
1. Frontend authenticates with Supabase (`supabase.auth.signInWithPassword()`)
2. Frontend receives JWT token from Supabase
3. Frontend sends JWT in `Authorization: Bearer <token>` header
4. Backend validates JWT using `core.auth.get_current_user()`
5. Backend fetches user profile from Supabase `profiles` table

**User Roles:**
- `free` - Limited access, can see unprofitable bets only
- `basic` - All main betting lines, unlimited EV access
- `subscriber` - Premium features, all markets, advanced analytics  
- `admin` - Full platform access including debug endpoints

## Stripe Integration

**Subscription Flow:**
1. User clicks upgrade on `/pricing` page
2. Frontend calls `POST /api/billing/create-checkout-session`
3. User completes Stripe Checkout
4. Stripe webhook `checkout.session.completed` hits `POST /api/billing/stripe/webhook`
5. Backend updates user role in Supabase `profiles` table
6. User automatically gains access to premium features

**Webhook Events Handled:**
- `checkout.session.completed` - Upgrade user to paid tier
- `customer.subscription.updated` - Handle plan changes
- `customer.subscription.deleted` - Downgrade to free tier
- `invoice.payment_succeeded` - Confirm active subscription
- `invoice.payment_failed` - Handle failed payments

**Test Users (Pre-confirmed in Supabase):**
- Free: `test-free@fairedge.com` / `TestPassword123!`
- Basic: `test-basic@fairedge.com` / `TestPassword123!`
- Premium: `test-premium@fairedge.com` / `TestPassword123!`

## Code Quality Standards

**Python (Backend):**
- Use type hints for all functions
- Supabase operations instead of raw SQL
- Proper error handling with structured logging
- JWT authentication on all protected routes

**TypeScript (Frontend):**
- Strict mode enabled
- Proper interfaces for API responses
- Error boundaries and loading states
- Supabase client for authentication

## Testing Strategy

**Test Types:**
- **Smoke Tests**: Basic functionality and health checks (`./scripts/run_tests.sh smoke`)
- **E2E Tests**: Playwright subscription flow testing (`cd frontend && npm run test:e2e`)
- **Stripe Tests**: Webhook and payment flow testing (`./scripts/run-subscription-tests.sh`)
- **Load Tests**: Performance testing with Locust (`./scripts/run_tests.sh load`)

**E2E Testing Notes:**
- Tests use pre-confirmed Supabase users to bypass email verification
- Tests cover complete subscription flow: login → upgrade → downgrade → cancel
- Webhook testing requires `./scripts/start-webhook-forwarding.sh`

## Deployment Process

**Development:**
```bash
# Start development environment
docker compose up -d
# Access: Frontend (5173), Backend (8000), API Docs (8000/docs)
```

**Production:**
```bash
# 1. Configure environment
cp environments/production.env environments/production.env.local
# Edit environments/production.env.local with your actual values

# 2. Deploy
docker compose -f docker-compose.production.yml up -d

# 3. Verify deployment
curl http://your-domain/health
```

**Production Notes:**
- Single production Docker Compose file: `docker-compose.production.yml`
- Frontend served as static files via Caddy reverse proxy
- API accessible at `/health`, `/api/*`, `/docs`
- Stripe webhooks require HTTPS endpoint configuration

## Key Services

**API Endpoints:**
- `GET /health` - System health check
- `GET /api/opportunities` - Betting opportunities (role-based access)
- `POST /api/billing/create-checkout-session` - Start Stripe checkout
- `GET /api/billing/subscription-status` - User subscription info
- `POST /api/billing/stripe/webhook` - Stripe webhook processor
- `GET /api/user-info` - User profile and capabilities

**Background Processing:**
- Celery worker processes background tasks
- Celery beat schedules periodic data refresh
- Redis serves as message broker and cache
- Smart refresh based on business hours and activity

## Common Troubleshooting

**Supabase connection issues:**
```bash
# Test Supabase connection
python -c "from db import get_supabase; print(get_supabase().table('profiles').select('*').limit(1).execute())"

# Check environment variables
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_ROLE_KEY
```

**Authentication issues:**
```bash
# Test JWT validation
curl -H "Authorization: Bearer <jwt_token>" http://localhost:8000/api/user-info

# Check user profile sync
curl -H "Authorization: Bearer <jwt_token>" http://localhost:8000/api/billing/subscription-status
```

**Stripe webhook issues:**
```bash
# Start webhook forwarding for local development
./scripts/start-webhook-forwarding.sh

# Test webhook endpoint
curl -X POST http://localhost:8000/api/billing/stripe/webhook \
  -H "Content-Type: application/json" \
  -H "stripe-signature: test" \
  -d '{"type": "checkout.session.completed"}'
```

**Billing route errors:**
```bash
# Check if billing routes are loaded
curl http://localhost:8000/api/billing/subscription-status

# Common issue: get_db() errors
# Solution: Ensure db.py provides Supabase session wrapper, not SQLAlchemy
```

## Recent Major Changes

**Current Status (January 2025):**
- ✅ Migrated from PostgreSQL direct connections to Supabase REST API only
- ✅ Implemented comprehensive Stripe subscription billing
- ✅ Added Playwright E2E testing for subscription flows
- ✅ Created pre-confirmed test users to bypass email verification issues
- ✅ Modular FastAPI architecture with proper separation of concerns
- ✅ Production-ready Docker deployment with Caddy reverse proxy

**Known Issues Being Addressed:**
- Billing routes expect SQLAlchemy AsyncSession but get Supabase session wrapper
- Need to refactor billing operations to use direct Supabase table operations
- Some legacy Alembic migrations exist but are not used

**Architecture Evolution:**
- **Before**: FastAPI + SQLAlchemy + PostgreSQL
- **Now**: FastAPI + Supabase REST API + Stripe
- **Database**: Supabase handles auth, storage, and real-time features
- **Payments**: Stripe handles subscription billing with webhook integration
- **Testing**: Playwright covers full subscription user journeys

**Data Access Pattern:**
```python
# Current correct pattern
from db import get_supabase
supabase = get_supabase()
user_data = supabase.table('profiles').select('role, subscription_status').eq('email', email).execute()

# Legacy pattern (don't use)
# from sqlalchemy import text
# result = await session.execute(text("SELECT role FROM profiles WHERE email = :email"))
```

This architecture provides a modern, scalable SaaS platform with integrated authentication, payments, and comprehensive testing.