"""
Unit tests for milestone service layer.
"""
import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from uuid import uuid4

from app.services.milestone_service import MilestoneService
from app.schemas.milestone import MilestoneCreateRequest, MilestoneUpdateRequest, MilestoneDependencyRequest
from app.models.milestone import Milestone, MilestoneDependency
from app.models.project import Project
from app.models.user import User
from app.core.auth import AuthUtils


class TestMilestoneService:
    """Test cases for milestone service functionality."""
    
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
    def sample_milestone(self, sample_project):
        """Sample milestone object."""
        return Milestone(
            id=uuid4(),
            name="Test Milestone",
            description="A test milestone",
            project_id=sample_project.id,
            due_date=date(2025, 12, 31),
            is_completed=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    @pytest.fixture
    def sample_milestone_data(self):
        """Sample milestone creation data."""
        return MilestoneCreateRequest(
            name="Test Milestone",
            description="A test milestone",
            due_date=date(2025, 12, 31),
            dependencies=[]
        )
    
    @pytest.fixture
    def sample_dependency_milestone(self, sample_project):
        """Sample dependency milestone object."""
        return Milestone(
            id=uuid4(),
            name="Dependency Milestone",
            description="A dependency milestone",
            project_id=sample_project.id,
            due_date=date(2025, 11, 15),
            is_completed=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    @pytest.fixture
    def sample_milestone_dependency(self, sample_milestone, sample_dependency_milestone):
        """Sample milestone dependency object."""
        return MilestoneDependency(
            id=uuid4(),
            dependent_milestone_id=sample_milestone.id,
            prerequisite_milestone_id=sample_dependency_milestone.id,
            created_at=datetime.now(timezone.utc)
        )
    
    def test_create_milestone_success(self, mock_db_session, sample_project, sample_milestone_data):
        """Test successful milestone creation."""
        # Mock project query to return sample project
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_project
        
        result = MilestoneService.create_milestone(
            mock_db_session,
            str(sample_project.id),
            sample_milestone_data,
            "test-user-id"
        )
        
        assert result is not None
        assert result.name == "Test Milestone"
        assert str(result.project_id) == str(sample_project.id)
        assert result.is_completed is False
        
        # Verify database operations
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    def test_create_milestone_project_not_found(self, mock_db_session, sample_milestone_data):
        """Test milestone creation when project not found."""
        # Mock project query to return None
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="Project not found"):
            MilestoneService.create_milestone(
                mock_db_session,
                "non-existent-project",
                sample_milestone_data,
                "test-user-id"
            )
    
    def test_create_milestone_with_dependencies(self, mock_db_session, sample_project, sample_dependency_milestone, sample_milestone_data):
        """Test milestone creation with dependencies."""
        # Add dependency to milestone data
        sample_milestone_data.dependencies = [sample_dependency_milestone.id]
        
        # Mock project query to return sample project
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = sample_project
        
        # Mock dependency milestone query to return sample dependency milestone
        mock_dependency_query = MagicMock()
        mock_dependency_query.filter.return_value.first.return_value = sample_dependency_milestone
        
        # Set up mock_db_session.query to return different mocks for different calls
        mock_db_session.query.side_effect = [mock_project_query, mock_dependency_query]
        
        result = MilestoneService.create_milestone(
            mock_db_session,
            str(sample_project.id),
            sample_milestone_data,
            "test-user-id"
        )
        
        assert result is not None
        # Verify dependency was added
        assert mock_db_session.add.call_count >= 2  # Milestone + dependency
    
    def test_create_milestone_dependency_not_found(self, mock_db_session, sample_project, sample_milestone_data):
        """Test milestone creation with non-existent dependency."""
        # Add non-existent dependency to milestone data
        sample_milestone_data.dependencies = [uuid4()]
        
        # Mock project query to return sample project
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = sample_project
        
        # Mock dependency milestone query to return None
        mock_dependency_query = MagicMock()
        mock_dependency_query.filter.return_value.first.return_value = None
        
        # Set up mock_db_session.query to return different mocks for different calls
        mock_db_session.query.side_effect = [mock_project_query, mock_dependency_query]
        
        with pytest.raises(ValueError, match="Dependency milestone .* not found"):
            MilestoneService.create_milestone(
                mock_db_session,
                str(sample_project.id),
                sample_milestone_data,
                "test-user-id"
            )
    
    def test_get_milestone_by_id_success(self, mock_db_session, sample_milestone):
        """Test successful milestone retrieval by ID."""
        mock_db_session.query.return_value.options.return_value.filter.return_value.first.return_value = sample_milestone
        
        result = MilestoneService.get_milestone_by_id(mock_db_session, str(sample_milestone.id))
        
        assert result == sample_milestone
        mock_db_session.query.assert_called_once()
    
    def test_get_milestone_by_id_not_found(self, mock_db_session):
        """Test milestone retrieval when milestone not found."""
        mock_db_session.query.return_value.options.return_value.filter.return_value.first.return_value = None
        
        result = MilestoneService.get_milestone_by_id(mock_db_session, "non-existent-id")
        
        assert result is None
    
    def test_get_project_milestones_no_filter(self, mock_db_session, sample_milestone):
        """Test project milestones retrieval with no filter."""
        # Mock milestones query
        mock_milestones = [sample_milestone]
        mock_db_session.query.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = mock_milestones
        
        result = MilestoneService.get_project_milestones(mock_db_session, "test-project-id")
        
        assert len(result) == 1
        assert result[0] == sample_milestone
        mock_db_session.query.assert_called_once()
    
    def test_get_project_milestones_with_completion_filter(self, mock_db_session, sample_milestone):
        """Test project milestones retrieval with completion filter."""
        # Mock milestones query
        mock_milestones = [sample_milestone]
        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_milestones
        
        mock_db_session.query.return_value = mock_query
        
        result = MilestoneService.get_project_milestones(mock_db_session, "test-project-id", is_completed=False)
        
        assert len(result) == 1
        assert result[0] == sample_milestone
        mock_db_session.query.assert_called_once()
    
    def test_update_milestone_success(self, mock_db_session, sample_milestone):
        """Test successful milestone update."""
        # Mock milestone query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_milestone
        
        update_data = MilestoneUpdateRequest(
            name="Updated Milestone",
            is_completed=True
        )
        
        result = MilestoneService.update_milestone(
            mock_db_session,
            str(sample_milestone.id),
            update_data
        )
        
        assert result == sample_milestone
        assert sample_milestone.name == "Updated Milestone"
        assert sample_milestone.is_completed is True
        assert sample_milestone.completed_at is not None
        assert sample_milestone.updated_at is not None
        
        # Verify database operations
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    def test_update_milestone_not_found(self, mock_db_session):
        """Test milestone update when milestone not found."""
        # Mock milestone query to return None
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        update_data = MilestoneUpdateRequest(name="Updated Milestone")
        
        result = MilestoneService.update_milestone(
            mock_db_session,
            "non-existent-id",
            update_data
        )
        
        assert result is None
    
    def test_delete_milestone_success(self, mock_db_session, sample_milestone):
        """Test successful milestone deletion."""
        # Mock milestone query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_milestone
        
        result = MilestoneService.delete_milestone(mock_db_session, str(sample_milestone.id))
        
        assert result is True
        mock_db_session.delete.assert_called_once_with(sample_milestone)
        mock_db_session.commit.assert_called_once()
    
    def test_delete_milestone_not_found(self, mock_db_session):
        """Test milestone deletion when milestone not found."""
        # Mock milestone query to return None
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = MilestoneService.delete_milestone(mock_db_session, "non-existent-id")
        
        assert result is False
    
    def test_add_milestone_dependency_success(self, mock_db_session, sample_milestone, sample_dependency_milestone):
        """Test successful milestone dependency addition."""
        # Mock milestone queries
        mock_milestone_query = MagicMock()
        mock_milestone_query.filter.return_value.first.return_value = sample_milestone
        
        mock_dependency_query = MagicMock()
        mock_dependency_query.filter.return_value.first.return_value = sample_dependency_milestone
        
        # Mock dependency query to return no existing dependency
        mock_existing_dependency_query = MagicMock()
        mock_existing_dependency_query.filter.return_value.first.return_value = None
        
        # Set up mock_db_session.query to return different mocks for different calls
        mock_db_session.query.side_effect = [mock_milestone_query, mock_dependency_query, mock_existing_dependency_query]
        
        dependency_data = MilestoneDependencyRequest(prerequisite_milestone_id=sample_dependency_milestone.id)
        
        result = MilestoneService.add_milestone_dependency(
            mock_db_session,
            str(sample_milestone.id),
            dependency_data
        )
        
        assert result is not None
        assert result.dependent_milestone_id == sample_milestone.id
        assert result.prerequisite_milestone_id == sample_dependency_milestone.id
        
        # Verify database operations
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    def test_add_milestone_dependency_milestone_not_found(self, mock_db_session, sample_dependency_milestone):
        """Test milestone dependency addition when milestone not found."""
        # Mock milestone query to return None
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        dependency_data = MilestoneDependencyRequest(prerequisite_milestone_id=sample_dependency_milestone.id)
        
        with pytest.raises(ValueError, match="Milestone not found"):
            MilestoneService.add_milestone_dependency(
                mock_db_session,
                "non-existent-milestone",
                dependency_data
            )
    
    def test_add_milestone_dependency_prerequisite_not_found(self, mock_db_session, sample_milestone):
        """Test milestone dependency addition when prerequisite milestone not found."""
        # Mock milestone query to return sample milestone
        mock_milestone_query = MagicMock()
        mock_milestone_query.filter.return_value.first.return_value = sample_milestone
        
        # Mock prerequisite milestone query to return None
        mock_prerequisite_query = MagicMock()
        mock_prerequisite_query.filter.return_value.first.return_value = None
        
        # Set up mock_db_session.query to return different mocks for different calls
        mock_db_session.query.side_effect = [mock_milestone_query, mock_prerequisite_query]
        
        dependency_data = MilestoneDependencyRequest(prerequisite_milestone_id=uuid4())
        
        with pytest.raises(ValueError, match="Prerequisite milestone not found"):
            MilestoneService.add_milestone_dependency(
                mock_db_session,
                str(sample_milestone.id),
                dependency_data
            )
    
    def test_remove_milestone_dependency_success(self, mock_db_session, sample_milestone_dependency):
        """Test successful milestone dependency removal."""
        # Mock dependency query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_milestone_dependency
        
        result = MilestoneService.remove_milestone_dependency(
            mock_db_session,
            str(sample_milestone_dependency.dependent_milestone_id),
            str(sample_milestone_dependency.prerequisite_milestone_id)
        )
        
        assert result is True
        mock_db_session.delete.assert_called_once_with(sample_milestone_dependency)
        mock_db_session.commit.assert_called_once()
    
    def test_remove_milestone_dependency_not_found(self, mock_db_session):
        """Test milestone dependency removal when dependency not found."""
        # Mock dependency query to return None
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = MilestoneService.remove_milestone_dependency(
            mock_db_session,
            "test-dependent-id",
            "test-prerequisite-id"
        )
        
        assert result is False
    
    def test_get_milestone_statistics_success(self, mock_db_session, sample_milestone):
        """Test successful milestone statistics calculation."""
        # Create additional milestones for testing
        completed_milestone = Milestone(
            id=uuid4(),
            name="Completed Milestone",
            project_id=sample_milestone.project_id,
            due_date=date(2024, 5, 15),
            is_completed=True,
            completed_at=datetime.now(timezone.utc)
        )
        
        overdue_milestone = Milestone(
            id=uuid4(),
            name="Overdue Milestone",
            project_id=sample_milestone.project_id,
            due_date=date(2023, 12, 31),
            is_completed=False
        )
        
        mock_milestones = [sample_milestone, completed_milestone, overdue_milestone]
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_milestones
        
        result = MilestoneService.get_milestone_statistics(mock_db_session, str(sample_milestone.project_id))
        
        assert result["total_milestones"] == 3
        assert result["completed_milestones"] == 1
        assert result["overdue_milestones"] == 1
        assert result["upcoming_milestones"] == 1
        assert result["completion_percentage"] == pytest.approx(33.33, rel=1e-2)
        assert result["average_completion_time_days"] is not None
    
    def test_get_milestone_statistics_empty_project(self, mock_db_session):
        """Test milestone statistics calculation for empty project."""
        # Mock empty milestones query
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        result = MilestoneService.get_milestone_statistics(mock_db_session, "test-project-id")
        
        assert result["total_milestones"] == 0
        assert result["completed_milestones"] == 0
        assert result["overdue_milestones"] == 0
        assert result["upcoming_milestones"] == 0
        assert result["completion_percentage"] == 0
        assert result["average_completion_time_days"] is None
    
    def test_can_access_milestone_admin(self, sample_milestone):
        """Test milestone access for admin user."""
        can_access = MilestoneService.can_access_milestone(
            sample_milestone,
            "admin-user-id",
            "Admin"
        )
        
        assert can_access is True
    
    def test_can_access_milestone_project_manager(self, sample_milestone):
        """Test milestone access for project manager user."""
        can_access = MilestoneService.can_access_milestone(
            sample_milestone,
            "manager-user-id",
            "Project Manager"
        )
        
        assert can_access is True
    
    def test_can_manage_milestone_admin(self, sample_milestone):
        """Test milestone management for admin user."""
        can_manage = MilestoneService.can_manage_milestone(
            sample_milestone,
            "admin-user-id",
            "Admin"
        )
        
        assert can_manage is True
    
    def test_can_manage_milestone_project_manager(self, sample_milestone):
        """Test milestone management for project manager user."""
        can_manage = MilestoneService.can_manage_milestone(
            sample_milestone,
            "manager-user-id",
            "Project Manager"
        )
        
        assert can_manage is True
    
    def test_can_manage_milestone_unauthorized(self, sample_milestone):
        """Test milestone management for unauthorized user."""
        can_manage = MilestoneService.can_manage_milestone(
            sample_milestone,
            "unauthorized-user-id",
            "Developer"
        )
        
        assert can_manage is False


class TestMilestoneValidation:
    """Test cases for milestone validation."""
    
    def test_milestone_create_request_valid(self):
        """Test valid milestone creation request."""
        milestone_data = MilestoneCreateRequest(
            name="Test Milestone",
            description="A test milestone",
            due_date=date(2025, 12, 31),
            dependencies=[]
        )
        
        assert milestone_data.name == "Test Milestone"
        assert milestone_data.due_date == date(2025, 12, 31)
    
    def test_milestone_create_request_past_due_date(self):
        """Test milestone creation request with past due date."""
        with pytest.raises(ValueError, match="Due date cannot be in the past"):
            MilestoneCreateRequest(
                name="Test Milestone",
                due_date=date(2020, 1, 1)
            )
    
    def test_milestone_update_request_valid(self):
        """Test valid milestone update request."""
        update_data = MilestoneUpdateRequest(
            name="Updated Milestone",
            is_completed=True
        )
        
        assert update_data.name == "Updated Milestone"
        assert update_data.is_completed is True
    
    def test_milestone_update_request_past_due_date(self):
        """Test milestone update request with past due date."""
        with pytest.raises(ValueError, match="Due date cannot be in the past"):
            MilestoneUpdateRequest(due_date=date(2020, 1, 1))
    
    def test_milestone_dependency_request_valid(self):
        """Test valid milestone dependency request."""
        dependency_data = MilestoneDependencyRequest(prerequisite_milestone_id=uuid4())
        
        assert dependency_data.prerequisite_milestone_id is not None 