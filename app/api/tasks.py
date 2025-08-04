"""
Tasks API endpoints.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status as http_status, Query
from sqlalchemy.orm import Session

from app.db.database import AsyncSessionWrapper, get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.services.task_service import TaskService
from app.services.project_service import ProjectService
from app.models.task import Task, TaskDependency
from app.schemas.task import (
    TaskCreateRequest,
    TaskUpdateRequest,
    TaskDependencyRequest,
    TaskDependencyResponse,
    TaskAssignmentRequest,
    TaskStatusRequest,
    TaskSearchRequest,
    TaskFilterRequest,
    TaskSortRequest,
    TaskCreateResponseWrapper,
    TaskUpdateResponseWrapper,
    TaskDeleteResponseWrapper,
    TaskListResponse,
    TaskDetailResponseWrapper,
    TaskDependencyCreateResponseWrapper,
    TaskStatsWrapper,
    TaskResponse
)

router = APIRouter(prefix="/projects", tags=["Task Management"])


@router.get("/tasks/all")
async def get_all_tasks(
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all tasks for testing."""
    try:
        from app.models.task import Task
        tasks = db.session.query(Task).limit(10).all()
        
        task_list = []
        for task in tasks:
            task_response = TaskResponse(
                id=task.id,
                title=task.title,
                description=task.description,
                status=task.status,
                priority=task.priority,
                estimated_hours=task.estimated_hours,
                actual_hours=task.actual_hours,
                due_date=task.due_date,
                assignee=None,
                dependencies_count=0,
                created_at=task.created_at
            )
            task_list.append(task_response)
        
        return TaskListResponse(
            success=True,
            data=task_list,
            message="Tasks retrieved successfully"
        )
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


@router.get("/debug/tasks")
async def debug_tasks(
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Debug endpoint to test task queries."""
    try:
        from app.models.task import Task
        # Simple query to test
        tasks = db.session.query(Task).limit(5).all()
        return {
            "success": True,
            "count": len(tasks),
            "tasks": [
                {
                    "id": str(t.id),
                    "title": t.title,
                    "status": t.status,
                    "priority": t.priority,
                    "project_id": str(t.project_id) if t.project_id else None
                }
                for t in tasks
            ]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


@router.get("/{project_id}/tasks", response_model=TaskListResponse)
async def get_project_tasks(
    project_id: str,
    task_status_filter: Optional[str] = Query(None, description="Filter by task status"),
    assignee_id: Optional[str] = Query(None, description="Filter by assignee ID"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    search: Optional[str] = Query(None, description="Search by task title"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all tasks for a project with optional filtering.
    """
    try:
        # Get project and check access permissions
        project = ProjectService.get_project_by_id(db.session, project_id)
        
        if not project:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check access permissions
        if not ProjectService.can_access_project(project, str(current_user.id), current_user.role):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project"
            )
        
        # Simple query without complex relationships
        query = db.session.query(Task).filter(Task.project_id == project_id)
        
        # Apply filters
        if task_status_filter:
            query = query.filter(Task.status == task_status_filter)
        
        if assignee_id:
            query = query.filter(Task.assignee_id == assignee_id)
        
        if priority:
            query = query.filter(Task.priority == priority)
        
        if search:
            query = query.filter(Task.title.ilike(f"%{search}%"))
        
        tasks = query.order_by(Task.created_at.desc()).all()
        
        # Convert to response models
        task_list = []
        for task in tasks:
            # Simple dependencies count without loading relationships
            dependencies_count = db.session.query(TaskDependency).filter(
                TaskDependency.dependent_task_id == task.id
            ).count()
            
            task_response = TaskResponse(
                id=task.id,
                title=task.title,
                description=task.description,
                status=task.status,
                priority=task.priority,
                estimated_hours=task.estimated_hours,
                actual_hours=task.actual_hours,
                due_date=task.due_date,
                assignee=None,  # Don't load assignee for now
                dependencies_count=dependencies_count,
                created_at=task.created_at
            )
            task_list.append(task_response)
        
        return TaskListResponse(
            success=True,
            data=task_list,
            message="Tasks retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in get_project_tasks: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/tasks/{task_id}", response_model=TaskDetailResponseWrapper)
