"""
Reports schemas for analytics and reporting operations.
"""
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from enum import Enum

from app.schemas.project import ProjectResponse
from app.schemas.user import UserResponse


class ReportFormat(str, Enum):
    """Supported report formats."""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    EXCEL = "excel"


class ReportType(str, Enum):
    """Types of project reports."""
    SUMMARY = "summary"
    DETAILED = "detailed"
    FINANCIAL = "financial"
    TIMELINE = "timeline"
    TEAM_PERFORMANCE = "team_performance"
    MILESTONE = "milestone"
    TASK_ANALYSIS = "task_analysis"


class TimeReportType(str, Enum):
    """Types of time reports."""
    GENERAL = "general"
    BY_USER = "by_user"
    BY_PROJECT = "by_project"


class PerformanceReportType(str, Enum):
    """Types of performance reports."""
    GENERAL = "general"
    INDIVIDUAL = "individual"
    TEAM = "team"


class ProjectReportRequest(BaseModel):
    """Request model for project report generation."""
    project_id: str = Field(..., description="Project ID")
    report_type: ReportType = Field(..., description="Type of report to generate")
    start_date: Optional[date] = Field(None, description="Start date for report period")
    end_date: Optional[date] = Field(None, description="End date for report period")
    include_details: bool = Field(True, description="Include detailed information")
    format: ReportFormat = Field(ReportFormat.JSON, description="Report format")

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, values):
        """Validate that end_date is after start_date."""
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError("End date must be after start date")
        return v


class PerformanceReportRequest(BaseModel):
    """Request model for performance report generation."""
    report_type: PerformanceReportType = Field(..., description="Type of performance report to generate")
    user_id: Optional[str] = Field(None, description="User ID for individual performance reports")
    start_date: Optional[date] = Field(None, description="Start date for report period")
    end_date: Optional[date] = Field(None, description="End date for report period")
    include_details: bool = Field(True, description="Include detailed information")
    format: ReportFormat = Field(ReportFormat.JSON, description="Report format")

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, values):
        """Validate that end_date is after start_date."""
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError("End date must be after start date")
        return v

    @field_validator('user_id')
    @classmethod
    def validate_user_id_for_individual_report(cls, v, values):
        """Validate user_id is provided for individual performance reports."""
        if 'report_type' in values and values['report_type'] == PerformanceReportType.INDIVIDUAL and not v:
            raise ValueError("user_id is required for individual performance reports")
        return v


class PerformanceReportExportRequest(BaseModel):
    """Request model for performance report export."""
    report_type: PerformanceReportType = Field(..., description="Type of performance report to export")
    user_id: Optional[str] = Field(None, description="User ID for individual performance reports")
    format: ReportFormat = Field(..., description="Export format")
    start_date: Optional[date] = Field(None, description="Start date for report period")
    end_date: Optional[date] = Field(None, description="End date for report period")
    include_charts: bool = Field(True, description="Include charts in export")
    filename: Optional[str] = Field(None, description="Custom filename for export")

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, values):
        """Validate that end_date is after start_date."""
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError("End date must be after start date")
        return v

    @field_validator('user_id')
    @classmethod
    def validate_user_id_for_individual_report(cls, v, values):
        """Validate user_id is provided for individual performance reports."""
        if 'report_type' in values and values['report_type'] == PerformanceReportType.INDIVIDUAL and not v:
            raise ValueError("user_id is required for individual performance reports")
        return v


class TimeReportRequest(BaseModel):
    """Request model for time report generation."""
    report_type: TimeReportType = Field(..., description="Type of time report to generate")
    user_id: Optional[str] = Field(None, description="User ID for user-specific reports")
    project_id: Optional[str] = Field(None, description="Project ID for project-specific reports")
    start_date: Optional[date] = Field(None, description="Start date for report period")
    end_date: Optional[date] = Field(None, description="End date for report period")
    include_details: bool = Field(True, description="Include detailed information")
    format: ReportFormat = Field(ReportFormat.JSON, description="Report format")

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, values):
        """Validate that end_date is after start_date."""
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError("End date must be after start date")
        return v

    @field_validator('user_id')
    @classmethod
    def validate_user_id_for_user_report(cls, v, values):
        """Validate user_id is provided for user-specific reports."""
        if 'report_type' in values and values['report_type'] == TimeReportType.BY_USER and not v:
            raise ValueError("user_id is required for user-specific time reports")
        return v

    @field_validator('project_id')
    @classmethod
    def validate_project_id_for_project_report(cls, v, values):
        """Validate project_id is provided for project-specific reports."""
        if 'report_type' in values and values['report_type'] == TimeReportType.BY_PROJECT and not v:
            raise ValueError("project_id is required for project-specific time reports")
        return v


