"""
Unit tests for team management service layer.
"""
import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from uuid import uuid4

from app.services.project_service import ProjectService
from app.schemas.team import TeamMemberRoleUpdateRequest
from app.models.project import Project, ProjectTeamMember
from app.models.user import User
from app.core.auth import AuthUtils


class TestTeamService:
    """Test cases for team management functionality."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return MagicMock()
    
    @pytest.fixture
    def sample_user(self):
        """Sample user object."""
        return User(
            id=uuid4(),
            email="test@example.com",
            password_hash=AuthUtils.get_password_hash("SecurePass123!"),
            first_name="Test",
            last_name="User",
            role="Project Manager",
            hourly_rate=50.0,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
    
    @pytest.fixture
    def sample_project(self, sample_user):
        """Sample project object."""
        return Project(
            id=uuid4(),
            name="Test Project",
            description="A test project",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            budget=Decimal('10000.00'),
            actual_cost=Decimal('5000.00'),
            status="Active",
            manager_id=sample_user.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    @pytest.fixture
    def sample_team_member(self, sample_project, sample_user):
        """Sample team member object."""
        return ProjectTeamMember(
            id=uuid4(),
            project_id=sample_project.id,
            user_id=sample_user.id,
            role="Developer",
            joined_at=datetime.now(timezone.utc)
        )
    
    @pytest.fixture
    def sample_role_update_data(self):
        """Sample role update data."""
        return TeamMemberRoleUpdateRequest(role="Senior Developer")
    
    def test_get_project_team_members_success(self, mock_db_session, sample_team_member):
        """Test successful retrieval of project team members."""
        # Mock team members query
        mock_team_members = [sample_team_member]
        mock_db_session.query.return_value.options.return_value.filter.return_value.all.return_value = mock_team_members
        
        result = ProjectService.get_project_team_members(mock_db_session, "test-project-id")
        
        assert result == mock_team_members
        mock_db_session.query.assert_called_once()
    
    def test_get_project_team_members_empty(self, mock_db_session):
        """Test retrieval of team members when project has no team."""
        # Mock empty team members query
        mock_db_session.query.return_value.options.return_value.filter.return_value.all.return_value = []
        
        result = ProjectService.get_project_team_members(mock_db_session, "test-project-id")
        
        assert result == []
        mock_db_session.query.assert_called_once()
    
    def test_get_project_team_member_success(self, mock_db_session, sample_team_member):
        """Test successful retrieval of specific team member."""
        # Mock team member query
        mock_db_session.query.return_value.options.return_value.filter.return_value.first.return_value = sample_team_member
        
        result = ProjectService.get_project_team_member(
            mock_db_session,
            "test-project-id",
            "test-member-id"
        )
        
        assert result == sample_team_member
        mock_db_session.query.assert_called_once()
    
    def test_get_project_team_member_not_found(self, mock_db_session):
        """Test retrieval of team member when not found."""
        # Mock team member query to return None
        mock_db_session.query.return_value.options.return_value.filter.return_value.first.return_value = None
        
        result = ProjectService.get_project_team_member(
            mock_db_session,
            "test-project-id",
            "non-existent-member-id"
        )
        
        assert result is None
    
    def test_update_team_member_role_success(self, mock_db_session, sample_team_member):
        """Test successful team member role update."""
        # Mock team member query to return sample team member
        mock_db_session.query.return_value.options.return_value.filter.return_value.first.return_value = sample_team_member
        
        result = ProjectService.update_team_member_role(
            mock_db_session,
            "test-project-id",
            "test-member-id",
            "Senior Developer"
        )
        
        assert result == sample_team_member
        assert sample_team_member.role == "Senior Developer"
        
        # Verify database operations
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    def test_update_team_member_role_not_found(self, mock_db_session):
        """Test team member role update when member not found."""
        # Mock team member query to return None
        mock_db_session.query.return_value.options.return_value.filter.return_value.first.return_value = None
        
        result = ProjectService.update_team_member_role(
            mock_db_session,
            "test-project-id",
            "non-existent-member-id",
            "Senior Developer"
        )
        
        assert result is None
    
    def test_get_team_statistics_success(self, mock_db_session, sample_team_member):
        """Test successful team statistics calculation."""
        # Create additional team members for testing
        user2 = User(id=uuid4(), email="user2@example.com", first_name="User", last_name="Two")
        user3 = User(id=uuid4(), email="user3@example.com", first_name="User", last_name="Three")
        
        team_member2 = ProjectTeamMember(
            id=uuid4(),
            project_id=sample_team_member.project_id,
            user_id=user2.id,
            role="QA",
            joined_at=datetime.now(timezone.utc)
        )
        
        team_member3 = ProjectTeamMember(
            id=uuid4(),
            project_id=sample_team_member.project_id,
            user_id=user3.id,
            role="Developer",
            joined_at=datetime.now(timezone.utc),
            left_at=datetime.now(timezone.utc)  # Inactive member
        )
        
        mock_team_members = [sample_team_member, team_member2, team_member3]
        mock_db_session.query.return_value.options.return_value.filter.return_value.all.return_value = mock_team_members
        
        result = ProjectService.get_team_statistics(mock_db_session, "test-project-id")
        
        assert result["total_members"] == 3
        assert result["active_members"] == 2
        assert result["inactive_members"] == 1
        assert result["roles_distribution"]["Developer"] == 2
        assert result["roles_distribution"]["QA"] == 1
        assert result["average_tenure_days"] is not None
    
    def test_get_team_statistics_empty_team(self, mock_db_session):
        """Test team statistics calculation for empty team."""
        # Mock empty team members query
        mock_db_session.query.return_value.options.return_value.filter.return_value.all.return_value = []
        
        result = ProjectService.get_team_statistics(mock_db_session, "test-project-id")
        
        assert result["total_members"] == 0
        assert result["active_members"] == 0
        assert result["inactive_members"] == 0
        assert result["roles_distribution"] == {}
        assert result["average_tenure_days"] is None
    
    def test_get_team_statistics_all_inactive(self, mock_db_session, sample_team_member):
        """Test team statistics calculation when all members are inactive."""
        # Set team member as inactive
        sample_team_member.left_at = datetime.now(timezone.utc)
        
        mock_team_members = [sample_team_member]
        mock_db_session.query.return_value.options.return_value.filter.return_value.all.return_value = mock_team_members
        
        result = ProjectService.get_team_statistics(mock_db_session, "test-project-id")
        
        assert result["total_members"] == 1
        assert result["active_members"] == 0
        assert result["inactive_members"] == 1
        assert result["roles_distribution"]["Developer"] == 1
        assert result["average_tenure_days"] is None
    
    def test_get_team_statistics_single_active_member(self, mock_db_session, sample_team_member):
        """Test team statistics calculation for single active member."""
        mock_team_members = [sample_team_member]
        mock_db_session.query.return_value.options.return_value.filter.return_value.all.return_value = mock_team_members
        
        result = ProjectService.get_team_statistics(mock_db_session, "test-project-id")
        
        assert result["total_members"] == 1
        assert result["active_members"] == 1
        assert result["inactive_members"] == 0
        assert result["roles_distribution"]["Developer"] == 1
        assert result["average_tenure_days"] is not None
        assert result["average_tenure_days"] >= 0


class TestTeamValidation:
    """Test cases for team validation."""
    
    def test_team_member_role_update_request_valid(self):
        """Test valid team member role update request."""
        role_data = TeamMemberRoleUpdateRequest(role="Senior Developer")
        
        assert role_data.role == "Senior Developer"
    
    def test_team_member_role_update_request_empty_role(self):
        """Test team member role update request with empty role."""
        with pytest.raises(ValueError, match="String should have at least 1 character"):
            TeamMemberRoleUpdateRequest(role="")
    
    def test_team_member_role_update_request_whitespace_role(self):
        """Test team member role update request with whitespace role."""
        with pytest.raises(ValueError, match="Role cannot be empty"):
            TeamMemberRoleUpdateRequest(role="   ")
    
    def test_team_member_role_update_request_trimmed_role(self):
        """Test team member role update request with role that gets trimmed."""
        role_data = TeamMemberRoleUpdateRequest(role="  Senior Developer  ")
        
        assert role_data.role == "Senior Developer"
    
    def test_team_member_role_update_request_long_role(self):
        """Test team member role update request with long role."""
        long_role = "A" * 50  # Exactly at max length
        role_data = TeamMemberRoleUpdateRequest(role=long_role)
        
        assert role_data.role == long_role
    
    def test_team_member_role_update_request_too_long_role(self):
        """Test team member role update request with too long role."""
        too_long_role = "A" * 51  # Exceeds max length
        with pytest.raises(ValueError):
            TeamMemberRoleUpdateRequest(role=too_long_role)


class TestTeamIntegration:
    """Test cases for team management integration."""
    
    def test_team_member_lifecycle(self, mock_db_session, sample_user, sample_project):
        """Test complete team member lifecycle."""
        # Create team member
        team_member = ProjectTeamMember(
            id=uuid4(),
            project_id=sample_project.id,
            user_id=sample_user.id,
            role="Developer",
            joined_at=datetime.now(timezone.utc)
        )
        
        # Mock queries for different operations
        mock_db_session.query.return_value.options.return_value.filter.return_value.first.return_value = team_member
        mock_db_session.query.return_value.options.return_value.filter.return_value.all.return_value = [team_member]
        
        # Test get team members
        team_members = ProjectService.get_project_team_members(mock_db_session, str(sample_project.id))
        assert len(team_members) == 1
        assert team_members[0].role == "Developer"
        
        # Test update role
        updated_member = ProjectService.update_team_member_role(
            mock_db_session,
            str(sample_project.id),
            str(team_member.id),
            "Senior Developer"
        )
        assert updated_member.role == "Senior Developer"
        
        # Test get team statistics
        stats = ProjectService.get_team_statistics(mock_db_session, str(sample_project.id))
        assert stats["total_members"] == 1
        assert stats["active_members"] == 1
        assert stats["roles_distribution"]["Senior Developer"] == 1
    
    def test_team_member_removal(self, mock_db_session, sample_team_member):
        """Test team member removal and statistics update."""
        # Mock team member query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_team_member
        
        # Remove team member
        success = ProjectService.remove_team_member(
            mock_db_session,
            str(sample_team_member.project_id),
            str(sample_team_member.user_id)
        )
        
        assert success is True
        assert sample_team_member.left_at is not None
        
        # Mock updated team members list (now empty)
        mock_db_session.query.return_value.options.return_value.filter.return_value.all.return_value = []
        
        # Test statistics after removal
        stats = ProjectService.get_team_statistics(mock_db_session, str(sample_team_member.project_id))
        assert stats["total_members"] == 0
        assert stats["active_members"] == 0
        assert stats["inactive_members"] == 0 