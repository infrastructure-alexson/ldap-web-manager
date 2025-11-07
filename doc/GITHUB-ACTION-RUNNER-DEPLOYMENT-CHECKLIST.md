# GitHub Action Runner - Deployment Checklist

**Purpose**: Step-by-step checklist for deploying GitHub Action Runner  
**Target**: `docker.io/salexson/github-action-runner`  
**Status**: Production Ready

---

## Pre-Deployment Planning

### Prerequisites Review
- [ ] Podman 4.0+ or Docker 20.10+ installed
- [ ] Docker Hub account with credentials
- [ ] GitHub account with admin access to repository
- [ ] ~10GB disk space available
- [ ] Network access to github.com and docker.io

### Repository Access
- [ ] Have GitHub repository URL: `https://github.com/OWNER/REPO`
- [ ] Have repository admin access
- [ ] Know repository is public or have access

### Infrastructure Ready
- [ ] Target host(s) identified and accessible
- [ ] Firewall allows outbound HTTPS (github.com, docker.io)
- [ ] DNS resolution working
- [ ] Internet connectivity verified

---

## Phase 1: Prepare Authentication

### GitHub Runner Token
- [ ] Go to `https://github.com/OWNER/REPO/settings/actions/runners`
- [ ] Click "New self-hosted runner"
- [ ] Copy registration token (valid 1 hour)
- [ ] Store token securely (do not commit to git)
- [ ] Note token will be needed immediately

### Docker Hub Authentication
- [ ] Go to `https://hub.docker.com`
- [ ] Login to Docker Hub account
- [ ] Generate Personal Access Token:
  - [ ] Go to Account Settings → Security
  - [ ] Click "New Access Token"
  - [ ] Select "Read, Write" scope
  - [ ] Copy token and store securely
- [ ] Credentials ready for use

---

## Phase 2: Prepare Environment

### Linux Host Setup
- [ ] Install Podman:
  ```bash
  [ ] sudo dnf install -y podman     # Rocky Linux
  [ ] sudo apt-get install podman    # Ubuntu
  ```
- [ ] Verify Podman installed:
  ```bash
  [ ] podman --version  # Should be 4.0+
  ```
- [ ] Podman service running:
  ```bash
  [ ] sudo systemctl start podman
  [ ] sudo systemctl enable podman
  ```

### Docker Host Setup (Alternative)
- [ ] Install Docker:
  ```bash
  [ ] sudo dnf install -y docker     # Rocky Linux
  [ ] sudo apt-get install docker.io # Ubuntu
  ```
- [ ] Verify Docker installed:
  ```bash
  [ ] docker --version  # Should be 20.10+
  ```
- [ ] Docker service running:
  ```bash
  [ ] sudo systemctl start docker
  [ ] sudo systemctl enable docker
  ```

### Create Working Directories
- [ ] Create runner work directory:
  ```bash
  [ ] mkdir -p /opt/runner-work
  [ ] mkdir -p /opt/runner-config
  [ ] sudo chown -R $(whoami) /opt/runner-*
  ```

---

## Phase 3: Build Container Image

### Option A: Build Locally (Recommended)
- [ ] Clone repository or navigate to project
- [ ] Make build script executable:
  ```bash
  [ ] chmod +x scripts/build-and-push-podman.sh
  ```
- [ ] Build image locally (no push):
  ```bash
  [ ] ./scripts/build-and-push-podman.sh --no-push
  ```
- [ ] Verify build successful:
  ```bash
  [ ] podman images salexson/github-action-runner
  ```

### Option B: Pull from Docker Hub (Pre-built)
- [ ] Pull pre-built image:
  ```bash
  [ ] podman pull docker.io/salexson/github-action-runner:latest
  ```
- [ ] Verify image pulled:
  ```bash
  [ ] podman images salexson/github-action-runner
  ```

