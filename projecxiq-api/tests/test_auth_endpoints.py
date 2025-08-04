"""
Integration tests for enhanced authentication endpoints.
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.auth import AuthUtils
from app.core.security import SecurityUtils
from app.models.user import User
from app.db.database import get_db


class TestEnhancedAuthEndpoints:
    """Test cases for enhanced authentication endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        from unittest.mock import AsyncMock
        
        # Create a mock that mimics AsyncSessionWrapper
        mock_session = MagicMock()
        mock_session.session = MagicMock()
        mock_session.session.query.return_value.filter.return_value.first.return_value = None
        mock_session.session.add.return_value = None
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.rollback = AsyncMock()
        return mock_session
    
    @pytest.fixture
    def sample_user(self):
        """Create a sample user for testing."""
        return User(
            id="test-user-id",
            email="test@example.com",
            password_hash=AuthUtils.get_password_hash("SecurePass123!"),
            first_name="Test",
            last_name="User",
            role="Developer",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            last_login_at=datetime.now(timezone.utc)
        )
    
    def test_forgot_password_success(self, client, mock_db_session, sample_user):
        """Test successful forgot password request."""
        with patch('app.api.auth.get_db', return_value=mock_db_session):
            mock_db_session.session.query.return_value.filter.return_value.first.return_value = sample_user
            
            response = client.post("/auth/forgot-password", json={
                "email": "test@example.com"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "Password reset email sent" in data["message"]
    
    def test_forgot_password_user_not_found(self, client, mock_db_session):
        """Test forgot password with non-existent user."""
        with patch('app.api.auth.get_db', return_value=mock_db_session):
            mock_db_session.session.query.return_value.filter.return_value.first.return_value = None
            
            response = client.post("/auth/forgot-password", json={
                "email": "nonexistent@example.com"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "If the email exists" in data["message"]
    
    def test_reset_password_success(self, client, mock_db_session, sample_user):
        """Test successful password reset."""
        with patch('app.api.auth.get_db', return_value=mock_db_session):
            # Mock the password reset tokens
            from app.api.auth import password_reset_tokens
            reset_token = SecurityUtils.generate_verification_token()
            password_reset_tokens[reset_token] = (
                str(sample_user.id),
                datetime.now(timezone.utc) + timedelta(hours=1)
            )
            
            mock_db_session.session.query.return_value.filter.return_value.first.return_value = sample_user
            
            response = client.post("/auth/reset-password", json={
                "token": reset_token,
                "new_password": "NewSecurePass456!"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Password reset successfully"
    
    def test_reset_password_invalid_token(self, client, mock_db_session):
        """Test password reset with invalid token."""
        with patch('app.api.auth.get_db', return_value=mock_db_session):
            response = client.post("/auth/reset-password", json={
                "token": "invalid-token",
                "new_password": "NewSecurePass456!"
            })
            
            assert response.status_code == 400
            data = response.json()
            assert "Invalid or expired reset token" in data["detail"]
    
    def test_reset_password_weak_password(self, client, mock_db_session, sample_user):
        """Test password reset with weak password."""
        with patch('app.api.auth.get_db', return_value=mock_db_session):
            # Mock the password reset tokens
            from app.api.auth import password_reset_tokens
            reset_token = SecurityUtils.generate_verification_token()
            password_reset_tokens[reset_token] = (
                str(sample_user.id),
                datetime.now(timezone.utc) + timedelta(hours=1)
            )
            
            mock_db_session.session.query.return_value.filter.return_value.first.return_value = sample_user
            
            response = client.post("/auth/reset-password", json={
                "token": reset_token,
                "new_password": "weak"
            })
            
            assert response.status_code == 400
            data = response.json()
            assert "Password does not meet security requirements" in data["detail"]
    
    def test_change_password_success(self, client, mock_db_session, sample_user):
        """Test successful password change."""
        with patch('app.api.auth.get_db', return_value=mock_db_session):
            mock_db_session.session.query.return_value.filter.return_value.first.return_value = sample_user
            
            # Mock authentication
            with patch('app.api.auth.get_current_user', return_value=sample_user):
                response = client.post("/auth/change-password", 
                    headers={"Authorization": "Bearer test-token"},
                    json={
                        "current_password": "SecurePass123!",
                        "new_password": "NewSecurePass456!"
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["message"] == "Password changed successfully"
    
    def test_change_password_incorrect_current(self, client, mock_db_session, sample_user):
        """Test password change with incorrect current password."""
        with patch('app.api.auth.get_db', return_value=mock_db_session):
            mock_db_session.session.query.return_value.filter.return_value.first.return_value = sample_user
            
            # Mock authentication
            with patch('app.api.auth.get_current_user', return_value=sample_user):
                response = client.post("/auth/change-password", 
                    headers={"Authorization": "Bearer test-token"},
                    json={
                        "current_password": "WrongPassword123!",
                        "new_password": "NewSecurePass456!"
                    }
                )
                
                assert response.status_code == 400
                data = response.json()
                assert "Current password is incorrect" in data["detail"]
    
    def test_verify_email_success(self, client, mock_db_session, sample_user):
        """Test successful email verification."""
        with patch('app.api.auth.get_db', return_value=mock_db_session):
            # Mock the email verification tokens
            from app.api.auth import email_verification_tokens
            verification_token = SecurityUtils.generate_verification_token()
            email_verification_tokens[verification_token] = (
                str(sample_user.id),
                datetime.now(timezone.utc) + timedelta(hours=24)
            )
            
            mock_db_session.session.query.return_value.filter.return_value.first.return_value = sample_user
            
            response = client.post("/auth/verify-email", json={
                "token": verification_token
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Email verified successfully"
    
    def test_verify_email_invalid_token(self, client, mock_db_session):
        """Test email verification with invalid token."""
        with patch('app.api.auth.get_db', return_value=mock_db_session):
            response = client.post("/auth/verify-email", json={
                "token": "invalid-token"
            })
            
            assert response.status_code == 400
            data = response.json()
            assert "Invalid or expired verification token" in data["detail"]
    
    def test_resend_verification_success(self, client, mock_db_session, sample_user):
        """Test successful resend verification."""
        with patch('app.api.auth.get_db', return_value=mock_db_session):
            mock_db_session.session.query.return_value.filter.return_value.first.return_value = sample_user
            
            response = client.post("/auth/resend-verification", json={
                "email": "test@example.com"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "Verification email sent" in data["message"]
    
    def test_resend_verification_user_not_found(self, client, mock_db_session):
        """Test resend verification with non-existent user."""
        with patch('app.api.auth.get_db', return_value=mock_db_session):
            mock_db_session.session.query.return_value.filter.return_value.first.return_value = None
            
            response = client.post("/auth/resend-verification", json={
                "email": "nonexistent@example.com"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "If the email exists" in data["message"]
    
    def test_get_user_sessions_success(self, client, mock_db_session, sample_user):
        """Test successful get user sessions."""
        with patch('app.api.auth.get_db', return_value=mock_db_session):
            # Mock user sessions
            from app.api.auth import user_sessions
            session_info = {
                "session_id": "test-session-id",
                "created_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "ip_address": "127.0.0.1",
                "user_agent": "test-agent",
                "is_current": True
            }
            user_sessions[str(sample_user.id)] = [session_info]
            
            # Mock authentication
            with patch('app.api.auth.get_current_user', return_value=sample_user):
                response = client.get("/auth/sessions",
                    headers={"Authorization": "Bearer test-token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert len(data["data"]) == 1
                assert data["data"][0]["session_id"] == "test-session-id"
    
    def test_get_user_sessions_no_sessions(self, client, mock_db_session, sample_user):
        """Test get user sessions when no sessions exist."""
        with patch('app.api.auth.get_db', return_value=mock_db_session):
            # Mock authentication
            with patch('app.api.auth.get_current_user', return_value=sample_user):
                response = client.get("/auth/sessions",
                    headers={"Authorization": "Bearer test-token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert len(data["data"]) == 0
    
    def test_revoke_session_success(self, client, mock_db_session, sample_user):
        """Test successful session revocation."""
        with patch('app.api.auth.get_db', return_value=mock_db_session):
            # Mock user sessions
            from app.api.auth import user_sessions
            session_info = {
                "session_id": "test-session-id",
                "created_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "ip_address": "127.0.0.1",
                "user_agent": "test-agent",
                "is_current": False
            }
            user_sessions[str(sample_user.id)] = [session_info]
            
            # Mock authentication
            with patch('app.api.auth.get_current_user', return_value=sample_user):
                response = client.delete("/auth/sessions/test-session-id",
                    headers={"Authorization": "Bearer test-token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["message"] == "Session revoked successfully"
    
    def test_revoke_session_not_found(self, client, mock_db_session, sample_user):
        """Test session revocation with non-existent session."""
        with patch('app.api.auth.get_db', return_value=mock_db_session):
            # Mock authentication
            with patch('app.api.auth.get_current_user', return_value=sample_user):
                response = client.delete("/auth/sessions/non-existent-session",
                    headers={"Authorization": "Bearer test-token"}
                )
                
                assert response.status_code == 404
                data = response.json()
                assert "Session not found" in data["detail"]
    
    def test_register_with_email_verification(self, client, mock_db_session):
        """Test user registration with email verification."""
        with patch('app.api.auth.get_db', return_value=mock_db_session):
            mock_db_session.session.query.return_value.filter.return_value.first.return_value = None
            
            response = client.post("/auth/register", json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "first_name": "New",
                "last_name": "User",
                "role": "Developer"
            })
            
            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert "verification_token" in data["data"]
            assert "Please check your email for verification" in data["message"]
    
    def test_login_with_session_tracking(self, client, mock_db_session, sample_user):
        """Test login with session tracking."""
        with patch('app.api.auth.get_db', return_value=mock_db_session):
            mock_db_session.session.query.return_value.filter.return_value.first.return_value = sample_user
            
            response = client.post("/auth/login", json={
                "email": "test@example.com",
                "password": "SecurePass123!"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "access_token" in data["data"]
            assert "refresh_token" in data["data"]
    
    def test_logout_with_session_cleanup(self, client, mock_db_session, sample_user):
        """Test logout with session cleanup."""
        with patch('app.api.auth.get_db', return_value=mock_db_session):
            # Mock user sessions
            from app.api.auth import user_sessions
            session_info = {
                "session_id": "test-session-id",
                "created_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "ip_address": "127.0.0.1",
                "user_agent": "test-agent",
                "is_current": True
            }
            user_sessions[str(sample_user.id)] = [session_info]
            
            # Mock authentication
            with patch('app.api.auth.get_current_user', return_value=sample_user):
                response = client.post("/auth/logout",
                    headers={"Authorization": "Bearer test-token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["message"] == "Logout successful"
    
    def test_password_reset_token_expiry(self, client, mock_db_session, sample_user):
        """Test password reset with expired token."""
        with patch('app.api.auth.get_db', return_value=mock_db_session):
            # Mock the password reset tokens with expired token
            from app.api.auth import password_reset_tokens
            reset_token = SecurityUtils.generate_verification_token()
            password_reset_tokens[reset_token] = (
                str(sample_user.id),
                datetime.now(timezone.utc) - timedelta(hours=1)  # Expired
            )
            
            response = client.post("/auth/reset-password", json={
                "token": reset_token,
                "new_password": "NewSecurePass456!"
            })
            
            assert response.status_code == 400
            data = response.json()
            assert "Reset token has expired" in data["detail"]
    
    def test_email_verification_token_expiry(self, client, mock_db_session, sample_user):
        """Test email verification with expired token."""
        with patch('app.api.auth.get_db', return_value=mock_db_session):
            # Mock the email verification tokens with expired token
            from app.api.auth import email_verification_tokens
            verification_token = SecurityUtils.generate_verification_token()
            email_verification_tokens[verification_token] = (
                str(sample_user.id),
                datetime.now(timezone.utc) - timedelta(hours=1)  # Expired
            )
            
            response = client.post("/auth/verify-email", json={
                "token": verification_token
            })
            
            assert response.status_code == 400
            data = response.json()
            assert "Verification token has expired" in data["detail"] 