# PostgreSQL Setup Guide for LDAP Web Manager

**Version**: 1.0  
**Last Updated**: 2025-11-06  
**Component**: IPAM & Audit Logging Database Backend

---

## Overview

This guide covers setting up PostgreSQL for LDAP Web Manager's production database backend. PostgreSQL replaces SQLite for:

- **IPAM** (IP Address Management) - IP pools, allocations, tracking
- **Audit Logging** - All LDAP, DNS, DHCP, and IPAM operations
- **Session Management** (optional) - User sessions with Redis

---

## Prerequisites

- PostgreSQL 13 or later
- Python 3.9+
- LDAP Web Manager v2.1.0+
- Network connectivity to PostgreSQL server
- Administrator access to create databases

---

## Installation

### Option 1: PostgreSQL Server (Recommended)

**On Rocky Linux 8**:

```bash
# Install PostgreSQL repository
sudo dnf install https://download.postgresql.org/pub/repos/yum/reporpms/EL-8-x86_64/pgdg-redhat-repo-latest.noarch.rpm

# Install PostgreSQL server
sudo dnf install postgresql15-server postgresql15-contrib

# Initialize database cluster
sudo /usr/pgsql-15/bin/postgresql-15-setup initdb

# Enable and start PostgreSQL
sudo systemctl enable postgresql-15
sudo systemctl start postgresql-15

# Verify installation
sudo -u postgres psql --version
```

### Option 2: Docker Container

**Using Podman**:

```bash
podman run -d \
  --name ldap-web-manager-db \
  -e POSTGRES_USER=ldap_manager \
  -e POSTGRES_PASSWORD=your_secure_password \
  -e POSTGRES_DB=ldap_manager \
  -p 5432:5432 \
  -v pgdata:/var/lib/postgresql/data \
  postgres:15-alpine

# Verify container is running
podman logs ldap-web-manager-db
```

---

## Database Setup

### Create Database and User

```bash
# Connect to PostgreSQL as admin
sudo -u postgres psql

# Create application user
CREATE USER ldap_manager WITH PASSWORD 'your_secure_password' CREATEDB;

# Create database
CREATE DATABASE ldap_manager OWNER ldap_manager;

# Enable required extensions
\c ldap_manager
CREATE EXTENSION IF NOT EXISTS citext;        -- Case-insensitive text
CREATE EXTENSION IF NOT EXISTS uuid-ossp;     -- UUID generation
CREATE EXTENSION IF NOT EXISTS hstore;        -- Key-value storage

# Set connection limit
ALTER USER ldap_manager CONNECTION LIMIT 100;

# Exit psql
\q
```

### Configure PostgreSQL for Production

Edit `/etc/postgresql/15/main/postgresql.conf`:

```ini
# Connection settings
max_connections = 200
superuser_reserved_connections = 10
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# WAL and checkpointing
wal_buffers = 16MB
checkpoint_completion_target = 0.9
wal_compression = on

# Query planning
random_page_cost = 1.1
effective_io_concurrency = 200

# Logging
log_min_duration_statement = 1000  # Log queries > 1 second
log_connections = on
log_disconnections = on
log_statement = 'mod'              # Log modifying statements

# Replication (if needed)
wal_level = replica
```

Edit `/etc/postgresql/15/main/pg_hba.conf`:

```
# IPv4 local connections
host    ldap_manager    ldap_manager    127.0.0.1/32            md5
host    ldap_manager    ldap_manager    192.168.1.0/24          md5

# IPv6 local connections
host    ldap_manager    ldap_manager    ::1/128                 md5
```

Reload configuration:

```bash
sudo systemctl reload postgresql-15
```

---

## Application Configuration

### Set Environment Variables

Create `.env` file in project root:

```bash
# PostgreSQL Database URL
# Format: postgresql+asyncpg://user:password@host:port/database
DATABASE_URL=postgresql+asyncpg://ldap_manager:your_secure_password@localhost:5432/ldap_manager

# Connection pool settings
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600
```

Or update `config/app-config.yaml`:

```yaml
database:
  url: postgresql+asyncpg://ldap_manager:your_secure_password@localhost:5432/ldap_manager
  pool_size: 20
  max_overflow: 40
  pool_timeout: 30
  pool_recycle: 3600  # Recycle connections after 1 hour
```

### Update requirements.txt

The following dependencies are required (already in `backend/requirements.txt`):

```
sqlalchemy==2.0.25
asyncpg==0.29.0
psycopg2-binary==2.9.9
alembic==1.13.1
```

---

## Database Migrations

### Run Migrations

Initialize database schema:

```bash
cd backend

# Run all pending migrations
python -m alembic upgrade head

# Verify current revision
python -m alembic current

# View migration history
python -m alembic history
```

Or use the provided migration script:

