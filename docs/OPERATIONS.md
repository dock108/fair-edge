# FairEdge Operations Guide

Production operations, monitoring, and maintenance guide for the FairEdge sports betting analysis platform.

## Production Environment Overview

### Infrastructure Stack
- **Application**: FastAPI (Uvicorn/Gunicorn) + React (Nginx)
- **Database**: PostgreSQL (Supabase) with connection pooling
- **Cache**: Redis for data caching and Celery message broker
- **Background Processing**: Celery workers with beat scheduler
- **Monitoring**: Prometheus + Grafana + structured logging
- **Deployment**: Docker Compose with health checks

### Service Architecture
```
[Load Balancer] → [Nginx] → [FastAPI] → [PostgreSQL]
                    ↓         ↓           ↑
                [React]   [Celery] → [Redis]
                            ↓
                      [External APIs]
```

## Monitoring & Alerting

### Health Check Endpoints

#### Application Health
```bash
# Primary health check
curl https://api.yourdomain.com/health

# Response format
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy", 
    "celery": "healthy"
  },
  "version": "1.0.0"
}
```

#### Service-Specific Checks
```bash
# Database connectivity
curl https://api.yourdomain.com/health/database

# Redis connectivity  
curl https://api.yourdomain.com/health/redis

# Background worker status
curl https://api.yourdomain.com/health/celery
```

### Key Metrics to Monitor

#### Application Metrics
- **Response Time**: 95th percentile < 2 seconds
- **Error Rate**: < 0.1% for 5xx errors
- **Request Volume**: Baseline throughput tracking
- **Active Users**: Concurrent authenticated sessions

#### Infrastructure Metrics
- **CPU Usage**: < 80% sustained
- **Memory Usage**: < 85% with swap monitoring
- **Disk Usage**: < 90% on all partitions
- **Network I/O**: Bandwidth utilization tracking

#### Business Metrics
- **Opportunity Count**: Minimum 10 opportunities available
- **Data Freshness**: Last API refresh < 10 minutes ago
- **Subscription Health**: Active vs churned subscribers
- **API Rate Limits**: Usage vs limits by tier

### Alerting Rules

#### Critical Alerts (Immediate Response)
```yaml
# Service Down
- alert: ServiceDown
  expr: up{job="fairedge-api"} == 0
  for: 1m
  severity: critical
  
# High Error Rate  
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
  for: 2m
  severity: critical

# Database Connection Failure
- alert: DatabaseDown
  expr: fairedge_database_health == 0
  for: 30s
  severity: critical
```

#### Warning Alerts (Monitor Closely) 
```yaml
# High Response Time
- alert: HighResponseTime
  expr: histogram_quantile(0.95, http_request_duration_seconds) > 2
  for: 5m
  severity: warning

# Low Opportunity Count
- alert: LowOpportunityCount  
  expr: fairedge_opportunities_count < 10
  for: 10m
  severity: warning

# High Memory Usage
- alert: HighMemoryUsage
  expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) > 0.85
  for: 5m
  severity: warning
```

## Log Management

### Log Locations and Formats

#### Application Logs
```bash
# Production logs (JSON format)
tail -f /var/log/fairedge/api.log
tail -f /var/log/fairedge/celery.log

# Docker container logs
docker logs fairedge-api -f
docker logs fairedge-celery-worker -f
```

#### Log Format Structure
```json
{
  "timestamp": "2024-01-01T12:00:00.000Z",
  "level": "INFO",
  "service": "api",
  "message": "Request processed successfully",
  "request_id": "req_123456789",
  "user_id": "user_123",
  "endpoint": "/api/opportunities",
  "duration_ms": 150,
  "status_code": 200
}
```

### Important Log Patterns

#### Error Patterns to Monitor
```bash
# Database connection issues
grep "database connection" /var/log/fairedge/api.log

# External API failures  
grep "odds_api_error" /var/log/fairedge/celery.log

# Authentication failures
grep "auth_failed" /var/log/fairedge/api.log

# Rate limit violations
grep "rate_limit_exceeded" /var/log/fairedge/api.log
```