async def get_task(
    task_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific task details.
    
    Args:
        task_id: Task ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Task details
    """
    try:
        # Get task
        task = TaskService.get_task_by_id(db.session, task_id)
        
        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Check access permissions
        if not TaskService.can_access_task(task, str(current_user.id), current_user.role):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this task"
            )
        
        return TaskDetailResponseWrapper(
            success=True,
            data=task,
            message="Task retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/{project_id}/tasks", response_model=TaskCreateResponseWrapper, status_code=http_status.HTTP_201_CREATED)
async def create_task(
    project_id: str,
    task_data: TaskCreateRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create new task in project.
    
    Args:
        project_id: Project ID
        task_data: Task creation data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created task details
    """
    try:
        # Get project and check permissions
        project = ProjectService.get_project_by_id(db.session, project_id)
        
        if not project:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check if user can access the project (team member or manager)
        if not ProjectService.can_access_project(project, str(current_user.id), current_user.role):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project"
            )
        
        task = TaskService.create_task(
            db.session,
            project_id,
            task_data,
            str(current_user.id)
        )
        
        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Failed to create task"
            )
        
        return TaskCreateResponseWrapper(
            success=True,
            data=task,
            message="Task created successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.put("/tasks/{task_id}", response_model=TaskUpdateResponseWrapper)
async def update_task(
    task_id: str,
    update_data: TaskUpdateRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update task details.
    
    Args:
        task_id: Task ID
        update_data: Task update data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated task details
    """
    try:
        # Get task and check permissions
        task = TaskService.get_task_by_id(db.session, task_id)
        
        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Check management permissions
        if not TaskService.can_manage_task(task, str(current_user.id), current_user.role):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this task"
            )
        
        updated_task = TaskService.update_task(
            db.session,
            task_id,
            update_data
        )
        
        if not updated_task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return TaskUpdateResponseWrapper(
            success=True,
            data=updated_task,
            message="Task updated successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/tasks/{task_id}", response_model=TaskDeleteResponseWrapper)
async def delete_task(
    task_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "ProjectManager"]))
):
    """
    Delete task.
    
    Args:
        task_id: Task ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Deletion confirmation
    """
    try:
        # Get task and check permissions
        task = TaskService.get_task_by_id(db.session, task_id)
        
        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Check management permissions
        if not TaskService.can_manage_task(task, str(current_user.id), current_user.role):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this task"
            )
        
        success = TaskService.delete_task(db.session, task_id)
        
        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return TaskDeleteResponseWrapper(
            success=True,
            message="Task deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/tasks/{task_id}/dependencies", response_model=List[TaskDependencyResponse])
async def get_task_dependencies(
    task_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get task dependencies.
    
    Args:
        task_id: Task ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of task dependencies
    """
    try:
        # Get task and check access permissions
        task = TaskService.get_task_by_id(db.session, task_id)
        
        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Check access permissions
        if not TaskService.can_access_task(task, str(current_user.id), current_user.role):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this task"
            )
        
        # Get dependencies
        dependencies = TaskService.get_task_dependencies(db.session, task_id)
        
        return dependencies
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/tasks/{task_id}/dependencies", response_model=TaskDependencyCreateResponseWrapper, status_code=http_status.HTTP_201_CREATED)
async def add_task_dependency(
    task_id: str,
    dependency_data: TaskDependencyRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "ProjectManager"]))
):
    """
    Add dependency to task.
    
    Args:
        task_id: Task ID
        dependency_data: Dependency data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created dependency details
    """
    try:
        # Get task and check permissions
        task = TaskService.get_task_by_id(db.session, task_id)
        
        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Check management permissions
        if not TaskService.can_manage_task(task, str(current_user.id), current_user.role):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Not authorized to manage dependencies for this task"
            )
        
        dependency = TaskService.add_task_dependency(
            db.session,
            task_id,
            dependency_data
        )
        
        if not dependency:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Failed to create dependency"
            )
        
        return TaskDependencyCreateResponseWrapper(
            success=True,
            data=dependency,
            message="Task dependency created successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/tasks/{task_id}/dependencies/{prerequisite_task_id}", response_model=TaskDeleteResponseWrapper)
async def remove_task_dependency(
    task_id: str,
    prerequisite_task_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "ProjectManager"]))
):
    """
    Remove dependency from task.
    
    Args:
        task_id: Task ID
        prerequisite_task_id: Prerequisite task ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Removal confirmation
    """
    try:
        # Get task and check permissions
        task = TaskService.get_task_by_id(db.session, task_id)
        
        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Check management permissions
        if not TaskService.can_manage_task(task, str(current_user.id), current_user.role):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Not authorized to manage dependencies for this task"
            )
        
        success = TaskService.remove_task_dependency(
            db.session,
            task_id,
            prerequisite_task_id
        )
        
        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Dependency not found"
            )
        
        return TaskDeleteResponseWrapper(
            success=True,
            message="Task dependency removed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{project_id}/tasks/stats", response_model=TaskStatsWrapper)
