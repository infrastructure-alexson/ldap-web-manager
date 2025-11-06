#!/usr/bin/env python3
"""
Bulk Operations Models

Defines Pydantic models for bulk user, group, DNS, DHCP, and IPAM operations.
"""

from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List, Dict, Any
from enum import Enum


class BulkOperationType(str, Enum):
    """Types of bulk operations"""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    ADD_TO_GROUP = "ADD_TO_GROUP"
    REMOVE_FROM_GROUP = "REMOVE_FROM_GROUP"


class BulkUserOperation(BaseModel):
    """Bulk user operation"""
    operation: BulkOperationType = Field(..., description="Operation type")
    usernames: List[str] = Field(..., min_items=1, max_items=1000, description="List of usernames")
    common_name: Optional[str] = Field(None, description="Common name for CREATE operations")
    mail: Optional[EmailStr] = Field(None, description="Email for CREATE operations")
    description: Optional[str] = Field(None, description="Description for UPDATE/CREATE")
    
    class Config:
        schema_extra = {
            "example": {
                "operation": "CREATE",
                "usernames": ["user1", "user2", "user3"],
                "common_name": "New Employee",
                "mail": "employee@example.com"
            }
        }


class BulkGroupOperation(BaseModel):
    """Bulk group operation"""
    operation: BulkOperationType = Field(..., description="Operation type")
    group_name: str = Field(..., description="Target group name")
    usernames: List[str] = Field(..., min_items=1, max_items=1000, description="List of usernames")
    
    class Config:
        schema_extra = {
            "example": {
                "operation": "ADD_TO_GROUP",
                "group_name": "developers",
                "usernames": ["user1", "user2", "user3"]
            }
        }


class BulkDNSRecord(BaseModel):
    """Single DNS record for bulk operations"""
    name: str = Field(..., description="Record name")
    type: str = Field(..., description="Record type (A, AAAA, MX, CNAME, TXT, etc.)")
    value: str = Field(..., description="Record value")
    ttl: int = Field(3600, description="Time to live in seconds")


class BulkDNSOperation(BaseModel):
    """Bulk DNS operation"""
    operation: str = Field(..., description="Operation type (create, update, delete)")
    zone_name: str = Field(..., description="Zone name")
    records: List[BulkDNSRecord] = Field(..., min_items=1, max_items=100, description="DNS records")
    
    class Config:
        schema_extra = {
            "example": {
                "operation": "create",
                "zone_name": "example.com",
                "records": [
                    {
                        "name": "www",
                        "type": "A",
                        "value": "192.168.1.100",
                        "ttl": 3600
                    },
                    {
                        "name": "mail",
                        "type": "A",
                        "value": "192.168.1.101",
                        "ttl": 3600
                    }
                ]
            }
        }


class BulkIPAllocation(BaseModel):
    """Single IP allocation for bulk operations"""
    ip_address: str = Field(..., description="IP address to allocate")
    hostname: Optional[str] = Field(None, description="Hostname")
    mac_address: Optional[str] = Field(None, description="MAC address")
    owner: str = Field(..., description="Owner/user name")
    purpose: Optional[str] = Field(None, description="Purpose")
    description: Optional[str] = Field(None, description="Description")


class BulkIPAMOperation(BaseModel):
    """Bulk IPAM operation"""
    operation: str = Field(..., description="Operation type (allocate, release, update)")
    pool_id: int = Field(..., description="IP pool ID")
    allocations: List[BulkIPAllocation] = Field(..., min_items=1, max_items=500, description="IP allocations")
    
    class Config:
        schema_extra = {
            "example": {
                "operation": "allocate",
                "pool_id": 1,
                "allocations": [
                    {
                        "ip_address": "10.0.0.50",
                        "hostname": "server1",
                        "owner": "admin",
                        "purpose": "server"
                    },
                    {
                        "ip_address": "10.0.0.51",
                        "hostname": "server2",
                        "owner": "admin",
                        "purpose": "server"
                    }
                ]
            }
        }


class BulkOperationResult(BaseModel):
    """Result of a single bulk operation item"""
    index: int = Field(..., description="Index in the original request")
    identifier: str = Field(..., description="Item identifier (username, IP, etc.)")
    status: str = Field(..., description="success, failure, skipped")
    message: str = Field(..., description="Result message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")


class BulkOperationResponse(BaseModel):
    """Response from bulk operation"""
    total: int = Field(..., description="Total items in operation")
    successful: int = Field(..., description="Successfully processed items")
    failed: int = Field(..., description="Failed items")
    skipped: int = Field(..., description="Skipped items")
    operation_id: str = Field(..., description="Operation identifier")
    results: List[BulkOperationResult] = Field(..., description="Detailed results")
    summary: str = Field(..., description="Human-readable summary")
    
    class Config:
        schema_extra = {
            "example": {
                "total": 5,
                "successful": 4,
                "failed": 1,
                "skipped": 0,
                "operation_id": "bulk_20251106_123456",
                "results": [
                    {
                        "index": 0,
                        "identifier": "user1",
                        "status": "success",
                        "message": "User created successfully"
                    },
                    {
                        "index": 1,
                        "identifier": "user2",
                        "status": "success",
                        "message": "User created successfully"
                    },
                    {
                        "index": 3,
                        "identifier": "user4",
                        "status": "failure",
                        "message": "User already exists"
                    }
                ],
                "summary": "4 of 5 users created successfully"
            }
        }


class BulkCSVUpload(BaseModel):
    """CSV upload for bulk operations"""
    operation: str = Field(..., description="Operation type")
    resource_type: str = Field(..., description="Resource type (user, group, dns, dhcp, ipam)")
    
    class Config:
        schema_extra = {
            "example": {
                "operation": "create",
                "resource_type": "user"
            }
        }


class BulkExportRequest(BaseModel):
    """Request to export bulk operation results"""
    format: str = Field(..., description="Export format: csv, json")
    include_failed: bool = Field(True, description="Include failed items")
    include_skipped: bool = Field(False, description="Include skipped items")
    
    class Config:
        schema_extra = {
            "example": {
                "format": "csv",
                "include_failed": True,
                "include_skipped": False
            }
        }

