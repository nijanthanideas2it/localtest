"""
Unit tests for authentication functionality.
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.auth import AuthUtils, add_to_blacklist, is_token_blacklisted
from app.models.user import User
from app.schemas.auth import UserLoginRequest, UserRegisterRequest


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Mock database session fixture."""
    session = MagicMock(spec=Session)
    wrapper = MagicMock()
    wrapper.session = session
    wrapper.commit = AsyncMock()
    wrapper.rollback = AsyncMock()
    wrapper.refresh = AsyncMock()
    return wrapper


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
def sample_user(sample_user_data):
    """Sample user object for testing."""
    user = User(
        id="123e4567-e89b-12d3-a456-426614174000",
        email=sample_user_data["email"],
        first_name=sample_user_data["first_name"],
        last_name=sample_user_data["last_name"],
        password_hash=AuthUtils.get_password_hash(sample_user_data["password"]),
        role=sample_user_data["role"],
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    return user


class TestAuthUtils:
    """Test cases for AuthUtils class."""
    
    def test_verify_password_valid(self):
        """Test password verification with valid password."""
        password = "TestPass123!"
        hashed = AuthUtils.get_password_hash(password)
        assert AuthUtils.verify_password(password, hashed) is True
    
    def test_verify_password_invalid(self):
        """Test password verification with invalid password."""
        password = "TestPass123!"
        wrong_password = "WrongPass123!"
        hashed = AuthUtils.get_password_hash(password)
        assert AuthUtils.verify_password(wrong_password, hashed) is False
    
    def test_get_password_hash(self):
        """Test password hashing."""
        password = "TestPass123!"
        hashed = AuthUtils.get_password_hash(password)
        assert hashed != password
        assert len(hashed) > len(password)
    
    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "123", "email": "test@example.com"}
        token = AuthUtils.create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        data = {"sub": "123", "email": "test@example.com"}
        token = AuthUtils.create_refresh_token(data)
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token_valid(self):
        """Test token verification with valid token."""
        data = {"sub": "123", "email": "test@example.com"}
        token = AuthUtils.create_access_token(data)
        payload = AuthUtils.verify_token(token, "access")
        assert payload["sub"] == "123"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"
    
    def test_verify_token_invalid_type(self):
        """Test token verification with wrong token type."""
        data = {"sub": "123", "email": "test@example.com"}
        token = AuthUtils.create_access_token(data)
        with pytest.raises(Exception):
            AuthUtils.verify_token(token, "refresh")
    
    def test_verify_token_expired(self):
        """Test token verification with expired token."""
        data = {"sub": "123", "email": "test@example.com"}
        # Create token with very short expiration
        token = AuthUtils.create_access_token(data, timedelta(seconds=-1))
        with pytest.raises(Exception):
            AuthUtils.verify_token(token, "access")
    
    def test_verify_token_invalid(self):
        """Test token verification with invalid token."""
        with pytest.raises(Exception):
            AuthUtils.verify_token("invalid_token", "access")
    
    def test_validate_password_strength_valid(self):
        """Test password strength validation with valid password."""
        valid_passwords = [
            "TestPass123!",
            "MySecureP@ss1",
            "Complex#Pass2",
            "Strong$Pass3"
        ]
        for password in valid_passwords:
            assert AuthUtils.validate_password_strength(password) is True
    
    def test_validate_password_strength_invalid(self):
        """Test password strength validation with invalid passwords."""
        invalid_passwords = [
            "short",  # Too short
            "nouppercase123!",  # No uppercase
            "NOLOWERCASE123!",  # No lowercase
            "NoNumbers!",  # No numbers
            "NoSpecial123",  # No special characters
            "onlylowercase",  # Only lowercase
            "ONLYUPPERCASE",  # Only uppercase
            "123456789",  # Only numbers
        ]
        for password in invalid_passwords:
            assert AuthUtils.validate_password_strength(password) is False


class TestTokenBlacklist:
    """Test cases for token blacklist functionality."""
    
    def test_add_to_blacklist(self):
        """Test adding token to blacklist."""
        token = "test_token_123"
        add_to_blacklist(token)
        assert is_token_blacklisted(token) is True
    
    def test_is_token_blacklisted_false(self):
        """Test checking non-blacklisted token."""
        token = "non_blacklisted_token"
        assert is_token_blacklisted(token) is False


