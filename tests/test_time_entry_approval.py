"""
Tests for time entry approval functionality.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from uuid import uuid4

from app.services.time_entry_service import TimeEntryService
from app.schemas.time_entry import TimeEntryApprovalRequest, TimeEntryRejectionRequest
from app.models.time_entry import TimeEntry
from app.models.project import Project
from app.models.task import Task
from app.models.user import User


class TestTimeEntryApproval:
    """Test cases for time entry approval functionality."""
    
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
    def sample_approver(self):
        """Sample approver for testing."""
        approver = User(
            id=uuid4(),
            email="approver@example.com",
            first_name="Approver",
            last_name="User",
            password_hash="hashed_password",
            role="ProjectManager",
            is_active=True
        )
        return approver
    
    @pytest.fixture
    def sample_project(self, sample_approver):
        """Sample project for testing."""
        project = Project(
            id=uuid4(),
            name="Test Project",
            description="A test project",
            manager_id=sample_approver.id,
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
    def sample_approved_time_entry(self, sample_user, sample_project, sample_task, sample_approver):
        """Sample approved time entry for testing."""
        time_entry = TimeEntry(
            id=uuid4(),
            user_id=sample_user.id,
            task_id=sample_task.id,
            project_id=sample_project.id,
            hours=Decimal('8.00'),
            date=date(2025, 1, 15),
            category="Development",
            notes="Test time entry",
            is_approved=True,
            approved_by=sample_approver.id,
            approved_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        return time_entry
    
    def test_get_pending_time_entries_success(self, mock_db_session, sample_time_entry):
        """Test successful retrieval of pending time entries."""
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
        
        time_entries, pagination_info = TimeEntryService.get_pending_time_entries(
            mock_db_session,
            str(uuid4()),
            page=1,
            limit=20
        )
        
        assert len(time_entries) == 1
        assert time_entries[0] == sample_time_entry
        assert pagination_info["total"] == 1
        assert pagination_info["page"] == 1
        assert pagination_info["limit"] == 20
        mock_db_session.query.assert_called_once()
    
    def test_get_pending_time_entries_with_project_filter(self, mock_db_session, sample_time_entry):
        """Test pending time entries retrieval with project filter."""
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
        
        time_entries, pagination_info = TimeEntryService.get_pending_time_entries(
            mock_db_session,
            str(uuid4()),
            project_id=str(sample_time_entry.project_id),
            page=1,
            limit=20
        )
        
        assert len(time_entries) == 1
        assert time_entries[0] == sample_time_entry
        mock_db_session.query.assert_called_once()
    
    def test_get_approved_time_entries_success(self, mock_db_session, sample_approved_time_entry):
        """Test successful retrieval of approved time entries."""
        # Mock time entries query with proper chaining
        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_approved_time_entry]
        
        mock_db_session.query.return_value = mock_query
        
        time_entries, pagination_info = TimeEntryService.get_approved_time_entries(
            mock_db_session,
            page=1,
            limit=20
        )
        
        assert len(time_entries) == 1
        assert time_entries[0] == sample_approved_time_entry
        assert pagination_info["total"] == 1
        assert pagination_info["page"] == 1
        assert pagination_info["limit"] == 20
        mock_db_session.query.assert_called_once()
    
    def test_get_approved_time_entries_with_filters(self, mock_db_session, sample_approved_time_entry):
        """Test approved time entries retrieval with filters."""
        # Mock time entries query with proper chaining
        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_approved_time_entry]
        
        mock_db_session.query.return_value = mock_query
        
        time_entries, pagination_info = TimeEntryService.get_approved_time_entries(
            mock_db_session,
            user_id=str(sample_approved_time_entry.user_id),
            project_id=str(sample_approved_time_entry.project_id),
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            page=1,
            limit=20
        )
        
        assert len(time_entries) == 1
        assert time_entries[0] == sample_approved_time_entry
        mock_db_session.query.assert_called_once()
    
    def test_approve_time_entry_success(self, mock_db_session, sample_time_entry, sample_approver):
        """Test successful time entry approval."""
        # Mock time entry query
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = sample_time_entry
        
        mock_db_session.query.return_value = mock_query
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.return_value = None
        
        approval_notes = "Approved after review"
        
        result = TimeEntryService.approve_time_entry(
            mock_db_session,
            str(sample_time_entry.id),
            str(sample_approver.id),
            approval_notes
        )
        
        assert result == sample_time_entry
        assert sample_time_entry.is_approved is True
        assert str(sample_time_entry.approved_by) == str(sample_approver.id)
        assert sample_time_entry.approved_at is not None
        assert approval_notes in sample_time_entry.notes
        mock_db_session.commit.assert_called_once()
    
    def test_approve_time_entry_not_found(self, mock_db_session):
        """Test time entry approval when not found."""
        # Mock time entry query (not found)
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        
        mock_db_session.query.return_value = mock_query
        
        result = TimeEntryService.approve_time_entry(
            mock_db_session,
            str(uuid4()),
            str(uuid4()),
            "Approval notes"
        )
        
        assert result is None
        mock_db_session.query.assert_called_once()
    
    def test_approve_time_entry_already_approved(self, mock_db_session, sample_approved_time_entry):
        """Test approval of already approved time entry."""
        # Mock time entry query
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = sample_approved_time_entry
        
        mock_db_session.query.return_value = mock_query
        
        with pytest.raises(ValueError, match="Time entry is already approved"):
            TimeEntryService.approve_time_entry(
                mock_db_session,
                str(sample_approved_time_entry.id),
                str(uuid4()),
                "Approval notes"
            )
    
    def test_approve_time_entry_without_notes(self, mock_db_session, sample_time_entry, sample_approver):
        """Test time entry approval without notes."""
        # Mock time entry query
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = sample_time_entry
        
        mock_db_session.query.return_value = mock_query
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.return_value = None
        
        result = TimeEntryService.approve_time_entry(
            mock_db_session,
            str(sample_time_entry.id),
            str(sample_approver.id),
            None
        )
        
        assert result == sample_time_entry
        assert sample_time_entry.is_approved is True
        assert str(sample_time_entry.approved_by) == str(sample_approver.id)
        assert sample_time_entry.approved_at is not None
        mock_db_session.commit.assert_called_once()
    
    def test_reject_time_entry_success(self, mock_db_session, sample_time_entry, sample_approver):
        """Test successful time entry rejection."""
        # Mock time entry query
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = sample_time_entry
        
        mock_db_session.query.return_value = mock_query
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.return_value = None
        
        rejection_reason = "Insufficient details provided"
        
        result = TimeEntryService.reject_time_entry(
            mock_db_session,
            str(sample_time_entry.id),
            str(sample_approver.id),
            rejection_reason
        )
        
        assert result == sample_time_entry
        assert sample_time_entry.is_approved is False
        assert sample_time_entry.approved_by is None
        assert sample_time_entry.approved_at is None
        assert rejection_reason in sample_time_entry.notes
        mock_db_session.commit.assert_called_once()
    
    def test_reject_time_entry_not_found(self, mock_db_session):
        """Test time entry rejection when not found."""
        # Mock time entry query (not found)
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        
        mock_db_session.query.return_value = mock_query
        
        result = TimeEntryService.reject_time_entry(
            mock_db_session,
            str(uuid4()),
            str(uuid4()),
            "Rejection reason"
        )
        
        assert result is None
        mock_db_session.query.assert_called_once()
    
    def test_reject_time_entry_already_approved(self, mock_db_session, sample_approved_time_entry):
        """Test rejection of already approved time entry."""
        # Mock time entry query
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = sample_approved_time_entry
        
        mock_db_session.query.return_value = mock_query
        
        with pytest.raises(ValueError, match="Cannot reject an already approved time entry"):
            TimeEntryService.reject_time_entry(
                mock_db_session,
                str(sample_approved_time_entry.id),
                str(uuid4()),
                "Rejection reason"
            )
    
    def test_reject_time_entry_with_existing_notes(self, mock_db_session, sample_time_entry, sample_approver):
        """Test time entry rejection with existing notes."""
        # Set existing notes
        sample_time_entry.notes = "Original notes"
        
        # Mock time entry query
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = sample_time_entry
        
        mock_db_session.query.return_value = mock_query
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.return_value = None
        
        rejection_reason = "Insufficient details"
        
        result = TimeEntryService.reject_time_entry(
            mock_db_session,
            str(sample_time_entry.id),
            str(sample_approver.id),
            rejection_reason
        )
        
        assert result == sample_time_entry
        assert "Original notes" in sample_time_entry.notes
        assert rejection_reason in sample_time_entry.notes
        mock_db_session.commit.assert_called_once()
    
    def test_can_approve_time_entry(self, sample_time_entry):
        """Test approval permission check."""
        result = TimeEntryService.can_approve_time_entry(
            sample_time_entry,
            str(uuid4())
        )
        
        # Currently returns True for any user (TODO: implement proper role checking)
        assert result is True
    
    def test_can_reject_time_entry(self, sample_time_entry):
        """Test rejection permission check."""
        result = TimeEntryService.can_reject_time_entry(
            sample_time_entry,
            str(uuid4())
        )
        
        # Currently returns True for any user (TODO: implement proper role checking)
        assert result is True


class TestTimeEntryApprovalValidation:
    """Test cases for time entry approval validation."""
    
    def test_time_entry_approval_request_valid(self):
        """Test valid time entry approval request."""
        request = TimeEntryApprovalRequest(
            approval_notes="Approved after review"
        )
        
        assert request.approval_notes == "Approved after review"
    
    def test_time_entry_approval_request_no_notes(self):
        """Test time entry approval request without notes."""
        request = TimeEntryApprovalRequest(
            approval_notes=None
        )
        
        assert request.approval_notes is None
    
    def test_time_entry_rejection_request_valid(self):
        """Test valid time entry rejection request."""
        request = TimeEntryRejectionRequest(
            rejection_reason="Insufficient details provided"
        )
        
        assert request.rejection_reason == "Insufficient details provided"
    
    def test_time_entry_rejection_request_empty_reason(self):
        """Test time entry rejection request with empty reason."""
        with pytest.raises(ValueError):
            TimeEntryRejectionRequest(
                rejection_reason=""
            )
    
    def test_time_entry_rejection_request_long_reason(self):
        """Test time entry rejection request with very long reason."""
        long_reason = "x" * 501  # Exceeds max length of 500
        
        with pytest.raises(ValueError):
            TimeEntryRejectionRequest(
                rejection_reason=long_reason
            ) 