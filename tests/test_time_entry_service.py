"""
Tests for time entry service layer.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from uuid import uuid4

from app.services.time_entry_service import TimeEntryService
from app.schemas.time_entry import TimeEntryCreateRequest, TimeEntryUpdateRequest
from app.models.time_entry import TimeEntry
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from pydantic import ValidationError


class TestTimeEntryService:
    """Test cases for time entry service."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return MagicMock()
    
    @pytest.fixture
    def sample_user(self):
        """Sample user for testing."""
        user = User(
            id=uuid4(),
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password_hash="hashed_password",
            role="Developer",
            is_active=True
        )
        return user
    
    @pytest.fixture
    def sample_project(self, sample_user):
        """Sample project for testing."""
        project = Project(
            id=uuid4(),
            name="Test Project",
            description="A test project",
            manager_id=sample_user.id,
            status="Active",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31)
        )
        return project
    
    @pytest.fixture
    def sample_task(self, sample_project, sample_user):
        """Sample task for testing."""
        task = Task(
            id=uuid4(),
            title="Test Task",
            description="A test task",
            project_id=sample_project.id,
            assignee_id=sample_user.id,
            priority="Medium",
            status="ToDo",
            estimated_hours=Decimal('8.00'),
            due_date=date(2025, 12, 31)
        )
        return task
    
    @pytest.fixture
    def sample_time_entry(self, sample_user, sample_project, sample_task):
        """Sample time entry for testing."""
        time_entry = TimeEntry(
            id=uuid4(),
            user_id=sample_user.id,
            task_id=sample_task.id,
            project_id=sample_project.id,
            hours=Decimal('8.00'),
            date=date(2025, 1, 15),
            category="Development",
            notes="Test time entry",
            is_approved=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        return time_entry
    
    @pytest.fixture
    def sample_time_entry_data(self, sample_project, sample_task):
        """Sample time entry creation data."""
        return TimeEntryCreateRequest(
            task_id=sample_task.id,
            project_id=sample_project.id,
            hours=Decimal('8.00'),
            work_date=date(2025, 1, 15),
            category="Development",
            notes="Test time entry"
        )
    
    def test_create_time_entry_success(self, mock_db_session, sample_project, sample_task, sample_time_entry_data):
        """Test successful time entry creation."""
        # Mock project query
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = sample_project
        
        # Mock task query
        mock_task_query = MagicMock()
        mock_task_query.filter.return_value.first.return_value = sample_task
        
        # Mock existing entry query (no existing entry)
        mock_existing_query = MagicMock()
        mock_existing_query.filter.return_value.first.return_value = None
        
        # Mock database session
        mock_db_session.query.side_effect = [
            mock_project_query,
            mock_task_query,
            mock_existing_query
        ]
        
        # Mock time entry creation
        mock_time_entry = MagicMock()
        mock_time_entry.id = uuid4()
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.return_value = None
        
        result = TimeEntryService.create_time_entry(
            mock_db_session,
            sample_time_entry_data,
            str(sample_project.manager_id)
        )
        
        assert result is not None
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    def test_create_time_entry_project_not_found(self, mock_db_session, sample_time_entry_data):
        """Test time entry creation with non-existent project."""
        # Mock project query (project not found)
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = None
        
        mock_db_session.query.return_value = mock_project_query
        
        with pytest.raises(ValueError, match="Project not found"):
            TimeEntryService.create_time_entry(
                mock_db_session,
                sample_time_entry_data,
                str(uuid4())
            )
    
    def test_create_time_entry_task_not_found(self, mock_db_session, sample_project, sample_time_entry_data):
        """Test time entry creation with non-existent task."""
        # Mock project query
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = sample_project
        
        # Mock task query (task not found)
        mock_task_query = MagicMock()
        mock_task_query.filter.return_value.first.return_value = None
        
        mock_db_session.query.side_effect = [mock_project_query, mock_task_query]
        
        with pytest.raises(ValueError, match="Task not found"):
            TimeEntryService.create_time_entry(
                mock_db_session,
                sample_time_entry_data,
                str(uuid4())
            )
    
    def test_create_time_entry_task_wrong_project(self, mock_db_session, sample_project, sample_task, sample_time_entry_data):
        """Test time entry creation with task from different project."""
        # Mock project query
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = sample_project
        
        # Mock task query (task from different project)
        mock_task_query = MagicMock()
        wrong_project_task = MagicMock()
        wrong_project_task.project_id = uuid4()  # Different project ID
        mock_task_query.filter.return_value.first.return_value = wrong_project_task
        
        mock_db_session.query.side_effect = [mock_project_query, mock_task_query]
        
        with pytest.raises(ValueError, match="Task must belong to the specified project"):
            TimeEntryService.create_time_entry(
                mock_db_session,
                sample_time_entry_data,
                str(uuid4())
            )
    
    def test_create_time_entry_duplicate(self, mock_db_session, sample_project, sample_task, sample_time_entry_data, sample_time_entry):
        """Test time entry creation with duplicate entry."""
        # Mock project query
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = sample_project
        
        # Mock task query
        mock_task_query = MagicMock()
        mock_task_query.filter.return_value.first.return_value = sample_task
        
        # Mock existing entry query (duplicate found)
        mock_existing_query = MagicMock()
        mock_existing_query.filter.return_value.first.return_value = sample_time_entry
        
        mock_db_session.query.side_effect = [mock_project_query, mock_task_query, mock_existing_query]
        
        with pytest.raises(ValueError, match="Time entry already exists"):
            TimeEntryService.create_time_entry(
                mock_db_session,
                sample_time_entry_data,
                str(sample_time_entry.user_id)
            )
    
    def test_get_time_entry_by_id_success(self, mock_db_session, sample_time_entry):
        """Test successful time entry retrieval by ID."""
        # Mock time entry query
        mock_query = MagicMock()
        mock_query.options.return_value.filter.return_value.first.return_value = sample_time_entry
        
        mock_db_session.query.return_value = mock_query
        
        result = TimeEntryService.get_time_entry_by_id(mock_db_session, str(sample_time_entry.id))
        
        assert result == sample_time_entry
        mock_db_session.query.assert_called_once()
    
    def test_get_time_entry_by_id_not_found(self, mock_db_session):
        """Test time entry retrieval by ID when not found."""
        # Mock time entry query (not found)
        mock_query = MagicMock()
        mock_query.options.return_value.filter.return_value.first.return_value = None
        
        mock_db_session.query.return_value = mock_query
        
        result = TimeEntryService.get_time_entry_by_id(mock_db_session, str(uuid4()))
        
        assert result is None
        mock_db_session.query.assert_called_once()
    
    def test_get_user_time_entries_success(self, mock_db_session, sample_time_entry):
        """Test successful user time entries retrieval."""
        # Mock time entries query with proper chaining
        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_time_entry]
        
        mock_db_session.query.return_value = mock_query
        
        time_entries, pagination_info = TimeEntryService.get_user_time_entries(
            mock_db_session,
            str(sample_time_entry.user_id),
            page=1,
            limit=20
        )
        
        assert len(time_entries) == 1
        assert time_entries[0] == sample_time_entry
        assert pagination_info["total"] == 1
        assert pagination_info["page"] == 1
        assert pagination_info["limit"] == 20
        mock_db_session.query.assert_called_once()
    
    def test_update_time_entry_success(self, mock_db_session, sample_time_entry):
        """Test successful time entry update."""
        # Mock time entry query
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = sample_time_entry
        
        mock_db_session.query.return_value = mock_query
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.return_value = None
        
        update_data = TimeEntryUpdateRequest(
            hours=Decimal('6.00'),
            category="Testing",
            notes="Updated notes"
        )
        
        result = TimeEntryService.update_time_entry(
            mock_db_session,
            str(sample_time_entry.id),
            update_data,
            str(sample_time_entry.user_id)
        )
        
        assert result == sample_time_entry
        assert sample_time_entry.hours == Decimal('6.00')
        assert sample_time_entry.category == "Testing"
        assert sample_time_entry.notes == "Updated notes"
        mock_db_session.commit.assert_called_once()
    
    def test_update_time_entry_not_found(self, mock_db_session):
        """Test time entry update when not found."""
        # Mock time entry query (not found)
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        
        mock_db_session.query.return_value = mock_query
        
        update_data = TimeEntryUpdateRequest(hours=Decimal('6.00'))
        
        result = TimeEntryService.update_time_entry(
            mock_db_session,
            str(uuid4()),
            update_data,
            str(uuid4())
        )
        
        assert result is None
        mock_db_session.query.assert_called_once()
    
    def test_update_time_entry_unauthorized(self, mock_db_session, sample_time_entry):
        """Test time entry update by unauthorized user."""
        # Mock time entry query
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = sample_time_entry
        
        mock_db_session.query.return_value = mock_query
        
        update_data = TimeEntryUpdateRequest(hours=Decimal('6.00'))
        
        with pytest.raises(ValueError, match="Not authorized to update this time entry"):
            TimeEntryService.update_time_entry(
                mock_db_session,
                str(sample_time_entry.id),
                update_data,
                str(uuid4())  # Different user ID
            )
    
    def test_update_time_entry_outside_editable_period(self, mock_db_session, sample_time_entry):
        """Test time entry update outside editable period."""
        # Set created_at to more than 7 days ago
        sample_time_entry.created_at = datetime.now(timezone.utc) - timedelta(days=8)
        
        # Mock time entry query
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = sample_time_entry
        
        mock_db_session.query.return_value = mock_query
        
        update_data = TimeEntryUpdateRequest(hours=Decimal('6.00'))
        
        with pytest.raises(ValueError, match="Time entry can only be updated within 7 days"):
            TimeEntryService.update_time_entry(
                mock_db_session,
                str(sample_time_entry.id),
                update_data,
                str(sample_time_entry.user_id)
            )
    
    def test_delete_time_entry_success(self, mock_db_session, sample_time_entry):
        """Test successful time entry deletion."""
        # Mock time entry query
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = sample_time_entry
        
        mock_db_session.query.return_value = mock_query
        mock_db_session.delete.return_value = None
        mock_db_session.commit.return_value = None
        
        result = TimeEntryService.delete_time_entry(
            mock_db_session,
            str(sample_time_entry.id),
            str(sample_time_entry.user_id)
        )
        
        assert result is True
        mock_db_session.delete.assert_called_once_with(sample_time_entry)
        mock_db_session.commit.assert_called_once()
    
    def test_delete_time_entry_not_found(self, mock_db_session):
        """Test time entry deletion when not found."""
        # Mock time entry query (not found)
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        
        mock_db_session.query.return_value = mock_query
        
        result = TimeEntryService.delete_time_entry(
            mock_db_session,
            str(uuid4()),
            str(uuid4())
        )
        
        assert result is False
        mock_db_session.query.assert_called_once()
    
    def test_delete_time_entry_unauthorized(self, mock_db_session, sample_time_entry):
        """Test time entry deletion by unauthorized user."""
        # Mock time entry query
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = sample_time_entry
        
        mock_db_session.query.return_value = mock_query
        
        with pytest.raises(ValueError, match="Not authorized to delete this time entry"):
            TimeEntryService.delete_time_entry(
                mock_db_session,
                str(sample_time_entry.id),
                str(uuid4())  # Different user ID
            )
    
    def test_can_update_time_entry_owner(self, sample_time_entry):
        """Test that time entry owner can update."""
        result = TimeEntryService.can_update_time_entry(
            sample_time_entry,
            str(sample_time_entry.user_id)
        )
        
        assert result is True
    
    def test_can_update_time_entry_unauthorized(self, sample_time_entry):
        """Test that unauthorized user cannot update."""
        result = TimeEntryService.can_update_time_entry(
            sample_time_entry,
            str(uuid4())  # Different user ID
        )
        
        assert result is False
    
    def test_can_delete_time_entry_owner(self, sample_time_entry):
        """Test that time entry owner can delete."""
        result = TimeEntryService.can_delete_time_entry(
            sample_time_entry,
            str(sample_time_entry.user_id)
        )
        
        assert result is True
    
    def test_can_delete_time_entry_unauthorized(self, sample_time_entry):
        """Test that unauthorized user cannot delete."""
        result = TimeEntryService.can_delete_time_entry(
            sample_time_entry,
            str(uuid4())  # Different user ID
        )
        
        assert result is False
    
    def test_is_within_editable_period_recent(self, sample_time_entry):
        """Test that recent time entry is within editable period."""
        sample_time_entry.created_at = datetime.now(timezone.utc) - timedelta(days=3)
        
        result = TimeEntryService.is_within_editable_period(sample_time_entry)
        
        assert result is True
    
    def test_is_within_editable_period_old(self, sample_time_entry):
        """Test that old time entry is outside editable period."""
        sample_time_entry.created_at = datetime.now(timezone.utc) - timedelta(days=10)
        
        result = TimeEntryService.is_within_editable_period(sample_time_entry)
        
        assert result is False
    
    def test_get_time_entry_statistics_success(self, mock_db_session, sample_time_entry):
        """Test successful time entry statistics retrieval."""
        # Mock time entries query with proper chaining
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [sample_time_entry]
        
        mock_db_session.query.return_value = mock_query
        
        result = TimeEntryService.get_time_entry_statistics(
            mock_db_session,
            str(sample_time_entry.user_id)
        )
        
        assert result["total_hours"] == sample_time_entry.hours
        assert result["total_entries"] == 1
        assert result["approved_entries"] == 0
        assert result["pending_entries"] == 1
        assert "Development" in result["hours_by_category"]
        assert result["hours_by_category"]["Development"] == sample_time_entry.hours
        mock_db_session.query.assert_called_once()
    
    def test_get_time_entry_statistics_empty(self, mock_db_session):
        """Test time entry statistics with no entries."""
        # Mock time entries query (empty)
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.all.return_value = []
        
        mock_db_session.query.return_value = mock_query
        
        result = TimeEntryService.get_time_entry_statistics(
            mock_db_session,
            str(uuid4())
        )
        
        assert result["total_hours"] == 0
        assert result["total_entries"] == 0
        assert result["approved_entries"] == 0
        assert result["pending_entries"] == 0
        assert result["avg_hours_per_day"] == 0
        mock_db_session.query.assert_called_once()


