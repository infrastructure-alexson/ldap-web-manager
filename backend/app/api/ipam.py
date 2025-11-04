#!/usr/bin/env python3
"""
IPAM (IP Address Management) API endpoints
"""

import sqlite3
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
import ipaddress
import json
from pathlib import Path
from datetime import datetime
from app.models.ipam import (
    IPPoolCreate, IPPoolUpdate, IPPoolResponse, IPPoolListResponse,
    IPAllocationCreate, IPAllocationUpdate, IPAllocationResponse, IPAllocationListResponse,
    IPPoolStatsResponse, IPConflictResponse, IPAMStatsResponse,
    IPSearchRequest, IPSearchResponse
)
from app.auth.jwt import get_current_user, require_admin, require_operator
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Database path
DB_PATH = Path("/var/lib/ldap-web-manager/ipam.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize IPAM database"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Create pools table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ip_pools (
            id TEXT PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            network TEXT NOT NULL,
            description TEXT,
            vlan_id INTEGER,
            gateway TEXT,
            dns_servers TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create allocations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ip_allocations (
            id TEXT PRIMARY KEY,
            pool_id TEXT NOT NULL,
            ip_address TEXT NOT NULL,
            hostname TEXT,
            mac_address TEXT,
            allocation_type TEXT NOT NULL,
            description TEXT,
            allocated_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pool_id) REFERENCES ip_pools(id) ON DELETE CASCADE,
            UNIQUE(pool_id, ip_address)
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_allocations_pool ON ip_allocations(pool_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_allocations_ip ON ip_allocations(ip_address)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_allocations_hostname ON ip_allocations(hostname)")
    
    conn.commit()
    conn.close()


# Initialize database on module load
init_db()


def calculate_pool_stats(pool_id: str, network: str) -> dict:
    """Calculate statistics for an IP pool"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Parse network
    net = ipaddress.IPv4Network(network, strict=False)
    total_ips = net.num_addresses - 2  # Exclude network and broadcast
    
    # Count allocations
    cursor.execute(
        "SELECT COUNT(*), allocation_type FROM ip_allocations WHERE pool_id = ? GROUP BY allocation_type",
        (pool_id,)
    )
    allocations = cursor.fetchall()
    
    used_ips = sum(row[0] for row in allocations)
    available_ips = total_ips - used_ips
    utilization = (used_ips / total_ips * 100) if total_ips > 0 else 0
    
    conn.close()
    
    return {
        "total_ips": total_ips,
        "used_ips": used_ips,
        "available_ips": available_ips,
        "utilization_percent": round(utilization, 2)
    }


# ============================================================================
# IP POOLS
# ============================================================================

@router.get("/pools", response_model=IPPoolListResponse)
async def list_pools(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    List all IP pools
    
    Args:
        page: Page number
        page_size: Items per page
        search: Search term
        current_user: Authenticated user
        
    Returns:
        List of IP pools
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # Build query
    if search:
        query = "SELECT * FROM ip_pools WHERE name LIKE ? OR network LIKE ? OR description LIKE ?"
        params = (f"%{search}%", f"%{search}%", f"%{search}%")
    else:
        query = "SELECT * FROM ip_pools"
        params = ()
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # Convert to response objects
    pools = []
    for row in rows:
        stats = calculate_pool_stats(row['id'], row['network'])
        dns_servers = json.loads(row['dns_servers']) if row['dns_servers'] else None
        
        pool_data = {
            'id': row['id'],
            'name': row['name'],
            'network': row['network'],
            'description': row['description'],
            'vlan_id': row['vlan_id'],
            'gateway': row['gateway'],
            'dns_servers': dns_servers,
            'total_ips': stats['total_ips'],
            'used_ips': stats['used_ips'],
            'available_ips': stats['available_ips'],
            'utilization_percent': stats['utilization_percent'],
            'createTimestamp': row['created_at'],
            'modifyTimestamp': row['modified_at'],
        }
        pools.append(IPPoolResponse(**pool_data))
    
    # Pagination
    total = len(pools)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_pools = pools[start:end]
    
    conn.close()
    
    return {
        "pools": paginated_pools,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/pools", response_model=IPPoolResponse, status_code=status.HTTP_201_CREATED)
async def create_pool(
    pool: IPPoolCreate,
    current_user: dict = Depends(require_operator)
):
    """
    Create new IP pool
    
    Args:
        pool: Pool information
        current_user: Authenticated user (operator or admin)
        
    Returns:
        Created pool
    """
    import uuid
    
    conn = get_db()
    cursor = conn.cursor()
    
    pool_id = str(uuid.uuid4())
    dns_json = json.dumps(pool.dns_servers) if pool.dns_servers else None
    
    try:
        cursor.execute("""
            INSERT INTO ip_pools (id, name, network, description, vlan_id, gateway, dns_servers)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (pool_id, pool.name, pool.network, pool.description, pool.vlan_id, pool.gateway, dns_json))
        
        conn.commit()
        logger.info(f"IP pool created: {pool.name} by {current_user.get('username')}")
        
        # Return created pool
        stats = calculate_pool_stats(pool_id, pool.network)
        
        conn.close()
        
        return IPPoolResponse(
            id=pool_id,
            name=pool.name,
            network=pool.network,
            description=pool.description,
            vlan_id=pool.vlan_id,
            gateway=pool.gateway,
            dns_servers=pool.dns_servers,
            **stats
        )
        
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"IP pool already exists: {pool.name}"
        )


@router.delete("/pools/{pool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pool(
    pool_id: str,
    current_user: dict = Depends(require_admin)
):
    """
    Delete IP pool
    
    Args:
        pool_id: Pool ID
        current_user: Authenticated user (admin only)
    """
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM ip_pools WHERE id = ?", (pool_id,))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IP pool not found: {pool_id}"
        )
    
    conn.commit()
    conn.close()
    logger.info(f"IP pool deleted: {pool_id} by {current_user.get('username')}")


