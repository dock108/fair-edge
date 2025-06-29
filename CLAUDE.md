# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Quick Start Commands

```bash
# Start development environment
docker compose up -d

# View logs
docker compose logs -f api

# Run tests
./scripts/run_tests.sh smoke        # Quick health checks
./scripts/run_tests.sh integration  # Full test suite
./scripts/run_tests.sh load         # Performance testing

# Database migrations
alembic upgrade head                # Apply migrations
alembic revision --autogenerate -m "description"  # Generate migrations
```

## Architecture Overview

**Tech Stack:**
- **Frontend**: React 19 + TypeScript + Vite + TailwindCSS (port 5173)
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL/Supabase (port 8000)
- **Cache**: Redis for caching and Celery broker (port 6379)
- **Background**: Celery worker and beat scheduler
- **Deployment**: Docker + Docker Compose

**Key Components:**
- `app.py` - Main FastAPI application (286 lines, refactored from 1,926 lines)
- `routes/` - Modular API endpoints (opportunities, auth, analytics, etc.)
- `services/` - Background services and business logic
- `core/` - Utilities, configuration, and shared components
- `frontend/src/` - React application with TypeScript
- `tests/` - Comprehensive test suite with smoke, integration, and load tests

## Environment Configuration

**Environment Files (Root Level):**
- `.env.example` - Template for setup (copy to create local configs)
- `.env.development` - Development settings
- `.env.production` - Production template (copy to .env.production.local)
- `.env.local` - Local environment file (gitignored)

**Key Variables:**
```bash
# Backend
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret
ODDS_API_KEY=your-odds-api-key
REDIS_URL=redis://localhost:6379/0

# Frontend (VITE_* prefix)
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=your-supabase-url
VITE_SUPABASE_ANON_KEY=your-anon-key
```

## Code Quality Standards

**Python (Backend):**
- Use type hints for all functions
- Follow Black formatting
- Implement proper error handling
- Use structured logging (JSON in production)

**TypeScript (Frontend):**
- Strict mode enabled
- Use proper interfaces for API responses
- Implement loading states and error handling
- Follow React best practices

## Testing Strategy

**Test Types:**
- **Smoke Tests**: Basic functionality and health checks (`tests/test_smoke_ci.py`)
- **Load Tests**: Performance testing with Locust (`tests/locustfile.py`)
- **Integration Tests**: Full system testing with database
- **CI Pipeline**: GitHub Actions with comprehensive testing

**Test Execution:**
```bash
# Run before committing
./scripts/run_tests.sh smoke

# Performance validation
./scripts/run_tests.sh load
```

## Deployment Process

**Development:**
```bash
# Start development environment
docker compose -f docker-compose.dev.yml up -d
# Access: Frontend (5173), Backend (8000), API Docs (8000/docs)
```

**Production:**
```bash
# 1. Configure environment
cp .env.production .env.production.local
# Edit .env.production.local with your actual values

# 2. Build and deploy
docker compose up -d

# 3. Build and deploy frontend
docker compose --profile build build frontend
docker run --rm -v fairedge-prod_frontend_build:/target fairedge-prod-frontend sh -c "cp -r /usr/share/nginx/html/* /target/"
docker compose restart caddy

# 4. Verify deployment
curl http://your-domain/health
```

**Production Notes:**
- Uses host networking for IPv6 compatibility (Hetzner, DigitalOcean, etc.)
- Frontend served as static files via Caddy reverse proxy
- API accessible at `/health`, `/api/*`, `/docs`
- Smart refresh system: 15-min intervals when dashboard active
- Background workers may need manual restart if migrations are enabled

## Key Services

**Celery Tasks:**
- `tasks.odds.refresh_data` - Fetch odds from external API
- `tasks.ev.calculate_opportunities` - Calculate EV for betting opportunities
- `tasks.cache.warm_critical_data` - Warm important cache keys

**Background Processing:**
- Celery worker processes background tasks
- Celery beat schedules periodic tasks (every 5 minutes)
- Redis serves as message broker and cache

## Common Troubleshooting

**Services won't start:**
```bash
# Check Docker status
./scripts/deploy.sh status development

# View logs
./scripts/deploy.sh logs development
```

**Database issues:**
```bash
# Check connection
python -c "import asyncpg; print('DB connection test')"

# Apply migrations
alembic upgrade head
```

**Redis issues:**
```bash
# Test connectivity
redis-cli -u ${REDIS_URL} ping

# Clear cache if needed
redis-cli -u ${REDIS_URL} FLUSHALL
```

**Celery issues:**
```bash
# Check worker status
celery -A services.celery_app.celery_app inspect active

# Check scheduled tasks
celery -A services.celery_app.celery_app inspect scheduled
```

## Recent Major Changes

**Sprint 5 Completed (Dec 2024):**
- ✅ Refactored monolithic app.py (1,926 → 286 lines)
- ✅ Fixed CI pipeline with comprehensive testing
- ✅ Named Celery tasks explicitly for observability
- ✅ Fixed upgrade page rendering with proper React component
- ✅ Added loading state UI with skeleton/shimmer indicators
- ✅ Added UI/config polishes (favicon, meta tags, etc.)
- ✅ Streamlined documentation structure

**Current Status:**
- Production-ready with 90%+ test coverage
- Modular architecture with separation of concerns
- Comprehensive CI/CD pipeline
- Professional UI/UX with loading states
- Proper error handling and monitoring