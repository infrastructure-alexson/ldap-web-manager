# Health Check Endpoints Documentation

**Version**: 2.2.0 (Phase 1)  
**Status**: Implemented ✅  
**Purpose**: Kubernetes and Docker health monitoring

---

## Overview

The LDAP Web Manager now includes comprehensive health check endpoints that are compatible with Kubernetes probes and Docker health checks. These endpoints allow orchestration platforms to monitor application health and automatically restart unhealthy containers.

---

## Endpoints

### 1. `/health` - Basic Health Check

**Method**: `GET`  
**Purpose**: Simple health status check  
**Use Case**: General monitoring, heartbeat

**Response (200 OK)**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-06T20:15:30.123456",
  "version": "2.2.0"
}
```

**Response (503 Service Unavailable)**:
```json
{
  "detail": "Service not healthy"
}
```

---

### 2. `/health/live` - Liveness Probe

**Method**: `GET`  
**Purpose**: Determine if the service process is running  
**Use Case**: Kubernetes liveness probe

**Kubernetes Configuration**:
```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 3
```

**Response (200 OK)**:
```json
{
  "status": "alive",
  "timestamp": "2025-11-06T20:15:30.123456",
  "uptime_seconds": 3661.234
}
```

**Notes**:
- Only checks if the service is running
- Returns quickly
- Does not check dependencies

---

### 3. `/health/ready` - Readiness Probe

**Method**: `GET`  
**Purpose**: Determine if the service is ready to accept traffic  
**Use Case**: Kubernetes readiness probe

**Kubernetes Configuration**:
```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

**Response (200 OK)**:
```json
{
  "status": "ready",
  "timestamp": "2025-11-06T20:15:30.123456",
  "checks": {
    "database": {
      "status": "ready",
      "message": "Database connected",
      "timestamp": "2025-11-06T20:15:30.123456"
    },
    "ldap": {
      "status": "ready",
      "message": "LDAP connected",
      "server": "ldap://ldap.example.com:389",
      "timestamp": "2025-11-06T20:15:30.123456"
    },
    "config": {
      "status": "ready",
      "message": "Configuration valid",
      "timestamp": "2025-11-06T20:15:30.123456"
    }
  }
}
```

**Response (503 Service Unavailable)**:
```json
{
  "detail": "Service not ready",
  "checks": {
    "database": {
      "status": "unhealthy",
      "message": "Database connection failed: Connection refused"
    },
    "ldap": {
      "status": "degraded",
      "message": "LDAP connection issue: timeout"
    }
  }
}
```

**Notes**:
- Checks all critical dependencies
- Service won't receive traffic until ready
- Returns 503 if any critical check fails

---

### 4. `/health/startup` - Startup Probe

**Method**: `GET`  
**Purpose**: Determine if the service has completed startup  
**Use Case**: Kubernetes startup probe

**Kubernetes Configuration**:
```yaml
startupProbe:
  httpGet:
    path: /health/startup
    port: 8000
  initialDelaySeconds: 0
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 30
```

**Response (200 OK)**:
```json
{
  "status": "started",
  "timestamp": "2025-11-06T20:15:30.123456",
  "checks": {
    "database": {
      "status": "ready"
    },
    "ldap": {
      "status": "ready"
    },
    "config": {
      "status": "ready"
    }
  }
}
```

**Notes**:
- Allows time for service initialization
- Kubernetes waits for success before starting liveness checks
- Useful for services with slow startup times

---

### 5. `/health/detailed` - Detailed Health Report

**Method**: `GET`  
**Purpose**: Comprehensive health information for monitoring dashboards  
**Use Case**: Monitoring, troubleshooting, diagnostics

**Response (200 OK)**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-06T20:15:30.123456",
  "uptime_seconds": 3661.234,
  "version": "2.2.0",
  "checks": {
    "database": {
      "status": "ready",
      "message": "Database connected",
      "timestamp": "2025-11-06T20:15:30.123456"
    },
    "ldap": {
      "status": "ready",
      "message": "LDAP connected",
      "server": "ldap://ldap.example.com:389",
      "timestamp": "2025-11-06T20:15:30.123456"
    },
    "config": {
      "status": "ready",
      "message": "Configuration valid",
      "timestamp": "2025-11-06T20:15:30.123456"
    }
  },
  "services": {
    "api": {
      "status": "running",
      "port": 8000
    },
    "frontend": {
      "status": "running",
      "port": 8080
    }
  }
}
```

**Possible Status Values**:
- `healthy` - All systems operational
- `degraded` - Some non-critical issues
- `unhealthy` - Critical issues present

---

## Docker Health Checks

### Docker Compose Configuration

Update your `docker-compose.yml` to use the health check:

```yaml
services:
  app:
    build: .
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 40s
```

### Docker Run Command

```bash
docker run \
  --health-cmd='curl -f http://localhost:8000/health || exit 1' \
  --health-interval=30s \
  --health-timeout=3s \
  --health-retries=3 \
  --health-start-period=40s \
  ldap-web-manager:latest
