"""
DHCP Lease Monitoring API
Tracks and monitors DHCP lease status, expiration, and utilization
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import List, Optional
import logging

from app.models.dhcp_monitoring import (
    DHCPLeaseResponse,
    DHCPLeaseListResponse,
    DHCPSubnetUtilization,
    DHCPStatistics,
    DHCPAlertResponse,
)
from app.db.base import get_session
from app.auth.jwt import require_admin

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/leases", response_model=DHCPLeaseListResponse)
async def list_dhcp_leases(
    subnet: Optional[str] = Query(None, description="Filter by subnet"),
    status: Optional[str] = Query(None, description="Filter by lease status (active, expired, reserved)"),
    host: Optional[str] = Query(None, description="Search by hostname or IP"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sort_by: str = Query("ip_address", description="Sort by field"),
    session=Depends(get_session),
    _=Depends(require_admin),
):
    """
    List DHCP leases with filtering and pagination.
    
    Filters:
    - subnet: Filter by subnet (e.g., "192.168.1.0/24")
    - status: active, expired, reserved, released
    - host: Search by hostname or IP address
    
    Returns paginated list of leases with expiration status.
    """
    try:
        # Build query
        query = session.query(DHCPLease)
        
        # Apply filters
        if subnet:
            query = query.filter(DHCPLease.subnet == subnet)
        
        if status:
            now = datetime.utcnow()
            if status == "active":
                query = query.filter(
                    and_(
                        DHCPLease.lease_end > now,
                        DHCPLease.lease_start <= now
                    )
                )
            elif status == "expired":
                query = query.filter(DHCPLease.lease_end <= now)
            elif status == "reserved":
                query = query.filter(DHCPLease.reserved == True)
        
        if host:
            query = query.filter(
                (DHCPLease.ip_address.ilike(f"%{host}%")) |
                (DHCPLease.hostname.ilike(f"%{host}%")) |
                (DHCPLease.mac_address.ilike(f"%{host}%"))
            )
        
        # Get total count
        total = query.count()
        
        # Apply sorting and pagination
        if sort_by == "expiration":
            query = query.order_by(DHCPLease.lease_end)
        elif sort_by == "hostname":
            query = query.order_by(DHCPLease.hostname)
        else:  # default: ip_address
            query = query.order_by(DHCPLease.ip_address)
        
        leases = query.offset(skip).limit(limit).all()
        
        # Convert to response models
        lease_responses = [
            DHCPLeaseResponse(
                ip_address=lease.ip_address,
                hostname=lease.hostname or "unknown",
                mac_address=lease.mac_address,
                subnet=lease.subnet,
                lease_start=lease.lease_start,
                lease_end=lease.lease_end,
                lease_duration_seconds=int((lease.lease_end - lease.lease_start).total_seconds()),
                status=get_lease_status(lease),
                days_remaining=get_days_remaining(lease.lease_end),
                reserved=lease.reserved,
                client_id=lease.client_id,
                state=lease.state or "BOUND",
            )
            for lease in leases
        ]
        
        logger.info(f"Listed {len(leases)} DHCP leases (total: {total})")
        
        return DHCPLeaseListResponse(
            total=total,
            skip=skip,
            limit=limit,
            leases=lease_responses,
        )
    
    except Exception as e:
        logger.error(f"Error listing DHCP leases: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list DHCP leases")


@router.get("/leases/{ip_address}", response_model=DHCPLeaseResponse)
async def get_dhcp_lease(
    ip_address: str,
    session=Depends(get_session),
    _=Depends(require_admin),
):
    """Get details for a specific DHCP lease."""
    try:
        lease = session.query(DHCPLease).filter(
            DHCPLease.ip_address == ip_address
        ).first()
        
        if not lease:
            raise HTTPException(status_code=404, detail="Lease not found")
        
        return DHCPLeaseResponse(
            ip_address=lease.ip_address,
            hostname=lease.hostname or "unknown",
            mac_address=lease.mac_address,
            subnet=lease.subnet,
            lease_start=lease.lease_start,
            lease_end=lease.lease_end,
            lease_duration_seconds=int((lease.lease_end - lease.lease_start).total_seconds()),
            status=get_lease_status(lease),
            days_remaining=get_days_remaining(lease.lease_end),
            reserved=lease.reserved,
            client_id=lease.client_id,
            state=lease.state or "BOUND",
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting DHCP lease {ip_address}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get DHCP lease")


@router.get("/subnets/{subnet}/utilization", response_model=DHCPSubnetUtilization)
async def get_subnet_utilization(
    subnet: str,
    session=Depends(get_session),
    _=Depends(require_admin),
):
    """
    Get utilization statistics for a DHCP subnet.
    
    Returns:
    - Total addresses in subnet
    - Used addresses (leased)
    - Available addresses
    - Reserved addresses
    - Utilization percentage
    """
    try:
        # Get all leases in subnet
        leases = session.query(DHCPLease).filter(
            DHCPLease.subnet == subnet
        ).all()
        
        now = datetime.utcnow()
        
        # Calculate utilization
        total_leases = len(leases)
        active_leases = sum(
            1 for lease in leases
            if lease.lease_end > now and lease.lease_start <= now
        )
        reserved_leases = sum(1 for lease in leases if lease.reserved)
        expired_leases = sum(1 for lease in leases if lease.lease_end <= now)
        
        # Parse subnet to get total IPs (simplified)
        # In production, use ipaddress library for accurate calculations
        total_ips = 254  # Placeholder for /24 network
        
        available_ips = total_ips - active_leases - reserved_leases
        utilization_percent = round((active_leases / total_ips * 100) if total_ips > 0 else 0, 2)
        
        return DHCPSubnetUtilization(
            subnet=subnet,
            total_ips=total_ips,
            used_ips=active_leases,
            available_ips=available_ips,
            reserved_ips=reserved_leases,
            expired_ips=expired_leases,
            utilization_percent=utilization_percent,
            leases_count=total_leases,
        )
    
    except Exception as e:
        logger.error(f"Error getting subnet utilization for {subnet}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get subnet utilization")


@router.get("/statistics", response_model=DHCPStatistics)
async def get_dhcp_statistics(
    session=Depends(get_session),
    _=Depends(require_admin),
):
    """
    Get overall DHCP statistics across all subnets.
    
    Returns:
    - Total leases
    - Active leases
    - Subnets count
    - Expiration alerts
    - Utilization summary
    """
    try:
        leases = session.query(DHCPLease).all()
        now = datetime.utcnow()
        alert_threshold = now + timedelta(days=7)
        
        total_leases = len(leases)
        active_leases = sum(
            1 for lease in leases
            if lease.lease_end > now and lease.lease_start <= now
        )
        reserved_leases = sum(1 for lease in leases if lease.reserved)
        expiring_soon = sum(
            1 for lease in leases
            if now < lease.lease_end < alert_threshold
        )
        
        # Get unique subnets
        subnets = session.query(
            func.distinct(DHCPLease.subnet)
        ).all()
        subnets_count = len(subnets)
        
        total_ips = subnets_count * 254  # Placeholder
        utilization_percent = round(
            (active_leases / total_ips * 100) if total_ips > 0 else 0,
            2
        )
        
        logger.info(f"DHCP Statistics: {active_leases} active, {expiring_soon} expiring")
        
        return DHCPStatistics(
            total_leases=total_leases,
            active_leases=active_leases,
            reserved_leases=reserved_leases,
            subnets_count=subnets_count,
            total_ips=total_ips,
            utilization_percent=utilization_percent,
            expiring_soon=expiring_soon,
            alerts=get_active_alerts(leases, now),
        )
    
    except Exception as e:
        logger.error(f"Error getting DHCP statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get DHCP statistics")


@router.get("/alerts", response_model=List[DHCPAlertResponse])
async def get_dhcp_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity (critical, warning, info)"),
    session=Depends(get_session),
    _=Depends(require_admin),
):
    """
    Get DHCP-related alerts and warnings.
    
    Alert Types:
    - Lease expiration (7 days)
    - Subnet exhaustion (>80% utilization)
    - Expired leases
    - High utilization subnets
    """
    try:
        leases = session.query(DHCPLease).all()
        now = datetime.utcnow()
        alerts = []
        
        # Check for expiring leases (7 days)
        alert_threshold = now + timedelta(days=7)
        for lease in leases:
            if now < lease.lease_end < alert_threshold and not lease.reserved:
                severity_level = "warning" if lease.lease_end < now + timedelta(days=3) else "info"
                if severity and severity != severity_level:
                    continue
                
                alerts.append(DHCPAlertResponse(
                    type="lease_expiration",
                    severity=severity_level,
                    ip_address=lease.ip_address,
                    hostname=lease.hostname or "unknown",
                    message=f"Lease expires in {get_days_remaining(lease.lease_end)} days",
                    created_at=now,
                ))
        
        # Check for subnet exhaustion
        subnets = session.query(func.distinct(DHCPLease.subnet)).all()
        for subnet_tuple in subnets:
            subnet = subnet_tuple[0]
            subnet_leases = [l for l in leases if l.subnet == subnet]
            active_count = sum(
                1 for l in subnet_leases
                if l.lease_end > now and l.lease_start <= now
            )
            total_ips = 254  # Placeholder
            utilization = (active_count / total_ips * 100) if total_ips > 0 else 0
            
            if utilization > 80:
                severity_level = "critical" if utilization > 95 else "warning"
                if severity and severity != severity_level:
                    continue
                
                alerts.append(DHCPAlertResponse(
                    type="subnet_exhaustion",
                    severity=severity_level,
                    ip_address=subnet,
                    hostname=subnet,
                    message=f"Subnet utilization: {utilization:.1f}%",
                    created_at=now,
                ))
        
        logger.info(f"Found {len(alerts)} DHCP alerts")
        
        return alerts
    
    except Exception as e:
        logger.error(f"Error getting DHCP alerts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get DHCP alerts")


# Helper functions

def get_lease_status(lease) -> str:
    """Determine lease status."""
    now = datetime.utcnow()
    if lease.reserved:
        return "reserved"
    elif lease.lease_end <= now:
        return "expired"
    elif lease.lease_start <= now <= lease.lease_end:
        return "active"
    else:
        return "pending"


def get_days_remaining(lease_end: datetime) -> int:
    """Calculate days remaining until lease expiration."""
    delta = lease_end - datetime.utcnow()
    return max(0, delta.days)


def get_active_alerts(leases, now: datetime) -> int:
    """Count active alerts."""
    alert_threshold = now + timedelta(days=7)
    count = sum(
        1 for lease in leases
        if now < lease.lease_end < alert_threshold
    )
    return count


# Placeholder model for database (would be in db.models in production)
class DHCPLease:
    """DHCP Lease database model."""
    ip_address: str
    hostname: Optional[str]
    mac_address: str
    subnet: str
    lease_start: datetime
    lease_end: datetime
    reserved: bool
    client_id: Optional[str]
    state: Optional[str]

