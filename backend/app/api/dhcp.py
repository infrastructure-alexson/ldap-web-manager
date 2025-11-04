#!/usr/bin/env python3
"""
DHCP Management API endpoints for Kea DHCP
"""

import ldap
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
import ipaddress
from app.models.dhcp import (
    DHCPSubnetCreate, DHCPSubnetUpdate, DHCPSubnetResponse, DHCPSubnetListResponse,
    DHCPPoolCreate, DHCPPoolResponse,
    DHCPHostCreate, DHCPHostUpdate, DHCPHostResponse, DHCPHostListResponse,
    DHCPStatsResponse
)
from app.auth.jwt import get_current_user, require_admin, require_operator
from app.ldap.connection import get_ldap_connection
from app.config import get_config
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# DHCP SUBNETS
# ============================================================================

@router.get("/subnets", response_model=DHCPSubnetListResponse)
async def list_subnets(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    List all DHCP subnets
    
    Args:
        page: Page number
        page_size: Items per page
        search: Search term
        current_user: Authenticated user
        
    Returns:
        List of DHCP subnets
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    # Build search filter
    if search:
        search_filter = f"(&(objectClass=dhcpSubnet)(|(cn=*{search}*)(description=*{search}*)))"
    else:
        search_filter = "(objectClass=dhcpSubnet)"
    
    try:
        # Search in cn=config under DHCP
        config_dn = f"cn=config,{config.ldap_dhcp_ou}"
        results = ldap_conn.search(
            config_dn,
            search_filter,
            attributes=['cn', 'dhcpNetMask', 'dhcpOption', 'dhcpRange', 
                       'description', 'createTimestamp', 'modifyTimestamp']
        )
        
        # Convert to DHCPSubnetResponse objects
        subnets = []
        for subnet_dn, attrs in results:
            # Skip the config container itself
            if subnet_dn == config_dn:
                continue
            
            subnet_data = {
                'dn': subnet_dn,
                'cn': attrs.get('cn', [b''])[0].decode('utf-8'),
                'dhcpNetMask': int(attrs.get('dhcpNetMask', [b'24'])[0]),
                'dhcpOption': [opt.decode('utf-8') for opt in attrs.get('dhcpOption', [])] if attrs.get('dhcpOption') else None,
                'dhcpRange': [rng.decode('utf-8') for rng in attrs.get('dhcpRange', [])] if attrs.get('dhcpRange') else None,
                'description': attrs.get('description', [b''])[0].decode('utf-8') if attrs.get('description') else None,
                'createTimestamp': attrs.get('createTimestamp', [b''])[0].decode('utf-8') if attrs.get('createTimestamp') else None,
                'modifyTimestamp': attrs.get('modifyTimestamp', [b''])[0].decode('utf-8') if attrs.get('modifyTimestamp') else None,
            }
            subnets.append(DHCPSubnetResponse(**subnet_data))
        
        # Pagination
        total = len(subnets)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_subnets = subnets[start:end]
        
        return {
            "subnets": paginated_subnets,
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
    except ldap.LDAPError as e:
        logger.error(f"LDAP error listing DHCP subnets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list DHCP subnets: {str(e)}"
        )


@router.get("/subnets/{subnet_id}", response_model=DHCPSubnetResponse)
async def get_subnet(
    subnet_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get DHCP subnet by ID
    
    Args:
        subnet_id: Subnet identifier
        current_user: Authenticated user
        
    Returns:
        DHCP subnet information
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    config_dn = f"cn=config,{config.ldap_dhcp_ou}"
    subnet_dn = f"cn={subnet_id},{config_dn}"
    
    try:
        results = ldap_conn.search(
            subnet_dn,
            "(objectClass=dhcpSubnet)",
            attributes=['cn', 'dhcpNetMask', 'dhcpOption', 'dhcpRange',
                       'description', 'createTimestamp', 'modifyTimestamp'],
            scope=ldap.SCOPE_BASE
        )
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"DHCP subnet not found: {subnet_id}"
            )
        
        _, attrs = results[0]
        subnet_data = {
            'dn': subnet_dn,
            'cn': attrs.get('cn', [b''])[0].decode('utf-8'),
            'dhcpNetMask': int(attrs.get('dhcpNetMask', [b'24'])[0]),
            'dhcpOption': [opt.decode('utf-8') for opt in attrs.get('dhcpOption', [])] if attrs.get('dhcpOption') else None,
            'dhcpRange': [rng.decode('utf-8') for rng in attrs.get('dhcpRange', [])] if attrs.get('dhcpRange') else None,
            'description': attrs.get('description', [b''])[0].decode('utf-8') if attrs.get('description') else None,
            'createTimestamp': attrs.get('createTimestamp', [b''])[0].decode('utf-8') if attrs.get('createTimestamp') else None,
            'modifyTimestamp': attrs.get('modifyTimestamp', [b''])[0].decode('utf-8') if attrs.get('modifyTimestamp') else None,
        }
        
        return DHCPSubnetResponse(**subnet_data)
        
    except ldap.LDAPError as e:
        logger.error(f"LDAP error getting DHCP subnet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get DHCP subnet: {str(e)}"
        )


@router.post("/subnets", response_model=DHCPSubnetResponse, status_code=status.HTTP_201_CREATED)
async def create_subnet(
    subnet: DHCPSubnetCreate,
    current_user: dict = Depends(require_operator)
):
    """
    Create new DHCP subnet
    
    Args:
        subnet: Subnet information
        current_user: Authenticated user (operator or admin)
        
    Returns:
        Created subnet
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    config_dn = f"cn=config,{config.ldap_dhcp_ou}"
    subnet_dn = f"cn={subnet.cn},{config_dn}"
    
    # Build LDAP attributes
    attributes = {
        'objectClass': [b'dhcpSubnet', b'top'],
        'cn': [subnet.cn.encode('utf-8')],
        'dhcpNetMask': [str(subnet.dhcpNetMask).encode('utf-8')],
    }
    
    # Add optional attributes
    if subnet.dhcpOption:
        attributes['dhcpOption'] = [opt.encode('utf-8') for opt in subnet.dhcpOption]
    if subnet.dhcpRange:
        attributes['dhcpRange'] = [rng.encode('utf-8') for rng in subnet.dhcpRange]
    if subnet.description:
        attributes['description'] = [subnet.description.encode('utf-8')]
    
    try:
        ldap_conn.add(subnet_dn, attributes)
        logger.info(f"DHCP subnet created: {subnet.cn} by {current_user.get('username')}")
        
        # Retrieve and return created subnet
        return await get_subnet(subnet.cn, current_user)
        
    except ldap.ALREADY_EXISTS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"DHCP subnet already exists: {subnet.cn}"
        )
    except ldap.LDAPError as e:
        logger.error(f"LDAP error creating DHCP subnet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create DHCP subnet: {str(e)}"
        )


@router.patch("/subnets/{subnet_id}", response_model=DHCPSubnetResponse)
async def update_subnet(
    subnet_id: str,
    subnet_update: DHCPSubnetUpdate,
    current_user: dict = Depends(require_operator)
):
    """
    Update DHCP subnet
    
    Args:
        subnet_id: Subnet identifier
        subnet_update: Fields to update
        current_user: Authenticated user (operator or admin)
        
    Returns:
        Updated subnet
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    config_dn = f"cn=config,{config.ldap_dhcp_ou}"
    subnet_dn = f"cn={subnet_id},{config_dn}"
    
    # Build modification list
    modifications = []
    update_dict = subnet_update.dict(exclude_unset=True)
    
    for attr, value in update_dict.items():
        if value is not None:
            if isinstance(value, list):
                modifications.append((
                    ldap.MOD_REPLACE,
                    attr,
                    [v.encode('utf-8') for v in value]
                ))
            else:
                modifications.append((
                    ldap.MOD_REPLACE,
                    attr,
                    [str(value).encode('utf-8')]
                ))
    
    if not modifications:
        # No changes
        return await get_subnet(subnet_id, current_user)
    
    try:
        ldap_conn.modify(subnet_dn, modifications)
        logger.info(f"DHCP subnet updated: {subnet_id} by {current_user.get('username')}")
        
        # Retrieve and return updated subnet
        return await get_subnet(subnet_id, current_user)
        
    except ldap.NO_SUCH_OBJECT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"DHCP subnet not found: {subnet_id}"
        )
    except ldap.LDAPError as e:
        logger.error(f"LDAP error updating DHCP subnet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update DHCP subnet: {str(e)}"
        )


@router.delete("/subnets/{subnet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subnet(
    subnet_id: str,
    current_user: dict = Depends(require_admin)
):
    """
    Delete DHCP subnet
    
    Args:
        subnet_id: Subnet identifier
        current_user: Authenticated user (admin only)
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    config_dn = f"cn=config,{config.ldap_dhcp_ou}"
    subnet_dn = f"cn={subnet_id},{config_dn}"
    
    try:
        ldap_conn.delete(subnet_dn)
        logger.info(f"DHCP subnet deleted: {subnet_id} by {current_user.get('username')}")
        
    except ldap.NO_SUCH_OBJECT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"DHCP subnet not found: {subnet_id}"
        )
    except ldap.NOT_ALLOWED_ON_NONLEAF:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete subnet with existing hosts or pools. Delete them first."
        )
    except ldap.LDAPError as e:
        logger.error(f"LDAP error deleting DHCP subnet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete DHCP subnet: {str(e)}"
        )


# ============================================================================
# DHCP HOSTS (Static Reservations)
# ============================================================================

@router.get("/subnets/{subnet_id}/hosts", response_model=DHCPHostListResponse)
async def list_hosts(
    subnet_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    List all static host reservations in a subnet
    
    Args:
        subnet_id: Subnet identifier
        current_user: Authenticated user
        
    Returns:
        List of DHCP host reservations
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    config_dn = f"cn=config,{config.ldap_dhcp_ou}"
    subnet_dn = f"cn={subnet_id},{config_dn}"
    
    try:
        results = ldap_conn.search(
            subnet_dn,
            "(objectClass=dhcpHost)",
            attributes=['cn', 'dhcpHWAddress', 'dhcpStatements', 'dhcpOption',
                       'description', 'createTimestamp', 'modifyTimestamp'],
            scope=ldap.SCOPE_ONELEVEL
        )
        
        # Convert to DHCPHostResponse objects
        hosts = []
        for host_dn, attrs in results:
            hw_addr = attrs.get('dhcpHWAddress', [b''])[0].decode('utf-8')
            statements = [stmt.decode('utf-8') for stmt in attrs.get('dhcpStatements', [])]
            
            # Parse MAC and IP
            mac = hw_addr.replace('ethernet ', '') if 'ethernet' in hw_addr else None
            ip = None
            for stmt in statements:
                if 'fixed-address' in stmt:
                    ip = stmt.replace('fixed-address ', '').strip()
                    break
            
            host_data = {
                'dn': host_dn,
                'cn': attrs.get('cn', [b''])[0].decode('utf-8'),
                'dhcpHWAddress': hw_addr,
                'dhcpStatements': statements,
                'dhcpOption': [opt.decode('utf-8') for opt in attrs.get('dhcpOption', [])] if attrs.get('dhcpOption') else None,
                'description': attrs.get('description', [b''])[0].decode('utf-8') if attrs.get('description') else None,
                'createTimestamp': attrs.get('createTimestamp', [b''])[0].decode('utf-8') if attrs.get('createTimestamp') else None,
                'modifyTimestamp': attrs.get('modifyTimestamp', [b''])[0].decode('utf-8') if attrs.get('modifyTimestamp') else None,
                'mac_address': mac,
                'ip_address': ip,
            }
            hosts.append(DHCPHostResponse(**host_data))
        
        return {
            "hosts": hosts,
            "total": len(hosts),
            "subnet": subnet_id
        }
        
    except ldap.NO_SUCH_OBJECT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"DHCP subnet not found: {subnet_id}"
        )
    except ldap.LDAPError as e:
        logger.error(f"LDAP error listing DHCP hosts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list DHCP hosts: {str(e)}"
        )


@router.post("/subnets/{subnet_id}/hosts", response_model=DHCPHostResponse, status_code=status.HTTP_201_CREATED)
async def create_host(
    subnet_id: str,
    host: DHCPHostCreate,
    current_user: dict = Depends(require_operator)
):
    """
    Create static host reservation
    
    Args:
        subnet_id: Subnet identifier
        host: Host reservation information
        current_user: Authenticated user (operator or admin)
        
    Returns:
        Created host reservation
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    config_dn = f"cn=config,{config.ldap_dhcp_ou}"
    subnet_dn = f"cn={subnet_id},{config_dn}"
    host_dn = f"cn={host.cn},{subnet_dn}"
    
    # Build LDAP attributes
    attributes = {
        'objectClass': [b'dhcpHost', b'top'],
        'cn': [host.cn.encode('utf-8')],
        'dhcpHWAddress': [host.dhcpHWAddress.encode('utf-8')],
        'dhcpStatements': [stmt.encode('utf-8') for stmt in host.dhcpStatements],
    }
    
    # Add optional attributes
    if host.dhcpOption:
        attributes['dhcpOption'] = [opt.encode('utf-8') for opt in host.dhcpOption]
    if host.description:
        attributes['description'] = [host.description.encode('utf-8')]
    
    try:
        ldap_conn.add(host_dn, attributes)
        logger.info(f"DHCP host created: {host.cn} in {subnet_id} by {current_user.get('username')}")
        
        # Parse and return created host
        mac = host.dhcpHWAddress.replace('ethernet ', '')
        ip = None
        for stmt in host.dhcpStatements:
            if 'fixed-address' in stmt:
                ip = stmt.replace('fixed-address ', '').strip()
                break
        
        return DHCPHostResponse(
            dn=host_dn,
            cn=host.cn,
            dhcpHWAddress=host.dhcpHWAddress,
            dhcpStatements=host.dhcpStatements,
            dhcpOption=host.dhcpOption,
            description=host.description,
            mac_address=mac,
            ip_address=ip,
        )
        
    except ldap.ALREADY_EXISTS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"DHCP host already exists: {host.cn}"
        )
    except ldap.LDAPError as e:
        logger.error(f"LDAP error creating DHCP host: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create DHCP host: {str(e)}"
        )


