"""
Unit tests for time reports functionality.
"""
import pytest
from datetime import date, datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.services.reports_service import ReportsService
from app.schemas.reports import (
    TimeReportType,
    TimeReportResponse,
    TimeReportSummaryData,
    TimeReportByProjectData,
    TimeReportByCategoryData,
    TimeReportByUserData,
    TimeReportDailyData,
    ReportFormat
)
from app.models.time_entry import TimeEntry
from app.models.project import Project
from app.models.user import User
from app.models.task import Task
from app.core.auth import AuthUtils

client = TestClient(app)


class TestTimeReportsService:
    """Test cases for time reports service functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=Session)
        self.mock_user = Mock(spec=User)
        self.mock_user.id = "user-123"
        self.mock_user.name = "Test User"
        self.mock_user.role = "User"
        
        self.mock_project = Mock(spec=Project)
        self.mock_project.id = "project-123"
        self.mock_project.name = "Test Project"
        
        self.mock_task = Mock(spec=Task)
        self.mock_task.id = "task-123"
        self.mock_task.name = "Test Task"
        
        # Create mock time entries
        self.mock_time_entries = [
            Mock(spec=TimeEntry),
            Mock(spec=TimeEntry),
            Mock(spec=TimeEntry)
        ]
        
        # Configure mock time entries
        for i, entry in enumerate(self.mock_time_entries):
            entry.id = f"entry-{i+1}"
            entry.user_id = "user-123"
            entry.project_id = "project-123"
            entry.task_id = "task-123"
            entry.hours = 8.0
            entry.date = date(2024, 1, 1 + i)
            entry.category = "Development"
            entry.notes = f"Test entry {i+1}"
            entry.is_approved = True
            entry.user = self.mock_user
            entry.project = self.mock_project
            entry.task = self.mock_task
    
    def test_generate_general_time_report(self):
        """Test generating a general time report."""
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = self.mock_time_entries
        self.mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        
        # Generate report
        report = ReportsService._generate_general_time_report(
            self.mock_db,
            date(2024, 1, 1),
            date(2024, 1, 3),
            True
        )
        
        # Verify report structure
        assert isinstance(report, TimeReportResponse)
        assert report.report_type == TimeReportType.GENERAL
        assert report.period_start == date(2024, 1, 1)
        assert report.period_end == date(2024, 1, 3)
        assert report.summary.total_hours == 24.0
        assert report.summary.total_days == 3
        assert report.summary.total_entries == 3
        assert report.summary.approved_entries == 3
        assert report.summary.pending_entries == 0
        assert report.summary.approval_rate == 100.0
    
    def test_generate_user_time_report(self):
        """Test generating a user-specific time report."""
        # Mock database queries
        mock_user_query = Mock()
        mock_user_query.filter.return_value = mock_user_query
        mock_user_query.first.return_value = self.mock_user
        
        mock_time_query = Mock()
        mock_time_query.filter.return_value = mock_time_query
        mock_time_query.all.return_value = self.mock_time_entries
        mock_time_query.options.return_value = mock_time_query
        
        self.mock_db.query.side_effect = [mock_user_query, mock_time_query]
        
        # Generate report
        report = ReportsService._generate_user_time_report(
            self.mock_db,
            "user-123",
            date(2024, 1, 1),
            date(2024, 1, 3),
            True
        )
        
        # Verify report structure
        assert isinstance(report, TimeReportResponse)
        assert report.report_type == TimeReportType.BY_USER
        assert report.metadata["user_id"] == "user-123"
        assert report.summary.total_hours == 24.0
    
    def test_generate_project_time_report(self):
        """Test generating a project-specific time report."""
        # Mock database queries
        mock_project_query = Mock()
        mock_project_query.filter.return_value = mock_project_query
        mock_project_query.first.return_value = self.mock_project
        
        mock_time_query = Mock()
        mock_time_query.filter.return_value = mock_time_query
        mock_time_query.all.return_value = self.mock_time_entries
        mock_time_query.options.return_value = mock_time_query
        
        self.mock_db.query.side_effect = [mock_project_query, mock_time_query]
        
        # Generate report
        report = ReportsService._generate_project_time_report(
            self.mock_db,
            "project-123",
            date(2024, 1, 1),
            date(2024, 1, 3),
            True
        )
        
        # Verify report structure
        assert isinstance(report, TimeReportResponse)
        assert report.report_type == TimeReportType.BY_PROJECT
        assert report.metadata["project_id"] == "project-123"
        assert report.summary.total_hours == 24.0
    
    def test_get_time_report_summary(self):
        """Test generating time report summary data."""
        summary = ReportsService._get_time_report_summary(self.mock_time_entries)
        
        assert isinstance(summary, TimeReportSummaryData)
        assert summary.total_hours == 24.0
        assert summary.total_days == 3
        assert summary.average_hours_per_day == 8.0
        assert summary.total_entries == 3
        assert summary.approved_entries == 3
        assert summary.pending_entries == 0
        assert summary.approval_rate == 100.0
    
    def test_get_time_report_summary_empty(self):
        """Test generating time report summary with no entries."""
        summary = ReportsService._get_time_report_summary([])
        
        assert isinstance(summary, TimeReportSummaryData)
        assert summary.total_hours == 0.0
        assert summary.total_days == 0
        assert summary.average_hours_per_day == 0.0
        assert summary.total_entries == 0
        assert summary.approved_entries == 0
        assert summary.pending_entries == 0
        assert summary.approval_rate == 0.0
    
    def test_get_time_by_project(self):
        """Test generating time data grouped by project."""
        by_project = ReportsService._get_time_by_project(self.mock_time_entries)
        
        assert len(by_project) == 1
        assert isinstance(by_project[0], TimeReportByProjectData)
        assert by_project[0].project_id == "project-123"
        assert by_project[0].project_name == "Test Project"
        assert by_project[0].hours == 24.0
        assert by_project[0].percentage == 100.0
        assert by_project[0].entries_count == 3
        assert by_project[0].average_hours_per_entry == 8.0
    
    def test_get_time_by_category(self):
        """Test generating time data grouped by category."""
        by_category = ReportsService._get_time_by_category(self.mock_time_entries)
        
        assert len(by_category) == 1
        assert isinstance(by_category[0], TimeReportByCategoryData)
        assert by_category[0].category == "Development"
        assert by_category[0].hours == 24.0
        assert by_category[0].percentage == 100.0
        assert by_category[0].entries_count == 3
    
    def test_get_time_by_user(self):
        """Test generating time data grouped by user."""
        by_user = ReportsService._get_time_by_user(self.mock_time_entries)
        
        assert len(by_user) == 1
        assert isinstance(by_user[0], TimeReportByUserData)
        assert by_user[0].user_id == "user-123"
        assert by_user[0].user_name == "Test User"
        assert by_user[0].hours == 24.0
        assert by_user[0].percentage == 100.0
        assert by_user[0].entries_count == 3
        assert by_user[0].average_hours_per_day == 8.0
    
    def test_get_time_daily_breakdown(self):
        """Test generating daily breakdown of time entries."""
        daily_breakdown = ReportsService._get_time_daily_breakdown(self.mock_time_entries)
        
        assert len(daily_breakdown) == 3
        for i, daily in enumerate(daily_breakdown):
            assert isinstance(daily, TimeReportDailyData)
            assert daily.date == date(2024, 1, 1 + i)
            assert daily.hours == 8.0
            assert daily.entries_count == 1
            assert daily.projects_count == 1
    
    def test_export_time_report(self):
        """Test exporting a time report."""
        # Mock the generate_time_report method
        mock_report = Mock(spec=TimeReportResponse)
        mock_report.report_id = "report-123"
        mock_report.report_type = TimeReportType.GENERAL
        
        with patch.object(ReportsService, 'generate_time_report', return_value=mock_report):
            with patch('os.path.exists', return_value=False):
                with patch('os.makedirs'):
                    with patch('builtins.open', create=True) as mock_open:
                        mock_file = Mock()
                        mock_open.return_value.__enter__.return_value = mock_file
                        
                        export_response = ReportsService.export_time_report(
                            self.mock_db,
                            TimeReportType.GENERAL,
                            ReportFormat.JSON,
                            filename="test_report"
                        )
                        
                        assert export_response.export_id is not None
                        assert export_response.filename == "test_report.json"
                        assert export_response.format == ReportFormat.JSON
                        assert "test_report.json" in export_response.download_url
    
    def test_get_time_report_by_id(self):
        """Test retrieving a time report by ID."""
        # Create a test report
        test_report = Mock(spec=TimeReportResponse)
        test_report.report_id = "test-report-123"
        
        # Store it in the service
        ReportsService._generated_time_reports["test-report-123"] = test_report
        
        # Retrieve it
        retrieved_report = ReportsService.get_time_report_by_id("test-report-123")
        
        assert retrieved_report == test_report
        
        # Test non-existent report
        non_existent = ReportsService.get_time_report_by_id("non-existent")
        assert non_existent is None


class TestTimeReportsAPI:
    """Test cases for time reports API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_user = {
            "id": "user-123",
            "email": "test@example.com",
            "name": "Test User",
            "role": "User"
        }
        
        self.test_project = {
            "id": "project-123",
            "name": "Test Project",
            "description": "Test project description"
        }
        
        # Create access token
        self.access_token = AuthUtils.create_access_token(data={"sub": self.test_user["email"]})
        self.headers = {"Authorization": f"Bearer {self.access_token}"}
    
    @patch('app.api.reports.ReportsService.generate_time_report')
    def test_get_time_report_general(self, mock_generate_report):
        """Test GET /reports/time for general report."""
        # Mock the service response
        mock_report = Mock(spec=TimeReportResponse)
        mock_report.report_id = "report-123"
        mock_report.report_type = TimeReportType.GENERAL
        mock_generate_report.return_value = mock_report
        
        response = client.get(
            "/reports/time",
            headers=self.headers,
            params={"report_type": "general"}
        )
        
        assert response.status_code == 200
        mock_generate_report.assert_called_once()
    
    @patch('app.api.reports.ReportsService.generate_time_report')
    def test_get_time_report_by_user(self, mock_generate_report):
        """Test GET /reports/time/by-user."""
        # Mock the service response
        mock_report = Mock(spec=TimeReportResponse)
        mock_report.report_id = "report-123"
        mock_report.report_type = TimeReportType.BY_USER
        mock_generate_report.return_value = mock_report
        
        response = client.get(
            "/reports/time/by-user",
            headers=self.headers,
            params={"user_id": "user-123"}
        )
        
        assert response.status_code == 200
        mock_generate_report.assert_called_once()
    
    @patch('app.api.reports.ProjectService.get_project_by_id')
    @patch('app.api.reports.ProjectService.can_access_project')
    @patch('app.api.reports.ReportsService.generate_time_report')
    def test_get_time_report_by_project(self, mock_generate_report, mock_can_access, mock_get_project):
        """Test GET /reports/time/by-project."""
        # Mock project service responses
        mock_project = Mock()
        mock_project.id = "project-123"
        mock_get_project.return_value = mock_project
        mock_can_access.return_value = True
        
        # Mock the service response
        mock_report = Mock(spec=TimeReportResponse)
        mock_report.report_id = "report-123"
        mock_report.report_type = TimeReportType.BY_PROJECT
        mock_generate_report.return_value = mock_report
        
        response = client.get(
            "/reports/time/by-project",
            headers=self.headers,
            params={"project_id": "project-123"}
        )
        
        assert response.status_code == 200
        mock_generate_report.assert_called_once()
    
    @patch('app.api.reports.ReportsService.export_time_report')
    def test_export_time_report(self, mock_export_report):
        """Test POST /reports/time/export."""
        # Mock the service response
        mock_export_response = Mock(spec=TimeReportExportResponse)
        mock_export_response.export_id = "export-123"
        mock_export_response.filename = "test_report.json"
        mock_export_response.format = ReportFormat.JSON
        mock_export_report.return_value = mock_export_response
        
        export_request = {
            "report_type": "general",
            "format": "json",
            "include_charts": True
        }
        
        response = client.post(
            "/reports/time/export",
            headers=self.headers,
            json=export_request
        )
        
        assert response.status_code == 200
        mock_export_report.assert_called_once()
    
    def test_get_time_report_invalid_date_range(self):
        """Test GET /reports/time with invalid date range."""
        response = client.get(
            "/reports/time",
            headers=self.headers,
            params={
                "start_date": "2024-01-03",
                "end_date": "2024-01-01"
            }
        )
        
        assert response.status_code == 400
        assert "Start date cannot be after end date" in response.json()["detail"]
    
    def test_get_time_report_by_user_missing_user_id(self):
        """Test GET /reports/time/by-user with missing user_id."""
        response = client.get(
            "/reports/time/by-user",
            headers=self.headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_time_report_by_project_missing_project_id(self):
        """Test GET /reports/time/by-project with missing project_id."""
        response = client.get(
            "/reports/time/by-project",
            headers=self.headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_time_report_unauthorized(self):
        """Test GET /reports/time without authentication."""
        response = client.get("/reports/time")
        
        assert response.status_code == 401
    
    @patch('app.api.reports.ProjectService.get_project_by_id')
    def test_get_time_report_by_project_not_found(self, mock_get_project):
        """Test GET /reports/time/by-project with non-existent project."""
        mock_get_project.return_value = None
        
        response = client.get(
            "/reports/time/by-project",
            headers=self.headers,
            params={"project_id": "non-existent"}
        )
        
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]
    
    @patch('app.api.reports.ProjectService.get_project_by_id')
    @patch('app.api.reports.ProjectService.can_access_project')
    def test_get_time_report_by_project_forbidden(self, mock_can_access, mock_get_project):
        """Test GET /reports/time/by-project without access permission."""
        mock_project = Mock()
        mock_project.id = "project-123"
        mock_get_project.return_value = mock_project
        mock_can_access.return_value = False
        
        response = client.get(
            "/reports/time/by-project",
            headers=self.headers,
            params={"project_id": "project-123"}
        )
        
        assert response.status_code == 403
        assert "Not authorized to access this project's time report" in response.json()["detail"]


class TestTimeReportsValidation:
    """Test cases for time reports validation."""
    
    def test_time_report_request_validation(self):
        """Test TimeReportRequest validation."""
        from app.schemas.reports import TimeReportRequest
        
        # Valid request
        valid_request = TimeReportRequest(
            report_type=TimeReportType.GENERAL,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        assert valid_request.report_type == TimeReportType.GENERAL
        
        # Invalid date range
        with pytest.raises(ValueError, match="End date must be after start date"):
            TimeReportRequest(
                report_type=TimeReportType.GENERAL,
                start_date=date(2024, 1, 31),
                end_date=date(2024, 1, 1)
            )
        
        # Missing user_id for user report
        with pytest.raises(ValueError, match="user_id is required for user-specific time reports"):
            TimeReportRequest(
                report_type=TimeReportType.BY_USER,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31)
            )
        
        # Missing project_id for project report
        with pytest.raises(ValueError, match="project_id is required for project-specific time reports"):
            TimeReportRequest(
                report_type=TimeReportType.BY_PROJECT,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31)
            )
    
    def test_time_report_export_request_validation(self):
        """Test TimeReportExportRequest validation."""
        from app.schemas.reports import TimeReportExportRequest
        
        # Valid request
        valid_request = TimeReportExportRequest(
            report_type=TimeReportType.GENERAL,
            format=ReportFormat.JSON,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        assert valid_request.report_type == TimeReportType.GENERAL
        assert valid_request.format == ReportFormat.JSON
        
        # Invalid date range
        with pytest.raises(ValueError, match="End date must be after start date"):
            TimeReportExportRequest(
                report_type=TimeReportType.GENERAL,
                format=ReportFormat.JSON,
                start_date=date(2024, 1, 31),
                end_date=date(2024, 1, 1)
            )
        
        # Missing user_id for user report
        with pytest.raises(ValueError, match="user_id is required for user-specific time reports"):
            TimeReportExportRequest(
                report_type=TimeReportType.BY_USER,
                format=ReportFormat.JSON,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31)
            )
        
        # Missing project_id for project report
        with pytest.raises(ValueError, match="project_id is required for project-specific time reports"):
            TimeReportExportRequest(
                report_type=TimeReportType.BY_PROJECT,
                format=ReportFormat.JSON,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31)
            )


