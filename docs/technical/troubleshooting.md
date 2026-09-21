# DMLog Troubleshooting Guide

## Overview

This comprehensive troubleshooting guide helps diagnose and resolve common issues with DMLog deployments. It covers system failures, performance problems, database issues, network problems, and more.

## Quick Diagnosis Checklist

### System Health Check
```bash
# 1. Check all services status
docker-compose ps

# 2. Check system resources
docker stats
free -h
df -h
top

# 3. Check application health
curl -f http://localhost:8000/api/v1/health

# 4. Check logs for errors
docker-compose logs --tail=50 api
```

### Network Connectivity
```bash
# 1. Test API connectivity
curl -v http://localhost:8000/api/v1/characters/

# 2. Test database connectivity
docker-compose exec postgres pg_isready

# 3. Test Redis connectivity
docker-compose exec redis redis-cli ping

# 4. Check port availability
netstat -tlnp | grep -E ':(80|443|8000|5432|6379|3000|3001)'
```

## Common Issues and Solutions

### 1. Application Startup Issues

#### Problem: API Server Won't Start
**Symptoms:**
- Container exits immediately
- Health check failures
- Connection refused errors

**Diagnosis:**
```bash
# Check container logs
docker-compose logs api

# Check configuration
docker-compose config

# Verify environment variables
docker-compose exec api env | grep -E '(DATABASE|REDIS|SECRET)'

# Check database connection
docker-compose exec api python -c "
import asyncio
import asyncpg

async def test_db():
    try:
        conn = await asyncpg.connect('$DATABASE_URL')
        print('Database connection successful')
        await conn.close()
    except Exception as e:
        print(f'Database connection failed: {e}')

asyncio.run(test_db())
"
```

**Solutions:**

1. **Database Connection Issues**
```bash
# Fix database URL format
DATABASE_URL="postgresql+asyncpg://username:password@host:5432/database"

# Check if database is running
docker-compose restart postgres

# Wait for database to be ready
docker-compose exec postgres timeout 30 bash -c 'until pg_isready; do sleep 1; done'
```

2. **Port Conflicts**
```bash
# Find what's using the port
sudo lsof -i :8000

# Kill conflicting process
sudo kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "8001:8000"  # Use different port
```

3. **Environment Variable Issues**
```bash
# Check .env file
cat .env

# Verify required variables
grep -E '^DATABASE_URL|^REDIS_URL|^SECRET_KEY' .env

# Regenerate secrets
openssl rand -hex 32
```

#### Problem: Frontend Not Loading
**Symptoms:**
- Blank page or 404 errors
- Static assets not loading
- CORS errors

**Diagnosis:**
```bash
# Check Nginx configuration
docker-compose exec nginx nginx -t

# Check Nginx logs
docker-compose logs nginx

# Test static file serving
curl -I http://localhost:3000/static/css/main.css

# Check CORS headers
curl -v -H "Origin: http://localhost:3000" http://localhost:8000/api/v1/characters/
```

**Solutions:**

1. **Nginx Configuration Issues**
```nginx
# Ensure correct upstream configuration
upstream api {
    server api:8000;
}

server {
    listen 80;

    # Serve frontend
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests
    location /api/ {
        proxy_pass http://api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

2. **CORS Issues**
```python
# In FastAPI app
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. Database Issues

#### Problem: Database Connection Refused
**Symptoms:**
- "Connection refused" errors
- Timeout errors
- Authentication failures

**Diagnosis:**
```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready

# Check PostgreSQL logs
docker-compose logs postgres

# Test connection from API container
docker-compose exec api python -c "
import asyncpg
import asyncio

async def test():
    try:
        conn = await asyncpg.connect('postgresql://user:pass@postgres:5432/dmlog')
        print('Connection successful')
        await conn.close()
    except Exception as e:
        print(f'Connection failed: {e}')

asyncio.run(test())
"
```

**Solutions:**

1. **Database Not Ready**
```bash
# Restart PostgreSQL
docker-compose restart postgres

# Wait for database to be ready
docker-compose exec postgres bash -c '
until pg_isready -h localhost -p 5432; do
  echo "Waiting for database..."
  sleep 2
done
'

# Run migrations
docker-compose exec api alembic upgrade head
```

2. **Authentication Issues**
```bash
# Check database credentials
docker-compose exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT current_user;"

# Reset password if needed
docker-compose exec postgres psql -U postgres -c "
ALTER USER dmlog_user PASSWORD 'new_password';
"
```

