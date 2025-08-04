"""
Database utility functions for common operations and error handling.
"""
from typing import TypeVar, Type, Optional, List, Any
from sqlalchemy import select, update, delete
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, NoResultFound
from fastapi import HTTPException, status
import logging

from app.db.database import Base, AsyncSessionWrapper

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=Base)


class DatabaseError(Exception):
    """Custom database error for handling database-specific exceptions."""
    pass


class NotFoundError(DatabaseError):
    """Raised when a record is not found."""
    pass


class ValidationError(DatabaseError):
    """Raised when data validation fails."""
    pass


async def get_by_id(
    session: AsyncSessionWrapper, 
    model: Type[T], 
    record_id: Any
) -> Optional[T]:
    """
    Get a record by ID.
    
    Args:
        session: Database session wrapper
        model: SQLAlchemy model class
        record_id: Record ID to find
        
    Returns:
        Model instance or None if not found
        
    Raises:
        DatabaseError: If database operation fails
    """
    try:
        stmt = select(model).where(model.id == record_id)
        result = session.execute(stmt)
        return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_by_id: {e}")
        raise DatabaseError(f"Failed to retrieve {model.__name__} with id {record_id}")


async def get_all(
    session: AsyncSessionWrapper, 
    model: Type[T], 
    skip: int = 0, 
    limit: int = 100
) -> List[T]:
    """
    Get all records with pagination.
    
    Args:
        session: Database session wrapper
        model: SQLAlchemy model class
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of model instances
        
    Raises:
        DatabaseError: If database operation fails
    """
    try:
        stmt = select(model).offset(skip).limit(limit)
        result = session.execute(stmt)
        return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_all: {e}")
        raise DatabaseError(f"Failed to retrieve {model.__name__} records")


async def create(
    session: AsyncSessionWrapper, 
    model: Type[T], 
    **kwargs
) -> T:
    """
    Create a new record.
    
    Args:
        session: Database session wrapper
        model: SQLAlchemy model class
        **kwargs: Model attributes
        
    Returns:
        Created model instance
        
    Raises:
        DatabaseError: If database operation fails
        ValidationError: If data validation fails
    """
    try:
        instance = model(**kwargs)
        session.add(instance)
        await session.commit()
        session.refresh(instance)
        return instance
    except IntegrityError as e:
        await session.rollback()
        logger.error(f"Integrity error in create: {e}")
        raise ValidationError(f"Data validation failed for {model.__name__}")
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Database error in create: {e}")
        raise DatabaseError(f"Failed to create {model.__name__}")


async def update(
    session: AsyncSessionWrapper, 
    model: Type[T], 
    record_id: Any, 
    **kwargs
) -> Optional[T]:
    """
    Update a record by ID.
    
    Args:
        session: Database session wrapper
        model: SQLAlchemy model class
        record_id: Record ID to update
        **kwargs: Model attributes to update
        
    Returns:
        Updated model instance or None if not found
        
    Raises:
        DatabaseError: If database operation fails
        ValidationError: If data validation fails
    """
    try:
        stmt = update(model).where(model.id == record_id).values(**kwargs)
        result = session.execute(stmt)
        await session.commit()
        
        if result.rowcount == 0:
            return None
            
        return await get_by_id(session, model, record_id)
    except IntegrityError as e:
        await session.rollback()
        logger.error(f"Integrity error in update: {e}")
        raise ValidationError(f"Data validation failed for {model.__name__}")
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Database error in update: {e}")
        raise DatabaseError(f"Failed to update {model.__name__} with id {record_id}")


async def delete_by_id(
    session: AsyncSessionWrapper, 
    model: Type[T], 
    record_id: Any
) -> bool:
    """
    Delete a record by ID.
    
    Args:
        session: Database session wrapper
        model: SQLAlchemy model class
        record_id: Record ID to delete
        
    Returns:
        True if deleted, False if not found
        
    Raises:
        DatabaseError: If database operation fails
    """
    try:
        stmt = delete(model).where(model.id == record_id)
        result = session.execute(stmt)
        await session.commit()
        return result.rowcount > 0
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Database error in delete_by_id: {e}")
        raise DatabaseError(f"Failed to delete {model.__name__} with id {record_id}")


async def exists(
    session: AsyncSessionWrapper, 
    model: Type[T], 
    **filters
) -> bool:
    """
    Check if a record exists based on filters.
    
    Args:
        session: Database session wrapper
        model: SQLAlchemy model class
        **filters: Filter conditions
        
    Returns:
        True if record exists, False otherwise
        
    Raises:
        DatabaseError: If database operation fails
    """
    try:
        stmt = select(model).filter_by(**filters)
        result = session.execute(stmt)
        return result.scalar_one_or_none() is not None
    except SQLAlchemyError as e:
        logger.error(f"Database error in exists: {e}")
        raise DatabaseError(f"Failed to check existence of {model.__name__}")


def handle_database_error(error: DatabaseError) -> HTTPException:
    """
    Convert database errors to HTTP exceptions.
    
    Args:
        error: Database error to handle
        
    Returns:
        HTTPException with appropriate status code and message
    """
    if isinstance(error, NotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )
    elif isinstance(error, ValidationError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error)
        )
    else:
        logger.error(f"Unhandled database error: {error}")
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) 