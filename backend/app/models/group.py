#!/usr/bin/env python3
"""
Group models and schemas
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator
import re


class GroupBase(BaseModel):
    """Base group model"""
    cn: str = Field(..., min_length=1, max_length=64, description="Group name")
    description: Optional[str] = Field(None, description="Group description")
    
    @validator('cn')
    def validate_cn(cls, v):
        """Validate group name format"""
        if not re.match(r'^[a-z][a-z0-9._-]*$', v):
            raise ValueError('Group name must start with a letter and contain only lowercase letters, numbers, dots, hyphens, and underscores')
        return v


class GroupCreate(GroupBase):
    """Group creation model"""
    gidNumber: Optional[int] = Field(None, description="Unix GID")
    memberUid: List[str] = Field(default=[], description="Member usernames")


class GroupUpdate(BaseModel):
    """Group update model"""
    description: Optional[str] = None
    memberUid: Optional[List[str]] = None


class GroupAddMember(BaseModel):
    """Add member to group"""
    username: str = Field(..., description="Username to add")


class GroupRemoveMember(BaseModel):
    """Remove member from group"""
    username: str = Field(..., description="Username to remove")


class GroupResponse(BaseModel):
    """Group response model"""
    dn: str
    cn: str
    description: Optional[str] = None
    gidNumber: Optional[int] = None
    memberUid: List[str] = []
    createTimestamp: Optional[str] = None
    modifyTimestamp: Optional[str] = None
    
    class Config:
        from_attributes = True


class GroupListResponse(BaseModel):
    """Group list response"""
    groups: List[GroupResponse]
    total: int
    page: int
    page_size: int

