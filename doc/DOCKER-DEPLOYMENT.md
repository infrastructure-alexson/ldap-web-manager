# Docker Deployment Guide

**Version**: 2.2.0  
**Status**: Production Ready ✅  
**Last Updated**: 2025-11-06

---

## Overview

This guide covers deploying LDAP Web Manager using Docker and Docker Compose for both development and production environments.

---

## Prerequisites

### Required
- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum
- 10GB disk space

### Optional (for monitoring)
- Prometheus 2.30+ (included in docker-compose)
- Grafana 8.0+ (included in docker-compose)

---

## Quick Start - Development

### 1. Clone and Setup

```bash
git clone https://github.com/infrastructure-alexson/ldap-web-manager.git
cd ldap-web-manager

# Copy environment file
cp .env.example .env
# Edit .env with your values
nano .env
```

### 2. Build and Start

```bash
# Build the image
docker build -t ldap-web-manager:dev .

# Start all services (development)
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f app
```

### 3. Test Health Checks

```bash
# Basic health check
curl http://localhost:8000/health

# Readiness probe
curl http://localhost:8000/health/ready

# Detailed status
curl http://localhost:8000/health/detailed
```

### 4. Access Application

- **Frontend**: http://localhost:8080
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## Production Deployment

### 1. Environment Configuration

Create `.env` file with production values:

```bash
# Database
DB_PASSWORD=your_secure_password
DB_NAME=ldap_manager_prod

# Redis
REDIS_PASSWORD=your_redis_secure_password

# LDAP
LDAP_ADMIN_PASSWORD=your_ldap_admin_password
LDAP_BASE_DN=dc=example,dc=com

# Security
JWT_SECRET=your_very_long_secure_jwt_secret_minimum_32_characters
SECURE_SSL_REDIRECT=true

# Application
ALLOWED_HOSTS=ldap-manager.example.com,api.example.com
ENVIRONMENT=production
```

### 2. Build Production Image

```bash
# Build with version tag
docker build -t ldap-web-manager:2.2.0 .

# Tag for registry
docker tag ldap-web-manager:2.2.0 your-registry/ldap-web-manager:2.2.0

# Push to registry
docker push your-registry/ldap-web-manager:2.2.0
```

### 3. Start Production Environment

```bash
# Start main services
docker-compose -f docker-compose-prod.yml up -d

# Start with monitoring (optional)
docker-compose -f docker-compose-prod.yml --profile monitoring up -d

# Check services
docker-compose -f docker-compose-prod.yml ps

# View logs
docker-compose -f docker-compose-prod.yml logs -f app
```

### 4. Database Setup

```bash
# Run migrations
docker-compose -f docker-compose-prod.yml exec app \
  alembic upgrade head

# Verify database
docker-compose -f docker-compose-prod.yml exec postgres \
  psql -U ldap_user -d ldap_manager -c "SELECT version();"
```

### 5. Verify Health

```bash
# Check readiness probe
curl -I http://localhost:8000/health/ready
# Should return: HTTP/1.1 200 OK

# Check all services
docker-compose -f docker-compose-prod.yml ps
# All should show "healthy" status
```

---

## Configuration Files

### docker-compose.yml (Development)
- Development environment setup
- Mock LDAP server (openldap)
- Single database instance
- Volume mounts for live code editing

### docker-compose-prod.yml (Production)
- Production-grade configuration
- 389 Directory Service LDAP
- Resource limits and reservations
- Security hardening
- Persistent volumes
- Optional monitoring services
- Health checks on all services

---

## Environment Variables

### Database Variables
```env
DB_NAME=ldap_manager              # Database name
DB_USER=ldap_user                 # Database user
DB_PASSWORD=secure_password       # Database password
DB_HOST=postgres                  # Database host
DB_PORT=5432                      # Database port
```

### Redis Variables
```env
REDIS_PASSWORD=secure_password    # Redis password
REDIS_HOST=redis                  # Redis host
REDIS_PORT=6379                   # Redis port
```

### LDAP Variables
```env
LDAP_SERVER=ldap://ldap:389       # LDAP server URL
LDAP_BASE_DN=dc=example,dc=com    # LDAP base DN
LDAP_ADMIN_DN=cn=Directory Manager
LDAP_ADMIN_PASSWORD=secure_password
```

### Security Variables
```env
JWT_SECRET=very_long_secure_key   # JWT signing key (min 32 chars)
JWT_ALGORITHM=HS256               # JWT algorithm
JWT_EXPIRATION=3600               # Token expiration (seconds)
```

### Application Variables
```env
ENVIRONMENT=production            # Environment (development/production)
LOG_LEVEL=info                    # Logging level
WORKERS=4                         # Number of workers
ALLOWED_HOSTS=localhost,127.0.0.1
SECURE_SSL_REDIRECT=true
SESSION_COOKIE_SECURE=true
```

---

## Monitoring (Optional)

### Enable Monitoring Profile

```bash
docker-compose -f docker-compose-prod.yml --profile monitoring up -d
```

### Access Monitoring Services

- **Prometheus**: http://localhost:9090
  - Metrics: http://localhost:9090/metrics
  - Targets: http://localhost:9090/targets

- **Grafana**: http://localhost:3000
  - Default username: admin
  - Default password: (from GRAFANA_PASSWORD env var)

### Prometheus Configuration

Update `config/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'ldap-web-manager'
    static_configs:
      - targets: ['app:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboards

Available dashboards:
- Application Metrics
- Database Performance
- Service Health
- Request Latency

---

## Logging

### View Logs

```bash
# All services
docker-compose -f docker-compose-prod.yml logs

