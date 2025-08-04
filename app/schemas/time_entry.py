"""
Time entry schemas for the Project Management Dashboard.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, UUID4

from app.schemas.user import UserResponse
from app.schemas.project import ProjectResponse
from app.schemas.task import TaskResponse


class TimeEntryCreateRequest(BaseModel):
    """Time entry creation request model."""
    task_id: Optional[UUID4] = Field(None, description="Associated task ID")
    project_id: UUID4 = Field(..., description="Associated project ID")
    hours: Decimal = Field(..., gt=0, le=24, description="Hours worked (0 < hours <= 24)")
    work_date: date = Field(..., description="Date of work")
    category: str = Field(..., description="Work category")
    notes: Optional[str] = Field(None, description="Additional notes")

    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        """Validate category is valid."""
        valid_categories = ['Development', 'Testing', 'Documentation', 'Meeting', 'Other']
        if v not in valid_categories:
            raise ValueError(f"Category must be one of: {', '.join(valid_categories)}")
        return v

    @field_validator('work_date')
    @classmethod
    def validate_work_date(cls, v):
        """Validate date is not in the future."""
        if v > date.today():
            raise ValueError("Date cannot be in the future")
        return v

    @field_validator('hours')
    @classmethod
    def validate_hours(cls, v):
        """Validate hours is within reasonable range."""
        if v <= 0:
            raise ValueError("Hours must be greater than 0")
        if v > 24:
            raise ValueError("Hours cannot exceed 24")
        return v


class TimeEntryUpdateRequest(BaseModel):
    """Time entry update request model."""
    hours: Optional[Decimal] = Field(None, gt=0, le=24, description="Hours worked (0 < hours <= 24)")
    category: Optional[str] = Field(None, description="Work category")
    notes: Optional[str] = Field(None, description="Additional notes")

    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        """Validate category is valid."""
        if v is not None:
            valid_categories = ['Development', 'Testing', 'Documentation', 'Meeting', 'Other']
            if v not in valid_categories:
                raise ValueError(f"Category must be one of: {', '.join(valid_categories)}")
        return v

    @field_validator('hours')
    @classmethod
    def validate_hours(cls, v):
        """Validate hours is within reasonable range."""
        if v is not None:
            if v <= 0:
                raise ValueError("Hours must be greater than 0")
            if v > 24:
                raise ValueError("Hours cannot exceed 24")
        return v


class TimeEntryResponse(BaseModel):
    """Time entry response model."""
    id: UUID4
    user_id: UUID4
    task_id: Optional[UUID4]
    project_id: UUID4
    hours: Decimal
    work_date: date
    category: str
    notes: Optional[str]
    is_approved: bool
    approved_by: Optional[UUID4]
    approved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TimeEntryDetailResponse(BaseModel):
    """Time entry detail response model with related data."""
    id: UUID4
    user_id: UUID4
    task_id: Optional[UUID4]
    project_id: UUID4
    hours: Decimal
    work_date: date
    category: str
    notes: Optional[str]
    is_approved: bool
    approved_by: Optional[UUID4]
    approved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    user: UserResponse
    task: Optional[TaskResponse]
    project: ProjectResponse
    approved_by_user: Optional[UserResponse]

    class Config:
        from_attributes = True


class TimeEntryListResponse(BaseModel):
    """Time entry list response model."""
    success: bool
    data: List[TimeEntryDetailResponse]
    message: str
    pagination: Optional[dict] = None


class TimeEntryCreateResponseWrapper(BaseModel):
    """Time entry creation response wrapper."""
    success: bool
    data: TimeEntryDetailResponse
    message: str


class TimeEntryUpdateResponseWrapper(BaseModel):
    """Time entry update response wrapper."""
    success: bool
    data: TimeEntryDetailResponse
    message: str


class TimeEntryDeleteResponseWrapper(BaseModel):
    """Time entry deletion response wrapper."""
    success: bool
    message: str


class TimeEntryDetailResponseWrapper(BaseModel):
    """Time entry detail response wrapper."""
    success: bool
    data: TimeEntryDetailResponse
    message: str


class TimeEntryFilterRequest(BaseModel):
    """Time entry filter request model."""
    project_id: Optional[UUID4] = Field(None, description="Filter by project ID")
    task_id: Optional[UUID4] = Field(None, description="Filter by task ID")
    start_date: Optional[date] = Field(None, description="Filter by start date")
    end_date: Optional[date] = Field(None, description="Filter by end date")
    category: Optional[str] = Field(None, description="Filter by category")
    is_approved: Optional[bool] = Field(None, description="Filter by approval status")
    page: Optional[int] = Field(1, ge=1, description="Page number")
    limit: Optional[int] = Field(20, ge=1, le=100, description="Items per page")

    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        """Validate category is valid."""
        if v is not None:
            valid_categories = ['Development', 'Testing', 'Documentation', 'Meeting', 'Other']
            if v not in valid_categories:
                raise ValueError(f"Category must be one of: {', '.join(valid_categories)}")
        return v

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, values):
        """Validate date range is valid."""
        if v is not None and 'start_date' in values and values['start_date'] is not None:
            if v < values['start_date']:
                raise ValueError("End date must be after start date")
        return v


class TimeEntryApprovalRequest(BaseModel):
    """Time entry approval request model."""
    approval_notes: Optional[str] = Field(None, description="Optional approval notes")


class TimeEntryRejectionRequest(BaseModel):
    """Time entry rejection request model."""
    rejection_reason: str = Field(..., min_length=1, max_length=500, description="Reason for rejection")


class TimeEntryApprovalResponse(BaseModel):
    """Time entry approval response model."""
    id: UUID4
    is_approved: bool
    approved_at: Optional[datetime]
    approved_by: Optional[UUID4]
    approval_notes: Optional[str]

    class Config:
        from_attributes = True


class TimeEntryApprovalResponseWrapper(BaseModel):
    """Time entry approval response wrapper."""
    success: bool
    data: TimeEntryApprovalResponse
    message: str


class TimeEntryRejectionResponseWrapper(BaseModel):
    """Time entry rejection response wrapper."""
    success: bool
    data: TimeEntryDetailResponse
    message: str


class PendingTimeEntriesResponse(BaseModel):
    """Pending time entries response model."""
    success: bool
    data: List[TimeEntryDetailResponse]
    message: str
    pagination: Optional[dict] = None


class ApprovedTimeEntriesResponse(BaseModel):
    """Approved time entries response model."""
    success: bool
    data: List[TimeEntryDetailResponse]
    message: str
    pagination: Optional[dict] = None


# Analytics Schemas
class TimeAnalyticsData(BaseModel):
    """Time analytics data model."""
    total_hours: Decimal
    total_entries: int
    average_hours_per_day: Decimal
    average_hours_per_entry: Decimal
    hours_by_category: Dict[str, Decimal]
    hours_by_project: Dict[str, Decimal]
    hours_by_user: Dict[str, Decimal]
    entries_by_status: Dict[str, int]
    top_productive_days: List[Dict[str, Any]]
    weekly_trends: List[Dict[str, Any]]
    monthly_summary: Dict[str, Any]


class TimeAnalyticsResponse(BaseModel):
    """Time analytics response model."""
    success: bool
    data: TimeAnalyticsData
    message: str


class TimeReportData(BaseModel):
    """Time report data model."""
    report_id: str
    report_type: str
    generated_at: datetime
    date_range: Dict[str, date]
    summary: Dict[str, Any]
    detailed_data: List[Dict[str, Any]]
    export_url: Optional[str] = None


class TimeReportResponse(BaseModel):
    """Time report response model."""
    success: bool
    data: TimeReportData
    message: str


class TimeSummaryData(BaseModel):
    """Time summary data model."""
    period: str
    total_hours: Decimal
    total_entries: int
    approved_hours: Decimal
    pending_hours: Decimal
    rejected_hours: Decimal
    average_hours_per_day: Decimal
    most_productive_category: str
    most_productive_project: str
    completion_rate: Decimal


class TimeSummaryResponse(BaseModel):
    """Time summary response model."""
    success: bool
    data: TimeSummaryData
    message: str 