3. **Connection Pool Issues**
```python
# Increase pool size in settings
DATABASE_CONFIG = {
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 3600,
}
```

#### Problem: Slow Database Queries
**Symptoms:**
- API responses are slow
- Database timeout errors
- High CPU usage on database

**Diagnosis:**
```sql
-- Check slow queries
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Check active connections
SELECT state, count(*)
FROM pg_stat_activity
GROUP BY state;

-- Check table sizes
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC
LIMIT 10;
```

**Solutions:**

1. **Add Missing Indexes**
```sql
-- Add indexes for frequently queried columns
CREATE INDEX CONCURRENTLY idx_characters_active ON characters(is_active);
CREATE INDEX CONCURRENTLY idx_sessions_campaign ON sessions(campaign_id);
CREATE INDEX CONCURRENTLY idx_characters_name ON characters(name);

-- Create composite indexes for common query patterns
CREATE INDEX CONCURRENTLY idx_sessions_status_campaign
ON sessions(status, campaign_id);
```

2. **Optimize Queries**
```python
# Use selectinload for relationships
from sqlalchemy.orm import selectinload

# Instead of lazy loading
characters = await session.execute(
    select(Character).options(selectinload(Character.memories))
)

# Use pagination for large result sets
characters = await session.execute(
    select(Character)
    .offset(skip)
    .limit(limit)
)
```

3. **Connection Pool Tuning**
```python
# Optimize connection pool
DATABASE_URL = "postgresql+asyncpg://user:pass@host:5432/db?pool_size=20&max_overflow=30&pool_timeout=30&pool_recycle=3600"
```

#### Problem: Database Locks
**Symptoms:**
- Queries hanging indefinitely
- "Lock wait timeout" errors
- Deadlock errors

**Diagnosis:**
```sql
-- Check for locks
SELECT blocked_locks.pid AS blocked_pid,
       blocked_activity.usename AS blocked_user,
       blocking_locks.pid AS blocking_pid,
       blocking_activity.usename AS blocking_user,
       blocked_activity.query AS blocked_statement,
       blocking_activity.query AS current_statement_in_blocking_process
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;

-- Check long-running queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';
```

**Solutions:**

1. **Kill Long-Running Queries**
```sql
-- Terminate specific query
SELECT pg_terminate_backend(pid);

-- Cancel specific query
SELECT pg_cancel_backend(pid);
```

2. **Optimize Transaction Handling**
```python
# Keep transactions short
async def update_character(character_id: str, updates: dict):
    async with get_db_session() as session:
        try:
            character = await session.get(Character, character_id)
            for key, value in updates.items():
                setattr(character, key, value)
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### 3. Cache Issues

#### Problem: Redis Connection Fails
**Symptoms:**
- Cache-related errors
- Slow performance
- Session management issues

**Diagnosis:**
```bash
# Check Redis status
docker-compose exec redis redis-cli ping

# Check Redis logs
docker-compose logs redis

# Test Redis from API container
docker-compose exec api python -c "
import redis
try:
    r = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
    print('Redis connection successful:', r.ping())
    print('Memory usage:', r.info()['used_memory_human'])
except Exception as e:
    print(f'Redis connection failed: {e}')
"
```

**Solutions:**

1. **Redis Memory Issues**
```bash
# Check memory usage
docker-compose exec redis redis-cli info memory

# Clear cache if needed
docker-compose exec redis redis-cli FLUSHDB

# Configure memory limits
# In redis.conf or docker-compose.yml
maxmemory 2gb
maxmemory-policy allkeys-lru
```

2. **Connection Pool Issues**
```python
# Optimize Redis connection pool
REDIS_CONFIG = {
    "host": "redis",
    "port": 6379,
    "db": 0,
    "max_connections": 50,
    "retry_on_timeout": True,
    "socket_keepalive": True,
    "socket_keepalive_options": {},
}
```

#### Problem: Cache Inconsistency
**Symptoms:**
- Stale data being served
- Inconsistent API responses
- Cache misses

**Diagnosis:**
```bash
# Check cache hit rate
docker-compose exec redis redis-cli info stats | grep keyspace

# Monitor cache operations
docker-compose exec redis redis-cli monitor