### Verify Image
- [ ] Test image locally:
  ```bash
  [ ] podman run --rm docker.io/salexson/github-action-runner:latest echo "Works!"
  [ ] podman run --rm docker.io/salexson/github-action-runner:latest gh --version
  ```

---

## Phase 4: Deploy Runner (Choose One)

### Option A: Docker Compose (Easiest for Multiple Runners)

#### Prepare Environment File
- [ ] Create `.env` file:
  ```bash
  [ ] cat > .env <<EOF
  GITHUB_REPOSITORY=owner/repo
  RUNNER_TOKEN=ghs_xxxxx
  RUNNER_NAME=runner-01
  RUNNER_LABELS=podman,linux,amd64
  WORK_DIR=/opt/runner-work
  CONFIG_DIR=/opt/runner-config
  RUNNER_CPUS=2
  RUNNER_MEMORY=4G
  EOF
  ```

#### Deploy with Compose
- [ ] Navigate to compose directory:
  ```bash
  [ ] cd docker/github-action-runner
  ```
- [ ] Start runner:
  ```bash
  [ ] docker-compose up -d
  ```
- [ ] Verify running:
  ```bash
  [ ] docker-compose ps
  [ ] docker-compose logs github-runner
  ```

#### Verify Deployment
- [ ] Check container running:
  ```bash
  [ ] docker-compose ps
  ```
- [ ] Check logs for errors:
  ```bash
  [ ] docker-compose logs github-runner | grep -i error
  ```

---

### Option B: Direct Podman Run (Quick Testing)

#### Create Environment
- [ ] Set environment variables:
  ```bash
  [ ] export GITHUB_REPOSITORY="owner/repo"
  [ ] export RUNNER_TOKEN="ghs_xxxxx"
  [ ] export RUNNER_NAME="runner-01"
  [ ] export RUNNER_LABELS="podman,linux,amd64"
  ```

#### Run Container
- [ ] Run container:
  ```bash
  [ ] podman run -d \
    --name github-runner \
    --hostname github-runner \
    -e GITHUB_REPOSITORY="$GITHUB_REPOSITORY" \
    -e RUNNER_TOKEN="$RUNNER_TOKEN" \
    -e RUNNER_NAME="$RUNNER_NAME" \
    -e RUNNER_LABELS="$RUNNER_LABELS" \
    -v /var/run/podman/podman.sock:/var/run/podman/podman.sock \
    -v /opt/runner-work:/home/runner/_work \
    -v /opt/runner-config:/home/runner/.runner \
    docker.io/salexson/github-action-runner:latest
  ```

#### Verify Deployment
- [ ] Container running:
  ```bash
  [ ] podman ps | grep github-runner
  ```
- [ ] Check logs:
  ```bash
  [ ] podman logs github-runner
  ```
- [ ] No errors visible

---

### Option C: Systemd Service (Long-term Deployment)

#### Create Service File
- [ ] Create `/etc/systemd/system/github-runner.service`:
  ```bash
  [ ] sudo cat > /etc/systemd/system/github-runner.service <<EOF
  [Unit]
  Description=GitHub Actions Self-Hosted Runner
  After=network-online.target
  Wants=network-online.target

  [Service]
  Type=simple
  User=root
  WorkingDirectory=/opt/runner
  Environment="GITHUB_REPOSITORY=owner/repo"
  Environment="RUNNER_TOKEN=ghs_xxxxx"
  Environment="RUNNER_NAME=runner-01"
  Environment="RUNNER_LABELS=podman,linux,amd64"
  ExecStart=/usr/bin/podman run --rm \
    -e GITHUB_REPOSITORY=owner/repo \
    -e RUNNER_TOKEN=ghs_xxxxx \
    -e RUNNER_NAME=runner-01 \
    -e RUNNER_LABELS=podman,linux,amd64 \
    -v /var/run/podman/podman.sock:/var/run/podman/podman.sock \
    -v /opt/runner-work:/home/runner/_work \
    docker.io/salexson/github-action-runner:latest
  Restart=always
  RestartSec=10

  [Install]
  WantedBy=multi-user.target
  EOF
  ```

