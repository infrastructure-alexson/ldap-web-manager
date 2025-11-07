# Quick Reference: Podman Build & Push

## TL;DR - Just Build & Push

```bash
cd infrastructure/ldap-web-manager
./scripts/build-and-push-podman.sh
```

Done! Your image is now at `docker.io/salexson/github-action-runner:latest`

---

## Common Commands

### Build Only (No Push)
```bash
./scripts/build-and-push-podman.sh --no-push
```

### Build with Specific Tag
```bash
./scripts/build-and-push-podman.sh --tag v1.0.0
```

### Build for Single Platform
```bash
./scripts/build-and-push-podman.sh --platform linux/amd64
```

### Push Existing Image
```bash
podman push docker.io/salexson/github-action-runner:latest
```

### Test Image Locally
```bash
podman run --rm docker.io/salexson/github-action-runner:latest echo "Works!"
```

### Pull Image from Docker Hub
```bash
podman pull docker.io/salexson/github-action-runner:latest
```

---

## Setup (One Time)

### 1. Install Podman
```bash
# Rocky Linux 8/9
sudo dnf install -y podman

# Ubuntu/Debian
sudo apt-get install -y podman

# macOS
brew install podman
```

### 2. Login to Docker Hub
```bash
podman login docker.io
# Enter username: salexson
# Enter password/token: [your_token_here]
```

### 3. Make Script Executable
```bash
chmod +x infrastructure/ldap-web-manager/scripts/build-and-push-podman.sh
```

---

## All Options

```bash
./build-and-push-podman.sh \
  --image github-action-runner \
  --tag latest \
  --registry docker.io \
  --username salexson \
  --dockerfile Dockerfile \
  --context . \
  --platform linux/amd64,linux/arm64 \
  --verbose
```

| Option | Default | Purpose |
|--------|---------|---------|
| `--image` | `github-action-runner` | Image name |
| `--tag` | `latest` | Version tag |
| `--registry` | `docker.io` | Registry URL |
| `--username` | `salexson` | Docker Hub user |
| `--dockerfile` | `Dockerfile` | Dockerfile path |
| `--context` | `.` | Build context |
| `--platform` | `linux/amd64,linux/arm64` | Architectures |
| `--no-push` | Skip push to registry |
| `--verbose` | Detailed output |

---

## GitHub Actions (Automatic Builds)

The script includes GitHub Actions workflow:

**File**: `.github/workflows/build-action-runner.yml`

**Triggers**:
- Push to `main` or `develop`
- Create git tag (e.g., `git tag v1.0.0`)
- Manual trigger via Actions tab

**Builds**:
- ✅ Multi-platform (amd64, arm64)
- ✅ Automatic push on main
- ✅ PR build verification

**Setup**:
1. Add `DOCKER_HUB_TOKEN` secret in GitHub
2. Copy workflow to `.github/workflows/`
3. Commit and push

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Podman not found" | Install Podman first |
| "Not authenticated" | Run `podman login docker.io` |
| "Dockerfile not found" | Use `--dockerfile ./path/to/Dockerfile` |
| "Push failed" | Check credentials and disk space |
| "Multi-platform failed" | Use `--platform linux/amd64` only |

---

## Image Location

**Docker Hub**: `docker.io/salexson/github-action-runner`

**Pull command**:
```bash
podman pull docker.io/salexson/github-action-runner:latest
```

**Docker command**:
```bash
docker pull docker.io/salexson/github-action-runner:latest
```

---

## Next Steps

- ✅ Build image locally
- ✅ Test image with `podman run`
- ✅ Push to Docker Hub
- ✅ Use in GitHub Actions
- ✅ Monitor with GitHub Actions logs

**Done!** 🎉

---

For full documentation, see: `doc/GITHUB-ACTION-RUNNER-BUILD.md`