```

### Dockerfile Integration

The Dockerfile already includes:

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

---

## Kubernetes Probe Configuration

### Complete Probe Setup

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ldap-web-manager
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: app
        image: ldap-web-manager:2.2.0
        ports:
        - containerPort: 8000
          name: http
        
        # Startup Probe (run first, waits up to 5 minutes)
        startupProbe:
          httpGet:
            path: /health/startup
            port: http
          failureThreshold: 30
          periodSeconds: 10
        
        # Liveness Probe (after startup succeeds)
        livenessProbe:
          httpGet:
            path: /health/live
            port: http
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 3
          failureThreshold: 3
        
        # Readiness Probe (traffic decision)
        readinessProbe:
          httpGet:
            path: /health/ready
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
```

---

## Monitoring Integration

### Prometheus Metrics

Health check status can be monitored through:
- Individual endpoint response codes
- Check result tracking
- Uptime monitoring

### Grafana Dashboards

Monitor using:
- Response time for health endpoints
- HTTP status codes (200 vs 503)
- Check failure rates

---

## Status Codes Reference

| Endpoint | 200 OK | 503 | Notes |
|----------|--------|-----|-------|
| `/health` | Healthy | N/A | Basic status |
| `/health/live` | Alive | No | Liveness probe |
| `/health/ready` | Ready | Not Ready | Readiness probe |
| `/health/startup` | Started | Not Started | Startup probe |
| `/health/detailed` | Healthy | Unhealthy | Detailed report |

---

## Dependency Checks

Each endpoint checks the following dependencies:

### Database Check
- Connects to PostgreSQL
- Executes `SELECT 1`
- Returns status and error message

### LDAP Check
- Connects to LDAP server
- Performs basic search
- Returns status and server info
- **Note**: Non-critical (degraded status if down)

### Configuration Check
- Validates all required configs exist
- Checks LDAP, Database, JWT settings
- Returns missing configs if any

---

## Implementation Details

### Health Check API

Located in: `backend/app/api/health.py`

**Features**:
- Async/await for non-blocking checks
- Comprehensive error handling
- Configurable check intervals
- Timestamp tracking
- Service uptime calculation

### Integration

- Registered as root router in `main.py`
- No API prefix (available at `/health`, not `/api/health`)
- Included in OpenAPI documentation
- Production-ready code

---

## Best Practices

### Kubernetes Configuration
```yaml
# Startup probe allows 5 minutes for initialization
startupProbe:
  failureThreshold: 30  # 30 × 10s = 5 minutes
  periodSeconds: 10

# Liveness probe checks every 10 seconds
livenessProbe:
  periodSeconds: 10
  failureThreshold: 3   # Restart after 30 seconds of failure

# Readiness probe checks every 5 seconds
readinessProbe:
  periodSeconds: 5
  failureThreshold: 3   # Remove from load balancer after 15 seconds of failure
```

### Monitoring
- Set up alerts for `/health/ready` returning 503
- Track uptime from `/health/live` responses
- Use `/health/detailed` for troubleshooting

### Troubleshooting
- Check logs if `/health/detailed` shows failures
- Verify database connectivity independently
- Check LDAP server if degraded status persists

---

## Testing Health Endpoints

### Using curl

```bash
# Basic health
curl http://localhost:8000/health

# Liveness probe
curl http://localhost:8000/health/live

# Readiness probe
curl http://localhost:8000/health/ready

# Startup probe
curl http://localhost:8000/health/startup

# Detailed report
curl http://localhost:8000/health/detailed

# With headers
curl -v http://localhost:8000/health/ready
```

### Using docker-compose

```bash
# Check container health
docker ps --format "table {{.Names}}\t{{.Status}}"

# View health logs
docker inspect --format='{{json .State.Health}}' container_name | jq

# Manual health check
docker exec container_name curl -f http://localhost:8000/health
```

---

## Troubleshooting

### `/health/ready` returning 503

Check the response for specific failures:

```bash
curl http://localhost:8000/health/ready | jq '.checks'
```

Common issues:
- **Database**: Check PostgreSQL is running and accessible
- **LDAP**: Check LDAP server connectivity (non-critical)
- **Config**: Check environment variables are set correctly

### Service not becoming ready

1. Check startup probe: `/health/startup`
2. Verify all dependencies are accessible
3. Check application logs for initialization errors
4. Increase startup probe `failureThreshold` if needed

### Frequent liveness probe failures

- Increase `periodSeconds` if resource-constrained
- Check application logs for crashes
- Verify database/LDAP connectivity is stable

---

## Future Enhancements

- [ ] Metrics export for Prometheus
- [ ] Custom check plugins
- [ ] Dependency-specific timeout configuration
- [ ] Health history tracking
- [ ] Automated recovery actions

---

**Version**: 2.2.0  
**Status**: Production Ready ✅  
**Last Updated**: 2025-11-06

