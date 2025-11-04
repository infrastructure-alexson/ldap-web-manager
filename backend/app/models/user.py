#!/usr/bin/env python3
"""
User models and schemas
"""

from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator
import re


class UserBase(BaseModel):
    """Base user model"""
    uid: str = Field(..., min_length=3, max_length=32, description="Username")
    cn: str = Field(..., min_length=1, max_length=128, description="Common name (full name)")
    mail: Optional[EmailStr] = Field(None, description="Email address")
    givenName: Optional[str] = Field(None, description="First name")
    sn: Optional[str] = Field(None, description="Last name (surname)")
    description: Optional[str] = Field(None, description="Description")
    
    @validator('uid')
    def validate_uid(cls, v):
        """Validate username format"""
        if not re.match(r'^[a-z][a-z0-9._-]*$', v):
            raise ValueError('Username must start with a letter and contain only lowercase letters, numbers, dots, hyphens, and underscores')
        return v


class UserCreate(UserBase):
    """User creation model"""
    userPassword: str = Field(..., min_length=12, description="Password")
    uidNumber: Optional[int] = Field(None, description="Unix UID")
    gidNumber: Optional[int] = Field(None, description="Unix GID")
    homeDirectory: Optional[str] = Field(None, description="Home directory path")
    loginShell: Optional[str] = Field('/bin/bash', description="Login shell")
    
    @validator('userPassword')
    def validate_password(cls, v):
        """Validate password complexity"""
        if len(v) < 12:
            raise ValueError('Password must be at least 12 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserUpdate(BaseModel):
    """User update model"""
    cn: Optional[str] = None
    mail: Optional[EmailStr] = None
    givenName: Optional[str] = None
    sn: Optional[str] = None
    description: Optional[str] = None
    loginShell: Optional[str] = None


class UserPasswordChange(BaseModel):
    """Password change model"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=12, description="New password")
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password complexity"""
        if len(v) < 12:
            raise ValueError('Password must be at least 12 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserPasswordReset(BaseModel):
    """Admin password reset model"""
    new_password: str = Field(..., min_length=12, description="New password")


class UserResponse(BaseModel):
    """User response model"""
    dn: str
    uid: str
    cn: str
    mail: Optional[str] = None
    givenName: Optional[str] = None
    sn: Optional[str] = None
    description: Optional[str] = None
    uidNumber: Optional[int] = None
    gidNumber: Optional[int] = None
    homeDirectory: Optional[str] = None
    loginShell: Optional[str] = None
    memberOf: List[str] = []
    createTimestamp: Optional[str] = None
    modifyTimestamp: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """User list response"""
    users: List[UserResponse]
    total: int
    page: int
    page_size: int

