# GitHub Self-Hosted Runner Setup Guide

## Overview

This guide covers setting up a self-hosted GitHub Actions runner using the `github-action-runner` container image.

**Benefits of Self-Hosted Runners**:
- ✅ Custom hardware/specifications
- ✅ Pre-installed tools and dependencies
- ✅ Persistent cache and storage
- ✅ Lower cost for high-volume workflows
- ✅ Direct access to private networks
- ✅ Podman/Docker support

---

## Prerequisites

### Host System Requirements
- Rocky Linux 8/9, Ubuntu 20.04+, or macOS 11+
- 2+ CPU cores
- 4GB+ RAM
- 10GB+ disk space
- Docker or Podman installed
- Internet connectivity to github.com

### GitHub Requirements
- Organization or personal GitHub account
- Repository admin access
- Personal Access Token or runner registration token

---

## Installation Steps

### Step 1: Create Registration Token

#### For Organization:
1. Go to: `https://github.com/organizations/YOUR-ORG/settings/actions/runners`
2. Click "New self-hosted runner"
3. Select OS and architecture
4. Copy the registration token

#### For Repository:
1. Go to: `https://github.com/YOUR-OWNER/YOUR-REPO/settings/actions/runners`
2. Click "New self-hosted runner"
3. Copy the registration token

**Note**: Token expires after 1 hour, generate new if needed

---

## Running with Podman

### Quick Start

```bash
# Set environment variables
export GITHUB_REPOSITORY="owner/repo"
export RUNNER_TOKEN="your_registration_token_here"
export RUNNER_NAME="my-runner"
export RUNNER_LABELS="podman,linux,amd64"

# Run container
podman run -d \
  --name github-runner \
  -e GITHUB_REPOSITORY="$GITHUB_REPOSITORY" \
  -e RUNNER_TOKEN="$RUNNER_TOKEN" \
  -e RUNNER_NAME="$RUNNER_NAME" \
  -e RUNNER_LABELS="$RUNNER_LABELS" \
  -v /var/run/podman/podman.sock:/var/run/podman/podman.sock \
  -v /opt/runner-work:/home/runner/_work \
  docker.io/salexson/github-action-runner:latest
```

### Full Configuration Example

```bash
#!/bin/bash
# setup-github-runner.sh

# Configuration
GITHUB_REPOSITORY="infrastructure-alexson/ldap-web-manager"
RUNNER_TOKEN="your_token_here"
RUNNER_NAME="podman-runner-01"
RUNNER_LABELS="podman,linux,amd64,ldap-web-manager"
WORK_DIR="/opt/runner-work"
CONFIG_DIR="/opt/runner-config"

# Create directories
mkdir -p "$WORK_DIR" "$CONFIG_DIR"

# Run self-hosted runner
podman run -d \
  --name github-runner \
  --hostname "$RUNNER_NAME" \
  --restart always \
  -e GITHUB_REPOSITORY="$GITHUB_REPOSITORY" \
  -e RUNNER_TOKEN="$RUNNER_TOKEN" \
  -e RUNNER_NAME="$RUNNER_NAME" \
  -e RUNNER_LABELS="$RUNNER_LABELS" \
  -e RUNNER_WORKDIR="$WORK_DIR" \
  -e RUNNER_ALLOW_RUNASROOT=true \
  -v "$CONFIG_DIR:/home/runner/.runner" \
  -v "$WORK_DIR:/home/runner/_work" \
  -v /var/run/podman/podman.sock:/var/run/podman/podman.sock \
  -v /etc/passwd:/etc/passwd:ro \
  -v /etc/group:/etc/group:ro \
  docker.io/salexson/github-action-runner:latest

# Wait for startup
sleep 5

# Check logs
podman logs github-runner
```

---

## Running with Docker

### Docker Installation

```bash
# Rocky Linux 8
sudo dnf install -y docker
sudo systemctl start docker
sudo systemctl enable docker

# Ubuntu
sudo apt-get install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker
```

### Docker Container

```bash
# Set environment variables
export GITHUB_REPOSITORY="owner/repo"
export RUNNER_TOKEN="your_registration_token_here"
export RUNNER_NAME="my-runner"
export RUNNER_LABELS="docker,linux,amd64"

# Run container
docker run -d \
  --name github-runner \
  -e GITHUB_REPOSITORY="$GITHUB_REPOSITORY" \
  -e RUNNER_TOKEN="$RUNNER_TOKEN" \
  -e RUNNER_NAME="$RUNNER_NAME" \
  -e RUNNER_LABELS="$RUNNER_LABELS" \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /opt/runner-work:/home/runner/_work \
  docker.io/salexson/github-action-runner:latest
```

---

## Systemd Service Setup

### Create Service File

Create `/etc/systemd/system/github-runner.service`:

