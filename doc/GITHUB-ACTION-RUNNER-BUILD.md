# GitHub Action Runner - Podman Build & Push Guide

## Overview

This guide covers building and pushing the GitHub Action Runner container image to Docker Hub using Podman.

**Image Location**: `docker.io/salexson/github-action-runner`

---

## Prerequisites

### System Requirements
- Podman 4.0+ installed
- Docker Hub account with credentials
- Network access to docker.io
- ~5GB disk space for build cache

### Installation

#### On Rocky Linux 8/9:
```bash
sudo dnf install -y podman podman-compose
```

#### On Ubuntu/Debian:
```bash
sudo apt-get install -y podman podman-compose
```

#### On macOS:
```bash
brew install podman
```

---

## Quick Start

### Basic Build & Push

```bash
./scripts/build-and-push-podman.sh
```

This will:
1. Build the container locally
2. Verify the image
3. Check Docker Hub authentication
4. Push to `docker.io/salexson/github-action-runner:latest`

### Build Only (No Push)

```bash
./scripts/build-and-push-podman.sh --no-push
```

### Custom Tag

```bash
./scripts/build-and-push-podman.sh --tag v1.0.0
```

---

## Script Usage

### Full Command Syntax

```bash
./build-and-push-podman.sh [OPTIONS]
```

### Available Options

| Option | Default | Description |
|--------|---------|-------------|
| `--image` | `github-action-runner` | Container image name |
| `--tag` | `latest` | Image tag/version |
| `--registry` | `docker.io` | Docker registry URL |
| `--username` | `salexson` | Docker Hub username |
| `--dockerfile` | `Dockerfile` | Path to Dockerfile |
| `--context` | `.` | Build context directory |
| `--platform` | `linux/amd64,linux/arm64` | Target platforms |
| `--no-push` | N/A | Build only, skip push |
| `--verbose` | N/A | Verbose build output |
| `--help` | N/A | Show help message |

### Examples

#### Multi-platform build with custom tag:
```bash
./build-and-push-podman.sh --tag v2.0.0 --platform linux/amd64,linux/arm64
```

#### Build for single architecture:
```bash
./build-and-push-podman.sh --platform linux/amd64
```

#### Use custom Dockerfile location:
```bash
./build-and-push-podman.sh \
  --dockerfile ./docker/github-action-runner/Dockerfile \
  --context ./docker/github-action-runner
```

#### Verbose output:
```bash
./build-and-push-podman.sh --verbose
```

---

## Authentication

### Option 1: Interactive Login (Recommended)

```bash
podman login docker.io
```

Then run the script:
```bash
./build-and-push-podman.sh
```

### Option 2: Environment Variables

```bash
export DOCKER_USERNAME=salexson
export DOCKER_PASSWORD=your_token_here
./build-and-push-podman.sh
```

### Option 3: Use Docker Hub Token

1. Generate a token at: https://hub.docker.com/settings/security
2. Save to file: `~/.podman/auth.json`
3. Run the script

---

## GitHub Actions Workflow

### Setup GitHub Secrets

1. Go to Repository Settings → Secrets and Variables → Actions
2. Add these secrets:
   - `DOCKER_HUB_TOKEN`: Your Docker Hub Personal Access Token
   - `DOCKER_HUB_USERNAME`: Your Docker Hub username (optional)

### Workflow File

The included `github-actions-build-workflow.yml` provides:

✅ Multi-platform builds (amd64, arm64)  
✅ Automatic pushing on main branch  
✅ Pull request build verification  
✅ Tag-based releases  
✅ Layer caching for faster builds  

### Using in GitHub Actions

1. Copy workflow file to `.github/workflows/build-action-runner.yml`:
```bash
cp scripts/github-actions-build-workflow.yml .github/workflows/build-action-runner.yml
```

2. Commit and push:
```bash
git add .github/workflows/build-action-runner.yml
git commit -m "Add GitHub Actions build workflow"
git push
```

