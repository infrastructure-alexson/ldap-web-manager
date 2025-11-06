# Container Registry Setup & Configuration

**Date**: November 6, 2025  
**Status**: Implementation Guide  
**Registries**: Docker Hub, Quay.io, GitHub Container Registry

---

## Overview

LDAP Web Manager container images are published to three major registries:

1. **Docker Hub** - Most popular, easy access
2. **Quay.io** - Enterprise features, vulnerability scanning
3. **GitHub Container Registry (GHCR)** - Integrated with GitHub

All registries provide:
- ✅ Multi-architecture support (amd64, arm64)
- ✅ Automated builds on release tags
- ✅ Vulnerability scanning
- ✅ Version tagging
- ✅ Latest tag for bleeding edge

---

## Registries Overview

### Docker Hub

**Organization**: `infrastructure-alexson`

**Images**:
- `docker.io/infrastructure-alexson/ldap-web-manager-backend`
- `docker.io/infrastructure-alexson/ldap-web-manager-frontend`

**Features**:
- Free public hosting
- Automatic builds from GitHub
- Docker Scout security scanning
- Official Docker registry
- High visibility in community

**Setup**:
```bash
# Create Docker Hub account at https://hub.docker.com
# Create organization: infrastructure-alexson
# Enable automated builds from GitHub
```

### Quay.io

**Organization**: `infrastructure-alexson`

**Images**:
- `quay.io/infrastructure-alexson/ldap-web-manager-backend`
- `quay.io/infrastructure-alexson/ldap-web-manager-frontend`

**Features**:
- Free tier available
- Advanced security scanning (Clair)
- Build automation
- Robot accounts for CI/CD
- Team management
- Repository mirroring

**Setup**:
```bash
# Create Quay account at https://quay.io
# Create organization: infrastructure-alexson
# Enable vulnerability scanning
# Configure robot account for automation
```

### GitHub Container Registry (GHCR)

**Organization**: `github.com/infrastructure-alexson`

**Images**:
- `ghcr.io/infrastructure-alexson/ldap-web-manager-backend`
- `ghcr.io/infrastructure-alexson/ldap-web-manager-frontend`

**Features**:
- Integrated with GitHub Actions
- Free for public repositories
- Fine-grained access control
- Works with GitHub Package authentication
- Easy integration with CI/CD

**Setup**: Automatic (enabled by default in GitHub Actions)

---

## Authentication & Credentials

### Docker Hub

```bash
# Create Docker Hub access token
# Settings → Security → New Access Token

# Store in GitHub Secrets:
DOCKER_HUB_USERNAME=<your-username>
DOCKER_HUB_PASSWORD=<access-token>

# Test locally:
docker login -u $DOCKER_HUB_USERNAME -p $DOCKER_HUB_PASSWORD docker.io
```

### Quay.io

```bash
# Create Quay robot account
# Settings → Robot Accounts → Create Robot Account

# Store in GitHub Secrets:
QUAY_USERNAME=<robot-account>
QUAY_PASSWORD=<encrypted-password>

# Create repo first:
# Repositories → Create New Repository

# Test locally:
docker login -u $QUAY_USERNAME -p $QUAY_PASSWORD quay.io
```

### GitHub Container Registry

```bash
# Automatically uses GITHUB_TOKEN
# Token permissions needed: write:packages, read:packages

# No additional setup required - GitHub Actions handles it
# Can also login manually:
docker login ghcr.io -u $GITHUB_ACTOR -p $GITHUB_TOKEN
```

---

## Pulling Images

### From Docker Hub

```bash
# Latest version
docker pull infrastructure-alexson/ldap-web-manager-backend:latest
docker pull infrastructure-alexson/ldap-web-manager-frontend:latest

# Specific version
docker pull infrastructure-alexson/ldap-web-manager-backend:v2.2.0
docker pull infrastructure-alexson/ldap-web-manager-frontend:v2.2.0

# With explicit registry
docker pull docker.io/infrastructure-alexson/ldap-web-manager-backend:v2.2.0
```

### From Quay.io

```bash
# Latest version
docker pull quay.io/infrastructure-alexson/ldap-web-manager-backend:latest
docker pull quay.io/infrastructure-alexson/ldap-web-manager-frontend:latest

# Specific version
docker pull quay.io/infrastructure-alexson/ldap-web-manager-backend:v2.2.0
docker pull quay.io/infrastructure-alexson/ldap-web-manager-frontend:v2.2.0
```