# Check specific cache keys
docker-compose exec redis redis-cli keys "character:*"
```

**Solutions:**

1. **Implement Cache Invalidation**
```python
# Cache invalidation on updates
async def update_character(character_id: str, updates: dict):
    cache_manager = await get_cache_manager()

    # Update database
    character = await repo.update(character_id, updates)

    # Invalidate cache
    await cache_manager.delete_character(character_id)

    return character
```

2. **Add Cache Expiration**
```python
# Set TTL for cache entries
await cache_manager.set(
    f"character:{character_id}",
    character_data,
    ttl=3600  # 1 hour
)
```

### 4. Performance Issues

#### Problem: High Memory Usage
**Symptoms:**
- Container OOM kills
- Slow response times
- System swapping

**Diagnosis:**
```bash
# Check memory usage by container
docker stats --no-stream

# Check system memory
free -h

# Check for memory leaks in application
docker-compose exec api python -c "
import tracemalloc
tracemalloc.start()

# Run your application code here...
# Then check memory usage
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)
"
```

**Solutions:**

1. **Optimize Memory Usage**
```python
# Use generators for large datasets
async def list_characters(limit: int = 100):
    async for character in character_repo.stream(limit=limit):
        yield character

# Clear object references
def process_large_data(data):
    result = process(data)
    del data  # Explicitly free memory
    return result
```

2. **Increase Container Memory Limits**
```yaml
# In docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
```

#### Problem: High CPU Usage
**Symptoms:**
- Slow API responses
- High system load
- Container CPU throttling

**Diagnosis:**
```bash
# Check CPU usage by container
docker stats --no-stream

# Check system load
top
htop

# Profile Python application
docker-compose exec api python -m cProfile -o profile.stats -m source_code.backend.api_server_new
```

**Solutions:**

1. **Optimize Code Performance**
```python
# Use async/await properly
async def fetch_characters():
    tasks = [fetch_character(id) for id in character_ids]
    return await asyncio.gather(*tasks)

# Use efficient data structures
from collections import defaultdict
character_map = defaultdict(list)

# Avoid unnecessary computations
@lru_cache(maxsize=128)
def expensive_calculation(param):
    # Complex calculation
    return result
```

2. **Add Caching**
```python
# Cache expensive operations
from functools import lru_cache

@lru_cache(maxsize=1000)
def calculate_character_stats(character_data):
    # Expensive calculation
    return stats
```

#### Problem: Slow API Responses
**Symptoms:**
- Response times > 1 second
- Timeout errors
- Poor user experience

**Diagnosis:**
```bash
# Measure API response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/v1/characters/

# Profile API endpoints
docker-compose exec api python -c "
import time
import asyncio

async def time_request():
    start = time.time()
    async with httpx.AsyncClient() as client:
        response = await client.get('http://localhost:8000/api/v1/characters/')
    end = time.time()
    print(f'Request took {end - start:.2f} seconds')

asyncio.run(time_request())
"
```

**Solutions:**

1. **Database Optimization**
```sql
-- Add indexes for frequently queried columns
EXPLAIN ANALYZE SELECT * FROM characters WHERE is_active = true;

-- Use database-specific optimizations
SET work_mem = '256MB';
SET shared_buffers = '256MB';
```

2. **Implement Response Caching**
```python
from fastapi import Response

@app.get("/api/v1/characters/")
@cache(expire=300)  # 5 minutes
async def list_characters():
    return await character_service.get_all()
```

### 5. WebSocket Issues

#### Problem: WebSocket Connection Fails
**Symptoms:**
- Connection refused errors
- Connection drops frequently
- Real-time updates not working

**Diagnosis:**
```bash
# Test WebSocket connection
wscat -c ws://localhost:8000/ws/connect?user_id=test

# Check WebSocket logs
docker-compose logs api | grep websocket

# Monitor WebSocket connections
docker-compose exec api python -c "
import asyncio
import websockets

async def test_websocket():
    uri = "ws://localhost:8000/ws/connect?user_id=test"
    async with websockets.connect(uri) as websocket:
        await websocket.send('{"type": "ping"}')
        response = await websocket.recv()
        print(f"Received: {response}")

asyncio.run(test_websocket())
"
```

**Solutions:**

1. **Fix WebSocket Configuration**
```python
# Ensure proper WebSocket middleware
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/connect")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            # Process message
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        # Handle disconnect
        pass
