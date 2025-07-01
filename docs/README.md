# Fair-Edge Documentation

Welcome to the Fair-Edge developer documentation.

## 📚 Documentation Index

### Getting Started
- **[Quick Reference](QUICK_REFERENCE.md)** - Common commands and configurations
- **[Development Guide](DEVELOPMENT.md)** - Local development setup and workflow
- **[API Reference](API.md)** - REST API endpoints and examples

### Deployment & Operations
- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment procedures
- **[Operations Guide](OPERATIONS.md)** - Monitoring, maintenance, and troubleshooting

### Testing & Quality
- **[Testing Guide](TESTING.md)** - Test procedures and CI/CD pipeline

### AI Integration
- **[Claude Instructions](CLAUDE.md)** - Guide for AI assistant integration

## 🚀 Quick Start

```bash
# Development
./scripts/setup-dev.sh
docker compose up -d

# Production
./scripts/setup-prod.sh
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile production up -d
```

## 📋 Prerequisites

- Docker & Docker Compose
- Git
- API Keys: The Odds API, Supabase

## 🏗️ Architecture Overview

Fair-Edge is a modern sports betting analysis platform built with:

- **Frontend**: React 19 + TypeScript + Vite + TailwindCSS
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Cache**: Redis for high-performance caching
- **Background**: Celery for task processing
- **Deployment**: Docker Compose + Caddy

## 🔍 Finding Information

- **Commands?** → [Quick Reference](QUICK_REFERENCE.md)
- **Setup issues?** → [Development Guide](DEVELOPMENT.md#troubleshooting)
- **API endpoints?** → [API Reference](API.md)
- **Production deployment?** → [Deployment Guide](DEPLOYMENT.md)
- **Monitoring & logs?** → [Operations Guide](OPERATIONS.md)
- **Running tests?** → [Testing Guide](TESTING.md)

## 📝 Contributing

1. Read the [Development Guide](DEVELOPMENT.md)
2. Follow the code style guidelines
3. Write tests for new features
4. Submit pull requests with clear descriptions

---

For additional help, check the [Quick Reference](QUICK_REFERENCE.md) or search the codebase for specific implementations.