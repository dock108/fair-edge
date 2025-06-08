# Development Guide

This guide provides comprehensive information for developers working on the bet-intel project.

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+** with pip
- **Node.js 18+** with npm
- **Redis** for caching and task queue
- **PostgreSQL** or Supabase account
- **Git** for version control

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/bet-intel.git
   cd bet-intel
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Quick start (recommended - Full Docker)**
   ```bash
   # Start everything (frontend + backend) in Docker
   ./scripts/start_dev_full.sh
   ```

   **Alternative: Backend Docker + Local Frontend**
   ```bash
   # Start backend services only
   ./scripts/start_local_dev.sh
   
   # In another terminal, start frontend locally
   cd frontend
   npm install
   npm run dev
   ```

   **Alternative: Everything Local**
   ```bash
   # Start backend services locally (no Docker)
   ./scripts/start_local_no_docker.sh
   
   # In another terminal, start frontend
   cd frontend
   npm install
   npm run dev
   ```

4. **Verify setup**
   ```bash
   ./scripts/check_status.sh
   ```

5. **Access your application**
   - **Frontend**: http://localhost:5173 (React app with hot reload)
   - **Backend API**: http://localhost:8000
   - **API Docs**: http://localhost:8000/docs
   - **Celery Flower**: http://localhost:5555 (task monitoring)

6. **Stop development environment**
   ```bash
   ./scripts/stop_dev.sh
   ```

## 🏗 Architecture Overview

### System Components

```mermaid
graph LR
    A[React Frontend] -->|HTTP/JSON| B[FastAPI Backend]
    B -->|Cache| C[Redis]
    B -->|Database| D[PostgreSQL]
    B -->|Tasks| E[Celery Workers]
    F[Celery Beat] -->|Schedule| E
    G[The Odds API] -->|Data| E
```

### Directory Structure

```
bet-intel/
├── app.py                 # Main FastAPI application
├── core/                  # Core utilities and configuration
│   ├── auth.py           # Authentication logic
│   ├── settings.py       # Configuration management
│   └── ...
├── services/             # Business logic services
│   ├── tasks.py          # Celery background tasks
│   ├── redis_cache.py    # Cache management
│   └── ...
├── routes/               # API route modules
├── models.py             # Database models
├── utils/                # Shared utilities
│   ├── odds_utils.py     # Odds conversion functions
│   └── math_utils.py     # Mathematical calculations
├── frontend/             # React SPA
│   ├── src/
│   ├── public/
│   └── package.json
├── docs/                 # Documentation
├── tests/                # Test suite
└── scripts/              # Development scripts
```

## 🛠 Development Workflow

### Backend Development

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start services manually** (alternative to start_local_dev.sh)
   ```bash
   # Terminal 1: Redis
   redis-server
   
   # Terminal 2: Celery Worker
   celery -A worker worker --loglevel=info
   
   # Terminal 3: Celery Beat (scheduler)
   celery -A worker beat --loglevel=info
   
   # Terminal 4: FastAPI server
   uvicorn app:app --reload --port 8000
   ```

3. **Access backend services**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

### Frontend Development

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server**
   ```bash
   npm run dev
   ```

3. **Access frontend**
   - Application: http://localhost:5173
   - Hot reload enabled for React components

### Database Migrations

```bash
# Generate new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Downgrade if needed
alembic downgrade -1
```

## 🧪 Testing

### Quick Testing
```bash
# Run smoke tests (2-3 minutes)
./scripts/run_tests.sh smoke

# Run load tests (5-10 minutes)  
./scripts/run_tests.sh load

# Run full integration tests (10-15 minutes)
./scripts/run_tests.sh integration
```

### Test Types

1. **Smoke Tests** (`tests/test_smoke_ci.py`)
   - Health endpoint verification
   - API documentation accessibility
   - Rate limiting functionality
   - Basic error handling

2. **Load Tests** (`tests/locustfile.py`)
   - Performance testing with realistic user scenarios
   - Concurrent user simulation
   - Error rate monitoring

3. **Integration Tests**
   - Database connectivity
   - Redis functionality
   - End-to-end API workflows

### Running Tests Manually

```bash
# Python tests
pytest tests/ -v

# Frontend tests
cd frontend
npm test

# Docker tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 🔧 Configuration

### Environment Variables

**Essential Configuration** (`.env`):
```bash
# Database & Authentication
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret
DB_CONNECTION_STRING=postgresql://user:pass@host:port/db

# External APIs
ODDS_API_KEY=your-odds-api-key
ODDS_API_BASE_URL=https://api.the-odds-api.com/v4

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Application Settings
APP_ENV=development
DEBUG_MODE=true
REFRESH_INTERVAL_MINUTES=5

# Optional: Stripe (for payments)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

**Frontend Configuration** (`frontend/.env.development`):
```bash
VITE_API_URL=http://localhost:8000
```

### Feature Flags

Toggle features via environment variables:
```bash
# Enable advanced analytics
ENABLE_ADVANCED_ANALYTICS=true

# Enable admin features
ENABLE_ADMIN_DASHBOARD=true
```

