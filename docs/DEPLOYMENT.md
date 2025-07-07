# Deployment Guide

Complete guide for deploying Fair-Edge SaaS platform to production environments.

## 🚀 Quick Deploy

```bash
# 1. Setup environment
cp environments/production.env .env.production
nano .env.production          # Add your API keys

# 2. Deploy
docker compose -f docker-compose.production.yml up -d

# 3. Verify
curl http://your-domain/health
```

## 📋 Prerequisites

- Linux server (Ubuntu 20.04+ recommended)
- Docker & Docker Compose v2 installed
- Domain name with DNS configured
- SSL certificate (auto-configured with Caddy)
- Supabase project with configured schema
- Stripe account with webhook endpoints
- API keys for The Odds API

## 🔧 Environment Configuration

Create `.env.production` with:

```bash
# Supabase Configuration (Required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-key  
SUPABASE_JWT_SECRET=your-jwt-secret

# Stripe Configuration (Required)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_BASIC_PRICE=price_...
STRIPE_PREMIUM_PRICE=price_...

# External APIs
ODDS_API_KEY=your-odds-api-key

# Redis (Docker internal)
REDIS_URL=redis://redis:6379/0

# Frontend Build Variables (VITE_* prefix)
VITE_API_URL=https://your-domain.com
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key

# Domain Configuration
DOMAIN=your-domain.com
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
                    Supabase (Cloud)         Redis
                     (Auth + DB)               │
                          │                     │
                   Stripe Webhooks      Celery Workers
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
cp environments/production.env .env.production

# Configure environment variables
nano .env.production

# Deploy services
docker compose -f docker-compose.production.yml up -d
```

### 3. Configure Domain & Services

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

**Stripe Webhook Configuration:**
```bash
# Configure webhook endpoint in Stripe Dashboard:
# URL: https://your-domain.com/api/billing/stripe/webhook
# Events: checkout.session.completed, customer.subscription.*
```

**Supabase Configuration:**
- Set site URL to your domain
- Configure CORS origins
- Ensure RLS policies are in place

### 4. Verify Deployment

```bash
# Check services
docker compose -f docker-compose.production.yml ps

# Test endpoints
curl https://your-domain.com/health
curl https://your-domain.com/api/opportunities

# Test Stripe integration
curl -X POST https://your-domain.com/api/billing/stripe/webhook \
  -H "Content-Type: application/json" \
  -H "stripe-signature: test"

# View logs
docker compose -f docker-compose.production.yml logs -f api
```

## 🔄 Updates & Maintenance

### Deploy Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker compose -f docker-compose.production.yml up -d --build

# Zero-downtime update (if needed)
docker compose -f docker-compose.production.yml up -d --no-deps --build api
```

### Supabase Schema Changes

**Note:** Use Supabase Dashboard or CLI, not Alembic migrations.

```bash
# Option 1: Supabase Dashboard
# Go to https://supabase.com/dashboard > SQL Editor
# Run your schema changes

# Option 2: Supabase CLI (if installed)
supabase db push
```

### Backup Strategy

**Database:** Managed by Supabase with automatic backups

```bash
# Export data via Supabase Dashboard if needed
# Or use SQL dumps from Dashboard > SQL Editor

# Backup environment and config
cp .env.production backup/env_$(date +%Y%m%d).backup
tar -czf backup/config_$(date +%Y%m%d).tar.gz docker/ environments/
```

## 🚨 Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check logs
docker compose -f docker-compose.production.yml logs api
docker compose -f docker-compose.production.yml logs frontend

# Restart services
docker compose -f docker-compose.production.yml restart
```

**Supabase connection issues:**
```bash
# Test Supabase connection
docker compose -f docker-compose.production.yml exec api \
  python -c "from db import get_supabase; print(get_supabase().table('profiles').select('*').limit(1).execute())"

# Check environment variables
docker compose -f docker-compose.production.yml exec api env | grep SUPABASE
```

**Stripe webhook issues:**
```bash
# Check webhook logs
docker compose -f docker-compose.production.yml logs api | grep stripe

# Test webhook endpoint
curl -X POST https://your-domain.com/api/billing/stripe/webhook \
  -H "Content-Type: application/json" \
  -H "stripe-signature: test"
```

**Caddy/SSL issues:**
```bash
# Check Caddy logs
docker compose -f docker-compose.production.yml logs frontend

# Test SSL certificate
echo | openssl s_client -connect your-domain.com:443 2>/dev/null | openssl x509 -noout -dates
```

### Health Monitoring

```bash
# API health
curl https://your-domain.com/health

# Supabase health (check from API container)
docker compose -f docker-compose.production.yml exec api \
  python -c "from db import get_supabase; print('Supabase OK')"

# Redis health
docker compose -f docker-compose.production.yml exec redis redis-cli ping

# Celery worker health
docker compose -f docker-compose.production.yml exec celery_worker \
  python -c "import celery; print('Celery OK')"
```

## 🔐 Security Checklist

- [ ] Environment files have restricted permissions (600)
- [ ] Supabase RLS policies properly configured
- [ ] Stripe webhook secret properly set
- [ ] SSL/TLS properly configured (auto-managed by Caddy)
- [ ] Firewall rules configured (allow 80, 443, 22 only)
- [ ] Regular security updates applied
- [ ] Supabase backup strategy verified
- [ ] Monitoring and alerting configured
- [ ] JWT secrets are cryptographically secure
- [ ] Stripe API keys are in live mode (not test mode)

## 📊 Performance Optimization

### Redis Caching
- All opportunities cached for 5 minutes
- User sessions cached for 1 hour
- Static data cached for 24 hours
- Memory limit: 512MB with LRU eviction

### Supabase Optimization
- Connection pooling handled by Supabase
- Proper indexes on frequently queried columns
- RLS policies optimized for performance
- Query optimization via Supabase Dashboard

### Frontend Optimization
- Static assets served by Caddy
- Gzip compression enabled
- Browser caching headers set
- CDN via Cloudflare

### Stripe Integration
- Webhook processing optimized
- Subscription status cached
- Async payment processing

## 🆘 Support

For deployment issues:
1. Check logs: `docker compose -f docker-compose.production.yml logs -f`
2. Review this guide's troubleshooting section
3. Consult the [Operations Guide](OPERATIONS.md) for monitoring
4. Check [CLAUDE.md](CLAUDE.md) for architecture details
5. Contact the development team

## 📚 Related Documentation

- [Development Guide](DEVELOPMENT.md) - Local development setup
- [Operations Guide](OPERATIONS.md) - Monitoring and maintenance
- [API Reference](API.md) - Complete endpoint documentation
- [Claude Instructions](CLAUDE.md) - Architecture and troubleshooting

---

**Note:** This deployment uses Supabase for database and authentication, Stripe for payments. No local PostgreSQL required.