3. Trigger builds by:
   - Pushing to `main` branch
   - Creating a tag: `git tag v1.0.0 && git push --tags`
   - Manual trigger via Actions tab

---

## Docker Hub Repository Setup

### Create Repository

1. Go to https://hub.docker.com
2. Click "Create Repository"
3. Name: `github-action-runner`
4. Description: "GitHub Action Runner - Podman/Docker compatible"
5. Visibility: Public
6. Create

### Repository Settings

**Tags Management**:
```bash
podman pull docker.io/salexson/github-action-runner:latest
podman pull docker.io/salexson/github-action-runner:v1.0.0
```

**Description**:
```
GitHub Action Runner - Podman/Docker compatible container image

Includes:
- GitHub CLI (gh)
- Docker/Podman support
- Multi-platform support (amd64, arm64)
- CI/CD tool integration

Pull: docker pull salexson/github-action-runner
```

---

## Verification & Testing

### Verify Local Build

```bash
# List images
podman images salexson/github-action-runner

# Inspect image
podman inspect docker.io/salexson/github-action-runner:latest

# Show image details
podman images docker.io/salexson/github-action-runner --format "{{.ID}}: {{.Size}}"
```

### Test Image Locally

```bash
# Run container
podman run --rm docker.io/salexson/github-action-runner:latest echo "Hello from GitHub Action Runner"

# Run interactive shell
podman run --rm -it docker.io/salexson/github-action-runner:latest /bin/bash

# Check installed tools
podman run --rm docker.io/salexson/github-action-runner:latest which gh
podman run --rm docker.io/salexson/github-action-runner:latest docker --version
podman run --rm docker.io/salexson/github-action-runner:latest podman --version
```

### Pull and Test from Docker Hub

```bash
# Pull latest
podman pull docker.io/salexson/github-action-runner:latest

# Or pull specific version
podman pull docker.io/salexson/github-action-runner:v1.0.0

# Run tests
podman run --rm docker.io/salexson/github-action-runner:latest /usr/local/bin/test-runner.sh
```

---

## Troubleshooting

### Issue: "Dockerfile not found"

**Solution**: Ensure Dockerfile path is correct
```bash
./build-and-push-podman.sh --dockerfile ./docker/Dockerfile --context ./docker
```

### Issue: "Not authenticated to Docker Hub"

**Solution**: Login first
```bash
podman login docker.io
# Enter username and password
```

### Issue: "Multi-platform build not supported"

**Solution**: Use single platform
```bash
./build-and-push-podman.sh --platform linux/amd64
```

### Issue: "Push fails - invalid tag"

**Solution**: Verify format
```bash
# Correct format
./build-and-push-podman.sh --username salexson --image github-action-runner

# Not: --image salexson/github-action-runner
```

### Issue: "Insufficient disk space"

**Solution**: Clean up build cache
```bash
podman system prune -a
```

---

## Advanced Usage

### Custom Build Arguments

For Dockerfile with build args:

```bash
# Modify the script to add build args
podman build \
  --tag "$FULL_IMAGE_NAME" \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --build-arg VCS_REF=$(git rev-parse --short HEAD) \
  --file "$DOCKERFILE" \
  "$BUILD_CONTEXT"
```

### Multi-Registry Push

Modify script to push to multiple registries:

```bash
# Push to Docker Hub
podman push "$FULL_IMAGE_NAME"

# Push to Quay.io
podman tag "$FULL_IMAGE_NAME" "quay.io/$USERNAME/$IMAGE_NAME:$IMAGE_TAG"
podman push "quay.io/$USERNAME/$IMAGE_NAME:$IMAGE_TAG"

# Push to GHCR
podman tag "$FULL_IMAGE_NAME" "ghcr.io/$USERNAME/$IMAGE_NAME:$IMAGE_TAG"
podman push "ghcr.io/$USERNAME/$IMAGE_NAME:$IMAGE_TAG"
```

### Rootless Container Build

