#!/usr/bin/env python3
"""
Group Management API endpoints
"""

import ldap
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.models.group import (
    GroupCreate, GroupUpdate, GroupResponse, GroupListResponse,
    GroupAddMember, GroupRemoveMember
)
from app.auth.jwt import get_current_user, require_admin, require_operator
from app.ldap.connection import get_ldap_connection
from app.config import get_config
from app.db.base import get_session
from app.db.models import AuditAction
from app.db.audit import get_audit_logger
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def get_next_gid_number() -> int:
    """Get next available GID number"""
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    # Search for highest GID number
    results = ldap_conn.search(
        config.ldap_groups_ou,
        "(objectClass=posixGroup)",
        attributes=['gidNumber']
    )
    
    max_gid = 1000  # Start from 1000
    for _, attrs in results:
        gid_num = int(attrs.get('gidNumber', [b'0'])[0])
        if gid_num > max_gid:
            max_gid = gid_num
    
    return max_gid + 1


@router.get("", response_model=GroupListResponse)
async def list_groups(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    List all groups with pagination and search
    
    Args:
        page: Page number
        page_size: Items per page
        search: Search term (searches cn, description)
        current_user: Authenticated user
        
    Returns:
        List of groups
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    # Build search filter
    if search:
        search_filter = f"(&(objectClass=posixGroup)(|(cn=*{search}*)(description=*{search}*)))"
    else:
        search_filter = "(objectClass=posixGroup)"
    
    try:
        results = ldap_conn.search(
            config.ldap_groups_ou,
            search_filter,
            attributes=['cn', 'description', 'gidNumber', 'memberUid',
                       'createTimestamp', 'modifyTimestamp']
        )
        
        # Convert to GroupResponse objects
        groups = []
        for group_dn, attrs in results:
            group_data = {
                'dn': group_dn,
                'cn': attrs.get('cn', [b''])[0].decode('utf-8'),
                'description': attrs.get('description', [b''])[0].decode('utf-8') if attrs.get('description') else None,
                'gidNumber': int(attrs.get('gidNumber', [b'0'])[0]) if attrs.get('gidNumber') else None,
                'memberUid': [m.decode('utf-8') for m in attrs.get('memberUid', [])],
                'createTimestamp': attrs.get('createTimestamp', [b''])[0].decode('utf-8') if attrs.get('createTimestamp') else None,
                'modifyTimestamp': attrs.get('modifyTimestamp', [b''])[0].decode('utf-8') if attrs.get('modifyTimestamp') else None,
            }
            groups.append(GroupResponse(**group_data))
        
        # Pagination
        total = len(groups)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_groups = groups[start:end]
        
        return {
            "groups": paginated_groups,
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
    except ldap.LDAPError as e:
        logger.error(f"LDAP error listing groups: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list groups: {str(e)}"
        )


@router.get("/{group_name}", response_model=GroupResponse)
async def get_group(
    group_name: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get group by name
    
    Args:
        group_name: Group name (cn)
        current_user: Authenticated user
        
    Returns:
        Group information
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    try:
        results = ldap_conn.search(
            config.ldap_groups_ou,
            f"(cn={group_name})",
            attributes=['cn', 'description', 'gidNumber', 'memberUid',
                       'createTimestamp', 'modifyTimestamp']
        )
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group not found: {group_name}"
            )
        
        group_dn, attrs = results[0]
        group_data = {
            'dn': group_dn,
            'cn': attrs.get('cn', [b''])[0].decode('utf-8'),
            'description': attrs.get('description', [b''])[0].decode('utf-8') if attrs.get('description') else None,
            'gidNumber': int(attrs.get('gidNumber', [b'0'])[0]) if attrs.get('gidNumber') else None,
            'memberUid': [m.decode('utf-8') for m in attrs.get('memberUid', [])],
            'createTimestamp': attrs.get('createTimestamp', [b''])[0].decode('utf-8') if attrs.get('createTimestamp') else None,
            'modifyTimestamp': attrs.get('modifyTimestamp', [b''])[0].decode('utf-8') if attrs.get('modifyTimestamp') else None,
        }
        
        return GroupResponse(**group_data)
        
    except ldap.LDAPError as e:
        logger.error(f"LDAP error getting group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get group: {str(e)}"
        )


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group: GroupCreate,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_operator)
):
    """
    Create new group
    
    Args:
        group: Group information
        session: Database session for audit logging
        current_user: Authenticated user (operator or admin)
        
    Returns:
        Created group
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    # Generate GID if not provided
    if not group.gidNumber:
        group.gidNumber = get_next_gid_number()
    
    # Build DN
    group_dn = f"cn={group.cn},{config.ldap_groups_ou}"
    
    # Build LDAP attributes
    attributes = {
        'objectClass': [b'posixGroup', b'top'],
        'cn': [group.cn.encode('utf-8')],
        'gidNumber': [str(group.gidNumber).encode('utf-8')],
    }
    
    # Add optional attributes
    if group.description:
        attributes['description'] = [group.description.encode('utf-8')]
    if group.memberUid:
        attributes['memberUid'] = [m.encode('utf-8') for m in group.memberUid]
    
    try:
        ldap_conn.add(group_dn, attributes)
        logger.info(f"Group created: {group.cn} by {current_user.get('username')}")
        
        # Audit log
        audit = await get_audit_logger(session)
        await audit.log_group_action(
            AuditAction.CREATE,
            group_name=group.cn,
            user_id=current_user.get('username'),
            details={
                'gidNumber': group.gidNumber,
                'description': group.description,
                'members': group.memberUid or []
            }
        )
        await session.commit()
        
        # Retrieve and return created group
        return await get_group(group.cn, current_user)
        
    except ldap.ALREADY_EXISTS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Group already exists: {group.cn}"
        )
    except ldap.LDAPError as e:
        logger.error(f"LDAP error creating group: {e}")
        
        # Audit log failure
        audit = await get_audit_logger(session)
        await audit.log_group_action(
            AuditAction.CREATE,
            group_name=group.cn,
            user_id=current_user.get('username'),
            status="failure",
            details={'error': str(e)}
        )
        await session.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create group: {str(e)}"
        )


@router.patch("/{group_name}", response_model=GroupResponse)
async def update_group(
    group_name: str,
    group_update: GroupUpdate,
    current_user: dict = Depends(require_operator)
):
    """
    Update group information
    
    Args:
        group_name: Group name (cn)
        group_update: Fields to update
        current_user: Authenticated user (operator or admin)
        
    Returns:
        Updated group
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    # Build DN
    group_dn = f"cn={group_name},{config.ldap_groups_ou}"
    
    # Build modification list
    modifications = []
    update_dict = group_update.dict(exclude_unset=True)
    
    for attr, value in update_dict.items():
        if value is not None:
            if attr == 'memberUid':
                # Replace entire member list
                modifications.append((
                    ldap.MOD_REPLACE,
                    attr,
                    [m.encode('utf-8') for m in value]
                ))
            else:
                modifications.append((
                    ldap.MOD_REPLACE,
                    attr,
                    [value.encode('utf-8')]
                ))
    
    if not modifications:
        # No changes
        return await get_group(group_name, current_user)
    
    try:
        ldap_conn.modify(group_dn, modifications)
        logger.info(f"Group updated: {group_name} by {current_user.get('username')}")
        
        # Retrieve and return updated group
        return await get_group(group_name, current_user)
        
    except ldap.NO_SUCH_OBJECT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group not found: {group_name}"
        )
    except ldap.LDAPError as e:
        logger.error(f"LDAP error updating group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update group: {str(e)}"
        )


