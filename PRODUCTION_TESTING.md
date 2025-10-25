# Production Deployment Testing Guide

## Overview
This document provides comprehensive testing procedures for validating the Replo HQ production deployment.

## Deployment Status ✅

### Services Status
All core services are running and operational:

| Service | Status | Health Check | Ports |
|---------|--------|--------------|-------|
| **Backend** | ✅ Healthy | `/api/health` | 8000 |
| **Frontend** | ✅ Running | HTTP 200 | 3000 |
| **PostgreSQL** | ✅ Healthy | Internal | 5432 |
| **Redis** | ✅ Healthy | Internal | 6379 |
| **Worker** | ✅ Running | ARQ Worker | - |

## Fixed Issues

### 1. Redis Authentication ✅
- **Problem**: Redis was running in protected mode without authentication
- **Solution**: Enabled `requirepass` in `redis-prod.conf` with password authentication
- **Validation**: Backend successfully connects with "Redis connection pool initialized"

### 2. Backend Health Check ✅
- **Problem**: Health check was using incorrect endpoint `/health`
- **Solution**: Updated to correct endpoint `/api/health` in `docker-compose.prod.yml`
- **Validation**: Backend container shows healthy status

### 3. Worker Configuration ✅
- **Problem**: Worker was looking for `WorkerSettings` in wrong module
- **Solution**: Fixed command to use `app.workers.worker.WorkerSettings`
- **Validation**: Worker starts successfully and connects to Redis

## Testing Procedures

### 1. Service Health Checks

#### Backend API Test
```bash
curl http://localhost:8000/api/health
# Expected: {"status":"ok","message":"Backend is running!"}
```

#### Frontend Test
```bash
curl -I http://localhost:3000
# Expected: HTTP/1.1 200 OK
```

#### Alternative Health Endpoint
```bash
curl http://localhost:8000/api/v1/health
# Expected: {"status":"ok","message":"Backend is running!"}
```

### 2. Container Status Validation
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### 3. Service Logs Monitoring

#### Backend Logs
```bash
docker logs replo-hq-backend-1 --tail 20
# Look for: "Redis connection pool initialized"
```

#### Worker Logs
```bash
docker logs replo-hq-worker-1 --tail 20
# Look for: "Starting worker for 1 functions: process_repository_analysis"
```

#### Redis Connection Test
```bash
docker logs replo-hq-backend-1 | grep -i redis
# Should show successful Redis connection
```

### 4. Inter-Container Communication

#### Redis Connectivity
- Backend → Redis: ✅ Confirmed via connection pool initialization
- Worker → Redis: ✅ Confirmed via ARQ worker startup

#### Database Connectivity
- Backend → PostgreSQL: ✅ Confirmed via healthy status
- Application startup completes without database errors

## Deployment Commands

### Start Production Environment
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Stop Production Environment
```bash
docker-compose -f docker-compose.prod.yml down
```

### Restart Specific Service
```bash
docker-compose -f docker-compose.prod.yml restart <service_name>
```

### Force Recreate Service
```bash
docker-compose -f docker-compose.prod.yml up -d --force-recreate <service_name>
```

## Environment Configuration

### Required Environment Variables
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `REDIS_PASSWORD` (set to `redis_password_123`)
- `BACKEND_VERSION`, `FRONTEND_VERSION` (default: latest)

### Redis Configuration
- Authentication enabled with password
- Protected mode: enabled
- Configuration file: `redis-prod.conf`

### Database Configuration
- PostgreSQL 15 Alpine
- Configuration file: `postgres-prod.conf`

## Troubleshooting

### Common Issues

1. **Redis Connection Denied**
   - Check `redis-prod.conf` has correct `requirepass` setting
   - Verify `REDIS_PASSWORD` environment variable matches

2. **Backend Health Check Failing**
   - Ensure health check endpoint is `/api/health` not `/health`
   - Check backend logs for startup errors

3. **Worker Import Errors**
   - Verify worker command uses `app.workers.worker.WorkerSettings`
   - Check worker logs for module import issues

### Log Analysis Commands
```bash
# Check all container statuses
docker ps

# View specific service logs
docker logs <container_name> --tail 50

# Follow logs in real-time
docker logs <container_name> -f

# Check resource usage
docker stats
```

## Success Criteria ✅

- [x] All containers start successfully
- [x] Backend API responds to health checks
- [x] Frontend serves content (HTTP 200)
- [x] Redis authentication working
- [x] Worker connects to Redis and starts processing
- [x] No critical errors in logs
- [x] Inter-container communication functional

## Next Steps

1. **Performance Testing**: Load test the API endpoints
2. **Security Review**: Audit exposed ports and authentication
3. **Monitoring Setup**: Implement logging and metrics collection
4. **Backup Strategy**: Configure database and Redis backups
5. **SSL/TLS**: Add HTTPS support for production

---

**Last Updated**: October 25, 2025  
**Deployment Status**: ✅ OPERATIONAL