```

2. **Handle Connection Timeouts**
```python
# Set appropriate timeouts
@app.websocket("/ws/connect")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                # Process message
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_text('{"type": "ping"}')
    except WebSocketDisconnect:
        pass
```

### 6. SSL/TLS Issues

#### Problem: SSL Certificate Errors
**Symptoms:**
- Certificate expired warnings
- Chain certificate errors
- HTTPS not working

**Diagnosis:**
```bash
# Check certificate validity
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/cert.pem -text -noout

# Check certificate chain
openssl s_client -connect yourdomain.com:443 -showcerts

# Test SSL configuration
sslscan yourdomain.com

# Check certificate expiration
certbot certificates
```

**Solutions:**

1. **Renew Certificate**
```bash
# Force renewal
sudo certbot renew --force-renewal

# Test renewal process
sudo certbot renew --dry-run

# Setup auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

2. **Fix Certificate Chain**
```nginx
# Ensure full chain is served
ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
```

### 7. Monitoring Issues

#### Problem: Prometheus Not Collecting Metrics
**Symptoms:**
- No data in Grafana dashboards
- Prometheus target down
- Missing metrics

**Diagnosis:**
```bash
# Check Prometheus configuration
docker-compose exec prometheus promtool check config /etc/prometheus/prometheus.yml

# Check target status
curl http://localhost:9090/api/v1/targets

# Check metrics endpoint
curl http://localhost:8000/metrics

# Check Prometheus logs
docker-compose logs prometheus
```

**Solutions:**

1. **Fix Prometheus Configuration**
```yaml
# Ensure correct scrape configuration
scrape_configs:
  - job_name: 'dmlog-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
    scrape_timeout: 10s
```

2. **Ensure Metrics are Exposed**
```python
# Add metrics to FastAPI app
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(duration)

    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## Advanced Troubleshooting

### Debug Mode

#### Enable Debug Logging
```python
# In production settings
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "detailed"
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "filename": "/app/logs/debug.log",
            "formatter": "detailed"
        }
    },
    "loggers": {
        "": {
            "level": "DEBUG",
            "handlers": ["console", "file"]
        }
    }
}
```

#### Performance Profiling
```python
# Add profiling middleware
import cProfile
import io
import pstats

@app.middleware("http")
async def profiling_middleware(request: Request, call_next):
    if request.query_params.get("profile") == "true":
        pr = cProfile.Profile()
        pr.enable()

        response = await call_next(request)

        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(50)

        # Add profiling info to response headers
        response.headers["X-Profile-Data"] = s.getvalue()
        return response
    else:
        return await call_next(request)
```

### Database Debugging

#### Query Analysis
```sql
-- Enable query logging
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 1000;  # Log queries > 1s
SELECT pg_reload_conf();

-- Analyze query plans
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT * FROM characters WHERE name LIKE '%search%';

-- Check for missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY tablename, attname;
```

#### Connection Pool Monitoring
```python
# Monitor connection pool usage
async def monitor_connection_pool():
    pool = await get_database().engine.pool
    print(f"Pool size: {pool.size()}")
    print(f"Checked in: {pool.checkedin()}")
    print(f"Checked out: {pool.checkedout()}")
    print(f"Invalid: {pool.invalid()}")
```

### Memory Debugging

#### Memory Leak Detection
```python
import tracemalloc
import gc

def start_memory_tracking():
    tracemalloc.start()
    gc.set_debug(gc.DEBUG_STATS)

def take_memory_snapshot():
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')

    print("Top memory allocations:")
    for stat in top_stats[:10]:
        print(stat)

# Usage in API endpoints
@app.get("/debug/memory")
async def debug_memory():
    take_memory_snapshot()
    return {"status": "memory snapshot taken"}
```

#### Object Lifetime Tracking
```python
import weakref

class TrackedObject:
    _instances = weakref.WeakSet()

    def __init__(self):
        self._instances.add(self)

    @classmethod
    def count_instances(cls):
        return len(cls._instances)

# Use for tracking object leaks
@app.get("/debug/objects")
async def debug_objects():
    return {
        "character_instances": TrackedObject.count_instances()
    }
```

## Emergency Procedures

### System Recovery

#### Complete System Restart
```bash
#!/bin/bash
# emergency_restart.sh

echo "Emergency system restart initiated..."

# Backup current state
./scripts/backup_database.sh

# Stop all services
docker-compose down

# Clean up
docker system prune -f

# Start core services first
docker-compose up -d postgres redis