## 📊 Data Processing Pipeline

### EV Calculation Flow

1. **Data Ingestion** (Every 5 minutes)
   ```python
   # services/tasks.py
   @shared_task
   def refresh_odds_data():
       raw_data = fetch_raw_odds_data()
       opportunities = process_opportunities(raw_data)
       store_ev_data(opportunities)
   ```

2. **EV Analysis** 
   ```python
   # Core EV calculation
   fair_probability = american_to_probability(fair_odds)
   market_decimal = american_to_decimal(market_odds)
   ev = (fair_probability * market_decimal) - 1
   ```

3. **Role-based Filtering**
   ```python
   # Filter by user role
   if user.role == "free":
       opportunities = filter_main_lines_only(opportunities)
   elif user.role in ["subscriber", "admin"]:
       opportunities = opportunities  # All markets
   ```

### Adding New Markets

1. **Update models** (`models.py`)
2. **Add processing logic** (`services/fastapi_data_processor.py`)
3. **Update cache keys** (`services/redis_cache.py`)
4. **Add frontend components** (`frontend/src/components/`)

## 🚀 Deployment

### Local Production Testing

```bash
# Build frontend
cd frontend
npm run build

# Test production build
npm run preview

# Build Docker image
docker build -t bet-intel .
docker run -p 8000:8000 bet-intel
```

### Environment-specific Deployment

**Development**: Use `./start_local_dev.sh`
**Staging**: Deploy with docker-compose.yml
**Production**: Use container orchestration (K8s, ECS)

### Environment Variables by Environment

| Variable | Development | Staging | Production |
|----------|------------|---------|------------|
| DEBUG_MODE | true | false | false |
| APP_ENV | development | staging | production |
| CORS_ORIGINS | localhost:* | staging-domain | prod-domain |

## 🔍 Debugging

### Common Issues

1. **Redis Connection Errors**
   ```bash
   # Check Redis status
   redis-cli ping
   
   # Restart Redis
   sudo service redis restart
   ```

2. **Celery Worker Issues**
   ```bash
   # Check worker status
   celery -A worker inspect active
   
   # Purge task queue
   celery -A worker purge
   ```

3. **Database Connection Issues**
   ```bash
   # Test database connection
   python -c "from db import get_db; print('DB connection OK')"
   ```

### Debugging Tools

- **System Status**: `./scripts/check_status.sh`
- **Log Files**: `tail -f logs/*.log`
- **Redis Monitoring**: `redis-cli monitor`
- **API Testing**: http://localhost:8000/docs

### Development Commands

```bash
# Reset Redis cache
redis-cli FLUSHALL

# Restart all services
./scripts/stop_local_dev.sh && ./scripts/start_local_dev.sh

# View active Celery tasks
celery -A worker inspect active

# Manual data refresh
curl -X POST http://localhost:8000/api/opportunities/refresh
```

## 🎯 Code Standards

### Python Code Style

- **Formatter**: Black
- **Linting**: Flake8
- **Type Hints**: Required for new functions
- **Docstrings**: Google style

```python
def calculate_ev(fair_probability: float, decimal_odds: float) -> float:
    """Calculate expected value percentage.
    
    Args:
        fair_probability: True win probability (0.0 to 1.0)
        decimal_odds: Market odds in decimal format
        
    Returns:
        EV as decimal (e.g., 0.045 = 4.5% EV)
    """
    return (fair_probability * decimal_odds) - 1
```

### TypeScript Code Style

- **Formatter**: Prettier
- **Linting**: ESLint
- **Type Safety**: Strict mode enabled

```typescript
interface BettingOpportunity {
  id: string;
  event: string;
  evPercentage: number;
  bestOdds: string;
  bookmaker: string;
}
```

### Git Workflow

1. Create feature branch: `git checkout -b feature/description`
2. Make changes with clear commits
3. Run tests: `./scripts/run_tests.sh smoke`
4. Push and create PR
5. Ensure CI passes before merging

## 📈 Performance Optimization

### Backend Performance

- **Cache Strategy**: Redis for all expensive calculations
- **Database**: Use indexes for frequent queries
- **API**: Implement pagination for large datasets
- **Background Tasks**: Celery for heavy processing

### Frontend Performance

- **Code Splitting**: Vite handles automatically
- **API Calls**: Debounced search, optimistic updates
- **Caching**: React Query for API state management
- **Bundle Size**: Regular analysis with `npm run build -- --analyze`

## 🤝 Contributing Guidelines

### Pull Request Process

1. **Branch Naming**: `feature/feature-name` or `fix/bug-description`
2. **Commit Messages**: Use conventional commits
3. **Testing**: All tests must pass
4. **Documentation**: Update relevant docs
5. **Code Review**: At least one approval required

### Code Quality Checklist

- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] No hardcoded secrets
- [ ] Error handling implemented
- [ ] Performance considerations addressed

---

**Need Help?**
- Check system status: `./scripts/check_status.sh`
- View logs: `ls logs/`
- Run diagnostics: `python scripts/test_setup.py`
- Ask in development channel 