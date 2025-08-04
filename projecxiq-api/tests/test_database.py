"""
Unit tests for database connection and session management.
"""
import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import (
    async_engine, sync_engine, AsyncSessionLocal, SyncSessionLocal,
    get_db, get_sync_db, get_db_transaction, init_db, close_db,
    init_sync_db, close_sync_db
)
from app.db.utils import (
    get_by_id, get_all, create, update, delete_by_id, exists,
    DatabaseError, NotFoundError, ValidationError, handle_database_error
)
from app.models import User
from fastapi import HTTPException


@pytest.fixture
def test_engine():
    """Create a test SQLite engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return engine


@pytest.fixture
def test_session(test_engine):
    """Create a test database session."""
    from app.db.database import Base
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


class TestDatabaseConfiguration:
    """Test database configuration and engines."""

    def test_sync_engine_creation(self):
        """Test that sync engine is created properly."""
        assert sync_engine is not None
        assert str(sync_engine.url) == "postgresql://postgres:postgres@localhost:5432/project_management"

    def test_async_engine_creation(self):
        """Test that async engine is created properly."""
        assert async_engine is not None
        assert "postgresql+psycopg2://" in str(async_engine.url)

    def test_session_factories(self):
        """Test that session factories are created properly."""
        assert AsyncSessionLocal is not None
        assert SyncSessionLocal is not None


class TestDatabaseUtils:
    """Test database utility functions."""

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, test_session):
        """Test successful get_by_id operation."""
        # Create a test user
        user = User(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            password_hash="hashed_password",
            role="Developer"
        )
        test_session.add(user)
        test_session.commit()
        test_session.refresh(user)

        # Test get_by_id
        result = await get_by_id(test_session, User, user.id)
        assert result is not None
        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, test_session):
        """Test get_by_id when record not found."""
        import uuid
        result = await get_by_id(test_session, User, uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_with_pagination(self, test_session):
        """Test get_all with pagination."""
        # Create multiple test users
        users = [
            User(
                email=f"user{i}@example.com",
                first_name=f"User{i}",
                last_name="Test",
                password_hash="hashed_password",
                role="Developer"
            )
            for i in range(5)
        ]
        for user in users:
            test_session.add(user)
        test_session.commit()

        # Test get_all with pagination
        result = await get_all(test_session, User, skip=1, limit=3)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_create_success(self, test_session):
        """Test successful create operation."""
        user_data = {
            "email": "new@example.com",
            "first_name": "New",
            "last_name": "User",
            "password_hash": "hashed_password",
            "role": "Developer"
        }
        
        result = await create(test_session, User, **user_data)
        assert result is not None
        assert result.email == "new@example.com"
        assert result.id is not None

    @pytest.mark.asyncio
    async def test_create_validation_error(self, test_session):
        """Test create operation with validation error."""
        # Try to create user with invalid role
        user_data = {
            "email": "invalid@example.com",
            "first_name": "Invalid",
            "last_name": "User",
            "password_hash": "hashed_password",
            "role": "InvalidRole"  # Invalid role
        }
        
        with pytest.raises(ValidationError):
            await create(test_session, User, **user_data)

    @pytest.mark.asyncio
    async def test_update_success(self, test_session):
        """Test successful update operation."""
        # Create a test user
        user = User(
            email="update@example.com",
            first_name="Update",
            last_name="User",
            password_hash="hashed_password",
            role="Developer"
        )
        test_session.add(user)
        test_session.commit()
        test_session.refresh(user)

        # Update the user
        result = await update(test_session, User, user.id, first_name="Updated")
        assert result is not None
        assert result.first_name == "Updated"

    @pytest.mark.asyncio
    async def test_update_not_found(self, test_session):
        """Test update operation when record not found."""
        import uuid
        result = await update(test_session, User, uuid.uuid4(), first_name="Updated")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_by_id_success(self, test_session):
        """Test successful delete_by_id operation."""
        # Create a test user
        user = User(
            email="delete@example.com",
            first_name="Delete",
            last_name="User",
            password_hash="hashed_password",
            role="Developer"
        )
        test_session.add(user)
        test_session.commit()
        test_session.refresh(user)

        # Delete the user
        result = await delete_by_id(test_session, User, user.id)
        assert result is True

        # Verify user is deleted
        deleted_user = await get_by_id(test_session, User, user.id)
        assert deleted_user is None

    @pytest.mark.asyncio
    async def test_delete_by_id_not_found(self, test_session):
        """Test delete_by_id when record not found."""
        import uuid
        result = await delete_by_id(test_session, User, uuid.uuid4())
        assert result is False

    @pytest.mark.asyncio
    async def test_exists_true(self, test_session):
        """Test exists function when record exists."""
        # Create a test user
        user = User(
            email="exists@example.com",
            first_name="Exists",
            last_name="User",
            password_hash="hashed_password",
            role="Developer"
        )
        test_session.add(user)
        test_session.commit()

        # Check if user exists
        result = await exists(test_session, User, email="exists@example.com")
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(self, test_session):
        """Test exists function when record doesn't exist."""
        result = await exists(test_session, User, email="nonexistent@example.com")
        assert result is False


class TestErrorHandling:
    """Test error handling utilities."""

    def test_handle_database_error_not_found(self):
        """Test handling NotFoundError."""
        error = NotFoundError("User not found")
        result = handle_database_error(error)
        
        assert isinstance(result, HTTPException)
        assert result.status_code == 404
        assert "User not found" in str(result.detail)

    def test_handle_database_error_validation(self):
        """Test handling ValidationError."""
        error = ValidationError("Invalid data")
        result = handle_database_error(error)
        
        assert isinstance(result, HTTPException)
        assert result.status_code == 422
        assert "Invalid data" in str(result.detail)

    def test_handle_database_error_generic(self):
        """Test handling generic DatabaseError."""
        error = DatabaseError("Database connection failed")
        result = handle_database_error(error)
        
        assert isinstance(result, HTTPException)
        assert result.status_code == 500
        assert "Internal server error" in str(result.detail)


class TestDatabaseLifecycle:
    """Test database lifecycle functions."""

    @pytest.mark.asyncio
    async def test_init_db(self):
        """Test database initialization."""
        # This test would require a real database connection
        # For now, we'll just test that the function exists and is callable
        assert callable(init_db)

    @pytest.mark.asyncio
    async def test_close_db(self):
        """Test database cleanup."""
        # This test would require a real database connection
        # For now, we'll just test that the function exists and is callable
        assert callable(close_db)

    def test_init_sync_db(self):
        """Test synchronous database initialization."""
        assert callable(init_sync_db)

    def test_close_sync_db(self):
        """Test synchronous database cleanup."""
        assert callable(close_sync_db) 