```ini
[Unit]
Description=GitHub Actions Self-Hosted Runner
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/runner
Environment="GITHUB_REPOSITORY=owner/repo"
Environment="RUNNER_TOKEN=your_token_here"
Environment="RUNNER_NAME=runner-01"
Environment="RUNNER_LABELS=podman,linux,amd64"
ExecStart=/usr/bin/podman run --rm \
  --name github-runner \
  -e GITHUB_REPOSITORY=%i \
  -e RUNNER_TOKEN=%E{RUNNER_TOKEN} \
  -e RUNNER_NAME=%E{RUNNER_NAME} \
  -e RUNNER_LABELS=%E{RUNNER_LABELS} \
  -v /var/run/podman/podman.sock:/var/run/podman/podman.sock \
  -v /opt/runner-work:/home/runner/_work \
  docker.io/salexson/github-action-runner:latest
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable on boot
sudo systemctl enable github-runner.service

# Start service
sudo systemctl start github-runner.service

# Check status
sudo systemctl status github-runner.service

# View logs
sudo journalctl -u github-runner.service -f
```

---

## Using with GitHub Actions Workflows

### Workflow Configuration

The included workflow automatically runs on self-hosted runners:

```yaml
name: Build and Push GitHub Action Runner Image

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  workflow_dispatch:

jobs:
  build:
    runs-on: self-hosted  # ← Runs on self-hosted runner
    steps:
      - uses: actions/checkout@v3
      - name: Build image
        run: ./scripts/build-and-push-podman.sh --tag ${{ github.ref_name }}
```

### Label-Based Selection

```yaml
jobs:
  build:
    runs-on: [self-hosted, linux, podman]  # ← Specific runner with labels
    steps:
      - uses: actions/checkout@v3
```

---

## Runner Management

### View Runners

```bash
# List all runners in repository
gh api repos/owner/repo/actions/runners

# List organization runners
gh api orgs/org-name/actions/runners
```

### Remove Runner

```bash
# From container
podman stop github-runner
podman rm github-runner

# From GitHub UI:
# 1. Go to Settings → Actions → Runners
# 2. Click "..." next to runner
# 3. Click "Remove"
```

### Restart Runner

```bash
# Restart container
podman restart github-runner

# Or restart systemd service
sudo systemctl restart github-runner.service
```

---

## Environment Variables

### Required
| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_REPOSITORY` | Repository URL | `owner/repo` |
| `RUNNER_TOKEN` | Registration token | From GitHub settings |

### Optional
| Variable | Default | Description |
|----------|---------|-------------|
| `RUNNER_NAME` | hostname | Custom runner name |
| `RUNNER_LABELS` | `linux` | Comma-separated labels |
| `RUNNER_GROUPS` | `default` | Runner group name |
| `RUNNER_WORKDIR` | `/home/runner/_work` | Working directory |
| `RUNNER_ALLOW_RUNASROOT` | `false` | Allow root execution |

### Example Setup

```bash
cat > /opt/runner.env <<EOF
GITHUB_REPOSITORY=infrastructure-alexson/ldap-web-manager
RUNNER_TOKEN=abc123xyz789
RUNNER_NAME=podman-builder-01
RUNNER_LABELS=podman,linux,amd64,ldap
EOF

podman run -d \
  --name github-runner \
  --env-file /opt/runner.env \
  -v /var/run/podman/podman.sock:/var/run/podman/podman.sock \
  -v /opt/runner-work:/home/runner/_work \
  docker.io/salexson/github-action-runner:latest
```

---

## Volume Mounts

### Essential Mounts

```bash
podman run -d \
  # Podman/Docker socket (for container builds)
  -v /var/run/podman/podman.sock:/var/run/podman/podman.sock \
  # Working directory (persistent workspace)
  -v /opt/runner-work:/home/runner/_work \
  # Runner configuration (persistent state)
  -v /opt/runner-config:/home/runner/.runner \
  docker.io/salexson/github-action-runner:latest
```

### Optional Mounts

```bash
# SSH keys for git operations
-v ~/.ssh:/home/runner/.ssh:ro

# Docker credentials
-v ~/.docker:/home/runner/.docker:ro

# Podman credentials
-v ~/.podman:/home/runner/.podman:ro

# Custom scripts
-v /opt/scripts:/opt/scripts:ro

# Cache directory
-v /opt/runner-cache:/home/runner/.cache
```

---

## Networking

### Port Mapping (if needed)

```bash
podman run -d \
  # SSH access (optional)
  -p 2222:22 \
  # Health check endpoint (optional)
  -p 8080:8080 \
  docker.io/salexson/github-action-runner:latest
```

### Host Network Mode

```bash
podman run -d \
  --network host \
  docker.io/salexson/github-action-runner:latest
```

---

## Security Considerations

### 1. Use Latest Image

```bash
podman pull docker.io/salexson/github-action-runner:latest
```

### 2. Limit Resource Usage

```bash
podman run -d \
  --cpus 2 \
  --memory 4g \
  --memory-swap 4g \
  docker.io/salexson/github-action-runner:latest
