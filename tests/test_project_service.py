"""
Unit tests for project service layer.
"""
import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from uuid import uuid4

from app.services.project_service import ProjectService
from app.schemas.project import ProjectCreateRequest, ProjectUpdateRequest, ProjectQueryParams, TeamMemberRequest
from app.models.project import Project, ProjectTeamMember
from app.models.user import User
from app.core.auth import AuthUtils


class TestProjectService:
    """Test cases for project service functionality."""
    
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
    def sample_project_data(self, sample_user):
        """Sample project creation data."""
        return ProjectCreateRequest(
            name="Test Project",
            description="A test project",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            budget=Decimal('10000.00'),
            manager_id=sample_user.id,
            team_members=[]
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
    
    def test_create_project_success(self, mock_db_session, sample_user, sample_project_data):
        """Test successful project creation."""
        # Mock user query to return sample user
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_user
        
        # Mock project creation
        created_project = Project(
            id=uuid4(),
            name=sample_project_data.name,
            description=sample_project_data.description,
            start_date=sample_project_data.start_date,
            end_date=sample_project_data.end_date,
            budget=sample_project_data.budget,
            manager_id=sample_project_data.manager_id,
            status="Draft"
        )
        
        result = ProjectService.create_project(
            mock_db_session,
            sample_project_data,
            str(sample_user.id)
        )
        
        assert result is not None
        assert result.name == "Test Project"
        assert result.status == "Draft"
        
        # Verify database operations
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    def test_create_project_manager_not_found(self, mock_db_session, sample_project_data):
        """Test project creation when manager not found."""
        # Mock user query to return None
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="Manager not found"):
            ProjectService.create_project(
                mock_db_session,
                sample_project_data,
                "test-user-id"
            )
    
    def test_create_project_with_team_members(self, mock_db_session, sample_user, sample_project_data):
        """Test project creation with team members."""
        # Add team member to project data
        team_member = TeamMemberRequest(user_id=sample_user.id, role="Developer")
        sample_project_data.team_members = [team_member]
        
        # Mock user queries
        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.first.return_value = sample_user
        
        # Mock team member query to return no existing member
        mock_team_query = MagicMock()
        mock_team_query.filter.return_value.first.return_value = None
        
        # Set up mock_db_session.query to return different mocks for different calls
        mock_db_session.query.side_effect = [mock_user_query, mock_user_query, mock_team_query, mock_team_query]
        
        result = ProjectService.create_project(
            mock_db_session,
            sample_project_data,
            str(sample_user.id)
        )
        
        assert result is not None
        # Verify team member was added
        assert mock_db_session.add.call_count >= 2  # Project + team member
    
    def test_create_project_duplicate_team_member(self, mock_db_session, sample_user, sample_project_data):
        """Test project creation with duplicate team member."""
        # Add team member to project data
        team_member = TeamMemberRequest(user_id=sample_user.id, role="Developer")
        sample_project_data.team_members = [team_member]
        
        # Mock user queries
        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.first.return_value = sample_user
        
        # Mock team member query to return existing member
        existing_member = ProjectTeamMember(user_id=sample_user.id, role="Developer")
        mock_team_query = MagicMock()
        mock_team_query.filter.return_value.first.return_value = existing_member
        
        # Set up mock_db_session.query to return different mocks for different calls
        mock_db_session.query.side_effect = [mock_user_query, mock_user_query, mock_team_query]
        
        with pytest.raises(ValueError, match="User .* is already a team member"):
            ProjectService.create_project(
                mock_db_session,
                sample_project_data,
                str(sample_user.id)
            )
    
    def test_get_project_by_id_success(self, mock_db_session, sample_project):
        """Test successful project retrieval by ID."""
        mock_db_session.query.return_value.options.return_value.filter.return_value.first.return_value = sample_project
        
        result = ProjectService.get_project_by_id(mock_db_session, str(sample_project.id))
        
        assert result == sample_project
        mock_db_session.query.assert_called_once()
    
    def test_get_project_by_id_not_found(self, mock_db_session):
        """Test project retrieval when project not found."""
        mock_db_session.query.return_value.options.return_value.filter.return_value.first.return_value = None
        
        result = ProjectService.get_project_by_id(mock_db_session, "non-existent-id")
        
        assert result is None
    
    def test_get_projects_with_pagination_no_filters(self, mock_db_session, sample_project):
        """Test project retrieval with pagination and no filters."""
        # Mock query chain
        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = [sample_project]
        
        mock_db_session.query.return_value = mock_query
        
        query_params = ProjectQueryParams(page=1, limit=20)
        
        projects, total_count = ProjectService.get_projects_with_pagination(
            mock_db_session,
            query_params,
            "test-user-id",
            "Admin"
        )
        
        assert len(projects) == 1
        assert total_count == 1
        assert projects[0] == sample_project
    
    def test_get_projects_with_status_filter(self, mock_db_session, sample_project):
        """Test project retrieval with status filter."""
        # Mock query chain
        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = [sample_project]
        
        mock_db_session.query.return_value = mock_query
        
        query_params = ProjectQueryParams(page=1, limit=20, status="Active")
        
        projects, total_count = ProjectService.get_projects_with_pagination(
            mock_db_session,
            query_params,
            "test-user-id",
            "Admin"
        )
        
        assert len(projects) == 1
        assert total_count == 1
    
    def test_get_projects_my_projects_filter(self, mock_db_session, sample_project):
        """Test project retrieval with my_projects filter."""
        # Mock query chain
        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = [sample_project]
        
        mock_db_session.query.return_value = mock_query
        
        query_params = ProjectQueryParams(page=1, limit=20, my_projects=True)
        
        projects, total_count = ProjectService.get_projects_with_pagination(
            mock_db_session,
            query_params,
            "test-user-id",
            "Developer"
        )
        
        assert len(projects) == 1
        assert total_count == 1
    
    def test_update_project_success(self, mock_db_session, sample_project):
        """Test successful project update."""
        # Mock project query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_project
        
        update_data = ProjectUpdateRequest(
            name="Updated Project",
            status="Completed"
        )
        
        result = ProjectService.update_project(
            mock_db_session,
            str(sample_project.id),
            update_data
        )
        
        assert result == sample_project
        assert sample_project.name == "Updated Project"
        assert sample_project.status == "Completed"
        assert sample_project.updated_at is not None
        
        # Verify database operations
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    def test_update_project_not_found(self, mock_db_session):
        """Test project update when project not found."""
        # Mock project query to return None
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        update_data = ProjectUpdateRequest(name="Updated Project")
        
        result = ProjectService.update_project(
            mock_db_session,
            "non-existent-id",
            update_data
        )
        
        assert result is None
    
    def test_delete_project_success(self, mock_db_session, sample_project):
        """Test successful project deletion."""
        # Mock project query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_project
        
        result = ProjectService.delete_project(mock_db_session, str(sample_project.id))
        
        assert result is True
        mock_db_session.delete.assert_called_once_with(sample_project)
        mock_db_session.commit.assert_called_once()
    
    def test_delete_project_not_found(self, mock_db_session):
        """Test project deletion when project not found."""
        # Mock project query to return None
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = ProjectService.delete_project(mock_db_session, "non-existent-id")
        
        assert result is False
    
    def test_add_team_member_success(self, mock_db_session, sample_project, sample_user):
        """Test successful team member addition."""
        # Mock project and user queries
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = sample_project
        
        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.first.return_value = sample_user
        
        # Mock team member query to return no existing member
        mock_team_query = MagicMock()
        mock_team_query.filter.return_value.first.return_value = None
        
        # Set up mock_db_session.query to return different mocks for different calls
        mock_db_session.query.side_effect = [mock_project_query, mock_user_query, mock_team_query]
        
        result = ProjectService.add_team_member(
            mock_db_session,
            str(sample_project.id),
            str(sample_user.id),
            "Developer"
        )
        
        assert result is not None
        assert result.project_id == sample_project.id
        assert result.user_id == sample_user.id
        assert result.role == "Developer"
        
        # Verify database operations
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    def test_add_team_member_project_not_found(self, mock_db_session, sample_user):
        """Test team member addition when project not found."""
        # Mock project query to return None
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="Project not found"):
            ProjectService.add_team_member(
                mock_db_session,
                "non-existent-project",
                str(sample_user.id),
                "Developer"
            )
    
    def test_add_team_member_user_not_found(self, mock_db_session, sample_project):
        """Test team member addition when user not found."""
        # Mock project query to return sample project
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = sample_project
        
        # Mock user query to return None
        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.first.return_value = None
        
        # Set up mock_db_session.query to return different mocks for different calls
        mock_db_session.query.side_effect = [mock_project_query, mock_user_query]
        
        with pytest.raises(ValueError, match="User not found"):
            ProjectService.add_team_member(
                mock_db_session,
                str(sample_project.id),
                "non-existent-user",
                "Developer"
            )
    
    def test_add_team_member_already_exists(self, mock_db_session, sample_project, sample_user):
        """Test team member addition when user is already a team member."""
        # Mock project and user queries
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = sample_project
        
        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.first.return_value = sample_user
        
        # Mock team member query to return existing member
        existing_member = ProjectTeamMember(user_id=sample_user.id, role="Developer")
        mock_team_query = MagicMock()
        mock_team_query.filter.return_value.first.return_value = existing_member
        
        # Set up mock_db_session.query to return different mocks for different calls
        mock_db_session.query.side_effect = [mock_project_query, mock_user_query, mock_team_query]
        
        with pytest.raises(ValueError, match="User is already a team member"):
            ProjectService.add_team_member(
                mock_db_session,
                str(sample_project.id),
                str(sample_user.id),
                "Developer"
            )
    
    def test_remove_team_member_success(self, mock_db_session, sample_team_member):
        """Test successful team member removal."""
        # Mock team member query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_team_member
        
        result = ProjectService.remove_team_member(
            mock_db_session,
            str(sample_team_member.project_id),
            str(sample_team_member.user_id)
        )
        
        assert result is True
        assert sample_team_member.left_at is not None
        mock_db_session.commit.assert_called_once()
    
    def test_remove_team_member_not_found(self, mock_db_session):
        """Test team member removal when member not found."""
        # Mock team member query to return None
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = ProjectService.remove_team_member(
            mock_db_session,
            "test-project-id",
            "test-user-id"
        )
        
        assert result is False
    
    def test_calculate_pagination_info(self):
        """Test pagination info calculation."""
        pagination = ProjectService.calculate_pagination_info(100, 1, 20)
        
        assert pagination["page"] == 1
        assert pagination["limit"] == 20
        assert pagination["total"] == 100
        assert pagination["pages"] == 5
        assert pagination["has_next"] is True
        assert pagination["has_prev"] is False
    
    def test_can_access_project_admin(self, sample_project):
        """Test project access for admin user."""
        can_access = ProjectService.can_access_project(
            sample_project,
            "admin-user-id",
            "Admin"
        )
        
        assert can_access is True
    
    def test_can_access_project_manager(self, sample_project):
        """Test project access for project manager."""
        can_access = ProjectService.can_access_project(
            sample_project,
            str(sample_project.manager_id),
            "Project Manager"
        )
        
        assert can_access is True
    
    def test_can_access_project_team_member(self, sample_project, sample_team_member):
        """Test project access for team member."""
        # Add team member to project
        sample_project.team_members = [sample_team_member]
        
        can_access = ProjectService.can_access_project(
            sample_project,
            str(sample_team_member.user_id),
            "Developer"
        )
        
        assert can_access is True
    
    def test_can_access_project_unauthorized(self, sample_project):
        """Test project access for unauthorized user."""
        can_access = ProjectService.can_access_project(
            sample_project,
            "unauthorized-user-id",
            "Developer"
        )
        
        assert can_access is False
    
    def test_can_manage_project_admin(self, sample_project):
        """Test project management for admin user."""
        can_manage = ProjectService.can_manage_project(
            sample_project,
            "admin-user-id",
            "Admin"
        )
        
        assert can_manage is True
    
    def test_can_manage_project_manager(self, sample_project):
        """Test project management for project manager."""
        can_manage = ProjectService.can_manage_project(
            sample_project,
            str(sample_project.manager_id),
            "Project Manager"
        )
        
        assert can_manage is True
    
    def test_can_manage_project_unauthorized(self, sample_project):
        """Test project management for unauthorized user."""
        can_manage = ProjectService.can_manage_project(
            sample_project,
            "unauthorized-user-id",
            "Developer"
        )
        
        assert can_manage is False


