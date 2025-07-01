# Development Guide

Complete guide for local development setup and best practices.

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
- Git
- Code editor (VS Code recommended)
- API keys for The Odds API and Supabase

### Environment Configuration

After running `setup-dev.sh`, edit your `.env.local`:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-key
SUPABASE_JWT_SECRET=your-jwt-secret

# External APIs
ODDS_API_KEY=your-odds-api-key

# Redis (Docker internal)
REDIS_URL=redis://redis:6379/0
```

### Manual Setup (Without Docker)

```bash
# Backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

## 📁 Project Structure

```
fair-edge/
├── app.py                  # Main FastAPI application
├── routes/                 # API endpoints
│   ├── opportunities.py    # Betting opportunities
│   ├── auth.py            # Authentication
│   └── analytics.py       # Analytics endpoints
├── services/              # Business logic
│   ├── odds_service.py    # Odds data fetching
│   ├── ev_calculator.py   # EV calculations
│   └── celery_app.py      # Background tasks
├── core/                  # Shared utilities
│   ├── auth.py           # Auth helpers
│   ├── cache.py          # Redis caching
│   └── config.py         # Configuration
├── frontend/             # React application
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/       # Page components
│   │   └── hooks/       # Custom hooks
│   └── package.json
├── tests/               # Test suite
├── docker/              # Docker configurations
└── scripts/             # Helper scripts
```

## 🧪 Testing

### Run Tests

```bash
# Quick smoke tests
./scripts/run_tests.sh smoke

# Full test suite
./scripts/run_tests.sh integration

# Performance tests
./scripts/run_tests.sh load
```

### Writing Tests

```python
# tests/test_opportunities.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_opportunities(client: AsyncClient, auth_headers):
    response = await client.get("/api/opportunities", headers=auth_headers)
    assert response.status_code == 200
    assert "opportunities" in response.json()
```

## 🔄 Development Workflow

### 1. Making Changes

```bash
# Create feature branch
git checkout -b feature/your-feature

# Make changes and test
docker compose logs -f api  # Watch logs

# Run tests
./scripts/run_tests.sh smoke
```

### 2. Database Changes

```bash
# Generate migration
docker compose exec api alembic revision --autogenerate -m "Add new table"

# Apply migration
docker compose exec api alembic upgrade head
```

### 3. Frontend Development

```bash
# Hot reload is enabled by default
# Make changes in frontend/src and see them instantly

# Build for production
cd frontend && npm run build
```

## 🐛 Debugging

### Backend Debugging

```python
# Add breakpoints in code
import pdb; pdb.set_trace()

# Or use logging
import logging
logger = logging.getLogger(__name__)
logger.info(f"Debug info: {variable}")
```

### Frontend Debugging

```typescript
// Use React DevTools
console.log('Debug:', data);

// Network tab for API calls
// React Query DevTools for cache debugging
```

### Common Issues

**Port already in use:**
```bash
# Find and kill process
lsof -i :8000
kill -9 <PID>
```

**Database connection failed:**
```bash
# Check if services are running
docker compose ps

# Restart database
docker compose restart db
```

**Redis connection issues:**
```bash
# Clear Redis cache
docker compose exec redis redis-cli FLUSHALL
```

## 🎨 Code Style

### Python (Backend)
- Follow PEP 8
- Use type hints
- Format with Black: `black .`
- Lint with Ruff: `ruff check .`

### TypeScript (Frontend)
- Use strict mode
- Follow React best practices
- Format with Prettier: `npm run format`
- Lint with ESLint: `npm run lint`

## 📝 Commit Guidelines

```bash
# Format: <type>(<scope>): <subject>

feat(api): add new endpoint for user stats
fix(frontend): resolve race condition in opportunity fetch
docs(readme): update deployment instructions
test(opportunities): add edge case coverage
refactor(cache): optimize Redis key structure
```

## 🔗 Useful Commands

```bash
# View all logs
docker compose logs -f

# Access containers
docker compose exec api bash
docker compose exec frontend sh

# Database shell
docker compose exec db psql -U postgres fairedge

# Redis CLI
docker compose exec redis redis-cli

# Clean everything
docker compose down -v
```

## 📚 Additional Resources

- [API Reference](API.md) - Endpoint documentation
- [Testing Guide](TESTING.md) - Comprehensive testing docs
- [Claude Instructions](CLAUDE.md) - AI assistant guide
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Docs](https://react.dev/)