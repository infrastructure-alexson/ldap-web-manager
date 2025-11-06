# GitHub Secrets Configuration

**For**: Container Registry Publishing Workflow  
**File**: `.github/workflows/publish-containers.yml`

---

## Required Secrets

These secrets must be configured in GitHub repository settings:
**Settings → Secrets and variables → Actions → New repository secret**

### Docker Hub

**`DOCKER_HUB_USERNAME`**
- **Type**: Personal Access Token (PAT) or Docker Hub username
- **Value**: Your Docker Hub username
- **How to Create**:
  1. Go to https://hub.docker.com/settings/security
  2. Create new access token
  3. Copy token
  4. Add to GitHub Secrets as `DOCKER_HUB_USERNAME`

**`DOCKER_HUB_PASSWORD`**
- **Type**: Personal Access Token
- **Value**: The access token (NOT your password)
- **How to Create**:
  1. Go to https://hub.docker.com/settings/security
  2. Create new access token with appropriate scopes
  3. Copy token value
  4. Add to GitHub Secrets as `DOCKER_HUB_PASSWORD`

**Permissions Needed**:
- Read & Write access to repositories
- Create new repositories

### Quay.io

**`QUAY_USERNAME`**
- **Type**: Robot Account name
- **Value**: Format: `+<org>+<robot-name>`
- **How to Create**:
  1. Go to https://quay.io/organization/infrastructure-alexson/robots
  2. Create new robot account
  3. Copy the robot account name
  4. Add to GitHub Secrets as `QUAY_USERNAME`

**`QUAY_PASSWORD`**
- **Type**: Robot Account password (encrypted token)
- **Value**: The encrypted password from robot account
- **How to Create**:
  1. In robot account details, copy the password
  2. Add to GitHub Secrets as `QUAY_PASSWORD`

**Permissions Needed**:
- Read & Write access to repositories
- Repository creation permission

### Required Variables

**`QUAY_ORG`** (GitHub Variables, not Secrets)
- **Type**: Repository Variable
- **Value**: `infrastructure-alexson`
- **Location**: Settings → Variables and secrets → Variables

---

## Setup Instructions

### Step 1: Create Docker Hub Access Token

1. Navigate to https://hub.docker.com/settings/security
2. Click "New Access Token"
3. Name: `GitHub Actions`
4. Permissions: Select "Read & Write"
5. Click "Generate"
6. Copy the token

### Step 2: Create Quay.io Robot Account

1. Navigate to https://quay.io/organization/infrastructure-alexson/robots
2. Click "Create Robot Account"
3. Name: `github-actions`
4. Description: `For automated container builds and publishing`
5. Click "Create Robot Account"
6. In robot details, copy the username and password

### Step 3: Add Secrets to GitHub

1. Go to **Settings → Secrets and variables → Actions**

2. Click **"New repository secret"**

3. Add each secret:
   - **Name**: `DOCKER_HUB_USERNAME`
   - **Value**: Your Docker Hub username
   - **Click**: Add secret

4. Repeat for:
   - **`DOCKER_HUB_PASSWORD`**: Docker Hub access token
   - **`QUAY_USERNAME`**: Quay.io robot account name
   - **`QUAY_PASSWORD`**: Quay.io robot password

### Step 4: Add Repository Variable

1. Go to **Settings → Secrets and variables → Variables**

2. Click **"New repository variable"**

3. Add:
   - **Name**: `QUAY_ORG`
   - **Value**: `infrastructure-alexson`
   - **Click**: Add variable

### Step 5: Verify Setup

1. Go to **Actions → Publish Container Images**
2. Click **"Run workflow"**
3. Check that the workflow completes successfully
4. Verify images appear in registries:
   - Docker Hub: https://hub.docker.com/r/infrastructure-alexson
   - Quay.io: https://quay.io/organization/infrastructure-alexson
   - GHCR: ghcr.io packages in repository

---

## Secret Security Best Practices

✅ **DO**:
- Use access tokens instead of passwords
- Limit token permissions to minimum needed
- Rotate tokens periodically
- Store tokens securely
- Use different tokens for different services
- Keep tokens in GitHub Secrets (encrypted)
- Audit token usage regularly

❌ **DON'T**:
- Commit secrets to repository
- Use personal passwords
- Share tokens with team members
- Use same token for multiple services
- Log secrets in workflow output
- Publish secrets in documentation

---

## Testing the Workflow

### Manual Trigger

1. Go to **Actions → Publish Container Images**
2. Click **"Run workflow"**
3. Select **main** branch
4. Click **"Run workflow"**

### Via Release Tag

1. Create and push a release tag:
   ```bash
   git tag -a v2.2.0 -m "Release v2.2.0"
   git push origin v2.2.0
   ```

2. Workflow automatically triggers

3. Watch progress in **Actions → Publish Container Images**

### Verify Publication

```bash
# Docker Hub
docker pull infrastructure-alexson/ldap-web-manager-backend:latest

# Quay.io
docker pull quay.io/infrastructure-alexson/ldap-web-manager-backend:latest

# GitHub Container Registry
docker pull ghcr.io/infrastructure-alexson/ldap-web-manager-backend:latest
```

---

## Troubleshooting

### Secret Not Recognized

**Error**: `Authentication failed for docker.io`

**Solution**:
1. Verify secret name exactly matches workflow file
2. Check secret value is not empty
3. Try manually re-entering the secret
4. Ensure secret is at repository level (not organization)

### Token Expired

**Error**: `Invalid credentials`

**Solution**:
1. Generate new access token (old one expired)
2. Update GitHub Secret with new token
3. Retry workflow

### Image Not Published

**Error**: Image doesn't appear in registry

**Solution**:
1. Check workflow execution logs
2. Verify authentication secrets are correct
3. Check Docker Hub/Quay.io permissions
4. Manually test login: `docker login docker.io`

### Slow Builds

**Issue**: Multi-architecture builds taking too long

**Solution**:
1. Enable GitHub Actions cache
2. Use self-hosted runner for faster builds
3. Build single architecture for testing, multi-arch for releases

---

## Maintenance

### Quarterly Rotation

- [ ] Rotate Docker Hub access tokens
- [ ] Rotate Quay.io robot account credentials
- [ ] Review GitHub Secrets audit log
- [ ] Update documentation

### Security Audit

- [ ] Check for unused secrets
- [ ] Verify token permissions are minimal
- [ ] Review recent workflow executions
- [ ] Check for failed authentication attempts

---

## References

- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions)
- [Docker Hub Security](https://docs.docker.com/docker-hub/access-tokens/)
- [Quay.io Robot Accounts](https://docs.quay.io/glossary/robot-accounts.html)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)

---

**Last Updated**: November 6, 2025  
**Status**: Configuration Guide  
**For**: v2.2.0 Container Registry Implementation