async def get_project_task_stats(
    project_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get task statistics for a project.
    
    Args:
        project_id: Project ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Task statistics
    """
    try:
        # Get project and check access permissions
        project = ProjectService.get_project_by_id(db.session, project_id)
        
        if not project:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check access permissions
        if not ProjectService.can_access_project(project, str(current_user.id), current_user.role):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project"
            )
        
        # Get task statistics
        stats = TaskService.get_task_statistics(db.session, project_id)
        
        return TaskStatsWrapper(
            success=True,
            data=stats,
            message="Task statistics retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.put("/tasks/{task_id}/assign", response_model=TaskUpdateResponseWrapper)
async def assign_task(
    task_id: str,
    assignment_data: TaskAssignmentRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "ProjectManager"]))
):
    """
    Assign task to a user.
    
    Args:
        task_id: Task ID
        assignment_data: Assignment data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated task details
    """
    try:
        # Get task and check permissions
        task = TaskService.get_task_by_id(db.session, task_id)
        
        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Check management permissions
        if not TaskService.can_manage_task(task, str(current_user.id), current_user.role):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Not authorized to assign this task"
            )
        
        updated_task = TaskService.assign_task(
            db.session,
            task_id,
            str(assignment_data.assignee_id)
        )
        
        if not updated_task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return TaskUpdateResponseWrapper(
            success=True,
            data=updated_task,
            message="Task assigned successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.put("/tasks/{task_id}/status", response_model=TaskUpdateResponseWrapper)
async def update_task_status(
    task_id: str,
    status_data: TaskStatusRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update task status.
    
    Args:
        task_id: Task ID
        status_data: Status update data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated task details
    """
    try:
        # Get task and check permissions
        task = TaskService.get_task_by_id(db.session, task_id)
        
        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Check management permissions
        if not TaskService.can_manage_task(task, str(current_user.id), current_user.role):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this task"
            )
        
        updated_task = TaskService.update_task_status(
            db.session,
            task_id,
            status_data.status
        )
        
        if not updated_task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return TaskUpdateResponseWrapper(
            success=True,
            data=updated_task,
            message="Task status updated successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/tasks/assigned", response_model=TaskListResponse)