class TestProjectValidation:
    """Test cases for project validation."""
    
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
    
    def test_project_create_request_valid(self, sample_user):
        """Test valid project creation request."""
        project_data = ProjectCreateRequest(
            name="Test Project",
            description="A test project",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            budget=Decimal('10000.00'),
            manager_id=sample_user.id,
            team_members=[]
        )
        
        assert project_data.name == "Test Project"
        assert project_data.start_date == date(2024, 1, 1)
        assert project_data.end_date == date(2024, 12, 31)
    
    def test_project_create_request_invalid_dates(self, sample_user):
        """Test project creation request with invalid dates."""
        with pytest.raises(ValueError, match="End date must be after start date"):
            ProjectCreateRequest(
                name="Test Project",
                start_date=date(2024, 12, 31),
                end_date=date(2024, 1, 1),
                manager_id=sample_user.id
            )
    
    def test_project_update_request_valid(self):
        """Test valid project update request."""
        update_data = ProjectUpdateRequest(
            name="Updated Project",
            status="Completed"
        )
        
        assert update_data.name == "Updated Project"
        assert update_data.status == "Completed"
    
    def test_project_update_request_invalid_status(self):
        """Test project update request with invalid status."""
        with pytest.raises(ValueError, match="Status must be one of"):
            ProjectUpdateRequest(status="Invalid")
    
    def test_project_query_params_valid(self):
        """Test valid project query parameters."""
        query_params = ProjectQueryParams(
            page=1,
            limit=20,
            status="Active",
            search="test"
        )
        
        assert query_params.page == 1
        assert query_params.limit == 20
        assert query_params.status == "Active"
        assert query_params.search == "test"
    
    def test_project_query_params_invalid_status(self):
        """Test project query parameters with invalid status."""
        with pytest.raises(ValueError, match="Status must be one of"):
            ProjectQueryParams(status="Invalid") 