#### Performance Patterns
```bash
# Slow queries (>1s)
grep "slow_query" /var/log/fairedge/api.log | grep "duration.*[0-9][0-9][0-9][0-9]"

# High memory usage warnings
grep "memory_warning" /var/log/fairedge/*.log

# Cache miss patterns
grep "cache_miss" /var/log/fairedge/api.log
```

## Database Operations

### Connection Management

#### PostgreSQL Health Checks
```sql
-- Active connections
SELECT count(*) as active_connections 
FROM pg_stat_activity 
WHERE state = 'active';

-- Long-running queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';

-- Database size monitoring
SELECT pg_size_pretty(pg_database_size('fairedge_prod'));
```

#### Connection Pool Monitoring
```bash
# Check Supabase dashboard for:
# - Active connections vs limits
# - Connection pool health
# - Query performance metrics
# - Storage usage trends
```

### Migration Management

#### Production Migration Process
```bash
# 1. Backup current state
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Test migration on staging
alembic upgrade head --sql > migration_preview.sql

# 3. Apply migration with monitoring
alembic upgrade head

# 4. Verify migration success
alembic current
```

#### Migration Rollback Procedure
```bash
# Immediate rollback to previous version
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# Restore from backup if needed
psql $DATABASE_URL < backup_20240101_120000.sql
```

## Cache Management (Redis)

### Redis Health Monitoring

#### Connection and Performance
```bash
# Basic connectivity test
redis-cli -u $REDIS_URL ping

# Memory usage monitoring
redis-cli -u $REDIS_URL info memory

# Key space information
redis-cli -u $REDIS_URL info keyspace

# Connection stats
redis-cli -u $REDIS_URL info clients
```

#### Cache Performance Metrics
```bash
# Hit ratio (should be >90%)
redis-cli -u $REDIS_URL info stats | grep keyspace

# Slow operations (should be minimal)
redis-cli -u $REDIS_URL slowlog get 10

# Memory usage (monitor for growth)
redis-cli -u $REDIS_URL info memory | grep used_memory_human
```

### Cache Maintenance

#### Cache Clearing Procedures
```bash
# Clear all cache (emergency only)
redis-cli -u $REDIS_URL FLUSHALL

# Clear specific patterns
redis-cli -u $REDIS_URL --scan --pattern "opportunities:*" | xargs redis-cli -u $REDIS_URL DEL

# Clear expired keys
redis-cli -u $REDIS_URL --scan --pattern "*" | while read key; do
  ttl=$(redis-cli -u $REDIS_URL TTL "$key")
  if [ "$ttl" -eq "-1" ]; then
    echo "Key without TTL: $key"
  fi
done
```

#### Cache Warming Scripts
```bash
# Warm critical cache keys after restart
python scripts/warm_cache.py --priority=high

# Scheduled cache warming (cron job)
0 */6 * * * /app/scripts/warm_cache.py --all
```

## Background Task Management (Celery)

### Worker Health Monitoring

#### Celery Status Commands
```bash
# Worker status
docker exec fairedge-celery-worker celery -A services.celery_app.celery_app inspect active

# Scheduled tasks
docker exec fairedge-celery-beat celery -A services.celery_app.celery_app inspect scheduled

# Worker statistics
docker exec fairedge-celery-worker celery -A services.celery_app.celery_app inspect stats
```

#### Queue Management
```bash
# View queue lengths
redis-cli -u $REDIS_URL LLEN celery

# Purge tasks (emergency)
docker exec fairedge-celery-worker celery -A services.celery_app.celery_app purge

# Monitor task results
redis-cli -u $REDIS_URL KEYS "celery-task-meta-*" | wc -l
```

### Task Performance Monitoring

#### Key Tasks to Monitor
- **odds_refresh**: Should complete in <5 minutes
- **ev_calculation**: Should process all opportunities in <2 minutes  
- **cache_warming**: Should complete in <1 minute
- **user_cleanup**: Daily cleanup should complete in <30 seconds

