#!/usr/bin/env python3
"""
Migration script: SQLite to PostgreSQL for IPAM data

This script migrates existing IPAM data from SQLite (development)
to PostgreSQL (production) while maintaining data integrity.

Usage:
    python migrate-from-sqlite.py --sqlite-db /path/to/ipam.db

Prerequisites:
    - PostgreSQL database initialized (run: alembic upgrade head)
    - DATABASE_URL environment variable set
    - SQLite database file exists
"""

import sqlite3
import asyncio
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

import os
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_config
from app.db.base import get_database
from app.db.models import IPPool, IPAllocation, AuditLog, AuditAction
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SQLiteToPostgresMigrator:
    """Migrates IPAM data from SQLite to PostgreSQL"""
    
    def __init__(self, sqlite_db_path: str):
        self.sqlite_db_path = sqlite_db_path
        self.sqlite_conn = None
        self.stats = {
            'pools': 0,
            'allocations': 0,
            'errors': 0,
        }
    
    def connect_sqlite(self) -> None:
        """Connect to SQLite database"""
        if not Path(self.sqlite_db_path).exists():
            raise FileNotFoundError(f"SQLite database not found: {self.sqlite_db_path}")
        
        self.sqlite_conn = sqlite3.connect(self.sqlite_db_path)
        self.sqlite_conn.row_factory = sqlite3.Row
        logger.info(f"Connected to SQLite: {self.sqlite_db_path}")
    
    def close_sqlite(self) -> None:
        """Close SQLite connection"""
        if self.sqlite_conn:
            self.sqlite_conn.close()
            logger.info("SQLite connection closed")
    
    async def migrate_pools(self, session: AsyncSession) -> int:
        """Migrate IP pools from SQLite to PostgreSQL"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute("SELECT * FROM ip_pools")
        
        migrated = 0
        for row in cursor.fetchall():
            try:
                pool = IPPool(
                    name=row['name'],
                    description=row.get('description'),
                    network=row['network'],
                    gateway=row.get('gateway'),
                    vlan_id=row.get('vlan_id'),
                    site=row.get('site'),
                    environment=row.get('environment'),
                    is_active=bool(row.get('is_active', True)),
                    created_at=datetime.fromisoformat(row['created_at']) if row.get('created_at') else datetime.utcnow(),
                    updated_at=datetime.fromisoformat(row['updated_at']) if row.get('updated_at') else datetime.utcnow(),
                    created_by=row.get('created_by'),
                )
                session.add(pool)
                migrated += 1
                logger.debug(f"Migrating pool: {pool.name}")
            
            except Exception as e:
                logger.error(f"Error migrating pool {row.get('name', 'unknown')}: {e}")
                self.stats['errors'] += 1
        
        await session.flush()
        logger.info(f"Migrated {migrated} IP pools")
        return migrated
    
    async def migrate_allocations(self, session: AsyncSession) -> int:
        """Migrate IP allocations from SQLite to PostgreSQL"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute("SELECT * FROM ip_allocations")
        
        migrated = 0
        for row in cursor.fetchall():
            try:
                # Get pool by name
                pool_result = await session.execute(
                    select(IPPool).where(IPPool.id == row['pool_id'])
                )
                pool = pool_result.scalar_one_or_none()
                
                if not pool:
                    logger.warning(f"Pool ID {row['pool_id']} not found for allocation {row.get('ip_address')}")
                    self.stats['errors'] += 1
                    continue
                
                allocation = IPAllocation(
                    pool_id=pool.id,
                    ip_address=row['ip_address'],
                    mac_address=row.get('mac_address'),
                    hostname=row.get('hostname'),
                    owner=row.get('owner'),
                    purpose=row.get('purpose'),
                    description=row.get('description'),
                    status=row.get('status', 'available'),
                    dns_managed=bool(row.get('dns_managed')),
                    dhcp_managed=bool(row.get('dhcp_managed')),
                    allocated_at=datetime.fromisoformat(row['allocated_at']) if row.get('allocated_at') else None,
                    released_at=datetime.fromisoformat(row['released_at']) if row.get('released_at') else None,
                    created_at=datetime.fromisoformat(row['created_at']) if row.get('created_at') else datetime.utcnow(),
                    updated_at=datetime.fromisoformat(row['updated_at']) if row.get('updated_at') else datetime.utcnow(),
                    allocated_by=row.get('allocated_by'),
                )
                session.add(allocation)
                migrated += 1
                logger.debug(f"Migrating allocation: {allocation.ip_address}")
            
            except Exception as e:
                logger.error(f"Error migrating allocation {row.get('ip_address', 'unknown')}: {e}")
                self.stats['errors'] += 1
        
        await session.flush()
        logger.info(f"Migrated {migrated} IP allocations")
        return migrated
    
    async def run(self) -> None:
        """Run complete migration"""
        try:
            logger.info("=" * 60)
            logger.info("Starting SQLite to PostgreSQL migration")
            logger.info("=" * 60)
            
            # Connect to SQLite
            self.connect_sqlite()
            
            # Get PostgreSQL session
            db = await get_database()
            async with db.AsyncSessionLocal() as session:
                # Migrate pools first (parent tables)
                self.stats['pools'] = await self.migrate_pools(session)
                
                # Then migrate allocations (child tables)
                self.stats['allocations'] = await self.migrate_allocations(session)
                
                # Log migration audit entry
                audit_log = AuditLog(
                    action=AuditAction.CREATE,
                    resource_type="migration",
                    resource_name="sqlite_to_postgres",
                    user_id="system",
                    status="success",
                    details={
                        'source': 'sqlite',
                        'destination': 'postgresql',
                        'pools_migrated': self.stats['pools'],
                        'allocations_migrated': self.stats['allocations'],
                        'errors': self.stats['errors'],
                    }
                )
                session.add(audit_log)
                
                # Commit all changes
                await session.commit()
                logger.info("All changes committed to PostgreSQL")
            
            # Close SQLite connection
            self.close_sqlite()
            
            # Print summary
            logger.info("=" * 60)
            logger.info("Migration Summary")
            logger.info("=" * 60)
            logger.info(f"IP Pools:       {self.stats['pools']:>6}")
            logger.info(f"Allocations:    {self.stats['allocations']:>6}")
            logger.info(f"Errors:         {self.stats['errors']:>6}")
            logger.info("=" * 60)
            
            if self.stats['errors'] > 0:
                logger.warning(f"Migration completed with {self.stats['errors']} errors")
            else:
                logger.info("Migration completed successfully!")
        
        except Exception as e:
            logger.error(f"Migration failed: {e}", exc_info=True)
            raise


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Migrate IPAM data from SQLite to PostgreSQL"
    )
    parser.add_argument(
        "--sqlite-db",
        required=True,
        help="Path to SQLite database file"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Verify database URL is set
    if not os.environ.get('DATABASE_URL'):
        config = get_config()
        os.environ['DATABASE_URL'] = config.database_url
    
    # Run migration
    migrator = SQLiteToPostgresMigrator(args.sqlite_db)
    await migrator.run()


if __name__ == "__main__":
    asyncio.run(main())

