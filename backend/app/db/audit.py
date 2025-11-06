"""
Audit logging utilities
Provides functions to log all operations for compliance and debugging
"""

import logging
from typing import Any, Dict, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from enum import Enum

from .models import AuditLog, AuditAction

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Helper class for logging audit events
    Use this to track all LDAP, DNS, DHCP, and IPAM operations
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def log(
        self,
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        user_id: Optional[str] = None,
        user_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Log an audit event
        
        Args:
            action: Type of action (create, read, update, delete, etc.)
            resource_type: Type of resource (user, group, dns_zone, dhcp_subnet, ip_pool, etc.)
            resource_id: ID of the resource
            resource_name: Name of the resource
            user_id: LDAP username performing the action
            user_ip: IP address of the user
            user_agent: User agent string
            status: Success/failure status
            details: Additional details (before/after snapshots, error messages, etc.)
        
        Returns:
            AuditLog: The created audit log entry
        """
        try:
            # Create audit log entry
            audit_log = AuditLog(
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_name=resource_name,
                user_id=user_id or "system",
                user_ip=user_ip,
                user_agent=user_agent,
                status=status,
                details=details or {},
            )
            
            # Add to session
            self.session.add(audit_log)
            await self.session.flush()
            
            logger.info(
                f"Audit: {action.value} {resource_type}/{resource_name} by {user_id} - {status}"
            )
            
            return audit_log
        
        except Exception as e:
            logger.error(f"Error logging audit event: {e}", exc_info=True)
            raise
    
    async def log_user_action(
        self,
        action: AuditAction,
        username: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
    ) -> AuditLog:
        """
        Log a user-related action (create, update, delete)
        
        Args:
            action: Type of action
            username: Username of the user
            user_id: LDAP username performing the action
            details: Additional details
            status: Success/failure status
        
        Returns:
            AuditLog: The created audit log entry
        """
        return await self.log(
            action=action,
            resource_type="user",
            resource_id=username,
            resource_name=username,
            user_id=user_id,
            status=status,
            details=details,
        )
    
    async def log_group_action(
        self,
        action: AuditAction,
        group_name: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
    ) -> AuditLog:
        """Log a group-related action"""
        return await self.log(
            action=action,
            resource_type="group",
            resource_id=group_name,
            resource_name=group_name,
            user_id=user_id,
            status=status,
            details=details,
        )
    
    async def log_dns_action(
        self,
        action: AuditAction,
        zone_name: str,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
    ) -> AuditLog:
        """Log a DNS-related action"""
        return await self.log(
            action=action,
            resource_type="dns_zone",
            resource_id=resource_id or zone_name,
            resource_name=zone_name,
            user_id=user_id,
            status=status,
            details=details,
        )
    
    async def log_dhcp_action(
        self,
        action: AuditAction,
        subnet: str,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
    ) -> AuditLog:
        """Log a DHCP-related action"""
        return await self.log(
            action=action,
            resource_type="dhcp_subnet",
            resource_id=resource_id or subnet,
            resource_name=subnet,
            user_id=user_id,
            status=status,
            details=details,
        )
    
    async def log_ipam_action(
        self,
        action: AuditAction,
        pool_name: str,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
    ) -> AuditLog:
        """Log an IPAM-related action"""
        return await self.log(
            action=action,
            resource_type="ip_pool",
            resource_id=resource_id or pool_name,
            resource_name=pool_name,
            user_id=user_id,
            status=status,
            details=details,
        )
    
    async def log_allocation_action(
        self,
        action: AuditAction,
        ip_address: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
    ) -> AuditLog:
        """Log an IP allocation action"""
        return await self.log(
            action=action,
            resource_type="ip_allocation",
            resource_id=ip_address,
            resource_name=ip_address,
            user_id=user_id,
            status=status,
            details=details,
        )
    
    async def log_authentication(
        self,
        username: str,
        status: str = "success",
        user_ip: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Log authentication event"""
        action = AuditAction.LOGIN if status == "success" else AuditAction.ERROR
        return await self.log(
            action=action,
            resource_type="authentication",
            resource_id=username,
            resource_name=username,
            user_id=username,
            user_ip=user_ip,
            status=status,
            details=details,
        )


async def get_audit_logger(session: AsyncSession) -> AuditLogger:
    """
    Get an audit logger instance
    
    Usage:
        @app.post("/api/users")
        async def create_user(
            user: UserCreate,
            session: AsyncSession = Depends(get_session),
            current_user: dict = Depends(require_admin),
        ):
            audit = await get_audit_logger(session)
            await audit.log_user_action(
                AuditAction.CREATE,
                user.username,
                user_id=current_user["username"],
                details={"uid": user.uid, "gid": user.gid}
            )
    """
    return AuditLogger(session)


