# Sports Betting +EV Analyzer

A modern sports betting analysis tool that identifies positive expected value (EV) betting opportunities across multiple sportsbooks.

## 🚀 Quick Start

### Development Environment
```bash
# Start the full development environment (frontend + backend)
docker-compose up -d

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs

# Stop services
docker-compose down
```

### Production Environment
```bash
# Start production environment
docker-compose -f docker-compose.prod.yml up -d

# Frontend: http://localhost:80
# Backend API: http://localhost:8000
```

**Manual Setup:**
```bash
# Backend
pip install -r requirements.txt
cp .env.example .env  # Edit with your configuration
./scripts/start_local_dev.sh

# Frontend (separate terminal)
cd frontend && npm install && npm run dev
```

## 🏗 Architecture

- **Frontend**: React TypeScript with Vite
- **Backend**: FastAPI with JSON APIs
- **Cache**: Redis for data caching and Celery broker
- **Database**: PostgreSQL with Supabase authentication
- **Background Tasks**: Celery worker and beat scheduler

## 🎯 Key Features

- **Real-time EV Analysis**: Live calculation across multiple sportsbooks
- **Automated Updates**: 5-minute refresh intervals via background tasks
- **Role-based Access**: Free tier (main lines) vs Premium (all markets)
- **Market Coverage**: Moneyline, spreads, totals, and player props

## 🔧 Configuration

Key environment variables in `.env`:
```bash
# Database & Auth
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret

# APIs
ODDS_API_KEY=your-odds-api-key

# Redis
REDIS_URL=redis://localhost:6379/0
REFRESH_INTERVAL_MINUTES=5
```

## 🧪 Testing

```bash
# Quick health checks
./scripts/run_tests.sh smoke

# Performance testing
./scripts/run_tests.sh load

# Full test suite
./scripts/run_tests.sh integration
```

## 📚 Documentation

- **[Development Guide](docs/DEVELOPMENT.md)** - Complete setup and workflows
- **[Testing Guide](docs/TESTING.md)** - Testing infrastructure and CI/CD
- **[Database Guide](docs/DB_ENUM_UPGRADES.md)** - Schema management

## 🛠 Tech Stack

**Frontend**: React, TypeScript, Vite, TailwindCSS  
**Backend**: FastAPI, SQLAlchemy, Pydantic, Supabase  
**Cache**: Redis, Celery  
**Testing**: pytest, Locust, GitHub Actions  
**Deployment**: Docker, Docker Compose 