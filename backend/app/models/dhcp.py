#!/usr/bin/env python3
"""
DHCP models and schemas for Kea DHCP
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator
import ipaddress


class DHCPSubnetBase(BaseModel):
    """Base DHCP subnet model"""
    cn: str = Field(..., description="Subnet identifier (e.g., 192.168.1.0)")
    dhcpNetMask: int = Field(..., ge=0, le=32, description="Subnet mask (CIDR notation)")
    dhcpOption: Optional[List[str]] = Field(None, description="DHCP options")
    description: Optional[str] = Field(None, description="Subnet description")
    
    @validator('cn')
    def validate_subnet(cls, v):
        """Validate subnet format"""
        try:
            ipaddress.IPv4Network(v, strict=False)
            return v
        except ValueError:
            raise ValueError('Invalid subnet format')


class DHCPSubnetCreate(DHCPSubnetBase):
    """DHCP subnet creation model"""
    dhcpRange: Optional[List[str]] = Field(None, description="IP ranges (start end)")


class DHCPSubnetUpdate(BaseModel):
    """DHCP subnet update model"""
    dhcpOption: Optional[List[str]] = None
    dhcpRange: Optional[List[str]] = None
    description: Optional[str] = None


class DHCPSubnetResponse(BaseModel):
    """DHCP subnet response model"""
    dn: str
    cn: str
    dhcpNetMask: int
    dhcpOption: Optional[List[str]] = None
    dhcpRange: Optional[List[str]] = None
    description: Optional[str] = None
    createTimestamp: Optional[str] = None
    modifyTimestamp: Optional[str] = None
    
    class Config:
        from_attributes = True


class DHCPSubnetListResponse(BaseModel):
    """DHCP subnet list response"""
    subnets: List[DHCPSubnetResponse]
    total: int
    page: int
    page_size: int


class DHCPPoolBase(BaseModel):
    """Base DHCP pool model"""
    cn: str = Field(..., description="Pool identifier")
    dhcpRange: str = Field(..., description="IP range (start end)")
    dhcpPermitList: Optional[List[str]] = Field(None, description="Permitted clients")
    
    @validator('dhcpRange')
    def validate_range(cls, v):
        """Validate IP range format"""
        parts = v.split()
        if len(parts) != 2:
            raise ValueError('Range must be "start_ip end_ip"')
        try:
            ipaddress.IPv4Address(parts[0])
            ipaddress.IPv4Address(parts[1])
        except ValueError:
            raise ValueError('Invalid IP addresses in range')
        return v


class DHCPPoolCreate(DHCPPoolBase):
    """DHCP pool creation model"""
    pass


class DHCPPoolResponse(BaseModel):
    """DHCP pool response model"""
    dn: str
    cn: str
    dhcpRange: str
    dhcpPermitList: Optional[List[str]] = None
    createTimestamp: Optional[str] = None
    
    class Config:
        from_attributes = True


class DHCPHostBase(BaseModel):
    """Base DHCP host (static reservation) model"""
    cn: str = Field(..., description="Host identifier")
    dhcpHWAddress: str = Field(..., description="MAC address (ethernet XX:XX:XX:XX:XX:XX)")
    dhcpStatements: List[str] = Field(..., description="DHCP statements including fixed-address")
    dhcpOption: Optional[List[str]] = Field(None, description="Host-specific DHCP options")
    
    @validator('dhcpHWAddress')
    def validate_mac(cls, v):
        """Validate MAC address format"""
        if not v.startswith('ethernet '):
            raise ValueError('MAC must start with "ethernet "')
        mac = v.replace('ethernet ', '')
        parts = mac.split(':')
        if len(parts) != 6:
            raise ValueError('MAC must have 6 octets')
        for part in parts:
            try:
                int(part, 16)
            except ValueError:
                raise ValueError('Invalid MAC address format')
        return v
    
    @validator('dhcpStatements')
    def validate_statements(cls, v):
        """Validate DHCP statements"""
        has_fixed_address = any('fixed-address' in stmt for stmt in v)
        if not has_fixed_address:
            raise ValueError('Must include fixed-address statement')
        return v


class DHCPHostCreate(DHCPHostBase):
    """DHCP host creation model"""
    description: Optional[str] = Field(None, description="Host description")


class DHCPHostUpdate(BaseModel):
    """DHCP host update model"""
    dhcpHWAddress: Optional[str] = None
    dhcpStatements: Optional[List[str]] = None
    dhcpOption: Optional[List[str]] = None
    description: Optional[str] = None


class DHCPHostResponse(BaseModel):
    """DHCP host response model"""
    dn: str
    cn: str
    dhcpHWAddress: str
    dhcpStatements: List[str]
    dhcpOption: Optional[List[str]] = None
    description: Optional[str] = None
    createTimestamp: Optional[str] = None
    modifyTimestamp: Optional[str] = None
    
    # Parsed fields for convenience
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None
    
    class Config:
        from_attributes = True


class DHCPHostListResponse(BaseModel):
    """DHCP host list response"""
    hosts: List[DHCPHostResponse]
    total: int
    subnet: str


class DHCPOptionBase(BaseModel):
    """Base DHCP option model"""
    option_name: str = Field(..., description="Option name (e.g., routers, domain-name-servers)")
    option_value: str = Field(..., description="Option value")


class DHCPStatsResponse(BaseModel):
    """DHCP statistics response"""
    total_subnets: int
    total_pools: int
    total_static_hosts: int
    total_ip_addresses: int
    allocated_addresses: int
    available_addresses: int
    utilization_percent: float

