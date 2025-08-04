"""
Unit tests for reports functionality.
"""
import pytest
import json
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch, AsyncMock
from uuid import uuid4
from decimal import Decimal

from app.services.reports_service import ReportsService
from app.schemas.reports import (
    ReportType,
    ReportFormat,
    ProjectSummaryData,
    ProjectFinancialData,
    TeamMemberPerformance,
    MilestoneReportData,
    TaskAnalysisData,
    ProjectReportResponse,
    ProjectReportExportResponse
)
from app.models.project import Project
from app.models.task import Task
from app.models.milestone import Milestone
from app.models.time_entry import TimeEntry
from app.models.user import User
from app.models.project import ProjectTeamMember


class TestReportsService:
    """Test cases for ReportsService."""
    
    @pytest.fixture
    def sample_project(self):
        """Sample project for testing."""
        project = Project(
            id=uuid4(),
            name="Test Project",
            description="Test project description",
            status="active",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            budget=Decimal("10000.00"),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        return project
    
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
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        return user
    
    @pytest.fixture
    def sample_tasks(self, sample_project, sample_user):
        """Sample tasks for testing."""
        tasks = [
            Task(
                id=uuid4(),
                title="Task 1",
                description="Task 1 description",
                status="completed",
                priority="high",
                project_id=sample_project.id,
                assignee_id=str(sample_user.id),
                estimated_hours=8.0,
                actual_hours=6.0,
                due_date=date(2024, 6, 1),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            ),
            Task(
                id=uuid4(),
                title="Task 2",
                description="Task 2 description",
                status="in_progress",
                priority="medium",
                project_id=sample_project.id,
                assignee_id=str(sample_user.id),
                estimated_hours=12.0,
                actual_hours=4.0,
                due_date=date(2024, 6, 15),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            ),
            Task(
                id=uuid4(),
                title="Task 3",
                description="Task 3 description",
                status="pending",
                priority="low",
                project_id=sample_project.id,
                assignee_id=None,
                estimated_hours=16.0,
                actual_hours=0.0,
                due_date=date(2024, 7, 1),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
        ]
        return tasks
    
    @pytest.fixture
    def sample_milestones(self, sample_project):
        """Sample milestones for testing."""
        milestones = [
            Milestone(
                id=uuid4(),
                title="Milestone 1",
                description="Milestone 1 description",
                project_id=sample_project.id,
                due_date=date(2024, 6, 30),
                status="completed",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            ),
            Milestone(
                id=uuid4(),
                title="Milestone 2",
                description="Milestone 2 description",
                project_id=sample_project.id,
                due_date=date(2024, 8, 31),
                status="in_progress",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
        ]
        return milestones
    
    @pytest.fixture
    def sample_time_entries(self, sample_project, sample_user):
        """Sample time entries for testing."""
        time_entries = [
            TimeEntry(
                id=uuid4(),
                user_id=str(sample_user.id),
                project_id=sample_project.id,
                task_id=uuid4(),
                date=date(2024, 6, 1),
                duration=6.0,
                description="Work on Task 1",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            ),
            TimeEntry(
                id=uuid4(),
                user_id=str(sample_user.id),
                project_id=sample_project.id,
                task_id=uuid4(),
                date=date(2024, 6, 2),
                duration=4.0,
                description="Work on Task 2",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
        ]
        return time_entries
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        session = MagicMock()
        session.query = MagicMock()
        session.add = MagicMock()
        session.commit = MagicMock()
        session.rollback = MagicMock()
        session.close = MagicMock()
        return session
    
    def test_generate_summary_report(self, mock_db_session, sample_project, sample_tasks, sample_milestones, sample_time_entries):
        """Test generating a summary report."""
        # Mock database queries
        mock_db_session.query.return_value.options.return_value.filter.return_value.first.return_value = sample_project
        mock_db_session.query.return_value.filter.return_value.count.side_effect = [3, 1, 1, 1, 0]  # tasks, completed, in_progress, pending, overdue
        mock_db_session.query.return_value.filter.return_value.scalar.return_value = 10.0  # total time
        
        # Mock team member query
        mock_db_session.query.return_value.filter.return_value.count.return_value = 2  # team size
        
        # Mock milestone queries
        mock_db_session.query.return_value.filter.return_value.count.side_effect = [2, 1]  # milestones, completed milestones
        
        with patch('app.services.reports_service.ProjectService.project_to_response') as mock_project_response:
            mock_project_response.return_value = {
                "id": str(sample_project.id),
                "name": sample_project.name,
                "description": sample_project.description,
                "status": sample_project.status
            }
            
            report = ReportsService.generate_project_report(
                mock_db_session,
                str(sample_project.id),
                ReportType.SUMMARY,
                date(2024, 1, 1),
                date(2024, 12, 31),
                True
            )
        
        assert report is not None
        assert report.report_type == ReportType.SUMMARY
        assert report.project["id"] == str(sample_project.id)
        assert report.summary.total_tasks == 3
        assert report.summary.completed_tasks == 1
        assert report.summary.in_progress_tasks == 1
        assert report.summary.pending_tasks == 1
        assert report.summary.overdue_tasks == 0
        assert report.summary.completion_rate == pytest.approx(33.33, abs=0.01)
        assert report.summary.total_time_logged == 10.0
        assert report.summary.team_size == 2
        assert report.summary.milestones_count == 2
        assert report.summary.completed_milestones == 1
    
    def test_generate_financial_report(self, mock_db_session, sample_project, sample_time_entries):
        """Test generating a financial report."""
        # Mock database queries
        mock_db_session.query.return_value.options.return_value.filter.return_value.first.return_value = sample_project
        mock_db_session.query.return_value.filter.return_value.count.side_effect = [3, 1]  # total tasks, completed tasks
        mock_db_session.query.return_value.filter.return_value.scalar.side_effect = [10.0, 8.0]  # total time, avg duration
        
        with patch('app.services.reports_service.ProjectService.project_to_response') as mock_project_response:
            mock_project_response.return_value = {
                "id": str(sample_project.id),
                "name": sample_project.name,
                "description": sample_project.description,
                "status": sample_project.status
            }
            
            report = ReportsService.generate_project_report(
                mock_db_session,
                str(sample_project.id),
                ReportType.FINANCIAL,
                date(2024, 1, 1),
                date(2024, 12, 31),
                True
            )
        
        assert report is not None
        assert report.report_type == ReportType.FINANCIAL
        assert report.financial_data is not None
        assert report.financial_data.total_budget == Decimal("10000.00")
        assert report.financial_data.total_hours_billed == 10.0
        assert report.financial_data.cost_per_hour == Decimal("50.00")
    
    def test_generate_team_performance_report(self, mock_db_session, sample_project, sample_user):
        """Test generating a team performance report."""
        # Mock database queries
        mock_db_session.query.return_value.options.return_value.filter.return_value.first.return_value = sample_project
        mock_db_session.query.return_value.filter.return_value.all.return_value = [
            ProjectTeamMember(project_id=sample_project.id, user_id=str(sample_user.id))
        ]
        mock_db_session.query.return_value.filter.return_value.count.side_effect = [2, 1]  # tasks assigned, completed
        mock_db_session.query.return_value.filter.return_value.scalar.return_value = 8.0  # time logged
        
        with patch('app.services.reports_service.ProjectService.project_to_response') as mock_project_response, \
             patch('app.services.reports_service.ProjectService.user_to_response') as mock_user_response:
            mock_project_response.return_value = {
                "id": str(sample_project.id),
                "name": sample_project.name,
                "description": sample_project.description,
                "status": sample_project.status
            }
            mock_user_response.return_value = {
                "id": str(sample_user.id),
                "email": sample_user.email,
                "first_name": sample_user.first_name,
                "last_name": sample_user.last_name,
                "role": sample_user.role
            }
            
            report = ReportsService.generate_project_report(
                mock_db_session,
                str(sample_project.id),
                ReportType.TEAM_PERFORMANCE,
                date(2024, 1, 1),
                date(2024, 12, 31),
                True
            )
        
        assert report is not None
        assert report.report_type == ReportType.TEAM_PERFORMANCE
        assert len(report.team_performance) == 1
        assert report.team_performance[0].tasks_assigned == 2
        assert report.team_performance[0].tasks_completed == 1
        assert report.team_performance[0].completion_rate == 50.0
        assert report.team_performance[0].time_logged == 8.0
    
    def test_generate_milestone_report(self, mock_db_session, sample_project, sample_milestones):
        """Test generating a milestone report."""
        # Mock database queries
        mock_db_session.query.return_value.options.return_value.filter.return_value.first.return_value = sample_project
        mock_db_session.query.return_value.filter.return_value.all.return_value = sample_milestones
        mock_db_session.query.return_value.filter.return_value.count.side_effect = [2, 1]  # tasks in milestone, completed tasks
        
        with patch('app.services.reports_service.ProjectService.project_to_response') as mock_project_response:
            mock_project_response.return_value = {
                "id": str(sample_project.id),
                "name": sample_project.name,
                "description": sample_project.description,
                "status": sample_project.status
            }
            
            report = ReportsService.generate_project_report(
                mock_db_session,
                str(sample_project.id),
                ReportType.MILESTONE,
                date(2024, 1, 1),
                date(2024, 12, 31),
                True
            )
        
        assert report is not None
        assert report.report_type == ReportType.MILESTONE
        assert len(report.milestones) == 2
        assert report.milestones[0].title == "Milestone 1"
        assert report.milestones[0].status == "completed"
        assert report.milestones[1].title == "Milestone 2"
        assert report.milestones[1].status == "in_progress"
    
    def test_generate_task_analysis_report(self, mock_db_session, sample_project, sample_tasks):
        """Test generating a task analysis report."""
        # Mock database queries
        mock_db_session.query.return_value.options.return_value.filter.return_value.first.return_value = sample_project
        mock_db_session.query.return_value.filter.return_value.count.side_effect = [3, 1, 1, 1, 0]  # total tasks, by status, by priority, by assignee
        mock_db_session.query.return_value.filter.return_value.scalar.return_value = 8.0  # avg duration
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [("Task 1",), ("Task 3",)]  # longest, shortest
        mock_db_session.query.return_value.filter.return_value.distinct.return_value.all.return_value = [("user1",)]
        
        with patch('app.services.reports_service.ProjectService.project_to_response') as mock_project_response:
            mock_project_response.return_value = {
                "id": str(sample_project.id),
                "name": sample_project.name,
                "description": sample_project.description,
                "status": sample_project.status
            }
            
            report = ReportsService.generate_project_report(
                mock_db_session,
                str(sample_project.id),
                ReportType.TASK_ANALYSIS,
                date(2024, 1, 1),
                date(2024, 12, 31),
                True
            )
        
        assert report is not None
        assert report.report_type == ReportType.TASK_ANALYSIS
        assert report.task_analysis is not None
        assert report.task_analysis.total_tasks == 3
        assert report.task_analysis.average_task_duration == 8.0
        assert report.task_analysis.longest_running_task == "Task 1"
        assert report.task_analysis.shortest_completed_task == "Task 3"
    
    def test_export_project_report_json(self, mock_db_session, sample_project):
        """Test exporting a project report to JSON format."""
        # Mock the report generation
        mock_report = ProjectReportResponse(
            report_id=str(uuid4()),
            project={"id": str(sample_project.id), "name": sample_project.name},
            report_type=ReportType.SUMMARY,
            generated_at=datetime.now(timezone.utc),
            summary=ProjectSummaryData(
                total_tasks=3,
                completed_tasks=1,
                in_progress_tasks=1,
                pending_tasks=1,
                overdue_tasks=0,
                completion_rate=33.33,
                total_time_logged=10.0,
                team_size=2,
                milestones_count=2,
                completed_milestones=1
            ),
            team_performance=[],
            milestones=[],
            metadata={}
        )
        
        with patch('app.services.reports_service.ReportsService.generate_project_report') as mock_generate:
            mock_generate.return_value = mock_report
            
            with patch('builtins.open', create=True) as mock_open:
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file
                
                export_response = ReportsService.export_project_report(
                    mock_db_session,
                    str(sample_project.id),
                    ReportType.SUMMARY,
                    ReportFormat.JSON,
                    filename="test_report"
                )
        
        assert export_response is not None
        assert export_response.format == ReportFormat.JSON
        assert export_response.filename == "test_report.json"
        assert export_response.download_url == "/static/exports/test_report.json"
    
    def test_export_project_report_csv(self, mock_db_session, sample_project):
        """Test exporting a project report to CSV format."""
        # Mock the report generation
        mock_report = ProjectReportResponse(
            report_id=str(uuid4()),
            project={"id": str(sample_project.id), "name": sample_project.name},
            report_type=ReportType.SUMMARY,
            generated_at=datetime.now(timezone.utc),
            summary=ProjectSummaryData(
                total_tasks=3,
                completed_tasks=1,
                in_progress_tasks=1,
                pending_tasks=1,
                overdue_tasks=0,
                completion_rate=33.33,
                total_time_logged=10.0,
                team_size=2,
                milestones_count=2,
                completed_milestones=1
            ),
            team_performance=[],
            milestones=[],
            metadata={}
        )
        
        with patch('app.services.reports_service.ReportsService.generate_project_report') as mock_generate:
            mock_generate.return_value = mock_report
            
            with patch('builtins.open', create=True) as mock_open:
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file
                
                export_response = ReportsService.export_project_report(
                    mock_db_session,
                    str(sample_project.id),
                    ReportType.SUMMARY,
                    ReportFormat.CSV,
                    filename="test_report"
                )
        
        assert export_response is not None
        assert export_response.format == ReportFormat.CSV
        assert export_response.filename == "test_report.csv"
        assert export_response.download_url == "/static/exports/test_report.csv"
    
    def test_get_project_summary_data(self, mock_db_session, sample_project):
        """Test getting project summary data."""
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.count.side_effect = [3, 1, 1, 1, 0]  # tasks, completed, in_progress, pending, overdue
        mock_db_session.query.return_value.filter.return_value.scalar.return_value = 10.0  # total time
        mock_db_session.query.return_value.filter.return_value.count.return_value = 2  # team size, milestones, completed milestones
        
        summary_data = ReportsService._get_project_summary_data(
            mock_db_session,
            sample_project,
            date(2024, 1, 1),
            date(2024, 12, 31)
        )
        
        assert summary_data is not None
        assert summary_data.total_tasks == 3
        assert summary_data.completed_tasks == 1
        assert summary_data.in_progress_tasks == 1
        assert summary_data.pending_tasks == 1
        assert summary_data.overdue_tasks == 0
        assert summary_data.completion_rate == pytest.approx(33.33, abs=0.01)
        assert summary_data.total_time_logged == 10.0
        assert summary_data.team_size == 2
        assert summary_data.milestones_count == 2
        assert summary_data.completed_milestones == 1
    
    def test_get_financial_data(self, mock_db_session, sample_project):
        """Test getting financial data."""
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.scalar.return_value = 10.0  # total hours
        mock_db_session.query.return_value.filter.return_value.count.side_effect = [3, 1]  # total tasks, completed tasks
        
        financial_data = ReportsService._get_financial_data(
            mock_db_session,
            sample_project,
            date(2024, 1, 1),
            date(2024, 12, 31)
        )
        
        assert financial_data is not None
        assert financial_data.total_budget == Decimal("10000.00")
        assert financial_data.total_hours_billed == 10.0
        assert financial_data.cost_per_hour == Decimal("50.00")
        assert financial_data.spent_amount == Decimal("500.00")
        assert financial_data.remaining_budget == Decimal("9500.00")
        assert financial_data.budget_utilization_percentage == 5.0
    
    def test_get_financial_data_no_budget(self, mock_db_session):
        """Test getting financial data for project without budget."""
        project = Project(
            id=uuid4(),
            name="Test Project",
            description="Test project description",
            status="active",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            budget=None,  # No budget
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        financial_data = ReportsService._get_financial_data(
            mock_db_session,
            project,
            date(2024, 1, 1),
            date(2024, 12, 31)
        )
        
        assert financial_data is None
    
    def test_get_team_performance_data(self, mock_db_session, sample_project, sample_user):
        """Test getting team performance data."""
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.all.return_value = [
            ProjectTeamMember(project_id=sample_project.id, user_id=str(sample_user.id))
        ]
        mock_db_session.query.return_value.filter.return_value.count.side_effect = [2, 1]  # tasks assigned, completed
        mock_db_session.query.return_value.filter.return_value.scalar.return_value = 8.0  # time logged
        
        with patch('app.services.reports_service.ProjectService.user_to_response') as mock_user_response:
            mock_user_response.return_value = {
                "id": str(sample_user.id),
                "email": sample_user.email,
                "first_name": sample_user.first_name,
                "last_name": sample_user.last_name,
                "role": sample_user.role
            }
            
            team_performance = ReportsService._get_team_performance_data(
                mock_db_session,
                sample_project,
                date(2024, 1, 1),
                date(2024, 12, 31)
            )
        
        assert len(team_performance) == 1
        assert team_performance[0].tasks_assigned == 2
        assert team_performance[0].tasks_completed == 1
        assert team_performance[0].completion_rate == 50.0
        assert team_performance[0].time_logged == 8.0
        assert team_performance[0].on_time_delivery_rate == 100.0
    
    def test_get_milestone_report_data(self, mock_db_session, sample_project, sample_milestones):
        """Test getting milestone report data."""
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.all.return_value = sample_milestones
        mock_db_session.query.return_value.filter.return_value.count.side_effect = [2, 1]  # tasks in milestone, completed tasks
        
        milestone_data = ReportsService._get_milestone_report_data(
            mock_db_session,
            sample_project,
            date(2024, 1, 1),
            date(2024, 12, 31)
        )
        
        assert len(milestone_data) == 2
        assert milestone_data[0].title == "Milestone 1"
        assert milestone_data[0].status == "completed"
        assert milestone_data[0].completion_percentage == 50.0
        assert milestone_data[0].is_overdue == False
        assert milestone_data[1].title == "Milestone 2"
        assert milestone_data[1].status == "in_progress"
        assert milestone_data[1].completion_percentage == 50.0
    
    def test_get_task_analysis_data(self, mock_db_session, sample_project):
        """Test getting task analysis data."""
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.count.side_effect = [3, 1, 1, 1, 0]  # total tasks, by status, by priority, by assignee
        mock_db_session.query.return_value.filter.return_value.scalar.return_value = 8.0  # avg duration
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [("Task 1",), ("Task 3",)]  # longest, shortest
        mock_db_session.query.return_value.filter.return_value.distinct.return_value.all.return_value = [("user1",)]
        
        task_analysis = ReportsService._get_task_analysis_data(
            mock_db_session,
            sample_project,
            date(2024, 1, 1),
            date(2024, 12, 31)
        )
        
        assert task_analysis is not None
        assert task_analysis.total_tasks == 3
        assert task_analysis.average_task_duration == 8.0
        assert task_analysis.longest_running_task == "Task 1"
        assert task_analysis.shortest_completed_task == "Task 3"
        assert "tasks_with_dependencies" in task_analysis.dependency_analysis
    
    def test_project_not_found(self, mock_db_session):
        """Test generating report for non-existent project."""
        mock_db_session.query.return_value.options.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="Project with ID"):
            ReportsService.generate_project_report(
                mock_db_session,
                str(uuid4()),
                ReportType.SUMMARY,
                date(2024, 1, 1),
                date(2024, 12, 31),
                True
            )
    
    def test_invalid_report_type(self, mock_db_session, sample_project):
        """Test generating report with invalid report type."""
        mock_db_session.query.return_value.options.return_value.filter.return_value.first.return_value = sample_project
        
        with pytest.raises(ValueError, match="Unsupported report type"):
            ReportsService.generate_project_report(
                mock_db_session,
                str(sample_project.id),
                "invalid_type",  # Invalid report type
                date(2024, 1, 1),
                date(2024, 12, 31),
                True
            )
    
    def test_get_report_by_id(self):
        """Test getting report by ID."""
        # Clear existing reports
        ReportsService._generated_reports.clear()
        
        # Create a test report
        test_report = ProjectReportResponse(
            report_id="test-id",
            project={"id": "project-id", "name": "Test Project"},
            report_type=ReportType.SUMMARY,
            generated_at=datetime.now(timezone.utc),
            summary=ProjectSummaryData(
                total_tasks=1,
                completed_tasks=1,
                in_progress_tasks=0,
                pending_tasks=0,
                overdue_tasks=0,
                completion_rate=100.0,
                total_time_logged=8.0,
                team_size=1,
                milestones_count=1,
                completed_milestones=1
            ),
            team_performance=[],
            milestones=[],
            metadata={}
        )
        
        ReportsService._generated_reports["test-id"] = test_report
        
        # Get the report
        retrieved_report = ReportsService.get_report_by_id("test-id")
        
        assert retrieved_report is not None
        assert retrieved_report.report_id == "test-id"
        assert retrieved_report.project["name"] == "Test Project"
    
    def test_get_report_by_id_not_found(self):
        """Test getting report by non-existent ID."""
        # Clear existing reports
        ReportsService._generated_reports.clear()
        
        retrieved_report = ReportsService.get_report_by_id("non-existent-id")
        
        assert retrieved_report is None
    
    def test_cleanup_expired_exports(self):
        """Test cleaning up expired exports."""
        # Clear existing exports
        ReportsService._export_files.clear()
        
        # Add a test export
        test_export = {
            "file_path": "test_file.json",
            "expires_at": datetime.now(timezone.utc),  # Expired
            "response": ProjectReportExportResponse(
                export_id="test-export",
                filename="test_file.json",
                format=ReportFormat.JSON,
                download_url="/static/exports/test_file.json",
                expires_at=datetime.now(timezone.utc),
                metadata={}
            )
        }
        
        ReportsService._export_files["test-export"] = test_export
        
        # Run cleanup
        ReportsService.cleanup_expired_exports()
        
        # Check that expired export was removed
        assert "test-export" not in ReportsService._export_files 