#!/usr/bin/env python3
"""
Audit Log Models

Defines Pydantic models for viewing and querying audit logs.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


class AuditActionEnum(str, Enum):
    """Audit action types"""
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    AUTHENTICATION = "AUTHENTICATION"


class AuditLogFilter(BaseModel):
    """Filter criteria for audit logs"""
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    action: Optional[AuditActionEnum] = Field(None, description="Filter by action type")
    resource_type: Optional[str] = Field(None, description="Filter by resource type (User, Group, DNS, DHCP, etc.)")
    resource_id: Optional[str] = Field(None, description="Filter by resource ID")
    status: Optional[str] = Field(None, description="Filter by status (success, failure, error)")
    start_date: Optional[datetime] = Field(None, description="Start date (inclusive)")
    end_date: Optional[datetime] = Field(None, description="End date (inclusive)")
    search_text: Optional[str] = Field(None, description="Search in details or error messages")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "admin",
                "action": "CREATE",
                "resource_type": "User",
                "start_date": "2025-11-01T00:00:00Z",
                "end_date": "2025-11-06T23:59:59Z"
            }
        }


class AuditLogResponse(BaseModel):
    """Single audit log entry response"""
    id: str = Field(..., description="Audit log ID")
    timestamp: datetime = Field(..., description="When the action occurred")
    user_id: str = Field(..., description="Who performed the action")
    action: AuditActionEnum = Field(..., description="Type of action")
    resource_type: str = Field(..., description="Type of resource affected")
    resource_id: Optional[str] = Field(None, description="ID of resource affected")
    status: str = Field(..., description="success, failure, error")
    details: Optional[dict] = Field(None, description="Action-specific details")
    before_state: Optional[dict] = Field(None, description="State before the change")
    after_state: Optional[dict] = Field(None, description="State after the change")
    error_message: Optional[str] = Field(None, description="Error message if action failed")
    ip_address: Optional[str] = Field(None, description="IP address of request")
    user_agent: Optional[str] = Field(None, description="User agent of request")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "audit_12345",
                "timestamp": "2025-11-06T12:30:45Z",
                "user_id": "admin",
                "action": "CREATE",
                "resource_type": "User",
                "resource_id": "john.doe",
                "status": "success",
                "details": {
                    "username": "john.doe",
                    "email": "john@example.com",
                    "groups": ["users", "staff"]
                },
                "after_state": {
                    "uid": "john.doe",
                    "cn": "John Doe",
                    "mail": "john@example.com"
                }
            }
        }


class AuditLogListResponse(BaseModel):
    """List of audit log entries with pagination"""
    total: int = Field(..., description="Total audit log entries")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Items per page")
    items: List[AuditLogResponse] = Field(..., description="Audit log entries")
    
    class Config:
        schema_extra = {
            "example": {
                "total": 1250,
                "page": 1,
                "page_size": 50,
                "items": [
                    {
                        "id": "audit_12345",
                        "timestamp": "2025-11-06T12:30:45Z",
                        "user_id": "admin",
                        "action": "CREATE",
                        "resource_type": "User",
                        "resource_id": "john.doe",
                        "status": "success"
                    }
                ]
            }
        }


class AuditStatistics(BaseModel):
    """Audit log statistics"""
    total_logs: int = Field(..., description="Total number of log entries")
    date_range: str = Field(..., description="Date range of logs")
    actions_breakdown: dict = Field(..., description="Count by action type")
    resource_types_breakdown: dict = Field(..., description="Count by resource type")
    users_count: int = Field(..., description="Number of unique users")
    success_rate: float = Field(..., description="Percentage of successful operations")
    failure_count: int = Field(..., description="Number of failed operations")
    error_count: int = Field(..., description="Number of error operations")
    
    class Config:
        schema_extra = {
            "example": {
                "total_logs": 1250,
                "date_range": "2025-11-01 to 2025-11-06",
                "actions_breakdown": {
                    "CREATE": 250,
                    "UPDATE": 400,
                    "DELETE": 100,
                    "READ": 300,
                    "AUTHENTICATION": 200
                },
                "resource_types_breakdown": {
                    "User": 300,
                    "Group": 150,
                    "DNS": 200,
                    "DHCP": 200,
                    "IPAM": 150,
                    "ServiceAccount": 50,
                    "Auth": 200
                },
                "users_count": 5,
                "success_rate": 96.8,
                "failure_count": 30,
                "error_count": 10
            }
        }


class AuditExportRequest(BaseModel):
    """Request to export audit logs"""
    format: str = Field(..., description="Export format: csv, json, excel")
    filters: Optional[AuditLogFilter] = Field(None, description="Filters to apply")
    include_details: bool = Field(True, description="Include detailed information")
    
    class Config:
        schema_extra = {
            "example": {
                "format": "csv",
                "filters": {
                    "action": "CREATE",
                    "start_date": "2025-11-01T00:00:00Z"
                },
                "include_details": True
            }
        }


class AuditLogEntry(BaseModel):
    """Internal audit log entry for processing"""
    id: str
    timestamp: datetime
    user_id: str
    action: str
    resource_type: str
    resource_id: Optional[str]
    status: str
    details: Optional[dict]
    before_state: Optional[dict]
    after_state: Optional[dict]
    error_message: Optional[str]

