"""
Milestones API endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.database import AsyncSessionWrapper, get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.services.milestone_service import MilestoneService
from app.services.project_service import ProjectService
from app.schemas.milestone import (
    MilestoneCreateRequest,
    MilestoneUpdateRequest,
    MilestoneDependencyRequest,
    MilestoneCreateResponseWrapper,
    MilestoneUpdateResponseWrapper,
    MilestoneDeleteResponseWrapper,
    MilestoneListResponse,
    MilestoneDetailResponseWrapper,
    MilestoneDependencyCreateResponseWrapper,
    MilestoneStatsWrapper
)

router = APIRouter(prefix="/projects", tags=["Milestone Management"])


@router.get("/{project_id}/milestones", response_model=MilestoneListResponse)
async def get_project_milestones(
    project_id: str,
    is_completed: Optional[bool] = Query(None, description="Filter by completion status"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all milestones for a project.
    
    Args:
        project_id: Project ID
        is_completed: Optional filter by completion status
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of milestones
    """
    try:
        # Get project and check access permissions
        project = ProjectService.get_project_by_id(db.session, project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check access permissions
        if not ProjectService.can_access_project(project, str(current_user.id), current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project"
            )
        
        # Get milestones
        milestones = MilestoneService.get_project_milestones(db.session, project_id, is_completed)
        
        # Convert to response models
        milestone_list = []
        for milestone in milestones:
            # Calculate dependencies count
            dependencies_count = len(milestone.dependent_milestones)
            
            # Calculate completion percentage (simple calculation)
            completion_percentage = 100.0 if milestone.is_completed else 0.0
            
            milestone_response = {
                "id": milestone.id,
                "name": milestone.name,
                "description": milestone.description,
                "project_id": milestone.project_id,
                "due_date": milestone.due_date,
                "is_completed": milestone.is_completed,
                "completed_at": milestone.completed_at,
                "dependencies_count": dependencies_count,
                "completion_percentage": completion_percentage,
                "created_at": milestone.created_at,
                "updated_at": milestone.updated_at
            }
            milestone_list.append(milestone_response)
        
        return MilestoneListResponse(
            success=True,
            data=milestone_list,
            message="Milestones retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{project_id}/milestones/{milestone_id}", response_model=MilestoneDetailResponseWrapper)
async def get_milestone(
    project_id: str,
    milestone_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific milestone details.
    
    Args:
        project_id: Project ID
        milestone_id: Milestone ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Milestone details
    """
    try:
        # Get project and check access permissions
        project = ProjectService.get_project_by_id(db.session, project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check access permissions
        if not ProjectService.can_access_project(project, str(current_user.id), current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project"
            )
        
        # Get milestone
        milestone = MilestoneService.get_milestone_by_id(db.session, milestone_id)
        
        if not milestone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Milestone not found"
            )
        
        # Verify milestone belongs to the project
        if str(milestone.project_id) != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Milestone not found in this project"
            )
        
        return MilestoneDetailResponseWrapper(
            success=True,
            data=milestone,
            message="Milestone retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/{project_id}/milestones", response_model=MilestoneCreateResponseWrapper, status_code=status.HTTP_201_CREATED)
async def create_milestone(
    project_id: str,
    milestone_data: MilestoneCreateRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Project Manager"]))
):
    """
    Create new milestone for project.
    
    Args:
        project_id: Project ID
        milestone_data: Milestone creation data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created milestone details
    """
    try:
        # Get project and check permissions
        project = ProjectService.get_project_by_id(db.session, project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check management permissions
        if not ProjectService.can_manage_project(project, str(current_user.id), current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create milestones in this project"
            )
        
        milestone = MilestoneService.create_milestone(
            db.session,
            project_id,
            milestone_data,
            str(current_user.id)
        )
        
        if not milestone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create milestone"
            )
        
        return MilestoneCreateResponseWrapper(
            success=True,
            data=milestone,
            message="Milestone created successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.put("/milestones/{milestone_id}", response_model=MilestoneUpdateResponseWrapper)
async def update_milestone(
    milestone_id: str,
    update_data: MilestoneUpdateRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Project Manager"]))
):
    """
    Update milestone details.
    
    Args:
        milestone_id: Milestone ID
        update_data: Milestone update data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated milestone details
    """
    try:
        # Get milestone and check permissions
        milestone = MilestoneService.get_milestone_by_id(db.session, milestone_id)
        
        if not milestone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Milestone not found"
            )
        
        # Check management permissions
        if not MilestoneService.can_manage_milestone(milestone, str(current_user.id), current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this milestone"
            )
        
        updated_milestone = MilestoneService.update_milestone(
            db.session,
            milestone_id,
            update_data
        )
        
        if not updated_milestone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Milestone not found"
            )
        
        return MilestoneUpdateResponseWrapper(
            success=True,
            data=updated_milestone,
            message="Milestone updated successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/milestones/{milestone_id}", response_model=MilestoneDeleteResponseWrapper)
async def delete_milestone(
    milestone_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Project Manager"]))
):
    """
    Delete milestone.
    
    Args:
        milestone_id: Milestone ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Deletion confirmation
    """
    try:
        # Get milestone and check permissions
        milestone = MilestoneService.get_milestone_by_id(db.session, milestone_id)
        
        if not milestone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Milestone not found"
            )
        
        # Check management permissions
        if not MilestoneService.can_manage_milestone(milestone, str(current_user.id), current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this milestone"
            )
        
        success = MilestoneService.delete_milestone(db.session, milestone_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Milestone not found"
            )
        
        return MilestoneDeleteResponseWrapper(
            success=True,
            message="Milestone deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/milestones/{milestone_id}/dependencies", response_model=MilestoneDependencyCreateResponseWrapper, status_code=status.HTTP_201_CREATED)
async def add_milestone_dependency(
    milestone_id: str,
    dependency_data: MilestoneDependencyRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Project Manager"]))
):
    """
    Add dependency to milestone.
    
    Args:
        milestone_id: Milestone ID
        dependency_data: Dependency data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created dependency details
    """
    try:
        # Get milestone and check permissions
        milestone = MilestoneService.get_milestone_by_id(db.session, milestone_id)
        
        if not milestone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Milestone not found"
            )
        
        # Check management permissions
        if not MilestoneService.can_manage_milestone(milestone, str(current_user.id), current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to manage dependencies for this milestone"
            )
        
        dependency = MilestoneService.add_milestone_dependency(
            db.session,
            milestone_id,
            dependency_data
        )
        
        if not dependency:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create dependency"
            )
        
        return MilestoneDependencyCreateResponseWrapper(
            success=True,
            data=dependency,
            message="Milestone dependency created successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/milestones/{milestone_id}/dependencies/{prerequisite_milestone_id}", response_model=MilestoneDeleteResponseWrapper)
async def remove_milestone_dependency(
    milestone_id: str,
    prerequisite_milestone_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Project Manager"]))
):
    """
    Remove dependency from milestone.
    
    Args:
        milestone_id: Milestone ID
        prerequisite_milestone_id: Prerequisite milestone ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Removal confirmation
    """
    try:
        # Get milestone and check permissions
        milestone = MilestoneService.get_milestone_by_id(db.session, milestone_id)
        
        if not milestone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Milestone not found"
            )
        
        # Check management permissions
        if not MilestoneService.can_manage_milestone(milestone, str(current_user.id), current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to manage dependencies for this milestone"
            )
        
        success = MilestoneService.remove_milestone_dependency(
            db.session,
            milestone_id,
            prerequisite_milestone_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dependency not found"
            )
        
        return MilestoneDeleteResponseWrapper(
            success=True,
            message="Milestone dependency removed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{project_id}/milestones/stats", response_model=MilestoneStatsWrapper)
async def get_project_milestone_stats(
    project_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get milestone statistics for a project.
    
    Args:
        project_id: Project ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Milestone statistics
    """
    try:
        # Get project and check access permissions
        project = ProjectService.get_project_by_id(db.session, project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check access permissions
        if not ProjectService.can_access_project(project, str(current_user.id), current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project"
            )
        
        # Get milestone statistics
        stats = MilestoneService.get_milestone_statistics(db.session, project_id)
        
        return MilestoneStatsWrapper(
            success=True,
            data=stats,
            message="Milestone statistics retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        ) 