#### Enable and Start
- [ ] Reload systemd:
  ```bash
  [ ] sudo systemctl daemon-reload
  ```
- [ ] Enable on boot:
  ```bash
  [ ] sudo systemctl enable github-runner.service
  ```
- [ ] Start service:
  ```bash
  [ ] sudo systemctl start github-runner.service
  ```
- [ ] Check status:
  ```bash
  [ ] sudo systemctl status github-runner.service
  ```
- [ ] Verify logs:
  ```bash
  [ ] sudo journalctl -u github-runner.service -f
  ```

---

## Phase 5: Verify Runner Registration

### Check in GitHub UI
- [ ] Go to `https://github.com/OWNER/REPO/settings/actions/runners`
- [ ] Runner should appear in list
- [ ] Status should be "Idle" or "Active"
- [ ] Note the runner name and labels

### Verify Runner Communication
- [ ] Runner shows as online
- [ ] No error messages in runner settings
- [ ] Last activity recent (within last minute)

### Test Runner Execution
- [ ] Create simple test workflow:
  ```bash
  [ ] mkdir -p .github/workflows
  [ ] cat > .github/workflows/test-runner.yml <<EOF
  name: Test Runner
  on: workflow_dispatch
  jobs:
    test:
      runs-on: self-hosted
      steps:
        - run: echo "Runner works!"
        - run: uname -a
        - run: podman --version
        - run: gh --version
  EOF
  ```
- [ ] Commit and push:
  ```bash
  [ ] git add .github/workflows/test-runner.yml
  [ ] git commit -m "Add test workflow"
  [ ] git push
  ```
- [ ] Trigger workflow:
  - [ ] Go to Actions tab on GitHub
  - [ ] Click "Test Runner"
  - [ ] Click "Run workflow"
- [ ] Verify execution:
  - [ ] Workflow should start immediately
  - [ ] Check runner in GitHub Actions logs
  - [ ] Should show system info output

---

## Phase 6: Production Hardening

### Security Hardening
- [ ] Update runner labels to match capabilities
- [ ] Configure resource limits if running multiple
- [ ] Set up SSH access if needed
- [ ] Configure firewall if necessary
- [ ] Review logs for any errors

### Performance Tuning
- [ ] Monitor CPU usage:
  ```bash
  [ ] podman stats github-runner
  ```
- [ ] Monitor memory usage
- [ ] Adjust resource limits if needed
- [ ] Check disk usage
- [ ] Clean up old builds if needed

### Maintenance Setup
- [ ] Set up automated log rotation
- [ ] Configure monitoring/alerting
- [ ] Test container restart procedures
- [ ] Document any customizations
- [ ] Create backup of configuration

### Security Review
- [ ] Verify token is not exposed
- [ ] Check no secrets in logs
- [ ] Verify volume permissions correct
- [ ] Confirm firewall rules allow outbound HTTPS
- [ ] Review network access

---

## Phase 7: Scale to Multiple Runners (Optional)

### Add Second Runner
- [ ] Generate new GitHub runner token
- [ ] Update Docker Compose to include `github-runner-2` service
- [ ] Or create separate systemd service for second runner
- [ ] Test workflow distribution

### Load Balancing
- [ ] Use workflow labels to distribute work
- [ ] Monitor runner utilization
- [ ] Add/remove runners based on demand
- [ ] Keep runners synchronized

---

## Phase 8: Ongoing Maintenance

### Daily Tasks
- [ ] Monitor runner health:
  ```bash
  [ ] docker-compose ps  # Or: systemctl status github-runner
  ```
- [ ] Check for stuck workflows
- [ ] Review error logs

### Weekly Tasks
- [ ] Update base image:
  ```bash
  [ ] podman pull rockylinux:8
  ```