### From GitHub Container Registry

```bash
# Requires authentication
echo $PAT | docker login ghcr.io -u USERNAME --password-stdin

# Latest version
docker pull ghcr.io/infrastructure-alexson/ldap-web-manager-backend:latest
docker pull ghcr.io/infrastructure-alexson/ldap-web-manager-frontend:latest

# Specific version
docker pull ghcr.io/infrastructure-alexson/ldap-web-manager-backend:v2.2.0
docker pull ghcr.io/infrastructure-alexson/ldap-web-manager-frontend:v2.2.0
```

---

## Using with docker-compose

### Docker Hub

```yaml
version: '3.8'

services:
  backend:
    image: infrastructure-alexson/ldap-web-manager-backend:v2.2.0
    # ... rest of config ...

  frontend:
    image: infrastructure-alexson/ldap-web-manager-frontend:v2.2.0
    # ... rest of config ...
```

### Quay.io

```yaml
version: '3.8'

services:
  backend:
    image: quay.io/infrastructure-alexson/ldap-web-manager-backend:v2.2.0
    # ... rest of config ...

  frontend:
    image: quay.io/infrastructure-alexson/ldap-web-manager-frontend:v2.2.0
    # ... rest of config ...
```

### GitHub Container Registry

```yaml
version: '3.8'

services:
  backend:
    image: ghcr.io/infrastructure-alexson/ldap-web-manager-backend:v2.2.0
    # ... rest of config ...

  frontend:
    image: ghcr.io/infrastructure-alexson/ldap-web-manager-frontend:v2.2.0
    # ... rest of config ...
```

---

## Multi-Architecture Support

All images support multiple architectures:

- **linux/amd64** - Intel/AMD 64-bit (most common)
- **linux/arm64** - ARM 64-bit (Apple Silicon, ARM servers)

Docker automatically selects the correct architecture:

```bash
# On Intel Mac
docker pull infrastructure-alexson/ldap-web-manager-backend:latest
# → Pulls linux/amd64 image

# On Apple Silicon Mac
docker pull infrastructure-alexson/ldap-web-manager-backend:latest
# → Pulls linux/arm64 image

# Force specific architecture
docker pull --platform linux/amd64 infrastructure-alexson/ldap-web-manager-backend:latest
docker pull --platform linux/arm64 infrastructure-alexson/ldap-web-manager-backend:latest
```

### For Podman

```bash
# Podman also supports multi-arch
podman pull quay.io/infrastructure-alexson/ldap-web-manager-backend:latest

# Force specific architecture
podman pull --platform linux/amd64 quay.io/infrastructure-alexson/ldap-web-manager-backend:latest
```

---

## Vulnerability Scanning

### Docker Scout (Docker Hub)

```bash
# View scan results on Docker Hub
# Repository → Security Scan → View Results

# Using Docker Scout CLI:
docker scout cves infrastructure-alexson/ldap-web-manager-backend:latest
```

### Clair (Quay.io)

```bash
# Automatic scanning on push
# Repository → Security Scan → View Results
# Settings → Enable Security Scanning
```

### Trivy (CI/CD)

GitHub Actions workflow includes Trivy scanning:

```bash
# View scan results in GitHub Security tab
# Actions → Publish Container Images → security-scan job
```

---

## Image Tags & Versioning

### Automatic Tagging Strategy

On each release tag (e.g., `v2.2.0`):

- **Semver tags**:
  - `v2.2.0` - Full version
  - `v2.2` - Major.minor
  - `v2` - Major only

- **Special tags**:
  - `latest` - Points to latest release
  - `main` - Points to main branch (if builds from main)

- **Build tags**:
  - `sha-<commit>` - Commit-specific tag
  - `<branch>` - Branch name

### Example Tags

```bash
# For tag v2.2.0:
docker pull infrastructure-alexson/ldap-web-manager-backend:v2.2.0
docker pull infrastructure-alexson/ldap-web-manager-backend:v2.2
docker pull infrastructure-alexson/ldap-web-manager-backend:v2
docker pull infrastructure-alexson/ldap-web-manager-backend:latest

# All point to the same image
```

---

## Automated Publishing

### GitHub Actions Workflow

File: `.github/workflows/publish-containers.yml`

