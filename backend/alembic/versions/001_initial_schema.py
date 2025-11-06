"""Initial schema creation for IPAM and audit logging

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-11-06

This migration creates the initial database schema for:
- IPAM (IP pools and allocations)
- Audit logging (all operations)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    audit_action_enum = postgresql.ENUM('create', 'read', 'update', 'delete', 'login', 'logout', 'authenticate', 'authorize', 'error', name='auditaction')
    audit_action_enum.create(op.get_bind(), checkfirst=True)
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('action', audit_action_enum, nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', sa.String(255)),
        sa.Column('resource_name', sa.String(255)),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('user_ip', sa.String(45)),
        sa.Column('user_agent', sa.String(255)),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('details', postgresql.JSON),
    )
    
    # Create indexes for audit_logs
    op.create_index('idx_audit_logs_created_at_action', 'audit_logs', ['created_at', 'action'])
    op.create_index('idx_audit_logs_user_id_created_at', 'audit_logs', ['user_id', 'created_at'])
    op.create_index('idx_audit_logs_resource_type_created_at', 'audit_logs', ['resource_type', 'created_at'])
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'])
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_logs_resource_type', 'audit_logs', ['resource_type'])
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'])
    
    # Create ip_pools table
    op.create_table(
        'ip_pools',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(255), unique=True, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('network', postgresql.CIDR, unique=True, nullable=False),
        sa.Column('gateway', postgresql.INET),
        sa.Column('vlan_id', sa.Integer),
        sa.Column('site', sa.String(255)),
        sa.Column('environment', sa.String(50)),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('created_by', sa.String(255)),
    )
    
    # Create indexes for ip_pools
    op.create_index('idx_ip_pools_name', 'ip_pools', ['name'])
    op.create_index('idx_ip_pools_is_active', 'ip_pools', ['is_active'])
    
    # Create ip_allocations table
    op.create_table(
        'ip_allocations',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('pool_id', sa.Integer, sa.ForeignKey('ip_pools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ip_address', postgresql.INET, unique=True, nullable=False),
        sa.Column('mac_address', postgresql.MACADDR),
        sa.Column('hostname', sa.String(255)),
        sa.Column('owner', sa.String(255)),
        sa.Column('purpose', sa.String(255)),
        sa.Column('description', sa.Text),
        sa.Column('status', sa.String(50), nullable=False, default='available'),
        sa.Column('dns_managed', sa.Boolean, default=False),
        sa.Column('dhcp_managed', sa.Boolean, default=False),
        sa.Column('allocated_at', sa.DateTime(timezone=True)),
        sa.Column('released_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('allocated_by', sa.String(255)),
    )
    
    # Create indexes for ip_allocations
    op.create_index('idx_ip_allocations_pool_id', 'ip_allocations', ['pool_id'])
    op.create_index('idx_ip_allocations_ip_address', 'ip_allocations', ['ip_address'])
    op.create_index('idx_ip_allocations_mac_address', 'ip_allocations', ['mac_address'])
    op.create_index('idx_ip_allocations_hostname', 'ip_allocations', ['hostname'])
    op.create_index('idx_ip_allocations_pool_id_status', 'ip_allocations', ['pool_id', 'status'])
    
    # Create audit_log_retention_policies table
    op.create_table(
        'audit_log_retention_policies',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('resource_type', sa.String(50), unique=True, nullable=False),
        sa.Column('retention_days', sa.Integer, default=365),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    # Drop audit_log_retention_policies table
    op.drop_table('audit_log_retention_policies')
    
    # Drop ip_allocations table and indexes
    op.drop_index('idx_ip_allocations_pool_id_status')
    op.drop_index('idx_ip_allocations_hostname')
    op.drop_index('idx_ip_allocations_mac_address')
    op.drop_index('idx_ip_allocations_ip_address')
    op.drop_index('idx_ip_allocations_pool_id')
    op.drop_table('ip_allocations')
    
    # Drop ip_pools table and indexes
    op.drop_index('idx_ip_pools_is_active')
    op.drop_index('idx_ip_pools_name')
    op.drop_table('ip_pools')
    
    # Drop audit_logs table and indexes
    op.drop_index('idx_audit_logs_user_id')
    op.drop_index('idx_audit_logs_resource_type')
    op.drop_index('idx_audit_logs_action')
    op.drop_index('idx_audit_logs_created_at')
    op.drop_index('idx_audit_logs_resource_type_created_at')
    op.drop_index('idx_audit_logs_user_id_created_at')
    op.drop_index('idx_audit_logs_created_at_action')
    op.drop_table('audit_logs')
    
    # Drop enum type
    audit_action_enum = postgresql.ENUM('create', 'read', 'update', 'delete', 'login', 'logout', 'authenticate', 'authorize', 'error', name='auditaction')
    audit_action_enum.drop(op.get_bind(), checkfirst=True)