class TimeReportExportRequest(BaseModel):
    """Request model for time report export."""
    report_type: TimeReportType = Field(..., description="Type of time report to export")
    user_id: Optional[str] = Field(None, description="User ID for user-specific reports")
    project_id: Optional[str] = Field(None, description="Project ID for project-specific reports")
    format: ReportFormat = Field(..., description="Export format")
    start_date: Optional[date] = Field(None, description="Start date for report period")
    end_date: Optional[date] = Field(None, description="End date for report period")
    include_charts: bool = Field(True, description="Include charts in export")
    filename: Optional[str] = Field(None, description="Custom filename for export")

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, values):
        """Validate that end_date is after start_date."""
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError("End date must be after start date")
        return v

    @field_validator('user_id')
    @classmethod
    def validate_user_id_for_user_report(cls, v, values):
        """Validate user_id is provided for user-specific reports."""
        if 'report_type' in values and values['report_type'] == TimeReportType.BY_USER and not v:
            raise ValueError("user_id is required for user-specific time reports")
        return v

    @field_validator('project_id')
    @classmethod
    def validate_project_id_for_project_report(cls, v, values):
        """Validate project_id is provided for project-specific reports."""
        if 'report_type' in values and values['report_type'] == TimeReportType.BY_PROJECT and not v:
            raise ValueError("project_id is required for project-specific time reports")
        return v


class ProjectReportExportRequest(BaseModel):
    """Request model for project report export."""
    project_id: str = Field(..., description="Project ID")
    report_type: ReportType = Field(..., description="Type of report to export")
    format: ReportFormat = Field(..., description="Export format")
    start_date: Optional[date] = Field(None, description="Start date for report period")
    end_date: Optional[date] = Field(None, description="End date for report period")
    include_charts: bool = Field(True, description="Include charts in export")
    filename: Optional[str] = Field(None, description="Custom filename for export")

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, values):
        """Validate that end_date is after start_date."""
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError("End date must be after start date")
        return v


class ProjectSummaryData(BaseModel):
    """Project summary data for reports."""
    total_tasks: int = Field(..., description="Total number of tasks")
    completed_tasks: int = Field(..., description="Number of completed tasks")
    in_progress_tasks: int = Field(..., description="Number of tasks in progress")
    pending_tasks: int = Field(..., description="Number of pending tasks")
    overdue_tasks: int = Field(..., description="Number of overdue tasks")
    completion_rate: float = Field(..., description="Task completion rate (0-100)")
    total_time_logged: float = Field(..., description="Total time logged in hours")
    budget_utilization: Optional[float] = Field(None, description="Budget utilization percentage")
    risk_score: Optional[float] = Field(None, description="Project risk score (0-100)")
    team_size: int = Field(..., description="Number of team members")
    milestones_count: int = Field(..., description="Number of milestones")
    completed_milestones: int = Field(..., description="Number of completed milestones")


class PerformanceSummaryData(BaseModel):
    """Performance summary data for reports."""
    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    total_tasks_completed: int = Field(..., description="Total tasks completed")
    total_time_logged: float = Field(..., description="Total time logged in hours")
    average_completion_rate: float = Field(..., description="Average task completion rate (0-100)")
    average_time_per_task: float = Field(..., description="Average time per task in hours")
    top_performers_count: int = Field(..., description="Number of top performers")
    improvement_areas_count: int = Field(..., description="Number of users needing improvement")


class IndividualPerformanceData(BaseModel):
    """Individual user performance data."""
    user: UserResponse = Field(..., description="User information")
    tasks_assigned: int = Field(..., description="Number of tasks assigned")
    tasks_completed: int = Field(..., description="Number of tasks completed")
    tasks_in_progress: int = Field(..., description="Number of tasks in progress")
    tasks_overdue: int = Field(..., description="Number of overdue tasks")
    completion_rate: float = Field(..., description="Task completion rate (0-100)")
    total_time_logged: float = Field(..., description="Total time logged in hours")
    average_time_per_task: float = Field(..., description="Average time per task in hours")
    on_time_delivery_rate: float = Field(..., description="On-time delivery rate (0-100)")
    performance_score: float = Field(..., description="Overall performance score (0-100)")
    skills_utilization: Dict[str, float] = Field(..., description="Skills utilization by category")
    project_contributions: List[Dict[str, Any]] = Field(..., description="Contributions to projects")


class TeamPerformanceData(BaseModel):
    """Team performance data."""
    team_size: int = Field(..., description="Team size")
    total_tasks: int = Field(..., description="Total tasks assigned to team")
    completed_tasks: int = Field(..., description="Completed tasks")
    team_completion_rate: float = Field(..., description="Team completion rate (0-100)")
    average_performance_score: float = Field(..., description="Average team performance score (0-100)")
    collaboration_score: float = Field(..., description="Team collaboration score (0-100)")
    top_performers: List[IndividualPerformanceData] = Field(..., description="Top performing team members")
    improvement_areas: List[Dict[str, Any]] = Field(..., description="Areas for team improvement")
    skill_gaps: List[Dict[str, Any]] = Field(..., description="Identified skill gaps")


