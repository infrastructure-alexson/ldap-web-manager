#!/usr/bin/env python3
"""
Service Account Management API endpoints

Service accounts are special accounts used for system-to-system integration.
They typically have restricted permissions and are used for services like DHCP, DNS, etc.
"""

import ldap
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.models.service_account import (
    ServiceAccountCreate, ServiceAccountUpdate, ServiceAccountResponse,
    ServiceAccountListResponse, ServiceAccountPasswordReset,
    ServiceAccountPermissions, ServiceAccountAssignPermissions
)
from app.auth.jwt import get_current_user, require_admin
from app.ldap.connection import get_ldap_connection
from app.config import get_config
from app.auth.jwt import get_password_hash
from app.db.base import get_session
from app.db.models import AuditAction
from app.db.audit import get_audit_logger
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def get_next_service_account_uid() -> int:
    """Get next available UID number for service accounts (starting at 5000)"""
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    # Search for highest UID number in service accounts OU
    service_accounts_ou = f"ou=ServiceAccounts,{config.ldap_base_dn}"
    try:
        results = ldap_conn.search(
            service_accounts_ou,
            "(objectClass=posixAccount)",
            attributes=['uidNumber']
        )
        
        max_uid = 4999  # Start from 5000
        for _, attrs in results:
            uid_num = int(attrs.get('uidNumber', [b'0'])[0])
            if uid_num > max_uid:
                max_uid = uid_num
        
        return max_uid + 1
    except ldap.NO_SUCH_OBJECT:
        # Service Accounts OU doesn't exist yet, return default
        return 5000


