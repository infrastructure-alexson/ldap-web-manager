# Podman Setup & Configuration

**Date**: November 6, 2025  
**Status**: Implementation Guide  
**Container Runtime**: Podman (Docker-compatible alternative)

---

## Overview

Podman is a daemonless, open-source container runtime that provides a Docker-compatible experience. LDAP Web Manager container images are fully compatible with Podman.

**Key Differences from Docker**:
- ✅ No daemon process required
- ✅ Native rootless containers
- ✅ Better security model
- ✅ Pod support (multiple containers)
- ✅ Pod.yaml file format

---

## Installation

### macOS

```bash
# Using Homebrew
brew install podman

# Verify installation
podman --version

# Initialize Podman machine (for macOS/Windows)
podman machine init
podman machine start

# Verify connection
podman run hello-world
```

### Linux (Red Hat / CentOS / Rocky)

```bash
# Install Podman
sudo dnf install podman podman-compose

# Verify installation
podman --version

# Start Podman service (if needed)
sudo systemctl start podman
sudo systemctl enable podman

# Verify connection
podman run hello-world
```

### Linux (Debian / Ubuntu)

```bash
# Install Podman
sudo apt-get install podman podman-compose

# Verify installation
podman --version

# Verify connection
podman run hello-world
```

### Windows

```bash
# Using Chocolatey
choco install podman

# Or download installer from:
# https://github.com/containers/podman/releases

# Verify installation
podman --version

# Start machine
podman machine init
podman machine start

# Verify connection
podman run hello-world
```

---

## Rootless Container Support

### Enable Rootless Mode

```bash
# Check if rootless is available
podman info | grep rootless

# Run containers as current user (rootless)
podman run -it quay.io/infrastructure-alexson/ldap-web-manager-backend:latest /bin/sh

# Verify running as regular user
podman ps
podman images
```

### Rootless Benefits

✅ **Security**:
- No root privilege escalation
- Better isolation from host
- Safer for shared systems

✅ **Convenience**:
- No sudo required
- No daemon process
- Better for development

### Rootless Limitations

⚠️ **Port Binding** (< 1024):
```bash
# Cannot bind to ports < 1024 without extra setup
podman run -p 80:8000 backend  # May fail

# Use ports >= 1024
podman run -p 8000:8000 backend  # Works

# Or configure user namespaces for low ports
```

⚠️ **Volume Mounts**:
```bash
# May need to adjust permissions
podman run -v /path/to/data:/data backend

# Or use volume instead
podman volume create mydata
podman run -v mydata:/data backend
```

---

## Pulling Images

### From Quay.io (Recommended for Podman)

```bash
# Pull latest
podman pull quay.io/infrastructure-alexson/ldap-web-manager-backend:latest
podman pull quay.io/infrastructure-alexson/ldap-web-manager-frontend:latest

# Pull specific version
podman pull quay.io/infrastructure-alexson/ldap-web-manager-backend:v2.2.0

# Specify architecture
podman pull --platform linux/arm64 quay.io/infrastructure-alexson/ldap-web-manager-backend:latest
```

### From Docker Hub

```bash
# Pull latest
podman pull infrastructure-alexson/ldap-web-manager-backend:latest

# With full registry
podman pull docker.io/infrastructure-alexson/ldap-web-manager-backend:latest
```

### From GitHub Container Registry

```bash
# Requires authentication
podman login ghcr.io

# Pull image
podman pull ghcr.io/infrastructure-alexson/ldap-web-manager-backend:latest
```

---

## Running Containers

### Basic Container

```bash
# Run backend container
podman run -d \
  --name ldap-backend \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:pass@localhost:5432/ldap_manager" \
  -e REDIS_URL="redis://localhost:6379/0" \
  quay.io/infrastructure-alexson/ldap-web-manager-backend:latest

# Run frontend container
podman run -d \
  --name ldap-frontend \
  -p 8080:8080 \
  quay.io/infrastructure-alexson/ldap-web-manager-frontend:latest

# Check running containers
podman ps

# Check container logs
podman logs ldap-backend
podman logs -f ldap-frontend

# Stop containers
podman stop ldap-backend ldap-frontend

# Remove containers
podman rm ldap-backend ldap-frontend
```

### Using Pods (Recommended)