class TestTimeEntryValidation:
    """Test cases for time entry validation."""
    
    def test_time_entry_create_request_valid(self):
        """Test valid time entry creation request."""
        request = TimeEntryCreateRequest(
            project_id=uuid4(),
            hours=Decimal('8.00'),
            work_date=date(2025, 1, 15),
            category="Development",
            notes="Test notes"
        )
        
        assert request.project_id is not None
        assert request.hours == Decimal('8.00')
        assert request.work_date == date(2025, 1, 15)
        assert request.category == "Development"
        assert request.notes == "Test notes"
    
    def test_time_entry_create_request_invalid_category(self):
        """Test time entry creation request with invalid category."""
        with pytest.raises(ValueError, match="Category must be one of"):
            TimeEntryCreateRequest(
                project_id=uuid4(),
                hours=Decimal('8.00'),
                work_date=date(2025, 1, 15),
                category="InvalidCategory"
            )
    
    def test_time_entry_create_request_future_date(self):
        """Test time entry creation request with future date."""
        future_date = date.today() + timedelta(days=1)
        with pytest.raises(ValueError, match="Date cannot be in the future"):
            TimeEntryCreateRequest(
                project_id=uuid4(),
                hours=Decimal('8.00'),
                work_date=future_date,
                category="Development"
            )
    
    def test_time_entry_create_request_invalid_hours(self):
        """Test time entry creation request with invalid hours."""
        with pytest.raises(ValidationError):
            TimeEntryCreateRequest(
                project_id=uuid4(),
                hours=Decimal('0.00'),
                work_date=date(2025, 1, 15),
                category="Development"
            )
        
        with pytest.raises(ValidationError):
            TimeEntryCreateRequest(
                project_id=uuid4(),
                hours=Decimal('25.00'),
                work_date=date(2025, 1, 15),
                category="Development"
            )
    
    def test_time_entry_update_request_valid(self):
        """Test valid time entry update request."""
        request = TimeEntryUpdateRequest(
            hours=Decimal('6.00'),
            category="Testing",
            notes="Updated notes"
        )
        
        assert request.hours == Decimal('6.00')
        assert request.category == "Testing"
        assert request.notes == "Updated notes"
    
    def test_time_entry_update_request_invalid_category(self):
        """Test time entry update request with invalid category."""
        with pytest.raises(ValueError, match="Category must be one of"):
            TimeEntryUpdateRequest(category="InvalidCategory")
    
    def test_time_entry_update_request_invalid_hours(self):
        """Test time entry update request with invalid hours."""
        with pytest.raises(ValidationError):
            TimeEntryUpdateRequest(hours=Decimal('0.00'))
        
        with pytest.raises(ValidationError):
            TimeEntryUpdateRequest(hours=Decimal('25.00')) 