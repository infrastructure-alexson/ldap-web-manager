"""
LDAP Server Monitoring Models
Pydantic models for LDAP server health, replication, and performance monitoring
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class LDAPServerStatus(BaseModel):
    """Status of a single LDAP server."""
    hostname: str = Field(..., description="LDAP server hostname")
    ip_address: str = Field(..., description="LDAP server IP address")
    port: int = Field(default=389, description="LDAP port")
    is_online: bool = Field(..., description="Is server online and responding")
    response_time_ms: float = Field(..., description="Response time in milliseconds")
    connection_successful: bool = Field(..., description="Could establish connection")
    tls_enabled: bool = Field(default=False, description="TLS/SSL enabled")
    version: Optional[str] = Field(None, description="LDAP server version")
    last_check: datetime = Field(..., description="Last health check timestamp")
    uptime_seconds: Optional[int] = Field(None, description="Server uptime")
    
    class Config:
        schema_extra = {
            "example": {
                "hostname": "ldap1.svc.eh168.alexson.org",
                "ip_address": "192.168.1.1",
                "port": 389,
                "is_online": True,
                "response_time_ms": 45.2,
                "connection_successful": True,
                "tls_enabled": True,
                "version": "3.18",
                "last_check": "2025-11-06T12:00:00",
                "uptime_seconds": 86400,
            }
        }


class ReplicationStatus(BaseModel):
    """Replication status between LDAP servers."""
    server_from: str = Field(..., description="Source server hostname")
    server_to: str = Field(..., description="Target/replica server hostname")
    is_replicating: bool = Field(..., description="Is replication active")
    replication_lag_seconds: float = Field(..., description="Lag in seconds")
    last_sync: datetime = Field(..., description="Last successful sync")
    sync_failures: int = Field(default=0, description="Number of failed syncs")
    total_changes_replicated: int = Field(..., description="Total changes replicated")
    status: str = Field(..., description="Replication status (in_sync, lagging, failed)")
    
    class Config:
        schema_extra = {
            "example": {
                "server_from": "ldap1.svc.eh168.alexson.org",
                "server_to": "ldap2.svc.eh168.alexson.org",
                "is_replicating": True,
                "replication_lag_seconds": 2.5,
                "last_sync": "2025-11-06T12:00:15",
                "sync_failures": 0,
                "total_changes_replicated": 1250,
                "status": "in_sync",
            }
        }


class QueryPerformance(BaseModel):
    """Query performance metrics."""
    query_type: str = Field(..., description="Type of LDAP query (search, bind, modify)")
    count: int = Field(..., description="Number of queries of this type")
    avg_latency_ms: float = Field(..., description="Average latency in ms")
    max_latency_ms: float = Field(..., description="Max latency in ms")
    min_latency_ms: float = Field(..., description="Min latency in ms")
    failure_rate: float = Field(..., description="Failure rate (0-100%)")
    
    class Config:
        schema_extra = {
            "example": {
                "query_type": "search",
                "count": 5000,
                "avg_latency_ms": 12.3,
                "max_latency_ms": 145.2,
                "min_latency_ms": 2.1,
                "failure_rate": 0.1,
            }
        }


class ConnectionPoolStats(BaseModel):
    """Connection pool statistics."""
    max_connections: int = Field(..., description="Maximum pool size")
    active_connections: int = Field(..., description="Currently active connections")
    idle_connections: int = Field(..., description="Idle connections")
    waiting_requests: int = Field(..., description="Requests waiting for connection")
    total_created: int = Field(..., description="Total connections created")
    pool_utilization_percent: float = Field(..., description="Utilization percentage")
    
    class Config:
        schema_extra = {
            "example": {
                "max_connections": 50,
                "active_connections": 25,
                "idle_connections": 20,
                "waiting_requests": 0,
                "total_created": 500,
                "pool_utilization_percent": 50.0,
            }
        }


class LDAPHealthResponse(BaseModel):
    """Overall LDAP server health status."""
    primary_server: LDAPServerStatus
    secondary_server: Optional[LDAPServerStatus] = None
    replication_status: Optional[ReplicationStatus] = None
    is_healthy: bool = Field(..., description="Overall health status")
    primary_online: bool = Field(..., description="Is primary online")
    secondary_online: Optional[bool] = None
    failover_available: bool = Field(..., description="Can failover to secondary")
    last_check: datetime = Field(..., description="Last health check")
    
    class Config:
        schema_extra = {
            "example": {
                "primary_server": {
                    "hostname": "ldap1.svc.eh168.alexson.org",
                    "ip_address": "192.168.1.1",
                    "is_online": True,
                    "response_time_ms": 45.2,
                },
                "is_healthy": True,
                "primary_online": True,
                "failover_available": True,
                "last_check": "2025-11-06T12:00:00",
            }
        }


class LDAPPerformanceMetrics(BaseModel):
    """Comprehensive LDAP performance metrics."""
    period_seconds: int = Field(..., description="Time period for metrics")
    query_performance: List[QueryPerformance] = Field(..., description="Per-query-type performance")
    connection_pool: ConnectionPoolStats = Field(..., description="Connection pool stats")
    avg_response_time_ms: float = Field(..., description="Overall average response time")
    total_queries: int = Field(..., description="Total queries in period")
    total_failures: int = Field(..., description="Total failed queries")
    success_rate: float = Field(..., description="Success rate percentage")
    
    class Config:
        schema_extra = {
            "example": {
                "period_seconds": 3600,
                "query_performance": [],
                "connection_pool": {
                    "max_connections": 50,
                    "active_connections": 25,
                },
                "avg_response_time_ms": 12.5,
                "total_queries": 50000,
                "total_failures": 50,
                "success_rate": 99.9,
            }
        }


class LDAPMonitoringAlert(BaseModel):
    """Alert from LDAP monitoring."""
    type: str = Field(..., description="Alert type (server_down, replication_lag, high_latency, pool_exhaustion)")
    severity: str = Field(..., description="Severity (critical, warning, info)")
    server: str = Field(..., description="Affected server")
    message: str = Field(..., description="Alert message")
    created_at: datetime = Field(..., description="Alert creation timestamp")
    threshold_value: Optional[float] = None
    current_value: Optional[float] = None
    
    class Config:
        schema_extra = {
            "example": {
                "type": "replication_lag",
                "severity": "warning",
                "server": "ldap2.svc.eh168.alexson.org",
                "message": "Replication lag exceeds 5 seconds",
                "created_at": "2025-11-06T12:00:00",
                "threshold_value": 5.0,
                "current_value": 8.2,
            }
        }


class LDAPSummary(BaseModel):
    """Summary of LDAP infrastructure health."""
    servers_total: int = Field(..., description="Total LDAP servers")
    servers_online: int = Field(..., description="Online servers")
    servers_offline: int = Field(..., description="Offline servers")
    replication_healthy: bool = Field(..., description="Replication status")
    active_alerts: int = Field(..., description="Number of active alerts")
    avg_response_time_ms: float = Field(..., description="Average response time")
    success_rate: float = Field(..., description="Overall success rate")
    last_check: datetime = Field(..., description="Last health check")
    
    class Config:
        schema_extra = {
            "example": {
                "servers_total": 2,
                "servers_online": 2,
                "servers_offline": 0,
                "replication_healthy": True,
                "active_alerts": 0,
                "avg_response_time_ms": 45.2,
                "success_rate": 99.9,
                "last_check": "2025-11-06T12:00:00",
            }
        }

