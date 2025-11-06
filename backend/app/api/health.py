#!/usr/bin/env python3
"""
Health Check Endpoints

Provides Kubernetes-compatible liveness, readiness, and startup probes.
Also includes detailed health status information.
"""

from fastapi import APIRouter, HTTPException, status
from datetime import datetime
import logging
from typing import Dict, Any

from app.config import get_config
from app.ldap.connection import get_ldap_connection
import ldap

logger = logging.getLogger(__name__)

router = APIRouter()

# Global startup time
_startup_time = datetime.utcnow()


@router.get("/health", tags=["Health"])
async def health():
    """
    Basic health check endpoint.
    Returns 200 if service is running.
    
    Used for: General health monitoring
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.2.0"
    }


@router.get("/health/live", tags=["Health"])
async def health_live():
    """
    Liveness probe endpoint.
    Returns 200 if service is alive and responsive.
    
    Kubernetes uses this to determine if the pod should be restarted.
    This should return quickly and only check if the service itself is running.
    """
    try:
        return {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": (datetime.utcnow() - _startup_time).total_seconds()
        }
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not alive"
        )


@router.get("/health/ready", tags=["Health"])
async def health_ready():
    """
    Readiness probe endpoint.
    Returns 200 only if service is ready to accept traffic.
    
    Kubernetes uses this to determine if the pod should receive traffic.
    Checks all critical dependencies.
    """
    checks = {
        "database": await check_database(),
        "ldap": await check_ldap(),
        "config": await check_config()
    }
    
    all_ready = all(check["status"] == "ready" for check in checks.values())
    
    if not all_ready:
        logger.warning(f"Readiness check failed: {checks}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready",
            headers={"X-Health-Check": "ready"}
        )
    
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }


@router.get("/health/startup", tags=["Health"])
async def health_startup():
    """
    Startup probe endpoint.
    Returns 200 once the service has completed startup.
    
    Kubernetes uses this to know when to start checking liveness probe.
    Used for services that need time to initialize.
    """
    checks = {
        "database": await check_database(),
        "ldap": await check_ldap(),
        "config": await check_config()
    }
    
    all_started = all(check["status"] in ["ready", "ready_with_warnings"] for check in checks.values())
    
    if not all_started:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not started"
        )
    
    return {
        "status": "started",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }


@router.get("/health/detailed", tags=["Health"])
async def health_detailed():
    """
    Detailed health status endpoint.
    Returns comprehensive information about service status.
    
    Useful for: Monitoring dashboards, troubleshooting, detailed health reports
    """
    try:
        db_check = await check_database()
        ldap_check = await check_ldap()
        config_check = await check_config()
        
        overall_status = "healthy"
        if any(check["status"] == "unhealthy" for check in [db_check, ldap_check, config_check]):
            overall_status = "unhealthy"
        elif any(check["status"] == "degraded" for check in [db_check, ldap_check, config_check]):
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": (datetime.utcnow() - _startup_time).total_seconds(),
            "version": "2.2.0",
            "checks": {
                "database": db_check,
                "ldap": ldap_check,
                "config": config_check
            },
            "services": {
                "api": {
                    "status": "running",
                    "port": 8000
                },
                "frontend": {
                    "status": "running",
                    "port": 8080
                }
            }
        }
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )


# Health Check Helper Functions

async def check_database() -> Dict[str, Any]:
    """
    Check database connectivity and health.
    """
    try:
        from sqlalchemy import text
        from app.db.base import get_session
        
        # Try to get a session and execute a simple query
        async with get_session() as session:
            await session.execute(text("SELECT 1"))
            return {
                "status": "ready",
                "message": "Database connected",
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }


async def check_ldap() -> Dict[str, Any]:
    """
    Check LDAP server connectivity.
    """
    try:
        config = get_config()
        ldap_conn = get_ldap_connection()
        
        # Try to bind to LDAP
        if ldap_conn:
            # Simple search to verify connection
            result = ldap_conn.search_s(
                config.ldap_base_dn,
                ldap.SCOPE_BASE,
                "(objectClass=*)",
                attributes=["*"]
            )
            if result is not None:
                return {
                    "status": "ready",
                    "message": "LDAP connected",
                    "server": config.ldap_server,
                    "timestamp": datetime.utcnow().isoformat()
                }
    except Exception as e:
        logger.warning(f"LDAP health check warning: {e}")
        # LDAP being unavailable might not be critical
        return {
            "status": "degraded",
            "message": f"LDAP connection issue: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    return {
        "status": "degraded",
        "message": "LDAP health check inconclusive",
        "timestamp": datetime.utcnow().isoformat()
    }


async def check_config() -> Dict[str, Any]:
    """
    Check application configuration validity.
    """
    try:
        config = get_config()
        
        # Verify critical config values exist
        required_configs = {
            "ldap_server": config.ldap_server,
            "ldap_base_dn": config.ldap_base_dn,
            "jwt_secret": config.jwt_secret,
            "database_url": config.database_url
        }
        
        missing = [k for k, v in required_configs.items() if not v]
        
        if missing:
            return {
                "status": "unhealthy",
                "message": f"Missing configuration: {', '.join(missing)}",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return {
            "status": "ready",
            "message": "Configuration valid",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Config health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Configuration check failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }

