"""
Unit tests for performance reports functionality.
"""
import pytest
from datetime import date, datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.services.reports_service import ReportsService
from app.schemas.reports import (
    PerformanceReportType,
    PerformanceReportResponse,
    PerformanceSummaryData,
    IndividualPerformanceData,
    TeamPerformanceData,
    PerformanceMetricsData,
    ReportFormat
)
from app.models.task import Task
from app.models.project import Project
from app.models.user import User
from app.models.time_entry import TimeEntry
from app.core.auth import AuthUtils

client = TestClient(app)


class TestPerformanceReportsService:
    """Test cases for performance reports service functionality."""
    
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
        self.mock_task.status = "completed"
        self.mock_task.created_at = datetime.now(timezone.utc)
        self.mock_task.completed_at = datetime.now(timezone.utc)
        self.mock_task.due_date = date.today()
        self.mock_task.project_id = "project-123"
        
        self.mock_time_entry = Mock(spec=TimeEntry)
        self.mock_time_entry.id = "entry-123"
        self.mock_time_entry.hours = 8.0
        self.mock_time_entry.date = date.today()
        self.mock_time_entry.category = "Development"
        self.mock_time_entry.project_id = "project-123"
        self.mock_time_entry.is_approved = True
        
        # Configure mock user with tasks and time entries
        self.mock_user.tasks = [self.mock_task]
        self.mock_user.time_entries = [self.mock_time_entry]
    
    def test_generate_general_performance_report(self):
        """Test generating a general performance report."""
        # Mock database query
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.all.return_value = [self.mock_user]
        self.mock_db.query.return_value = mock_query
        
        # Generate report
        report = ReportsService._generate_general_performance_report(
            self.mock_db,
            date(2024, 1, 1),
            date(2024, 1, 31),
            True
        )
        
        # Verify report structure
        assert isinstance(report, PerformanceReportResponse)
        assert report.report_type == PerformanceReportType.GENERAL
        assert report.period_start == date(2024, 1, 1)
        assert report.period_end == date(2024, 1, 31)
        assert report.summary.total_users == 1
        assert report.summary.active_users == 1
        assert report.summary.total_tasks_completed == 1
        assert report.summary.total_time_logged == 8.0
        assert report.summary.average_completion_rate == 100.0
    
    def test_generate_individual_performance_report(self):
        """Test generating an individual performance report."""
        # Mock database queries
        mock_user_query = Mock()
        mock_user_query.options.return_value = mock_user_query
        mock_user_query.filter.return_value = mock_user_query
        mock_user_query.first.return_value = self.mock_user
        
        self.mock_db.query.return_value = mock_user_query
        
        # Generate report
        report = ReportsService._generate_individual_performance_report(
            self.mock_db,
            "user-123",
            date(2024, 1, 1),
            date(2024, 1, 31),
            True
        )
        
        # Verify report structure
        assert isinstance(report, PerformanceReportResponse)
        assert report.report_type == PerformanceReportType.INDIVIDUAL
        assert report.metadata["user_id"] == "user-123"
        assert report.summary.total_users == 1
        assert report.summary.total_tasks_completed == 1
    
    def test_generate_team_performance_report(self):
        """Test generating a team performance report."""
        # Mock database query
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.all.return_value = [self.mock_user]
        self.mock_db.query.return_value = mock_query
        
        # Generate report
        report = ReportsService._generate_team_performance_report(
            self.mock_db,
            date(2024, 1, 1),
            date(2024, 1, 31),
            True
        )
        
        # Verify report structure
        assert isinstance(report, PerformanceReportResponse)
        assert report.report_type == PerformanceReportType.TEAM
        assert report.summary.total_users == 1
        assert report.team_performance is not None
        assert report.team_performance.team_size == 1
    
    def test_get_performance_summary(self):
        """Test generating performance summary data."""
        summary = ReportsService._get_performance_summary([self.mock_user], date(2024, 1, 1), date(2024, 1, 31))
        
        assert isinstance(summary, PerformanceSummaryData)
        assert summary.total_users == 1
        assert summary.active_users == 1
        assert summary.total_tasks_completed == 1
        assert summary.total_time_logged == 8.0
        assert summary.average_completion_rate == 100.0
        assert summary.average_time_per_task == 8.0
        assert summary.top_performers_count == 1
        assert summary.improvement_areas_count == 0
    
    def test_get_performance_summary_empty(self):
        """Test generating performance summary with no users."""
        summary = ReportsService._get_performance_summary([], date(2024, 1, 1), date(2024, 1, 31))
        
        assert isinstance(summary, PerformanceSummaryData)
        assert summary.total_users == 0
        assert summary.active_users == 0
        assert summary.total_tasks_completed == 0
        assert summary.total_time_logged == 0.0
        assert summary.average_completion_rate == 0.0
        assert summary.average_time_per_task == 0.0
        assert summary.top_performers_count == 0
        assert summary.improvement_areas_count == 0
    
    def test_get_individual_performances(self):
        """Test generating individual performance data."""
        individual_performances = ReportsService._get_individual_performances([self.mock_user], date(2024, 1, 1), date(2024, 1, 31))
        
        assert len(individual_performances) == 1
        assert isinstance(individual_performances[0], IndividualPerformanceData)
        assert individual_performances[0].user == self.mock_user
        assert individual_performances[0].tasks_assigned == 1
        assert individual_performances[0].tasks_completed == 1
        assert individual_performances[0].completion_rate == 100.0
        assert individual_performances[0].total_time_logged == 8.0
        assert individual_performances[0].performance_score > 0
    
    def test_get_team_performance(self):
        """Test generating team performance data."""
        team_performance = ReportsService._get_team_performance([self.mock_user], date(2024, 1, 1), date(2024, 1, 31))
        
        assert isinstance(team_performance, TeamPerformanceData)
        assert team_performance.team_size == 1
        assert team_performance.total_tasks == 1
        assert team_performance.completed_tasks == 1
        assert team_performance.team_completion_rate == 100.0
        assert team_performance.average_performance_score > 0
        assert team_performance.collaboration_score == 75.0
        assert len(team_performance.top_performers) == 1
        assert len(team_performance.improvement_areas) == 0
    
    def test_get_performance_metrics(self):
        """Test generating performance metrics."""
        performance_metrics = ReportsService._get_performance_metrics([self.mock_user], date(2024, 1, 1), date(2024, 1, 31))
        
        assert isinstance(performance_metrics, PerformanceMetricsData)
        assert performance_metrics.productivity_score > 0
        assert performance_metrics.efficiency_score > 0
        assert performance_metrics.quality_score == 85.0
        assert performance_metrics.reliability_score == 90.0
        assert performance_metrics.collaboration_score == 80.0
        assert performance_metrics.innovation_score == 75.0
    
    def test_export_performance_report(self):
        """Test exporting a performance report."""
        # Mock the generate_performance_report method
        mock_report = Mock(spec=PerformanceReportResponse)
        mock_report.report_id = "report-123"
        mock_report.report_type = PerformanceReportType.GENERAL
        
        with patch.object(ReportsService, 'generate_performance_report', return_value=mock_report):
            with patch('os.path.exists', return_value=False):
                with patch('os.makedirs'):
                    with patch('builtins.open', create=True) as mock_open:
                        mock_file = Mock()
                        mock_open.return_value.__enter__.return_value = mock_file
                        
                        export_response = ReportsService.export_performance_report(
                            self.mock_db,
                            PerformanceReportType.GENERAL,
                            ReportFormat.JSON,
                            filename="test_report"
                        )
                        
                        assert export_response.export_id is not None
                        assert export_response.filename == "test_report.json"
                        assert export_response.format == ReportFormat.JSON
                        assert "test_report.json" in export_response.download_url
    
    def test_get_performance_report_by_id(self):
        """Test retrieving a performance report by ID."""
        # Create a test report
        test_report = Mock(spec=PerformanceReportResponse)
        test_report.report_id = "test-report-123"
        
        # Store it in the service
        ReportsService._generated_performance_reports["test-report-123"] = test_report
        
        # Retrieve it
        retrieved_report = ReportsService.get_performance_report_by_id("test-report-123")
        
        assert retrieved_report == test_report
        
        # Test non-existent report
        non_existent = ReportsService.get_performance_report_by_id("non-existent")
        assert non_existent is None


class TestPerformanceReportsAPI:
    """Test cases for performance reports API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_user = {
            "id": "user-123",
            "email": "test@example.com",
            "name": "Test User",
            "role": "User"
        }
        
        # Create access token
        self.access_token = AuthUtils.create_access_token(data={"sub": self.test_user["email"]})
        self.headers = {"Authorization": f"Bearer {self.access_token}"}
    
    @patch('app.api.reports.ReportsService.generate_performance_report')
    def test_get_performance_report_general(self, mock_generate_report):
        """Test GET /reports/performance for general report."""
        # Mock the service response
        mock_report = Mock(spec=PerformanceReportResponse)
        mock_report.report_id = "report-123"
        mock_report.report_type = PerformanceReportType.GENERAL
        mock_generate_report.return_value = mock_report
        
        response = client.get(
            "/reports/performance",
            headers=self.headers,
            params={"report_type": "general"}
        )
        
        assert response.status_code == 200
        mock_generate_report.assert_called_once()
    
    @patch('app.api.reports.ReportsService.generate_performance_report')
    def test_get_individual_performance_report(self, mock_generate_report):
        """Test GET /reports/performance/{user_id}."""
        # Mock the service response
        mock_report = Mock(spec=PerformanceReportResponse)
        mock_report.report_id = "report-123"
        mock_report.report_type = PerformanceReportType.INDIVIDUAL
        mock_generate_report.return_value = mock_report
        
        response = client.get(
            "/reports/performance/user-123",
            headers=self.headers
        )
        
        assert response.status_code == 200
        mock_generate_report.assert_called_once()
    
    @patch('app.api.reports.ReportsService.generate_performance_report')
    def test_get_team_performance_report(self, mock_generate_report):
        """Test GET /reports/performance/team."""
        # Mock the service response
        mock_report = Mock(spec=PerformanceReportResponse)
        mock_report.report_id = "report-123"
        mock_report.report_type = PerformanceReportType.TEAM
        mock_generate_report.return_value = mock_report
        
        response = client.get(
            "/reports/performance/team",
            headers=self.headers
        )
        
        assert response.status_code == 200
        mock_generate_report.assert_called_once()
    
    @patch('app.api.reports.ReportsService.export_performance_report')
    def test_export_performance_report(self, mock_export_report):
        """Test POST /reports/performance/export."""
        # Mock the service response
        mock_export_response = Mock(spec=PerformanceReportExportResponse)
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
            "/reports/performance/export",
            headers=self.headers,
            json=export_request
        )
        
        assert response.status_code == 200
        mock_export_report.assert_called_once()
    
    def test_get_performance_report_invalid_date_range(self):
        """Test GET /reports/performance with invalid date range."""
        response = client.get(
            "/reports/performance",
            headers=self.headers,
            params={
                "start_date": "2024-01-31",
                "end_date": "2024-01-01"
            }
        )
        
        assert response.status_code == 400
        assert "Start date cannot be after end date" in response.json()["detail"]
    
    def test_get_individual_performance_report_missing_user_id(self):
        """Test GET /reports/performance with missing user_id for individual report."""
        response = client.get(
            "/reports/performance",
            headers=self.headers,
            params={"report_type": "individual"}
        )
        
        assert response.status_code == 400
        assert "user_id is required for individual performance reports" in response.json()["detail"]
    
    def test_get_performance_report_unauthorized(self):
        """Test GET /reports/performance without authentication."""
        response = client.get("/reports/performance")
        
        assert response.status_code == 401
    
    def test_get_team_performance_report_unauthorized(self):
        """Test GET /reports/performance/team without proper role."""
        # Create a regular user token
        regular_user_token = AuthUtils.create_access_token(data={"sub": "regular@example.com"})
        regular_headers = {"Authorization": f"Bearer {regular_user_token}"}
        
        response = client.get(
            "/reports/performance/team",
            headers=regular_headers
        )
        
        assert response.status_code == 403


class TestPerformanceReportsValidation:
    """Test cases for performance reports validation."""
    
    def test_performance_report_request_validation(self):
        """Test PerformanceReportRequest validation."""
        from app.schemas.reports import PerformanceReportRequest
        
        # Valid request
        valid_request = PerformanceReportRequest(
            report_type=PerformanceReportType.GENERAL,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        assert valid_request.report_type == PerformanceReportType.GENERAL
        
        # Invalid date range
        with pytest.raises(ValueError, match="End date must be after start date"):
            PerformanceReportRequest(
                report_type=PerformanceReportType.GENERAL,
                start_date=date(2024, 1, 31),
                end_date=date(2024, 1, 1)
            )
        
        # Missing user_id for individual report
        with pytest.raises(ValueError, match="user_id is required for individual performance reports"):
            PerformanceReportRequest(
                report_type=PerformanceReportType.INDIVIDUAL,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31)
            )
    
    def test_performance_report_export_request_validation(self):
        """Test PerformanceReportExportRequest validation."""
        from app.schemas.reports import PerformanceReportExportRequest
        
        # Valid request
        valid_request = PerformanceReportExportRequest(
            report_type=PerformanceReportType.GENERAL,
            format=ReportFormat.JSON,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        assert valid_request.report_type == PerformanceReportType.GENERAL
        assert valid_request.format == ReportFormat.JSON
        
        # Invalid date range
        with pytest.raises(ValueError, match="End date must be after start date"):
            PerformanceReportExportRequest(
                report_type=PerformanceReportType.GENERAL,
                format=ReportFormat.JSON,
                start_date=date(2024, 1, 31),
                end_date=date(2024, 1, 1)
            )
        
        # Missing user_id for individual report
        with pytest.raises(ValueError, match="user_id is required for individual performance reports"):
            PerformanceReportExportRequest(
                report_type=PerformanceReportType.INDIVIDUAL,
                format=ReportFormat.JSON,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31)
            )


class TestPerformanceReportsEdgeCases:
    """Test cases for performance reports edge cases."""
    
    def test_performance_report_with_mixed_task_statuses(self):
        """Test performance report with mixed task statuses."""
        # Create users with different task statuses
        user1 = Mock(spec=User)
        user1.id = "user-1"
        user1.name = "User 1"
        user1.role = "User"
        
        task1 = Mock(spec=Task)
        task1.status = "completed"
        task1.created_at = datetime.now(timezone.utc)
        task1.completed_at = datetime.now(timezone.utc)
        task1.due_date = date.today()
        task1.project_id = "project-1"
        
        task2 = Mock(spec=Task)
        task2.status = "in_progress"
        task2.created_at = datetime.now(timezone.utc)
        task2.completed_at = None
        task2.due_date = date.today() + timedelta(days=7)
        task2.project_id = "project-1"
        
        user1.tasks = [task1, task2]
        user1.time_entries = []
        
        summary = ReportsService._get_performance_summary([user1], date(2024, 1, 1), date(2024, 1, 31))
        
        assert summary.total_users == 1
        assert summary.active_users == 1
        assert summary.total_tasks_completed == 1
        assert summary.average_completion_rate == 50.0
    
    def test_performance_report_with_overdue_tasks(self):
        """Test performance report with overdue tasks."""
        # Create user with overdue task
        user = Mock(spec=User)
        user.id = "user-1"
        user.name = "User 1"
        user.role = "User"
        
        overdue_task = Mock(spec=Task)
        overdue_task.status = "in_progress"
        overdue_task.created_at = datetime.now(timezone.utc)
        overdue_task.completed_at = None
        overdue_task.due_date = date.today() - timedelta(days=7)  # Overdue
        overdue_task.project_id = "project-1"
        
        user.tasks = [overdue_task]
        user.time_entries = []
        
        individual_performances = ReportsService._get_individual_performances([user], date(2024, 1, 1), date(2024, 1, 31))
        
        assert len(individual_performances) == 1
        assert individual_performances[0].tasks_overdue == 1
        assert individual_performances[0].completion_rate == 0.0
    
    def test_performance_report_with_multiple_users(self):
        """Test performance report with multiple users."""
        # Create multiple users
        users = []
        for i in range(3):
            user = Mock(spec=User)
            user.id = f"user-{i+1}"
            user.name = f"User {i+1}"
            user.role = "User"
            
            task = Mock(spec=Task)
            task.status = "completed"
            task.created_at = datetime.now(timezone.utc)
            task.completed_at = datetime.now(timezone.utc)
            task.due_date = date.today()
            task.project_id = f"project-{i+1}"
            
            time_entry = Mock(spec=TimeEntry)
            time_entry.hours = 8.0
            time_entry.date = date.today()
            time_entry.category = "Development"
            time_entry.project_id = f"project-{i+1}"
            time_entry.is_approved = True
            
            user.tasks = [task]
            user.time_entries = [time_entry]
            users.append(user)
        
        summary = ReportsService._get_performance_summary(users, date(2024, 1, 1), date(2024, 1, 31))
        
        assert summary.total_users == 3
        assert summary.active_users == 3
        assert summary.total_tasks_completed == 3
        assert summary.total_time_logged == 24.0
        assert summary.average_completion_rate == 100.0
    
    def test_performance_report_with_no_tasks(self):
        """Test performance report with users having no tasks."""
        # Create user with no tasks
        user = Mock(spec=User)
        user.id = "user-1"
        user.name = "User 1"
        user.role = "User"
        user.tasks = []
        user.time_entries = []
        
        summary = ReportsService._get_performance_summary([user], date(2024, 1, 1), date(2024, 1, 31))
        
        assert summary.total_users == 1
        assert summary.active_users == 0  # No tasks or time entries
        assert summary.total_tasks_completed == 0
        assert summary.total_time_logged == 0.0
        assert summary.average_completion_rate == 0.0 