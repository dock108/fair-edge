# Operations Guide

Production monitoring, maintenance, and troubleshooting guide for Fair-Edge SaaS platform.

## 🔍 Monitoring

### Health Checks

```bash
# API health
curl https://your-domain.com/health

# Service status
docker compose -f docker-compose.production.yml ps

# Container health
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Supabase connection test
curl -H "Authorization: Bearer SERVICE_ROLE_KEY" \
  "https://your-project.supabase.co/rest/v1/profiles?select=id&limit=1"

# Stripe webhook test
curl -X POST https://your-domain.com/api/billing/stripe/webhook \
  -H "Content-Type: application/json" \
  -H "stripe-signature: test"
```

### Key Metrics

**API Performance:**
- Response time: < 100ms (p95)
- Error rate: < 0.1%
- Cache hit rate: > 80%

**Background Jobs:**
- Celery queue length: < 100
- Task failure rate: < 1%
- Scheduled task execution: 100%

**Billing & Subscriptions:**
- Stripe webhook success rate: > 99%
- Subscription upgrade success rate: > 95%
- Payment failure rate: < 5%

**Supabase Integration:**
- Auth success rate: > 99%
- Database query response time: < 50ms
- Connection pool utilization: < 80%

### Logs

```bash
# View all logs
docker compose -f docker-compose.production.yml logs -f

# Specific service logs
docker compose -f docker-compose.production.yml logs -f api
docker compose -f docker-compose.production.yml logs -f celery_worker
docker compose -f docker-compose.production.yml logs -f celery_beat
docker compose -f docker-compose.production.yml logs -f frontend

# Filter by time
docker compose -f docker-compose.production.yml logs --since 1h api

# Search logs
docker compose -f docker-compose.production.yml logs api | grep ERROR
docker compose -f docker-compose.production.yml logs api | grep stripe
docker compose -f docker-compose.production.yml logs api | grep supabase
```

## 🔧 Maintenance

### Regular Tasks

**Daily:**
- Check health endpoints
- Review error logs
- Monitor API quota usage

**Weekly:**
- Database backup
- Review performance metrics
- Check disk usage

**Monthly:**
- Security updates
- Dependency updates
- Performance optimization review

### Supabase Monitoring

**Database managed by Supabase - no direct maintenance required**

```bash
# Check Supabase connection from API container
docker compose -f docker-compose.production.yml exec api \
  python -c "from db import get_supabase; print(get_supabase().table('profiles').select('*').limit(1).execute())"

# Monitor API usage in Supabase Dashboard:
# https://supabase.com/dashboard > Settings > API > API Usage

# Check auth metrics in Supabase Dashboard:
# https://supabase.com/dashboard > Authentication > Users

# Review database metrics:
# https://supabase.com/dashboard > Settings > Database > Database Health
```

### Stripe Monitoring

```bash
# Check Stripe webhook logs
docker compose -f docker-compose.production.yml logs api | grep "Received Stripe webhook"

# Monitor failed payments
docker compose -f docker-compose.production.yml logs api | grep "payment_failed"

# Check subscription events
docker compose -f docker-compose.production.yml logs api | grep "subscription"

# Stripe Dashboard monitoring:
# https://dashboard.stripe.com/webhooks (webhook health)
# https://dashboard.stripe.com/customers (subscription status)
# https://dashboard.stripe.com/payments (payment success/failure rates)
```

### Cache Management

```bash
# Monitor Redis memory
docker compose -f docker-compose.production.yml exec redis redis-cli INFO memory

# Check Redis configuration
docker compose -f docker-compose.production.yml exec redis redis-cli CONFIG GET maxmemory
docker compose -f docker-compose.production.yml exec redis redis-cli CONFIG GET maxmemory-policy

# Clear cache (caution in production)
docker compose -f docker-compose.production.yml exec redis redis-cli FLUSHALL

# View cache keys
docker compose -f docker-compose.production.yml exec redis redis-cli --scan --pattern "fair-edge:*"

# Monitor cache hit rate
docker compose -f docker-compose.production.yml exec redis redis-cli INFO stats | grep keyspace
```

## 🚨 Incident Response

### Common Issues

**High Memory Usage:**
```bash
# Check memory by container
docker stats --no-stream

# Restart memory-heavy service
docker compose -f docker-compose.production.yml restart celery_worker
```

**API Errors Spike:**
```bash
# Check recent errors
docker compose -f docker-compose.production.yml logs --since 10m api | grep ERROR

# Check for Supabase connection issues
docker compose -f docker-compose.production.yml logs api | grep "supabase\|Supabase"

# Check for Stripe webhook failures
docker compose -f docker-compose.production.yml logs api | grep "stripe\|webhook"
```

**Supabase Connection Issues:**
```bash
# Test Supabase connection
docker compose -f docker-compose.production.yml exec api \
  python -c "from db import get_supabase; client = get_supabase(); print('Connection OK')"

# Check environment variables
docker compose -f docker-compose.production.yml exec api env | grep SUPABASE

# Check Supabase Dashboard for service status:
# https://status.supabase.com/
```

**Stripe Integration Issues:**
```bash
# Test Stripe API connection
docker compose -f docker-compose.production.yml exec api \
  python -c "import stripe; from core.settings import settings; stripe.api_key = settings.stripe_secret_key; print(stripe.Account.retrieve())"

# Check webhook endpoint health
curl -X POST https://your-domain.com/api/billing/stripe/webhook \
  -H "Content-Type: application/json" \
  -H "stripe-signature: test" \
  -d '{"type": "test"}'

# Check Stripe Dashboard webhook logs:
# https://dashboard.stripe.com/webhooks
```

### Recovery Procedures

