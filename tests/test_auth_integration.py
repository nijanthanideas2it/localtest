"""
Integration tests for authentication functionality.
"""
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.auth import AuthUtils
from app.models.user import User
from app.db.database import get_sync_db, init_sync_db


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Database session fixture."""
    # Initialize test database
    init_sync_db()
    
    # Get database session
    session = next(get_sync_db())
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "TestPass123!",
        "first_name": "Test",
        "last_name": "User",
        "role": "Developer"
    }


@pytest.fixture
def sample_user(db_session, sample_user_data):
    """Sample user object for testing."""
    user = User(
        email=sample_user_data["email"],
        first_name=sample_user_data["first_name"],
        last_name=sample_user_data["last_name"],
        password_hash=AuthUtils.get_password_hash(sample_user_data["password"]),
        role=sample_user_data["role"],
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user


class TestAuthIntegration:
    """Integration tests for authentication endpoints."""
    
    def test_register_success(self, client, sample_user_data):
        """Test successful user registration."""
        response = client.post("/auth/register", json=sample_user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == sample_user_data["email"]
        assert data["data"]["first_name"] == sample_user_data["first_name"]
        assert data["data"]["last_name"] == sample_user_data["last_name"]
        assert data["data"]["role"] == sample_user_data["role"]
    
    def test_register_email_exists(self, client, sample_user_data, sample_user):
        """Test registration with existing email."""
        response = client.post("/auth/register", json=sample_user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "Email already registered" in data["detail"]
    
    def test_register_weak_password(self, client):
        """Test registration with weak password."""
        weak_password_data = {
            "email": "test2@example.com",
            "password": "weak",
            "first_name": "Test",
            "last_name": "User",
            "role": "Developer"
        }
        
        response = client.post("/auth/register", json=weak_password_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "Password does not meet security requirements" in data["detail"]
    
    def test_login_success(self, client, sample_user_data, sample_user):
        """Test successful user login."""
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"
        assert data["data"]["user"]["email"] == sample_user_data["email"]
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "Incorrect email or password" in data["detail"]
    
    def test_refresh_token_success(self, client, sample_user_data, sample_user):
        """Test successful token refresh."""
        # First login to get refresh token
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        
        login_response = client.post("/auth/login", json=login_data)
        login_data = login_response.json()
        refresh_token = login_data["data"]["refresh_token"]
        
        # Now test refresh
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"
    
    def test_refresh_token_invalid(self, client):
        """Test token refresh with invalid token."""
        refresh_data = {"refresh_token": "invalid_token"}
        
        response = client.post("/auth/refresh", json=refresh_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "Could not validate credentials" in data["detail"]
    
    def test_logout_success(self, client, sample_user_data, sample_user):
        """Test successful logout."""
        # First login to get access token
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        
        login_response = client.post("/auth/login", json=login_data)
        login_data = login_response.json()
        access_token = login_data["data"]["access_token"]
        
        # Now test logout
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.post("/auth/logout", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Logged out successfully" in data["message"]
    
    def test_get_current_user_info(self, client, sample_user_data, sample_user):
        """Test getting current user information."""
        # First login to get access token
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        
        login_response = client.post("/auth/login", json=login_data)
        login_data = login_response.json()
        access_token = login_data["data"]["access_token"]
        
        # Now test getting user info
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["first_name"] == sample_user_data["first_name"]
        assert data["last_name"] == sample_user_data["last_name"]
        assert data["role"] == sample_user_data["role"]
    
    def test_get_current_user_info_no_auth(self, client):
        """Test getting current user info without authentication."""
        response = client.get("/auth/me")
        
        assert response.status_code == 401
        data = response.json()
        assert "Not authenticated" in data["detail"] 