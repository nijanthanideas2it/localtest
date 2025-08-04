"""
Unit tests for user service layer.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.services.user_service import UserService
from app.schemas.user import UserCreateRequest, UserUpdateRequest, UserQueryParams
from app.models.user import User
from app.models.user import UserSkill
from app.core.auth import AuthUtils


class TestUserService:
    """Test cases for UserService class."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def sample_user_data(self):
        """Sample user creation data."""
        return UserCreateRequest(
            email="test@example.com",
            password="SecurePass123!",
            first_name="Test",
            last_name="User",
            role="Developer",
            hourly_rate=50.0,
            is_active=True
        )
    
    @pytest.fixture
    def sample_user(self):
        """Sample user object."""
        return User(
            id="test-user-id",
            email="test@example.com",
            password_hash=AuthUtils.get_password_hash("SecurePass123!"),
            first_name="Test",
            last_name="User",
            role="Developer",
            hourly_rate=50.0,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
    
    def test_create_user_success(self, mock_db_session, sample_user_data):
        """Test successful user creation."""
        # Mock database query to return no existing user
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Mock password validation
        with patch('app.services.user_service.AuthUtils.validate_password_strength', return_value=True):
            with patch('app.services.user_service.AuthUtils.get_password_hash', return_value="hashed_password"):
                result = UserService.create_user(mock_db_session, sample_user_data)
        
        assert result is not None
        assert result.email == sample_user_data.email
        assert result.first_name == sample_user_data.first_name
        assert result.last_name == sample_user_data.last_name
        assert result.role == sample_user_data.role
        assert result.hourly_rate == sample_user_data.hourly_rate
        assert result.is_active == sample_user_data.is_active
        
        # Verify database operations
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    def test_create_user_email_exists(self, mock_db_session, sample_user_data):
        """Test user creation with existing email."""
        # Mock database query to return existing user
        mock_db_session.query.return_value.filter.return_value.first.return_value = User()
        
        with pytest.raises(ValueError, match="Email already registered"):
            UserService.create_user(mock_db_session, sample_user_data)
    
    def test_create_user_weak_password(self, mock_db_session, sample_user_data):
        """Test user creation with weak password."""
        # Mock database query to return no existing user
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Mock password validation to fail
        with patch('app.services.user_service.AuthUtils.validate_password_strength', return_value=False):
            with pytest.raises(ValueError, match="Password does not meet security requirements"):
                UserService.create_user(mock_db_session, sample_user_data)
    
    def test_get_user_by_id_found(self, mock_db_session, sample_user):
        """Test getting user by ID when found."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_user
        
        result = UserService.get_user_by_id(mock_db_session, "test-user-id")
        
        assert result == sample_user
    
    def test_get_user_by_id_not_found(self, mock_db_session):
        """Test getting user by ID when not found."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = UserService.get_user_by_id(mock_db_session, "non-existent-id")
        
        assert result is None
    
    def test_get_users_with_pagination_no_filters(self, mock_db_session):
        """Test getting users with pagination and no filters."""
        # Mock users
        users = [
            User(id=f"user-{i}", email=f"user{i}@example.com", first_name=f"User{i}")
            for i in range(5)
        ]
        
        # Mock query chain
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.offset.return_value.limit.return_value.all.return_value = users
        mock_db_session.query.return_value = mock_query
        
        query_params = UserQueryParams(page=1, limit=10)
        result_users, total_count = UserService.get_users_with_pagination(mock_db_session, query_params)
        
        assert result_users == users
        assert total_count == 5
    
    def test_get_users_with_role_filter(self, mock_db_session):
        """Test getting users with role filter."""
        # Mock users
        users = [
            User(id="user-1", email="user1@example.com", role="Developer")
        ]
        
        # Mock query chain
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.offset.return_value.limit.return_value.all.return_value = users
        mock_db_session.query.return_value = mock_query
        
        query_params = UserQueryParams(page=1, limit=10, role="Developer")
        result_users, total_count = UserService.get_users_with_pagination(mock_db_session, query_params)
        
        assert result_users == users
        assert total_count == 1
    
    def test_get_users_with_search_filter(self, mock_db_session):
        """Test getting users with search filter."""
        # Mock users
        users = [
            User(id="user-1", email="john@example.com", first_name="John")
        ]
        
        # Mock query chain
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.offset.return_value.limit.return_value.all.return_value = users
        mock_db_session.query.return_value = mock_query
        
        query_params = UserQueryParams(page=1, limit=10, search="john")
        result_users, total_count = UserService.get_users_with_pagination(mock_db_session, query_params)
        
        assert result_users == users
        assert total_count == 1
    
    def test_update_user_success(self, mock_db_session, sample_user):
        """Test successful user update."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_user
        
        update_data = UserUpdateRequest(
            first_name="Updated",
            last_name="Name",
            hourly_rate=75.0
        )
        
        result = UserService.update_user(mock_db_session, "test-user-id", update_data)
        
        assert result == sample_user
        assert sample_user.first_name == "Updated"
        assert sample_user.last_name == "Name"
        assert sample_user.hourly_rate == 75.0
        assert sample_user.updated_at is not None
        
        # Verify database operations
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    def test_update_user_not_found(self, mock_db_session):
        """Test user update when user not found."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        update_data = UserUpdateRequest(first_name="Updated")
        
        result = UserService.update_user(mock_db_session, "non-existent-id", update_data)
        
        assert result is None
    
    def test_delete_user_success(self, mock_db_session, sample_user):
        """Test successful user deletion."""
        sample_user.role = "Developer"  # Not admin
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_user
        mock_db_session.query.return_value.filter.return_value.count.return_value = 2  # Multiple admins
        
        result = UserService.delete_user(mock_db_session, "test-user-id")
        
        assert result is True
        mock_db_session.delete.assert_called_once_with(sample_user)
        mock_db_session.commit.assert_called_once()
    
    def test_delete_user_not_found(self, mock_db_session):
        """Test user deletion when user not found."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = UserService.delete_user(mock_db_session, "non-existent-id")
        
        assert result is False
    
    def test_delete_last_admin_fails(self, mock_db_session, sample_user):
        """Test that deleting the last admin fails."""
        sample_user.role = "Admin"
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_user
        mock_db_session.query.return_value.filter.return_value.count.return_value = 1  # Only one admin
        
        with pytest.raises(ValueError, match="Cannot delete the last admin user"):
            UserService.delete_user(mock_db_session, "test-user-id")
    
    def test_add_user_skill_success(self, mock_db_session, sample_user):
        """Test successful skill addition."""
        # Mock user query to return sample user
        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.first.return_value = sample_user
        
        # Mock skill query to return no existing skill
        mock_skill_query = MagicMock()
        mock_skill_query.filter.return_value.first.return_value = None
        
        # Set up mock_db_session.query to return different mocks for different calls
        mock_db_session.query.side_effect = [mock_user_query, mock_skill_query]
        
        result = UserService.add_user_skill(
            mock_db_session, 
            "test-user-id", 
            "Python", 
            "Advanced"
        )
        
        assert result is not None
        assert result.skill_name == "Python"
        assert result.proficiency_level == "Advanced"
        assert result.user_id == "test-user-id"
        
        # Verify database operations
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    def test_add_user_skill_user_not_found(self, mock_db_session):
        """Test skill addition when user not found."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = UserService.add_user_skill(
            mock_db_session, 
            "non-existent-id", 
            "Python", 
            "Advanced"
        )
        
        assert result is None
    
    def test_add_user_skill_already_exists(self, mock_db_session, sample_user):
        """Test skill addition when skill already exists."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_user
        
        # Mock skill query to return existing skill
        existing_skill = UserSkill(skill_name="Python", proficiency_level="Intermediate")
        mock_skill_query = MagicMock()
        mock_skill_query.filter.return_value.first.return_value = existing_skill
        mock_db_session.query.return_value = mock_skill_query
        
        with pytest.raises(ValueError, match="Skill already exists for this user"):
            UserService.add_user_skill(
                mock_db_session, 
                "test-user-id", 
                "Python", 
                "Advanced"
            )
    
    def test_update_user_skill_success(self, mock_db_session):
        """Test successful skill update."""
        existing_skill = UserSkill(
            id="skill-1",
            user_id="test-user-id",
            skill_name="Python",
            proficiency_level="Intermediate"
        )
        
        # Mock skill queries
        mock_skill_query1 = MagicMock()
        mock_skill_query1.filter.return_value.first.return_value = existing_skill
        
        mock_skill_query2 = MagicMock()
        mock_skill_query2.filter.return_value.first.return_value = None  # No duplicate skill
        
        # Set up mock_db_session.query to return different mocks for different calls
        mock_db_session.query.side_effect = [mock_skill_query1, mock_skill_query2]
        
        result = UserService.update_user_skill(
            mock_db_session, 
            "test-user-id", 
            "skill-1", 
            "Python", 
            "Expert"
        )
        
        assert result == existing_skill
        assert existing_skill.proficiency_level == "Expert"
        assert existing_skill.updated_at is not None
        
        # Verify database operations
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    def test_update_user_skill_not_found(self, mock_db_session):
        """Test skill update when skill not found."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = UserService.update_user_skill(
            mock_db_session, 
            "test-user-id", 
            "non-existent-skill", 
            "Python", 
            "Expert"
        )
        
        assert result is None
    
    def test_delete_user_skill_success(self, mock_db_session):
        """Test successful skill deletion."""
        existing_skill = UserSkill(
            id="skill-1",
            user_id="test-user-id",
            skill_name="Python"
        )
        
        # Mock skill query to return existing skill
        mock_skill_query = MagicMock()
        mock_skill_query.filter.return_value.first.return_value = existing_skill
        mock_db_session.query.return_value = mock_skill_query
        
        result = UserService.delete_user_skill(mock_db_session, "test-user-id", "skill-1")
        
        assert result is True
        mock_db_session.delete.assert_called_once_with(existing_skill)
        mock_db_session.commit.assert_called_once()
    
    def test_delete_user_skill_not_found(self, mock_db_session):
        """Test skill deletion when skill not found."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = UserService.delete_user_skill(mock_db_session, "test-user-id", "non-existent-skill")
        
        assert result is False
    
    def test_get_user_skills(self, mock_db_session):
        """Test getting user skills."""
        skills = [
            UserSkill(id="skill-1", skill_name="Python", proficiency_level="Advanced"),
            UserSkill(id="skill-2", skill_name="JavaScript", proficiency_level="Intermediate")
        ]
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = skills
        
        result = UserService.get_user_skills(mock_db_session, "test-user-id")
        
        assert result == skills
    
    def test_calculate_pagination_info(self):
        """Test pagination info calculation."""
        # Test with exact division
        pagination = UserService.calculate_pagination_info(100, 1, 20)
        assert pagination["page"] == 1
        assert pagination["limit"] == 20
        assert pagination["total"] == 100
        assert pagination["pages"] == 5
        
        # Test with remainder
        pagination = UserService.calculate_pagination_info(101, 1, 20)
        assert pagination["pages"] == 6
        
        # Test with zero total
        pagination = UserService.calculate_pagination_info(0, 1, 20)
        assert pagination["pages"] == 0 