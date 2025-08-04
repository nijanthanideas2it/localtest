"""
Reports API endpoints for project reporting functionality.
"""
import logging
from typing import Optional, List
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.database import AsyncSessionWrapper, get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.services.reports_service import ReportsService
from app.services.project_service import ProjectService
from app.schemas.reports import (
    ProjectReportRequest,
    ProjectReportExportRequest,
    ProjectReportResponse,
    ProjectReportExportResponse,
    ReportsListResponse,
    ReportType,
    ReportFormat,
    TimeReportRequest,
    TimeReportExportRequest,
    TimeReportResponse,
    TimeReportExportResponse,
    TimeReportType,
    PerformanceReportRequest,
    PerformanceReportExportRequest,
    PerformanceReportResponse,
    PerformanceReportExportResponse,
    PerformanceReportType
)

router = APIRouter(prefix="/reports", tags=["Reports"])
logger = logging.getLogger(__name__)


@router.get("/performance", response_model=PerformanceReportResponse)
async def get_performance_report(
    report_type: PerformanceReportType = Query(PerformanceReportType.GENERAL, description="Type of performance report to generate"),
    user_id: Optional[str] = Query(None, description="User ID for individual performance reports"),
    start_date: Optional[date] = Query(None, description="Start date for report period (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for report period (YYYY-MM-DD)"),
    include_details: bool = Query(True, description="Include detailed information"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a comprehensive performance report.
    
    Args:
        report_type: Type of performance report to generate
        user_id: Optional user ID for individual performance reports
        start_date: Optional start date for report period
        end_date: Optional end date for report period
        include_details: Whether to include detailed information
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Generated performance report
    """
    try:
        # Validate date range
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date cannot be after end date"
            )
        
        # Validate required parameters based on report type
        if report_type == PerformanceReportType.INDIVIDUAL and not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id is required for individual performance reports"
            )
        
        # Check permissions for individual performance reports
        if report_type == PerformanceReportType.INDIVIDUAL and user_id != str(current_user.id):
            if current_user.role not in ["Admin", "Manager"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view other users' performance reports"
                )
        
        # Generate the report
        report = ReportsService.generate_performance_report(
            db.session,
            report_type,
            user_id,
            start_date,
            end_date,
            include_details
        )
        
        return report
        
    except ValueError as e:
        logger.error(f"Value error generating performance report: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating performance report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate performance report"
        )


@router.get("/performance/{user_id}", response_model=PerformanceReportResponse)
async def get_individual_performance_report(
    user_id: str,
    start_date: Optional[date] = Query(None, description="Start date for report period (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for report period (YYYY-MM-DD)"),
    include_details: bool = Query(True, description="Include detailed information"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a performance report for a specific user.
    
    Args:
        user_id: User ID for the report
        start_date: Optional start date for report period
        end_date: Optional end date for report period
        include_details: Whether to include detailed information
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Individual performance report
    """
    try:
        # Validate date range
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date cannot be after end date"
            )
        
        # Check permissions
        if user_id != str(current_user.id):
            if current_user.role not in ["Admin", "Manager"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view other users' performance reports"
                )
        
        # Generate the report
        report = ReportsService.generate_performance_report(
            db.session,
            PerformanceReportType.INDIVIDUAL,
            user_id,
            start_date,
            end_date,
            include_details
        )
        
        return report
        
    except ValueError as e:
        logger.error(f"Value error generating individual performance report: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating individual performance report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate individual performance report"
        )


@router.get("/performance/team", response_model=PerformanceReportResponse)
async def get_team_performance_report(
    start_date: Optional[date] = Query(None, description="Start date for report period (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for report period (YYYY-MM-DD)"),
    include_details: bool = Query(True, description="Include detailed information"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Manager"]))
):
    """
    Generate a team performance report.
    
    Args:
        start_date: Optional start date for report period
        end_date: Optional end date for report period
        include_details: Whether to include detailed information
        db: Database session
        current_user: Current authenticated user (Admin/Manager only)
        
    Returns:
        Team performance report
    """
    try:
        # Validate date range
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date cannot be after end date"
            )
        
        # Generate the report
        report = ReportsService.generate_performance_report(
            db.session,
            PerformanceReportType.TEAM,
            None,
            start_date,
            end_date,
            include_details
        )
        
        return report
        
    except ValueError as e:
        logger.error(f"Value error generating team performance report: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating team performance report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate team performance report"
        )


@router.post("/performance/export", response_model=PerformanceReportExportResponse)
async def export_performance_report(
    export_request: PerformanceReportExportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export a performance report in the specified format.
    
    Args:
        export_request: Export request parameters
        background_tasks: Background tasks for async processing
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Export response with download information
    """
    try:
        # Validate date range
        if export_request.start_date and export_request.end_date:
            if export_request.start_date > export_request.end_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Start date cannot be after end date"
                )
        
        # Check permissions for individual performance reports
        if export_request.report_type == PerformanceReportType.INDIVIDUAL and export_request.user_id:
            if export_request.user_id != str(current_user.id):
                if current_user.role not in ["Admin", "Manager"]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Not authorized to export other users' performance reports"
                    )
        
        # Check permissions for team performance reports
        if export_request.report_type == PerformanceReportType.TEAM:
            if current_user.role not in ["Admin", "Manager"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to export team performance reports"
                )
        
        # Generate filename if not provided
        if not export_request.filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_request.filename = f"performance_report_{export_request.report_type.value}_{timestamp}"
        
        # Export the report
        export_response = ReportsService.export_performance_report(
            db.session,
            export_request.report_type,
            export_request.format,
            export_request.user_id,
            export_request.start_date,
            export_request.end_date,
            export_request.include_charts,
            export_request.filename
        )
        
        # Add cleanup task for expired exports
        background_tasks.add_task(ReportsService.cleanup_expired_exports)
        
        return export_response
        
    except ValueError as e:
        logger.error(f"Value error exporting performance report: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error exporting performance report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export performance report"
        )


@router.get("/time", response_model=TimeReportResponse)
async def get_time_report(
    report_type: TimeReportType = Query(TimeReportType.GENERAL, description="Type of time report to generate"),
    user_id: Optional[str] = Query(None, description="User ID for user-specific reports"),
    project_id: Optional[str] = Query(None, description="Project ID for project-specific reports"),
    start_date: Optional[date] = Query(None, description="Start date for report period (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for report period (YYYY-MM-DD)"),
    include_details: bool = Query(True, description="Include detailed information"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a comprehensive time report.
    
    Args:
        report_type: Type of time report to generate
        user_id: Optional user ID for user-specific reports
        project_id: Optional project ID for project-specific reports
        start_date: Optional start date for report period
        end_date: Optional end date for report period
        include_details: Whether to include detailed information
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Generated time report
    """
    try:
        # Validate date range
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date cannot be after end date"
            )
        
        # Validate required parameters based on report type
        if report_type == TimeReportType.BY_USER and not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id is required for user-specific time reports"
            )
        
        if report_type == TimeReportType.BY_PROJECT and not project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="project_id is required for project-specific time reports"
            )
        
        # Check permissions for user-specific reports
        if report_type == TimeReportType.BY_USER and user_id != str(current_user.id):
            if current_user.role not in ["Admin", "Manager"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view other users' time reports"
                )
        
        # Check permissions for project-specific reports
        if report_type == TimeReportType.BY_PROJECT and project_id:
            project = ProjectService.get_project_by_id(db.session, project_id)
            if not project:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found"
                )
            
            if not ProjectService.can_access_project(project, str(current_user.id), current_user.role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this project's time report"
                )
        
        # Generate the report
        report = ReportsService.generate_time_report(
            db.session,
            report_type,
            user_id,
            project_id,
            start_date,
            end_date,
            include_details
        )
        
        return report
        
    except ValueError as e:
        logger.error(f"Value error generating time report: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating time report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate time report"
        )