class PerformanceMetricsData(BaseModel):
    """Detailed performance metrics."""
    productivity_score: float = Field(..., description="Productivity score (0-100)")
    efficiency_score: float = Field(..., description="Efficiency score (0-100)")
    quality_score: float = Field(..., description="Quality score (0-100)")
    reliability_score: float = Field(..., description="Reliability score (0-100)")
    collaboration_score: float = Field(..., description="Collaboration score (0-100)")
    innovation_score: float = Field(..., description="Innovation score (0-100)")


class TimeReportSummaryData(BaseModel):
    """Time report summary data."""
    total_hours: float = Field(..., description="Total hours logged")
    total_days: int = Field(..., description="Total days with time entries")
    average_hours_per_day: float = Field(..., description="Average hours per day")
    total_entries: int = Field(..., description="Total number of time entries")
    approved_entries: int = Field(..., description="Number of approved entries")
    pending_entries: int = Field(..., description="Number of pending entries")
    approval_rate: float = Field(..., description="Approval rate percentage")


class TimeReportByProjectData(BaseModel):
    """Time report data by project."""
    project_id: str = Field(..., description="Project ID")
    project_name: str = Field(..., description="Project name")
    hours: float = Field(..., description="Hours logged on project")
    percentage: float = Field(..., description="Percentage of total time")
    entries_count: int = Field(..., description="Number of time entries")
    average_hours_per_entry: float = Field(..., description="Average hours per entry")


class TimeReportByCategoryData(BaseModel):
    """Time report data by category."""
    category: str = Field(..., description="Time entry category")
    hours: float = Field(..., description="Hours logged in category")
    percentage: float = Field(..., description="Percentage of total time")
    entries_count: int = Field(..., description="Number of time entries")


class TimeReportDailyData(BaseModel):
    """Time report daily breakdown data."""
    work_date: date = Field(..., description="Date")
    hours: float = Field(..., description="Hours logged on date")
    entries_count: int = Field(..., description="Number of time entries")
    projects_count: int = Field(..., description="Number of projects worked on")


class TimeReportByUserData(BaseModel):
    """Time report data by user."""
    user_id: str = Field(..., description="User ID")
    user_name: str = Field(..., description="User name")
    hours: float = Field(..., description="Hours logged by user")
    percentage: float = Field(..., description="Percentage of total time")
    entries_count: int = Field(..., description="Number of time entries")
    average_hours_per_day: float = Field(..., description="Average hours per day")


class ProjectFinancialData(BaseModel):
    """Project financial data for reports."""
    total_budget: Optional[Decimal] = Field(None, description="Total project budget")
    spent_amount: Optional[Decimal] = Field(None, description="Amount spent so far")
    remaining_budget: Optional[Decimal] = Field(None, description="Remaining budget")
    budget_utilization_percentage: Optional[float] = Field(None, description="Budget utilization percentage")
    cost_per_hour: Optional[Decimal] = Field(None, description="Average cost per hour")
    total_hours_billed: float = Field(..., description="Total hours billed")
    estimated_completion_cost: Optional[Decimal] = Field(None, description="Estimated cost at completion")


class TeamMemberPerformance(BaseModel):
    """Team member performance data for reports."""
    user: UserResponse = Field(..., description="Team member information")
    tasks_assigned: int = Field(..., description="Number of tasks assigned")
    completion_rate: float = Field(..., description="Task completion rate (0-100)")
    time_logged: float = Field(..., description="Total time logged in hours")
    average_task_duration: Optional[float] = Field(None, description="Average task duration in hours")
    on_time_delivery_rate: float = Field(..., description="On-time delivery rate (0-100)")


class MilestoneReportData(BaseModel):
    """Milestone data for reports."""
    milestone_id: str = Field(..., description="Milestone ID")
    title: str = Field(..., description="Milestone title")
    description: Optional[str] = Field(None, description="Milestone description")
    due_date: date = Field(..., description="Milestone due date")
    status: str = Field(..., description="Milestone status")
    completion_percentage: float = Field(..., description="Completion percentage (0-100)")
    tasks_count: int = Field(..., description="Number of tasks in milestone")
    completed_tasks: int = Field(..., description="Number of completed tasks")
    is_overdue: bool = Field(..., description="Whether milestone is overdue")
    days_remaining: Optional[int] = Field(None, description="Days remaining until due date")


