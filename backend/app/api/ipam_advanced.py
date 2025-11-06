#!/usr/bin/env python3
"""
Advanced IPAM API endpoints

Provides pool management, IP search/discovery, and subnet calculator endpoints.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
from ipaddress import IPv4Network, IPv4Address
import ipaddress
import logging

from app.models.ipam_advanced import (
    PoolManagementCreate, SubnetSplit, SubnetMerge, SubnetCalculatorRequest,
    SubnetInfo, IPSearchRequest, IPSearchResults, IPSearchResult,
    ConflictDetection
)
from app.db.base import get_session
from app.db.models import IPPool, IPAllocation
from app.auth.jwt import get_current_user, require_operator
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/calculator")
async def subnet_calculator(request: SubnetCalculatorRequest, current_user: dict = Depends(get_current_user)):
    """
    Perform subnet calculations (split, merge, info, validate)
    
    Args:
        request: Calculator request with operation and network(s)
        current_user: Authenticated user
        
    Returns:
        Calculator results
    """
    try:
        if request.operation == "info":
            network = IPv4Network(request.network, strict=False)
            
            return SubnetInfo(
                network=str(network.network_address),
                netmask=str(network.netmask),
                broadcast=str(network.broadcast_address),
                first_host=str(list(network.hosts())[0]) if network.num_addresses > 2 else str(network.network_address),
                last_host=str(list(network.hosts())[-1]) if network.num_addresses > 2 else str(network.broadcast_address),
                total_hosts=network.num_addresses,
                usable_hosts=max(0, network.num_addresses - 2),
                prefix_length=network.prefixlen
            )
        
        elif request.operation == "split":
            network = IPv4Network(request.network, strict=False)
            subnet_count = request.subnet_count or 2
            
            # Calculate new prefix length
            new_prefix = network.prefixlen + (subnet_count - 1).bit_length()
            if new_prefix > 32:
                raise ValueError("Cannot split into that many subnets")
            
            subnets = list(network.subnets(new_prefix=new_prefix))
            
            return SubnetSplit(
                original_network=str(network),
                subnets=[str(subnet) for subnet in subnets],
                subnet_count=len(subnets),
                hosts_per_subnet=subnets[0].num_addresses - 2 if len(subnets) > 0 else 0
            )
        
        elif request.operation == "merge":
            networks = [IPv4Network(n, strict=False) for n in request.networks]
            # Try to find common supernet
            try:
                merged = IPv4Network.common_prefix(networks)
                return SubnetMerge(
                    subnets=request.networks,
                    merged_network=str(merged)
                )
            except ValueError:
                raise ValueError("Networks cannot be merged into a single contiguous block")
        
        elif request.operation == "validate":
            try:
                network = IPv4Network(request.network, strict=False)
                return {"valid": True, "network": str(network), "message": "Valid network"}
            except ValueError as e:
                return {"valid": False, "message": str(e)}
        
        else:
            raise ValueError(f"Unknown operation: {request.operation}")
    
    except Exception as e:
        logger.error(f"Error in subnet calculator: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Calculation error: {str(e)}"
        )


@router.post("/search", response_model=IPSearchResults)
async def search_ips(
    request: IPSearchRequest,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Search and discover IPs across all pools
    
    Args:
        request: Search parameters
        session: Database session
        current_user: Authenticated user
        
    Returns:
        List of matching IPs
    """
    try:
        results = []
        
        # Build query
        query = select(IPAllocation, IPPool).join(IPPool)
        
        # Apply filters
        filters = []
        
        if request.search_type == "ip":
            filters.append(IPAllocation.ip_address.astext.like(f"%{request.query}%"))
        elif request.search_type == "hostname":
            filters.append(IPAllocation.hostname.ilike(f"%{request.query}%"))
        elif request.search_type == "mac":
            filters.append(IPAllocation.mac_address.ilike(f"%{request.query}%"))
        elif request.search_type == "owner":
            filters.append(IPAllocation.owner.ilike(f"%{request.query}%"))
        else:
            # Search all fields
            filters.append(
                or_(
                    IPAllocation.ip_address.astext.like(f"%{request.query}%"),
                    IPAllocation.hostname.ilike(f"%{request.query}%"),
                    IPAllocation.mac_address.ilike(f"%{request.query}%"),
                    IPAllocation.owner.ilike(f"%{request.query}%")
                )
            )
        
        if request.pool_id:
            filters.append(IPAllocation.pool_id == request.pool_id)
        
        if request.allocated_only:
            filters.append(IPAllocation.status == "allocated")
        
        if request.available_only:
            filters.append(IPAllocation.status == "available")
        
        if filters:
            query = query.where(and_(*filters))
        
        result = await session.execute(query)
        rows = result.all()
        
        for allocation, pool in rows:
            results.append(IPSearchResult(
                pool_name=pool.name,
                pool_id=pool.id,
                ip_address=str(allocation.ip_address),
                hostname=allocation.hostname,
                owner=allocation.owner,
                status=allocation.status or "unknown",
                mac_address=allocation.mac_address,
                purpose=allocation.purpose,
                allocated_at=allocation.created_at.isoformat() if allocation.created_at else None
            ))
        
        return IPSearchResults(
            total=len(results),
            results=results
        )
    
    except Exception as e:
        logger.error(f"Error searching IPs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/conflicts/detect")
async def detect_conflicts(
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Detect IP allocation conflicts across pools
    
    Args:
        session: Database session
        current_user: Authenticated user
        
    Returns:
        Conflict detection results
    """
    try:
        # Query all allocated IPs
        result = await session.execute(
            select(IPAllocation.ip_address, IPAllocation.pool_id).where(IPAllocation.status == "allocated")
        )
        allocations = result.all()
        
        # Check for duplicates
        ip_map = {}
        conflicts = []
        
        for ip, pool_id in allocations:
            ip_str = str(ip)
            if ip_str in ip_map:
                # Found a conflict
                conflicts.append({
                    "ip": ip_str,
                    "pools": sorted(list(set([ip_map[ip_str], pool_id]))),
                    "issue": "Allocated in multiple pools"
                })
            else:
                ip_map[ip_str] = pool_id
        
        return ConflictDetection(
            has_conflicts=len(conflicts) > 0,
            conflicts=conflicts,
            summary=f"Found {len(conflicts)} conflicts"
        )
    
    except Exception as e:
        logger.error(f"Error detecting conflicts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conflict detection failed: {str(e)}"
        )


@router.post("/pools/create-advanced")
async def create_pool_advanced(
    pool: PoolManagementCreate,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new IP pool with advanced options
    
    Args:
        pool: Pool creation request
        session: Database session
        current_user: Authenticated user
        
    Returns:
        Created pool
    """
    try:
        # Validate network
        network = IPv4Network(pool.network, strict=False)
        
        # Create pool
        new_pool = IPPool(
            name=pool.name,
            network=str(network),
            gateway=pool.gateway,
            vlan_id=pool.vlan_id,
            dns_servers=pool.dns_servers,
            description=pool.description,
            template=pool.template
        )
        
        session.add(new_pool)
        await session.commit()
        await session.refresh(new_pool)
        
        return {
            "id": new_pool.id,
            "name": new_pool.name,
            "network": new_pool.network,
            "message": "Pool created successfully"
        }
    
    except Exception as e:
        await session.rollback()
        logger.error(f"Error creating pool: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pool creation failed: {str(e)}"
        )

