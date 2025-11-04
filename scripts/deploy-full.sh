#!/bin/bash
#
# deploy-full.sh - Complete deployment script for LDAP Web Manager
#
# This script performs a full deployment of the LDAP Web Manager application
# including frontend build, backend setup, and NGINX configuration.
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Helper functions
print_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_header() {
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "This script must be run as root"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

print_header "LDAP Web Manager - Full Deployment"
echo ""

# Step 1: Check prerequisites
print_header "Step 1/7: Checking Prerequisites"
echo ""

check_command() {
    if command -v "$1" &> /dev/null; then
        print_success "$1 is installed"
        return 0
    else
        print_error "$1 is not installed"
        return 1
    fi
}

PREREQS_OK=true
check_command "python3" || PREREQS_OK=false
check_command "pip3" || PREREQS_OK=false
check_command "node" || PREREQS_OK=false
check_command "npm" || PREREQS_OK=false
check_command "nginx" || PREREQS_OK=false

if [ "$PREREQS_OK" = false ]; then
    print_error "Missing prerequisites. Please install required software."
    echo ""
    print_info "Install commands for Rocky Linux 8:"
    echo "  sudo dnf install -y python39 python39-pip"
    echo "  curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -"
    echo "  sudo dnf install -y nodejs nginx"
    exit 1
fi

echo ""

# Step 2: Check configuration
print_header "Step 2/7: Checking Configuration"
echo ""

CONFIG_FILE="${PROJECT_ROOT}/config/app-config.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    print_warning "Configuration file not found: $CONFIG_FILE"
    print_info "Copying example configuration..."
    cp "${PROJECT_ROOT}/config/app-config.example.yaml" "$CONFIG_FILE"
    print_warning "Please edit $CONFIG_FILE with your settings before continuing"
    exit 1
fi

print_success "Configuration file found"
echo ""

# Step 3: Setup backend
print_header "Step 3/7: Setting Up Backend"
echo ""

cd "${PROJECT_ROOT}/backend"

print_info "Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_info "Virtual environment already exists"
fi

print_info "Activating virtual environment..."
source venv/bin/activate

print_info "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
print_success "Python dependencies installed"

echo ""

# Step 4: Build frontend
print_header "Step 4/7: Building Frontend"
echo ""

cd "${PROJECT_ROOT}/frontend"

print_info "Installing Node.js dependencies..."
npm ci --production=false
print_success "Node.js dependencies installed"

print_info "Building React application..."
npm run build
print_success "Frontend built successfully"

echo ""

# Step 5: Deploy frontend to NGINX
print_header "Step 5/7: Deploying Frontend"
echo ""

NGINX_ROOT="/var/www/ldap-manager"
print_info "Creating NGINX web root: $NGINX_ROOT"
mkdir -p "$NGINX_ROOT"

print_info "Copying built files to $NGINX_ROOT..."
cp -r "${PROJECT_ROOT}/frontend/dist/"* "$NGINX_ROOT/"
chown -R nginx:nginx "$NGINX_ROOT"
chmod -R 755 "$NGINX_ROOT"
print_success "Frontend deployed to NGINX"

echo ""

# Step 6: Configure NGINX
print_header "Step 6/7: Configuring NGINX"
echo ""

NGINX_CONF="/etc/nginx/sites-available/ldap-manager.conf"
print_info "Installing NGINX configuration..."

# Create sites-available and sites-enabled directories if they don't exist
mkdir -p /etc/nginx/sites-available
mkdir -p /etc/nginx/sites-enabled

# Copy NGINX configuration
cp "${PROJECT_ROOT}/nginx/sites-available/ldap-manager.conf" "$NGINX_CONF"

# Enable site
ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/ldap-manager.conf

# Ensure NGINX includes sites-enabled directory
if ! grep -q "include /etc/nginx/sites-enabled/\*.conf;" /etc/nginx/nginx.conf; then
    print_info "Adding sites-enabled include to nginx.conf..."
    sed -i '/http {/a \    include /etc/nginx/sites-enabled/*.conf;' /etc/nginx/nginx.conf
fi

print_info "Testing NGINX configuration..."
if nginx -t; then
    print_success "NGINX configuration is valid"
else
    print_error "NGINX configuration test failed"
    exit 1
fi

echo ""

# Step 7: Setup systemd service for backend
print_header "Step 7/7: Setting Up Backend Service"
echo ""

SYSTEMD_SERVICE="/etc/systemd/system/ldap-web-manager.service"
print_info "Creating systemd service..."

cat > "$SYSTEMD_SERVICE" <<EOF
[Unit]
Description=LDAP Web Manager API Backend
After=network.target

[Service]
Type=simple
User=nginx
Group=nginx
WorkingDirectory=${PROJECT_ROOT}/backend
Environment="PATH=${PROJECT_ROOT}/backend/venv/bin"
EnvironmentFile=${PROJECT_ROOT}/config/app-config.yaml
ExecStart=${PROJECT_ROOT}/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

print_success "Systemd service created"

print_info "Reloading systemd daemon..."
systemctl daemon-reload

print_info "Enabling ldap-web-manager service..."
systemctl enable ldap-web-manager.service

print_info "Starting ldap-web-manager service..."
systemctl start ldap-web-manager.service

if systemctl is-active --quiet ldap-web-manager.service; then
    print_success "Backend service is running"
else
    print_error "Failed to start backend service"
    journalctl -u ldap-web-manager.service -n 20 --no-pager
    exit 1
fi

echo ""

# Restart NGINX
print_info "Restarting NGINX..."
systemctl restart nginx

if systemctl is-active --quiet nginx; then
    print_success "NGINX is running"
else
    print_error "Failed to start NGINX"
    exit 1
fi

echo ""

# Final summary
print_header "Deployment Complete!"
echo ""
print_success "LDAP Web Manager has been successfully deployed!"
echo ""
print_info "Service Status:"
echo "  - Backend API: $(systemctl is-active ldap-web-manager.service)"
echo "  - NGINX: $(systemctl is-active nginx.service)"
echo ""
print_info "Access Points:"
echo "  - Web Interface: https://ldap-manager.svc.eh168.alexson.org"
echo "  - API Documentation: https://ldap-manager.svc.eh168.alexson.org/docs"
echo "  - API Alternative Docs: https://ldap-manager.svc.eh168.alexson.org/redoc"
echo ""
print_warning "Next Steps:"
echo "  1. Ensure DNS is configured for ldap-manager.svc.eh168.alexson.org"
echo "  2. Install SSL certificates (see doc/NGINX-SETUP.md)"
echo "  3. Review configuration in ${CONFIG_FILE}"
echo "  4. Create admin user account"
echo ""
print_info "Useful Commands:"
echo "  - View backend logs:  journalctl -u ldap-web-manager.service -f"
echo "  - Restart backend:    systemctl restart ldap-web-manager.service"
echo "  - Restart NGINX:      systemctl restart nginx"
echo ""

