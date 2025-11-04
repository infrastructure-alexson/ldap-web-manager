#!/usr/bin/env python3
"""
DNS Management API endpoints
"""

import ldap
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
import time
from app.models.dns import (
    DNSZoneCreate, DNSZoneUpdate, DNSZoneResponse, DNSZoneListResponse,
    DNSRecordCreate, DNSRecordUpdate, DNSRecordResponse, DNSRecordListResponse
)
from app.auth.jwt import get_current_user, require_admin, require_operator
from app.ldap.connection import get_ldap_connection
from app.config import get_config
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def get_next_serial() -> int:
    """Generate SOA serial number (YYYYMMDDnn format)"""
    from datetime import datetime
    date_part = datetime.now().strftime('%Y%m%d')
    return int(f"{date_part}01")


# ============================================================================
# DNS ZONES
# ============================================================================

@router.get("/zones", response_model=DNSZoneListResponse)
async def list_zones(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    List all DNS zones
    
    Args:
        page: Page number
        page_size: Items per page
        search: Search term
        current_user: Authenticated user
        
    Returns:
        List of DNS zones
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    # Build search filter
    if search:
        search_filter = f"(&(objectClass=idnsZone)(|(idnsName=*{search}*)(description=*{search}*)))"
    else:
        search_filter = "(objectClass=idnsZone)"
    
    try:
        results = ldap_conn.search(
            config.ldap_dns_ou,
            search_filter,
            attributes=['idnsName', 'idnsSOAserial', 'idnsSOArefresh', 'idnsSOAretry',
                       'idnsSOAexpire', 'idnsSOAminimum', 'idnsSOAmName', 'idnsSOArName',
                       'description', 'createTimestamp', 'modifyTimestamp']
        )
        
        # Convert to DNSZoneResponse objects
        zones = []
        for zone_dn, attrs in results:
            zone_data = {
                'dn': zone_dn,
                'idnsName': attrs.get('idnsName', [b''])[0].decode('utf-8'),
                'idnsSOAserial': int(attrs.get('idnsSOAserial', [b'0'])[0]) if attrs.get('idnsSOAserial') else None,
                'idnsSOArefresh': int(attrs.get('idnsSOArefresh', [b'10800'])[0]),
                'idnsSOAretry': int(attrs.get('idnsSOAretry', [b'3600'])[0]),
                'idnsSOAexpire': int(attrs.get('idnsSOAexpire', [b'604800'])[0]),
                'idnsSOAminimum': int(attrs.get('idnsSOAminimum', [b'86400'])[0]),
                'idnsSOAmName': attrs.get('idnsSOAmName', [b''])[0].decode('utf-8'),
                'idnsSOArName': attrs.get('idnsSOArName', [b''])[0].decode('utf-8'),
                'description': attrs.get('description', [b''])[0].decode('utf-8') if attrs.get('description') else None,
                'createTimestamp': attrs.get('createTimestamp', [b''])[0].decode('utf-8') if attrs.get('createTimestamp') else None,
                'modifyTimestamp': attrs.get('modifyTimestamp', [b''])[0].decode('utf-8') if attrs.get('modifyTimestamp') else None,
            }
            zones.append(DNSZoneResponse(**zone_data))
        
        # Pagination
        total = len(zones)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_zones = zones[start:end]
        
        return {
            "zones": paginated_zones,
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
    except ldap.LDAPError as e:
        logger.error(f"LDAP error listing DNS zones: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list DNS zones: {str(e)}"
        )


@router.get("/zones/{zone_name}", response_model=DNSZoneResponse)
async def get_zone(
    zone_name: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get DNS zone by name
    
    Args:
        zone_name: Zone name
        current_user: Authenticated user
        
    Returns:
        DNS zone information
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    try:
        results = ldap_conn.search(
            config.ldap_dns_ou,
            f"(idnsName={zone_name})",
            attributes=['idnsName', 'idnsSOAserial', 'idnsSOArefresh', 'idnsSOAretry',
                       'idnsSOAexpire', 'idnsSOAminimum', 'idnsSOAmName', 'idnsSOArName',
                       'description', 'createTimestamp', 'modifyTimestamp']
        )
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"DNS zone not found: {zone_name}"
            )
        
        zone_dn, attrs = results[0]
        zone_data = {
            'dn': zone_dn,
            'idnsName': attrs.get('idnsName', [b''])[0].decode('utf-8'),
            'idnsSOAserial': int(attrs.get('idnsSOAserial', [b'0'])[0]) if attrs.get('idnsSOAserial') else None,
            'idnsSOArefresh': int(attrs.get('idnsSOArefresh', [b'10800'])[0]),
            'idnsSOAretry': int(attrs.get('idnsSOAretry', [b'3600'])[0]),
            'idnsSOAexpire': int(attrs.get('idnsSOAexpire', [b'604800'])[0]),
            'idnsSOAminimum': int(attrs.get('idnsSOAminimum', [b'86400'])[0]),
            'idnsSOAmName': attrs.get('idnsSOAmName', [b''])[0].decode('utf-8'),
            'idnsSOArName': attrs.get('idnsSOArName', [b''])[0].decode('utf-8'),
            'description': attrs.get('description', [b''])[0].decode('utf-8') if attrs.get('description') else None,
            'createTimestamp': attrs.get('createTimestamp', [b''])[0].decode('utf-8') if attrs.get('createTimestamp') else None,
            'modifyTimestamp': attrs.get('modifyTimestamp', [b''])[0].decode('utf-8') if attrs.get('modifyTimestamp') else None,
        }
        
        return DNSZoneResponse(**zone_data)
        
    except ldap.LDAPError as e:
        logger.error(f"LDAP error getting DNS zone: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get DNS zone: {str(e)}"
        )


@router.post("/zones", response_model=DNSZoneResponse, status_code=status.HTTP_201_CREATED)
async def create_zone(
    zone: DNSZoneCreate,
    current_user: dict = Depends(require_operator)
):
    """
    Create new DNS zone
    
    Args:
        zone: Zone information
        current_user: Authenticated user (operator or admin)
        
    Returns:
        Created zone
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    # Generate serial if not provided
    if not zone.idnsSOAserial:
        zone.idnsSOAserial = get_next_serial()
    
    # Build DN
    zone_dn = f"idnsName={zone.idnsName},{config.ldap_dns_ou}"
    
    # Build LDAP attributes
    attributes = {
        'objectClass': [b'idnsZone', b'idnsRecord', b'top'],
        'idnsName': [zone.idnsName.encode('utf-8')],
        'idnsSOAserial': [str(zone.idnsSOAserial).encode('utf-8')],
        'idnsSOArefresh': [str(zone.idnsSOArefresh).encode('utf-8')],
        'idnsSOAretry': [str(zone.idnsSOAretry).encode('utf-8')],
        'idnsSOAexpire': [str(zone.idnsSOAexpire).encode('utf-8')],
        'idnsSOAminimum': [str(zone.idnsSOAminimum).encode('utf-8')],
        'idnsSOAmName': [zone.idnsSOAmName.encode('utf-8')],
        'idnsSOArName': [zone.idnsSOArName.encode('utf-8')],
    }
    
    # Add optional attributes
    if zone.description:
        attributes['description'] = [zone.description.encode('utf-8')]
    
    try:
        ldap_conn.add(zone_dn, attributes)
        logger.info(f"DNS zone created: {zone.idnsName} by {current_user.get('username')}")
        
        # Retrieve and return created zone
        return await get_zone(zone.idnsName, current_user)
        
    except ldap.ALREADY_EXISTS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"DNS zone already exists: {zone.idnsName}"
        )
    except ldap.LDAPError as e:
        logger.error(f"LDAP error creating DNS zone: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create DNS zone: {str(e)}"
        )


@router.patch("/zones/{zone_name}", response_model=DNSZoneResponse)
async def update_zone(
    zone_name: str,
    zone_update: DNSZoneUpdate,
    current_user: dict = Depends(require_operator)
):
    """
    Update DNS zone
    
    Args:
        zone_name: Zone name
        zone_update: Fields to update
        current_user: Authenticated user (operator or admin)
        
    Returns:
        Updated zone
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    # Build DN
    zone_dn = f"idnsName={zone_name},{config.ldap_dns_ou}"
    
    # Build modification list
    modifications = []
    update_dict = zone_update.dict(exclude_unset=True)
    
    for attr, value in update_dict.items():
        if value is not None:
            modifications.append((
                ldap.MOD_REPLACE,
                attr,
                [str(value).encode('utf-8')]
            ))
    
    # Always increment serial on update
    current_serial = get_next_serial()
    modifications.append((
        ldap.MOD_REPLACE,
        'idnsSOAserial',
        [str(current_serial).encode('utf-8')]
    ))
    
    if not modifications:
        # No changes
        return await get_zone(zone_name, current_user)
    
    try:
        ldap_conn.modify(zone_dn, modifications)
        logger.info(f"DNS zone updated: {zone_name} by {current_user.get('username')}")
        
        # Retrieve and return updated zone
        return await get_zone(zone_name, current_user)
        
    except ldap.NO_SUCH_OBJECT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"DNS zone not found: {zone_name}"
        )
    except ldap.LDAPError as e:
        logger.error(f"LDAP error updating DNS zone: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update DNS zone: {str(e)}"
        )


@router.delete("/zones/{zone_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_zone(
    zone_name: str,
    current_user: dict = Depends(require_admin)
):
    """
    Delete DNS zone
    
    Args:
        zone_name: Zone name
        current_user: Authenticated user (admin only)
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    # Build DN
    zone_dn = f"idnsName={zone_name},{config.ldap_dns_ou}"
    
    try:
        # Note: This will fail if zone has records (children)
        # In production, you'd want to recursively delete or warn
        ldap_conn.delete(zone_dn)
        logger.info(f"DNS zone deleted: {zone_name} by {current_user.get('username')}")
        
    except ldap.NO_SUCH_OBJECT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"DNS zone not found: {zone_name}"
        )
    except ldap.NOT_ALLOWED_ON_NONLEAF:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete zone with existing records. Delete records first."
        )
    except ldap.LDAPError as e:
        logger.error(f"LDAP error deleting DNS zone: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete DNS zone: {str(e)}"
        )


# ============================================================================
# DNS RECORDS
# ============================================================================

@router.get("/zones/{zone_name}/records", response_model=DNSRecordListResponse)
async def list_records(
    zone_name: str,
    current_user: dict = Depends(get_current_user)
):
    """
    List all records in a DNS zone
    
    Args:
        zone_name: Zone name
        current_user: Authenticated user
        
    Returns:
        List of DNS records
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    zone_dn = f"idnsName={zone_name},{config.ldap_dns_ou}"
    
    try:
        # Search for all records under the zone
        results = ldap_conn.search(
            zone_dn,
            "(objectClass=idnsRecord)",
            attributes=['idnsName', 'aRecord', 'aAAARecord', 'cNAMERecord', 
                       'mXRecord', 'tXTRecord', 'pTRRecord', 'sRVRecord', 
                       'nSRecord', 'createTimestamp', 'modifyTimestamp'],
            scope=ldap.SCOPE_ONELEVEL
        )
        
        # Convert to DNSRecordResponse objects
        records = []
        for record_dn, attrs in results:
            # Skip the zone itself
            if record_dn == zone_dn:
                continue
            
            record_name = attrs.get('idnsName', [b''])[0].decode('utf-8')
            
            # Process each record type
            for record_type, attr_name in [
                ('A', 'aRecord'),
                ('AAAA', 'aAAARecord'),
                ('CNAME', 'cNAMERecord'),
                ('MX', 'mXRecord'),
                ('TXT', 'tXTRecord'),
                ('PTR', 'pTRRecord'),
                ('SRV', 'sRVRecord'),
                ('NS', 'nSRecord'),
            ]:
                values = attrs.get(attr_name, [])
                for value in values:
                    record_data = {
                        'dn': record_dn,
                        'idnsName': record_name,
                        'record_type': record_type,
                        'value': value.decode('utf-8'),
                        'createTimestamp': attrs.get('createTimestamp', [b''])[0].decode('utf-8') if attrs.get('createTimestamp') else None,
                        'modifyTimestamp': attrs.get('modifyTimestamp', [b''])[0].decode('utf-8') if attrs.get('modifyTimestamp') else None,
                    }
                    records.append(DNSRecordResponse(**record_data))
        
        return {
            "records": records,
            "total": len(records),
            "zone": zone_name
        }
        
    except ldap.NO_SUCH_OBJECT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"DNS zone not found: {zone_name}"
        )
    except ldap.LDAPError as e:
        logger.error(f"LDAP error listing DNS records: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list DNS records: {str(e)}"
        )

