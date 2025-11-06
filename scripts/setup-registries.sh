#!/bin/bash

# Setup Container Registries for LDAP Web Manager
# This script helps configure Docker Hub, Quay.io, and GitHub Container Registry
# 
# Usage: ./scripts/setup-registries.sh

set -e

echo "=========================================="
echo "LDAP Web Manager - Registry Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detect OS
OS_TYPE=$(uname -s)

# Function to print colored output
print_step() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to open URL (OS-aware)
open_url() {
    if [[ "$OS_TYPE" == "Darwin" ]]; then
        open "$1"
    elif [[ "$OS_TYPE" == "Linux" ]]; then
        xdg-open "$1" 2>/dev/null || echo "Please open: $1"
    else
        echo "Please open: $1"
    fi
}

# Check prerequisites
print_step "Checking prerequisites..."

if ! command_exists git; then
    print_error "git not found. Please install git."
    exit 1
fi

if ! command_exists docker; then
    print_warning "docker not found. Skipping registry login tests."
    DOCKER_AVAILABLE=false
else
    print_success "docker found"
    DOCKER_AVAILABLE=true
fi

echo ""

# Step 1: Docker Hub Setup
print_step "Step 1: Docker Hub Setup"
echo ""
echo "Please visit: https://hub.docker.com/settings/security"
echo ""
echo "Instructions:"
echo "1. Create a new Access Token"
echo "2. Name it: GitHub Actions"
echo "3. Give it 'Read & Write' permissions"
echo "4. Copy the token"
echo ""

read -p "Have you created your Docker Hub access token? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter your Docker Hub username: " DOCKER_HUB_USERNAME
    read -sp "Enter your Docker Hub access token: " DOCKER_HUB_PASSWORD
    echo ""
    
    if [ $DOCKER_AVAILABLE = true ]; then
        print_step "Testing Docker Hub login..."
        if echo "$DOCKER_HUB_PASSWORD" | docker login -u "$DOCKER_HUB_USERNAME" --password-stdin docker.io >/dev/null 2>&1; then
            print_success "Docker Hub login successful"
            docker logout docker.io >/dev/null 2>&1
        else
            print_error "Docker Hub login failed. Check your credentials."
        fi
    fi
else
    print_warning "Skipping Docker Hub setup"
fi

echo ""

# Step 2: Quay.io Setup
print_step "Step 2: Quay.io Setup"
echo ""
echo "Please visit: https://quay.io/organization/infrastructure-alexson/robots"
echo ""
echo "Instructions:"
echo "1. Create a new Robot Account"
echo "2. Name it: github-actions"
echo "3. Description: For automated container builds and publishing"
echo "4. Copy the robot account name (format: +infrastructure-alexson+github-actions)"
echo "5. Copy the robot account password"
echo ""

read -p "Have you created your Quay.io robot account? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter your Quay.io robot account name: " QUAY_USERNAME
    read -sp "Enter your Quay.io robot account password: " QUAY_PASSWORD
    echo ""
    
    if [ $DOCKER_AVAILABLE = true ]; then
        print_step "Testing Quay.io login..."
        if echo "$QUAY_PASSWORD" | docker login -u "$QUAY_USERNAME" --password-stdin quay.io >/dev/null 2>&1; then
            print_success "Quay.io login successful"
            docker logout quay.io >/dev/null 2>&1
        else
            print_error "Quay.io login failed. Check your credentials."
        fi
    fi
else
    print_warning "Skipping Quay.io setup"
fi

echo ""

# Step 3: GitHub Secrets Configuration
print_step "Step 3: Configure GitHub Secrets"
echo ""
echo "Now you need to add these secrets to your GitHub repository:"
echo ""
echo "Repository: infrastructure-alexson/ldap-web-manager"
echo "Location: Settings → Secrets and variables → Actions"
echo ""
echo "Secrets to add:"
echo "  1. DOCKER_HUB_USERNAME = $DOCKER_HUB_USERNAME"
echo "  2. DOCKER_HUB_PASSWORD = (your access token)"
echo "  3. QUAY_USERNAME = $QUAY_USERNAME"
echo "  4. QUAY_PASSWORD = (your robot password)"
echo ""
echo "Variables to add:"
echo "  1. QUAY_ORG = infrastructure-alexson"
echo ""

read -p "Do you want to open GitHub Secrets page now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    open_url "https://github.com/infrastructure-alexson/ldap-web-manager/settings/secrets/actions"
    echo "Opening GitHub Secrets page..."
    echo "Please add the secrets manually."
fi

echo ""

# Step 4: GitHub Actions Setup
print_step "Step 4: GitHub Actions Workflow"
echo ""
echo "The container publishing workflow is configured at:"
echo ".github/workflows/publish-containers.yml"
echo ""
echo "Features:"
echo "  ✓ Multi-architecture builds (amd64, arm64)"
echo "  ✓ Publishes to Docker Hub, Quay.io, GHCR"
echo "  ✓ Vulnerability scanning with Trivy"
echo "  ✓ Automatic version tagging"
echo "  ✓ Security scanning integration"
echo ""

# Step 5: Test the workflow
print_step "Step 5: Test the Workflow"
echo ""
echo "To test the container publishing workflow:"
echo ""
echo "Option 1: Create a release tag"
echo "  git tag -a v2.2.0-test -m 'Test release'"
echo "  git push origin v2.2.0-test"
echo ""
echo "Option 2: Manual trigger"
echo "  Go to: https://github.com/infrastructure-alexson/ldap-web-manager/actions"
echo "  Select: Publish Container Images"
echo "  Click: Run workflow"
echo ""

# Summary
echo ""
print_step "Setup Summary"
echo ""
echo "Registries configured:"
if [ ! -z "$DOCKER_HUB_USERNAME" ]; then
    print_success "Docker Hub (infrastructure-alexson)"
fi
if [ ! -z "$QUAY_USERNAME" ]; then
    print_success "Quay.io (infrastructure-alexson)"
fi
print_success "GitHub Container Registry (automatic)"
echo ""

print_step "Next Steps:"
echo ""
echo "1. Add GitHub Secrets (see instructions above)"
echo "2. Test the workflow with a release tag"
echo "3. Verify images appear in all registries"
echo "4. Monitor vulnerability scans"
echo ""

print_success "Setup script completed!"
echo ""
echo "For more information, see:"
echo "  doc/CONTAINER-REGISTRY-SETUP.md"
echo "  .github/SECRETS.md"
echo ""

