# Deployment Guide

Complete guide for deploying Fair-Edge to production environments.

## 🚀 Quick Deploy

```bash
# 1. Setup environment
./scripts/setup-prod.sh
nano .env.production.local          # Add your API keys

# 2. Deploy
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile production up -d

# 3. Verify
curl http://your-domain/health
```

## 📋 Prerequisites

- Linux server (Ubuntu 20.04+ recommended)
- Docker & Docker Compose installed
- Domain name with DNS configured
- SSL certificate (auto-configured with Caddy)
- API keys for The Odds API and Supabase

## 🔧 Environment Configuration

Create `.env.production.local` with:

```bash
# Core Services
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-key
SUPABASE_JWT_SECRET=your-jwt-secret

# External APIs
ODDS_API_KEY=your-odds-api-key

# Redis (Docker internal)
REDIS_URL=redis://redis:6379/0

# Domain Configuration
DOMAIN=your-domain.com
API_URL=https://your-domain.com
```

## 🏗️ Production Architecture

```
Internet → Cloudflare → Caddy (80/443) → Docker Services
                             ↓
                    ┌────────┴────────┐
                    │                 │
              Frontend (Static)   API (8000)
                                     │
                          ┌──────────┴──────────┐
                          │                     │
                     PostgreSQL              Redis
                          │                     │
                   Celery Workers ← ─ ─ ─ ─ ─ ─┘
```

## 📦 Deployment Steps

### 1. Initial Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin

# Create deployment directory
sudo mkdir -p /opt/fair-edge
sudo chown $USER:$USER /opt/fair-edge
cd /opt/fair-edge
```

### 2. Deploy Application

```bash
# Clone repository
git clone https://github.com/your-org/fair-edge.git .

# Setup production environment
./scripts/setup-prod.sh

# Configure environment
nano .env.production.local
nano frontend/.env.production.local

# Deploy services
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile production up -d
```

### 3. Configure Domain

**Cloudflare Settings:**
- SSL/TLS: Full (strict)
- Always Use HTTPS: On
- Auto Minify: JavaScript, CSS, HTML
- Caching Level: Standard

**DNS Records:**
```
Type  Name    Content           Proxy
A     @       your-server-ip    ✓
A     www     your-server-ip    ✓
```

### 4. Verify Deployment

```bash
# Check services
docker compose ps

# Test endpoints
curl https://your-domain.com/health
curl https://your-domain.com/api/opportunities

# View logs
docker compose logs -f api
```

## 🔄 Updates & Maintenance

### Deploy Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile production up -d --build
```

### Database Migrations

```bash
# Run migrations
docker compose exec api alembic upgrade head

# Create new migration
docker compose exec api alembic revision --autogenerate -m "description"
```

### Backup Database

```bash
# Create backup
docker compose exec -T db pg_dump -U postgres fairedge > backup_$(date +%Y%m%d).sql

# Restore backup
docker compose exec -T db psql -U postgres fairedge < backup_20240101.sql
```

## 🚨 Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check logs
docker compose logs api
docker compose logs frontend

# Restart services
docker compose restart
```

**Database connection issues:**
```bash
# Test connection
docker compose exec api python -c "from core.db import engine; print('Connected')"

# Check migrations
docker compose exec api alembic current
```

**Caddy/SSL issues:**
```bash
# Check Caddy logs
docker compose logs caddy

# Validate Caddyfile
docker compose exec caddy caddy validate --config /etc/caddy/Caddyfile
```

### Health Monitoring

```bash
# API health
curl https://your-domain.com/health

# Database health
docker compose exec db pg_isready

# Redis health
docker compose exec redis redis-cli ping
```

## 🔐 Security Checklist

- [ ] Environment files have restricted permissions (600)
- [ ] Database uses strong passwords
- [ ] SSL/TLS properly configured
- [ ] Firewall rules configured (allow 80, 443, 22 only)
- [ ] Regular security updates applied
- [ ] Backup strategy implemented
- [ ] Monitoring and alerting configured

## 📊 Performance Optimization

### Redis Caching
- All opportunities cached for 5 minutes
- User sessions cached for 1 hour
- Static data cached for 24 hours

### Database Optimization
- Proper indexes on frequently queried columns
- Connection pooling configured
- Regular VACUUM and ANALYZE

### Frontend Optimization
- Static assets served by Nginx
- Gzip compression enabled
- Browser caching headers set

## 🆘 Support

For deployment issues:
1. Check logs: `docker compose logs -f`
2. Review this guide's troubleshooting section
3. Consult the [Operations Guide](OPERATIONS.md) for monitoring
4. Contact the development team

---

**Note:** This guide covers standard VPS deployment. For specific cloud providers (AWS, GCP, Azure), refer to their documentation for additional considerations.