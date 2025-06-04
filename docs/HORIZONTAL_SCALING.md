# Horizontal Scaling Architecture - Phase 3.8

This document outlines the strategy for horizontally scaling bet-intel to handle increased traffic and computational demands.

## Current Architecture (Phase 3)

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │     FastAPI     │    │   Celery Beat   │
│    (Future)     │    │   (1 instance)  │    │  (Scheduler)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ├───────────────────────┼───────────────────────┤
         │                       │                       │
         v                       v                       v
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Redis Cache   │    │   PostgreSQL    │    │ Celery Workers  │
│   (Centralized) │    │   (Single DB)   │    │  (N instances)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Target Architecture (Horizontal Scale)

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   FastAPI Pod   │    │   FastAPI Pod   │
│ (nginx/HAProxy) │    │   (Instance 1)  │    │   (Instance 2)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ├───────────────────────┼───────────────────────┤
         │                       │                       │
         v                       v                       v
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Redis Cluster │    │  PostgreSQL     │    │   Celery Beat   │
│  (Multi-node)   │    │   (Primary +    │    │  (Single Inst)  │
│                 │    │   Read Replicas)│    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┤
                                 │                       │
                                 v                       v
                    ┌─────────────────┐    ┌─────────────────┐
                    │ Celery Workers  │    │ Celery Workers  │
                    │   (Pool 1)      │    │   (Pool 2)      │
                    └─────────────────┘    └─────────────────┘
```

## Scaling Strategy by Component

### 1. FastAPI Application Servers

#### Current State
- Single FastAPI instance handling all requests
- Uvicorn with gunicorn worker processes (Phase 3.4)

#### Scaling Approach
```yaml
# docker-compose.yml for horizontal scaling
version: '3.8'
services:
  fastapi-1:
    build: .
    environment:
      - WORKER_ID=1
      - MAX_WORKERS=4
    ports:
      - "8001:8000"
  
  fastapi-2:
    build: .
    environment:
      - WORKER_ID=2
      - MAX_WORKERS=4
    ports:
      - "8002:8000"
  
  fastapi-3:
    build: .
    environment:
      - WORKER_ID=3
      - MAX_WORKERS=4
    ports:
      - "8003:8000"
  
  nginx:
    image: nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - fastapi-1
      - fastapi-2
      - fastapi-3