```bash
# From project root
./backend/scripts/migrate.sh upgrade head

# View migration history
./backend/scripts/migrate.sh history
```

### Create New Migrations

```bash
cd backend

# Auto-generate migration for model changes
python -m alembic revision --autogenerate -m "Add new table"

# Or use the script
./scripts/migrate.sh revision -m "Add new table"

# Review generated migration file in alembic/versions/
# Then run it
python -m alembic upgrade head
```

---

## Data Migration (SQLite to PostgreSQL)

If migrating from an existing SQLite database:

### 1. Export SQLite Data

```bash
# Backup existing SQLite database
cp data/ipam.db data/ipam.db.backup
```

### 2. Run Migration Script

```bash
cd backend

# Run migration
python scripts/migrate-from-sqlite.py --sqlite-db /path/to/ipam.db

# With debug logging
python scripts/migrate-from-sqlite.py --sqlite-db /path/to/ipam.db --debug
```

### 3. Verify Migration

```bash
# Connect to PostgreSQL
psql -U ldap_manager -d ldap_manager

# Check data was migrated
SELECT COUNT(*) FROM ip_pools;
SELECT COUNT(*) FROM ip_allocations;
SELECT COUNT(*) FROM audit_logs;

# View audit log for migration
SELECT * FROM audit_logs WHERE resource_type = 'migration' ORDER BY created_at DESC LIMIT 1;

\q
```

---

## Backup and Recovery

### Automated Backups

Create cron job for daily backups:

```bash
# Create backup directory
sudo mkdir -p /var/backups/postgresql
sudo chown postgres:postgres /var/backups/postgresql

# Edit crontab
sudo crontab -e -u postgres

# Add daily backup at 2 AM
0 2 * * * /usr/pgsql-15/bin/pg_dump -d ldap_manager -F c -f /var/backups/postgresql/ldap_manager_$(date +\%Y\%m\%d).dump

# Verify backup
ls -lh /var/backups/postgresql/
```

### Manual Backup

```bash
# Full database dump
sudo -u postgres pg_dump -d ldap_manager -F c -f ldap_manager_backup.dump

# Backup size
ls -lh ldap_manager_backup.dump
```

### Restore from Backup

```bash
# Restore database (will overwrite existing data)
sudo -u postgres pg_restore -d ldap_manager -C ldap_manager_backup.dump

# Verify restoration
sudo -u postgres psql -d ldap_manager -c "SELECT COUNT(*) FROM ip_allocations;"
```

---

## Monitoring

### Connection Status

```bash
# Check active connections
psql -U ldap_manager -d ldap_manager -c "\
  SELECT datname, count(*) as num_connections \
  FROM pg_stat_activity \
  GROUP BY datname;"

# Check connection limits
psql -U postgres -c "SELECT usename, usecanlogin, useconnlimit FROM pg_user WHERE usename='ldap_manager';"
```

### Database Size

```bash
# Check database size
psql -U ldap_manager -d ldap_manager -c "\
  SELECT pg_size_pretty(pg_database_size('ldap_manager'));"

# Check table sizes
psql -U ldap_manager -d ldap_manager -c "\
  SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) \
  FROM pg_tables \
  WHERE schemaname NOT IN ('pg_catalog', 'information_schema') \
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

### Query Performance

```bash
# Check slow queries (requires log_min_duration_statement set)
tail -f /var/log/postgresql/postgresql-15-main.log | grep duration

# Analyze slow queries
psql -U ldap_manager -d ldap_manager -c "EXPLAIN ANALYZE SELECT * FROM ip_allocations WHERE status='allocated';"
```

### Maintenance

```bash
# Vacuum (remove dead rows)
psql -U ldap_manager -d ldap_manager -c "VACUUM ANALYZE;"

# Reindex tables
psql -U ldap_manager -d ldap_manager -c "REINDEX DATABASE ldap_manager;"

# Check index usage
psql -U ldap_manager -d ldap_manager -c "\
  SELECT schemaname, tablename, indexname \
  FROM pg_indexes \
  WHERE schemaname NOT IN ('pg_catalog', 'information_schema');"
```

---

## Troubleshooting

### Connection Refused

**Problem**: `psycopg2.OperationalError: could not connect to server`

**Solutions**:
```bash
# 1. Verify PostgreSQL is running
sudo systemctl status postgresql-15

# 2. Check if listening on correct port
sudo ss -tlnp | grep 5432

# 3. Verify firewall allows connections
sudo firewall-cmd --add-service=postgresql --permanent
sudo firewall-cmd --reload

# 4. Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

### Authentication Failed

**Problem**: `FATAL: password authentication failed`

**Solutions**:
```bash
# 1. Verify DATABASE_URL is correct
echo $DATABASE_URL

# 2. Reset user password
sudo -u postgres psql -c "ALTER USER ldap_manager WITH PASSWORD 'new_password';"

# 3. Check pg_hba.conf has correct authentication method
sudo grep -A 5 "ldap_manager" /etc/postgresql/15/main/pg_hba.conf

# 4. Reload PostgreSQL config
sudo systemctl reload postgresql-15
```