**Triggers**:
- Push of version tags (v*.*.*)
- Manual trigger via workflow_dispatch

**Jobs**:
1. **build-backend** - Build backend image for multiple architectures
2. **build-frontend** - Build frontend image for multiple architectures
3. **security-scan** - Run Trivy security scanner
4. **create-release** - Create GitHub release with pull instructions

**Platforms Tested**:
- linux/amd64
- linux/arm64

**Registries Published To**:
1. Docker Hub
2. Quay.io
3. GitHub Container Registry

### Manual Release

```bash
# Create and push release tag
git tag -a v2.2.0 -m "Release v2.2.0"
git push origin v2.2.0

# GitHub Actions automatically:
# 1. Builds images for amd64 and arm64
# 2. Publishes to all three registries
# 3. Runs security scans
# 4. Creates GitHub release with pull instructions
```

---

## Troubleshooting

### Authentication Failed

```bash
# Error: authentication required
# Solution: Check credentials in GitHub Secrets

# Verify Docker Hub token:
docker login docker.io

# Verify Quay.io token:
docker login quay.io

# Check GitHub token permissions (needs packages:write)
```

### Image Not Found

```bash
# Error: image not found
# Solution: Wait for build to complete

# Check workflow status:
# Actions → Publish Container Images

# Verify architecture:
docker pull --platform linux/arm64 quay.io/infrastructure-alexson/ldap-web-manager-backend:latest
```

### Vulnerability Scanning Issues

```bash
# High vulnerabilities blocking release?
# 1. Review Trivy scan results in GitHub Security
# 2. Update base images (python:3.11, node:20, nginx:1.27)
# 3. Update dependencies
# 4. Re-run workflow
```

### Multi-Arch Build Failures

```bash
# Error building for arm64
# Solution: Check Docker Buildx configuration

# Verify Buildx builder:
docker buildx ls

# Check Docker Buildx setup:
docker run --rm --privileged docker/binfmt:latest --install all
docker buildx create --use --name multiarch
```

---

## Best Practices

### For Pulling Images

1. ✅ Use specific version tags for production
   ```bash
   docker pull infrastructure-alexson/ldap-web-manager-backend:v2.2.0
   ```

2. ✅ Use `latest` only for development
   ```bash
   docker pull infrastructure-alexson/ldap-web-manager-backend:latest
   ```

3. ✅ Pin images in docker-compose
   ```yaml
   image: infrastructure-alexson/ldap-web-manager-backend:v2.2.0
   ```

4. ❌ Avoid untagged pulls
   ```bash
   # NOT RECOMMENDED
   docker pull infrastructure-alexson/ldap-web-manager-backend
   ```

### For Security

1. ✅ Pull from trusted registries
   - Use official Docker Hub account
   - Use Quay.io for enterprise features
   - Use GHCR for GitHub projects

2. ✅ Verify image signatures (future)
   - Use Notary or cosign for signed images

3. ✅ Regular security scans
   - Check vulnerability reports weekly
   - Update base images regularly

4. ✅ Use read-only filesystems
   - Deploy with security: readonly in docker-compose

---

## Registry Comparison

| Feature | Docker Hub | Quay.io | GHCR |
|---------|-----------|---------|------|
| **Cost** | Free | Free/Paid | Free |
| **Scanning** | Docker Scout | Clair | Trivy |
| **Multi-arch** | ✅ Yes | ✅ Yes | ✅ Yes |
| **CI/CD** | Manual | Manual | Automatic |
| **Private Repos** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Team Mgmt** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Mirroring** | ❌ No | ✅ Yes | ❌ No |

---

## Future Enhancements

- [ ] Container image signing (cosign)
- [ ] OCI artifact support
- [ ] SBOM (Software Bill of Materials) generation
- [ ] Helm chart publishing
- [ ] OCI compliance certification

---

## Related Documentation

- [DOCKER-DEPLOYMENT.md](DOCKER-DEPLOYMENT.md) - Docker deployment guide
- [v2.2.0-NEXT-STEPS.md](v2.2.0-NEXT-STEPS.md) - Implementation roadmap
- [HEALTH-CHECKS.md](HEALTH-CHECKS.md) - Health check endpoints

---

**Last Updated**: November 6, 2025  
**Status**: Implementation Complete  
**Next Phase**: Podman Support (Issue #48)