For enhanced security:

```bash
# Configure rootless mode
podman system migrate

# Build as regular user
./build-and-push-podman.sh
```

---

## CI/CD Integration

### GitHub Actions

Already provided in `github-actions-build-workflow.yml`:
- Runs on push to main/develop
- Builds on tags
- Multi-platform support
- Automatic Docker Hub push

### GitLab CI

```yaml
build-and-push:
  stage: build
  image: podman:latest
  script:
    - podman login -u $DOCKER_USERNAME -p $DOCKER_PASSWORD docker.io
    - ./scripts/build-and-push-podman.sh --tag $CI_COMMIT_TAG
  only:
    - tags
```

### Jenkins

```groovy
pipeline {
  agent any
  
  stages {
    stage('Build & Push') {
      steps {
        sh './scripts/build-and-push-podman.sh --tag ${BUILD_NUMBER}'
      }
    }
  }
}
```

---

## Security Best Practices

### 1. Use Personal Access Tokens

```bash
# Generate at https://hub.docker.com/settings/security
podman login --username salexson --password-stdin docker.io
# Paste token, press Enter
```

### 2. Never Commit Credentials

```bash
# Add to .gitignore
echo "~/.podman/auth.json" >> .gitignore
```

### 3. Use Rootless Mode

```bash
# Enable rootless for non-root builds
podman system migrate --rootless
```

### 4. Scan Images for Vulnerabilities

```bash
# Using Trivy
podman run --rm -v /var/run/podman/podman.sock:/var/run/podman/podman.sock \
  aquasec/trivy image docker.io/salexson/github-action-runner:latest
```

---

## Performance Optimization

### Enable BuildKit

```bash
# Use BuildKit for faster builds
export DOCKER_BUILDKIT=1
./build-and-push-podman.sh
```

### Layer Caching

```bash
# Leverage cache for faster rebuilds
podman build --cache-from docker.io/salexson/github-action-runner:latest \
  -t docker.io/salexson/github-action-runner:latest .
```

### Parallel Multi-Architecture Builds

```bash
# Build for multiple platforms in parallel
podman build \
  --platform linux/amd64,linux/arm64 \
  -t docker.io/salexson/github-action-runner:latest \
  .
```

---

## Release Management

### Semantic Versioning

```bash
# Version 1.0.0 release
./build-and-push-podman.sh --tag v1.0.0

# Version 1.1.0 release
./build-and-push-podman.sh --tag v1.1.0

# Version 2.0.0 release
./build-and-push-podman.sh --tag v2.0.0
```

### Tag Management

```bash
# Latest tag
podman tag docker.io/salexson/github-action-runner:v1.0.0 \
  docker.io/salexson/github-action-runner:latest
podman push docker.io/salexson/github-action-runner:latest

# Stable tag
podman tag docker.io/salexson/github-action-runner:v1.0.0 \
  docker.io/salexson/github-action-runner:stable
podman push docker.io/salexson/github-action-runner:stable
```

---

## Reference

### Documentation Links
- [Podman Documentation](https://docs.podman.io/)
- [Docker Hub API](https://docs.docker.com/docker-hub/api/)
- [Container Registries](https://podman.io/blogs/2021/04/08/signing-containers.html)

### Related Commands

```bash
# View build history
podman history docker.io/salexson/github-action-runner:latest

# Export image
podman save docker.io/salexson/github-action-runner:latest > runner.tar

# Import image
podman load < runner.tar

# Delete local image
podman rmi docker.io/salexson/github-action-runner:latest

# Check image size
podman images docker.io/salexson/github-action-runner --format "{{.Size}}"
```

---

## Support & Issues

For issues or questions:
1. Check the Troubleshooting section above
2. Review Podman documentation
3. Check Docker Hub for image status
4. Review GitHub Actions logs for workflow issues

---

**Last Updated**: 2025-11-06  
**Version**: 1.0.0  
**Status**: ✅ Production Ready

