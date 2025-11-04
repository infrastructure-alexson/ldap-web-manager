# LDAP Web Manager - Installation Guide

Complete step-by-step installation guide for deploying LDAP Web Manager on Rocky Linux 8.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Automated Installation](#automated-installation)
- [Manual Installation](#manual-installation)
- [Post-Installation](#post-installation)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### 1. System Requirements

- **Operating System**: Rocky Linux 8 (or RHEL 8/CentOS 8)
- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 20GB available space
- **Network**: Access to 389 DS LDAP servers

### 2. Required Software

```bash
# Update system
sudo dnf update -y

# Install EPEL repository
sudo dnf install -y epel-release

# Install Python 3.9+
sudo dnf install -y python39 python39-pip python39-devel

# Install Node.js 18.x
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo dnf install -y nodejs

# Install NGINX
sudo dnf install -y nginx

# Install development tools
sudo dnf groupinstall -y "Development Tools"
sudo dnf install -y openldap-devel gcc
```

### 3. LDAP Service Account

Create a dedicated service account in 389 DS:

```bash
# Create service account LDIF
cat > webmanager-account.ldif <<EOF
dn: cn=webmanager,ou=ServiceAccounts,dc=eh168,dc=alexson,dc=org
objectClass: simpleSecurityObject
objectClass: organizationalRole
cn: webmanager
description: Service account for LDAP Web Manager application
userPassword: {SSHA}YOUR_GENERATED_PASSWORD_HASH
EOF

# Add to LDAP
ldapadd -x -H ldaps://ldap1.svc.eh168.alexson.org:636 \
  -D "cn=Directory Manager" -W \
  -f webmanager-account.ldif
```

**Grant Permissions**:

The `webmanager` account needs read/write access to:
- `ou=People` (users)
- `ou=Groups` (groups)
- `ou=DNS,ou=Services` (DNS zones/records)
- `ou=DHCP,ou=Services` (DHCP configuration)

```bash
# Grant access using 389 DS console or CLI
dsconf ldap1.svc.eh168.alexson.org backend suffix modify \
  --aci-add "(target=\"ldap:///ou=People,dc=eh168,dc=alexson,dc=org\")\
(targetattr=\"*\")\
(version 3.0; acl \"webmanager access\"; \
allow (read,write,search,compare) \
userdn=\"ldap:///cn=webmanager,ou=ServiceAccounts,dc=eh168,dc=alexson,dc=org\";)"
```

### 4. Firewall Configuration

```bash
# Open HTTP and HTTPS ports
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 5. SELinux Configuration

```bash
# Allow NGINX to make network connections (for reverse proxy)
sudo setsebool -P httpd_can_network_connect 1

# Allow NGINX to read custom web content
sudo chcon -R -t httpd_sys_content_t /var/www/ldap-manager
```

---

## Automated Installation

### Quick Deploy

```bash
# Clone repository
git clone https://github.com/infrastructure-alexson/ldap-web-manager.git
cd ldap-web-manager

# Copy and edit configuration
cp config/app-config.example.yaml config/app-config.yaml
nano config/app-config.yaml  # Edit LDAP settings

# Set environment variables
export LDAP_WEBMANAGER_PASSWORD="your_service_account_password"
export JWT_SECRET=$(openssl rand -hex 32)
export SECRET_KEY=$(openssl rand -hex 32)

# Run deployment script
sudo ./scripts/deploy-full.sh
```

The automated script will:
1. ✅ Check prerequisites
2. ✅ Validate configuration
3. ✅ Setup Python backend with virtual environment
4. ✅ Build React frontend
5. ✅ Deploy to NGINX
6. ✅ Configure and start systemd services
7. ✅ Restart NGINX

---

## Manual Installation

### Step 1: Clone Repository

```bash
cd /opt
sudo git clone https://github.com/infrastructure-alexson/ldap-web-manager.git
cd ldap-web-manager
```

### Step 2: Configure Application

```bash
# Copy example configuration
sudo cp config/app-config.example.yaml config/app-config.yaml

# Edit configuration
sudo nano config/app-config.yaml
```

**Key settings to configure**:
- `ldap.servers.primary` - Primary LDAP server
- `ldap.servers.secondary` - Secondary LDAP server
- `ldap.bind_dn` - Service account DN
- `ldap.bind_password` - Use environment variable
- All organizational unit paths

### Step 3: Setup Backend

```bash
cd /opt/ldap-web-manager/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Build Frontend

```bash
cd /opt/ldap-web-manager/frontend

# Install dependencies
npm ci --production=false

# Build production bundle
npm run build
```

### Step 5: Deploy Frontend to NGINX

```bash
# Create web root
sudo mkdir -p /var/www/ldap-manager

# Copy built files
sudo cp -r /opt/ldap-web-manager/frontend/dist/* /var/www/ldap-manager/

# Set permissions
sudo chown -R nginx:nginx /var/www/ldap-manager
sudo chmod -R 755 /var/www/ldap-manager

# Set SELinux context
sudo chcon -R -t httpd_sys_content_t /var/www/ldap-manager
```

### Step 6: Configure NGINX

```bash
# Copy NGINX configuration
sudo cp /opt/ldap-web-manager/nginx/sites-available/ldap-manager.conf \
  /etc/nginx/sites-available/

# Create sites-enabled directory if needed
sudo mkdir -p /etc/nginx/sites-enabled

# Enable site
sudo ln -sf /etc/nginx/sites-available/ldap-manager.conf \
  /etc/nginx/sites-enabled/

# Update main nginx.conf to include sites-enabled
sudo nano /etc/nginx/nginx.conf
# Add inside http block:
#   include /etc/nginx/sites-enabled/*.conf;

# Test configuration
sudo nginx -t

# Restart NGINX
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### Step 7: Setup Backend Service

```bash
# Create systemd service
sudo cat > /etc/systemd/system/ldap-web-manager.service <<'EOF'
[Unit]
Description=LDAP Web Manager API Backend
After=network.target

[Service]
Type=simple
User=nginx
Group=nginx
WorkingDirectory=/opt/ldap-web-manager/backend
Environment="PATH=/opt/ldap-web-manager/backend/venv/bin"
EnvironmentFile=/opt/ldap-web-manager/config/environment
ExecStart=/opt/ldap-web-manager/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create environment file for secrets
sudo cat > /opt/ldap-web-manager/config/environment <<EOF
LDAP_WEBMANAGER_PASSWORD=your_password_here
JWT_SECRET=$(openssl rand -hex 32)
SECRET_KEY=$(openssl rand -hex 32)
EOF

sudo chmod 600 /opt/ldap-web-manager/config/environment

# Start and enable service
sudo systemctl daemon-reload
sudo systemctl enable ldap-web-manager.service
sudo systemctl start ldap-web-manager.service

# Check status
sudo systemctl status ldap-web-manager.service
```

---

## Post-Installation

### 1. Install SSL Certificates

**Option A: Let's Encrypt (Recommended)**

```bash
# Install Certbot
sudo dnf install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d ldap-manager.eh168.alexson.org

# Auto-renewal is configured automatically
```

**Option B: Self-Signed (Development)**

```bash
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/ldap-manager.key \
  -out /etc/nginx/ssl/ldap-manager.crt
```

Update certificate paths in `/etc/nginx/sites-available/ldap-manager.conf`.

### 2. Configure DNS

Add DNS A record for your hostname:

```
ldap-manager.eh168.alexson.org  A  <YOUR_SERVER_IP>
```

### 3. Create Admin User

```bash
# Connect to LDAP and create admin user
# This user will have admin role in the web interface
```

### 4. Verify Installation

```bash
# Check backend health
curl http://localhost:8000/api/health

# Check NGINX
curl -I http://localhost/

# Check full stack
curl -k https://ldap-manager.eh168.alexson.org/api/version
```

### 5. Access Web Interface

Navigate to: `https://ldap-manager.eh168.alexson.org`

Default login: Use your LDAP admin credentials

---

## Troubleshooting

### Backend Not Starting

```bash
# Check logs
sudo journalctl -u ldap-web-manager.service -f

# Check if port 8000 is in use
sudo netstat -tulpn | grep 8000

# Test backend manually
cd /opt/ldap-web-manager/backend
source venv/bin/activate
python app/main.py
```

### NGINX Errors

```bash
# Check NGINX error log
sudo tail -f /var/log/nginx/ldap-manager-error.log

# Test configuration
sudo nginx -t

# Check NGINX is running
sudo systemctl status nginx
```

### LDAP Connection Errors

```bash
# Test LDAP connection
ldapsearch -x -H ldaps://ldap1.svc.eh168.alexson.org:636 \
  -D "cn=webmanager,ou=ServiceAccounts,dc=eh168,dc=alexson,dc=org" -W \
  -b "dc=eh168,dc=alexson,dc=org" -s base

# Check firewall
sudo firewall-cmd --list-all

# Check SELinux denials
sudo ausearch -m avc -ts recent
```

### Frontend Not Loading

```bash
# Check if files are deployed
ls -la /var/www/ldap-manager/

# Check permissions
ls -Z /var/www/ldap-manager/

# Check NGINX is serving files
curl http://localhost/index.html
```

### Permission Denied Errors

```bash
# Fix file permissions
sudo chown -R nginx:nginx /var/www/ldap-manager
sudo chmod -R 755 /var/www/ldap-manager

# Fix SELinux contexts
sudo restorecon -Rv /var/www/ldap-manager
```

---

## Useful Commands

```bash
# Restart services
sudo systemctl restart ldap-web-manager.service
sudo systemctl restart nginx

# View logs
sudo journalctl -u ldap-web-manager.service -f
sudo tail -f /var/log/nginx/ldap-manager-access.log
sudo tail -f /var/log/nginx/ldap-manager-error.log

# Check service status
sudo systemctl status ldap-web-manager.service
sudo systemctl status nginx

# Update application
cd /opt/ldap-web-manager
sudo git pull
sudo ./scripts/deploy-full.sh
```

---

## Security Checklist

- [ ] SSL/TLS certificates installed
- [ ] Firewall configured (only 80/443 open)
- [ ] SE Linux enabled and properly configured
- [ ] Strong passwords for service accounts
- [ ] JWT secrets generated and secured
- [ ] Regular backups configured
- [ ] Audit logging enabled
- [ ] LDAP connections use LDAPS (not plain LDAP)
- [ ] NGINX security headers configured
- [ ] Rate limiting enabled

---

**Next**: See [NGINX-SETUP.md](NGINX-SETUP.md) for advanced NGINX configuration

---

**LDAP Web Manager Installation Guide**  
**Version**: 2.0.0  
**Last Updated**: November 4, 2025  
**Repository**: https://github.com/infrastructure-alexson/ldap-web-manager
