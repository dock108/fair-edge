# Sports Betting +EV Analyzer

A modern sports betting analysis tool that identifies positive expected value (EV) betting opportunities across multiple sportsbooks.

## 🚀 Quick Start

### Development Environment
```bash
# Start the full development environment (recommended)
./scripts/deploy.sh development

# Or using Docker Compose directly
docker-compose up -d

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs

# View logs
./scripts/deploy.sh logs development

# Stop services
./scripts/deploy.sh stop
```

### Production Environment
```bash
# Start production environment (recommended)
./scripts/deploy.sh production

# With monitoring stack
./scripts/deploy.sh production --monitoring

# Or using Docker Compose directly
docker-compose -f docker-compose.prod.yml up -d

# Access the application
# Frontend: http://localhost:80
# Backend API: http://localhost:8000
# Monitoring: http://localhost:3000 (Grafana)
```

**Manual Setup (Development Only):**
```bash
# Backend
pip install -r requirements.txt
cp .env.example .env  # Edit with your configuration
uvicorn app:app --reload

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

**Simplified Environment Management**: All configuration is managed from root-level environment files:

- **`.env.development`** - Development settings (backend + frontend)
- **`.env.production`** - Production settings (backend + frontend) 
- **`.env.example`** - Template for setup

Key environment variables:
```bash
# Backend Configuration
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret
ODDS_API_KEY=your-odds-api-key
REDIS_URL=redis://localhost:6379/0

# Frontend Configuration (VITE_* prefix)
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=your-supabase-url
VITE_SUPABASE_ANON_KEY=your-anon-key
```

**Setup**: `cp .env.example .env.development` and configure your values.

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

- **[Development & Deployment Guide](docs/DEVELOPMENT.md)** - Complete setup, workflows & production deployment
- **[Testing Guide](docs/TESTING.md)** - Testing infrastructure and CI/CD
- **[Database Guide](docs/DB_ENUM_UPGRADES.md)** - Schema management

## 🛠 Tech Stack

**Frontend**: React, TypeScript, Vite, TailwindCSS  
**Backend**: FastAPI, SQLAlchemy, Pydantic, Supabase  
**Cache**: Redis, Celery  
**Testing**: pytest, Locust, GitHub Actions  
**Deployment**: Docker, Docker Compose 