#### Task Failure Handling
```bash
# Check failed tasks
redis-cli -u $REDIS_URL LRANGE celery_failed 0 -1

# Retry failed tasks
docker exec fairedge-celery-worker celery -A services.celery_app.celery_app call tasks.retry_failed

# Monitor task retry attempts
grep "retry" /var/log/fairedge/celery.log | tail -20
```

## Deployment Operations

### Production Deployment Process

#### Pre-Deployment Checklist
- [ ] **Code Review**: All changes peer reviewed
- [ ] **Testing**: Smoke tests pass on staging
- [ ] **Database**: Migrations tested and ready
- [ ] **Configuration**: Environment variables updated
- [ ] **Dependencies**: Requirements.txt updated
- [ ] **Monitoring**: Alerts temporarily adjusted for deployment

#### Deployment Steps
```bash
# 1. Enable maintenance mode (optional)
echo "Maintenance in progress" > /var/www/maintenance.html

# 2. Pull latest code
git pull origin main

# 3. Update environment if needed
cp .env.production.new .env.production

# 4. Deploy with zero-downtime
./scripts/deploy.sh production --zero-downtime

# 5. Run database migrations
docker exec fairedge-api alembic upgrade head

# 6. Warm caches
python scripts/warm_cache.py --all

# 7. Health check verification
./scripts/run_tests.sh smoke --production

# 8. Disable maintenance mode
rm /var/www/maintenance.html
```

#### Rollback Procedure
```bash
# 1. Immediate service rollback
./scripts/rollback.sh

# 2. Database rollback if needed
alembic downgrade -1

# 3. Clear problem caches
redis-cli -u $REDIS_URL FLUSHALL

# 4. Restart all services
./scripts/deploy.sh production --restart

# 5. Verify rollback success
./scripts/run_tests.sh smoke --production
```

### Blue-Green Deployment (Advanced)

#### Setup Blue-Green Environment
```bash
# Deploy to green environment
./scripts/deploy.sh production --environment=green

# Run health checks on green
./scripts/health_check.sh --environment=green

# Switch traffic to green
./scripts/switch_traffic.sh green

# Keep blue as rollback option
./scripts/deploy.sh production --environment=blue --maintain
```

## Security Operations

### Access Control Management

#### User Role Monitoring
```sql
-- Monitor user role distribution
SELECT role, COUNT(*) as user_count 
FROM auth.users 
GROUP BY role;

-- Recent role changes
SELECT * FROM audit.user_role_changes 
WHERE created_at > NOW() - INTERVAL '24 hours';
```

#### API Key Management
```bash
# Rotate external API keys monthly
python scripts/rotate_api_keys.py --service=odds_api

# Update Stripe webhook secrets
python scripts/update_stripe_secrets.py

# Rotate JWT secrets (requires careful coordination)
python scripts/rotate_jwt_secrets.py --environment=production
```

### Security Monitoring

#### Authentication Monitoring
```bash
# Failed login attempts
grep "auth_failed" /var/log/fairedge/api.log | grep "$(date +%Y-%m-%d)" | wc -l

# Suspicious IP patterns
grep "auth_failed" /var/log/fairedge/api.log | awk '{print $NF}' | sort | uniq -c | sort -nr

# Rate limit violations
grep "rate_limit_exceeded" /var/log/fairedge/api.log | grep "$(date +%Y-%m-%d)"
```

#### Data Protection Monitoring
```bash
# Monitor for potential data leaks
grep -i "password\|secret\|key\|token" /var/log/fairedge/*.log | grep -v "masked"

# Check SSL certificate expiration
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com | openssl x509 -noout -dates

# Verify security headers
curl -I https://yourdomain.com | grep -E "(Strict-Transport|Content-Security|X-Frame)"
```

## Backup and Disaster Recovery

### Backup Procedures

#### Database Backups
```bash
# Daily automated backup
pg_dump $DATABASE_URL | gzip > /backups/daily/fairedge_$(date +%Y%m%d).sql.gz

# Point-in-time recovery preparation (Supabase handles this)
# Verify backup integrity monthly
gunzip -c /backups/daily/fairedge_20240101.sql.gz | head -20
```

