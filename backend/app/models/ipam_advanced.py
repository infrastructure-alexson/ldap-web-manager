#!/usr/bin/env python3
"""
Advanced IPAM Models

Defines models for pool management, IP search/discovery, and subnet calculator.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from ipaddress import IPv4Network, IPv4Address
import ipaddress


class PoolManagementCreate(BaseModel):
    """Advanced pool creation with templates"""
    name: str = Field(..., description="Pool name")
    network: str = Field(..., description="Network in CIDR notation")
    gateway: Optional[str] = Field(None, description="Gateway IP")
    vlan_id: Optional[int] = Field(None, description="VLAN ID")
    dns_servers: Optional[List[str]] = Field(None, description="DNS servers")
    description: Optional[str] = Field(None, description="Pool description")
    template: Optional[str] = Field(None, description="Template name (e.g., 'production', 'test')")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Production Pool",
                "network": "10.0.0.0/24",
                "gateway": "10.0.0.1",
                "vlan_id": 100,
                "dns_servers": ["8.8.8.8", "8.8.4.4"],
                "template": "production"
            }
        }


class SubnetSplit(BaseModel):
    """Result of subnet split operation"""
    original_network: str = Field(..., description="Original network")
    subnets: List[str] = Field(..., description="List of split subnets")
    subnet_count: int = Field(..., description="Number of resulting subnets")
    hosts_per_subnet: int = Field(..., description="Usable hosts per subnet")
    
    class Config:
        schema_extra = {
            "example": {
                "original_network": "10.0.0.0/24",
                "subnets": ["10.0.0.0/25", "10.0.0.128/25"],
                "subnet_count": 2,
                "hosts_per_subnet": 126
            }
        }


class SubnetMerge(BaseModel):
    """Result of subnet merge operation"""
    subnets: List[str] = Field(..., description="Subnets to merge")
    merged_network: str = Field(..., description="Resulting merged network")
    
    class Config:
        schema_extra = {
            "example": {
                "subnets": ["10.0.0.0/25", "10.0.0.128/25"],
                "merged_network": "10.0.0.0/24"
            }
        }


class SubnetCalculatorRequest(BaseModel):
    """Subnet calculator request"""
    operation: str = Field(..., description="Operation: split, merge, info, validate")
    network: Optional[str] = Field(None, description="Network for single operations")
    networks: Optional[List[str]] = Field(None, description="Networks for merge operations")
    subnet_count: Optional[int] = Field(None, description="Number of subnets for split")
    
    class Config:
        schema_extra = {
            "example": {
                "operation": "split",
                "network": "10.0.0.0/24",
                "subnet_count": 4
            }
        }


class SubnetInfo(BaseModel):
    """Detailed subnet information"""
    network: str = Field(..., description="Network address")
    netmask: str = Field(..., description="Network mask")
    broadcast: str = Field(..., description="Broadcast address")
    first_host: str = Field(..., description="First usable host")
    last_host: str = Field(..., description="Last usable host")
    total_hosts: int = Field(..., description="Total host count")
    usable_hosts: int = Field(..., description="Usable hosts (excluding network and broadcast)")
    prefix_length: int = Field(..., description="CIDR prefix length")
    
    class Config:
        schema_extra = {
            "example": {
                "network": "10.0.0.0",
                "netmask": "255.255.255.0",
                "broadcast": "10.0.0.255",
                "first_host": "10.0.0.1",
                "last_host": "10.0.0.254",
                "total_hosts": 256,
                "usable_hosts": 254,
                "prefix_length": 24
            }
        }


class IPSearchRequest(BaseModel):
    """IP search and discovery request"""
    query: str = Field(..., description="Search query (IP, hostname, MAC, owner, etc.)")
    search_type: Optional[str] = Field(None, description="Search type: ip, hostname, mac, owner, pool")
    pool_id: Optional[int] = Field(None, description="Filter to specific pool")
    allocated_only: bool = Field(False, description="Only allocated IPs")
    available_only: bool = Field(False, description="Only available IPs")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "server",
                "search_type": "hostname",
                "allocated_only": True
            }
        }


class IPSearchResult(BaseModel):
    """Result of IP search"""
    pool_name: str = Field(..., description="Pool name")
    pool_id: int = Field(..., description="Pool ID")
    ip_address: str = Field(..., description="IP address")
    hostname: Optional[str] = Field(None, description="Hostname")
    owner: Optional[str] = Field(None, description="Owner")
    status: str = Field(..., description="Status")
    mac_address: Optional[str] = Field(None, description="MAC address")
    purpose: Optional[str] = Field(None, description="Purpose")
    allocated_at: Optional[str] = Field(None, description="Allocation timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "pool_name": "Production",
                "pool_id": 1,
                "ip_address": "10.0.0.50",
                "hostname": "server1",
                "owner": "admin",
                "status": "allocated",
                "mac_address": "00:11:22:33:44:55"
            }
        }


class IPSearchResults(BaseModel):
    """List of IP search results"""
    total: int = Field(..., description="Total results")
    results: List[IPSearchResult] = Field(..., description="Search results")
    
    class Config:
        schema_extra = {
            "example": {
                "total": 5,
                "results": [
                    {
                        "pool_name": "Production",
                        "pool_id": 1,
                        "ip_address": "10.0.0.50",
                        "hostname": "server1",
                        "owner": "admin",
                        "status": "allocated"
                    }
                ]
            }
        }


class ConflictDetection(BaseModel):
    """IP conflict detection result"""
    has_conflicts: bool = Field(..., description="Whether conflicts were found")
    conflicts: List[Dict[str, Any]] = Field(..., description="List of conflicts")
    summary: str = Field(..., description="Conflict summary")
    
    class Config:
        schema_extra = {
            "example": {
                "has_conflicts": True,
                "conflicts": [
                    {
                        "ip": "10.0.0.50",
                        "pools": [1, 2],
                        "issue": "Allocated in multiple pools"
                    }
                ],
                "summary": "Found 1 conflict"
            }
        }

