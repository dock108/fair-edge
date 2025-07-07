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

```bash
# Backend testing
./scripts/run_tests.sh smoke        # Quick health checks (2 min)
./scripts/run_tests.sh integration  # Full test suite (10 min)

# Frontend E2E testing (Playwright)
cd frontend && npm run test:e2e     # Subscription flow tests

# Stripe testing
./scripts/setup-stripe-testing.sh   # Setup test environment
./scripts/start-webhook-forwarding.sh  # Local webhook testing
```

## 📄 License

Proprietary software. All rights reserved.