class TestAuthEndpoints:
    """Test cases for authentication API endpoints."""
    
    @patch('app.api.auth.get_db')
    def test_register_success(self, mock_get_db, client, sample_user_data, mock_db_session):
        """Test successful user registration."""
        # Mock database session
        mock_get_db.return_value = iter([mock_db_session])
        mock_db_session.session.query.return_value.filter.return_value.first.return_value = None
        mock_db_session.session.add.return_value = None
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.return_value = None
        
        response = client.post("/auth/register", json=sample_user_data)
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == sample_user_data["email"]
        assert data["data"]["first_name"] == sample_user_data["first_name"]
        assert data["data"]["last_name"] == sample_user_data["last_name"]
        assert data["data"]["role"] == sample_user_data["role"]
    
    @patch('app.api.auth.get_db')
    def test_register_email_exists(self, mock_get_db, client, sample_user_data, mock_db_session, sample_user):
        """Test registration with existing email."""
        # Mock database session to return existing user
        mock_get_db.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_user
        
        response = client.post("/auth/register", json=sample_user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "Email already registered" in data["detail"]
    
    @patch('app.api.auth.get_db')
    def test_register_weak_password(self, mock_get_db, client, mock_db_session):
        """Test registration with weak password."""
        # Mock database session
        mock_get_db.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        weak_password_data = {
            "email": "test@example.com",
            "password": "weak",
            "first_name": "Test",
            "last_name": "User",
            "role": "Developer"
        }
        
        response = client.post("/auth/register", json=weak_password_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "Password does not meet security requirements" in data["detail"]
    
    @patch('app.api.auth.get_db')
    def test_login_success(self, mock_get_db, client, sample_user_data, sample_user, mock_db_session):
        """Test successful user login."""
        # Mock database session
        mock_get_db.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_user
        mock_db_session.commit.return_value = None
        
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
    
    @patch('app.api.auth.get_db')
    def test_login_invalid_credentials(self, mock_get_db, client, mock_db_session):
        """Test login with invalid credentials."""
        # Mock database session to return None (user not found)
        mock_get_db.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "Incorrect email or password" in data["detail"]
    
    @patch('app.api.auth.get_db')
    def test_login_inactive_user(self, mock_get_db, client, sample_user_data, mock_db_session):
        """Test login with inactive user."""
        # Create inactive user
        inactive_user = User(
            id="123e4567-e89b-12d3-a456-426614174000",
            email=sample_user_data["email"],
            first_name=sample_user_data["first_name"],
            last_name=sample_user_data["last_name"],
            password_hash=AuthUtils.get_password_hash(sample_user_data["password"]),
            role=sample_user_data["role"],
            is_active=False,
            created_at=datetime.now(timezone.utc)
        )
        
        # Mock database session
        mock_get_db.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = inactive_user
        
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "User account is inactive" in data["detail"]
    
    @patch('app.api.auth.get_db')
    def test_refresh_token_success(self, mock_get_db, client, sample_user, mock_db_session):
        """Test successful token refresh."""
        # Create refresh token
        refresh_token = AuthUtils.create_refresh_token({
            "sub": str(sample_user.id),
            "email": sample_user.email
        })
        
        # Mock database session
        mock_get_db.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_user
        
        refresh_data = {"refresh_token": refresh_token}
        
        response = client.post("/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"
    
    @patch('app.api.auth.get_db')
    def test_refresh_token_invalid(self, mock_get_db, client, mock_db_session):
        """Test token refresh with invalid token."""
        # Mock database session
        mock_get_db.return_value = mock_db_session
        
        refresh_data = {"refresh_token": "invalid_token"}
        
        response = client.post("/auth/refresh", json=refresh_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "Could not validate credentials" in data["detail"]
    
    @patch('app.api.auth.get_db')
    def test_logout_success(self, mock_get_db, client, sample_user, mock_db_session):
        """Test successful logout."""
        # Create access token
        access_token = AuthUtils.create_access_token({
            "sub": str(sample_user.id),
            "email": sample_user.email,
            "role": sample_user.role
        })
        
        # Mock database session
        mock_get_db.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_user
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.post("/auth/logout", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Logged out successfully" in data["message"]
        
        # Verify token is blacklisted
        assert is_token_blacklisted(access_token) is True
    
    @patch('app.api.auth.get_db')
    def test_get_current_user_info(self, mock_get_db, client, sample_user, mock_db_session):
        """Test getting current user information."""
        # Create access token
        access_token = AuthUtils.create_access_token({
            "sub": str(sample_user.id),
            "email": sample_user.email,
            "role": sample_user.role
        })
        
        # Mock database session
        mock_get_db.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_user
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == sample_user.email
        assert data["first_name"] == sample_user.first_name
        assert data["last_name"] == sample_user.last_name
        assert data["role"] == sample_user.role
    
    def test_get_current_user_info_no_auth(self, client):
        """Test getting current user info without authentication."""
        response = client.get("/auth/me")
        
        assert response.status_code == 401
        data = response.json()
        assert "Not authenticated" in data["detail"]


class TestAuthSchemas:
    """Test cases for authentication schemas."""
    
    def test_user_login_request_valid(self):
        """Test valid user login request."""
        data = {
            "email": "test@example.com",
            "password": "TestPass123!"
        }
        request = UserLoginRequest(**data)
        assert request.email == data["email"]
        assert request.password == data["password"]
    
    def test_user_register_request_valid(self):
        """Test valid user register request."""
        data = {
            "email": "test@example.com",
            "password": "TestPass123!",
            "first_name": "Test",
            "last_name": "User",
            "role": "Developer"
        }
        request = UserRegisterRequest(**data)
        assert request.email == data["email"]
        assert request.password == data["password"]
        assert request.first_name == data["first_name"]
        assert request.last_name == data["last_name"]
        assert request.role == data["role"]
    
    def test_user_register_request_invalid_role(self):
        """Test user register request with invalid role."""
        data = {
            "email": "test@example.com",
            "password": "TestPass123!",
            "first_name": "Test",
            "last_name": "User",
            "role": "InvalidRole"
        }
        with pytest.raises(ValueError):
            UserRegisterRequest(**data)
    
    def test_user_register_request_default_role(self):
        """Test user register request with default role."""
        data = {
            "email": "test@example.com",
            "password": "TestPass123!",
            "first_name": "Test",
            "last_name": "User"
        }
        request = UserRegisterRequest(**data)
        assert request.role == "Developer"  # Default role 