```

#### Load Balancer Configuration
```nginx
# nginx.conf
upstream fastapi_backend {
    least_conn;  # Distribute based on active connections
    server fastapi-1:8000 max_fails=3 fail_timeout=30s;
    server fastapi-2:8000 max_fails=3 fail_timeout=30s;
    server fastapi-3:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    
    location / {
        proxy_pass http://fastapi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Health check bypass
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503;
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    location /health {
        access_log off;
        proxy_pass http://fastapi_backend/health;
    }
}
```

### 2. Redis Cache Cluster

#### Current State
- Single Redis instance for caching and Celery broker

#### Scaling Approach
```yaml
# Redis Cluster Configuration
redis-cluster:
  image: redis:7-alpine
  command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf
  volumes:
    - redis-data:/data
  
redis-node-1:
  extends: redis-cluster
  ports:
    - "7001:6379"
  
redis-node-2:
  extends: redis-cluster
  ports:
    - "7002:6379"
    
redis-node-3:
  extends: redis-cluster
  ports:
    - "7003:6379"
```

#### Cache Sharding Strategy
```python
# core/cache.py - Updated for cluster support
class RedisClusterCache(Cache):
    def __init__(self):
        from rediscluster import RedisCluster
        
        startup_nodes = [
            {"host": "redis-node-1", "port": "7001"},
            {"host": "redis-node-2", "port": "7002"},
            {"host": "redis-node-3", "port": "7003"},
        ]
        
        self.redis = RedisCluster(
            startup_nodes=startup_nodes,
            decode_responses=True,
            skip_full_coverage_check=True
        )
    
    async def get_with_fallback(self, key: str, fallback_nodes: List[str] = None):
        """Get with automatic failover to other cluster nodes"""
        try:
            return await self.redis.get(key)
        except Exception as e:
            logger.warning(f"Redis cluster node failed for key {key}: {e}")
            # Automatic cluster failover handles this
            raise
```

### 3. PostgreSQL Database Scaling

#### Current State
- Single PostgreSQL instance

#### Scaling Approach - Read Replicas
```yaml
# Database scaling with read replicas
postgres-primary:
  image: postgres:15
  environment:
    POSTGRES_DB: bet_intel
    POSTGRES_REPLICATION_USER: replicator
    POSTGRES_REPLICATION_PASSWORD: replica_pass
  volumes:
    - postgres-primary-data:/var/lib/postgresql/data
    - ./postgresql.conf:/etc/postgresql/postgresql.conf
  
postgres-replica-1:
  image: postgres:15
  environment:
    PGUSER: postgres
    POSTGRES_PASSWORD: replica_pass
    POSTGRES_MASTER_SERVICE: postgres-primary
  command: |
    bash -c "
    until pg_basebackup -h postgres-primary -D /var/lib/postgresql/data -U replicator -v -P -W; do
    echo 'Waiting for primary to connect...'
    sleep 1s
    done
    echo 'Backup done, starting replica...'
    chmod 0700 /var/lib/postgresql/data
    postgres
    "
```

#### Read/Write Splitting
```python
# core/database.py - Database connection routing
class DatabaseRouter:
    def __init__(self):
        self.write_engine = create_engine(settings.postgres_write_url)
        self.read_engines = [
            create_engine(settings.postgres_read_url_1),
            create_engine(settings.postgres_read_url_2),
        ]
        self.read_pool_index = 0
    
    def get_read_session(self):
        """Round-robin read replica selection"""
        engine = self.read_engines[self.read_pool_index]
        self.read_pool_index = (self.read_pool_index + 1) % len(self.read_engines)
        return SessionLocal(bind=engine)
    
    def get_write_session(self):
        """Always use primary for writes"""
        return SessionLocal(bind=self.write_engine)

# Usage in API endpoints
@app.get("/api/opportunities")
async def get_opportunities():
    """Read-only endpoint uses replica"""
    db = database_router.get_read_session()
    # ... read operations
    
@app.post("/api/opportunities/refresh")
async def refresh_opportunities():
    """Write operations use primary"""
    db = database_router.get_write_session()
    # ... write operations
```

### 4. Celery Worker Scaling

#### Current State
- Single worker pool processing all tasks

#### Scaling Approach - Dedicated Worker Pools
```yaml
# Specialized worker pools
celery-worker-ev:
  build: .
  command: celery -A services.celery_app worker --loglevel=info --queues=ev_calculation --concurrency=4
  environment:
    - WORKER_TYPE=ev_calculation
  
celery-worker-data:
  build: .
  command: celery -A services.celery_app worker --loglevel=info --queues=data_refresh --concurrency=2
  environment:
    - WORKER_TYPE=data_refresh
  
celery-worker-notifications:
  build: .
  command: celery -A services.celery_app worker --loglevel=info --queues=notifications --concurrency=8
  environment:
    - WORKER_TYPE=notifications
```

#### Queue Routing Configuration
```python
# services/celery_app.py - Queue routing
celery_app.conf.update(
    task_routes={
        'ev.calc_batch': {'queue': 'ev_calculation'},
        'refresh_odds_data': {'queue': 'data_refresh'},
        'send_notification': {'queue': 'notifications'},
        'health_check': {'queue': 'data_refresh'},
    },
    
    # Worker-specific settings
    worker_pool_restarts=True,
    worker_max_memory_per_child=200000,  # 200MB per child process
    worker_autoscaler='celery.worker.autoscale:Autoscaler',
    worker_autoscale_max=8,
    worker_autoscale_min=2,
)
```

## Container Orchestration (Kubernetes)

For larger scale deployments, use Kubernetes for automatic scaling:

```yaml
# k8s-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bet-intel-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: bet-intel-api
  template:
    metadata:
      labels:
        app: bet-intel-api
    spec:
      containers:
      - name: fastapi
        image: bet-intel:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          value: "redis://redis-cluster:6379"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: bet-intel-service
spec:
  selector:
    app: bet-intel-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: bet-intel-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: bet-intel-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Monitoring and Observability

### Prometheus Metrics for Scaling
```python
# Enhanced metrics for scaling decisions
from prometheus_client import Counter, Histogram, Gauge

# Application metrics
request_count = Counter('requests_total', 'Total requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('request_duration_seconds', 'Request duration')
active_connections = Gauge('active_connections', 'Active connections', ['worker_id'])

# Database metrics
db_query_duration = Histogram('db_query_duration_seconds', 'Database query duration', ['operation'])
db_connection_pool = Gauge('db_connections_active', 'Active DB connections', ['pool_type'])

# Cache metrics
cache_hit_rate = Gauge('cache_hit_rate', 'Cache hit rate percentage')
cache_memory_usage = Gauge('cache_memory_bytes', 'Cache memory usage')

# Celery metrics
celery_task_duration = Histogram('celery_task_duration_seconds', 'Task duration', ['task_name'])
celery_queue_length = Gauge('celery_queue_length', 'Queue length', ['queue_name'])
celery_workers_active = Gauge('celery_workers_active', 'Active workers', ['worker_type'])
```

### Grafana Dashboard Panels
- **Request Rate**: requests/second across all instances
- **Response Time**: p95/p99 latency by endpoint
- **Error Rate**: 4xx/5xx errors by instance
- **Database Performance**: query times, connection pool usage
- **Cache Performance**: hit rate, memory usage, eviction rate
- **Celery Performance**: queue depth, task processing time
- **Resource Usage**: CPU, memory, disk I/O per container

## Scaling Thresholds

### Automatic Scaling Triggers
```yaml
# HPA configuration for different metrics
metrics:
- type: Resource
  resource:
    name: cpu
    target:
      type: Utilization
      averageUtilization: 70  # Scale up at 70% CPU
      
- type: Resource
  resource:
    name: memory
    target:
      type: Utilization
      averageUtilization: 80  # Scale up at 80% memory
      
- type: Pods
  pods:
    metric:
      name: requests_per_second
    target:
      type: AverageValue
      averageValue: "100"  # Scale up at 100 RPS per pod
      
- type: Object
  object:
    metric:
      name: celery_queue_depth
    target:
      type: Value
      value: "50"  # Scale workers when queue > 50 tasks
```

### Manual Scaling Guidelines
- **FastAPI instances**: Scale when avg response time > 200ms
- **Celery workers**: Scale when queue depth > 30 seconds processing time  
- **Database replicas**: Add when read query time > 50ms
- **Redis nodes**: Scale when memory usage > 80% or hit rate < 95%

## Cost Optimization

### Resource Right-Sizing
```yaml
# Production resource allocation
fastapi:
  requests:
    memory: "256Mi"
    cpu: "200m"
  limits:
    memory: "512Mi" 
    cpu: "500m"
    
celery-worker:
  requests:
    memory: "512Mi"
    cpu: "300m"
  limits:
    memory: "1Gi"
    cpu: "800m"
    
redis:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "200m"
```

### Auto-scaling Policies
- **Scale down delay**: 5 minutes (prevent flapping)
- **Scale up delay**: 30 seconds (respond quickly to load)
- **Min replicas**: 3 (high availability)
- **Max replicas**: 20 (cost control)

## Implementation Phases

### Phase 1: Load Balancer + Multiple FastAPI Instances
1. Deploy nginx load balancer
2. Scale FastAPI to 3 instances
3. Update health checks and monitoring
4. Test failover scenarios

### Phase 2: Database Read Replicas  
1. Set up PostgreSQL streaming replication
2. Implement read/write routing in application
3. Monitor replication lag
4. Update connection pooling

### Phase 3: Redis Cluster
1. Deploy Redis cluster with 3 nodes
2. Update application to use Redis Cluster client
3. Test failover and data distribution
4. Monitor cluster health

### Phase 4: Celery Worker Specialization
1. Create dedicated worker pools by task type
2. Implement queue routing
3. Add worker auto-scaling
4. Monitor queue performance

### Phase 5: Container Orchestration
1. Migrate to Kubernetes
2. Implement horizontal pod autoscaling
3. Add advanced monitoring and alerting
4. Optimize resource allocation

This architecture enables bet-intel to scale from hundreds to thousands of requests per second while maintaining sub-200ms response times and high availability. 