#!/usr/bin/env python3
"""
LDAP Web Manager - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import time
import logging
from pathlib import Path

# Import routers
from app.api import auth, users, groups, dns, dhcp, ipam, service_accounts, audit, bulk
from app.db.base import get_database
from app.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Application metadata
APP_NAME = "LDAP Web Manager"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = """
## LDAP Web Manager API

Comprehensive REST API for managing:
- **Users & Groups**: LDAP user and group management
- **DNS**: BIND 9 zone and record management
- **DHCP**: Kea DHCP subnet and host management
- **IPAM**: IP address management and allocation

### Authentication

All API endpoints require authentication via JWT token:

```bash
curl -X POST https://ldap-manager.svc.eh168.alexson.org/api/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{"username": "admin", "password": "your_password"}'
```

Use the returned token in subsequent requests:

```bash
curl https://ldap-manager.svc.eh168.alexson.org/api/users \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Rate Limiting

- **60 requests per minute** per IP address
- **Burst**: 100 requests
- Rate limit headers included in responses

### Support

- Issues: https://github.com/infrastructure-alexson/ldap-web-manager/issues
- Documentation: https://github.com/infrastructure-alexson/ldap-web-manager
"""

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    
    try:
        logger.info("Initializing database connection...")
        db = await get_database()
        
        # Verify database connection
        if await db.health_check():
            logger.info("Database connection verified")
        else:
            logger.error("Database health check failed")
        
        logger.info("Initializing LDAP connections...")
        # TODO: Initialize LDAP connection pool
        
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    try:
        db = await get_database()
        await db.close()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)
    
    logger.info("Application stopped")


# Create FastAPI application
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ldap-manager.svc.eh168.alexson.org",
        "http://localhost:5173",  # Vite dev server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to responses"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    return response


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle generic exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "message": str(exc) if app.debug else "An error occurred"
        }
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """API root endpoint"""
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "status": "operational",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json"
    }


# Health check endpoint
@app.get("/api/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    
    Returns the health status of the application and its dependencies.
    """
    services = {
        "api": "up",
        "ldap": "unknown",
        "database": "down"
    }
    
    try:
        # Check database connection
        db = await get_database()
        if await db.health_check():
            services["database"] = "up"
        else:
            services["database"] = "down"
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        services["database"] = "error"
    
    # Check LDAP connection (TODO: Implement actual check)
    services["ldap"] = "checking"
    
    # Overall status
    status = "healthy" if services["database"] == "up" else "degraded"
    
    return {
        "status": status,
        "version": APP_VERSION,
        "services": services
    }


# API version info
@app.get("/api/version", tags=["Info"])
async def version_info():
    """Get API version information"""
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "api_version": "v1",
        "python_version": "3.9+"
    }


# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(groups.router, prefix="/api/groups", tags=["Groups"])
app.include_router(service_accounts.router, prefix="/api/service-accounts", tags=["Service Accounts"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit Logs"])
app.include_router(bulk.router, prefix="/api/bulk", tags=["Bulk Operations"])
app.include_router(dns.router, prefix="/api/dns", tags=["DNS"])
app.include_router(dhcp.router, prefix="/api/dhcp", tags=["DHCP"])
app.include_router(ipam.router, prefix="/api/ipam", tags=["IPAM"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Set to False in production
        workers=1,     # Use multiple workers in production
        log_level="info"
    )

