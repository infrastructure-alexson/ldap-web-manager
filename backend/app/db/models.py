"""
SQLAlchemy models for IPAM and audit logging
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, Enum as SQLEnum, Index, ForeignKey
from sqlalchemy.dialects.postgresql import INET, CIDR, MACADDR, UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
import uuid

from .base import Base


class AuditAction(str, Enum):
    """Types of actions that can be audited"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    AUTHENTICATE = "authenticate"
    AUTHORIZE = "authorize"
    ERROR = "error"


class AuditLog(Base):
    """
    Audit log entry for all LDAP, DNS, DHCP, and IPAM operations
    Used for compliance, debugging, and security monitoring
    """
    __tablename__ = "audit_logs"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), index=True, nullable=False, default=datetime.utcnow)
    
    # Action details
    action = Column(SQLEnum(AuditAction), index=True, nullable=False)
    resource_type = Column(String(50), index=True, nullable=False)  # user, group, dns_zone, dhcp_subnet, ip_pool, etc.
    resource_id = Column(String(255), index=True, nullable=True)
    resource_name = Column(String(255), nullable=True)
    
    # User information
    user_id = Column(String(255), index=True, nullable=False)  # LDAP username
    user_ip = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(255), nullable=True)
    
    # Change details
    status = Column(String(20), nullable=False, default="success")  # success, failure, warning
    details = Column(JSON, nullable=True)  # Before/after snapshots, error messages, etc.
    
    # Indexing for common queries
    __table_args__ = (
        Index('idx_audit_logs_created_at_action', 'created_at', 'action'),
        Index('idx_audit_logs_user_id_created_at', 'user_id', 'created_at'),
        Index('idx_audit_logs_resource_type_created_at', 'resource_type', 'created_at'),
    )
    
    def __repr__(self):
        return f"<AuditLog {self.id} {self.action} {self.resource_type}/{self.resource_name}>"


class IPPool(Base):
    """
    IP address pool for IPAM
    Represents a block of IP addresses available for allocation
    """
    __tablename__ = "ip_pools"
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Pool information
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Network information using PostgreSQL CIDR type
    network = Column(CIDR, nullable=False, unique=True)
    gateway = Column(INET, nullable=True)
    
    # Metadata
    vlan_id = Column(Integer, nullable=True)
    site = Column(String(255), nullable=True)
    environment = Column(String(50), nullable=True)  # production, staging, development
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Tracking
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    # Relationships
    allocations = relationship("IPAllocation", back_populates="pool", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<IPPool {self.name} {self.network}>"


class IPAllocation(Base):
    """
    Individual IP address allocation
    Tracks which IPs are allocated, reserved, or available
    """
    __tablename__ = "ip_allocations"
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Pool relationship
    pool_id = Column(Integer, ForeignKey('ip_pools.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # IP information using PostgreSQL INET type
    ip_address = Column(INET, nullable=False, unique=True, index=True)
    mac_address = Column(MACADDR, nullable=True)
    
    # Allocation details
    hostname = Column(String(255), nullable=True, index=True)
    owner = Column(String(255), nullable=True)  # LDAP user or service
    purpose = Column(String(255), nullable=True)  # Server, printer, workstation, etc.
    description = Column(Text, nullable=True)
    
    # Status
    status = Column(String(50), nullable=False, default="available")  # available, allocated, reserved, blocked
    dns_managed = Column(Boolean, default=False)  # Whether DNS record is managed
    dhcp_managed = Column(Boolean, default=False)  # Whether DHCP reservation is managed
    
    # Tracking
    allocated_at = Column(DateTime(timezone=True), nullable=True)
    released_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    allocated_by = Column(String(255), nullable=True)  # LDAP username
    
    # Relationships
    pool = relationship("IPPool", back_populates="allocations")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_ip_allocations_pool_id_status', 'pool_id', 'status'),
        Index('idx_ip_allocations_mac_address', 'mac_address'),
        Index('idx_ip_allocations_hostname', 'hostname'),
    )
    
    def __repr__(self):
        return f"<IPAllocation {self.ip_address} {self.status}>"


class AuditLogRetentionPolicy(Base):
    """
    Configuration for audit log retention
    Supports partitioning and automated cleanup
    """
    __tablename__ = "audit_log_retention_policies"
    
    id = Column(Integer, primary_key=True)
    resource_type = Column(String(50), unique=True, nullable=False)
    retention_days = Column(Integer, default=365)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<AuditLogRetentionPolicy {self.resource_type} {self.retention_days} days>"


# Database initialization hint for Alembic
# This module is used by: alembic/env.py
# Make sure to import all models here so Alembic detects them

