"""
Unit tests for skills service layer.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.services.user_service import UserService
from app.schemas.skills import SkillRequest
from app.models.user import User, UserSkill
from app.core.auth import AuthUtils


class TestSkillsService:
    """Test cases for skills service functionality."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return MagicMock()
    
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
    
    @pytest.fixture
    def sample_skill_data(self):
        """Sample skill request data."""
        return SkillRequest(
            skill_name="Python",
            proficiency_level="Advanced"
        )
    
    @pytest.fixture
    def sample_user_skill(self):
        """Sample user skill object."""
        return UserSkill(
            id="skill-1",
            user_id="test-user-id",
            skill_name="Python",
            proficiency_level="Advanced",
            created_at=datetime.now(timezone.utc)
        )
    
    def test_get_user_skills_success(self, mock_db_session, sample_user_skill):
        """Test successful retrieval of user skills."""
        # Mock skills query
        mock_skills = [sample_user_skill]
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_skills
        
        result = UserService.get_user_skills(mock_db_session, "test-user-id")
        
        assert result == mock_skills
        mock_db_session.query.assert_called_once()
    
    def test_get_user_skills_empty(self, mock_db_session):
        """Test retrieval of user skills when user has no skills."""
        # Mock empty skills query
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        result = UserService.get_user_skills(mock_db_session, "test-user-id")
        
        assert result == []
        mock_db_session.query.assert_called_once()
    
    def test_add_user_skill_success(self, mock_db_session, sample_user, sample_skill_data):
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
            sample_skill_data.skill_name, 
            sample_skill_data.proficiency_level
        )
        
        assert result is not None
        assert result.skill_name == "Python"
        assert result.proficiency_level == "Advanced"
        assert result.user_id == "test-user-id"
        
        # Verify database operations
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    def test_add_user_skill_user_not_found(self, mock_db_session, sample_skill_data):
        """Test skill addition when user not found."""
        # Mock user query to return None
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = UserService.add_user_skill(
            mock_db_session, 
            "non-existent-id", 
            sample_skill_data.skill_name, 
            sample_skill_data.proficiency_level
        )
        
        assert result is None
    
    def test_add_user_skill_already_exists(self, mock_db_session, sample_user, sample_skill_data):
        """Test skill addition when skill already exists."""
        # Mock user query to return sample user
        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.first.return_value = sample_user
        
        # Mock skill query to return existing skill
        existing_skill = UserSkill(skill_name="Python", proficiency_level="Intermediate")
        mock_skill_query = MagicMock()
        mock_skill_query.filter.return_value.first.return_value = existing_skill
        
        # Set up mock_db_session.query to return different mocks for different calls
        mock_db_session.query.side_effect = [mock_user_query, mock_skill_query]
        
        with pytest.raises(ValueError, match="Skill already exists for this user"):
            UserService.add_user_skill(
                mock_db_session, 
                "test-user-id", 
                sample_skill_data.skill_name, 
                sample_skill_data.proficiency_level
            )
    
    def test_update_user_skill_success(self, mock_db_session, sample_user_skill):
        """Test successful skill update."""
        # Mock skill queries
        mock_skill_query1 = MagicMock()
        mock_skill_query1.filter.return_value.first.return_value = sample_user_skill
        
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
        
        assert result == sample_user_skill
        assert sample_user_skill.proficiency_level == "Expert"
        assert sample_user_skill.updated_at is not None
        
        # Verify database operations
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    def test_update_user_skill_not_found(self, mock_db_session):
        """Test skill update when skill not found."""
        # Mock skill query to return None
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = UserService.update_user_skill(
            mock_db_session, 
            "test-user-id", 
            "non-existent-skill", 
            "Python", 
            "Expert"
        )
        
        assert result is None
    
    def test_update_user_skill_duplicate_name(self, mock_db_session, sample_user_skill):
        """Test skill update with duplicate skill name."""
        # Mock skill queries
        mock_skill_query1 = MagicMock()
        mock_skill_query1.filter.return_value.first.return_value = sample_user_skill
        
        # Mock duplicate skill query to return existing skill
        existing_skill = UserSkill(skill_name="Python", proficiency_level="Intermediate")
        mock_skill_query2 = MagicMock()
        mock_skill_query2.filter.return_value.first.return_value = existing_skill
        
        # Set up mock_db_session.query to return different mocks for different calls
        mock_db_session.query.side_effect = [mock_skill_query1, mock_skill_query2]
        
        with pytest.raises(ValueError, match="Skill already exists for this user"):
            UserService.update_user_skill(
                mock_db_session, 
                "test-user-id", 
                "skill-1", 
                "Python", 
                "Expert"
            )
    
    def test_delete_user_skill_success(self, mock_db_session, sample_user_skill):
        """Test successful skill deletion."""
        # Mock skill query to return existing skill
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_user_skill
        
        result = UserService.delete_user_skill(mock_db_session, "test-user-id", "skill-1")
        
        assert result is True
        mock_db_session.delete.assert_called_once_with(sample_user_skill)
        mock_db_session.commit.assert_called_once()
    
    def test_delete_user_skill_not_found(self, mock_db_session):
        """Test skill deletion when skill not found."""
        # Mock skill query to return None
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = UserService.delete_user_skill(mock_db_session, "test-user-id", "non-existent-skill")
        
        assert result is False


class TestSkillsValidation:
    """Test cases for skills validation."""
    
    def test_skill_request_valid(self):
        """Test valid skill request."""
        skill_data = SkillRequest(
            skill_name="Python",
            proficiency_level="Advanced"
        )
        
        assert skill_data.skill_name == "Python"
        assert skill_data.proficiency_level == "Advanced"
    
    def test_skill_request_invalid_proficiency_level(self):
        """Test skill request with invalid proficiency level."""
        with pytest.raises(ValueError, match="Proficiency level must be one of"):
            SkillRequest(
                skill_name="Python",
                proficiency_level="Invalid"
            )
    
    def test_skill_request_empty_skill_name(self):
        """Test skill request with empty skill name."""
        with pytest.raises(ValueError):
            SkillRequest(
                skill_name="",
                proficiency_level="Advanced"
            )
    
    def test_skill_request_long_skill_name(self):
        """Test skill request with very long skill name."""
        long_name = "a" * 101  # Exceeds max length of 100
        with pytest.raises(ValueError):
            SkillRequest(
                skill_name=long_name,
                proficiency_level="Advanced"
            )
    
    def test_skill_request_all_proficiency_levels(self):
        """Test all valid proficiency levels."""
        valid_levels = ["Beginner", "Intermediate", "Advanced", "Expert"]
        
        for level in valid_levels:
            skill_data = SkillRequest(
                skill_name="Python",
                proficiency_level=level
            )
            assert skill_data.proficiency_level == level 