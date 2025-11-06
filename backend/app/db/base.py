"""
Database base classes and connection management
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator, Optional
import logging

from app.config import get_config

logger = logging.getLogger(__name__)

# SQLAlchemy declarative base for all models
Base = declarative_base()

# Global database manager instance
_db_manager: Optional['DatabaseManager'] = None


class DatabaseManager:
    """
    Manages PostgreSQL database connections and sessions
    Supports both sync and async operations with connection pooling
    """
    
    def __init__(self):
        self.engine = None
        self.async_engine = None
        self.SessionLocal = None
        self.AsyncSessionLocal = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """
        Initialize database connection and create tables
        Must be called once at application startup
        """
        if self._initialized:
            return
        
        config = get_config()
        
        logger.info("Initializing PostgreSQL database connection...")
        
        # Create async engine for async operations
        # Using asyncpg for better async performance
        async_db_url = config.database_url
        if not async_db_url.startswith("postgresql+asyncpg://"):
            # Convert postgresql:// to postgresql+asyncpg://
            async_db_url = async_db_url.replace("postgresql://", "postgresql+asyncpg://")
        
        self.async_engine = create_async_engine(
            async_db_url,
            echo=config.debug,
            pool_size=config.database_pool_size,
            max_overflow=config.database_max_overflow,
            pool_timeout=config.database_pool_timeout,
            pool_recycle=config.database_pool_recycle,
            pool_pre_ping=True,  # Test connection before using
            connect_args={
                "timeout": config.database_pool_timeout,
                "server_settings": {
                    "jit": "off",  # Disable JIT for consistency
                }
            }
        )
        
        # Create async session factory
        self.AsyncSessionLocal = async_sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False
        )
        
        # Create all tables
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database initialization complete")
        self._initialized = True
    
    async def close(self) -> None:
        """Close database connection pool"""
        if self.async_engine:
            await self.async_engine.dispose()
            logger.info("Database connection pool closed")
    
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get an async database session
        Use as dependency in FastAPI routes
        
        Example:
            @app.get("/items")
            async def get_items(session: AsyncSession = Depends(get_session)):
                result = await session.execute(select(Item))
                return result.scalars().all()
        """
        if not self.AsyncSessionLocal:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        session = self.AsyncSessionLocal()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    async def health_check(self) -> bool:
        """
        Check database connection health
        
        Returns:
            bool: True if connection is healthy, False otherwise
        """
        try:
            async with self.AsyncSessionLocal() as session:
                await session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


async def get_database() -> DatabaseManager:
    """Get the global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        await _db_manager.initialize()
    return _db_manager


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for getting database session
    
    Usage:
        @app.get("/items")
        async def get_items(session: AsyncSession = Depends(get_session)):
            ...
    """
    db = await get_database()
    async for session in db.get_async_session():
        yield session


