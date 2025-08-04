"""
Task schemas for task management operations.
"""
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, UUID4
from decimal import Decimal

from app.schemas.user import UserResponse


class TaskCreateRequest(BaseModel):
    """Task creation request model."""
    title: str = Field(..., min_length=1, max_length=255, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    assignee_id: Optional[UUID4] = Field(None, description="Task assignee ID")
    priority: str = Field("Medium", description="Task priority")
    estimated_hours: Optional[Decimal] = Field(None, ge=0, description="Estimated hours")
    due_date: Optional[date] = Field(None, description="Task due date")
    dependencies: Optional[List[UUID4]] = Field(default=[], description="List of prerequisite task IDs")

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        """Validate priority is valid."""
        valid_priorities = ['Low', 'Medium', 'High', 'Critical']
        if v not in valid_priorities:
            raise ValueError(f"Priority must be one of: {', '.join(valid_priorities)}")
        return v

    @field_validator('dependencies')
    @classmethod
    def validate_dependencies(cls, v):
        """Validate dependencies list."""
        if v is None:
            return []
        return v

    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v):
        """Validate due date is not in the past."""
        if v is not None and v < date.today():
            raise ValueError("Due date cannot be in the past")
        return v


class TaskUpdateRequest(BaseModel):
    """Task update request model."""
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    assignee_id: Optional[UUID4] = Field(None, description="Task assignee ID")
    status: Optional[str] = Field(None, description="Task status")
    priority: Optional[str] = Field(None, description="Task priority")
    estimated_hours: Optional[Decimal] = Field(None, ge=0, description="Estimated hours")
    due_date: Optional[date] = Field(None, description="Task due date")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validate status is valid."""
        if v is not None:
            valid_statuses = ['ToDo', 'InProgress', 'Review', 'Done']
            if v not in valid_statuses:
                raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        """Validate priority is valid."""
        if v is not None:
            valid_priorities = ['Low', 'Medium', 'High', 'Critical']
            if v not in valid_priorities:
                raise ValueError(f"Priority must be one of: {', '.join(valid_priorities)}")
        return v

    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v):
        """Validate due date is not in the past."""
        if v is not None and v < date.today():
            raise ValueError("Due date cannot be in the past")
        return v


class TaskDependencyRequest(BaseModel):
    """Task dependency request model."""
    prerequisite_task_id: UUID4 = Field(..., description="ID of the prerequisite task")
    dependency_type: str = Field("Blocks", description="Type of dependency")

    @field_validator('dependency_type')
    @classmethod
    def validate_dependency_type(cls, v):
        """Validate dependency type is valid."""
        valid_types = ['Blocks', 'DependsOn', 'RelatedTo']
        if v not in valid_types:
            raise ValueError(f"Dependency type must be one of: {', '.join(valid_types)}")
        return v


class TaskAssignmentRequest(BaseModel):
    """Task assignment request model."""
    assignee_id: UUID4 = Field(..., description="ID of the user to assign the task to")

    @field_validator('assignee_id')
    @classmethod
    def validate_assignee_id(cls, v):
        """Validate assignee ID is not empty."""
        if not v:
            raise ValueError("Assignee ID cannot be empty")
        return v


class TaskStatusRequest(BaseModel):
    """Task status update request model."""
    status: str = Field(..., description="New task status")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validate status is valid."""
        valid_statuses = ['ToDo', 'InProgress', 'Review', 'Done']
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v


class TaskSearchRequest(BaseModel):
    """Task search request model."""
    query: str = Field(..., min_length=1, max_length=255, description="Search query")
    project_id: Optional[UUID4] = Field(None, description="Limit search to specific project")
    limit: Optional[int] = Field(20, ge=1, le=100, description="Maximum number of results")

    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        """Validate search query is not empty."""
        if not v.strip():
            raise ValueError("Search query cannot be empty")
        return v.strip()