class TaskAnalysisData(BaseModel):
    """Task analysis data for reports."""
    total_tasks: int = Field(..., description="Total number of tasks")
    tasks_by_status: Dict[str, int] = Field(..., description="Tasks grouped by status")
    tasks_by_priority: Dict[str, int] = Field(..., description="Tasks grouped by priority")
    tasks_by_assignee: Dict[str, int] = Field(..., description="Tasks grouped by assignee")
    average_task_duration: float = Field(..., description="Average task duration in hours")
    longest_running_task: Optional[str] = Field(None, description="Longest running task")
    shortest_completed_task: Optional[str] = Field(None, description="Shortest completed task")
    dependency_analysis: Dict[str, Any] = Field(..., description="Task dependency analysis")


class PerformanceReportResponse(BaseModel):
    """Response model for performance reports."""
    report_id: str = Field(..., description="Unique report ID")
    report_type: PerformanceReportType = Field(..., description="Type of performance report generated")
    generated_at: datetime = Field(..., description="Report generation timestamp")
    period_start: Optional[date] = Field(None, description="Report period start date")
    period_end: Optional[date] = Field(None, description="Report period end date")
    summary: PerformanceSummaryData = Field(..., description="Performance summary data")
    individual_performances: List[IndividualPerformanceData] = Field(..., description="Individual performance data")
    team_performance: Optional[TeamPerformanceData] = Field(None, description="Team performance data")
    performance_metrics: PerformanceMetricsData = Field(..., description="Detailed performance metrics")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class PerformanceReportExportResponse(BaseModel):
    """Response model for performance report exports."""
    export_id: str = Field(..., description="Unique export ID")
    filename: str = Field(..., description="Generated filename")
    format: ReportFormat = Field(..., description="Export format")
    download_url: str = Field(..., description="Download URL for the exported file")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    expires_at: datetime = Field(..., description="Expiration timestamp for download link")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TimeReportResponse(BaseModel):
    """Response model for time reports."""
    report_id: str = Field(..., description="Unique report ID")
    report_type: TimeReportType = Field(..., description="Type of time report generated")
    generated_at: datetime = Field(..., description="Report generation timestamp")
    period_start: Optional[date] = Field(None, description="Report period start date")
    period_end: Optional[date] = Field(None, description="Report period end date")
    summary: TimeReportSummaryData = Field(..., description="Time summary data")
    by_project: List[TimeReportByProjectData] = Field(..., description="Time data by project")
    by_category: List[TimeReportByCategoryData] = Field(..., description="Time data by category")
    by_user: List[TimeReportByUserData] = Field(..., description="Time data by user")
    daily_breakdown: List[TimeReportDailyData] = Field(..., description="Daily time breakdown")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TimeReportExportResponse(BaseModel):
    """Response model for time report exports."""
    export_id: str = Field(..., description="Unique export ID")
    filename: str = Field(..., description="Generated filename")
    format: ReportFormat = Field(..., description="Export format")
    download_url: str = Field(..., description="Download URL for the exported file")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    expires_at: datetime = Field(..., description="Expiration timestamp for download link")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ProjectReportResponse(BaseModel):
    """Response model for project reports."""
    report_id: str = Field(..., description="Unique report ID")
    project: ProjectResponse = Field(..., description="Project information")
    report_type: ReportType = Field(..., description="Type of report generated")
    generated_at: datetime = Field(..., description="Report generation timestamp")
    period_start: Optional[date] = Field(None, description="Report period start date")
    period_end: Optional[date] = Field(None, description="Report period end date")
    summary: ProjectSummaryData = Field(..., description="Project summary data")
    financial_data: Optional[ProjectFinancialData] = Field(None, description="Financial data")
    team_performance: List[TeamMemberPerformance] = Field(..., description="Team performance data")
    milestones: List[MilestoneReportData] = Field(..., description="Milestone data")
    task_analysis: Optional[TaskAnalysisData] = Field(None, description="Task analysis data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ProjectReportExportResponse(BaseModel):
    """Response model for project report exports."""
    export_id: str = Field(..., description="Unique export ID")
    filename: str = Field(..., description="Generated filename")
    format: ReportFormat = Field(..., description="Export format")
    download_url: str = Field(..., description="Download URL for the exported file")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    expires_at: datetime = Field(..., description="Expiration timestamp for download link")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ReportsListResponse(BaseModel):
    """Response model for listing available reports."""
    reports: List[ProjectReportResponse] = Field(..., description="List of available reports")
    total_count: int = Field(..., description="Total number of reports")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")


class ReportGenerationStatus(BaseModel):
    """Status model for report generation."""
    report_id: str = Field(..., description="Report ID")
    status: str = Field(..., description="Generation status")
    progress: Optional[float] = Field(None, description="Generation progress (0-100)")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp") 