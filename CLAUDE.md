# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Quick Start
```bash
# Start full development environment (recommended)
./scripts/deploy.sh development

# Manual local development
pip install -r requirements.txt
cd frontend && npm install && npm run dev
uvicorn app:app --reload --port 8000
```

### Testing
```bash
# Quick health checks
./scripts/run_tests.sh smoke

# Performance testing
./scripts/run_tests.sh load

# Full test suite
./scripts/run_tests.sh integration

# Install test dependencies
./scripts/run_tests.sh install-deps
```

### Frontend Commands
```bash
cd frontend
npm run dev          # Development server
npm run build        # Production build
npm run lint         # ESLint linting
npm run preview      # Preview build
```

### Database Management
```bash
# Generate migrations
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Downgrade
alembic downgrade -1
```

### Deployment
```bash
# Development environment
./scripts/deploy.sh development

# Production deployment
./scripts/deploy.sh production

# View logs
./scripts/deploy.sh logs development
```

## Architecture Overview

This is a monorepo sports betting analysis platform with the following structure:

### Core Components
- **Frontend**: React TypeScript app with Vite (port 5173)
- **Backend**: FastAPI with JSON APIs (port 8000)
- **Database**: PostgreSQL with Supabase authentication
- **Cache**: Redis for data caching and Celery broker (port 6379)
- **Background Tasks**: Celery worker and beat scheduler
- **Deployment**: Docker + Docker Compose

### Key Directories
- `frontend/` - React TypeScript application
- `core/` - Core utilities, configuration, and business logic
- `services/` - Background services (Celery, data processing, API clients)
- `routes/` - FastAPI route modules
- `models.py` - SQLAlchemy database models
- `docker/` - All Docker configurations and entrypoints
- `scripts/` - Deployment and utility scripts
- `tests/` - Comprehensive test suite

### Data Flow
1. Background tasks fetch odds data from The Odds API via Celery
2. Data is processed and cached in Redis
3. EV calculations are performed using core business logic
4. Frontend displays opportunities via FastAPI JSON APIs
5. User authentication handled through Supabase

### Key Features
- **EV Analysis**: Positive expected value calculation across sportsbooks
- **Real-time Updates**: 5-minute refresh intervals via background tasks
- **Tiered Access**: Free (main lines) vs Premium (all markets)
- **Market Coverage**: Moneyline, spreads, totals, player props

## Environment Configuration

### Environment Files (Root Level)
- `.env.development` - Development settings (backend + frontend)
- `.env.production` - Production settings (backend + frontend)
- `.env.example` - Template for setup

### Key Variables
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

## Development Workflow

### Daily Development
1. Start environment: `./scripts/deploy.sh development`
2. Make changes (auto-reload enabled for both frontend/backend)
3. Run smoke tests before committing: `./scripts/run_tests.sh smoke`
4. View logs for debugging: `./scripts/deploy.sh logs development`

### Code Quality
- **Python**: Use Black formatter, type hints required
- **TypeScript**: ESLint enabled, strict mode
- **Testing**: Smoke tests for critical paths, load tests for performance

### Background Services
The platform relies heavily on Celery for:
- Periodic odds data fetching from The Odds API
- EV calculation processing
- Data caching optimization

Core Celery services:
- `celery_worker` - Processes background tasks
- `celery_beat` - Schedules periodic tasks
- Redis broker for task queuing

### Database Schema
- Uses SQLAlchemy with Alembic migrations
- Enum types for sports, markets, bet types
- Optimized indexes for event time queries
- Supabase integration for user authentication

## Troubleshooting

### Common Issues
- **Services won't start**: Check Docker status and port availability
- **Environment variables**: Verify frontend can read root-level env files
- **Redis connection**: Test with `redis-cli ping`
- **Celery tasks**: Check worker status with `celery inspect active`

### Debugging
```bash
# Check service status
./scripts/deploy.sh status development

# View specific service logs
docker-compose logs -f api
docker-compose logs -f celery_worker

# Test Redis connectivity
redis-cli -u ${REDIS_URL} ping

# Check database connection
python -c "import asyncpg; print('DB connection test')"
```