@router.delete("/{group_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_name: str,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    """
    Delete group
    
    Args:
        group_name: Group name (cn)
        session: Database session for audit logging
        current_user: Authenticated user (admin only)
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    # Build DN
    group_dn = f"cn={group_name},{config.ldap_groups_ou}"
    
    try:
        ldap_conn.delete(group_dn)
        logger.info(f"Group deleted: {group_name} by {current_user.get('username')}")
        
        # Audit log
        audit = await get_audit_logger(session)
        await audit.log_group_action(
            AuditAction.DELETE,
            group_name=group_name,
            user_id=current_user.get('username')
        )
        await session.commit()
        
    except ldap.NO_SUCH_OBJECT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group not found: {group_name}"
        )
    except ldap.LDAPError as e:
        logger.error(f"LDAP error deleting group: {e}")
        
        # Audit log failure
        audit = await get_audit_logger(session)
        await audit.log_group_action(
            AuditAction.DELETE,
            group_name=group_name,
            user_id=current_user.get('username'),
            status="failure",
            details={'error': str(e)}
        )
        await session.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete group: {str(e)}"
        )


@router.post("/{group_name}/members", response_model=GroupResponse)
async def add_member(
    group_name: str,
    member: GroupAddMember,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_operator)
):
    """
    Add member to group
    
    Args:
        group_name: Group name (cn)
        member: Member to add
        session: Database session for audit logging
        current_user: Authenticated user (operator or admin)
        
    Returns:
        Updated group
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    # Build DN
    group_dn = f"cn={group_name},{config.ldap_groups_ou}"
    
    # Add member
    modifications = [(
        ldap.MOD_ADD,
        'memberUid',
        [member.username.encode('utf-8')]
    )]
    
    try:
        ldap_conn.modify(group_dn, modifications)
        logger.info(f"Member {member.username} added to group {group_name} by {current_user.get('username')}")
        
        # Audit log
        audit = await get_audit_logger(session)
        await audit.log_group_action(
            AuditAction.UPDATE,
            group_name=group_name,
            user_id=current_user.get('username'),
            details={'action': 'add_member', 'member': member.username}
        )
        await session.commit()
        
        return await get_group(group_name, current_user)
        
    except ldap.NO_SUCH_OBJECT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group not found: {group_name}"
        )
    except ldap.TYPE_OR_VALUE_EXISTS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User {member.username} is already a member of {group_name}"
        )
    except ldap.LDAPError as e:
        logger.error(f"LDAP error adding member: {e}")
        
        # Audit log failure
        audit = await get_audit_logger(session)
        await audit.log_group_action(
            AuditAction.UPDATE,
            group_name=group_name,
            user_id=current_user.get('username'),
            status="failure",
            details={'action': 'add_member', 'member': member.username, 'error': str(e)}
        )
        await session.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add member: {str(e)}"
        )


@router.delete("/{group_name}/members/{username}", response_model=GroupResponse)
async def remove_member(
    group_name: str,
    username: str,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_operator)
):
    """
    Remove member from group
    
    Args:
        group_name: Group name (cn)
        username: Username to remove
        session: Database session for audit logging
        current_user: Authenticated user (operator or admin)
        
    Returns:
        Updated group
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    # Build DN
    group_dn = f"cn={group_name},{config.ldap_groups_ou}"
    
    # Remove member
    modifications = [(
        ldap.MOD_DELETE,
        'memberUid',
        [username.encode('utf-8')]
    )]
    
    try:
        ldap_conn.modify(group_dn, modifications)
        logger.info(f"Member {username} removed from group {group_name} by {current_user.get('username')}")
        
        # Audit log
        audit = await get_audit_logger(session)
        await audit.log_group_action(
            AuditAction.UPDATE,
            group_name=group_name,
            user_id=current_user.get('username'),
            details={'action': 'remove_member', 'member': username}
        )
        await session.commit()
        
        return await get_group(group_name, current_user)
        
    except ldap.NO_SUCH_OBJECT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group not found: {group_name}"
        )
    except ldap.NO_SUCH_ATTRIBUTE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {username} is not a member of {group_name}"
        )
    except ldap.LDAPError as e:
        logger.error(f"LDAP error removing member: {e}")
        
        # Audit log failure
        audit = await get_audit_logger(session)
        await audit.log_group_action(
            AuditAction.UPDATE,
            group_name=group_name,
            user_id=current_user.get('username'),
            status="failure",
            details={'action': 'remove_member', 'member': username, 'error': str(e)}
        )
        await session.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove member: {str(e)}"
        )

