"""
Time entries API endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import date

from app.db.database import AsyncSessionWrapper, get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.services.time_entry_service import TimeEntryService
from app.schemas.time_entry import (
    TimeEntryCreateRequest,
    TimeEntryUpdateRequest,
    TimeEntryListResponse,
    TimeEntryCreateResponseWrapper,
    TimeEntryUpdateResponseWrapper,
    TimeEntryDeleteResponseWrapper,
    TimeEntryDetailResponseWrapper,
    TimeEntryApprovalRequest,
    TimeEntryRejectionRequest,
    TimeEntryApprovalResponseWrapper,
    TimeEntryRejectionResponseWrapper,
    PendingTimeEntriesResponse,
    ApprovedTimeEntriesResponse,
    TimeAnalyticsResponse,
    TimeReportResponse,
    TimeSummaryResponse
)

router = APIRouter(prefix="/time-entries", tags=["Time Tracking"])


@router.get("", response_model=TimeEntryListResponse)
async def get_time_entries(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
    start_date: Optional[str] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    page: Optional[int] = Query(1, ge=1, description="Page number"),
    limit: Optional[int] = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's time entries with optional filtering and pagination.
    
    Args:
        project_id: Optional filter by project ID
        task_id: Optional filter by task ID
        start_date: Optional filter by start date
        end_date: Optional filter by end date
        category: Optional filter by category
        page: Page number
        limit: Items per page
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of time entries with pagination info
    """
    try:
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
        
        # Validate category if provided
        if category:
            valid_categories = ['Development', 'Testing', 'Documentation', 'Meeting', 'Other']
            if category not in valid_categories:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}"
                )
        
        # Get time entries
        time_entries, pagination_info = TimeEntryService.get_user_time_entries(
            db.session,
            str(current_user.id),
            project_id=project_id,
            task_id=task_id,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            category=category,
            page=page,
            limit=limit
        )
        
        return TimeEntryListResponse(
            success=True,
            data=time_entries,
            message="Time entries retrieved successfully",
            pagination=pagination_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{time_entry_id}", response_model=TimeEntryDetailResponseWrapper)
async def get_time_entry(
    time_entry_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific time entry details.
    
    Args:
        time_entry_id: Time entry ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Time entry details
    """
    try:
        # Get time entry
        time_entry = TimeEntryService.get_time_entry_by_id(db.session, time_entry_id)
        
        if not time_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time entry not found"
            )
        
        # Check if user can access this time entry
        if str(time_entry.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this time entry"
            )
        
        return TimeEntryDetailResponseWrapper(
            success=True,
            data=time_entry,
            message="Time entry retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("", response_model=TimeEntryCreateResponseWrapper, status_code=status.HTTP_201_CREATED)
async def create_time_entry(
    time_entry_data: TimeEntryCreateRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create new time entry.
    
    Args:
        time_entry_data: Time entry creation data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created time entry details
    """
    try:
        time_entry = TimeEntryService.create_time_entry(
            db.session,
            time_entry_data,
            str(current_user.id)
        )
        
        if not time_entry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create time entry"
            )
        
        # Get the created time entry with all related data
        created_time_entry = TimeEntryService.get_time_entry_by_id(db.session, str(time_entry.id))
        
        return TimeEntryCreateResponseWrapper(
            success=True,
            data=created_time_entry,
            message="Time entry created successfully"
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


@router.put("/{time_entry_id}", response_model=TimeEntryUpdateResponseWrapper)
async def update_time_entry(
    time_entry_id: str,
    update_data: TimeEntryUpdateRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update time entry details.
    
    Args:
        time_entry_id: Time entry ID
        update_data: Time entry update data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated time entry details
    """
    try:
        # Get time entry and check permissions
        time_entry = TimeEntryService.get_time_entry_by_id(db.session, time_entry_id)
        
        if not time_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time entry not found"
            )
        
        # Check if user can update this time entry
        if not TimeEntryService.can_update_time_entry(time_entry, str(current_user.id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this time entry"
            )
        
        updated_time_entry = TimeEntryService.update_time_entry(
            db.session,
            time_entry_id,
            update_data,
            str(current_user.id)
        )
        
        if not updated_time_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time entry not found"
            )
        
        # Get the updated time entry with all related data
        final_time_entry = TimeEntryService.get_time_entry_by_id(db.session, time_entry_id)
        
        return TimeEntryUpdateResponseWrapper(
            success=True,
            data=final_time_entry,
            message="Time entry updated successfully"
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


@router.delete("/{time_entry_id}", response_model=TimeEntryDeleteResponseWrapper)
async def delete_time_entry(
    time_entry_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete time entry.
    
    Args:
        time_entry_id: Time entry ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Deletion confirmation
    """
    try:
        # Get time entry and check permissions
        time_entry = TimeEntryService.get_time_entry_by_id(db.session, time_entry_id)
        
        if not time_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time entry not found"
            )
        
        # Check if user can delete this time entry
        if not TimeEntryService.can_delete_time_entry(time_entry, str(current_user.id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this time entry"
            )
        
        success = TimeEntryService.delete_time_entry(
            db.session,
            time_entry_id,
            str(current_user.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time entry not found"
            )
        
        return TimeEntryDeleteResponseWrapper(
            success=True,
            message="Time entry deleted successfully"
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


@router.get("/pending", response_model=PendingTimeEntriesResponse)
async def get_pending_time_entries(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    page: Optional[int] = Query(1, ge=1, description="Page number"),
    limit: Optional[int] = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get pending time entries for approval.
    
    Args:
        project_id: Optional filter by project ID
        page: Page number
        limit: Items per page
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of pending time entries with pagination info
    """
    try:
        # Get pending time entries
        time_entries, pagination_info = TimeEntryService.get_pending_time_entries(
            db.session,
            str(current_user.id),
            project_id=project_id,
            page=page,
            limit=limit
        )
        
        return PendingTimeEntriesResponse(
            success=True,
            data=time_entries,
            message="Pending time entries retrieved successfully",
            pagination=pagination_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/approved", response_model=ApprovedTimeEntriesResponse)
async def get_approved_time_entries(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    start_date: Optional[str] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    page: Optional[int] = Query(1, ge=1, description="Page number"),
    limit: Optional[int] = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get approved time entries.
    
    Args:
        user_id: Optional filter by user ID
        project_id: Optional filter by project ID
        start_date: Optional filter by start date
        end_date: Optional filter by end date
        page: Page number
        limit: Items per page
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of approved time entries with pagination info
    """
    try:
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
        
        # Get approved time entries
        time_entries, pagination_info = TimeEntryService.get_approved_time_entries(
            db.session,
            user_id=user_id,
            project_id=project_id,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            page=page,
            limit=limit
        )
        
        return ApprovedTimeEntriesResponse(
            success=True,
            data=time_entries,
            message="Approved time entries retrieved successfully",
            pagination=pagination_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.put("/{time_entry_id}/approve", response_model=TimeEntryApprovalResponseWrapper)
async def approve_time_entry(
    time_entry_id: str,
    approval_data: TimeEntryApprovalRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Approve a time entry.
    
    Args:
        time_entry_id: Time entry ID
        approval_data: Approval data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Approval confirmation
    """
    try:
        # Get time entry and check permissions
        time_entry = TimeEntryService.get_time_entry_by_id(db.session, time_entry_id)
        
        if not time_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time entry not found"
            )
        
        # Check if user can approve this time entry
        if not TimeEntryService.can_approve_time_entry(time_entry, str(current_user.id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to approve this time entry"
            )
        
        approved_time_entry = TimeEntryService.approve_time_entry(
            db.session,
            time_entry_id,
            str(current_user.id),
            approval_data.approval_notes
        )
        
        if not approved_time_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time entry not found"
            )
        
        # Create approval response
        approval_response = TimeEntryApprovalResponse(
            id=approved_time_entry.id,
            is_approved=approved_time_entry.is_approved,
            approved_at=approved_time_entry.approved_at,
            approved_by=approved_time_entry.approved_by,
            approval_notes=approval_data.approval_notes
        )
        
        return TimeEntryApprovalResponseWrapper(
            success=True,
            data=approval_response,
            message="Time entry approved successfully"
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


@router.put("/{time_entry_id}/reject", response_model=TimeEntryRejectionResponseWrapper)
async def reject_time_entry(
    time_entry_id: str,
    rejection_data: TimeEntryRejectionRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reject a time entry.
    
    Args:
        time_entry_id: Time entry ID
        rejection_data: Rejection data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Rejection confirmation
    """
    try:
        # Get time entry and check permissions
        time_entry = TimeEntryService.get_time_entry_by_id(db.session, time_entry_id)
        
        if not time_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time entry not found"
            )
        
        # Check if user can reject this time entry
        if not TimeEntryService.can_reject_time_entry(time_entry, str(current_user.id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to reject this time entry"
            )
        
        rejected_time_entry = TimeEntryService.reject_time_entry(
            db.session,
            time_entry_id,
            str(current_user.id),
            rejection_data.rejection_reason
        )
        
        if not rejected_time_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time entry not found"
            )
        
        # Get the updated time entry with all related data
        final_time_entry = TimeEntryService.get_time_entry_by_id(db.session, time_entry_id)
        
        return TimeEntryRejectionResponseWrapper(
            success=True,
            data=final_time_entry,
            message="Time entry rejected successfully"
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


@router.get("/analytics", response_model=TimeAnalyticsResponse)
async def get_time_analytics(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    start_date: Optional[str] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive time analytics data.
    
    Args:
        user_id: Optional filter by user ID
        project_id: Optional filter by project ID
        start_date: Optional filter by start date
        end_date: Optional filter by end date
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Comprehensive analytics data
    """
    try:
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
        
        # Get analytics data
        analytics_data = TimeEntryService.get_time_analytics(
            db.session,
            user_id=user_id,
            project_id=project_id,
            start_date=parsed_start_date,
            end_date=parsed_end_date
        )
        
        return TimeAnalyticsResponse(
            success=True,
            data=analytics_data,
            message="Time analytics data retrieved successfully"
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/reports", response_model=TimeReportResponse)
async def generate_time_report(
    report_type: str = Query(..., description="Type of report (daily, weekly, monthly, general)"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    start_date: Optional[str] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate time tracking report.
    
    Args:
        report_type: Type of report to generate
        user_id: Optional filter by user ID
        project_id: Optional filter by project ID
        start_date: Optional filter by start date
        end_date: Optional filter by end date
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Generated report data
    """
    try:
        # Validate report type
        valid_report_types = ["daily", "weekly", "monthly", "general"]
        if report_type not in valid_report_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid report_type. Must be one of: {', '.join(valid_report_types)}"
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
        
        # Generate report
        report_data = TimeEntryService.generate_time_report(
            db.session,
            report_type=report_type,
            user_id=user_id,
            project_id=project_id,
            start_date=parsed_start_date,
            end_date=parsed_end_date
        )
        
        return TimeReportResponse(
            success=True,
            data=report_data,
            message=f"{report_type.capitalize()} report generated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/summary", response_model=TimeSummaryResponse)
async def get_time_summary(
    period: str = Query("current_month", description="Period for summary (current_week, current_month, current_year, all_time)"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get time summary for a specific period.
    
    Args:
        period: Period for summary
        user_id: Optional filter by user ID
        project_id: Optional filter by project ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Time summary data
    """
    try:
        # Validate period
        valid_periods = ["current_week", "current_month", "current_year", "all_time"]
        if period not in valid_periods:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid period. Must be one of: {', '.join(valid_periods)}"
            )
        
        # Get summary data
        summary_data = TimeEntryService.get_time_summary(
            db.session,
            period=period,
            user_id=user_id,
            project_id=project_id
        )
        
        return TimeSummaryResponse(
            success=True,
            data=summary_data,
            message=f"Time summary for {period} retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        ) 