```

### 3. Run as Non-Root (when possible)

```bash
podman run -d \
  --user 1000:1000 \
  docker.io/salexson/github-action-runner:latest
```

### 4. Use Read-Only Root Filesystem

```bash
podman run -d \
  --read-only \
  --tmpfs /run \
  --tmpfs /tmp \
  docker.io/salexson/github-action-runner:latest
```

### 5. Network Policies

```bash
# Restrict to specific networks
podman network create runner-network
podman run -d \
  --network runner-network \
  docker.io/salexson/github-action-runner:latest
```

---

## Troubleshooting

### Runner Not Connecting

```bash
# Check logs
podman logs github-runner

# Verify token is valid (expires after 1 hour)
# Generate new token and update container

# Check network connectivity
podman exec github-runner ping github.com
```

### High Resource Usage

```bash
# Check running containers
podman ps

# Limit resources
podman update --cpus 2 --memory 4g github-runner

# Restart with limits
podman stop github-runner
podman rm github-runner
# Run with --cpus and --memory flags
```

### Workflow Fails on Self-Hosted

```bash
# Verify runner has required tools
podman exec github-runner which git
podman exec github-runner which docker
podman exec github-runner which podman

# Check working directory permissions
podman exec github-runner ls -la /home/runner/_work

# Check runner logs
sudo journalctl -u github-runner.service -n 50
```

### Permission Denied Errors

```bash
# Ensure runner user has podman socket access
sudo usermod -aG docker runner
sudo usermod -aG podman runner

# Or run as root (less secure)
RUNNER_ALLOW_RUNASROOT=true
```

---

## Performance Optimization

### 1. Use Persistent Cache

```bash
# Keep build cache between runs
-v /opt/runner-cache:/home/runner/.cache
-v /opt/podman-cache:/var/lib/containers
```

### 2. Pre-Pull Images

```bash
# Pre-download base images
podman pull alpine:latest
podman pull rockylinux:8
```

### 3. Increase Resources

```bash
podman run -d \
  --cpus 4 \
  --memory 8g \
  docker.io/salexson/github-action-runner:latest
```

---

## Scaling to Multiple Runners

### Docker Compose

```yaml
version: '3.9'

services:
  runner-01:
    image: docker.io/salexson/github-action-runner:latest
    container_name: github-runner-01
    environment:
      GITHUB_REPOSITORY: owner/repo
      RUNNER_TOKEN: ${RUNNER_TOKEN_1}
      RUNNER_NAME: runner-01
      RUNNER_LABELS: podman,linux,amd64
    volumes:
      - /var/run/podman/podman.sock:/var/run/podman/podman.sock
      - /opt/runner-work-01:/home/runner/_work
    restart: always

  runner-02:
    image: docker.io/salexson/github-action-runner:latest
    container_name: github-runner-02
    environment:
      GITHUB_REPOSITORY: owner/repo
      RUNNER_TOKEN: ${RUNNER_TOKEN_2}
      RUNNER_NAME: runner-02
      RUNNER_LABELS: podman,linux,amd64
    volumes:
      - /var/run/podman/podman.sock:/var/run/podman/podman.sock
      - /opt/runner-work-02:/home/runner/_work
    restart: always
```

### Launch Multiple Runners

```bash
#!/bin/bash
for i in {1..3}; do
  podman run -d \
    --name github-runner-$i \
    -e GITHUB_REPOSITORY="owner/repo" \
    -e RUNNER_TOKEN="token_$i" \
    -e RUNNER_NAME="runner-0$i" \
    -e RUNNER_LABELS="podman,linux,amd64" \
    -v /var/run/podman/podman.sock:/var/run/podman/podman.sock \
    -v /opt/runner-work-$i:/home/runner/_work \
    docker.io/salexson/github-action-runner:latest
done
```

---

## Reference

### Useful Commands

```bash
# Check runner status
gh api repos/owner/repo/actions/runners

# Get runner details
podman inspect github-runner

# Monitor in real-time
watch podman stats github-runner

# Export runner logs
podman logs github-runner > runner.log

# Update image
podman pull docker.io/salexson/github-action-runner:latest
```

### Documentation Links
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Self-Hosted Runners](https://docs.github.com/en/actions/hosting-your-own-runners)
- [Runner Images](https://github.com/actions/runner)
- [Podman Documentation](https://docs.podman.io/)

---

## Support

For issues or questions:
1. Check runner logs: `podman logs github-runner`
2. Verify token is valid and not expired
3. Check GitHub runner settings
4. Review workflow syntax
5. Consult Podman/Docker documentation

---

**Last Updated**: 2025-11-06  
**Version**: 1.0.0  
**Status**: ✅ Production Ready