# ============================================================================
# IP ALLOCATIONS
# ============================================================================

@router.get("/pools/{pool_id}/allocations", response_model=IPAllocationListResponse)
async def list_allocations(
    pool_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    List all IP allocations in a pool
    
    Args:
        pool_id: Pool ID
        current_user: Authenticated user
        
    Returns:
        List of IP allocations
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # Verify pool exists
    cursor.execute("SELECT name FROM ip_pools WHERE id = ?", (pool_id,))
    pool = cursor.fetchone()
    if not pool:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IP pool not found: {pool_id}"
        )
    
    # Get allocations
    cursor.execute("""
        SELECT * FROM ip_allocations WHERE pool_id = ? ORDER BY ip_address
    """, (pool_id,))
    rows = cursor.fetchall()
    
    allocations = []
    for row in rows:
        alloc_data = {
            'id': row['id'],
            'pool_id': row['pool_id'],
            'ip_address': row['ip_address'],
            'hostname': row['hostname'],
            'mac_address': row['mac_address'],
            'allocation_type': row['allocation_type'],
            'description': row['description'],
            'allocated_at': row['created_at'],
            'allocated_by': row['allocated_by'],
            'createTimestamp': row['created_at'],
            'modifyTimestamp': row['modified_at'],
        }
        allocations.append(IPAllocationResponse(**alloc_data))
    
    conn.close()
    
    return {
        "allocations": allocations,
        "total": len(allocations),
        "pool": pool['name']
    }


