"""
Database configuration and session management for the Project Management Dashboard.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Generator
import asyncio
from functools import wraps

from app.db.config import get_database_url, get_database_echo

# Create sync engine for all operations
sync_engine = create_engine(
    get_database_url(),
    echo=get_database_echo(),
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_reset_on_return='commit',
)

# Create sync session factory
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

# Create base class for models
Base = declarative_base()


def async_to_sync(func):
    """Decorator to convert async functions to sync for compatibility."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(func(*args, **kwargs))
    return wrapper


class AsyncSessionWrapper:
    """Wrapper to provide async-like interface for sync sessions."""
    
    def __init__(self, session):
        self.session = session
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()
    
    async def commit(self):
        self.session.commit()
    
    async def rollback(self):
        self.session.rollback()
    
    async def close(self):
        self.session.close()
    
    def __getattr__(self, name):
        return getattr(self.session, name)


async def get_db() -> AsyncGenerator[AsyncSessionWrapper, None]:
    """
    Dependency to get database session.
    
    Yields:
        AsyncSessionWrapper: Database session wrapper for FastAPI dependency injection
    """
    session = SyncSessionLocal()
    wrapper = AsyncSessionWrapper(session)
    try:
        yield wrapper
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_sync_db() -> Generator:
    """
    Get synchronous database session for Alembic and testing.
    
    Yields:
        Session: Synchronous database session
    """
    session = SyncSessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@asynccontextmanager
async def get_db_transaction() -> AsyncGenerator[AsyncSessionWrapper, None]:
    """
    Context manager for database transactions.
    
    Yields:
        AsyncSessionWrapper: Database session wrapper with transaction management
    """
    session = SyncSessionLocal()
    wrapper = AsyncSessionWrapper(session)
    try:
        yield wrapper
    except Exception:
        session.rollback()
        raise


async def init_db():
    """Initialize database tables."""
    init_sync_db()


async def close_db():
    """Close database connections."""
    close_sync_db()


def init_sync_db():
    """Initialize database tables synchronously."""
    Base.metadata.create_all(bind=sync_engine)


def close_sync_db():
    """Close synchronous database connections."""
    sync_engine.dispose()


# For compatibility with existing code
async_engine = None  # Not used in this implementation
AsyncSessionLocal = None  # Not used in this implementation 
