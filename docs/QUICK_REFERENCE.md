# Quick Reference

Essential commands and configurations for Fair-Edge development.

## 🚀 Common Commands

```bash
# Development
./scripts/setup-dev.sh              # Initial setup
docker compose up -d                # Start all services
docker compose logs -f api          # Watch API logs
docker compose down                 # Stop all services

# Production
./scripts/setup-prod.sh             # Initial setup
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile production up -d

# Testing
./scripts/run_tests.sh smoke        # Quick tests (2 min)
./scripts/run_tests.sh integration  # Full suite (10 min)
pytest tests/test_specific.py -v    # Run specific test

# Database
docker compose exec api alembic upgrade head              # Run migrations
docker compose exec api alembic revision -m "description" # Create migration
docker compose exec db psql -U postgres fairedge         # Database shell

# Cache
docker compose exec redis redis-cli                      # Redis CLI
docker compose exec redis redis-cli FLUSHALL            # Clear cache
```

## 🔧 Environment Variables

```bash
# Backend (.env.local)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx
SUPABASE_SERVICE_ROLE_KEY=xxx
SUPABASE_JWT_SECRET=xxx
ODDS_API_KEY=xxx
REDIS_URL=redis://redis:6379/0

# Frontend (frontend/.env.local)
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=xxx
```

## 📁 Key Files

```
app.py                      # Main FastAPI app
routes/opportunities.py     # Betting endpoints
services/celery_app.py     # Background tasks
frontend/src/App.tsx       # React entry point
docker-compose.yml         # Dev configuration
docker-compose.prod.yml    # Prod overrides
```

## 🌐 Service URLs

**Development:**
- Frontend: http://localhost:5173
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Redis: localhost:6379

**Production:**
- Frontend: https://your-domain.com
- API: https://your-domain.com/api
- Health: https://your-domain.com/health

## 🐛 Troubleshooting

```bash
# Port conflicts
lsof -i :8000 && kill -9 <PID>

# Container issues
docker compose ps
docker compose restart <service>

# Database connection
docker compose exec api python -c "from core.db import engine; print('OK')"

# Clear everything
docker compose down -v
```

## 📊 Celery Tasks

```python
# Scheduled tasks
refresh_data         # Fetch odds from API
calculate_opportunities  # Calculate EV
warm_critical_data      # Warm cache

# Manual execution
docker compose exec celery-worker celery -A services.celery_app.celery_app call tasks.odds.refresh_data
```

## 🔍 Debugging

```bash
# API logs with timestamps
docker compose logs -f --timestamps api

# Search errors
docker compose logs api | grep -i error

# Database queries
docker compose exec db psql -U postgres -c "SELECT * FROM pg_stat_statements;"

# Redis monitoring
docker compose exec redis redis-cli MONITOR
```

## 📝 Git Workflow

```bash
# Feature branch
git checkout -b feature/description
git add .
git commit -m "feat: add new feature"
git push origin feature/description

# Hotfix
git checkout -b hotfix/issue-description
git commit -m "fix: resolve issue"
git push origin hotfix/issue-description
```

## 🚨 Emergency

```bash
# Stop everything
docker compose down

# Backup database
docker compose exec -T db pg_dump -U postgres fairedge > backup.sql

# Restore database
docker compose exec -T db psql -U postgres fairedge < backup.sql

# Force rebuild
docker compose build --no-cache
docker compose up -d --force-recreate
```