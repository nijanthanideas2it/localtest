"""
Tests for time analytics functionality.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from uuid import uuid4

from app.services.time_entry_service import TimeEntryService
from app.models.time_entry import TimeEntry
from app.models.project import Project
from app.models.task import Task
from app.models.user import User


class TestTimeAnalytics:
    """Test cases for time analytics functionality."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return MagicMock()
    
    @pytest.fixture
    def sample_user(self):
        """Sample user for testing."""
        return User(
            id=uuid4(),
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password_hash="hashed_password",
            role="Developer",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    @pytest.fixture
    def sample_project(self):
        """Sample project for testing."""
        return Project(
            id=uuid4(),
            name="Test Project",
            description="Test project description",
            status="active",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    @pytest.fixture
    def sample_task(self):
        """Sample task for testing."""
        return Task(
            id=uuid4(),
            title="Test Task",
            description="Test task description",
            status="in_progress",
            priority="medium",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    @pytest.fixture
    def sample_time_entries(self, sample_user, sample_project, sample_task):
        """Sample time entries for testing."""
        entries = []
        base_date = date(2025, 1, 1)
        
        # Create entries for different days and categories
        for i in range(10):
            entry = TimeEntry(
                id=uuid4(),
                user_id=sample_user.id,
                project_id=sample_project.id,
                task_id=sample_task.id if i % 2 == 0 else None,
                hours=Decimal('8.00'),
                date=base_date + timedelta(days=i),
                category="Development" if i % 3 == 0 else "Testing" if i % 3 == 1 else "Documentation",
                notes=f"Test entry {i}",
                is_approved=i < 7,  # 7 approved, 3 pending
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            entries.append(entry)
        
        return entries
    
    def test_get_time_analytics_success(self, mock_db_session, sample_time_entries):
        """Test successful time analytics retrieval."""
        # Mock time entries query
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_time_entries
        
        mock_db_session.query.return_value = mock_query
        
        result = TimeEntryService.get_time_analytics(
            mock_db_session,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 10)
        )
        
        assert result["total_hours"] == Decimal('80.00')  # 10 entries * 8 hours
        assert result["total_entries"] == 10
        assert result["average_hours_per_entry"] == Decimal('8.00')
        assert result["entries_by_status"]["approved"] == 7
        assert result["entries_by_status"]["pending"] == 3
        assert len(result["top_productive_days"]) == 10
        assert len(result["weekly_trends"]) > 0
        assert len(result["monthly_summary"]) > 0
    
    def test_get_time_analytics_empty_data(self, mock_db_session):
        """Test time analytics with no data."""
        # Mock empty time entries query
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db_session.query.return_value = mock_query
        
        result = TimeEntryService.get_time_analytics(mock_db_session)
        
        assert result["total_hours"] == Decimal('0.00')
        assert result["total_entries"] == 0
        assert result["average_hours_per_day"] == Decimal('0.00')
        assert result["average_hours_per_entry"] == Decimal('0.00')
        assert result["entries_by_status"]["approved"] == 0
        assert result["entries_by_status"]["pending"] == 0
        assert len(result["top_productive_days"]) == 0
        assert len(result["weekly_trends"]) == 0
        assert len(result["monthly_summary"]) == 0
    
    def test_get_time_analytics_with_filters(self, mock_db_session, sample_time_entries):
        """Test time analytics with user and project filters."""
        # Mock time entries query with filters
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_time_entries[:5]  # Return first 5 entries
        
        mock_db_session.query.return_value = mock_query
        
        result = TimeEntryService.get_time_analytics(
            mock_db_session,
            user_id=str(uuid4()),
            project_id=str(uuid4())
        )
        
        assert result["total_hours"] == Decimal('40.00')  # 5 entries * 8 hours
        assert result["total_entries"] == 5
    
    def test_generate_time_report_daily(self, mock_db_session, sample_time_entries):
        """Test daily report generation."""
        # Mock time entries query
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_time_entries
        
        mock_db_session.query.return_value = mock_query
        
        result = TimeEntryService.generate_time_report(
            mock_db_session,
            report_type="daily",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 10)
        )
        
        assert result["report_type"] == "daily"
        assert result["report_id"] is not None
        assert result["generated_at"] is not None
        assert len(result["detailed_data"]) == 10
        assert result["summary"]["total_hours"] == 80.0
        assert result["summary"]["total_entries"] == 10
    
    def test_generate_time_report_weekly(self, mock_db_session, sample_time_entries):
        """Test weekly report generation."""
        # Mock time entries query
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_time_entries
        
        mock_db_session.query.return_value = mock_query
        
        result = TimeEntryService.generate_time_report(
            mock_db_session,
            report_type="weekly"
        )
        
        assert result["report_type"] == "weekly"
        assert result["report_id"] is not None
        assert len(result["detailed_data"]) > 0
        assert "total_weeks" in result["summary"]
    
    def test_generate_time_report_monthly(self, mock_db_session, sample_time_entries):
        """Test monthly report generation."""
        # Mock time entries query
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_time_entries
        
        mock_db_session.query.return_value = mock_query
        
        result = TimeEntryService.generate_time_report(
            mock_db_session,
            report_type="monthly"
        )
        
        assert result["report_type"] == "monthly"
        assert result["report_id"] is not None
        assert len(result["detailed_data"]) > 0
        assert "total_months" in result["summary"]
    
    def test_generate_time_report_general(self, mock_db_session, sample_time_entries):
        """Test general report generation."""
        # Mock time entries query
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_time_entries
        
        mock_db_session.query.return_value = mock_query
        
        result = TimeEntryService.generate_time_report(
            mock_db_session,
            report_type="general"
        )
        
        assert result["report_type"] == "general"
        assert result["report_id"] is not None
        assert len(result["detailed_data"]) == 10
        assert result["summary"]["approval_rate"] == 70.0  # 7 approved out of 10
    
    def test_get_time_summary_current_month(self, mock_db_session, sample_time_entries):
        """Test time summary for current month."""
        # Mock time entries query
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_time_entries
        
        mock_db_session.query.return_value = mock_query
        
        result = TimeEntryService.get_time_summary(
            mock_db_session,
            period="current_month"
        )
        
        assert result["period"] == "current_month"
        assert result["total_hours"] == Decimal('80.00')
        assert result["total_entries"] == 10
        assert result["approved_hours"] == Decimal('56.00')  # 7 entries * 8 hours
        assert result["pending_hours"] == Decimal('24.00')   # 3 entries * 8 hours
        assert result["rejected_hours"] == Decimal('0.00')
        assert result["completion_rate"] == Decimal('70.00')  # 70% approval rate
    
    def test_get_time_summary_current_week(self, mock_db_session, sample_time_entries):
        """Test time summary for current week."""
        # Mock time entries query
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_time_entries[:7]  # First 7 entries
        
        mock_db_session.query.return_value = mock_query
        
        result = TimeEntryService.get_time_summary(
            mock_db_session,
            period="current_week"
        )
        
        assert result["period"] == "current_week"
        assert result["total_hours"] == Decimal('56.00')  # 7 entries * 8 hours
        assert result["total_entries"] == 7
    
    def test_get_time_summary_current_year(self, mock_db_session, sample_time_entries):
        """Test time summary for current year."""
        # Mock time entries query
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_time_entries
        
        mock_db_session.query.return_value = mock_query
        
        result = TimeEntryService.get_time_summary(
            mock_db_session,
            period="current_year"
        )
        
        assert result["period"] == "current_year"
        assert result["total_hours"] == Decimal('80.00')
        assert result["total_entries"] == 10
    
    def test_get_time_summary_all_time(self, mock_db_session, sample_time_entries):
        """Test time summary for all time."""
        # Mock time entries query
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_time_entries
        
        mock_db_session.query.return_value = mock_query
        
        result = TimeEntryService.get_time_summary(
            mock_db_session,
            period="all_time"
        )
        
        assert result["period"] == "all_time"
        assert result["total_hours"] == Decimal('80.00')
        assert result["total_entries"] == 10
    
    def test_get_time_summary_empty_data(self, mock_db_session):
        """Test time summary with no data."""
        # Mock empty time entries query
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db_session.query.return_value = mock_query
        
        result = TimeEntryService.get_time_summary(
            mock_db_session,
            period="current_month"
        )
        
        assert result["period"] == "current_month"
        assert result["total_hours"] == Decimal('0.00')
        assert result["total_entries"] == 0
        assert result["approved_hours"] == Decimal('0.00')
        assert result["pending_hours"] == Decimal('0.00')
        assert result["rejected_hours"] == Decimal('0.00')
        assert result["completion_rate"] == Decimal('0.00')
        assert result["most_productive_category"] == "N/A"
        assert result["most_productive_project"] == "N/A"
    
    def test_analytics_hours_by_category(self, mock_db_session, sample_time_entries):
        """Test hours by category calculation."""
        # Mock time entries query
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_time_entries
        
        mock_db_session.query.return_value = mock_query
        
        result = TimeEntryService.get_time_analytics(mock_db_session)
        
        # Check that hours by category is calculated correctly
        hours_by_category = result["hours_by_category"]
        assert "Development" in hours_by_category
        assert "Testing" in hours_by_category
        assert "Documentation" in hours_by_category
        
        # Total should equal total hours
        total_category_hours = sum(hours_by_category.values())
        assert total_category_hours == result["total_hours"]
    
    def test_analytics_hours_by_project(self, mock_db_session, sample_time_entries):
        """Test hours by project calculation."""
        # Mock time entries query
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_time_entries
        
        mock_db_session.query.return_value = mock_query
        
        result = TimeEntryService.get_time_analytics(mock_db_session)
        
        # Check that hours by project is calculated correctly
        hours_by_project = result["hours_by_project"]
        assert len(hours_by_project) == 1  # All entries have same project
        
        # Total should equal total hours
        total_project_hours = sum(hours_by_project.values())
        assert total_project_hours == result["total_hours"]
    
    def test_analytics_top_productive_days(self, mock_db_session, sample_time_entries):
        """Test top productive days calculation."""
        # Mock time entries query
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_time_entries
        
        mock_db_session.query.return_value = mock_query
        
        result = TimeEntryService.get_time_analytics(mock_db_session)
        
        # Check that top productive days is calculated correctly
        top_productive_days = result["top_productive_days"]
        assert len(top_productive_days) == 10  # All 10 days
        
        # Days should be sorted by hours (descending)
        for i in range(len(top_productive_days) - 1):
            assert top_productive_days[i]["hours"] >= top_productive_days[i + 1]["hours"]
        
        # Each day should have 8 hours and 1 entry
        for day in top_productive_days:
            assert day["hours"] == Decimal('8.00')
            assert day["entries"] == 1 