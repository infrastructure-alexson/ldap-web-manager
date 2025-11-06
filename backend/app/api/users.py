#!/usr/bin/env python3
"""
User Management API endpoints
"""

import ldap
import asyncio
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.models.user import (
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    UserPasswordChange, UserPasswordReset
)
from app.auth.jwt import get_current_user, require_admin, require_operator
from app.ldap.connection import get_ldap_connection
from app.config import get_config
from app.auth.jwt import get_password_hash
from app.db.base import get_session
from app.db.models import AuditAction
from app.db.audit import get_audit_logger
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def get_next_uid_number() -> int:
    """Get next available UID number"""
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    # Search for highest UID number
    results = ldap_conn.search(
        config.ldap_people_ou,
        "(objectClass=posixAccount)",
        attributes=['uidNumber']
    )
    
    max_uid = 1000  # Start from 1000
    for _, attrs in results:
        uid_num = int(attrs.get('uidNumber', [b'0'])[0])
        if uid_num > max_uid:
            max_uid = uid_num
    
    return max_uid + 1


@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    List all users with pagination and search
    
    Args:
        page: Page number
        page_size: Items per page
        search: Search term (searches uid, cn, mail)
        current_user: Authenticated user
        
    Returns:
        List of users
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    # Build search filter
    if search:
        search_filter = f"(&(objectClass=posixAccount)(|(uid=*{search}*)(cn=*{search}*)(mail=*{search}*)))"
    else:
        search_filter = "(objectClass=posixAccount)"
    
    try:
        results = ldap_conn.search(
            config.ldap_people_ou,
            search_filter,
            attributes=['uid', 'cn', 'mail', 'givenName', 'sn', 'description',
                       'uidNumber', 'gidNumber', 'homeDirectory', 'loginShell',
                       'memberOf', 'createTimestamp', 'modifyTimestamp']
        )
        
        # Convert to UserResponse objects
        users = []
        for user_dn, attrs in results:
            user_data = {
                'dn': user_dn,
                'uid': attrs.get('uid', [b''])[0].decode('utf-8'),
                'cn': attrs.get('cn', [b''])[0].decode('utf-8'),
                'mail': attrs.get('mail', [b''])[0].decode('utf-8') if attrs.get('mail') else None,
                'givenName': attrs.get('givenName', [b''])[0].decode('utf-8') if attrs.get('givenName') else None,
                'sn': attrs.get('sn', [b''])[0].decode('utf-8') if attrs.get('sn') else None,
                'description': attrs.get('description', [b''])[0].decode('utf-8') if attrs.get('description') else None,
                'uidNumber': int(attrs.get('uidNumber', [b'0'])[0]) if attrs.get('uidNumber') else None,
                'gidNumber': int(attrs.get('gidNumber', [b'0'])[0]) if attrs.get('gidNumber') else None,
                'homeDirectory': attrs.get('homeDirectory', [b''])[0].decode('utf-8') if attrs.get('homeDirectory') else None,
                'loginShell': attrs.get('loginShell', [b''])[0].decode('utf-8') if attrs.get('loginShell') else None,
                'memberOf': [g.decode('utf-8') for g in attrs.get('memberOf', [])],
                'createTimestamp': attrs.get('createTimestamp', [b''])[0].decode('utf-8') if attrs.get('createTimestamp') else None,
                'modifyTimestamp': attrs.get('modifyTimestamp', [b''])[0].decode('utf-8') if attrs.get('modifyTimestamp') else None,
            }
            users.append(UserResponse(**user_data))
        
        # Pagination
        total = len(users)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_users = users[start:end]
        
        return {
            "users": paginated_users,
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
    except ldap.LDAPError as e:
        logger.error(f"LDAP error listing users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}"
        )


@router.get("/{username}", response_model=UserResponse)
async def get_user(
    username: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get user by username
    
    Args:
        username: Username (uid)
        current_user: Authenticated user
        
    Returns:
        User information
        
    Raises:
        HTTPException: If user not found
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    try:
        results = ldap_conn.search(
            config.ldap_people_ou,
            f"(uid={username})",
            attributes=['uid', 'cn', 'mail', 'givenName', 'sn', 'description',
                       'uidNumber', 'gidNumber', 'homeDirectory', 'loginShell',
                       'memberOf', 'createTimestamp', 'modifyTimestamp']
        )
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {username}"
            )
        
        user_dn, attrs = results[0]
        user_data = {
            'dn': user_dn,
            'uid': attrs.get('uid', [b''])[0].decode('utf-8'),
            'cn': attrs.get('cn', [b''])[0].decode('utf-8'),
            'mail': attrs.get('mail', [b''])[0].decode('utf-8') if attrs.get('mail') else None,
            'givenName': attrs.get('givenName', [b''])[0].decode('utf-8') if attrs.get('givenName') else None,
            'sn': attrs.get('sn', [b''])[0].decode('utf-8') if attrs.get('sn') else None,
            'description': attrs.get('description', [b''])[0].decode('utf-8') if attrs.get('description') else None,
            'uidNumber': int(attrs.get('uidNumber', [b'0'])[0]) if attrs.get('uidNumber') else None,
            'gidNumber': int(attrs.get('gidNumber', [b'0'])[0]) if attrs.get('gidNumber') else None,
            'homeDirectory': attrs.get('homeDirectory', [b''])[0].decode('utf-8') if attrs.get('homeDirectory') else None,
            'loginShell': attrs.get('loginShell', [b''])[0].decode('utf-8') if attrs.get('loginShell') else None,
            'memberOf': [g.decode('utf-8') for g in attrs.get('memberOf', [])],
            'createTimestamp': attrs.get('createTimestamp', [b''])[0].decode('utf-8') if attrs.get('createTimestamp') else None,
            'modifyTimestamp': attrs.get('modifyTimestamp', [b''])[0].decode('utf-8') if attrs.get('modifyTimestamp') else None,
        }
        
        return UserResponse(**user_data)
        
    except ldap.LDAPError as e:
        logger.error(f"LDAP error getting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}"
        )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_operator)
):
    """
    Create new user
    
    Args:
        user: User information
        session: Database session for audit logging
        current_user: Authenticated user (operator or admin)
        
    Returns:
        Created user
        
    Raises:
        HTTPException: If creation fails
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    # Generate UID and GID if not provided
    if not user.uidNumber:
        user.uidNumber = get_next_uid_number()
    if not user.gidNumber:
        user.gidNumber = user.uidNumber
    if not user.homeDirectory:
        user.homeDirectory = f"/home/{user.uid}"
    
    # Build DN
    user_dn = f"uid={user.uid},{config.ldap_people_ou}"
    
    # Build LDAP attributes
    attributes = {
        'objectClass': [b'inetOrgPerson', b'posixAccount', b'top'],
        'uid': [user.uid.encode('utf-8')],
        'cn': [user.cn.encode('utf-8')],
        'uidNumber': [str(user.uidNumber).encode('utf-8')],
        'gidNumber': [str(user.gidNumber).encode('utf-8')],
        'homeDirectory': [user.homeDirectory.encode('utf-8')],
        'loginShell': [user.loginShell.encode('utf-8')],
        'userPassword': [user.userPassword.encode('utf-8')],  # Will be hashed by LDAP
    }
    
    # Add optional attributes
    if user.mail:
        attributes['mail'] = [user.mail.encode('utf-8')]
    if user.givenName:
        attributes['givenName'] = [user.givenName.encode('utf-8')]
    if user.sn:
        attributes['sn'] = [user.sn.encode('utf-8')]
    elif user.givenName:
        # Use givenName as sn if sn not provided (sn is required for inetOrgPerson)
        attributes['sn'] = [user.givenName.encode('utf-8')]
    else:
        # Use cn as sn if neither provided
        attributes['sn'] = [user.cn.encode('utf-8')]
    if user.description:
        attributes['description'] = [user.description.encode('utf-8')]
    
    try:
        ldap_conn.add(user_dn, attributes)
        logger.info(f"User created: {user.uid} by {current_user.get('username')}")
        
        # Audit log
        audit = await get_audit_logger(session)
        await audit.log_user_action(
            AuditAction.CREATE,
            username=user.uid,
            user_id=current_user.get('username'),
            details={
                'uidNumber': user.uidNumber,
                'gidNumber': user.gidNumber,
                'cn': user.cn,
                'mail': user.mail,
                'homeDirectory': user.homeDirectory,
                'loginShell': user.loginShell
            }
        )
        await session.commit()
        
        # Retrieve and return created user
        return await get_user(user.uid, current_user)
        
    except ldap.ALREADY_EXISTS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User already exists: {user.uid}"
        )
    except ldap.LDAPError as e:
        logger.error(f"LDAP error creating user: {e}")
        
        # Audit log failure
        audit = await get_audit_logger(session)
        await audit.log_user_action(
            AuditAction.CREATE,
            username=user.uid,
            user_id=current_user.get('username'),
            status="failure",
            details={'error': str(e)}
        )
        await session.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.patch("/{username}", response_model=UserResponse)
async def update_user(
    username: str,
    user_update: UserUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_operator)
):
    """
    Update user information
    
    Args:
        username: Username (uid)
        user_update: Fields to update
        session: Database session for audit logging
        current_user: Authenticated user (operator or admin)
        
    Returns:
        Updated user
        
    Raises:
        HTTPException: If update fails
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    # Build DN
    user_dn = f"uid={username},{config.ldap_people_ou}"
    
    # Build modification list
    modifications = []
    update_dict = user_update.dict(exclude_unset=True)
    
    for attr, value in update_dict.items():
        if value is not None:
            modifications.append((
                ldap.MOD_REPLACE,
                attr,
                [value.encode('utf-8')]
            ))
    
    if not modifications:
        # No changes
        return await get_user(username, current_user)
    
    try:
        ldap_conn.modify(user_dn, modifications)
        logger.info(f"User updated: {username} by {current_user.get('username')}")
        
        # Audit log
        audit = await get_audit_logger(session)
        await audit.log_user_action(
            AuditAction.UPDATE,
            username=username,
            user_id=current_user.get('username'),
            details=update_dict
        )
        await session.commit()
        
        # Retrieve and return updated user
        return await get_user(username, current_user)
        
    except ldap.NO_SUCH_OBJECT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {username}"
        )
    except ldap.LDAPError as e:
        logger.error(f"LDAP error updating user: {e}")
        
        # Audit log failure
        audit = await get_audit_logger(session)
        await audit.log_user_action(
            AuditAction.UPDATE,
            username=username,
            user_id=current_user.get('username'),
            status="failure",
            details={'error': str(e)}
        )
        await session.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete("/{username}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    username: str,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    """
    Delete user
    
    Args:
        username: Username (uid)
        session: Database session for audit logging
        current_user: Authenticated user (admin only)
        
    Raises:
        HTTPException: If deletion fails
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    # Build DN
    user_dn = f"uid={username},{config.ldap_people_ou}"
    
    try:
        ldap_conn.delete(user_dn)
        logger.info(f"User deleted: {username} by {current_user.get('username')}")
        
        # Audit log
        audit = await get_audit_logger(session)
        await audit.log_user_action(
            AuditAction.DELETE,
            username=username,
            user_id=current_user.get('username')
        )
        await session.commit()
        
    except ldap.NO_SUCH_OBJECT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {username}"
        )
    except ldap.LDAPError as e:
        logger.error(f"LDAP error deleting user: {e}")
        
        # Audit log failure
        audit = await get_audit_logger(session)
        await audit.log_user_action(
            AuditAction.DELETE,
            username=username,
            user_id=current_user.get('username'),
            status="failure",
            details={'error': str(e)}
        )
        await session.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