@router.get("", response_model=ServiceAccountListResponse)
async def list_service_accounts(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: dict = Depends(get_current_user)
):
    """
    List service accounts with pagination and filtering
    
    Args:
        page: Page number (1-indexed)
        page_size: Items per page
        search: Search by uid, cn, or description
        status_filter: Filter by status (active, disabled)
        current_user: Authenticated user
        
    Returns:
        List of service accounts with pagination info
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    service_accounts_ou = f"ou=ServiceAccounts,{config.ldap_base_dn}"
    
    try:
        # Build search filter
        filters = ["(objectClass=posixAccount)"]
        
        if search:
            search_filter = f"(|(uid=*{search}*)(cn=*{search}*)(description=*{search}*))"
            filters.append(search_filter)
        
        if status_filter and status_filter.lower() in ['active', 'disabled']:
            # This would be a custom LDAP attribute or derived from pwdAccountLockedTime
            pass
        
        combined_filter = f"(&{''.join(filters)})" if len(filters) > 1 else filters[0]
        
        results = ldap_conn.search(
            service_accounts_ou,
            combined_filter,
            attributes=['uid', 'cn', 'mail', 'description', 'uidNumber', 'gidNumber',
                       'homeDirectory', 'loginShell', 'memberOf', 'createTimestamp', 
                       'modifyTimestamp']
        )
        
        # Convert results to list and sort
        accounts = []
        for dn, attrs in results:
            account_data = {
                'dn': dn,
                'uid': attrs.get('uid', [b''])[0].decode('utf-8'),
                'cn': attrs.get('cn', [b''])[0].decode('utf-8'),
                'mail': attrs.get('mail', [b''])[0].decode('utf-8') if attrs.get('mail') else None,
                'description': attrs.get('description', [b''])[0].decode('utf-8') if attrs.get('description') else None,
                'uidNumber': int(attrs.get('uidNumber', [b'0'])[0]),
                'gidNumber': int(attrs.get('gidNumber', [b'0'])[0]),
                'homeDirectory': attrs.get('homeDirectory', [b''])[0].decode('utf-8'),
                'loginShell': attrs.get('loginShell', [b''])[0].decode('utf-8'),
                'memberOf': [g.decode('utf-8') for g in attrs.get('memberOf', [])],
                'status': 'active',  # Could be derived from LDAP attributes
                'created_at': None,
                'modified_at': None,
                'last_login': None
            }
            accounts.append(ServiceAccountResponse(**account_data))
        
        # Apply pagination
        total = len(accounts)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_accounts = accounts[start_idx:end_idx]
        
        return ServiceAccountListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=paginated_accounts
        )
        
    except ldap.LDAPError as e:
        logger.error(f"LDAP error listing service accounts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list service accounts: {str(e)}"
        )


@router.get("/{uid}", response_model=ServiceAccountResponse)
async def get_service_account(
    uid: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get service account by UID
    
    Args:
        uid: Service account UID
        current_user: Authenticated user
        
    Returns:
        Service account information
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    service_accounts_ou = f"ou=ServiceAccounts,{config.ldap_base_dn}"
    
    try:
        results = ldap_conn.search(
            service_accounts_ou,
            f"(uid={uid})",
            attributes=['uid', 'cn', 'mail', 'description', 'uidNumber', 'gidNumber',
                       'homeDirectory', 'loginShell', 'memberOf', 'createTimestamp',
                       'modifyTimestamp']
        )
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service account not found: {uid}"
            )
        
        dn, attrs = results[0]
        account_data = {
            'dn': dn,
            'uid': attrs.get('uid', [b''])[0].decode('utf-8'),
            'cn': attrs.get('cn', [b''])[0].decode('utf-8'),
            'mail': attrs.get('mail', [b''])[0].decode('utf-8') if attrs.get('mail') else None,
            'description': attrs.get('description', [b''])[0].decode('utf-8') if attrs.get('description') else None,
            'uidNumber': int(attrs.get('uidNumber', [b'0'])[0]),
            'gidNumber': int(attrs.get('gidNumber', [b'0'])[0]),
            'homeDirectory': attrs.get('homeDirectory', [b''])[0].decode('utf-8'),
            'loginShell': attrs.get('loginShell', [b''])[0].decode('utf-8'),
            'memberOf': [g.decode('utf-8') for g in attrs.get('memberOf', [])],
            'status': 'active',
            'created_at': None,
            'modified_at': None,
            'last_login': None
        }
        return ServiceAccountResponse(**account_data)
        
    except ldap.LDAPError as e:
        logger.error(f"LDAP error getting service account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service account: {str(e)}"
        )


@router.post("", response_model=ServiceAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_service_account(
    account: ServiceAccountCreate,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    """
    Create new service account
    
    Args:
        account: Service account information
        session: Database session for audit logging
        current_user: Authenticated admin user
        
    Returns:
        Created service account
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    service_accounts_ou = f"ou=ServiceAccounts,{config.ldap_base_dn}"
    
    # Generate UID and GID if not provided
    if not account.uidNumber:
        account.uidNumber = get_next_service_account_uid()
    if not account.gidNumber:
        account.gidNumber = account.uidNumber
    if not account.homeDirectory:
        account.homeDirectory = f"/srv/{account.uid}"
    
    # Build DN
    service_account_dn = f"uid={account.uid},{service_accounts_ou}"
    
    # Build LDAP attributes
    attributes = {
        'objectClass': [b'inetOrgPerson', b'posixAccount', b'top'],
        'uid': [account.uid.encode('utf-8')],
        'cn': [account.cn.encode('utf-8')],
        'uidNumber': [str(account.uidNumber).encode('utf-8')],
        'gidNumber': [str(account.gidNumber).encode('utf-8')],
        'homeDirectory': [account.homeDirectory.encode('utf-8')],
        'loginShell': [(account.loginShell or '/bin/false').encode('utf-8')],
        'userPassword': [get_password_hash(account.uid).encode('utf-8')],  # Default password based on UID
    }
    
    # Add optional attributes
    if account.mail:
        attributes['mail'] = [account.mail.encode('utf-8')]
    if account.description:
        attributes['description'] = [account.description.encode('utf-8')]
    else:
        attributes['description'] = [b'Service account']
    
    try:
        ldap_conn.add(service_account_dn, attributes)
        logger.info(f"Service account created: {account.uid} by {current_user.get('username')}")
        
        # Audit log
        audit = await get_audit_logger(session)
        await audit.log_action(
            AuditAction.CREATE,
            'ServiceAccount',
            account.uid,
            user_id=current_user.get('username'),
            details={
                'uid': account.uid,
                'cn': account.cn,
                'mail': account.mail,
                'uidNumber': account.uidNumber,
                'gidNumber': account.gidNumber
            }
        )
        await session.commit()
        
        # Retrieve and return created account
        return await get_service_account(account.uid, current_user)
        
    except ldap.ALREADY_EXISTS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Service account already exists: {account.uid}"
        )
    except ldap.LDAPError as e:
        logger.error(f"LDAP error creating service account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create service account: {str(e)}"
        )