async def get_assigned_tasks(
    task_status_filter: Optional[str] = Query(None, description="Filter by task status"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get tasks assigned to current user.
    
    Args:
        status: Optional filter by task status
        project_id: Optional filter by project ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of assigned tasks
    """
    try:
        # Validate status filter if provided
        if task_status_filter:
            valid_statuses = ['ToDo', 'InProgress', 'Review', 'Done']
            if task_status_filter not in valid_statuses:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                )
        
        # Get assigned tasks
        tasks = TaskService.get_assigned_tasks(
            db.session,
            str(current_user.id),
            status=task_status_filter,
            project_id=project_id
        )
        
        # Convert to response models
        task_list = []
        for task in tasks:
            # Calculate dependencies count
            dependencies_count = len(task.dependent_tasks)
            
            task_response = TaskResponse(
                id=task.id,
                title=task.title,
                description=task.description,
                status=task.status,
                priority=task.priority,
                estimated_hours=task.estimated_hours,
                actual_hours=task.actual_hours,
                due_date=task.due_date,
                assignee=task.assignee,
                dependencies_count=dependencies_count,
                created_at=task.created_at
            )
            task_list.append(task_response)
        
        return TaskListResponse(
            success=True,
            data=task_list,
            message="Assigned tasks retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/assigned", response_model=TaskListResponse)
async def get_assigned_tasks(
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get tasks assigned to the current user (developer).
    """
    try:
        tasks = TaskService.get_assigned_tasks(db.session, current_user.id)
        
        task_list = []
        for task in tasks:
            # Calculate dependencies count
            dependencies_count = len(task.dependent_tasks) if hasattr(task, 'dependent_tasks') else 0
            
            task_response = TaskResponse(
                id=task.id,
                title=task.title,
                description=task.description,
                status=task.status,
                priority=task.priority,
                estimated_hours=task.estimated_hours,
                actual_hours=task.actual_hours,
                due_date=task.due_date,
                assignee=task.assignee,
                dependencies_count=dependencies_count,
                created_at=task.created_at
            )
            task_list.append(task_response)
        
        return TaskListResponse(
            success=True,
            data=task_list,
            message="Assigned tasks retrieved successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/tasks/by-status", response_model=TaskListResponse)
async def get_tasks_by_status(
    task_status_filter: str = Query(..., description="Task status to filter by"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    assignee_id: Optional[str] = Query(None, description="Filter by assignee ID"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get tasks filtered by status.
    
    Args:
        status: Task status to filter by
        project_id: Optional filter by project ID
        assignee_id: Optional filter by assignee ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of tasks with the specified status
    """
    try:
        # Get tasks by status
        tasks = TaskService.get_tasks_by_status(
            db.session,
            task_status_filter,
            project_id=project_id,
            assignee_id=assignee_id
        )
        
        # Convert to response models
        task_list = []
        for task in tasks:
            # Calculate dependencies count
            dependencies_count = len(task.dependent_tasks)
            
            task_response = TaskResponse(
                id=task.id,
                title=task.title,
                description=task.description,
                status=task.status,
                priority=task.priority,
                estimated_hours=task.estimated_hours,
                actual_hours=task.actual_hours,
                due_date=task.due_date,
                assignee=task.assignee,
                dependencies_count=dependencies_count,
                created_at=task.created_at
            )
            task_list.append(task_response)
        
        return TaskListResponse(
            success=True,
            data=task_list,
            message=f"Tasks with status '{status}' retrieved successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/tasks/search", response_model=TaskListResponse)
async def search_tasks(
    query: str = Query(..., description="Search query"),
    project_id: Optional[str] = Query(None, description="Limit search to specific project"),
    limit: Optional[int] = Query(20, ge=1, le=100, description="Maximum number of results"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search tasks by text query.
    
    Args:
        query: Search query
        project_id: Optional limit to specific project
        limit: Maximum number of results
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of matching tasks
    """
    try:
        # Validate query
        if not query.strip():
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Search query cannot be empty"
            )
        
        # Search tasks
        tasks = TaskService.search_tasks(
            db.session,
            query.strip(),
            project_id=project_id,
            limit=limit
        )
        
        # Convert to response models
        task_list = []
        for task in tasks:
            # Calculate dependencies count
            dependencies_count = len(task.dependent_tasks)
            
            task_response = TaskResponse(
                id=task.id,
                title=task.title,
                description=task.description,
                status=task.status,
                priority=task.priority,
                estimated_hours=task.estimated_hours,
                actual_hours=task.actual_hours,
                due_date=task.due_date,
                assignee=task.assignee,
                dependencies_count=dependencies_count,
                created_at=task.created_at
            )
            task_list.append(task_response)
        
        return TaskListResponse(
            success=True,
            data=task_list,
            message=f"Found {len(task_list)} tasks matching '{query}'"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/tasks/filter", response_model=TaskListResponse)
async def filter_tasks(
    filter_data: TaskFilterRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Filter tasks by various criteria.
    
    Args:
        filter_data: Filter criteria
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of filtered tasks
    """
    try:
        # Filter tasks
        tasks = TaskService.filter_tasks(
            db.session,
            status=filter_data.status,
            priority=filter_data.priority,
            assignee_id=str(filter_data.assignee_id) if filter_data.assignee_id else None,
            project_id=str(filter_data.project_id) if filter_data.project_id else None,
            due_date_from=filter_data.due_date_from,
            due_date_to=filter_data.due_date_to,
            created_date_from=filter_data.created_date_from,
            created_date_to=filter_data.created_date_to,
            has_dependencies=filter_data.has_dependencies,
            is_overdue=filter_data.is_overdue,
            limit=filter_data.limit
        )
        
        # Convert to response models
        task_list = []
        for task in tasks:
            # Calculate dependencies count
            dependencies_count = len(task.dependent_tasks)
            
            task_response = TaskResponse(
                id=task.id,
                title=task.title,
                description=task.description,
                status=task.status,
                priority=task.priority,
                estimated_hours=task.estimated_hours,
                actual_hours=task.actual_hours,
                due_date=task.due_date,
                assignee=task.assignee,
                dependencies_count=dependencies_count,
                created_at=task.created_at
            )
            task_list.append(task_response)
        
        return TaskListResponse(
            success=True,
            data=task_list,
            message=f"Found {len(task_list)} tasks matching the filter criteria"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/tasks/sort", response_model=TaskListResponse)
async def sort_tasks(
    sort_data: TaskSortRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sort tasks by specified field.
    
    Args:
        sort_data: Sort criteria
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of sorted tasks
    """
    try:
        # Sort tasks
        tasks = TaskService.sort_tasks(
            db.session,
            sort_by=sort_data.sort_by,
            sort_order=sort_data.sort_order,
            limit=sort_data.limit
        )
        
        # Convert to response models
        task_list = []
        for task in tasks:
            # Calculate dependencies count
            dependencies_count = len(task.dependent_tasks)
            
            task_response = TaskResponse(
                id=task.id,
                title=task.title,
                description=task.description,
                status=task.status,
                priority=task.priority,
                estimated_hours=task.estimated_hours,
                actual_hours=task.actual_hours,
                due_date=task.due_date,
                assignee=task.assignee,
                dependencies_count=dependencies_count,
                created_at=task.created_at
            )
            task_list.append(task_response)
        
        return TaskListResponse(
            success=True,
            data=task_list,
            message=f"Retrieved {len(task_list)} tasks sorted by {sort_data.sort_by} ({sort_data.sort_order})"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        ) 