@router.post("/{username}/password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    username: str,
    password_reset: UserPasswordReset,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    """
    Reset user password (admin only)
    
    Args:
        username: Username (uid)
        password_reset: New password
        session: Database session for audit logging
        current_user: Authenticated user (admin only)
        
    Raises:
        HTTPException: If reset fails
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    # Build DN
    user_dn = f"uid={username},{config.ldap_people_ou}"
    
    # Modify password
    modifications = [(
        ldap.MOD_REPLACE,
        'userPassword',
        [password_reset.new_password.encode('utf-8')]
    )]
    
    try:
        ldap_conn.modify(user_dn, modifications)
        logger.info(f"Password reset for user: {username} by {current_user.get('username')}")
        
        # Audit log
        audit = await get_audit_logger(session)
        await audit.log_user_action(
            AuditAction.UPDATE,
            username=username,
            user_id=current_user.get('username'),
            details={'action': 'password_reset'}
        )
        await session.commit()
        
    except ldap.NO_SUCH_OBJECT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {username}"
        )
    except ldap.LDAPError as e:
        logger.error(f"LDAP error resetting password: {e}")
        
        # Audit log failure
        audit = await get_audit_logger(session)
        await audit.log_user_action(
            AuditAction.UPDATE,
            username=username,
            user_id=current_user.get('username'),
            status="failure",
            details={'action': 'password_reset', 'error': str(e)}
        )
        await session.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset password: {str(e)}"
        )

