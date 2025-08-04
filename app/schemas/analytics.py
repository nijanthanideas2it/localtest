"""
Analytics schemas for project analytics and reporting.
"""
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, UUID4

from app.schemas.user import UserResponse


class TaskSummaryResponse(BaseModel):
    """Task summary response model."""
    total: int
    completed: int
    in_progress: int
    todo: int
    overdue: int
    completion_percentage: float


class TimeSummaryResponse(BaseModel):
    """Time summary response model."""
    total_estimated: float
    total_actual: float
    variance: float
    variance_percentage: float


class TeamPerformanceResponse(BaseModel):
    """Team performance response model."""
    user_id: UUID4
    name: str
    tasks_completed: int
    hours_logged: float
    efficiency_score: Optional[float] = None


class MilestoneProgressResponse(BaseModel):
    """Milestone progress response model."""
    id: UUID4
    name: str
    due_date: date
    is_completed: bool
    completion_percentage: float
    days_remaining: Optional[int] = None


class ProjectProgressResponse(BaseModel):
    """Project progress response model."""
    id: UUID4
    name: str
    status: str
    progress_percentage: float
    start_date: date
    end_date: Optional[date] = None
    days_elapsed: int
    days_remaining: Optional[int] = None


class ProjectAnalyticsResponse(BaseModel):
    """Project analytics response model."""
    project: ProjectProgressResponse
    tasks_summary: TaskSummaryResponse
    time_summary: TimeSummaryResponse
    team_performance: List[TeamPerformanceResponse]
    milestones: List[MilestoneProgressResponse]
    budget_utilization: Optional[float] = None
    risk_score: Optional[float] = None


class TimelineEventResponse(BaseModel):
    """Timeline event response model."""
    id: UUID4
    type: str  # "milestone", "task", "event"
    title: str
    description: Optional[str] = None
    date: date
    status: str
    category: str


class ProjectTimelineResponse(BaseModel):
    """Project timeline response model."""
    project_id: UUID4
    project_name: str
    start_date: date
    end_date: Optional[date] = None
    events: List[TimelineEventResponse]
    phases: List[Dict[str, Any]]


class ProjectProgressWrapper(BaseModel):
    """Project progress response wrapper."""
    success: bool = True
    data: ProjectAnalyticsResponse
    message: str = "Project analytics retrieved successfully"


class ProjectTimelineWrapper(BaseModel):
    """Project timeline response wrapper."""
    success: bool = True
    data: ProjectTimelineResponse
    message: str = "Project timeline retrieved successfully"


class AnalyticsFilterRequest(BaseModel):
    """Analytics filter request model."""
    start_date: Optional[date] = Field(None, description="Start date for analytics period")
    end_date: Optional[date] = Field(None, description="End date for analytics period")
    include_team_performance: bool = Field(True, description="Include team performance data")
    include_time_tracking: bool = Field(True, description="Include time tracking data")
    include_milestones: bool = Field(True, description="Include milestone data")


class DashboardSummaryResponse(BaseModel):
    """Dashboard summary response model."""
    total_projects: int
    active_projects: int
    completed_projects: int
    overdue_projects: int
    total_tasks: int
    completed_tasks: int
    total_hours_logged: float
    team_members: int
    upcoming_deadlines: List[Dict[str, Any]]


class DashboardSummaryWrapper(BaseModel):
    """Dashboard summary response wrapper."""
    success: bool = True
    data: DashboardSummaryResponse
    message: str = "Dashboard summary retrieved successfully" 