# Specific service
docker-compose -f docker-compose-prod.yml logs app

# Follow logs
docker-compose -f docker-compose-prod.yml logs -f app

# Last 100 lines
docker-compose -f docker-compose-prod.yml logs --tail=100 app
```

### Log Configuration

- **Driver**: json-file
- **Max Size**: 100MB per file
- **Max Files**: 10 files
- **Location**: `/var/lib/docker/containers/*/`

### Log Aggregation

For centralized logging, configure your log agent:

```yaml
# Example Filebeat configuration
filebeat.inputs:
  - type: container
    enabled: true
    paths:
      - '/var/lib/docker/containers/*/*.log'
```

---

## Persistent Data

### Volumes

```
postgres_data_prod:    PostgreSQL database files
redis_data_prod:       Redis persistence
ldap_data_prod:        LDAP directory data
prometheus_data:       Metrics storage
grafana_data:          Grafana dashboards and settings
```

### Backup Strategy

```bash
# Backup PostgreSQL
docker-compose -f docker-compose-prod.yml exec postgres \
  pg_dump -U ldap_user ldap_manager > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup LDAP
docker-compose -f docker-compose-prod.yml exec ldap \
  dsctl ldap-prod db2ldif /tmp/ldap_backup.ldif

# Backup volumes
docker run --rm -v postgres_data_prod:/data \
  -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .
```

---

## Troubleshooting

### Service Won't Start

1. Check logs:
```bash
docker-compose -f docker-compose-prod.yml logs app
```

2. Verify environment variables:
```bash
docker-compose -f docker-compose-prod.yml config
```

3. Check ports are available:
```bash
lsof -i :8000
lsof -i :5432
```

### Database Connection Error

```bash
# Test database connection
docker-compose -f docker-compose-prod.yml exec postgres \
  psql -U ldap_user -d ldap_manager -c "SELECT 1;"

# Check database logs
docker-compose -f docker-compose-prod.yml logs postgres
```

### Health Check Failing

```bash
# Check readiness
docker-compose -f docker-compose-prod.yml exec app \
  curl http://localhost:8000/health/ready

# Check detailed status
docker-compose -f docker-compose-prod.yml exec app \
  curl http://localhost:8000/health/detailed
```

### Container Keeps Restarting

```bash
# Check container logs before restart
docker-compose -f docker-compose-prod.yml logs --tail=50 app

# Disable restart policy temporarily
docker update --restart=no container_name

# Check resource limits
docker stats

# Increase memory if needed
# Update docker-compose-prod.yml deploy.resources
```

---

## Performance Tuning

### Database Optimization

Update PostgreSQL parameters in `docker-compose-prod.yml`:

```yaml
environment:
  POSTGRES_INITDB_ARGS: >
    -c max_connections=200
    -c shared_buffers=512MB
    -c effective_cache_size=1GB
    -c maintenance_work_mem=128MB
    -c checkpoint_completion_target=0.9
    -c wal_buffers=16MB
    -c default_statistics_target=100
    -c random_page_cost=1.1
```

### Redis Optimization

```yaml
command: >
  redis-server
  --maxmemory 512mb
  --maxmemory-policy allkeys-lru
  --save 900 1
  --save 300 10
```

### Application Workers

Increase workers based on CPU:

```yaml
environment:
  WORKERS: 8  # For 4+ CPU cores
```

---

## Security Best Practices

### Network Isolation

- Use dedicated Docker network (included)
- Restrict external access with firewall
- Use VPN for remote access

### Environment Variables

- Store sensitive values in `.env` file
- Don't commit `.env` to version control
- Use Docker secrets for sensitive data in production

### Container Security

- Run as non-root user (included in Dockerfile)
- Use read-only root filesystem where possible (included)
- Drop unnecessary capabilities (included)
- Enable security scanning

### SSL/TLS

Set up SSL termination:
- Use reverse proxy (Nginx, HAProxy)
- Configure HTTPS on reverse proxy
- Set `SECURE_SSL_REDIRECT=true`

---

## Upgrade Procedure

### Backup Current Data

```bash
docker-compose -f docker-compose-prod.yml exec postgres \
  pg_dump -U ldap_user ldap_manager > backup_pre_upgrade.sql
```

### Pull New Version

```bash
git pull origin main
docker build -t ldap-web-manager:2.3.0 .
```

### Run Migrations

```bash
docker-compose -f docker-compose-prod.yml exec app \
  alembic upgrade head
```

### Restart Services

```bash
docker-compose -f docker-compose-prod.yml down
docker-compose -f docker-compose-prod.yml up -d
```

### Verify

```bash
docker-compose -f docker-compose-prod.yml ps
docker-compose -f docker-compose-prod.yml exec app \
  curl http://localhost:8000/health/ready
```

---

## Cleanup

### Remove Containers

```bash
docker-compose down
```

### Remove Volumes (WARNING: deletes data!)

```bash
docker-compose down -v
```

### Remove Images

```bash
docker rmi ldap-web-manager:2.2.0
```

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/dockerfile_best-practices/)
- [Health Checks Documentation](./HEALTH-CHECKS.md)
- [Kubernetes Deployment](./KUBERNETES-DEPLOYMENT.md) (Coming in v2.2.0)

---

**Status**: Production Ready ✅  
**Last Updated**: 2025-11-06  
**Version**: 2.2.0