# Wait for services to be ready
sleep 30

# Start application services
docker-compose up -d api nginx

# Verify system health
sleep 10
if curl -f http://localhost:8000/api/v1/health; then
    echo "System recovery successful"
else
    echo "System recovery failed - check logs"
    docker-compose logs --tail=50
fi
```

#### Database Recovery
```bash
#!/bin/bash
# database_recovery.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

echo "Starting database recovery..."

# Stop application services
docker-compose stop api

# Create recovery database
docker-compose exec postgres createdb -U $POSTGRES_USER dmlog_recovery

# Restore backup
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip -c $BACKUP_FILE | docker-compose exec -T postgres psql -U $POSTGRES_USER dmlog_recovery
else
    docker-compose exec -T postgres psql -U $POSTGRES_USER dmlog_recovery < $BACKUP_FILE
fi

# Switch to recovered database
docker-compose exec postgres psql -U $POSTGRES_USER -c "
DROP DATABASE dmlog;
ALTER DATABASE dmlog_recovery RENAME TO dmlog;
"

# Start application services
docker-compose start api

echo "Database recovery completed"
```

### Data Corruption Recovery

#### Character Data Recovery
```python
# scripts/recover_characters.py

import asyncio
import asyncpg
from datetime import datetime

async def recover_corrupted_characters():
    conn = await asyncpg.connect(DATABASE_URL)

    # Find characters with corrupted data
    corrupted = await conn.fetch("""
        SELECT id, name
        FROM characters
        WHERE created_at > NOW() - INTERVAL '1 day'
        AND (name IS NULL OR length(name) = 0)
    """)

    for character in corrupted:
        # Attempt recovery from backups or logs
        print(f"Attempting to recover character {character['id']}")

        # Recovery logic here...
        # Could restore from transaction logs, backups, etc.

    await conn.close()

if __name__ == "__main__":
    asyncio.run(recover_corrupted_characters())
```

## Getting Help

### Support Channels

1. **Documentation**: Check the latest documentation at https://docs.dmlog.com
2. **GitHub Issues**: Report bugs at https://github.com/dmlog/dmlog/issues
3. **Community**: Join our Discord community at https://discord.gg/dmlog
4. **Support Email**: Contact support@dmlog.com for enterprise support

### Reporting Issues

When reporting issues, please include:

1. **System Information**:
   ```bash
   # System info
   uname -a
   docker --version
   docker-compose --version

   # Application info
   curl -s http://localhost:8000/api/v1/health | jq .
   ```

2. **Logs**:
   ```bash
   # Recent logs
   docker-compose logs --tail=100 api > api.log
   docker-compose logs --tail=100 postgres > postgres.log
   docker-compose logs --tail=100 redis > redis.log
   ```

3. **Configuration**:
   ```bash
   # Sanitized configuration
   docker-compose config > compose-config.yml
   # Remove sensitive data before sharing
   ```

4. **Steps to Reproduce**:
   - Clear description of the problem
   - Steps to reproduce the issue
   - Expected vs actual behavior
   - Any error messages received

### Performance Analysis

#### Performance Test Script
```python
# scripts/performance_test.py

import asyncio
import aiohttp
import time
from statistics import mean, median

async def performance_test(base_url: str, num_requests: int = 100):
    """Run performance tests against API endpoints"""

    async with aiohttp.ClientSession() as session:
        times = []

        for i in range(num_requests):
            start_time = time.time()

            try:
                async with session.get(f"{base_url}/api/v1/characters/") as response:
                    await response.text()
                    end_time = time.time()
                    times.append(end_time - start_time)
            except Exception as e:
                print(f"Request {i} failed: {e}")

        if times:
            print(f"Performance Test Results:")
            print(f"Requests: {len(times)}")
            print(f"Average: {mean(times):.3f}s")
            print(f"Median: {median(times):.3f}s")
            print(f"Min: {min(times):.3f}s")
            print(f"Max: {max(times):.3f}s")
            print(f"Success Rate: {len(times)/num_requests*100:.1f}%")

if __name__ == "__main__":
    asyncio.run(performance_test("http://localhost:8000"))
```

This comprehensive troubleshooting guide provides systematic approaches to diagnosing and resolving common issues with DMLog deployments. It includes diagnostic tools, solutions for frequent problems, advanced debugging techniques, and emergency procedures to help maintain system reliability and performance.