@router.patch("/{uid}", response_model=ServiceAccountResponse)
async def update_service_account(
    uid: str,
    account_update: ServiceAccountUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    """
    Update service account
    
    Args:
        uid: Service account UID
        account_update: Updates to apply
        session: Database session for audit logging
        current_user: Authenticated admin user
        
    Returns:
        Updated service account
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    service_accounts_ou = f"ou=ServiceAccounts,{config.ldap_base_dn}"
    service_account_dn = f"uid={uid},{service_accounts_ou}"
    
    try:
        # Build modifications
        mod_attrs = []
        
        if account_update.cn:
            mod_attrs.append((ldap.MOD_REPLACE, 'cn', [account_update.cn.encode('utf-8')]))
        
        if account_update.mail:
            mod_attrs.append((ldap.MOD_REPLACE, 'mail', [account_update.mail.encode('utf-8')]))
        elif account_update.mail is None:
            # Explicitly None means delete
            mod_attrs.append((ldap.MOD_DELETE, 'mail', None))
        
        if account_update.description:
            mod_attrs.append((ldap.MOD_REPLACE, 'description', [account_update.description.encode('utf-8')]))
        
        if mod_attrs:
            ldap_conn.modify_s(service_account_dn, mod_attrs)
            logger.info(f"Service account updated: {uid} by {current_user.get('username')}")
            
            # Audit log
            audit = await get_audit_logger(session)
            await audit.log_action(
                AuditAction.UPDATE,
                'ServiceAccount',
                uid,
                user_id=current_user.get('username'),
                details=account_update.dict(exclude_unset=True)
            )
            await session.commit()
        
        # Retrieve and return updated account
        return await get_service_account(uid, current_user)
        
    except ldap.NO_SUCH_OBJECT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service account not found: {uid}"
        )
    except ldap.LDAPError as e:
        logger.error(f"LDAP error updating service account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update service account: {str(e)}"
        )


@router.delete("/{uid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_account(
    uid: str,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    """
    Delete service account
    
    Args:
        uid: Service account UID
        session: Database session for audit logging
        current_user: Authenticated admin user
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    service_accounts_ou = f"ou=ServiceAccounts,{config.ldap_base_dn}"
    service_account_dn = f"uid={uid},{service_accounts_ou}"
    
    try:
        ldap_conn.delete_s(service_account_dn)
        logger.info(f"Service account deleted: {uid} by {current_user.get('username')}")
        
        # Audit log
        audit = await get_audit_logger(session)
        await audit.log_action(
            AuditAction.DELETE,
            'ServiceAccount',
            uid,
            user_id=current_user.get('username'),
            details={'uid': uid}
        )
        await session.commit()
        
    except ldap.NO_SUCH_OBJECT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service account not found: {uid}"
        )
    except ldap.LDAPError as e:
        logger.error(f"LDAP error deleting service account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete service account: {str(e)}"
        )


@router.post("/{uid}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_service_account_password(
    uid: str,
    password_reset: ServiceAccountPasswordReset,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin)
):
    """
    Reset service account password
    
    Args:
        uid: Service account UID
        password_reset: New password
        session: Database session for audit logging
        current_user: Authenticated admin user
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    service_accounts_ou = f"ou=ServiceAccounts,{config.ldap_base_dn}"
    service_account_dn = f"uid={uid},{service_accounts_ou}"
    
    try:
        # Update password
        hashed_password = get_password_hash(password_reset.password)
        ldap_conn.modify_s(
            service_account_dn,
            [(ldap.MOD_REPLACE, 'userPassword', [hashed_password.encode('utf-8')])]
        )
        logger.info(f"Service account password reset: {uid} by {current_user.get('username')}")
        
        # Audit log
        audit = await get_audit_logger(session)
        await audit.log_action(
            AuditAction.UPDATE,
            'ServiceAccount',
            uid,
            user_id=current_user.get('username'),
            details={'action': 'password_reset'}
        )
        await session.commit()
        
    except ldap.NO_SUCH_OBJECT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service account not found: {uid}"
        )
    except ldap.LDAPError as e:
        logger.error(f"LDAP error resetting password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset password: {str(e)}"
        )

