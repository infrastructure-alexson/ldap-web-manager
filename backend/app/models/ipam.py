#!/usr/bin/env python3
"""
IPAM (IP Address Management) models and schemas
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator
import ipaddress
from datetime import datetime


class IPPoolBase(BaseModel):
    """Base IP pool model"""
    name: str = Field(..., description="Pool name")
    network: str = Field(..., description="Network address (CIDR notation)")
    description: Optional[str] = Field(None, description="Pool description")
    vlan_id: Optional[int] = Field(None, description="VLAN ID")
    gateway: Optional[str] = Field(None, description="Default gateway")
    dns_servers: Optional[List[str]] = Field(None, description="DNS servers")
    
    @validator('network')
    def validate_network(cls, v):
        """Validate network format"""
        try:
            ipaddress.IPv4Network(v, strict=False)
            return v
        except ValueError:
            raise ValueError('Invalid network format (use CIDR notation)')
    
    @validator('gateway')
    def validate_gateway(cls, v):
        """Validate gateway IP"""
        if v:
            try:
                ipaddress.IPv4Address(v)
            except ValueError:
                raise ValueError('Invalid gateway IP address')
        return v


class IPPoolCreate(IPPoolBase):
    """IP pool creation model"""
    pass


class IPPoolUpdate(BaseModel):
    """IP pool update model"""
    description: Optional[str] = None
    vlan_id: Optional[int] = None
    gateway: Optional[str] = None
    dns_servers: Optional[List[str]] = None


class IPPoolResponse(BaseModel):
    """IP pool response model"""
    id: int
    name: str
    network: str
    description: Optional[str] = None
    vlan_id: Optional[int] = None
    gateway: Optional[str] = None
    total_ips: int
    used_ips: int
    available_ips: int
    utilization_percent: float
    createTimestamp: Optional[str] = None
    modifyTimestamp: Optional[str] = None
    
    class Config:
        from_attributes = True


class IPPoolListResponse(BaseModel):
    """IP pool list response"""
    pools: List[IPPoolResponse]
    total: int
    page: int
    page_size: int


class IPAllocationBase(BaseModel):
    """Base IP allocation model"""
    ip_address: str = Field(..., description="IP address")
    hostname: Optional[str] = Field(None, description="Hostname")
    mac_address: Optional[str] = Field(None, description="MAC address")
    owner: Optional[str] = Field(None, description="Owner or assigned user")
    purpose: Optional[str] = Field(None, description="Purpose (server, workstation, printer, etc.)")
    allocation_type: Optional[str] = Field(None, description="Type: static, dhcp, reserved")
    description: Optional[str] = Field(None, description="Description")
    
    @validator('ip_address')
    def validate_ip(cls, v):
        """Validate IP address"""
        try:
            ipaddress.IPv4Address(v)
            return v
        except ValueError:
            raise ValueError('Invalid IP address')
    
    @validator('allocation_type')
    def validate_type(cls, v):
        """Validate allocation type"""
        valid_types = ['static', 'dhcp', 'reserved', 'infrastructure']
        if v.lower() not in valid_types:
            raise ValueError(f'Allocation type must be one of: {", ".join(valid_types)}')
        return v.lower()


class IPAllocationCreate(IPAllocationBase):
    """IP allocation creation model"""
    pool_id: Optional[int] = Field(None, description="Pool ID")


class IPAllocationUpdate(BaseModel):
    """IP allocation update model"""
    hostname: Optional[str] = None
    mac_address: Optional[str] = None
    allocation_type: Optional[str] = None
    description: Optional[str] = None


class IPAllocationResponse(BaseModel):
    """IP allocation response model"""
    id: int
    pool_id: int
    ip_address: str
    hostname: Optional[str] = None
    mac_address: Optional[str] = None
    allocation_type: Optional[str] = None
    description: Optional[str] = None
    allocated_at: Optional[str] = None
    allocated_by: Optional[str] = None
    createTimestamp: Optional[str] = None
    modifyTimestamp: Optional[str] = None
    
    class Config:
        from_attributes = True


class IPAllocationListResponse(BaseModel):
    """IP allocation list response"""
    allocations: List[IPAllocationResponse]
    total: int
    pool: str


class IPPoolStatsResponse(BaseModel):
    """IP pool statistics"""
    pool_id: str
    pool_name: str
    network: str
    total_ips: int
    allocated_ips: int
    available_ips: int
    reserved_ips: int
    infrastructure_ips: int
    utilization_percent: float
    allocations_by_type: dict


class IPConflictResponse(BaseModel):
    """IP conflict detection response"""
    ip_address: str
    conflicts: List[dict]
    conflict_count: int


class IPAMStatsResponse(BaseModel):
    """IPAM statistics response"""
    total_pools: int
    total_networks: int
    total_ip_addresses: int
    allocated_addresses: int
    available_addresses: int
    reserved_addresses: int
    utilization_percent: float
    pools_by_utilization: List[dict]


class IPSearchRequest(BaseModel):
    """IP search request"""
    query: str = Field(..., description="IP, hostname, or MAC to search")
    pool_id: Optional[str] = Field(None, description="Limit to specific pool")


class IPSearchResponse(BaseModel):
    """IP search response"""
    results: List[IPAllocationResponse]
    total: int