class TestTimeReportsEdgeCases:
    """Test cases for time reports edge cases."""
    
    def test_time_report_with_mixed_approval_status(self):
        """Test time report with mixed approval status."""
        # Create time entries with mixed approval status
        mock_entries = []
        for i in range(4):
            entry = Mock(spec=TimeEntry)
            entry.hours = 8.0
            entry.date = date(2024, 1, 1 + i)
            entry.is_approved = i < 2  # First 2 approved, last 2 pending
            entry.user = Mock()
            entry.user.name = "Test User"
            entry.project = Mock()
            entry.project.name = "Test Project"
            entry.category = "Development"
            mock_entries.append(entry)
        
        summary = ReportsService._get_time_report_summary(mock_entries)
        
        assert summary.total_hours == 32.0
        assert summary.total_entries == 4
        assert summary.approved_entries == 2
        assert summary.pending_entries == 2
        assert summary.approval_rate == 50.0
    
    def test_time_report_with_multiple_categories(self):
        """Test time report with multiple categories."""
        # Create time entries with different categories
        mock_entries = []
        categories = ["Development", "Testing", "Documentation"]
        
        for i, category in enumerate(categories):
            entry = Mock(spec=TimeEntry)
            entry.hours = 8.0
            entry.date = date(2024, 1, 1 + i)
            entry.is_approved = True
            entry.category = category
            entry.user = Mock()
            entry.user.name = "Test User"
            entry.project = Mock()
            entry.project.name = "Test Project"
            mock_entries.append(entry)
        
        by_category = ReportsService._get_time_by_category(mock_entries)
        
        assert len(by_category) == 3
        for category_data in by_category:
            assert category_data.hours == 8.0
            assert category_data.percentage == 33.33  # Approximately
            assert category_data.entries_count == 1
    
    def test_time_report_with_multiple_projects(self):
        """Test time report with multiple projects."""
        # Create time entries for different projects
        mock_entries = []
        projects = [
            ("project-1", "Project A"),
            ("project-2", "Project B"),
            ("project-3", "Project C")
        ]
        
        for i, (project_id, project_name) in enumerate(projects):
            entry = Mock(spec=TimeEntry)
            entry.hours = 8.0
            entry.date = date(2024, 1, 1 + i)
            entry.is_approved = True
            entry.project_id = project_id
            entry.project = Mock()
            entry.project.name = project_name
            entry.user = Mock()
            entry.user.name = "Test User"
            entry.category = "Development"
            mock_entries.append(entry)
        
        by_project = ReportsService._get_time_by_project(mock_entries)
        
        assert len(by_project) == 3
        for project_data in by_project:
            assert project_data.hours == 8.0
            assert project_data.percentage == 33.33  # Approximately
            assert project_data.entries_count == 1
    
    def test_time_report_with_same_date_entries(self):
        """Test time report with multiple entries on the same date."""
        # Create multiple entries for the same date
        mock_entries = []
        for i in range(3):
            entry = Mock(spec=TimeEntry)
            entry.hours = 4.0
            entry.date = date(2024, 1, 1)  # Same date
            entry.is_approved = True
            entry.user = Mock()
            entry.user.name = "Test User"
            entry.project = Mock()
            entry.project.name = "Test Project"
            entry.category = "Development"
            mock_entries.append(entry)
        
        summary = ReportsService._get_time_report_summary(mock_entries)
        daily_breakdown = ReportsService._get_time_daily_breakdown(mock_entries)
        
        assert summary.total_hours == 12.0
        assert summary.total_days == 1  # Only one unique date
        assert summary.average_hours_per_day == 12.0
        
        assert len(daily_breakdown) == 1
        assert daily_breakdown[0].date == date(2024, 1, 1)
        assert daily_breakdown[0].hours == 12.0
        assert daily_breakdown[0].entries_count == 3 