@router.get("/time/by-user", response_model=TimeReportResponse)
async def get_time_report_by_user(
    user_id: str = Query(..., description="User ID for the report"),
    start_date: Optional[date] = Query(None, description="Start date for report period (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for report period (YYYY-MM-DD)"),
    include_details: bool = Query(True, description="Include detailed information"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a time report for a specific user.
    
    Args:
        user_id: User ID for the report
        start_date: Optional start date for report period
        end_date: Optional end date for report period
        include_details: Whether to include detailed information
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        User-specific time report
    """
    try:
        # Validate date range
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date cannot be after end date"
            )
        
        # Check permissions
        if user_id != str(current_user.id):
            if current_user.role not in ["Admin", "Manager"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view other users' time reports"
                )
        
        # Generate the report
        report = ReportsService.generate_time_report(
            db.session,
            TimeReportType.BY_USER,
            user_id,
            None,
            start_date,
            end_date,
            include_details
        )
        
        return report
        
    except ValueError as e:
        logger.error(f"Value error generating user time report: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating user time report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate user time report"
        )


@router.get("/time/by-project", response_model=TimeReportResponse)
async def get_time_report_by_project(
    project_id: str = Query(..., description="Project ID for the report"),
    start_date: Optional[date] = Query(None, description="Start date for report period (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for report period (YYYY-MM-DD)"),
    include_details: bool = Query(True, description="Include detailed information"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a time report for a specific project.
    
    Args:
        project_id: Project ID for the report
        start_date: Optional start date for report period
        end_date: Optional end date for report period
        include_details: Whether to include detailed information
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Project-specific time report
    """
    try:
        # Validate date range
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date cannot be after end date"
            )
        
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
                detail="Not authorized to access this project's time report"
            )
        
        # Generate the report
        report = ReportsService.generate_time_report(
            db.session,
            TimeReportType.BY_PROJECT,
            None,
            project_id,
            start_date,
            end_date,
            include_details
        )
        
        return report
        
    except ValueError as e:
        logger.error(f"Value error generating project time report: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating project time report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate project time report"
        )


