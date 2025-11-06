"""
DHCP Monitoring Models
Pydantic models for DHCP lease monitoring API
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class DHCPLeaseResponse(BaseModel):
    """Response model for a single DHCP lease."""
    ip_address: str = Field(..., description="IP address")
    hostname: str = Field(default="unknown", description="Hostname")
    mac_address: str = Field(..., description="MAC address")
    subnet: str = Field(..., description="Subnet CIDR")
    lease_start: datetime = Field(..., description="Lease start time")
    lease_end: datetime = Field(..., description="Lease end time (expiration)")
    lease_duration_seconds: int = Field(..., description="Total lease duration in seconds")
    status: str = Field(..., description="Lease status (active, expired, reserved, pending)")
    days_remaining: int = Field(..., description="Days until expiration (0 if expired)")
    reserved: bool = Field(default=False, description="Is this a reserved lease")
    client_id: Optional[str] = Field(None, description="DHCP client ID")
    state: str = Field(default="BOUND", description="DHCP state")
    
    class Config:
        schema_extra = {
            "example": {
                "ip_address": "192.168.1.100",
                "hostname": "workstation-01",
                "mac_address": "aa:bb:cc:dd:ee:ff",
                "subnet": "192.168.1.0/24",
                "lease_start": "2025-11-06T10:00:00",
                "lease_end": "2025-11-13T10:00:00",
                "lease_duration_seconds": 604800,
                "status": "active",
                "days_remaining": 7,
                "reserved": False,
                "state": "BOUND",
            }
        }


class DHCPLeaseListResponse(BaseModel):
    """Response model for listing DHCP leases."""
    total: int = Field(..., description="Total number of leases")
    skip: int = Field(..., description="Number of skipped records")
    limit: int = Field(..., description="Limit of records returned")
    leases: List[DHCPLeaseResponse] = Field(..., description="List of leases")
    
    class Config:
        schema_extra = {
            "example": {
                "total": 45,
                "skip": 0,
                "limit": 20,
                "leases": [
                    {
                        "ip_address": "192.168.1.100",
                        "hostname": "workstation-01",
                        "mac_address": "aa:bb:cc:dd:ee:ff",
                        "subnet": "192.168.1.0/24",
                        "lease_start": "2025-11-06T10:00:00",
                        "lease_end": "2025-11-13T10:00:00",
                        "lease_duration_seconds": 604800,
                        "status": "active",
                        "days_remaining": 7,
                        "reserved": False,
                    }
                ]
            }
        }


class DHCPSubnetUtilization(BaseModel):
    """Utilization statistics for a subnet."""
    subnet: str = Field(..., description="Subnet CIDR")
    total_ips: int = Field(..., description="Total IPs in subnet")
    used_ips: int = Field(..., description="Number of used/active IPs")
    available_ips: int = Field(..., description="Number of available IPs")
    reserved_ips: int = Field(..., description="Number of reserved IPs")
    expired_ips: int = Field(..., description="Number of expired leases")
    utilization_percent: float = Field(..., description="Utilization percentage (0-100)")
    leases_count: int = Field(..., description="Total number of leases")
    
    class Config:
        schema_extra = {
            "example": {
                "subnet": "192.168.1.0/24",
                "total_ips": 254,
                "used_ips": 156,
                "available_ips": 95,
                "reserved_ips": 3,
                "expired_ips": 0,
                "utilization_percent": 61.4,
                "leases_count": 159,
            }
        }


class DHCPStatistics(BaseModel):
    """Overall DHCP statistics."""
    total_leases: int = Field(..., description="Total number of leases")
    active_leases: int = Field(..., description="Number of active leases")
    reserved_leases: int = Field(..., description="Number of reserved leases")
    subnets_count: int = Field(..., description="Number of configured subnets")
    total_ips: int = Field(..., description="Total IPs across all subnets")
    utilization_percent: float = Field(..., description="Overall utilization percentage")
    expiring_soon: int = Field(..., description="Number of leases expiring within 7 days")
    alerts: int = Field(..., description="Number of active alerts")
    
    class Config:
        schema_extra = {
            "example": {
                "total_leases": 250,
                "active_leases": 156,
                "reserved_leases": 10,
                "subnets_count": 4,
                "total_ips": 1016,
                "utilization_percent": 15.4,
                "expiring_soon": 12,
                "alerts": 3,
            }
        }


class DHCPAlertResponse(BaseModel):
    """DHCP alert or warning."""
    type: str = Field(..., description="Alert type (lease_expiration, subnet_exhaustion, etc.)")
    severity: str = Field(..., description="Severity level (critical, warning, info)")
    ip_address: str = Field(..., description="IP address related to alert")
    hostname: str = Field(..., description="Hostname related to alert")
    message: str = Field(..., description="Alert message")
    created_at: datetime = Field(..., description="When alert was created")
    
    class Config:
        schema_extra = {
            "example": {
                "type": "lease_expiration",
                "severity": "warning",
                "ip_address": "192.168.1.100",
                "hostname": "workstation-01",
                "message": "Lease expires in 3 days",
                "created_at": "2025-11-06T12:00:00",
            }
        }


class DHCPLeaseHistoryResponse(BaseModel):
    """Historical data for a DHCP lease."""
    ip_address: str = Field(..., description="IP address")
    hostname: str = Field(..., description="Hostname")
    mac_address: str = Field(..., description="MAC address")
    lease_start: datetime = Field(..., description="Lease start time")
    lease_end: datetime = Field(..., description="Lease end time")
    duration_days: int = Field(..., description="Lease duration in days")
    
    class Config:
        schema_extra = {
            "example": {
                "ip_address": "192.168.1.100",
                "hostname": "workstation-01",
                "mac_address": "aa:bb:cc:dd:ee:ff",
                "lease_start": "2025-11-06T10:00:00",
                "lease_end": "2025-11-13T10:00:00",
                "duration_days": 7,
            }
        }