@router.delete("/subnets/{subnet_id}/hosts/{host_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_host(
    subnet_id: str,
    host_id: str,
    current_user: dict = Depends(require_operator)
):
    """
    Delete static host reservation
    
    Args:
        subnet_id: Subnet identifier
        host_id: Host identifier
        current_user: Authenticated user (operator or admin)
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    config_dn = f"cn=config,{config.ldap_dhcp_ou}"
    subnet_dn = f"cn={subnet_id},{config_dn}"
    host_dn = f"cn={host_id},{subnet_dn}"
    
    try:
        ldap_conn.delete(host_dn)
        logger.info(f"DHCP host deleted: {host_id} from {subnet_id} by {current_user.get('username')}")
        
    except ldap.NO_SUCH_OBJECT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"DHCP host not found: {host_id}"
        )
    except ldap.LDAPError as e:
        logger.error(f"LDAP error deleting DHCP host: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete DHCP host: {str(e)}"
        )


# ============================================================================
# DHCP STATISTICS
# ============================================================================

@router.get("/stats", response_model=DHCPStatsResponse)
async def get_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    Get DHCP statistics
    
    Args:
        current_user: Authenticated user
        
    Returns:
        DHCP statistics
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    try:
        config_dn = f"cn=config,{config.ldap_dhcp_ou}"
        
        # Count subnets
        subnets = ldap_conn.search(config_dn, "(objectClass=dhcpSubnet)")
        total_subnets = len([s for s in subnets if s[0] != config_dn])
        
        # Count static hosts
        hosts = ldap_conn.search(config_dn, "(objectClass=dhcpHost)")
        total_static_hosts = len(hosts)
        
        # Calculate IP addresses (simplified)
        total_ips = 0
        for subnet_dn, attrs in subnets:
            if subnet_dn == config_dn:
                continue
            # Simple calculation based on netmask
            netmask = int(attrs.get('dhcpNetMask', [b'24'])[0])
            total_ips += 2 ** (32 - netmask) - 2  # Exclude network and broadcast
        
        return {
            "total_subnets": total_subnets,
            "total_pools": 0,  # Pools not fully implemented
            "total_static_hosts": total_static_hosts,
            "total_ip_addresses": total_ips,
            "allocated_addresses": total_static_hosts,
            "available_addresses": total_ips - total_static_hosts,
            "utilization_percent": round((total_static_hosts / total_ips * 100) if total_ips > 0 else 0, 2)
        }
        
    except ldap.LDAPError as e:
        logger.error(f"LDAP error getting DHCP stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get DHCP stats: {str(e)}"
        )