#### Redis Backup
```bash
# Snapshot Redis data
redis-cli -u $REDIS_URL BGSAVE

# Copy snapshot to backup location
docker cp fairedge-redis:/data/dump.rdb /backups/redis/dump_$(date +%Y%m%d).rdb
```

#### Application State Backup
```bash
# Backup configuration files
tar -czf /backups/config/config_$(date +%Y%m%d).tar.gz .env.production docker-compose.prod.yml

# Backup logs before rotation
tar -czf /backups/logs/logs_$(date +%Y%m%d).tar.gz /var/log/fairedge/
```

### Disaster Recovery

#### Service Recovery Priorities
1. **Database**: Restore from Supabase backup
2. **Cache**: Redis can be rebuilt from database
3. **Application**: Deploy from git with last known good configuration
4. **Background Tasks**: Will resume automatically after service restoration

#### Recovery Time Objectives (RTO)
- **Database**: < 15 minutes (Supabase restore)
- **Application Services**: < 5 minutes (container restart)
- **Full System**: < 30 minutes (complete recovery)

#### Recovery Testing
```bash
# Monthly disaster recovery test
./scripts/dr_test.sh --simulate --environment=staging

# Backup restoration test
./scripts/test_backup_restore.sh --backup=latest
```

## Performance Optimization

### Database Performance

#### Query Optimization
```sql
-- Monitor slow queries
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Index usage analysis
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE tablename = 'opportunities';
```

#### Connection Pool Tuning
```bash
# Monitor connection pool health
curl -s http://localhost:8000/health/database | jq '.pool_stats'

# Adjust pool size based on load
export DB_POOL_SIZE=20
export DB_MAX_OVERFLOW=10
```

### Application Performance

#### Response Time Optimization
```bash
# Profile API endpoints
curl -w "@curl-format.txt" -s -o /dev/null https://api.yourdomain.com/api/opportunities

# Monitor memory usage
docker stats fairedge-api --no-stream
```

#### Cache Hit Rate Optimization
```bash
# Monitor cache effectiveness
redis-cli -u $REDIS_URL info stats | grep keyspace_hits

# Adjust cache TTL based on usage patterns
python scripts/optimize_cache_ttl.py --analyze
```

## Capacity Planning

### Growth Monitoring

#### User Growth Metrics
- **Daily Active Users**: Track growth trends
- **API Request Volume**: Plan for traffic increases  
- **Database Size**: Monitor storage requirements
- **Concurrent Sessions**: Plan for peak usage

#### Infrastructure Scaling

#### Horizontal Scaling Triggers
- **CPU**: > 70% sustained for 10+ minutes
- **Memory**: > 80% sustained for 5+ minutes
- **Response Time**: 95th percentile > 3 seconds
- **Queue Length**: Celery queue > 100 pending tasks

#### Scaling Procedures
```bash
# Scale API workers
docker-compose -f docker-compose.prod.yml up -d --scale api=3

# Scale Celery workers  
docker-compose -f docker-compose.prod.yml up -d --scale celery_worker=3

# Monitor scaling effectiveness
./scripts/monitor_scaling.sh --duration=30m
```

---

## Emergency Contacts and Procedures

### Escalation Path
1. **On-Call Engineer**: Immediate response for critical alerts
2. **Technical Lead**: For complex issues requiring architectural decisions
3. **DevOps Team**: For infrastructure and deployment issues
4. **Business Owner**: For issues affecting revenue or customer experience

### Emergency Response Playbook
1. **Assess Impact**: Determine severity and user impact
2. **Immediate Response**: Apply temporary fixes to restore service
3. **Communication**: Update status page and notify stakeholders  
4. **Root Cause Analysis**: Investigate and document incident
5. **Post-Mortem**: Review response and implement improvements

### Status Page Updates
```bash
# Update status page during incidents
curl -X POST "https://api.statuspage.io/v1/pages/PAGE_ID/incidents" \
  -H "Authorization: OAuth TOKEN" \
  -d "incident[name]=Database Performance Issues" \
  -d "incident[status]=investigating" \
  -d "incident[impact_override]=minor"
```

This operations guide provides the foundation for maintaining a reliable, secure, and performant FairEdge production environment.