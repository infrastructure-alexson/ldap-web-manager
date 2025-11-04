# NGINX Setup Guide for LDAP Web Manager

This guide covers NGINX configuration, SSL/TLS setup, and optimization for LDAP Web Manager.

---

## Table of Contents

- [Basic Configuration](#basic-configuration)
- [SSL/TLS Setup](#ssltls-setup)
- [Security Hardening](#security-hardening)
- [Performance Tuning](#performance-tuning)
- [Troubleshooting](#troubleshooting)

---

## Basic Configuration

The LDAP Web Manager requires NGINX to:
1. Serve static React frontend files
2. Reverse proxy API requests to FastAPI backend (port 8000)
3. Handle SSL/TLS termination
4. Apply security headers

### Configuration File Location

```bash
# Main configuration
/etc/nginx/sites-available/ldap-manager.conf

# Symbolic link (enabled site)
/etc/nginx/sites-enabled/ldap-manager.conf
```

### Verify Configuration

```bash
# Test NGINX configuration
sudo nginx -t

# Reload without downtime
sudo nginx -s reload

# Full restart
sudo systemctl restart nginx
```

---

## SSL/TLS Setup

### Option 1: Let's Encrypt (Recommended for Production)

```bash
# Install Certbot
sudo dnf install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d ldap-manager.svc.eh168.alexson.org

# Verify auto-renewal
sudo certbot renew --dry-run

# Auto-renewal timer
sudo systemctl enable certbot-renew.timer
sudo systemctl start certbot-renew.timer
```

Certbot automatically updates the NGINX configuration with certificate paths.

### Option 2: Commercial Certificate

```bash
# Create certificate directory
sudo mkdir -p /etc/nginx/ssl

# Copy certificate files
sudo cp your-cert.crt /etc/nginx/ssl/ldap-manager.crt
sudo cp your-key.key /etc/nginx/ssl/ldap-manager.key
sudo cp chain.crt /etc/nginx/ssl/ldap-manager-chain.crt

# Set permissions
sudo chmod 600 /etc/nginx/ssl/ldap-manager.key
sudo chmod 644 /etc/nginx/ssl/ldap-manager.crt
sudo chmod 644 /etc/nginx/ssl/ldap-manager-chain.crt
```

Update paths in `/etc/nginx/sites-available/ldap-manager.conf`:

```nginx
ssl_certificate /etc/nginx/ssl/ldap-manager.crt;
ssl_certificate_key /etc/nginx/ssl/ldap-manager.key;
ssl_trusted_certificate /etc/nginx/ssl/ldap-manager-chain.crt;
```

### Option 3: Self-Signed (Development Only)

```bash
# Generate self-signed certificate
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
  -keyout /etc/nginx/ssl/ldap-manager.key \
  -out /etc/nginx/ssl/ldap-manager.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=ldap-manager.svc.eh168.alexson.org"

# Set permissions
sudo chmod 600 /etc/nginx/ssl/ldap-manager.key
sudo chmod 644 /etc/nginx/ssl/ldap-manager.crt
```

> ⚠️ **Warning**: Self-signed certificates will trigger browser warnings. Use only for development/testing.

---

## Security Hardening

### 1. SSL Configuration

Already configured in the provided `ldap-manager.conf`:

```nginx
# Modern SSL configuration (TLS 1.2/1.3 only)
ssl_protocols TLSv1.3 TLSv1.2;
ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:...';
ssl_prefer_server_ciphers on;

# Session settings
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_session_tickets off;

# OCSP Stapling
ssl_stapling on;
ssl_stapling_verify on;
```

### 2. Security Headers

Already configured:

```nginx
# HSTS
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

# Prevent clickjacking
add_header X-Frame-Options "SAMEORIGIN" always;

# Prevent MIME sniffing
add_header X-Content-Type-Options "nosniff" always;

# XSS Protection
add_header X-XSS-Protection "1; mode=block" always;

# Referrer Policy
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# Content Security Policy
add_header Content-Security-Policy "default-src 'self'; ..." always;
```

### 3. Rate Limiting

Add to `ldap-manager.conf`:

```nginx
# Define rate limiting zones (add to http block in main nginx.conf)
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;

# Apply to API endpoints (in server block)
location /api/ {
    limit_req zone=api_limit burst=20 nodelay;
    # ... rest of proxy configuration
}

location /api/auth/login {
    limit_req zone=login_limit burst=2 nodelay;
    # ... rest of proxy configuration
}
```

### 4. Block Common Exploits

```nginx
# Block access to sensitive files
location ~ /\.(git|env|htaccess) {
    deny all;
    return 404;
}

# Block SQL injection attempts
location ~ (\;|'|<|>|select|insert|update|delete|drop|union|concat|--|#) {
    return 403;
}
```

---

## Performance Tuning

### 1. Worker Processes

Edit `/etc/nginx/nginx.conf`:

```nginx
# Set to number of CPU cores
worker_processes auto;

# Maximum connections per worker
events {
    worker_connections 2048;
    use epoll;
}
```

### 2. Buffering and Timeouts

```nginx
# Client settings
client_max_body_size 10M;
client_body_buffer_size 128k;
client_header_buffer_size 1k;
large_client_header_buffers 4 16k;

# Timeouts
client_body_timeout 30s;
client_header_timeout 30s;
keepalive_timeout 65s;
send_timeout 30s;

# Proxy buffering
proxy_buffering on;
proxy_buffer_size 8k;
proxy_buffers 8 8k;
proxy_busy_buffers_size 16k;
```

### 3. Compression

Already configured in `ldap-manager.conf`:

```nginx
gzip on;
gzip_vary on;
gzip_proxied any;
gzip_comp_level 6;
gzip_types text/plain text/css text/javascript application/json ...;
```

### 4. Caching

Add caching for static assets:

```nginx
# Cache configuration
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m
                 max_size=100m inactive=60m use_temp_path=off;

# Apply to API endpoints
location /api/static/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 10m;
    proxy_cache_use_stale error timeout http_500 http_502 http_503;
    add_header X-Cache-Status $upstream_cache_status;
    proxy_pass http://ldap_manager_backend;
}
```

### 5. HTTP/2 and Keep-Alive

```nginx
# Enable HTTP/2
listen 443 ssl http2;

# Backend keep-alive
upstream ldap_manager_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}
```

---

## Monitoring and Logging

### 1. Access Log Format

Custom log format with timing:

```nginx
log_format detailed '$remote_addr - $remote_user [$time_local] '
                    '"$request" $status $body_bytes_sent '
                    '"$http_referer" "$http_user_agent" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

access_log /var/log/nginx/ldap-manager-access.log detailed;
```

### 2. Log Rotation

NGINX logs are automatically rotated by logrotate:

```bash
# Check logrotate configuration
cat /etc/logrotate.d/nginx

# Manual rotation test
sudo logrotate -f /etc/logrotate.d/nginx
```

### 3. Real-Time Monitoring

```bash
# Watch access log
sudo tail -f /var/log/nginx/ldap-manager-access.log

# Watch error log
sudo tail -f /var/log/nginx/ldap-manager-error.log

# Monitor NGINX status (if enabled)
curl http://localhost/nginx_status
```

---

## Troubleshooting

### Common Issues

#### 1. 502 Bad Gateway

Backend not running or unreachable:

```bash
# Check backend is running
sudo systemctl status ldap-web-manager.service

# Check backend is listening on port 8000
sudo netstat -tulpn | grep 8000

# Test backend directly
curl http://localhost:8000/api/health
```

#### 2. 403 Forbidden

Permission issues:

```bash
# Check file permissions
ls -Z /var/www/ldap-manager/

# Fix permissions
sudo chown -R nginx:nginx /var/www/ldap-manager
sudo chmod -R 755 /var/www/ldap-manager

# Fix SELinux context
sudo restorecon -Rv /var/www/ldap-manager
```

#### 3. SSL Certificate Errors

```bash
# Test SSL configuration
openssl s_client -connect ldap-manager.svc.eh168.alexson.org:443 -servername ldap-manager.svc.eh168.alexson.org

# Check certificate expiration
echo | openssl s_client -servername ldap-manager.svc.eh168.alexson.org \
  -connect ldap-manager.svc.eh168.alexson.org:443 2>/dev/null | \
  openssl x509 -noout -dates
```

#### 4. Configuration Test Fails

```bash
# Test configuration
sudo nginx -t

# Check for syntax errors
sudo nginx -T | less

# Verify includes
grep -r "include" /etc/nginx/nginx.conf
```

### Debug Mode

Enable debug logging temporarily:

```nginx
error_log /var/log/nginx/ldap-manager-error.log debug;
```

Don't forget to revert to `warn` or `error` level in production.

---

## Security Best Practices

1. ✅ **Use TLS 1.2/1.3 only** - Disable older protocols
2. ✅ **Enable HSTS** - Force HTTPS
3. ✅ **Keep certificates up to date** - Monitor expiration
4. ✅ **Apply security headers** - Prevent common attacks
5. ✅ **Rate limit API endpoints** - Prevent abuse
6. ✅ **Monitor logs** - Watch for suspicious activity
7. ✅ **Keep NGINX updated** - Apply security patches
8. ✅ **Use strong ciphers** - Follow Mozilla SSL Configuration Generator
9. ✅ **Disable unused modules** - Minimize attack surface
10. ✅ **Regular security audits** - Test with tools like SSL Labs

---

## Performance Checklist

- [ ] Worker processes set to number of CPU cores
- [ ] HTTP/2 enabled
- [ ] Gzip compression enabled
- [ ] Static asset caching configured
- [ ] Keep-alive connections enabled
- [ ] Appropriate buffer sizes set
- [ ] Access log sampling (if high traffic)
- [ ] CDN considered for static assets (if public)

---

## Useful Commands

```bash
# Reload configuration
sudo nginx -s reload

# Test configuration
sudo nginx -t

# View running configuration
sudo nginx -T

# Check NGINX version
nginx -v

# Check modules
nginx -V

# Restart NGINX
sudo systemctl restart nginx

# View logs
sudo journalctl -u nginx -f
```

---

**Related**: See [INSTALLATION.md](INSTALLATION.md) for complete deployment instructions

---

**LDAP Web Manager NGINX Setup Guide**  
**Version**: 2.0.0  
**Last Updated**: 2025-11-03  
**Repository**: https://github.com/infrastructure-alexson/ldap-web-manager
