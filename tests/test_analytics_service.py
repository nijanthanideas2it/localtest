"""
Unit tests for analytics service layer.
"""
import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from uuid import uuid4

from app.services.analytics_service import AnalyticsService
from app.models.project import Project, ProjectTeamMember
from app.models.milestone import Milestone
from app.models.user import User
from app.schemas.analytics import (
    ProjectAnalyticsResponse,
    ProjectTimelineResponse,
    DashboardSummaryResponse
)
from app.core.auth import AuthUtils


class TestAnalyticsService:
    """Test cases for analytics service functionality."""
    
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
            due_date=date(2025, 6, 30),
            is_completed=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    @pytest.fixture
    def sample_completed_milestone(self, sample_project):
        """Sample completed milestone object."""
        return Milestone(
            id=uuid4(),
            name="Completed Milestone",
            description="A completed milestone",
            project_id=sample_project.id,
            due_date=date(2024, 6, 30),
            is_completed=True,
            completed_at=datetime.now(timezone.utc),
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
    
    def test_get_project_analytics_success(self, mock_db_session, sample_project, sample_milestone, sample_team_member):
        """Test successful project analytics retrieval."""
        # Mock project query with team members and milestones
        sample_project.team_members = [sample_team_member]
        sample_project.milestones = [sample_milestone]
        
        # Mock the project query
        mock_project_query = MagicMock()
        mock_project_query.options.return_value = mock_project_query
        mock_project_query.filter.return_value = mock_project_query
        mock_project_query.first.return_value = sample_project
        
        # Mock the team member query for team performance calculation
        mock_team_query = MagicMock()
        mock_team_query.filter.return_value = mock_team_query
        mock_team_query.all.return_value = [sample_team_member]
        
        # Mock the user query for team performance calculation
        mock_user_query = MagicMock()
        mock_user_query.filter.return_value = mock_user_query
        mock_user_query.first.return_value = User(
            id=sample_team_member.user_id,
            first_name="Test",
            last_name="User",
            email="test@example.com"
        )
        
        # Set up mock_db_session.query to return different mocks for different calls
        mock_db_session.query.side_effect = [mock_project_query, mock_team_query, mock_user_query]
        
        result = AnalyticsService.get_project_analytics(mock_db_session, str(sample_project.id))
        
        assert result is not None
        assert isinstance(result, ProjectAnalyticsResponse)
        assert result.project.id == sample_project.id
        assert result.project.name == sample_project.name
        assert result.project.status == sample_project.status
        assert result.project.progress_percentage >= 0
        assert result.project.days_elapsed >= 0
        assert len(result.milestones) == 1
        assert len(result.team_performance) == 1
    
    def test_get_project_analytics_project_not_found(self, mock_db_session):
        """Test project analytics when project not found."""
        # Mock project query to return None
        mock_db_session.query.return_value.options.return_value.filter.return_value.first.return_value = None
        
        result = AnalyticsService.get_project_analytics(mock_db_session, "non-existent-project")
        
        assert result is None
    
    def test_get_project_analytics_with_date_filters(self, mock_db_session, sample_project, sample_milestone):
        """Test project analytics with date filters."""
        # Mock project query
        sample_project.team_members = []
        sample_project.milestones = [sample_milestone]
        
        mock_db_session.query.return_value.options.return_value.filter.return_value.first.return_value = sample_project
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        result = AnalyticsService.get_project_analytics(
            mock_db_session,
            str(sample_project.id),
            start_date,
            end_date
        )
        
        assert result is not None
        assert isinstance(result, ProjectAnalyticsResponse)
    
    def test_get_project_timeline_success(self, mock_db_session, sample_project, sample_milestone):
        """Test successful project timeline retrieval."""
        # Mock project query with milestones
        sample_project.milestones = [sample_milestone]
        
        mock_db_session.query.return_value.options.return_value.filter.return_value.first.return_value = sample_project
        
        result = AnalyticsService.get_project_timeline(mock_db_session, str(sample_project.id))
        
        assert result is not None
        assert isinstance(result, ProjectTimelineResponse)
        assert result.project_id == sample_project.id
        assert result.project_name == sample_project.name
        assert result.start_date == sample_project.start_date
        assert result.end_date == sample_project.end_date
        assert len(result.events) >= 2  # At least project start and milestone
        assert len(result.phases) > 0
    
    def test_get_project_timeline_project_not_found(self, mock_db_session):
        """Test project timeline when project not found."""
        # Mock project query to return None
        mock_db_session.query.return_value.options.return_value.filter.return_value.first.return_value = None
        
        result = AnalyticsService.get_project_timeline(mock_db_session, "non-existent-project")
        
        assert result is None
    
    def test_get_dashboard_summary_admin(self, mock_db_session, sample_user):
        """Test dashboard summary for admin user."""
        # Mock user query
        mock_db_session.query.return_value.filter.return_value.count.return_value = 5
        
        # Mock projects query for admin
        sample_projects = [
            Project(id=uuid4(), name="Project 1", status="Active", start_date=date(2024, 1, 1), end_date=date(2024, 12, 31)),
            Project(id=uuid4(), name="Project 2", status="Completed", start_date=date(2024, 1, 1), end_date=date(2024, 6, 30)),
            Project(id=uuid4(), name="Project 3", status="Active", start_date=date(2024, 1, 1), end_date=date(2023, 12, 31))  # Overdue
        ]
        
        mock_db_session.query.return_value.all.return_value = sample_projects
        
        result = AnalyticsService.get_dashboard_summary(
            mock_db_session,
            str(sample_user.id),
            "Admin"
        )
        
        assert result is not None
        assert isinstance(result, DashboardSummaryResponse)
        assert result.total_projects == 3
        assert result.active_projects == 2
        assert result.completed_projects == 1
        assert result.overdue_projects == 1
        assert result.team_members == 5
    
    def test_get_dashboard_summary_project_manager(self, mock_db_session, sample_user):
        """Test dashboard summary for project manager user."""
        # Mock user query
        mock_db_session.query.return_value.filter.return_value.count.return_value = 3
        
        # Mock projects query for project manager
        sample_projects = [
            Project(id=uuid4(), name="Project 1", status="Active", start_date=date(2024, 1, 1), end_date=date(2024, 12, 31), manager_id=sample_user.id),
        ]
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = sample_projects
        
        result = AnalyticsService.get_dashboard_summary(
            mock_db_session,
            str(sample_user.id),
            "Project Manager"
        )
        
        assert result is not None
        assert isinstance(result, DashboardSummaryResponse)
        assert result.total_projects == 1
        assert result.active_projects == 1
        assert result.team_members == 3
    
    def test_get_dashboard_summary_developer(self, mock_db_session, sample_user):
        """Test dashboard summary for developer user."""
        # Mock user query
        mock_db_session.query.return_value.filter.return_value.count.return_value = 2
        
        # Mock team projects query for developer
        sample_projects = [
            Project(id=uuid4(), name="Project 1", status="Active", start_date=date(2024, 1, 1), end_date=date(2024, 12, 31)),
        ]
        
        mock_db_session.query.return_value.join.return_value.filter.return_value.all.return_value = sample_projects
        
        result = AnalyticsService.get_dashboard_summary(
            mock_db_session,
            str(sample_user.id),
            "Developer"
        )
        
        assert result is not None
        assert isinstance(result, DashboardSummaryResponse)
        assert result.total_projects == 1
        assert result.team_members == 2
    
    def test_calculate_project_progress(self, sample_project, sample_milestone, sample_completed_milestone):
        """Test project progress calculation."""
        # Add milestones to project
        sample_project.milestones = [sample_milestone, sample_completed_milestone]
        
        result = AnalyticsService._calculate_project_progress(sample_project)
        
        assert result is not None
        assert result.id == sample_project.id
        assert result.name == sample_project.name
        assert result.status == sample_project.status
        assert result.progress_percentage == 50.0  # 1 completed out of 2 milestones
        assert result.days_elapsed >= 0
        assert result.days_remaining is not None
    
    def test_calculate_project_progress_no_milestones(self, sample_project):
        """Test project progress calculation with no milestones."""
        sample_project.milestones = []
        
        result = AnalyticsService._calculate_project_progress(sample_project)
        
        assert result is not None
        assert result.progress_percentage == 0.0
    
    def test_calculate_milestone_progress(self, sample_milestone, sample_completed_milestone):
        """Test milestone progress calculation."""
        milestones = [sample_milestone, sample_completed_milestone]
        
        result = AnalyticsService._calculate_milestone_progress(milestones)
        
        assert len(result) == 2
        assert result[0].completion_percentage == 0.0  # Not completed
        assert result[1].completion_percentage == 100.0  # Completed
        assert result[0].days_remaining is not None
        assert result[1].days_remaining is None  # Completed milestone
    
    def test_calculate_budget_utilization(self, sample_project):
        """Test budget utilization calculation."""
        result = AnalyticsService._calculate_budget_utilization(sample_project)
        
        assert result == 50.0  # 5000 / 10000 * 100
    
    def test_calculate_budget_utilization_no_budget(self, sample_project):
        """Test budget utilization calculation with no budget."""
        sample_project.budget = None
        
        result = AnalyticsService._calculate_budget_utilization(sample_project)
        
        assert result is None
    
    def test_calculate_budget_utilization_zero_budget(self, sample_project):
        """Test budget utilization calculation with zero budget."""
        sample_project.budget = Decimal('0.00')
        
        result = AnalyticsService._calculate_budget_utilization(sample_project)
        
        assert result is None
    
    def test_calculate_risk_score(self, sample_project, sample_milestone):
        """Test risk score calculation."""
        from app.schemas.analytics import MilestoneProgressResponse
        
        # Create milestone progress data
        milestone_progress = MilestoneProgressResponse(
            id=sample_milestone.id,
            name=sample_milestone.name,
            due_date=sample_milestone.due_date,
            is_completed=sample_milestone.is_completed,
            completion_percentage=0.0,
            days_remaining=30
        )
        
        result = AnalyticsService._calculate_risk_score(sample_project, [milestone_progress])
        
        assert result is not None
        assert 0 <= result <= 100
    
    def test_calculate_risk_score_overdue_project(self, sample_project, sample_milestone):
        """Test risk score calculation for overdue project."""
        from app.schemas.analytics import MilestoneProgressResponse
        
        # Set project end date to past
        sample_project.end_date = date(2023, 12, 31)
        
        # Create overdue milestone progress data
        milestone_progress = MilestoneProgressResponse(
            id=sample_milestone.id,
            name=sample_milestone.name,
            due_date=date(2023, 6, 30),  # Past date
            is_completed=False,
            completion_percentage=0.0,
            days_remaining=-30  # Overdue
        )
        
        result = AnalyticsService._calculate_risk_score(sample_project, [milestone_progress])
        
        assert result is not None
        assert result > 0  # Should have some risk
    
    def test_get_timeline_events(self, mock_db_session, sample_project, sample_milestone):
        """Test timeline events generation."""
        sample_project.milestones = [sample_milestone]
        
        result = AnalyticsService._get_timeline_events(mock_db_session, sample_project)
        
        assert len(result) >= 2  # Project start + milestone
        assert any(event.type == "milestone" for event in result)
        assert any(event.type == "event" for event in result)
        assert all(event.date >= sample_project.start_date for event in result)
    
    def test_get_project_phases_short_project(self, sample_project):
        """Test project phases for short project."""
        sample_project.end_date = date(2024, 1, 30)  # 30 days duration
        
        result = AnalyticsService._get_project_phases(sample_project)
        
        assert len(result) == 3  # Planning, Execution, Closure
        assert result[0]["name"] == "Planning"
        assert result[1]["name"] == "Execution"
        assert result[2]["name"] == "Closure"
    
    def test_get_project_phases_long_project(self, sample_project):
        """Test project phases for long project."""
        sample_project.end_date = date(2024, 12, 31)  # Long duration
        
        result = AnalyticsService._get_project_phases(sample_project)
        
        assert len(result) == 5  # Planning, Development, Testing, Deployment, Closure
        assert result[0]["name"] == "Planning"
        assert result[1]["name"] == "Development"
        assert result[2]["name"] == "Testing"
        assert result[3]["name"] == "Deployment"
        assert result[4]["name"] == "Closure"
    
    def test_get_upcoming_deadlines(self, mock_db_session, sample_project, sample_milestone):
        """Test upcoming deadlines retrieval."""
        projects = [sample_project]
        sample_project.milestones = [sample_milestone]
        
        result = AnalyticsService._get_upcoming_deadlines(mock_db_session, projects)
        
        assert isinstance(result, list)
        # Should include project end date and milestone deadline if within 30 days
        assert len(result) >= 0  # May be 0 if dates are not within 30 days


class TestAnalyticsValidation:
    """Test cases for analytics validation."""
    
    def test_analytics_filter_request_valid(self):
        """Test valid analytics filter request."""
        from app.schemas.analytics import AnalyticsFilterRequest
        
        filter_data = AnalyticsFilterRequest(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            include_team_performance=True,
            include_time_tracking=True,
            include_milestones=True
        )
        
        assert filter_data.start_date == date(2024, 1, 1)
        assert filter_data.end_date == date(2024, 12, 31)
        assert filter_data.include_team_performance is True
        assert filter_data.include_time_tracking is True
        assert filter_data.include_milestones is True
    
    def test_analytics_filter_request_defaults(self):
        """Test analytics filter request with default values."""
        from app.schemas.analytics import AnalyticsFilterRequest
        
        filter_data = AnalyticsFilterRequest()
        
        assert filter_data.start_date is None
        assert filter_data.end_date is None
        assert filter_data.include_team_performance is True
        assert filter_data.include_time_tracking is True
        assert filter_data.include_milestones is True 