class TaskFilterRequest(BaseModel):
    """Task filter request model."""
    status: Optional[str] = Field(None, description="Filter by task status")
    priority: Optional[str] = Field(None, description="Filter by task priority")
    assignee_id: Optional[UUID4] = Field(None, description="Filter by assignee")
    project_id: Optional[UUID4] = Field(None, description="Filter by project")
    due_date_from: Optional[date] = Field(None, description="Filter by due date from")
    due_date_to: Optional[date] = Field(None, description="Filter by due date to")
    created_date_from: Optional[date] = Field(None, description="Filter by creation date from")
    created_date_to: Optional[date] = Field(None, description="Filter by creation date to")
    has_dependencies: Optional[bool] = Field(None, description="Filter by tasks with/without dependencies")
    is_overdue: Optional[bool] = Field(None, description="Filter by overdue tasks")
    limit: Optional[int] = Field(20, ge=1, le=100, description="Maximum number of results")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validate status is valid."""
        if v is not None:
            valid_statuses = ['ToDo', 'InProgress', 'Review', 'Done']
            if v not in valid_statuses:
                raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        """Validate priority is valid."""
        if v is not None:
            valid_priorities = ['Low', 'Medium', 'High', 'Critical']
            if v not in valid_priorities:
                raise ValueError(f"Priority must be one of: {', '.join(valid_priorities)}")
        return v

    @field_validator('due_date_to')
    @classmethod
    def validate_due_date_range(cls, v, values):
        """Validate due date range is valid."""
        if v is not None and 'due_date_from' in values and values['due_date_from'] is not None:
            if v < values['due_date_from']:
                raise ValueError("Due date 'to' must be after due date 'from'")
        return v

    @field_validator('created_date_to')
    @classmethod
    def validate_created_date_range(cls, v, values):
        """Validate created date range is valid."""
        if v is not None and 'created_date_from' in values and values['created_date_from'] is not None:
            if v < values['created_date_from']:
                raise ValueError("Created date 'to' must be after created date 'from'")
        return v


class TaskSortRequest(BaseModel):
    """Task sort request model."""
    sort_by: str = Field("created_at", description="Field to sort by")
    sort_order: str = Field("desc", description="Sort order (asc or desc)")
    limit: Optional[int] = Field(20, ge=1, le=100, description="Maximum number of results")

    @field_validator('sort_by')
    @classmethod
    def validate_sort_by(cls, v):
        """Validate sort field is valid."""
        valid_fields = ['title', 'status', 'priority', 'due_date', 'created_at', 'updated_at', 'estimated_hours']
        if v not in valid_fields:
            raise ValueError(f"Sort field must be one of: {', '.join(valid_fields)}")
        return v

    @field_validator('sort_order')
    @classmethod
    def validate_sort_order(cls, v):
        """Validate sort order is valid."""
        if v not in ['asc', 'desc']:
            raise ValueError("Sort order must be 'asc' or 'desc'")
        return v


class TaskDependencyResponse(BaseModel):
    """Task dependency response model."""
    id: UUID4
    dependent_task_id: UUID4
    prerequisite_task_id: UUID4
    dependency_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class TaskAssigneeResponse(BaseModel):
    """Task assignee response model."""
    id: str
    first_name: str
    last_name: str
    email: Optional[str] = None

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        """Convert UUID objects to strings."""
        if hasattr(v, 'hex'):
            return str(v)
        return v

    class Config:
        from_attributes = True


class TaskProjectResponse(BaseModel):
    """Task project response model."""
    id: str
    name: str

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        """Convert UUID objects to strings."""
        if hasattr(v, 'hex'):
            return str(v)
        return v

    class Config:
        from_attributes = True


class TaskDependencySummaryResponse(BaseModel):
    """Task dependency summary response model."""
    id: UUID4
    title: str
    status: str

    class Config:
        from_attributes = True


class TaskTimeEntryResponse(BaseModel):
    """Task time entry response model."""
    id: UUID4
    hours: Decimal
    date: date
    category: str
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class TaskCommentResponse(BaseModel):
    """Task comment response model."""
    id: UUID4
    content: str
    author: Dict[str, str]
    created_at: datetime

    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    """Task response model."""
    id: str
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    estimated_hours: Optional[Decimal] = None
    actual_hours: Optional[Decimal] = None
    due_date: Optional[date] = None
    assignee: Optional[TaskAssigneeResponse] = None
    dependencies_count: int = 0
    created_at: datetime

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        """Convert UUID objects to strings."""
        if hasattr(v, 'hex'):
            return str(v)
        return v

    class Config:
        from_attributes = True


class TaskDetailResponse(BaseModel):
    """Task detail response model."""
    id: str
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    estimated_hours: Optional[Decimal] = None
    actual_hours: Optional[Decimal] = None
    due_date: Optional[date] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        """Convert UUID objects to strings."""
        if hasattr(v, 'hex'):
            return str(v)
        return v
    project: TaskProjectResponse
    assignee: Optional[TaskAssigneeResponse] = None
    dependencies: List[TaskDependencySummaryResponse] = []
    dependents: List[TaskDependencySummaryResponse] = []
    time_entries: List[TaskTimeEntryResponse] = []
    comments: List[TaskCommentResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Task list response model."""
    success: bool = True
    data: List[TaskResponse]
    message: str = "Tasks retrieved successfully"


class TaskCreateResponseWrapper(BaseModel):
    """Task creation response wrapper."""
    success: bool = True
    data: TaskDetailResponse
    message: str = "Task created successfully"


class TaskUpdateResponseWrapper(BaseModel):
    """Task update response wrapper."""
    success: bool = True
    data: TaskDetailResponse
    message: str = "Task updated successfully"


class TaskDeleteResponseWrapper(BaseModel):
    """Task deletion response wrapper."""
    success: bool = True
    message: str = "Task deleted successfully"


class TaskDetailResponseWrapper(BaseModel):
    """Task detail response wrapper."""
    success: bool = True
    data: TaskDetailResponse
    message: str = "Task retrieved successfully"


class TaskDependencyCreateResponseWrapper(BaseModel):
    """Task dependency creation response wrapper."""
    success: bool = True
    data: TaskDependencyResponse
    message: str = "Task dependency created successfully"


class TaskStatsResponse(BaseModel):
    """Task statistics response model."""
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    todo_tasks: int
    overdue_tasks: int
    completion_percentage: float
    average_completion_time_hours: Optional[float] = None

    class Config:
        from_attributes = True


class TaskStatsWrapper(BaseModel):
    """Task statistics response wrapper."""
    success: bool = True
    data: TaskStatsResponse
    message: str = "Task statistics retrieved successfully" 