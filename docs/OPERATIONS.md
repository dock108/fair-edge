# Operations Guide

Production monitoring, maintenance, and troubleshooting guide.

## 🔍 Monitoring

### Health Checks

```bash
# API health
curl https://your-domain.com/health

# Service status
docker compose ps

# Container health
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
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

### Logs

```bash
# View all logs
docker compose logs -f

# Specific service logs
docker compose logs -f api
docker compose logs -f celery-worker
docker compose logs -f celery-beat

# Filter by time
docker compose logs --since 1h api

# Search logs
docker compose logs api | grep ERROR
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

### Database Maintenance

```bash
# Backup database
docker compose exec -T db pg_dump -U postgres fairedge > backup_$(date +%Y%m%d_%H%M%S).sql

# Vacuum and analyze
docker compose exec db psql -U postgres -d fairedge -c "VACUUM ANALYZE;"

# Check table sizes
docker compose exec db psql -U postgres -d fairedge -c "
  SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
  FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

### Cache Management

```bash
# Monitor Redis memory
docker compose exec redis redis-cli INFO memory

# Clear cache (caution in production)
docker compose exec redis redis-cli FLUSHALL

# View cache keys
docker compose exec redis redis-cli --scan --pattern "fair-edge:*"
```

## 🚨 Incident Response

### Common Issues

**High Memory Usage:**
```bash
# Check memory by container
docker stats --no-stream

# Restart memory-heavy service
docker compose restart celery-worker
```

**API Errors Spike:**
```bash
# Check recent errors
docker compose logs --since 10m api | grep ERROR

# Scale workers if needed
docker compose up -d --scale celery-worker=3
```

**Database Connection Issues:**
```bash
# Check connections
docker compose exec db psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Kill idle connections
docker compose exec db psql -U postgres -c "
  SELECT pg_terminate_backend(pid)
  FROM pg_stat_activity
  WHERE state = 'idle' AND state_change < now() - interval '10 minutes';"
```

### Recovery Procedures

**Service Recovery:**
```bash
# Restart all services
docker compose restart

# Hard restart with cleanup
docker compose down
docker compose up -d
```

**Database Recovery:**
```bash
# Restore from backup
docker compose exec -T db psql -U postgres -d postgres -c "DROP DATABASE IF EXISTS fairedge;"
docker compose exec -T db psql -U postgres -d postgres -c "CREATE DATABASE fairedge;"
docker compose exec -T db psql -U postgres -d fairedge < backup_20240101_120000.sql
```

## 📊 Performance Tuning

### API Optimization

```python
# Check slow endpoints
docker compose logs api | grep "duration" | sort -k5 -nr | head -20
```

### Database Optimization

```sql
-- Find slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public'
AND n_distinct > 100
AND correlation < 0.1
ORDER BY n_distinct DESC;
```

### Redis Optimization

```bash
# Memory optimization
docker compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Check eviction stats
docker compose exec redis redis-cli INFO stats | grep evict
```

## 🔐 Security

### Regular Audits

```bash
# Check for exposed ports
netstat -tlnp | grep LISTEN

# Review user permissions
docker compose exec db psql -U postgres -c "\du"

# Check SSL certificates
echo | openssl s_client -connect your-domain.com:443 2>/dev/null | openssl x509 -noout -dates
```

### Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Update Docker images
docker compose pull
docker compose up -d

# Update dependencies
cd frontend && npm audit fix
pip list --outdated
```

## 📈 Scaling

### Horizontal Scaling

```bash
# Scale workers
docker compose up -d --scale celery-worker=5

# Add read replicas (configure in docker-compose.prod.yml)
docker compose up -d db-replica
```

### Resource Limits

```yaml
# docker-compose.prod.yml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

## 🆘 Emergency Contacts

- **On-call**: Check rotation schedule
- **Escalation**: Development team lead
- **Infrastructure**: DevOps team
- **Database**: DBA on-call

## 📋 Runbooks

### Deployment Rollback
1. Identify the last working commit
2. `git checkout <commit-hash>`
3. `docker compose build --no-cache`
4. `docker compose up -d`

### Emergency Maintenance Mode
1. Update Caddy to serve maintenance page
2. Stop API services
3. Perform maintenance
4. Restore services

### Data Recovery
1. Stop write operations
2. Create point-in-time backup
3. Restore to test environment
4. Verify data integrity
5. Restore to production