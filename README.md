# Fair-Edge - Sports Betting EV Analyzer

A professional sports betting analysis platform that identifies positive expected value (+EV) opportunities across multiple sportsbooks using advanced statistical analysis.

## ⚡ Quick Start

### Development (Recommended)
```bash
./scripts/deploy.sh development
```
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Manual Development Setup
```bash
# Backend
pip install -r requirements.txt
cp .env.example .env  # Edit with your API keys
uvicorn app:app --reload --port 8000

# Frontend (separate terminal)
cd frontend && npm install && npm run dev
```

### Production Deployment
```bash
./scripts/deploy.sh production
```

## 🏗️ Architecture

**Modern Stack:**
- **Frontend**: React 19 + TypeScript + Vite + TailwindCSS
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL (Supabase)
- **Cache**: Redis for high-performance data caching
- **Background**: Celery for heavy computations
- **Real-time**: Server-Sent Events + WebSocket support

**Core Features:**
- Real-time +EV opportunity detection
- Multi-sportsbook comparison engine
- Role-based access (Free/Basic/Premium/Admin)
- Advanced analytics and trend analysis
- API-first architecture with comprehensive documentation

## 🔧 Development Commands

```bash
# Testing
./scripts/run_tests.sh smoke        # Quick health checks
./scripts/run_tests.sh load         # Performance testing  
./scripts/run_tests.sh integration  # Full test suite

# Database
alembic upgrade head                # Apply migrations
python utils/migrations.py migrate # Manual migration

# Frontend
cd frontend && npm run build       # Production build
cd frontend && npm run lint        # Linting
```

## 📊 Features

### Core Analysis Engine
- **Expected Value Calculation**: No-vig fair odds methodology
- **Multi-Market Support**: Moneylines, spreads, totals, player props
- **Real-time Data**: Live odds from 10+ major sportsbooks
- **Smart Filtering**: Role-based opportunity filtering

### User Tiers
- **Free**: Limited opportunities (worst 10, -2% EV threshold)
- **Basic**: All main lines, unlimited EV access
- **Premium**: Full market access + advanced analytics + data export
- **Admin**: Complete system access + management tools

### Technical Features
- Sub-100ms response times with Redis caching
- Automatic failover and graceful degradation
- Comprehensive rate limiting and security
- Production-ready monitoring and observability

## 🚀 API Integration

```bash
# Get opportunities (authenticated)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/opportunities

# Health check (public)
curl http://localhost:8000/health

# Premium analytics (subscribers only)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/analytics/advanced
```

## 📚 Documentation

- **[Development Guide](docs/DEVELOPMENT.md)** - Complete setup, deployment, and troubleshooting
- **[API Reference](docs/API.md)** - Endpoint documentation with examples
- **[Testing Guide](docs/TESTING.md)** - Test procedures and CI/CD
- **[Operations Guide](docs/OPERATIONS.md)** - Production monitoring and maintenance
- **[User Guide](docs/USER_GUIDE.md)** - End-user feature documentation

## 🛠️ Environment Setup

Required environment variables:
```bash
# Core Services
DATABASE_URL=postgresql://...
REDIS_URL=redis://localhost:6379/0
SUPABASE_URL=https://...
SUPABASE_SERVICE_ROLE_KEY=...

# External APIs
THE_ODDS_API_KEY=your_odds_api_key
```

See `.env.example` for complete configuration options.

## 🧪 Testing

```bash
# Run specific test types
./scripts/run_tests.sh smoke        # 2 minutes - basic functionality
./scripts/run_tests.sh load         # 5 minutes - performance testing
./scripts/run_tests.sh integration  # 10 minutes - full system tests

# Manual testing
pytest tests/test_smoke_ci.py -v
```

## 📦 Deployment

**Development:**
```bash
./scripts/deploy.sh development
```

**Production:**
```bash
./scripts/deploy.sh production
```

**Monitoring:**
```bash
./scripts/deploy.sh logs development  # View logs
./scripts/deploy.sh stop              # Stop services
```

## 🤝 Contributing

1. Review the [Development Guide](docs/DEVELOPMENT.md)
2. Run tests: `./scripts/run_tests.sh smoke`
3. Check code quality: `cd frontend && npm run lint`
4. Submit pull request with test coverage

## 📄 License

All rights reserved. This is proprietary software for Fair-Edge sports betting analysis platform.

---

**Production Status**: ✅ Ready for deployment  
**Test Coverage**: 90%+ with comprehensive CI/CD  
**Performance**: Sub-100ms response times  
**Security**: Multi-layer authentication with rate limiting