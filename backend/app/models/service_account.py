#!/usr/bin/env python3
"""
Service Account Models

Defines Pydantic models for service account management.
Service accounts are special accounts used for system-to-system integration.
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime


class ServiceAccountBase(BaseModel):
    """Base model for service account"""
    uid: str = Field(..., min_length=3, max_length=32, description="Service account username (lowercase, no spaces)")
    cn: str = Field(..., min_length=3, max_length=255, description="Common name (display name)")
    mail: Optional[EmailStr] = Field(None, description="Email address")
    description: Optional[str] = Field(None, max_length=500, description="Service account purpose and notes")
    
    @validator('uid')
    def validate_uid(cls, v):
        """Validate uid is lowercase and contains no spaces"""
        if not v.islower():
            raise ValueError('uid must be lowercase')
        if ' ' in v:
            raise ValueError('uid cannot contain spaces')
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('uid can only contain alphanumeric characters, hyphens, and underscores')
        if v.startswith('sa-') or v.startswith('svc-'):
            return v
        # Recommend prefix
        return f"svc-{v}" if not v.startswith(('sa-', 'svc-')) else v
    
    class Config:
        schema_extra = {
            "example": {
                "uid": "svc-dhcp-server",
                "cn": "DHCP Service Account",
                "mail": "dhcp@example.com",
                "description": "Service account for Kea DHCP server"
            }
        }


class ServiceAccountCreate(ServiceAccountBase):
    """Create service account request"""
    uidNumber: Optional[int] = Field(None, description="UID number (auto-generated if not provided)")
    gidNumber: Optional[int] = Field(None, description="GID number (defaults to uidNumber)")
    homeDirectory: Optional[str] = Field(None, description="Home directory path")
    loginShell: Optional[str] = Field(None, default="/bin/false", description="Login shell (usually /bin/false for service accounts)")
    
    class Config:
        schema_extra = {
            "example": {
                "uid": "svc-dhcp",
                "cn": "DHCP Service Account",
                "mail": "dhcp@example.com",
                "description": "Service account for Kea DHCP server",
                "loginShell": "/bin/false"
            }
        }


class ServiceAccountUpdate(BaseModel):
    """Update service account request"""
    cn: Optional[str] = Field(None, min_length=3, max_length=255)
    mail: Optional[EmailStr] = None
    description: Optional[str] = Field(None, max_length=500)
    
    class Config:
        schema_extra = {
            "example": {
                "cn": "DHCP Service (Updated)",
                "description": "Updated description for DHCP service account"
            }
        }


class ServiceAccountPasswordReset(BaseModel):
    """Reset service account password request"""
    password: str = Field(..., min_length=12, max_length=128, description="New password (minimum 12 characters)")
    
    class Config:
        schema_extra = {
            "example": {
                "password": "NewSecurePassword123!@#"
            }
        }


class ServiceAccountPermissions(BaseModel):
    """Service account permissions"""
    can_read_users: bool = Field(False, description="Can read user information")
    can_manage_users: bool = Field(False, description="Can create/update/delete users")
    can_read_groups: bool = Field(False, description="Can read group information")
    can_manage_groups: bool = Field(False, description="Can create/update/delete groups")
    can_read_dns: bool = Field(False, description="Can read DNS information")
    can_manage_dns: bool = Field(False, description="Can create/update/delete DNS records")
    can_read_dhcp: bool = Field(False, description="Can read DHCP information")
    can_manage_dhcp: bool = Field(False, description="Can create/update/delete DHCP subnets")
    can_read_ipam: bool = Field(False, description="Can read IPAM information")
    can_manage_ipam: bool = Field(False, description="Can create/update/delete IP allocations")
    
    class Config:
        schema_extra = {
            "example": {
                "can_read_dhcp": True,
                "can_manage_dhcp": True,
                "can_read_dns": True
            }
        }


class ServiceAccountAssignPermissions(BaseModel):
    """Assign permissions to service account"""
    permissions: ServiceAccountPermissions
    
    class Config:
        schema_extra = {
            "example": {
                "permissions": {
                    "can_read_dhcp": True,
                    "can_manage_dhcp": True
                }
            }
        }


class ServiceAccountResponse(ServiceAccountBase):
    """Service account response"""
    dn: str = Field(..., description="LDAP distinguished name")
    uidNumber: int = Field(..., description="UID number")
    gidNumber: int = Field(..., description="GID number")
    homeDirectory: str = Field(..., description="Home directory")
    loginShell: str = Field(..., description="Login shell")
    memberOf: List[str] = Field(default=[], description="Groups the account is member of")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    modified_at: Optional[datetime] = Field(None, description="Last modification timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    status: str = Field(default="active", description="Account status (active, disabled, etc)")
    
    class Config:
        schema_extra = {
            "example": {
                "uid": "svc-dhcp",
                "cn": "DHCP Service Account",
                "mail": "dhcp@example.com",
                "description": "Service account for Kea DHCP server",
                "dn": "uid=svc-dhcp,ou=ServiceAccounts,dc=eh168,dc=alexson,dc=org",
                "uidNumber": 5001,
                "gidNumber": 5001,
                "homeDirectory": "/home/svc-dhcp",
                "loginShell": "/bin/false",
                "status": "active",
                "created_at": "2025-11-06T12:00:00Z"
            }
        }


class ServiceAccountListResponse(BaseModel):
    """Service account list response with pagination"""
    total: int = Field(..., description="Total service accounts")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Items per page")
    items: List[ServiceAccountResponse] = Field(..., description="Service accounts")
    
    class Config:
        schema_extra = {
            "example": {
                "total": 5,
                "page": 1,
                "page_size": 50,
                "items": [
                    {
                        "uid": "svc-dhcp",
                        "cn": "DHCP Service Account",
                        "mail": "dhcp@example.com",
                        "dn": "uid=svc-dhcp,ou=ServiceAccounts,dc=eh168,dc=alexson,dc=org",
                        "uidNumber": 5001,
                        "gidNumber": 5001,
                        "status": "active"
                    }
                ]
            }
        }


class ServiceAccountToken(BaseModel):
    """Service account API token response"""
    token_id: str = Field(..., description="Token identifier")
    token_secret: str = Field(..., description="Token secret (shown once on creation)")
    description: Optional[str] = Field(None, description="Token description")
    created_at: datetime = Field(..., description="Token creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Token expiration timestamp")
    scopes: List[str] = Field(default=[], description="Token scopes")
    
    class Config:
        schema_extra = {
            "example": {
                "token_id": "sat_1234567890",
                "token_secret": "svc_dhcp_abcdefghijklmnopqrstuvwxyz123456",
                "description": "DHCP server API token",
                "created_at": "2025-11-06T12:00:00Z",
                "scopes": ["read_dhcp", "write_dhcp"]
            }
        }


class ServiceAccountInfo(BaseModel):
    """Service account information for audit/logging"""
    uid: str
    cn: str
    status: str
    created_at: Optional[datetime]
    created_by: Optional[str]
    last_modified_at: Optional[datetime]
    last_modified_by: Optional[str]
    description: Optional[str]

