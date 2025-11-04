#!/usr/bin/env python3
"""
DNS models and schemas
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator
import re


class DNSZoneBase(BaseModel):
    """Base DNS zone model"""
    idnsName: str = Field(..., description="Zone name (e.g., example.com)")
    idnsSOAserial: Optional[int] = Field(None, description="SOA serial number")
    idnsSOArefresh: int = Field(10800, description="SOA refresh (seconds)")
    idnsSOAretry: int = Field(3600, description="SOA retry (seconds)")
    idnsSOAexpire: int = Field(604800, description="SOA expire (seconds)")
    idnsSOAminimum: int = Field(86400, description="SOA minimum TTL (seconds)")
    idnsSOAmName: str = Field(..., description="SOA primary nameserver")
    idnsSOArName: str = Field(..., description="SOA responsible person email")
    
    @validator('idnsName')
    def validate_zone_name(cls, v):
        """Validate zone name format"""
        # Allow forward zones (domain.com) and reverse zones (1.168.192.in-addr.arpa)
        if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-\.]*[a-zA-Z0-9])?$', v):
            raise ValueError('Invalid zone name format')
        return v.lower()


class DNSZoneCreate(DNSZoneBase):
    """DNS zone creation model"""
    description: Optional[str] = Field(None, description="Zone description")
    dnssec: bool = Field(False, description="Enable DNSSEC")


class DNSZoneUpdate(BaseModel):
    """DNS zone update model"""
    description: Optional[str] = None
    idnsSOArefresh: Optional[int] = None
    idnsSOAretry: Optional[int] = None
    idnsSOAexpire: Optional[int] = None
    idnsSOAminimum: Optional[int] = None
    dnssec: Optional[bool] = None


class DNSZoneResponse(BaseModel):
    """DNS zone response model"""
    dn: str
    idnsName: str
    idnsSOAserial: Optional[int] = None
    idnsSOArefresh: int
    idnsSOAretry: int
    idnsSOAexpire: int
    idnsSOAminimum: int
    idnsSOAmName: str
    idnsSOArName: str
    description: Optional[str] = None
    dnssec: bool = False
    createTimestamp: Optional[str] = None
    modifyTimestamp: Optional[str] = None
    
    class Config:
        from_attributes = True


class DNSZoneListResponse(BaseModel):
    """DNS zone list response"""
    zones: List[DNSZoneResponse]
    total: int
    page: int
    page_size: int


class DNSRecordBase(BaseModel):
    """Base DNS record model"""
    idnsName: str = Field(..., description="Record name (relative to zone)")
    record_type: str = Field(..., description="Record type (A, AAAA, CNAME, MX, TXT, PTR, SRV, NS)")
    value: str = Field(..., description="Record value")
    ttl: Optional[int] = Field(3600, description="TTL in seconds")
    
    @validator('record_type')
    def validate_record_type(cls, v):
        """Validate record type"""
        valid_types = ['A', 'AAAA', 'CNAME', 'MX', 'TXT', 'PTR', 'SRV', 'NS', 'SOA']
        if v.upper() not in valid_types:
            raise ValueError(f'Invalid record type. Must be one of: {", ".join(valid_types)}')
        return v.upper()


class DNSRecordCreate(DNSRecordBase):
    """DNS record creation model"""
    priority: Optional[int] = Field(None, description="Priority for MX/SRV records")


class DNSRecordUpdate(BaseModel):
    """DNS record update model"""
    value: Optional[str] = None
    ttl: Optional[int] = None
    priority: Optional[int] = None


class DNSRecordResponse(BaseModel):
    """DNS record response model"""
    dn: str
    idnsName: str
    record_type: str
    value: str
    ttl: Optional[int] = None
    priority: Optional[int] = None
    createTimestamp: Optional[str] = None
    modifyTimestamp: Optional[str] = None
    
    class Config:
        from_attributes = True


class DNSRecordListResponse(BaseModel):
    """DNS record list response"""
    records: List[DNSRecordResponse]
    total: int
    zone: str