**Service Recovery:**
```bash
# Restart all services
docker compose -f docker-compose.production.yml restart

# Hard restart with cleanup
docker compose -f docker-compose.production.yml down
docker compose -f docker-compose.production.yml up -d

# Individual service restart
docker compose -f docker-compose.production.yml restart api
docker compose -f docker-compose.production.yml restart celery_worker
```

**Supabase Recovery:**
```bash
# Supabase database is managed - check status at:
# https://status.supabase.com/
# https://supabase.com/dashboard > Settings > Database

# If connection issues persist, check environment variables:
docker compose -f docker-compose.production.yml exec api env | grep SUPABASE

# Restart API to refresh connections:
docker compose -f docker-compose.production.yml restart api
```

**Stripe Recovery:**
```bash
# Check Stripe API status: https://status.stripe.com/

# Verify webhook configuration in Stripe Dashboard:
# URL: https://your-domain.com/api/billing/stripe/webhook
# Events: checkout.session.completed, customer.subscription.*

# Test webhook endpoint:
curl -X POST https://your-domain.com/api/billing/stripe/webhook \
  -H "Content-Type: application/json" \
  -H "stripe-signature: test"
```

## 📊 Performance Tuning

### API Optimization

```bash
# Check slow endpoints
docker compose -f docker-compose.production.yml logs api | grep "duration" | sort -k5 -nr | head -20

# Monitor API response times
docker compose -f docker-compose.production.yml logs api | grep "GET\|POST" | grep -o "[0-9]*ms"
```

### Supabase Optimization

**Query Performance:**
- Monitor slow queries in Supabase Dashboard > Settings > Database > Query Performance
- Check API usage patterns in Supabase Dashboard > Settings > API
- Review connection pooling in Supabase Dashboard > Settings > Database

```bash
# Monitor Supabase API usage
# Check in Dashboard: https://supabase.com/dashboard > Settings > API > API Usage

# Check for connection pool exhaustion
docker compose -f docker-compose.production.yml logs api | grep "connection"
```

### Stripe Performance

```bash
# Monitor webhook processing time
docker compose -f docker-compose.production.yml logs api | grep "webhook" | grep "duration"

# Check payment processing latency
docker compose -f docker-compose.production.yml logs api | grep "checkout" | grep "ms"

# Monitor in Stripe Dashboard:
# https://dashboard.stripe.com/webhooks (response times)
# https://dashboard.stripe.com/payments (processing times)
```

### Redis Optimization

```bash
# Check current configuration (already optimized in production)
docker compose -f docker-compose.production.yml exec redis redis-cli CONFIG GET maxmemory
docker compose -f docker-compose.production.yml exec redis redis-cli CONFIG GET maxmemory-policy

# Check eviction stats
docker compose -f docker-compose.production.yml exec redis redis-cli INFO stats | grep evict

# Monitor memory usage
docker compose -f docker-compose.production.yml exec redis redis-cli INFO memory | grep used_memory_human

# Check cache efficiency
docker compose -f docker-compose.production.yml exec redis redis-cli INFO stats | grep keyspace_hits
```

## 🔐 Security

### Regular Audits

```bash
# Check for exposed ports
netstat -tlnp | grep LISTEN

# Verify only required ports are exposed (80, 443, 22)
sudo ufw status

# Check SSL certificates (auto-managed by Caddy)
echo | openssl s_client -connect your-domain.com:443 2>/dev/null | openssl x509 -noout -dates

# Verify Supabase RLS policies:
# https://supabase.com/dashboard > Authentication > Policies

# Check Stripe webhook security:
# https://dashboard.stripe.com/webhooks (verify signing secret is set)
```

### Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Update Docker images
docker compose -f docker-compose.production.yml pull
docker compose -f docker-compose.production.yml up -d

# Update dependencies (in development)
cd frontend && npm audit fix
pip list --outdated

# Monitor for security updates:
# - Supabase: Automatic updates
# - Stripe: Monitor API version changes
# - Docker images: Use dependabot or renovation
```

## 📈 Scaling

### Horizontal Scaling

```bash
# Scale Celery workers
docker compose -f docker-compose.production.yml up -d --scale celery_worker=5

# Scale API instances (requires load balancer)
docker compose -f docker-compose.production.yml up -d --scale api=3

# Supabase scaling is automatic
# For high-traffic scenarios, consider:
# - Supabase Pro plan for better performance
# - CDN for static assets (already using Cloudflare)
# - Redis clustering for cache scaling
```

### Resource Limits

**Current Production Limits (in docker-compose.production.yml):**

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
  
  celery_worker:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.25'
          memory: 256M

  redis:
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

## 🆘 Emergency Contacts

- **On-call**: Check rotation schedule
- **Escalation**: Development team lead
- **Infrastructure**: DevOps team
- **Supabase Issues**: https://status.supabase.com/ + support portal
- **Stripe Issues**: https://status.stripe.com/ + Stripe support
- **Domain/DNS**: Cloudflare support

## 📋 Runbooks

### Deployment Rollback
1. Identify the last working commit
2. `git checkout <commit-hash>`
3. `docker compose -f docker-compose.production.yml build --no-cache`
4. `docker compose -f docker-compose.production.yml up -d`

### Emergency Maintenance Mode
1. Update Caddy configuration to serve maintenance page
2. Stop API services: `docker compose -f docker-compose.production.yml stop api`
3. Perform maintenance
4. Restore services: `docker compose -f docker-compose.production.yml start api`

### Data Recovery (Supabase)
1. **Database**: Use Supabase Dashboard > Settings > Database > Backups
2. **Point-in-time recovery**: Available on Supabase Pro plans
3. **Manual export**: Use Dashboard > SQL Editor for data export
4. **Contact Supabase support** for critical data recovery scenarios