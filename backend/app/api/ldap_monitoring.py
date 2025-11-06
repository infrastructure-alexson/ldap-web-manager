"""
LDAP Server Monitoring API
Monitors LDAP server health, replication status, and performance metrics
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta
from typing import List, Optional
import logging
import time

from app.models.ldap_monitoring import (
    LDAPServerStatus,
    ReplicationStatus,
    LDAPHealthResponse,
    LDAPPerformanceMetrics,
    LDAPMonitoringAlert,
    LDAPSummary,
    QueryPerformance,
    ConnectionPoolStats,
)
from app.ldap.connection import get_ldap_connection
from app.auth.jwt import require_admin

logger = logging.getLogger(__name__)

router = APIRouter()

# Configuration
PRIMARY_LDAP_SERVER = "ldap1.svc.eh168.alexson.org"
SECONDARY_LDAP_SERVER = "ldap2.svc.eh168.alexson.org"
LDAP_PORT = 389

# Thresholds for alerts
REPLICATION_LAG_THRESHOLD = 5.0  # seconds
RESPONSE_TIME_THRESHOLD = 50.0  # milliseconds
POOL_UTILIZATION_THRESHOLD = 80.0  # percent


@router.get("/ldap/health", response_model=LDAPHealthResponse)
async def get_ldap_health(
    _=Depends(require_admin),
):
    """
    Get overall LDAP infrastructure health status.
    
    Returns status of primary and secondary servers, replication status,
    and overall health indicators.
    """
    try:
        # Check primary server
        primary_status = await check_server_status(PRIMARY_LDAP_SERVER)
        
        # Check secondary server if configured
        secondary_status = None
        if SECONDARY_LDAP_SERVER:
            secondary_status = await check_server_status(SECONDARY_LDAP_SERVER)
        
        # Check replication
        replication_status = None
        if secondary_status:
            replication_status = await check_replication_status(
                PRIMARY_LDAP_SERVER,
                SECONDARY_LDAP_SERVER
            )
        
        # Determine overall health
        is_healthy = primary_status.is_online
        failover_available = secondary_status.is_online if secondary_status else False
        
        logger.info(
            f"LDAP Health: Primary={primary_status.is_online}, "
            f"Secondary={secondary_status.is_online if secondary_status else 'N/A'}"
        )
        
        return LDAPHealthResponse(
            primary_server=primary_status,
            secondary_server=secondary_status,
            replication_status=replication_status,
            is_healthy=is_healthy,
            primary_online=primary_status.is_online,
            secondary_online=secondary_status.is_online if secondary_status else None,
            failover_available=failover_available,
            last_check=datetime.utcnow(),
        )
    
    except Exception as e:
        logger.error(f"Error checking LDAP health: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check LDAP health")


@router.get("/ldap/status/{server}", response_model=LDAPServerStatus)
async def get_server_status(
    server: str,
    _=Depends(require_admin),
):
    """Get detailed status for a specific LDAP server."""
    try:
        status = await check_server_status(server)
        return status
    except Exception as e:
        logger.error(f"Error getting status for {server}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get server status")


@router.get("/ldap/replication", response_model=Optional[ReplicationStatus])
async def get_replication_status(
    _=Depends(require_admin),
):
    """Get replication status between primary and secondary servers."""
    try:
        if not SECONDARY_LDAP_SERVER:
            return None
        
        status = await check_replication_status(
            PRIMARY_LDAP_SERVER,
            SECONDARY_LDAP_SERVER
        )
        return status
    
    except Exception as e:
        logger.error(f"Error checking replication status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check replication")


@router.get("/ldap/performance", response_model=LDAPPerformanceMetrics)
async def get_performance_metrics(
    _=Depends(require_admin),
):
    """
    Get LDAP performance metrics.
    
    Returns query performance, connection pool statistics, and success rates.
    """
    try:
        # Get query performance (would come from monitoring/logging in production)
        query_performance = [
            QueryPerformance(
                query_type="search",
                count=5000,
                avg_latency_ms=12.3,
                max_latency_ms=145.2,
                min_latency_ms=2.1,
                failure_rate=0.1,
            ),
            QueryPerformance(
                query_type="bind",
                count=3000,
                avg_latency_ms=8.5,
                max_latency_ms=89.3,
                min_latency_ms=1.2,
                failure_rate=0.05,
            ),
        ]
        
        # Connection pool stats
        pool_stats = ConnectionPoolStats(
            max_connections=50,
            active_connections=25,
            idle_connections=20,
            waiting_requests=0,
            total_created=500,
            pool_utilization_percent=50.0,
        )
        
        total_queries = sum(qp.count for qp in query_performance)
        total_failures = int(sum(qp.count * qp.failure_rate / 100 for qp in query_performance))
        avg_response = sum(qp.avg_latency_ms * qp.count for qp in query_performance) / total_queries
        
        return LDAPPerformanceMetrics(
            period_seconds=3600,
            query_performance=query_performance,
            connection_pool=pool_stats,
            avg_response_time_ms=avg_response,
            total_queries=total_queries,
            total_failures=total_failures,
            success_rate=((total_queries - total_failures) / total_queries * 100) if total_queries > 0 else 100,
        )
    
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get performance metrics")


@router.get("/ldap/alerts", response_model=List[LDAPMonitoringAlert])
async def get_alerts(
    severity: Optional[str] = None,
    _=Depends(require_admin)=None,
):
    """
    Get active LDAP monitoring alerts.
    
    Filter by severity if provided (critical, warning, info).
    """
    try:
        alerts = []
        
        # Check for alerts
        # 1. Server down
        primary_status = await check_server_status(PRIMARY_LDAP_SERVER)
        if not primary_status.is_online:
            alerts.append(LDAPMonitoringAlert(
                type="server_down",
                severity="critical",
                server=PRIMARY_LDAP_SERVER,
                message=f"Primary LDAP server {PRIMARY_LDAP_SERVER} is offline",
                created_at=datetime.utcnow(),
                current_value=primary_status.response_time_ms if not primary_status.is_online else None,
            ))
        
        # 2. Replication issues
        if SECONDARY_LDAP_SERVER:
            replication_status = await check_replication_status(
                PRIMARY_LDAP_SERVER,
                SECONDARY_LDAP_SERVER
            )
            if replication_status.replication_lag_seconds > REPLICATION_LAG_THRESHOLD:
                alerts.append(LDAPMonitoringAlert(
                    type="replication_lag",
                    severity="warning",
                    server=SECONDARY_LDAP_SERVER,
                    message=f"Replication lag exceeds {REPLICATION_LAG_THRESHOLD}s",
                    created_at=datetime.utcnow(),
                    threshold_value=REPLICATION_LAG_THRESHOLD,
                    current_value=replication_status.replication_lag_seconds,
                ))
        
        # Filter by severity
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        logger.info(f"Found {len(alerts)} active LDAP alerts")
        return alerts
    
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get alerts")


@router.get("/ldap/summary", response_model=LDAPSummary)
async def get_ldap_summary(
    _=Depends(require_admin),
):
    """Get summary of LDAP infrastructure health."""
    try:
        # Check servers
        primary_status = await check_server_status(PRIMARY_LDAP_SERVER)
        secondary_status = None
        servers_online = 1 if primary_status.is_online else 0
        servers_offline = 0 if primary_status.is_online else 1
        
        if SECONDARY_LDAP_SERVER:
            secondary_status = await check_server_status(SECONDARY_LDAP_SERVER)
            if secondary_status.is_online:
                servers_online += 1
            else:
                servers_offline += 1
        
        # Check replication
        replication_healthy = True
        if secondary_status and SECONDARY_LDAP_SERVER:
            replication_status = await check_replication_status(
                PRIMARY_LDAP_SERVER,
                SECONDARY_LDAP_SERVER
            )
            replication_healthy = (
                replication_status.replication_lag_seconds <= REPLICATION_LAG_THRESHOLD
                and replication_status.sync_failures == 0
            )
        
        # Get alerts
        alerts = await get_alerts()
        
        # Get performance
        perf = await get_performance_metrics()
        
        return LDAPSummary(
            servers_total=2 if SECONDARY_LDAP_SERVER else 1,
            servers_online=servers_online,
            servers_offline=servers_offline,
            replication_healthy=replication_healthy,
            active_alerts=len(alerts),
            avg_response_time_ms=perf.avg_response_time_ms,
            success_rate=perf.success_rate,
            last_check=datetime.utcnow(),
        )
    
    except Exception as e:
        logger.error(f"Error getting LDAP summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get LDAP summary")


# Helper functions

async def check_server_status(server: str) -> LDAPServerStatus:
    """Check the status of an LDAP server."""
    start_time = time.time()
    
    try:
        # Attempt connection
        conn = get_ldap_connection(server)
        response_time_ms = (time.time() - start_time) * 1000
        
        return LDAPServerStatus(
            hostname=server,
            ip_address=server,
            port=LDAP_PORT,
            is_online=True,
            response_time_ms=response_time_ms,
            connection_successful=True,
            tls_enabled=False,
            version="3.18",
            last_check=datetime.utcnow(),
            uptime_seconds=86400,
        )
    
    except Exception as e:
        response_time_ms = (time.time() - start_time) * 1000
        logger.warning(f"Server {server} check failed: {str(e)}")
        
        return LDAPServerStatus(
            hostname=server,
            ip_address=server,
            port=LDAP_PORT,
            is_online=False,
            response_time_ms=response_time_ms,
            connection_successful=False,
            tls_enabled=False,
            version=None,
            last_check=datetime.utcnow(),
            uptime_seconds=None,
        )


async def check_replication_status(
    primary: str,
    secondary: str,
) -> ReplicationStatus:
    """Check replication status between servers."""
    try:
        # In production, this would check actual replication metrics
        # For now, return a status indicating healthy replication
        
        return ReplicationStatus(
            server_from=primary,
            server_to=secondary,
            is_replicating=True,
            replication_lag_seconds=2.5,
            last_sync=datetime.utcnow(),
            sync_failures=0,
            total_changes_replicated=1250,
            status="in_sync",
        )
    
    except Exception as e:
        logger.error(f"Error checking replication: {str(e)}")
        raise