```bash
# Create a pod for the application
podman pod create \
  --name ldap-web-manager \
  -p 8000:8000 \
  -p 8080:8080

# Run backend in pod
podman run -d \
  --pod ldap-web-manager \
  --name backend \
  -e DATABASE_URL="postgresql://user:pass@db:5432/ldap_manager" \
  -e REDIS_URL="redis://localhost:6379/0" \
  quay.io/infrastructure-alexson/ldap-web-manager-backend:latest

# Run frontend in pod
podman run -d \
  --pod ldap-web-manager \
  --name frontend \
  quay.io/infrastructure-alexson/ldap-web-manager-frontend:latest

# Check pod status
podman pod ps

# Check containers in pod
podman ps --pod

# Stop pod (stops all containers)
podman pod stop ldap-web-manager

# Remove pod
podman pod rm ldap-web-manager
```

### With Persistent Volumes

```bash
# Create volumes
podman volume create pg-data
podman volume create redis-data
podman volume create app-logs

# Run with volumes
podman run -d \
  --name ldap-backend \
  -v pg-data:/var/lib/postgresql/data \
  -v redis-data:/var/lib/redis \
  -v app-logs:/app/logs \
  -p 8000:8000 \
  quay.io/infrastructure-alexson/ldap-web-manager-backend:latest

# List volumes
podman volume ls

# Inspect volume
podman volume inspect pg-data

# Backup volume
podman run --rm \
  -v pg-data:/data \
  -v /tmp:/backup \
  quay.io/infrastructure-alexson/ldap-web-manager-backend:latest \
  tar czf /backup/pg-data.tar.gz /data
```

---

## Podman Compose (Multi-Container)

### Setup

```bash
# Install podman-compose
sudo dnf install podman-compose    # Red Hat/CentOS
sudo apt install podman-compose    # Debian/Ubuntu
brew install podman-compose        # macOS

# Or via pip
pip install podman-compose
```

### Using docker-compose.yml with Podman

```bash
# Convert docker-compose.yml to work with podman
# (Most docker-compose files work directly with podman)

# Start services
podman-compose up -d

# Stop services
podman-compose down

# View logs
podman-compose logs -f

# Scale service
podman-compose up -d --scale backend=3
```

### Podman Compose Example

```yaml
# podman-compose.yml (same as docker-compose.yml)
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ldap_manager
      POSTGRES_USER: ldap_manager
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ldap_manager"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    image: quay.io/infrastructure-alexson/ldap-web-manager-backend:latest
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://ldap_manager:${DB_PASSWORD}@postgres:5432/ldap_manager
      REDIS_URL: redis://redis:6379/0
    ports:
      - "8000:8000"
    volumes:
      - ./config:/app/config:ro

  frontend:
    image: quay.io/infrastructure-alexson/ldap-web-manager-frontend:latest
    depends_on:
      - backend
    ports:
      - "8080:80"
    volumes:
      - ./nginx-certs:/etc/nginx/certs:ro

volumes:
  postgres_data:
  redis_data:
```

### Using with Podman

```bash
# Use same commands
podman-compose -f podman-compose.yml up -d
podman-compose -f podman-compose.yml down

# Some differences in networking (pods handle this)
```

---

## Pod Definition Files

### Create Pod Definition (pod.yaml)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ldap-web-manager
spec:
  restartPolicy: Always
  containers:
  - name: backend
    image: quay.io/infrastructure-alexson/ldap-web-manager-backend:latest
    ports:
    - containerPort: 8000
    env:
    - name: DATABASE_URL
      value: "postgresql://ldap_manager:password@postgres:5432/ldap_manager"
    - name: REDIS_URL
      value: "redis://redis:6379/0"
    volumeMounts:
    - name: config
      mountPath: /app/config
      readOnly: true

  - name: frontend
    image: quay.io/infrastructure-alexson/ldap-web-manager-frontend:latest
    ports:
    - containerPort: 8080
    volumeMounts:
    - name: nginx-certs
      mountPath: /etc/nginx/certs
      readOnly: true

  volumes:
  - name: config
    hostPath:
      path: /etc/ldap-web-manager/config
      type: Directory
  - name: nginx-certs
    hostPath:
      path: /etc/nginx/certs
      type: Directory
```

### Run Pod from Definition

```bash
# Create pod from definition
podman play kube pod.yaml

# Remove pod created from definition
podman play kube --down pod.yaml
```

---

## Systemd Integration

### Create Systemd Service

```ini
# /etc/systemd/user/ldap-web-manager.service
[Unit]
Description=LDAP Web Manager Pod
Wants=network-online.target
After=network-online.target

[Service]
Type=exec
Environment="PODMAN_SYSTEMD_UNIT=%n"
WorkingDirectory=%h/ldap-web-manager
ExecStart=/usr/bin/podman run \
  --rm \
  --name=ldap-web-manager \
  -p 8000:8000 \
  -p 8080:8080 \
  quay.io/infrastructure-alexson/ldap-web-manager-backend:latest