### Connection Pool Exhausted

**Problem**: `asyncpg.TooManyConnectionsError`

**Solutions**:
```bash
# 1. Check connection settings in .env
grep DATABASE_POOL /path/to/.env

# 2. Monitor active connections
psql -U ldap_manager -d ldap_manager -c "\
  SELECT count(*) FROM pg_stat_activity WHERE datname='ldap_manager';"

# 3. Increase pool size if needed
# Edit .env: DATABASE_POOL_SIZE=50

# 4. Kill stuck connections (use with caution)
sudo -u postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='ldap_manager' AND pid <> pg_backend_pid();"
```

### Audit Logs Growing Too Large

**Problem**: `relation "audit_logs" does not exist` or table too large

**Solutions**:
```bash
# Check table size
psql -U ldap_manager -d ldap_manager -c "\
  SELECT pg_size_pretty(pg_total_relation_size('audit_logs'));"

# Archive and clean old logs (older than 1 year)
psql -U ldap_manager -d ldap_manager -c "\
  DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '365 days';"

# Vacuum and reindex
psql -U ldap_manager -d ldap_manager -c "VACUUM ANALYZE audit_logs; REINDEX TABLE audit_logs;"
```

---

## Health Checks

### Application Health Check

```bash
# Check database status from application
curl http://localhost:8000/api/health | jq .

# Expected output:
# {
#   "status": "healthy",
#   "version": "2.1.0",
#   "services": {
#     "api": "up",
#     "database": "up",
#     "ldap": "checking"
#   }
# }
```

### Database Connection Test

```bash
# From application container/host
python -c "
from app.config import get_config
from app.db.base import get_database
import asyncio

async def test():
    db = await get_database()
    if await db.health_check():
        print('Database connection: OK')
    else:
        print('Database connection: FAILED')

asyncio.run(test())
"
```

---

## Performance Tuning

### Index Optimization

```bash
# Analyze index usage
psql -U ldap_manager -d ldap_manager <<EOF
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan as index_scans,
  idx_tup_read as tuples_read,
  idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY indexname;
EOF

# Drop unused indexes (with caution)
# psql -U ldap_manager -d ldap_manager -c "DROP INDEX index_name;"
```

### Query Optimization

```bash
# Find slow queries in logs
sudo grep -i "duration:" /var/log/postgresql/postgresql-15-main.log | sort -t: -k3 -rn | head -20

# Explain query plan
psql -U ldap_manager -d ldap_manager <<EOF
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM ip_allocations 
WHERE pool_id = 1 AND status = 'allocated'
ORDER BY ip_address;
EOF
```

### Connection Pooling

Recommended connection pool settings for different deployment scenarios:

**Development**:
```
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10
```

**Production (2-4 workers)**:
```
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
```

**High-load (8+ workers)**:
```
DATABASE_POOL_SIZE=50
DATABASE_MAX_OVERFLOW=100
```

---

## Security

### User Permissions

```bash
# Create read-only user (for reporting)
sudo -u postgres psql -d ldap_manager <<EOF
CREATE USER ldap_manager_readonly WITH PASSWORD 'readonly_password';
GRANT CONNECT ON DATABASE ldap_manager TO ldap_manager_readonly;
GRANT USAGE ON SCHEMA public TO ldap_manager_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ldap_manager_readonly;
EOF
```

### Network Security

```bash
# Restrict connections to localhost only
sudo tee -a /etc/postgresql/15/main/pg_hba.conf > /dev/null <<EOF
# Only allow connections from application server
host    ldap_manager    ldap_manager    192.168.1.0/24          md5
host    ldap_manager    ldap_manager    127.0.0.1/32            md5
EOF

sudo systemctl reload postgresql-15
```

### SSL/TLS Configuration

```bash
# Generate self-signed certificate
sudo -u postgres mkdir -p /etc/postgresql/15/main/certs
cd /etc/postgresql/15/main/certs
sudo openssl req -new -x509 -days 365 -nodes -out server.crt -keyout server.key
sudo chmod 600 server.key
sudo chown postgres:postgres server.*

# Enable SSL in postgresql.conf
echo "ssl = on" | sudo tee -a /etc/postgresql/15/main/postgresql.conf

# Update connection string to use SSL
# DATABASE_URL=postgresql+asyncpg://ldap_manager:password@host:5432/ldap_manager?ssl=require
```

---

## Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy PostgreSQL Guide](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/current/)

---

**PostgreSQL Setup Guide**  
**Version**: 1.0  
**Last Updated**: 2025-11-06  
**Repository**: https://github.com/infrastructure-alexson/ldap-web-manager