@router.post("/allocations", response_model=IPAllocationResponse, status_code=status.HTTP_201_CREATED)
async def create_allocation(
    allocation: IPAllocationCreate,
    current_user: dict = Depends(require_operator)
):
    """
    Create new IP allocation
    
    Args:
        allocation: Allocation information
        current_user: Authenticated user (operator or admin)
        
    Returns:
        Created allocation
    """
    import uuid
    
    conn = get_db()
    cursor = conn.cursor()
    
    alloc_id = str(uuid.uuid4())
    username = current_user.get('username')
    
    try:
        cursor.execute("""
            INSERT INTO ip_allocations (id, pool_id, ip_address, hostname, mac_address, 
                                       allocation_type, description, allocated_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (alloc_id, allocation.pool_id, allocation.ip_address, allocation.hostname,
              allocation.mac_address, allocation.allocation_type, allocation.description, username))
        
        conn.commit()
        conn.close()
        
        logger.info(f"IP allocated: {allocation.ip_address} by {username}")
        
        return IPAllocationResponse(
            id=alloc_id,
            pool_id=allocation.pool_id,
            ip_address=allocation.ip_address,
            hostname=allocation.hostname,
            mac_address=allocation.mac_address,
            allocation_type=allocation.allocation_type,
            description=allocation.description,
            allocated_by=username
        )
        
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"IP address already allocated: {allocation.ip_address}"
        )


@router.delete("/allocations/{allocation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_allocation(
    allocation_id: str,
    current_user: dict = Depends(require_operator)
):
    """
    Delete IP allocation
    
    Args:
        allocation_id: Allocation ID
        current_user: Authenticated user (operator or admin)
    """
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM ip_allocations WHERE id = ?", (allocation_id,))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IP allocation not found: {allocation_id}"
        )
    
    conn.commit()
    conn.close()
    logger.info(f"IP allocation deleted: {allocation_id} by {current_user.get('username')}")


# ============================================================================
# IPAM STATISTICS
# ============================================================================

@router.get("/stats", response_model=IPAMStatsResponse)
async def get_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    Get IPAM statistics
    
    Args:
        current_user: Authenticated user
        
    Returns:
        IPAM statistics
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # Count pools
    cursor.execute("SELECT COUNT(*) FROM ip_pools")
    total_pools = cursor.fetchone()[0]
    
    # Get all pools and calculate stats
    cursor.execute("SELECT id, name, network FROM ip_pools")
    pools = cursor.fetchall()
    
    total_ips = 0
    allocated_ips = 0
    pools_stats = []
    
    for pool in pools:
        stats = calculate_pool_stats(pool['id'], pool['network'])
        total_ips += stats['total_ips']
        allocated_ips += stats['used_ips']
        
        pools_stats.append({
            'pool_name': pool['name'],
            'utilization': stats['utilization_percent']
        })
    
    # Count reserved
    cursor.execute("SELECT COUNT(*) FROM ip_allocations WHERE allocation_type = 'reserved'")
    reserved = cursor.fetchone()[0]
    
    conn.close()
    
    available = total_ips - allocated_ips
    utilization = (allocated_ips / total_ips * 100) if total_ips > 0 else 0
    
    return {
        "total_pools": total_pools,
        "total_networks": total_pools,
        "total_ip_addresses": total_ips,
        "allocated_addresses": allocated_ips,
        "available_addresses": available,
        "reserved_addresses": reserved,
        "utilization_percent": round(utilization, 2),
        "pools_by_utilization": sorted(pools_stats, key=lambda x: x['utilization'], reverse=True)
    }


# ============================================================================
# IP SEARCH
# ============================================================================

@router.post("/search", response_model=IPSearchResponse)
async def search_ips(
    search: IPSearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Search for IP allocations
    
    Args:
        search: Search parameters
        current_user: Authenticated user
        
    Returns:
        Search results
    """
    conn = get_db()
    cursor = conn.cursor()
    
    query = search.query
    pool_filter = f"AND pool_id = '{search.pool_id}'" if search.pool_id else ""
    
    cursor.execute(f"""
        SELECT * FROM ip_allocations 
        WHERE (ip_address LIKE ? OR hostname LIKE ? OR mac_address LIKE ?)
        {pool_filter}
        ORDER BY ip_address
        LIMIT 100
    """, (f"%{query}%", f"%{query}%", f"%{query}%"))
    
    rows = cursor.fetchall()
    
    results = []
    for row in rows:
        results.append(IPAllocationResponse(
            id=row['id'],
            pool_id=row['pool_id'],
            ip_address=row['ip_address'],
            hostname=row['hostname'],
            mac_address=row['mac_address'],
            allocation_type=row['allocation_type'],
            description=row['description'],
            allocated_at=row['created_at'],
            allocated_by=row['allocated_by'],
            createTimestamp=row['created_at'],
            modifyTimestamp=row['modified_at'],
        ))
    
    conn.close()
    
    return {
        "results": results,
        "total": len(results)
    }

