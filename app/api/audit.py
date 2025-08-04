"""
Audit API endpoints for audit log management functionality.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.database import AsyncSessionWrapper, get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.services.audit_service import AuditService
from app.schemas.audit import (
    AuditLogResponse,
    AuditLogListResponse,
    AuditLogFilterRequest,
    AuditLogStatsResponse,
    AuditLogSummaryResponse,
    AuditLogExportRequest
)

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])
logger = logging.getLogger(__name__)


@router.get("", response_model=AuditLogListResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    ip_address: Optional[str] = Query(None, description="Filter by IP address"),
    date_from: Optional[str] = Query(None, description="Filter by date from (ISO format)"),
    date_to: Optional[str] = Query(None, description="Filter by date to (ISO format)"),
    search: Optional[str] = Query(None, description="Search in action descriptions"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Manager"]))
):
    """
    Get audit logs with pagination and filtering.
    
    Args:
        page: Page number
        page_size: Page size
        user_id: Filter by user ID
        action: Filter by action type
        entity_type: Filter by entity type
        entity_id: Filter by entity ID
        ip_address: Filter by IP address
        date_from: Filter by date from
        date_to: Filter by date to
        search: Search term
        db: Database session
        current_user: Current authenticated user (Admin/Manager only)
        
    Returns:
        List of audit logs with pagination information
    """
    try:
        # Create filter request
        filter_request = None
        if any([user_id, action, entity_type, entity_id, ip_address, date_from, date_to, search]):
            filter_request = AuditLogFilterRequest(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                ip_address=ip_address,
                date_from=date_from,
                date_to=date_to,
                search=search
            )
        
        # Get audit logs
        audit_logs, total_count = AuditService.get_audit_logs(
            db.session,
            page,
            page_size,
            filter_request
        )
        
        # Calculate pagination info
        has_next = (page * page_size) < total_count
        has_previous = page > 1
        
        return AuditLogListResponse(
            logs=audit_logs,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous
        )
        
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit logs"
        )


@router.get("/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Manager"]))
):
    """
    Get a specific audit log by ID.
    
    Args:
        log_id: Audit log ID
        db: Database session
        current_user: Current authenticated user (Admin/Manager only)
        
    Returns:
        Audit log information
    """
    try:
        audit_log = AuditService.get_audit_log_by_id(db.session, log_id)
        
        if not audit_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit log not found"
            )
        
        return audit_log
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audit log: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit log"
        )


@router.get("/by-user/{user_id}", response_model=AuditLogListResponse)
async def get_audit_logs_by_user(
    user_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Manager"]))
):
    """
    Get audit logs for a specific user.
    
    Args:
        user_id: User ID
        page: Page number
        page_size: Page size
        db: Database session
        current_user: Current authenticated user (Admin/Manager only)
        
    Returns:
        List of audit logs for the user
    """
    try:
        # Get audit logs for user
        audit_logs, total_count = AuditService.get_audit_logs_by_user(
            db.session,
            user_id,
            page,
            page_size
        )
        
        # Calculate pagination info
        has_next = (page * page_size) < total_count
        has_previous = page > 1
        
        return AuditLogListResponse(
            logs=audit_logs,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous
        )
        
    except Exception as e:
        logger.error(f"Error getting audit logs by user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit logs by user"
        )


@router.get("/by-action/{action}", response_model=AuditLogListResponse)
async def get_audit_logs_by_action(
    action: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Manager"]))
):
    """
    Get audit logs for a specific action.
    
    Args:
        action: Action type
        page: Page number
        page_size: Page size
        db: Database session
        current_user: Current authenticated user (Admin/Manager only)
        
    Returns:
        List of audit logs for the action
    """
    try:
        # Get audit logs for action
        audit_logs, total_count = AuditService.get_audit_logs_by_action(
            db.session,
            action,
            page,
            page_size
        )
        
        # Calculate pagination info
        has_next = (page * page_size) < total_count
        has_previous = page > 1
        
        return AuditLogListResponse(
            logs=audit_logs,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous
        )
        
    except Exception as e:
        logger.error(f"Error getting audit logs by action: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit logs by action"
        )


@router.get("/by-entity/{entity_type}/{entity_id}", response_model=AuditLogListResponse)
async def get_audit_logs_by_entity(
    entity_type: str,
    entity_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Manager"]))
):
    """
    Get audit logs for a specific entity.
    
    Args:
        entity_type: Entity type
        entity_id: Entity ID
        page: Page number
        page_size: Page size
        db: Database session
        current_user: Current authenticated user (Admin/Manager only)
        
    Returns:
        List of audit logs for the entity
    """
    try:
        # Get audit logs for entity
        audit_logs, total_count = AuditService.get_audit_logs_by_entity(
            db.session,
            entity_type,
            entity_id,
            page,
            page_size
        )
        
        # Calculate pagination info
        has_next = (page * page_size) < total_count
        has_previous = page > 1
        
        return AuditLogListResponse(
            logs=audit_logs,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous
        )
        
    except Exception as e:
        logger.error(f"Error getting audit logs by entity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit logs by entity"
        )


@router.get("/stats", response_model=AuditLogStatsResponse)
async def get_audit_log_stats(
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Manager"]))
):
    """
    Get audit log statistics.
    
    Args:
        db: Database session
        current_user: Current authenticated user (Admin/Manager only)
        
    Returns:
        Audit log statistics
    """
    try:
        stats = AuditService.get_audit_log_stats(db.session)
        return AuditLogStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting audit log stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit log statistics"
        )


@router.get("/summary", response_model=AuditLogSummaryResponse)
async def get_audit_log_summary(
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Manager"]))
):
    """
    Get audit log summary.
    
    Args:
        db: Database session
        current_user: Current authenticated user (Admin/Manager only)
        
    Returns:
        Audit log summary
    """
    try:
        summary = AuditService.get_audit_log_summary(db.session)
        return AuditLogSummaryResponse(**summary)
        
    except Exception as e:
        logger.error(f"Error getting audit log summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit log summary"
        )


@router.post("/export")
async def export_audit_logs(
    export_request: AuditLogExportRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Manager"]))
):
    """
    Export audit logs.
    
    Args:
        export_request: Export request parameters
        db: Database session
        current_user: Current authenticated user (Admin/Manager only)
        
    Returns:
        Exported audit log data
    """
    try:
        exported_data = AuditService.export_audit_logs(
            db.session,
            export_request.format,
            export_request.filter_request,
            export_request.include_details
        )
        
        # Log the export action
        AuditService.log_user_action(
            db=db.session,
            user_id=str(current_user.id),
            action="audit_log_export",
            entity_type="audit_logs",
            old_values={"format": export_request.format, "include_details": export_request.include_details}
        )
        
        return {
            "message": "Audit logs exported successfully",
            "format": export_request.format,
            "data": exported_data
        }
        
    except Exception as e:
        logger.error(f"Error exporting audit logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export audit logs"
        )


@router.get("/my-activity", response_model=AuditLogListResponse)
async def get_my_audit_activity(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's audit activity.
    
    Args:
        page: Page number
        page_size: Page size
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of current user's audit logs
    """
    try:
        # Get audit logs for current user
        audit_logs, total_count = AuditService.get_audit_logs_by_user(
            db.session,
            str(current_user.id),
            page,
            page_size
        )
        
        # Calculate pagination info
        has_next = (page * page_size) < total_count
        has_previous = page > 1
        
        return AuditLogListResponse(
            logs=audit_logs,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous
        )
        
    except Exception as e:
        logger.error(f"Error getting user audit activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user audit activity"
        ) 