ExecStop=/usr/bin/podman stop ldap-web-manager
Restart=on-failure
RestartSec=30

[Install]
WantedBy=default.target
```

### Enable Service

```bash
# Install service file
mkdir -p ~/.config/systemd/user
cp ldap-web-manager.service ~/.config/systemd/user/

# Reload systemd
systemctl --user daemon-reload

# Enable service
systemctl --user enable ldap-web-manager.service

# Start service
systemctl --user start ldap-web-manager.service

# Check status
systemctl --user status ldap-web-manager.service

# View logs
journalctl --user -u ldap-web-manager.service -f
```

---

## Networking

### Container-to-Container Communication

```bash
# Create network
podman network create ldap-network

# Run containers on network
podman run -d \
  --name backend \
  --network ldap-network \
  backend:latest

podman run -d \
  --name frontend \
  --network ldap-network \
  frontend:latest

# Containers can reach each other by name
# backend → frontend via hostname "frontend"
```

### Port Mapping

```bash
# Map single port
podman run -p 8000:8000 backend

# Map multiple ports
podman run -p 8000:8000 -p 8443:8443 backend

# Map to specific interface
podman run -p 127.0.0.1:8000:8000 backend

# Map random port
podman run -p 8000 backend  # Maps to random port on host
```

### DNS Configuration

```bash
# Use host DNS
podman run --dns host backend

# Use custom DNS
podman run --dns 8.8.8.8 backend

# For pod
podman pod create --dns 8.8.8.8 my-pod
```

---

## Security & Permissions

### SELinux Integration

```bash
# On systems with SELinux enabled
# Use :z or :Z flags for volumes

# :z - shared volume
podman run -v /path:/data:z backend

# :Z - private volume
podman run -v /path:/data:Z backend
```

### User Namespace Mapping

```bash
# For rootless with volume permission issues
podman run --userns=keep-id \
  -v /path/to/data:/data \
  backend

# Or adjust host permissions
chmod 777 /path/to/data
```

### Capabilities

```bash
# Drop unnecessary capabilities
podman run --cap-drop=ALL \
  --cap-add=NET_BIND_SERVICE \
  backend

# View container capabilities
podman inspect container-id | grep CapAdd
```

---

## Troubleshooting

### Image Not Found

```bash
# Error: image not found
# Solution: Ensure image is pulled first
podman pull quay.io/infrastructure-alexson/ldap-web-manager-backend:latest

# Check available images
podman images

# Search for image
podman search ldap-web-manager
```

### Cannot Connect to Container

```bash
# Check if container is running
podman ps

# View container logs
podman logs container-id

# Inspect container
podman inspect container-id

# Check port mappings
podman port container-id
```

### Permission Denied (Rootless)

```bash
# Problem: Cannot bind to port < 1024
# Solution: Use port >= 1024 or configure user namespaces

# Or configure sysctl (on host, requires privilege)
echo "net.ipv4.ip_unprivileged_port_start=80" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### Volume Mount Issues

```bash
# Problem: Cannot access volume data
# Solution: Check permissions

# Adjust volume permissions
podman volume inspect myvolume
# Check host path permissions

# Or use podman volume directly instead of host mounts
podman volume create mydata
podman run -v mydata:/data backend
```

---

## Best Practices

✅ **DO**:
- Use official images from Quay.io
- Use specific version tags in production
- Use pods for multi-container applications
- Enable health checks
- Use volumes for persistence
- Run as non-root user
- Set resource limits

❌ **DON'T**:
- Use latest tag in production
- Run containers as root
- Mount entire /var/lib
- Expose unnecessary ports
- Store secrets in environment variables
- Mix Docker and Podman on same system
- Ignore security scanning

---

## Comparison: Podman vs Docker

| Feature | Podman | Docker |
|---------|--------|--------|
| **Daemon** | Daemonless | Requires daemon |
| **Rootless** | Native support | Limited |
| **Pods** | Full support | None |
| **Docker CLI** | Compatible | Native |
| **Compose** | podman-compose | docker-compose |
| **Security** | Better isolation | Standard |
| **Performance** | Lower overhead | Higher overhead |
| **Community** | Growing | Large |

---

## References

- [Podman Documentation](https://podman.io/)
- [Podman Installation](https://podman.io/docs/installation)
- [Podman Compose](https://github.com/containers/podman-compose)
- [Podman Rootless](https://wiki.podman.io/display/podman/Podman+and+user+namespaces)
- [Container Networking](https://podman.io/docs/networking)

---

**Last Updated**: November 6, 2025  
**Status**: Complete Implementation Guide  
**Next**: Issue #45 - Container Deployment Meta

