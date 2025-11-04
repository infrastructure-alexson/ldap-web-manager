# External Reverse Proxy Configuration

**Last Updated**: 2025-11-03  
**Purpose**: Guide for deploying LDAP Web Manager behind an external NGINX reverse proxy

---

## Overview

This guide covers how to configure LDAP Web Manager when deployed behind an external NGINX reverse proxy that handles SSL/TLS termination.

### Architecture

```
[Client] --HTTPS--> [External NGINX (SSL)] --HTTP--> [LDAP Manager NGINX] --HTTP--> [FastAPI Backend]
```

**External NGINX**: 
- SSL/TLS termination
- Optional: Load balancing, WAF, rate limiting
- Forwards requests to internal LDAP Manager NGINX

**Internal LDAP Manager NGINX**:
- Serves React frontend static files
- Proxies API requests to FastAPI backend
- No SSL configuration needed

---

## Configuration Changes Needed

### 1. Modified Internal NGINX Configuration

Create a new configuration for internal use without SSL:

**File**: `nginx/sites-available/ldap-manager-internal.conf`

```nginx
# NGINX Configuration for LDAP Web Manager (Behind Reverse Proxy)
# Location: /etc/nginx/sites-available/ldap-manager-internal.conf

# Upstream FastAPI backend
upstream ldap_manager_backend {
    server 127.0.0.1:8000 fail_timeout=5s max_fails=3;
    keepalive 32;
}

# HTTP server (behind reverse proxy)
server {
    listen 8080;  # Internal port, not exposed externally
    listen [::]:8080;
    server_name ldap-manager.eh168.alexson.org;
    
    # Trust X-Forwarded headers from reverse proxy
    set_real_ip_from 192.168.1.0/24;  # Adjust to your reverse proxy IP range
    set_real_ip_from 10.0.0.0/8;      # If using internal network
    real_ip_header X-Forwarded-For;
    real_ip_recursive on;
    
    # Root directory for static files (React build)
    root /var/www/ldap-manager;
    index index.html;
    
    # Logging with real client IP
    log_format proxy_log '$remote_addr - $remote_user [$time_local] '
                        '"$request" $status $body_bytes_sent '
                        '"$http_referer" "$http_user_agent" '
                        'rt=$request_time upstream=$upstream_addr '
                        'upstream_status=$upstream_status '
                        'real_ip=$http_x_forwarded_for';
    
    access_log /var/log/nginx/ldap-manager-access.log proxy_log;
    error_log /var/log/nginx/ldap-manager-error.log warn;
    
    # Client settings
    client_max_body_size 10M;
    client_body_timeout 30s;
    client_header_timeout 30s;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/javascript
        text/xml
        text/comma-separated-values
        application/json
        application/javascript
        application/x-javascript
        application/atom+xml
        application/rss+xml
        application/vnd.ms-fontobject
        application/x-font-ttf
        application/x-font-opentype
        application/x-font-truetype
        image/svg+xml
        image/x-icon
        application/xml
        font/eot
        font/opentype
        font/otf;
    
    # Health check endpoint (for reverse proxy)
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
    
    # API Backend
    location /api/ {
        proxy_pass http://ldap_manager_backend;
        
        # Preserve original request details
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $http_x_forwarded_proto;
        proxy_set_header X-Forwarded-Host $http_x_forwarded_host;
        proxy_set_header X-Forwarded-Port $http_x_forwarded_port;
        
        # WebSocket support (for future real-time features)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;
        
        # Error handling
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503;
        proxy_next_upstream_tries 2;
    }
    
    # Docs (Swagger/ReDoc)
    location ~ ^/(docs|redoc|openapi.json) {
        proxy_pass http://ldap_manager_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $http_x_forwarded_proto;
    }
    
    # Static files (React SPA)
    location / {
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            access_log off;
        }
        
        # Don't cache index.html
        location = /index.html {
            add_header Cache-Control "no-cache, no-store, must-revalidate";
            add_header Pragma "no-cache";
            add_header Expires "0";
        }
    }
}
```