@router.post("/time/export", response_model=TimeReportExportResponse)
async def export_time_report(
    export_request: TimeReportExportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export a time report in the specified format.
    
    Args:
        export_request: Export request parameters
        background_tasks: Background tasks for async processing
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Export response with download information
    """
    try:
        # Validate date range
        if export_request.start_date and export_request.end_date:
            if export_request.start_date > export_request.end_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Start date cannot be after end date"
                )
        
        # Check permissions for user-specific reports
        if export_request.report_type == TimeReportType.BY_USER and export_request.user_id:
            if export_request.user_id != str(current_user.id):
                if current_user.role not in ["Admin", "Manager"]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Not authorized to export other users' time reports"
                    )
        
        # Check permissions for project-specific reports
        if export_request.report_type == TimeReportType.BY_PROJECT and export_request.project_id:
            project = ProjectService.get_project_by_id(db.session, export_request.project_id)
            if not project:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found"
                )
            
            if not ProjectService.can_access_project(project, str(current_user.id), current_user.role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to export this project's time report"
                )
        
        # Generate filename if not provided
        if not export_request.filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_request.filename = f"time_report_{export_request.report_type.value}_{timestamp}"
        
        # Export the report
        export_response = ReportsService.export_time_report(
            db.session,
            export_request.report_type,
            export_request.format,
            export_request.user_id,
            export_request.project_id,
            export_request.start_date,
            export_request.end_date,
            export_request.include_charts,
            export_request.filename
        )
        
        # Add cleanup task for expired exports
        background_tasks.add_task(ReportsService.cleanup_expired_exports)
        
        return export_response
        
    except ValueError as e:
        logger.error(f"Value error exporting time report: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error exporting time report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export time report"
        )


@router.get("/projects", response_model=ReportsListResponse)
async def get_project_reports(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    report_type: Optional[ReportType] = Query(None, description="Filter by report type"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of available project reports.
    
    Args:
        page: Page number for pagination
        page_size: Number of items per page
        project_id: Optional project ID filter
        report_type: Optional report type filter
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of available reports with pagination
    """
    try:
        # Get all generated reports
        all_reports = list(ReportsService._generated_reports.values())
        
        # Apply filters
        filtered_reports = all_reports
        
        if project_id:
            filtered_reports = [r for r in filtered_reports if r.project.id == project_id]
        
        if report_type:
            filtered_reports = [r for r in filtered_reports if r.report_type == report_type]
        
        # Apply pagination
        total_count = len(filtered_reports)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_reports = filtered_reports[start_idx:end_idx]
        
        return ReportsListResponse(
            reports=paginated_reports,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=end_idx < total_count,
            has_previous=page > 1
        )
        
    except Exception as e:
        logger.error(f"Error retrieving project reports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve project reports"
        )


@router.get("/projects/{project_id}", response_model=ProjectReportResponse)
async def get_project_report(
    project_id: str,
    report_type: ReportType = Query(ReportType.SUMMARY, description="Type of report to generate"),
    start_date: Optional[date] = Query(None, description="Start date for report period (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for report period (YYYY-MM-DD)"),
    include_details: bool = Query(True, description="Include detailed information"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate and retrieve a project report.
    
    Args:
        project_id: Project ID
        report_type: Type of report to generate
        start_date: Optional start date for report period
        end_date: Optional end date for report period
        include_details: Whether to include detailed information
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Generated project report
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
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date cannot be after end date"
            )
        
        # Generate the report
        report = ReportsService.generate_project_report(
            db.session,
            project_id,
            report_type,
            start_date,
            end_date,
            include_details
        )
        
        return report
        
    except ValueError as e:
        logger.error(f"Value error generating project report: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating project report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate project report"
        )


@router.post("/projects/export", response_model=ProjectReportExportResponse)
async def export_project_report(
    export_request: ProjectReportExportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export a project report in the specified format.
    
    Args:
        export_request: Export request parameters
        background_tasks: Background tasks for async processing
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Export response with download information
    """
    try:
        # Get project and check access permissions
        project = ProjectService.get_project_by_id(db.session, export_request.project_id)
        
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
        if export_request.start_date and export_request.end_date:
            if export_request.start_date > export_request.end_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Start date cannot be after end date"
                )
        
        # Generate filename if not provided
        if not export_request.filename:
            project_name = project.name.replace(" ", "_").lower()
            export_request.filename = f"{project_name}_{export_request.report_type.value}_{export_request.format.value}"
        
        # Export the report
        export_response = ReportsService.export_project_report(
            db.session,
            export_request.project_id,
            export_request.report_type,
            export_request.format,
            export_request.start_date,
            export_request.end_date,
            export_request.include_charts,
            export_request.filename
        )
        
        # Add cleanup task for expired exports
        background_tasks.add_task(ReportsService.cleanup_expired_exports)
        
        return export_response
        
    except ValueError as e:
        logger.error(f"Value error exporting project report: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error exporting project report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export project report"
        )


@router.get("/projects/{project_id}/summary", response_model=ProjectReportResponse)
async def get_project_summary_report(
    project_id: str,
    start_date: Optional[date] = Query(None, description="Start date for report period (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for report period (YYYY-MM-DD)"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a summary report for a specific project.
    
    Args:
        project_id: Project ID
        start_date: Optional start date for report period
        end_date: Optional end date for report period
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Project summary report
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
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date cannot be after end date"
            )
        
        # Generate summary report
        report = ReportsService.generate_project_report(
            db.session,
            project_id,
            ReportType.SUMMARY,
            start_date,
            end_date,
            True
        )
        
        return report
        
    except ValueError as e:
        logger.error(f"Value error generating summary report: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating summary report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate summary report"
        )


@router.get("/projects/{project_id}/financial", response_model=ProjectReportResponse)
async def get_project_financial_report(
    project_id: str,
    start_date: Optional[date] = Query(None, description="Start date for report period (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for report period (YYYY-MM-DD)"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a financial report for a specific project.
    
    Args:
        project_id: Project ID
        start_date: Optional start date for report period
        end_date: Optional end date for report period
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Project financial report
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
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date cannot be after end date"
            )
        
        # Generate financial report
        report = ReportsService.generate_project_report(
            db.session,
            project_id,
            ReportType.FINANCIAL,
            start_date,
            end_date,
            True
        )
        
        return report
        
    except ValueError as e:
        logger.error(f"Value error generating financial report: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating financial report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate financial report"
        )


@router.get("/projects/{project_id}/team-performance", response_model=ProjectReportResponse)
async def get_project_team_performance_report(
    project_id: str,
    start_date: Optional[date] = Query(None, description="Start date for report period (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for report period (YYYY-MM-DD)"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a team performance report for a specific project.
    
    Args:
        project_id: Project ID
        start_date: Optional start date for report period
        end_date: Optional end date for report period
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Project team performance report
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
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date cannot be after end date"
            )
        
        # Generate team performance report
        report = ReportsService.generate_project_report(
            db.session,
            project_id,
            ReportType.TEAM_PERFORMANCE,
            start_date,
            end_date,
            True
        )
        
        return report
        
    except ValueError as e:
        logger.error(f"Value error generating team performance report: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating team performance report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate team performance report"
        )


@router.get("/projects/{project_id}/milestones", response_model=ProjectReportResponse)
async def get_project_milestones_report(
    project_id: str,
    start_date: Optional[date] = Query(None, description="Start date for report period (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for report period (YYYY-MM-DD)"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a milestones report for a specific project.
    
    Args:
        project_id: Project ID
        start_date: Optional start date for report period
        end_date: Optional end date for report period
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Project milestones report
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
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date cannot be after end date"
            )
        
        # Generate milestones report
        report = ReportsService.generate_project_report(
            db.session,
            project_id,
            ReportType.MILESTONE,
            start_date,
            end_date,
            True
        )
        
        return report
        
    except ValueError as e:
        logger.error(f"Value error generating milestones report: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating milestones report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate milestones report"
        )


@router.get("/projects/{project_id}/task-analysis", response_model=ProjectReportResponse)
async def get_project_task_analysis_report(
    project_id: str,
    start_date: Optional[date] = Query(None, description="Start date for report period (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for report period (YYYY-MM-DD)"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a task analysis report for a specific project.
    
    Args:
        project_id: Project ID
        start_date: Optional start date for report period
        end_date: Optional end date for report period
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Project task analysis report
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
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date cannot be after end date"
            )
        
        # Generate task analysis report
        report = ReportsService.generate_project_report(
            db.session,
            project_id,
            ReportType.TASK_ANALYSIS,
            start_date,
            end_date,
            True
        )
        
        return report
        
    except ValueError as e:
        logger.error(f"Value error generating task analysis report: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating task analysis report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate task analysis report"
        )


@router.delete("/projects/{project_id}/reports/{report_id}")
async def delete_project_report(
    project_id: str,
    report_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a specific project report.
    
    Args:
        project_id: Project ID
        report_id: Report ID to delete
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
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
        
        # Get the report
        report = ReportsService.get_report_by_id(report_id)
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Verify the report belongs to the specified project
        if report.project.id != project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Report does not belong to the specified project"
            )
        
        # Delete the report
        if report_id in ReportsService._generated_reports:
            del ReportsService._generated_reports[report_id]
        
        return {"message": "Report deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete project report"
        )


@router.post("/cleanup")
async def cleanup_expired_reports(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_roles(["Admin", "Manager"]))
):
    """
    Clean up expired export files.
    
    Args:
        background_tasks: Background tasks for async processing
        current_user: Current authenticated user (Admin/Manager only)
        
    Returns:
        Success message
    """
    try:
        # Add cleanup task
        background_tasks.add_task(ReportsService.cleanup_expired_exports)
        
        return {"message": "Cleanup task scheduled successfully"}
        
    except Exception as e:
        logger.error(f"Error scheduling cleanup task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule cleanup task"
        ) 