- [ ] Clean up old images:
  ```bash
  [ ] podman system prune
  ```
- [ ] Review runner statistics

### Monthly Tasks
- [ ] Review runner token expiration (renew if needed)
- [ ] Update Docker Compose or systemd config
- [ ] Rebuild image with latest updates
- [ ] Test emergency procedures

### Quarterly Tasks
- [ ] Review runner performance
- [ ] Update documentation
- [ ] Audit security settings
- [ ] Plan for scaling

---

## Troubleshooting Checklist

### Runner Not Connecting
- [ ] Verify GitHub runner token is valid (< 1 hour old)
- [ ] Check network connectivity to github.com
- [ ] Verify GITHUB_REPOSITORY is correct format
- [ ] Check container logs for errors
- [ ] Restart container

### Workflows Not Executing
- [ ] Verify runner appears online in GitHub
- [ ] Check runner labels match workflow requirements
- [ ] Check for firewall blocking outbound
- [ ] Verify GitHub Actions not disabled
- [ ] Check runner workdir has space

### Container Crashes
- [ ] Check system resources (CPU, memory, disk)
- [ ] Review container logs
- [ ] Check Podman/Docker logs
- [ ] Verify base image available
- [ ] Check for permission issues

### High Resource Usage
- [ ] Monitor running workflows
- [ ] Check for stuck processes
- [ ] Limit resource usage if needed
- [ ] Review workflow efficiency
- [ ] Add more runners if needed

---

## Rollback Procedures

### If Deployment Fails
- [ ] Stop container:
  ```bash
  [ ] podman stop github-runner  # Or: docker-compose down
  ```
- [ ] Remove runner from GitHub settings
- [ ] Fix issues
- [ ] Restart deployment

### If Runner Breaks
- [ ] Unregister runner from GitHub
- [ ] Stop container
- [ ] Rebuild image
- [ ] Redeploy with fresh token

### Emergency Stop
- [ ] Stop container:
  ```bash
  [ ] sudo systemctl stop github-runner
  ```
- [ ] Remove from GitHub runners list manually
- [ ] Clean up directories
- [ ] Investigate root cause

---

## Post-Deployment

### Documentation
- [ ] Document runner configuration
- [ ] Document labels used
- [ ] Document scaling plan
- [ ] Update team runbooks
- [ ] Record deployment date/time

### Handoff
- [ ] Brief team on runner usage
- [ ] Provide troubleshooting guide
- [ ] Share escalation procedures
- [ ] Document access procedures
- [ ] Collect feedback

### Monitoring
- [ ] Set up alerts for runner down
- [ ] Monitor runner utilization
- [ ] Track workflow execution times
- [ ] Monitor resource usage
- [ ] Plan for scaling

---

## Sign-Off

### Deployment Complete
- [ ] All checklist items completed
- [ ] Runner operational and responsive
- [ ] Test workflow executed successfully
- [ ] Security reviewed and hardened
- [ ] Documentation complete

### Approval
- [ ] Deployment approved by: _______________
- [ ] Date: _______________
- [ ] Notes: ___________________________

---

## Quick Reference

### Key Commands
```bash
# Check status
podman ps | grep github-runner

# View logs
podman logs github-runner
# or
docker-compose logs github-runner

# Restart
podman restart github-runner
# or
docker-compose restart github-runner

# Stop
podman stop github-runner
# or
docker-compose down

# Clean up
podman system prune
```

### Key Directories
```bash
/opt/runner-work      # Working directory
/opt/runner-config    # Configuration storage
/var/log/runner       # Log files (if enabled)
```

### Key URLs
```
GitHub Runners: https://github.com/OWNER/REPO/settings/actions/runners
Docker Hub: https://hub.docker.com/repositories
Podman Docs: https://docs.podman.io/
```

---

**Status**: ✅ Ready for Deployment  
**Last Updated**: 2025-11-06  
**Version**: 1.0.0