---

### 2. External Reverse Proxy Configuration

**File**: On your external NGINX server

```nginx
# External Reverse Proxy for LDAP Web Manager
# Handles SSL/TLS termination

upstream ldap_manager_internal {
    server 192.168.1.10:8080;  # Internal LDAP Manager NGINX
    # Add additional servers for load balancing if needed
    # server 192.168.1.11:8080 backup;
    
    keepalive 64;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name ldap-manager.eh168.alexson.org;
    
    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # Redirect all other HTTP traffic to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server (SSL termination)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ldap-manager.eh168.alexson.org;
    
    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/ldap-manager.crt;
    ssl_certificate_key /etc/nginx/ssl/ldap-manager.key;
    
    # SSL Security Settings (Mozilla Modern Configuration)
    ssl_protocols TLSv1.3 TLSv1.2;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;
    
    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/nginx/ssl/ldap-manager-chain.crt;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self';" always;
    
    # Logging
    access_log /var/log/nginx/ldap-manager-proxy-access.log combined;
    error_log /var/log/nginx/ldap-manager-proxy-error.log warn;
    
    # Client settings
    client_max_body_size 10M;
    
    # Health check
    location /health {
        access_log off;
        proxy_pass http://ldap_manager_internal/health;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }
    
    # Proxy all requests to internal NGINX
    location / {
        proxy_pass http://ldap_manager_internal;
        
        # Preserve client information
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffering for better performance
        proxy_buffering on;
        proxy_buffer_size 8k;
        proxy_buffers 16 8k;
        
        # Error pages
        proxy_intercept_errors off;
    }
}

# WebSocket connection upgrade map
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}
```

---

### 3. FastAPI Backend Configuration

Update `backend/app/config.py` to trust proxy headers:

```python
from pydantic import BaseModel
from typing import List

class Settings(BaseModel):
    # ... existing settings ...
    
    # Proxy settings
    trust_proxy_headers: bool = True
    forwarded_allow_ips: str = "*"  # Or specific IP range: "192.168.1.0/24"
    
    # Cookie settings (for sessions behind proxy)
    cookie_secure: bool = True  # Require HTTPS
    cookie_samesite: str = "lax"  # or "strict" for tighter security
```

Update `backend/app/main.py`:

```python
from fastapi import FastAPI
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="LDAP Web Manager",
    # ... other settings ...
)

# Configure for proxy if enabled
if settings.trust_proxy_headers:
    # uvicorn will automatically handle X-Forwarded headers
    # when --forwarded-allow-ips is set
    pass
```

---

### 4. Running Backend with Proxy Support

Update systemd service or run command:

```bash
uvicorn app.main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --forwarded-allow-ips='*' \
    --proxy-headers
```

Or in `backend/app/systemd/ldap-web-manager-backend.service`:

```ini
[Service]
ExecStart=/usr/local/bin/uvicorn app.main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --forwarded-allow-ips='*' \
    --proxy-headers \
    --workers 4
```

---

## Important Considerations

### 1. IP Address Forwarding

**Problem**: Backend sees reverse proxy IP instead of client IP  
**Solution**: Configure `set_real_ip_from` in internal NGINX and `--proxy-headers` in uvicorn

### 2. Cookie Security

**Problem**: Cookies need `Secure` flag when using HTTPS  
**Solution**: Backend must check `X-Forwarded-Proto` header

```python
from fastapi import Request

def is_secure(request: Request) -> bool:
    # Check if behind HTTPS proxy
    proto = request.headers.get("X-Forwarded-Proto", "")
    return proto == "https" or request.url.scheme == "https"

# Use when setting cookies
response.set_cookie(
    key="session",
    value=token,
    secure=is_secure(request),  # Only send over HTTPS
    httponly=True,
    samesite="lax"
)
```

### 3. WebSocket Support

Ensure both proxy layers support WebSocket upgrades (already configured above).

