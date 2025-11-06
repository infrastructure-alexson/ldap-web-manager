#!/usr/bin/env python3
"""
IPAM (IP Address Management) API endpoints
Uses PostgreSQL backend with audit logging
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import Optional, List
import ipaddress
import logging
from datetime import datetime

from app.models.ipam import (
    IPPoolCreate, IPPoolUpdate, IPPoolResponse, IPPoolListResponse,
    IPAllocationCreate, IPAllocationUpdate, IPAllocationResponse, IPAllocationListResponse,
    IPPoolStatsResponse, IPAMStatsResponse,
    IPSearchRequest, IPSearchResponse
)
from app.auth.jwt import get_current_user, require_admin, require_operator
from app.db.base import get_session
from app.db.models import IPPool, IPAllocation, AuditAction
from app.db.audit import get_audit_logger

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# IP Pools Endpoints
# ============================================================================

@router.get("/pools", response_model=IPPoolListResponse)
async def list_pools(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(True),
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_operator)
):
    """
    List all IP pools
    
    Query Parameters:
        page: Page number (default: 1)
        page_size: Items per page (default: 20, max: 100)
        active_only: Only show active pools (default: true)
    """
    try:
        # Build query
        query = select(IPPool)
        
        if active_only:
            query = query.where(IPPool.is_active == True)
        
        # Get total count
        count_result = await session.execute(select(func.count()).select_from(IPPool))
        total = count_result.scalar() or 0
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(IPPool.name)
        
        result = await session.execute(query)
        pools = result.scalars().all()
        
        # Convert to response models with stats
        pool_responses = []
        for pool in pools:
            response = await _pool_to_response(pool, session)
            pool_responses.append(response)
        
        return IPPoolListResponse(
            pools=pool_responses,
            total=total,
            page=page,
            page_size=page_size
        )
    
    except Exception as e:
        logger.error(f"Error listing IP pools: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list IP pools"
        )


@router.post("/pools", response_model=IPPoolResponse, status_code=status.HTTP_201_CREATED)
async def create_pool(
    pool: IPPoolCreate,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    """
    Create a new IP pool
    
    Request Body:
        name: Pool name (unique)
        network: Network address (CIDR notation, e.g., 10.0.0.0/24)
        description: Optional description
        vlan_id: Optional VLAN ID
        gateway: Optional default gateway
    """
    try:
        # Validate network format
        try:
            net = ipaddress.ip_network(pool.network, strict=False)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid network format: {str(e)}"
            )
        
        # Check if pool name already exists
        existing = await session.execute(
            select(IPPool).where(IPPool.name == pool.name)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Pool '{pool.name}' already exists"
            )
        
        # Check if network already exists
        existing_net = await session.execute(
            select(IPPool).where(IPPool.network == str(net.cidr))
        )
        if existing_net.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Network {pool.network} already allocated"
            )
        
        # Create new pool
        new_pool = IPPool(
            name=pool.name,
            network=str(net.cidr),
            gateway=pool.gateway,
            description=pool.description,
            vlan_id=pool.vlan_id,
            created_by=current_user.get("username"),
            is_active=True
        )
        
        session.add(new_pool)
        await session.flush()
        
        # Audit log
        audit = await get_audit_logger(session)
        await audit.log_ipam_action(
            AuditAction.CREATE,
            pool_name=new_pool.name,
            resource_id=new_pool.id,
            user_id=current_user.get("username"),
            details={
                "network": str(net.cidr),
                "vlan_id": pool.vlan_id,
                "description": pool.description
            }
        )
        
        await session.commit()
        
        logger.info(f"Created IP pool: {new_pool.name} ({new_pool.network})")
        
        response = await _pool_to_response(new_pool, session)
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating IP pool: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create IP pool"
        )


@router.get("/pools/{pool_id}", response_model=IPPoolResponse)
async def get_pool(
    pool_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_operator)
):
    """Get a specific IP pool by ID"""
    try:
        result = await session.execute(select(IPPool).where(IPPool.id == pool_id))
        pool = result.scalar_one_or_none()
        
        if not pool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pool ID {pool_id} not found"
            )
        
        response = await _pool_to_response(pool, session)
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting IP pool: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve IP pool"
        )


@router.put("/pools/{pool_id}", response_model=IPPoolResponse)
async def update_pool(
    pool_id: int,
    pool_update: IPPoolUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    """Update an IP pool"""
    try:
        result = await session.execute(select(IPPool).where(IPPool.id == pool_id))
        pool = result.scalar_one_or_none()
        
        if not pool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pool ID {pool_id} not found"
            )
        
        # Audit log - capture before state
        audit = await get_audit_logger(session)
        before_state = {
            "description": pool.description,
            "vlan_id": pool.vlan_id,
            "gateway": pool.gateway
        }
        
        # Update fields
        if pool_update.description is not None:
            pool.description = pool_update.description
        if pool_update.vlan_id is not None:
            pool.vlan_id = pool_update.vlan_id
        if pool_update.gateway is not None:
            pool.gateway = pool_update.gateway
        
        pool.updated_at = datetime.utcnow()
        
        await session.flush()
        
        # Audit log
        after_state = {
            "description": pool.description,
            "vlan_id": pool.vlan_id,
            "gateway": pool.gateway
        }
        
        await audit.log_ipam_action(
            AuditAction.UPDATE,
            pool_name=pool.name,
            resource_id=pool.id,
            user_id=current_user.get("username"),
            details={"before": before_state, "after": after_state}
        )
        
        await session.commit()
        
        logger.info(f"Updated IP pool: {pool.name}")
        
        response = await _pool_to_response(pool, session)
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating IP pool: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update IP pool"
        )


@router.delete("/pools/{pool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pool(
    pool_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    """Delete an IP pool (and all allocations)"""
    try:
        result = await session.execute(select(IPPool).where(IPPool.id == pool_id))
        pool = result.scalar_one_or_none()
        
        if not pool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pool ID {pool_id} not found"
            )
        
        pool_name = pool.name
        
        # Audit log
        audit = await get_audit_logger(session)
        
        # Count allocations before deletion
        alloc_result = await session.execute(
            select(func.count()).select_from(IPAllocation).where(IPAllocation.pool_id == pool_id)
        )
        alloc_count = alloc_result.scalar() or 0
        
        # Delete pool (cascades to allocations)
        await session.delete(pool)
        await session.flush()
        
        # Audit log
        await audit.log_ipam_action(
            AuditAction.DELETE,
            pool_name=pool_name,
            resource_id=pool_id,
            user_id=current_user.get("username"),
            details={"allocations_deleted": alloc_count}
        )
        
        await session.commit()
        
        logger.info(f"Deleted IP pool: {pool_name} (removed {alloc_count} allocations)")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting IP pool: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete IP pool"
        )


# ============================================================================
# IP Allocations Endpoints
# ============================================================================

@router.get("/pools/{pool_id}/allocations", response_model=IPAllocationListResponse)
async def list_allocations(
    pool_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    status_filter: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_operator)
):
    """
    List all allocations in a pool
    
    Query Parameters:
        pool_id: Pool ID
        page: Page number (default: 1)
        page_size: Items per page (default: 50, max: 500)
        status_filter: Filter by status (available, allocated, reserved, blocked)
    """
    try:
        # Verify pool exists
        pool_result = await session.execute(select(IPPool).where(IPPool.id == pool_id))
        pool = pool_result.scalar_one_or_none()
        
        if not pool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pool ID {pool_id} not found"
            )
        
        # Build query
        query = select(IPAllocation).where(IPAllocation.pool_id == pool_id)
        
        if status_filter:
            query = query.where(IPAllocation.status == status_filter)
        
        # Get total count
        count_result = await session.execute(
            select(func.count()).select_from(IPAllocation).where(IPAllocation.pool_id == pool_id)
        )
        total = count_result.scalar() or 0
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(IPAllocation.ip_address)
        
        result = await session.execute(query)
        allocations = result.scalars().all()
        
        # Convert to response models
        allocation_responses = [_allocation_to_response(a) for a in allocations]
        
        return IPAllocationListResponse(
            allocations=allocation_responses,
            total=total,
            pool=pool.name
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing allocations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list allocations"
        )


@router.post("/pools/{pool_id}/allocations", response_model=IPAllocationResponse, status_code=status.HTTP_201_CREATED)
async def create_allocation(
    pool_id: int,
    allocation: IPAllocationCreate,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_operator)
):
    """
    Create a new IP allocation
    
    Request Body:
        ip_address: IP address to allocate
        hostname: Optional hostname
        mac_address: Optional MAC address
        owner: Owner of the allocation
        purpose: Purpose (server, workstation, printer, etc.)
        description: Optional description
    """
    try:
        # Verify pool exists
        pool_result = await session.execute(select(IPPool).where(IPPool.id == pool_id))
        pool = pool_result.scalar_one_or_none()
        
        if not pool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pool ID {pool_id} not found"
            )
        
        # Validate IP is in pool network
        try:
            ip = ipaddress.ip_address(allocation.ip_address)
            network = ipaddress.ip_network(pool.network, strict=False)
            
            if ip not in network:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"IP address {allocation.ip_address} not in pool network {pool.network}"
                )
        except ipaddress.AddressValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid IP address: {str(e)}"
            )
        
        # Check if IP already allocated
        existing = await session.execute(
            select(IPAllocation).where(
                and_(
                    IPAllocation.pool_id == pool_id,
                    IPAllocation.ip_address == allocation.ip_address
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"IP address {allocation.ip_address} already allocated in this pool"
            )
        
        # Create allocation
        new_allocation = IPAllocation(
            pool_id=pool_id,
            ip_address=allocation.ip_address,
            mac_address=allocation.mac_address,
            hostname=allocation.hostname,
            owner=allocation.owner,
            purpose=allocation.purpose,
            description=allocation.description,
            status="allocated",
            allocated_at=datetime.utcnow(),
            allocated_by=current_user.get("username")
        )
        
        session.add(new_allocation)
        await session.flush()
        
        # Audit log
        audit = await get_audit_logger(session)
        await audit.log_allocation_action(
            AuditAction.CREATE,
            ip_address=new_allocation.ip_address,
            user_id=current_user.get("username"),
            details={
                "pool_name": pool.name,
                "hostname": allocation.hostname,
                "mac_address": allocation.mac_address,
                "owner": allocation.owner,
                "purpose": allocation.purpose
            }
        )
        
        await session.commit()
        
        logger.info(f"Created allocation: {new_allocation.ip_address} in pool {pool.name}")
        
        return _allocation_to_response(new_allocation)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating allocation: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create allocation"
        )


@router.delete("/allocations/{allocation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def release_allocation(
    allocation_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_operator)
):
    """
    Release (delete) an IP allocation
    """
    try:
        result = await session.execute(
            select(IPAllocation).where(IPAllocation.id == allocation_id)
        )
        allocation = result.scalar_one_or_none()
        
        if not allocation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Allocation ID {allocation_id} not found"
            )
        
        ip_address = allocation.ip_address
        pool_id = allocation.pool_id
        
        # Get pool for logging
        pool_result = await session.execute(
            select(IPPool).where(IPPool.id == pool_id)
        )
        pool = pool_result.scalar_one_or_none()
        
        # Audit log
        audit = await get_audit_logger(session)
        await audit.log_allocation_action(
            AuditAction.DELETE,
            ip_address=ip_address,
            user_id=current_user.get("username"),
            details={
                "pool_name": pool.name if pool else "unknown",
                "hostname": allocation.hostname,
                "owner": allocation.owner
            }
        )
        
        # Delete allocation
        await session.delete(allocation)
        await session.commit()
        
        logger.info(f"Released allocation: {ip_address}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error releasing allocation: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to release allocation"
        )


# ============================================================================
# Statistics Endpoints
# ============================================================================

@router.get("/stats", response_model=IPAMStatsResponse)
async def get_ipam_stats(
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_operator)
):
    """Get overall IPAM statistics"""
    try:
        # Get pool counts
        pool_result = await session.execute(select(func.count()).select_from(IPPool))
        total_pools = pool_result.scalar() or 0
        
        # Get allocation stats
        alloc_result = await session.execute(
            select(
                func.count(IPAllocation.id),
                func.sum(func.cast(IPAllocation.status == "allocated", func.Integer))
            ).select_from(IPAllocation)
        )
        total_allocations, allocated_count = alloc_result.one()
        total_allocations = total_allocations or 0
        allocated_count = allocated_count or 0
        available = total_allocations - allocated_count
        
        # Calculate utilization
        utilization = (allocated_count / total_allocations * 100) if total_allocations > 0 else 0
        
        return IPAMStatsResponse(
            total_pools=total_pools,
            total_networks=total_pools,
            total_ip_addresses=total_allocations,
            allocated_addresses=allocated_count,
            available_addresses=available,
            reserved_addresses=0,  # TODO: Implement reserved tracking
            utilization_percent=round(utilization, 2),
            pools_by_utilization=[]  # TODO: Implement detailed stats
        )
    
    except Exception as e:
        logger.error(f"Error getting IPAM stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve IPAM statistics"
        )


@router.get("/search", response_model=IPSearchResponse)
async def search_ips(
    query: str = Query(..., description="IP, hostname, or MAC to search"),
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_operator)
):
    """
    Search for IP allocations
    
    Query Parameters:
        query: IP address, hostname, or MAC address to search for
    """
    try:
        # Build search query
        search_filter = or_(
            IPAllocation.ip_address.ilike(f"%{query}%"),
            IPAllocation.hostname.ilike(f"%{query}%"),
            IPAllocation.mac_address.ilike(f"%{query}%"),
            IPAllocation.owner.ilike(f"%{query}%")
        )
        
        result = await session.execute(
            select(IPAllocation).where(search_filter).limit(100)
        )
        allocations = result.scalars().all()
        
        allocation_responses = [_allocation_to_response(a) for a in allocations]
        
        return IPSearchResponse(
            results=allocation_responses,
            total=len(allocation_responses)
        )
    
    except Exception as e:
        logger.error(f"Error searching IPs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search IP allocations"
        )


# ============================================================================
# Helper Functions
# ============================================================================

async def _pool_to_response(pool: IPPool, session: AsyncSession) -> IPPoolResponse:
    """Convert IPPool database model to response model"""
    # Calculate statistics
    alloc_result = await session.execute(
        select(func.count()).select_from(IPAllocation).where(IPAllocation.pool_id == pool.id)
    )
    used_ips = alloc_result.scalar() or 0
    
    # Calculate total IPs in network (excluding network and broadcast)
    try:
        net = ipaddress.ip_network(pool.network, strict=False)
        total_ips = max(1, net.num_addresses - 2)  # Exclude network and broadcast
    except:
        total_ips = 0
    
    available_ips = max(0, total_ips - used_ips)
    utilization_percent = (used_ips / total_ips * 100) if total_ips > 0 else 0
    
    return IPPoolResponse(
        id=pool.id,
        name=pool.name,
        network=str(pool.network),
        description=pool.description,
        vlan_id=pool.vlan_id,
        gateway=pool.gateway,
        total_ips=total_ips,
        used_ips=used_ips,
        available_ips=available_ips,
        utilization_percent=round(utilization_percent, 2),
        createTimestamp=pool.created_at.isoformat() if pool.created_at else None,
        modifyTimestamp=pool.updated_at.isoformat() if pool.updated_at else None
    )


def _allocation_to_response(allocation: IPAllocation) -> IPAllocationResponse:
    """Convert IPAllocation database model to response model"""
    return IPAllocationResponse(
        id=allocation.id,
        pool_id=allocation.pool_id,
        ip_address=allocation.ip_address,
        hostname=allocation.hostname,
        mac_address=allocation.mac_address,
        allocation_type=allocation.status,  # Map status to allocation_type for compatibility
        description=allocation.description,
        allocated_at=allocation.allocated_at.isoformat() if allocation.allocated_at else None,
        allocated_by=allocation.allocated_by,
        createTimestamp=allocation.created_at.isoformat() if allocation.created_at else None,
        modifyTimestamp=allocation.updated_at.isoformat() if allocation.updated_at else None
    )
