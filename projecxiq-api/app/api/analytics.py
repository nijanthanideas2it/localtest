"""
Analytics API endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import date

from app.db.database import AsyncSessionWrapper, get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.services.analytics_service import AnalyticsService
from app.services.project_service import ProjectService
from app.schemas.analytics import (
    ProjectProgressWrapper,
    ProjectTimelineWrapper,
    DashboardSummaryWrapper,
    AnalyticsFilterRequest
)

router = APIRouter(prefix="/projects", tags=["Project Analytics"])


@router.get("/{project_id}/analytics", response_model=ProjectProgressWrapper)
async def get_project_analytics(
    project_id: str,
    start_date: Optional[str] = Query(None, description="Start date for analytics period (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date for analytics period (YYYY-MM-DD)"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive project analytics.
    
    Args:
        project_id: Project ID
        start_date: Optional start date for analytics period
        end_date: Optional end date for analytics period
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Project analytics data
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
        
        # Parse dates if provided
        parsed_start_date = None
        parsed_end_date = None
        
        if start_date:
            try:
                parsed_start_date = date.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use YYYY-MM-DD"
                )
        
        if end_date:
            try:
                parsed_end_date = date.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format. Use YYYY-MM-DD"
                )
        
        # Validate date range
        if parsed_start_date and parsed_end_date and parsed_start_date > parsed_end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date cannot be after end date"
            )
        
        # Get analytics data
        analytics_data = AnalyticsService.get_project_analytics(
            db.session,
            project_id,
            parsed_start_date,
            parsed_end_date
        )
        
        if not analytics_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project analytics not found"
            )
        
        return ProjectProgressWrapper(
            success=True,
            data=analytics_data,
            message="Project analytics retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{project_id}/progress", response_model=ProjectProgressWrapper)
async def get_project_progress(
    project_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get project progress report.
    
    Args:
        project_id: Project ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Project progress data
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
        
        # Get analytics data (progress is part of analytics)
        analytics_data = AnalyticsService.get_project_analytics(db.session, project_id)
        
        if not analytics_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project progress not found"
            )
        
        return ProjectProgressWrapper(
            success=True,
            data=analytics_data,
            message="Project progress retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{project_id}/timeline", response_model=ProjectTimelineWrapper)
async def get_project_timeline(
    project_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get project timeline with events and phases.
    
    Args:
        project_id: Project ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Project timeline data
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
        
        # Get timeline data
        timeline_data = AnalyticsService.get_project_timeline(db.session, project_id)
        
        if not timeline_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project timeline not found"
            )
        
        return ProjectTimelineWrapper(
            success=True,
            data=timeline_data,
            message="Project timeline retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/dashboard/summary", response_model=DashboardSummaryWrapper)
async def get_dashboard_summary(
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get dashboard summary for current user.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dashboard summary data
    """
    try:
        # Get dashboard summary
        summary_data = AnalyticsService.get_dashboard_summary(
            db.session,
            str(current_user.id),
            current_user.role
        )
        
        return DashboardSummaryWrapper(
            success=True,
            data=summary_data,
            message="Dashboard summary retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/{project_id}/analytics/filter", response_model=ProjectProgressWrapper)
async def get_filtered_project_analytics(
    project_id: str,
    filter_data: AnalyticsFilterRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get filtered project analytics based on criteria.
    
    Args:
        project_id: Project ID
        filter_data: Analytics filter criteria
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Filtered project analytics data
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
        
        # Validate date range
        if filter_data.start_date and filter_data.end_date and filter_data.start_date > filter_data.end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date cannot be after end date"
            )
        
        # Get analytics data with filters
        analytics_data = AnalyticsService.get_project_analytics(
            db.session,
            project_id,
            filter_data.start_date,
            filter_data.end_date
        )
        
        if not analytics_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project analytics not found"
            )
        
        # Apply filters to response
        if not filter_data.include_team_performance:
            analytics_data.team_performance = []
        
        if not filter_data.include_milestones:
            analytics_data.milestones = []
        
        # Note: Time tracking filtering would be implemented when TimeEntry model is available
        
        return ProjectProgressWrapper(
            success=True,
            data=analytics_data,
            message="Filtered project analytics retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        ) 