### 4. CORS Configuration

If frontend and backend are on different domains, configure CORS in FastAPI:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ldap-manager.eh168.alexson.org"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 5. Rate Limiting

Implement rate limiting on the external reverse proxy for better control:

```nginx
# In external NGINX http block
limit_req_zone $binary_remote_addr zone=ldap_manager_limit:10m rate=10r/s;

# In server block
location /api/ {
    limit_req zone=ldap_manager_limit burst=20 nodelay;
    # ... rest of proxy config ...
}
```

---

## Testing the Setup

### 1. Test Health Check

```bash
curl https://ldap-manager.eh168.alexson.org/health
# Expected: "healthy"
```

### 2. Test Headers are Forwarded

Check backend logs to verify client IP is correct:

```bash
tail -f /var/log/nginx/ldap-manager-access.log
```

Should show actual client IPs, not proxy IP.

### 3. Test API Endpoints

```bash
curl -H "Content-Type: application/json" \
     https://ldap-manager.eh168.alexson.org/api/auth/login \
     -d '{"username":"admin","password":"password"}'
```

### 4. Test Frontend

Open browser to `https://ldap-manager.eh168.alexson.org` and verify:
- [ ] Page loads correctly
- [ ] API calls work
- [ ] Login functions
- [ ] Browser console shows no CORS errors
- [ ] Cookies are set with `Secure` flag (check DevTools → Application → Cookies)

---

## Troubleshooting

### Issue: API calls return 502 Bad Gateway

**Check**:
1. Internal NGINX is running and listening on port 8080
2. FastAPI backend is running on port 8000
3. Firewall allows traffic from reverse proxy to internal NGINX
4. Health check endpoint works: `curl http://192.168.1.10:8080/health`

### Issue: Client IP shows as proxy IP in logs

**Fix**: Ensure `set_real_ip_from` is configured with correct proxy IP range

### Issue: Cookies not being set

**Fix**: Ensure `X-Forwarded-Proto: https` header is being sent and backend respects it

### Issue: CORS errors

**Fix**: Add CORS middleware in FastAPI with correct origin

### Issue: WebSocket connections fail

**Fix**: Ensure both NGINX layers have `proxy_http_version 1.1` and upgrade headers configured

---

## Security Checklist

When deploying behind a reverse proxy:

- [ ] Internal NGINX only listens on internal IP/port (not 0.0.0.0:80/443)
- [ ] Firewall blocks direct access to internal NGINX from internet
- [ ] `set_real_ip_from` only trusts your specific proxy IP range (not 0.0.0.0/0)
- [ ] SSL/TLS configured on external proxy with strong ciphers
- [ ] HSTS header enabled on external proxy
- [ ] Rate limiting configured on external proxy
- [ ] Backend validates `X-Forwarded-*` headers
- [ ] Cookies use `Secure` and `HttpOnly` flags
- [ ] Security headers (CSP, X-Frame-Options, etc.) configured on external proxy

---

## Benefits of External Reverse Proxy

1. **Centralized SSL Management**: Single place to manage certificates
2. **Load Balancing**: Distribute load across multiple backend instances
3. **WAF Integration**: Add Web Application Firewall protection
4. **Rate Limiting**: Protect backend from abuse
5. **Caching**: Cache static content at edge
6. **DDoS Protection**: Additional layer of protection
7. **Multiple Services**: Route multiple services through single proxy
8. **SSL Offloading**: Reduce CPU load on application servers

---

## Alternative: Direct SSL on Internal NGINX

If you prefer to keep SSL on the internal NGINX (without external proxy), use the original `ldap-manager.conf` configuration unchanged. This is simpler but less flexible for large deployments.

---

**Questions?** See [doc/NGINX-SETUP.md](NGINX-SETUP.md) for general NGINX configuration or open an issue.

---

**Last Updated**: 2025-11-03  
**Version**: 2.0.0  
**Repository**: https://github.com/infrastructure-alexson/ldap-web-manager

