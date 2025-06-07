# 📚 Documentation Index

Welcome to the bet-intel documentation. This directory contains comprehensive guides for development, deployment, and system architecture.

## 📖 Documentation Overview

### 🚀 Getting Started
- **[Main README](../README.md)** - Project overview and quick start guide
- **[Development Guide](DEVELOPMENT.md)** - Comprehensive developer setup and workflows
- **[Scripts Reference](../scripts/README.md)** - Development and setup scripts

### 🛠 Technical Guides
- **[Database Setup](DB_ENUM_UPGRADES.md)** - Database schema, migrations, and enum management
- **[UI Layout System](LAYOUT_GUIDE.md)** - Frontend layout components and responsive design
- **[Testing Guide](TESTING.md)** - Comprehensive testing infrastructure and guidelines
- **[Horizontal Scaling](HORIZONTAL_SCALING.md)** - Production scaling strategies and architecture

## 🎯 Quick Reference

| Documentation | Purpose | Audience |
|---------------|---------|----------|
| [Main README](../README.md) | Project overview, quick start | All users |
| [Development Guide](DEVELOPMENT.md) | Developer setup, workflows | Developers |
| [Database Guide](DB_ENUM_UPGRADES.md) | Schema management, migrations | Backend developers |
| [Layout Guide](LAYOUT_GUIDE.md) | UI components, responsive design | Frontend developers |
| [Testing Guide](TESTING.md) | Test infrastructure, CI/CD | All developers |
| [Scaling Guide](HORIZONTAL_SCALING.md) | Production architecture | DevOps, architects |

## 🔍 Documentation by Role

### 👨‍💻 New Developers
1. Start with [Main README](../README.md)
2. Follow [Development Guide](DEVELOPMENT.md) setup
3. Run tests with [Testing Guide](TESTING.md)

### 🎨 Frontend Developers
1. [Development Guide](DEVELOPMENT.md) - Frontend workflow
2. [Layout Guide](LAYOUT_GUIDE.md) - UI components and patterns
3. [Testing Guide](TESTING.md) - Frontend testing

### ⚙️ Backend Developers
1. [Development Guide](DEVELOPMENT.md) - Backend workflow
2. [Database Guide](DB_ENUM_UPGRADES.md) - Schema management
3. [Testing Guide](TESTING.md) - API and integration testing

### 🚀 DevOps Engineers
1. [Scaling Guide](HORIZONTAL_SCALING.md) - Production architecture
2. [Testing Guide](TESTING.md) - CI/CD pipelines
3. [Development Guide](DEVELOPMENT.md) - Deployment strategies

## 📁 Additional Resources

### Configuration Examples
- [Environment Variables](DEVELOPMENT.md#configuration) - Complete .env setup
- [Docker Configuration](HORIZONTAL_SCALING.md#docker-compose) - Container orchestration
- [Testing Configuration](TESTING.md#configuration) - Test environment setup

### Architecture Diagrams
- [System Overview](DEVELOPMENT.md#architecture-overview) - High-level system design
- [Data Pipeline](../README.md#data-pipeline) - EV calculation flow
- [Scaling Architecture](HORIZONTAL_SCALING.md#target-architecture) - Production scaling

### API Documentation
- **Interactive Docs**: http://localhost:8000/docs (when running locally)
- **Health Checks**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics (if enabled)

## 🤝 Contributing to Documentation

### Adding New Documentation
1. Create new file in `/docs/` directory
2. Use clear markdown formatting with emojis for navigation
3. Add entry to this index
4. Include cross-references to related docs

### Documentation Standards
- **Clear headings** with emoji icons for visual navigation
- **Code examples** with proper syntax highlighting
- **Step-by-step instructions** for complex procedures
- **Cross-references** to related documentation
- **Regular updates** to keep information current

### Maintenance
- Review documentation quarterly
- Update examples when code changes
- Remove outdated information
- Add new features and workflows

---

## 🔗 External Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **React Documentation**: https://react.dev/
- **Supabase Documentation**: https://supabase.io/docs
- **The Odds API**: https://the-odds-api.com/liveapi/guides/

**Need help?** Check the [Development Guide](DEVELOPMENT.md) troubleshooting section or reach out to the development team. 