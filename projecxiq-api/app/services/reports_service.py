"""
Reports service layer for project reporting functionality.
"""
import os
import csv
import json
import logging
from datetime import date, datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import uuid4
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, case, extract

from app.models.project import Project, ProjectTeamMember
from app.models.task import Task
from app.models.milestone import Milestone
from app.models.time_entry import TimeEntry
from app.models.user import User
from app.schemas.reports import (
    ProjectReportResponse,
    ProjectReportExportResponse,
    ProjectSummaryData,
    ProjectFinancialData,
    TeamMemberPerformance,
    MilestoneReportData,
    TaskAnalysisData,
    ReportType,
    ReportFormat,
    TimeReportResponse,
    TimeReportExportResponse,
    TimeReportSummaryData,
    TimeReportByProjectData,
    TimeReportByCategoryData,
    TimeReportByUserData,
    TimeReportDailyData,
    TimeReportType,
    PerformanceReportResponse,
    PerformanceReportExportResponse,
    PerformanceSummaryData,
    IndividualPerformanceData,
    TeamPerformanceData,
    PerformanceMetricsData,
    PerformanceReportType
)
from app.services.analytics_service import AnalyticsService
from app.services.project_service import ProjectService
from app.services.time_entry_service import TimeEntryService

logger = logging.getLogger(__name__)


class ReportsService:
    """Service class for project reporting functionality."""
    
    # In-memory storage for generated reports (in production, use Redis or database)
    _generated_reports: Dict[str, ProjectReportResponse] = {}
    _generated_time_reports: Dict[str, TimeReportResponse] = {}
    _generated_performance_reports: Dict[str, PerformanceReportResponse] = {}
    _export_files: Dict[str, Dict[str, Any]] = {}
    
    @staticmethod
    def generate_project_report(
        db: Session,
        project_id: str,
        report_type: ReportType,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        include_details: bool = True
    ) -> ProjectReportResponse:
        """
        Generate a comprehensive project report.
        
        Args:
            db: Database session
            project_id: Project ID
            report_type: Type of report to generate
            start_date: Optional start date for report period
            end_date: Optional end date for report period
            include_details: Whether to include detailed information
            
        Returns:
            Generated project report
        """
        # Get project with related data
        project = db.query(Project).options(
            joinedload(Project.team_members),
            joinedload(Project.milestones),
            joinedload(Project.tasks)
        ).filter(Project.id == project_id).first()
        
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")
        
        # Generate report based on type
        if report_type == ReportType.SUMMARY:
            return ReportsService._generate_summary_report(
                db, project, start_date, end_date, include_details
            )
        elif report_type == ReportType.DETAILED:
            return ReportsService._generate_detailed_report(
                db, project, start_date, end_date, include_details
            )
        elif report_type == ReportType.FINANCIAL:
            return ReportsService._generate_financial_report(
                db, project, start_date, end_date, include_details
            )
        elif report_type == ReportType.TIMELINE:
            return ReportsService._generate_timeline_report(
                db, project, start_date, end_date, include_details
            )
        elif report_type == ReportType.TEAM_PERFORMANCE:
            return ReportsService._generate_team_performance_report(
                db, project, start_date, end_date, include_details
            )
        elif report_type == ReportType.MILESTONE:
            return ReportsService._generate_milestone_report(
                db, project, start_date, end_date, include_details
            )
        elif report_type == ReportType.TASK_ANALYSIS:
            return ReportsService._generate_task_analysis_report(
                db, project, start_date, end_date, include_details
            )
        else:
            raise ValueError(f"Unsupported report type: {report_type}")
    
    @staticmethod
    def _generate_summary_report(
        db: Session,
        project: Project,
        start_date: Optional[date],
        end_date: Optional[date],
        include_details: bool
    ) -> ProjectReportResponse:
        """Generate a summary report for the project."""
        # Get project summary data
        summary_data = ReportsService._get_project_summary_data(db, project, start_date, end_date)
        
        # Get basic team performance
        team_performance = ReportsService._get_team_performance_data(db, project, start_date, end_date)
        
        # Get milestone data
        milestones = ReportsService._get_milestone_report_data(db, project, start_date, end_date)
        
        report_id = str(uuid4())
        
        report = ProjectReportResponse(
            report_id=report_id,
            project=ProjectService.project_to_response(project),
            report_type=ReportType.SUMMARY,
            generated_at=datetime.now(timezone.utc),
            period_start=start_date,
            period_end=end_date,
            summary=summary_data,
            team_performance=team_performance,
            milestones=milestones,
            metadata={
                "include_details": include_details,
                "generation_method": "summary_report"
            }
        )
        
        # Store report in memory
        ReportsService._generated_reports[report_id] = report
        
        return report
    
    @staticmethod
    def _generate_detailed_report(
        db: Session,
        project: Project,
        start_date: Optional[date],
        end_date: Optional[date],
        include_details: bool
    ) -> ProjectReportResponse:
        """Generate a detailed report for the project."""
        # Get all summary data
        summary_data = ReportsService._get_project_summary_data(db, project, start_date, end_date)
        team_performance = ReportsService._get_team_performance_data(db, project, start_date, end_date)
        milestones = ReportsService._get_milestone_report_data(db, project, start_date, end_date)
        financial_data = ReportsService._get_financial_data(db, project, start_date, end_date)
        task_analysis = ReportsService._get_task_analysis_data(db, project, start_date, end_date)
        
        report_id = str(uuid4())
        
        report = ProjectReportResponse(
            report_id=report_id,
            project=ProjectService.project_to_response(project),
            report_type=ReportType.DETAILED,
            generated_at=datetime.now(timezone.utc),
            period_start=start_date,
            period_end=end_date,
            summary=summary_data,
            financial_data=financial_data,
            team_performance=team_performance,
            milestones=milestones,
            task_analysis=task_analysis,
            metadata={
                "include_details": include_details,
                "generation_method": "detailed_report"
            }
        )
        
        ReportsService._generated_reports[report_id] = report
        return report
    
    @staticmethod
    def _generate_financial_report(
        db: Session,
        project: Project,
        start_date: Optional[date],
        end_date: Optional[date],
        include_details: bool
    ) -> ProjectReportResponse:
        """Generate a financial report for the project."""
        summary_data = ReportsService._get_project_summary_data(db, project, start_date, end_date)
        financial_data = ReportsService._get_financial_data(db, project, start_date, end_date)
        
        report_id = str(uuid4())
        
        report = ProjectReportResponse(
            report_id=report_id,
            project=ProjectService.project_to_response(project),
            report_type=ReportType.FINANCIAL,
            generated_at=datetime.now(timezone.utc),
            period_start=start_date,
            period_end=end_date,
            summary=summary_data,
            financial_data=financial_data,
            team_performance=[],
            milestones=[],
            metadata={
                "include_details": include_details,
                "generation_method": "financial_report"
            }
        )
        
        ReportsService._generated_reports[report_id] = report
        return report
    
    @staticmethod
    def _generate_timeline_report(
        db: Session,
        project: Project,
        start_date: Optional[date],
        end_date: Optional[date],
        include_details: bool
    ) -> ProjectReportResponse:
        """Generate a timeline report for the project."""
        summary_data = ReportsService._get_project_summary_data(db, project, start_date, end_date)
        milestones = ReportsService._get_milestone_report_data(db, project, start_date, end_date)
        
        report_id = str(uuid4())
        
        report = ProjectReportResponse(
            report_id=report_id,
            project=ProjectService.project_to_response(project),
            report_type=ReportType.TIMELINE,
            generated_at=datetime.now(timezone.utc),
            period_start=start_date,
            period_end=end_date,
            summary=summary_data,
            team_performance=[],
            milestones=milestones,
            metadata={
                "include_details": include_details,
                "generation_method": "timeline_report"
            }
        )
        
        ReportsService._generated_reports[report_id] = report
        return report
    
    @staticmethod
    def _generate_team_performance_report(
        db: Session,
        project: Project,
        start_date: Optional[date],
        end_date: Optional[date],
        include_details: bool
    ) -> ProjectReportResponse:
        """Generate a team performance report for the project."""
        summary_data = ReportsService._get_project_summary_data(db, project, start_date, end_date)
        team_performance = ReportsService._get_team_performance_data(db, project, start_date, end_date)
        
        report_id = str(uuid4())
        
        report = ProjectReportResponse(
            report_id=report_id,
            project=ProjectService.project_to_response(project),
            report_type=ReportType.TEAM_PERFORMANCE,
            generated_at=datetime.now(timezone.utc),
            period_start=start_date,
            period_end=end_date,
            summary=summary_data,
            team_performance=team_performance,
            milestones=[],
            metadata={
                "include_details": include_details,
                "generation_method": "team_performance_report"
            }
        )
        
        ReportsService._generated_reports[report_id] = report
        return report
    
    @staticmethod
    def _generate_milestone_report(
        db: Session,
        project: Project,
        start_date: Optional[date],
        end_date: Optional[date],
        include_details: bool
    ) -> ProjectReportResponse:
        """Generate a milestone report for the project."""
        summary_data = ReportsService._get_project_summary_data(db, project, start_date, end_date)
        milestones = ReportsService._get_milestone_report_data(db, project, start_date, end_date)
        
        report_id = str(uuid4())
        
        report = ProjectReportResponse(
            report_id=report_id,
            project=ProjectService.project_to_response(project),
            report_type=ReportType.MILESTONE,
            generated_at=datetime.now(timezone.utc),
            period_start=start_date,
            period_end=end_date,
            summary=summary_data,
            team_performance=[],
            milestones=milestones,
            metadata={
                "include_details": include_details,
                "generation_method": "milestone_report"
            }
        )
        
        ReportsService._generated_reports[report_id] = report
        return report
    
    @staticmethod
    def _generate_task_analysis_report(
        db: Session,
        project: Project,
        start_date: Optional[date],
        end_date: Optional[date],
        include_details: bool
    ) -> ProjectReportResponse:
        """Generate a task analysis report for the project."""
        summary_data = ReportsService._get_project_summary_data(db, project, start_date, end_date)
        task_analysis = ReportsService._get_task_analysis_data(db, project, start_date, end_date)
        
        report_id = str(uuid4())
        
        report = ProjectReportResponse(
            report_id=report_id,
            project=ProjectService.project_to_response(project),
            report_type=ReportType.TASK_ANALYSIS,
            generated_at=datetime.now(timezone.utc),
            period_start=start_date,
            period_end=end_date,
            summary=summary_data,
            team_performance=[],
            milestones=[],
            task_analysis=task_analysis,
            metadata={
                "include_details": include_details,
                "generation_method": "task_analysis_report"
            }
        )
        
        ReportsService._generated_reports[report_id] = report
        return report
    
    @staticmethod
    def _get_project_summary_data(
        db: Session,
        project: Project,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> ProjectSummaryData:
        """Get project summary data."""
        # Build query filters
        filters = [Task.project_id == project.id]
        if start_date:
            filters.append(Task.created_at >= start_date)
        if end_date:
            filters.append(Task.created_at <= end_date)
        
        # Get task statistics
        tasks_query = db.query(Task).filter(and_(*filters))
        total_tasks = tasks_query.count()
        
        completed_tasks = tasks_query.filter(Task.status == "completed").count()
        in_progress_tasks = tasks_query.filter(Task.status == "in_progress").count()
        pending_tasks = tasks_query.filter(Task.status == "pending").count()
        overdue_tasks = tasks_query.filter(
            and_(Task.due_date < date.today(), Task.status != "completed")
        ).count()
        
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Get time statistics
        time_filters = [TimeEntry.project_id == project.id]
        if start_date:
            time_filters.append(TimeEntry.date >= start_date)
        if end_date:
            time_filters.append(TimeEntry.date <= end_date)
        
        total_time_logged = db.query(func.sum(TimeEntry.duration)).filter(
            and_(*time_filters)
        ).scalar() or 0
        
        # Get team size
        team_size = db.query(ProjectTeamMember).filter(
            ProjectTeamMember.project_id == project.id
        ).count()
        
        # Get milestone statistics
        milestone_filters = [Milestone.project_id == project.id]
        if start_date:
            milestone_filters.append(Milestone.created_at >= start_date)
        if end_date:
            milestone_filters.append(Milestone.created_at <= end_date)
        
        milestones_query = db.query(Milestone).filter(and_(*milestone_filters))
        milestones_count = milestones_query.count()
        completed_milestones = milestones_query.filter(Milestone.status == "completed").count()
        
        # Calculate budget utilization and risk score
        budget_utilization = None
        risk_score = None
        
        if project.budget:
            # Simple budget calculation (in production, use more sophisticated logic)
            budget_utilization = min(100.0, (total_time_logged * 50) / float(project.budget) * 100)
        
        # Simple risk score calculation
        risk_factors = 0
        if overdue_tasks > 0:
            risk_factors += 1
        if completion_rate < 50:
            risk_factors += 1
        if budget_utilization and budget_utilization > 80:
            risk_factors += 1
        
        risk_score = min(100.0, risk_factors * 25)
        
        return ProjectSummaryData(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            in_progress_tasks=in_progress_tasks,
            pending_tasks=pending_tasks,
            overdue_tasks=overdue_tasks,
            completion_rate=round(completion_rate, 2),
            total_time_logged=round(total_time_logged, 2),
            budget_utilization=budget_utilization,
            risk_score=risk_score,
            team_size=team_size,
            milestones_count=milestones_count,
            completed_milestones=completed_milestones
        )
    
    @staticmethod
    def _get_financial_data(
        db: Session,
        project: Project,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> Optional[ProjectFinancialData]:
        """Get project financial data."""
        if not project.budget:
            return None
        
        # Get time entries for the project
        time_filters = [TimeEntry.project_id == project.id]
        if start_date:
            time_filters.append(TimeEntry.date >= start_date)
        if end_date:
            time_filters.append(TimeEntry.date <= end_date)
        
        total_hours_billed = db.query(func.sum(TimeEntry.duration)).filter(
            and_(*time_filters)
        ).scalar() or 0
        
        # Simple cost calculation (assume $50/hour average)
        cost_per_hour = Decimal('50.00')
        spent_amount = Decimal(str(total_hours_billed)) * cost_per_hour
        remaining_budget = Decimal(str(project.budget)) - spent_amount
        budget_utilization_percentage = (spent_amount / Decimal(str(project.budget)) * 100) if project.budget > 0 else 0
        
        # Estimate completion cost based on current progress
        total_tasks = db.query(Task).filter(Task.project_id == project.id).count()
        completed_tasks = db.query(Task).filter(
            and_(Task.project_id == project.id, Task.status == "completed")
        ).count()
        
        if total_tasks > 0:
            progress_ratio = completed_tasks / total_tasks
            estimated_completion_cost = spent_amount / progress_ratio if progress_ratio > 0 else spent_amount
        else:
            estimated_completion_cost = spent_amount
        
        return ProjectFinancialData(
            total_budget=Decimal(str(project.budget)),
            spent_amount=spent_amount,
            remaining_budget=remaining_budget,
            budget_utilization_percentage=round(float(budget_utilization_percentage), 2),
            cost_per_hour=cost_per_hour,
            total_hours_billed=round(total_hours_billed, 2),
            estimated_completion_cost=estimated_completion_cost
        )
    
    @staticmethod
    def _get_team_performance_data(
        db: Session,
        project: Project,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> List[TeamMemberPerformance]:
        """Get team performance data."""
        team_members = db.query(ProjectTeamMember).filter(
            ProjectTeamMember.project_id == project.id
        ).all()
        
        performance_data = []
        
        for member in team_members:
            user = member.user
            
            # Get tasks assigned to this user
            task_filters = [
                Task.project_id == project.id,
                Task.assignee_id == str(user.id)
            ]
            if start_date:
                task_filters.append(Task.created_at >= start_date)
            if end_date:
                task_filters.append(Task.created_at <= end_date)
            
            tasks_query = db.query(Task).filter(and_(*task_filters))
            tasks_assigned = tasks_query.count()
            tasks_completed = tasks_query.filter(Task.status == "completed").count()
            
            completion_rate = (tasks_completed / tasks_assigned * 100) if tasks_assigned > 0 else 0
            
            # Get time logged by this user
            time_filters = [
                TimeEntry.project_id == project.id,
                TimeEntry.user_id == str(user.id)
            ]
            if start_date:
                time_filters.append(TimeEntry.date >= start_date)
            if end_date:
                time_filters.append(TimeEntry.date <= end_date)
            
            time_logged = db.query(func.sum(TimeEntry.duration)).filter(
                and_(*time_filters)
            ).scalar() or 0
            
            # Calculate average task duration
            completed_tasks_duration = db.query(func.avg(Task.estimated_hours)).filter(
                and_(*task_filters, Task.status == "completed")
            ).scalar() or 0
            
            # Calculate on-time delivery rate
            overdue_tasks = db.query(Task).filter(
                and_(*task_filters, Task.due_date < date.today(), Task.status != "completed")
            ).count()
            
            on_time_delivery_rate = (
                (tasks_completed - overdue_tasks) / tasks_completed * 100
            ) if tasks_completed > 0 else 100
            
            performance_data.append(TeamMemberPerformance(
                user=ProjectService.user_to_response(user),
                tasks_assigned=tasks_assigned,
                tasks_completed=tasks_completed,
                completion_rate=round(completion_rate, 2),
                time_logged=round(time_logged, 2),
                average_task_duration=round(completed_tasks_duration, 2) if completed_tasks_duration else None,
                on_time_delivery_rate=round(on_time_delivery_rate, 2)
            ))
        
        return performance_data
    
    @staticmethod
    def _get_milestone_report_data(
        db: Session,
        project: Project,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> List[MilestoneReportData]:
        """Get milestone report data."""
        milestone_filters = [Milestone.project_id == project.id]
        if start_date:
            milestone_filters.append(Milestone.created_at >= start_date)
        if end_date:
            milestone_filters.append(Milestone.created_at <= end_date)
        
        milestones = db.query(Milestone).filter(and_(*milestone_filters)).all()
        
        milestone_data = []
        
        for milestone in milestones:
            # Get tasks in this milestone
            tasks_count = db.query(Task).filter(Task.milestone_id == milestone.id).count()
            completed_tasks = db.query(Task).filter(
                and_(Task.milestone_id == milestone.id, Task.status == "completed")
            ).count()
            
            completion_percentage = (completed_tasks / tasks_count * 100) if tasks_count > 0 else 0
            
            # Check if milestone is overdue
            is_overdue = milestone.due_date < date.today() and milestone.status != "completed"
            
            # Calculate days remaining
            days_remaining = None
            if milestone.status != "completed":
                days_remaining = (milestone.due_date - date.today()).days
            
            milestone_data.append(MilestoneReportData(
                milestone_id=str(milestone.id),
                title=milestone.title,
                description=milestone.description,
                due_date=milestone.due_date,
                status=milestone.status,
                completion_percentage=round(completion_percentage, 2),
                tasks_count=tasks_count,
                completed_tasks=completed_tasks,
                is_overdue=is_overdue,
                days_remaining=days_remaining
            ))
        
        return milestone_data
    
    @staticmethod
    def _get_task_analysis_data(
        db: Session,
        project: Project,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> TaskAnalysisData:
        """Get task analysis data."""
        task_filters = [Task.project_id == project.id]
        if start_date:
            task_filters.append(Task.created_at >= start_date)
        if end_date:
            task_filters.append(Task.created_at <= end_date)
        
        tasks_query = db.query(Task).filter(and_(*task_filters))
        total_tasks = tasks_query.count()
        
        # Tasks by status
        tasks_by_status = {}
        for status in ["pending", "in_progress", "completed", "cancelled"]:
            count = tasks_query.filter(Task.status == status).count()
            if count > 0:
                tasks_by_status[status] = count
        
        # Tasks by priority
        tasks_by_priority = {}
        for priority in ["low", "medium", "high", "critical"]:
            count = tasks_query.filter(Task.priority == priority).count()
            if count > 0:
                tasks_by_priority[priority] = count
        
        # Tasks by assignee
        tasks_by_assignee = {}
        assignees = db.query(Task.assignee_id).filter(and_(*task_filters)).distinct().all()
        for assignee_id, in assignees:
            if assignee_id:
                count = tasks_query.filter(Task.assignee_id == assignee_id).count()
                tasks_by_assignee[assignee_id] = count
        
        # Average task duration
        completed_tasks = tasks_query.filter(Task.status == "completed")
        avg_duration = db.query(func.avg(Task.estimated_hours)).filter(
            and_(*task_filters, Task.status == "completed")
        ).scalar() or 0
        
        # Longest and shortest tasks
        longest_task = db.query(Task.title).filter(
            and_(*task_filters, Task.status == "completed")
        ).order_by(desc(Task.estimated_hours)).first()
        
        shortest_task = db.query(Task.title).filter(
            and_(*task_filters, Task.status == "completed")
        ).order_by(Task.estimated_hours).first()
        
        # Dependency analysis
        tasks_with_dependencies = db.query(Task).filter(
            and_(*task_filters, Task.dependencies.any())
        ).count()
        
        dependency_analysis = {
            "tasks_with_dependencies": tasks_with_dependencies,
            "dependency_percentage": (tasks_with_dependencies / total_tasks * 100) if total_tasks > 0 else 0
        }
        
        return TaskAnalysisData(
            total_tasks=total_tasks,
            tasks_by_status=tasks_by_status,
            tasks_by_priority=tasks_by_priority,
            tasks_by_assignee=tasks_by_assignee,
            average_task_duration=round(avg_duration, 2),
            longest_running_task=longest_task[0] if longest_task else None,
            shortest_completed_task=shortest_task[0] if shortest_task else None,
            dependency_analysis=dependency_analysis
        )
    
    @staticmethod
    def export_project_report(
        db: Session,
        project_id: str,
        report_type: ReportType,
        format: ReportFormat,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        include_charts: bool = True,
        filename: Optional[str] = None
    ) -> ProjectReportExportResponse:
        """
        Export a project report in the specified format.
        
        Args:
            db: Database session
            project_id: Project ID
            report_type: Type of report to export
            format: Export format
            start_date: Optional start date for report period
            end_date: Optional end date for report period
            include_charts: Whether to include charts in export
            filename: Custom filename for export
            
        Returns:
            Export response with download information
        """
        # Generate the report first
        report = ReportsService.generate_project_report(
            db, project_id, report_type, start_date, end_date, True
        )
        
        # Generate filename if not provided
        if not filename:
            project = db.query(Project).filter(Project.id == project_id).first()
            project_name = project.name if project else "unknown_project"
            filename = f"{project_name}_{report_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        export_id = str(uuid4())
        
        # Create export file based on format
        file_path = f"exports/{filename}.{format.value}"
        os.makedirs("exports", exist_ok=True)
        
        if format == ReportFormat.JSON:
            ReportsService._export_to_json(report, file_path)
        elif format == ReportFormat.CSV:
            ReportsService._export_to_csv(report, file_path)
        elif format == ReportFormat.PDF:
            ReportsService._export_to_pdf(report, file_path, include_charts)
        elif format == ReportFormat.EXCEL:
            ReportsService._export_to_excel(report, file_path, include_charts)
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        # Get file size
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else None
        
        # Create download URL
        download_url = f"/static/exports/{filename}.{format.value}"
        
        # Set expiration (24 hours from now)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        
        export_response = ProjectReportExportResponse(
            export_id=export_id,
            filename=f"{filename}.{format.value}",
            format=format,
            download_url=download_url,
            file_size=file_size,
            expires_at=expires_at,
            metadata={
                "include_charts": include_charts,
                "original_report_id": report.report_id
            }
        )
        
        # Store export information
        ReportsService._export_files[export_id] = {
            "file_path": file_path,
            "expires_at": expires_at,
            "response": export_response
        }
        
        return export_response
    
    @staticmethod
    def _export_to_json(report: ProjectReportResponse, file_path: str):
        """Export report to JSON format."""
        with open(file_path, 'w') as f:
            json.dump(report.dict(), f, indent=2, default=str)
    
    @staticmethod
    def _export_to_csv(report: ProjectReportResponse, file_path: str):
        """Export report to CSV format."""
        # This is a simplified CSV export - in production, you'd want more sophisticated formatting
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(['Project Report', report.project.name])
            writer.writerow(['Generated At', report.generated_at])
            writer.writerow(['Report Type', report.report_type])
            writer.writerow([])
            
            # Write summary data
            writer.writerow(['Summary'])
            writer.writerow(['Total Tasks', report.summary.total_tasks])
            writer.writerow(['Completed Tasks', report.summary.completed_tasks])
            writer.writerow(['Completion Rate', f"{report.summary.completion_rate}%"])
            writer.writerow(['Total Time Logged', f"{report.summary.total_time_logged} hours"])
            writer.writerow([])
            
            # Write team performance
            if report.team_performance:
                writer.writerow(['Team Performance'])
                writer.writerow(['User', 'Tasks Assigned', 'Tasks Completed', 'Completion Rate', 'Time Logged'])
                for member in report.team_performance:
                    writer.writerow([
                        f"{member.user.first_name} {member.user.last_name}",
                        member.tasks_assigned,
                        member.tasks_completed,
                        f"{member.completion_rate}%",
                        f"{member.time_logged} hours"
                    ])
    
    @staticmethod
    def _export_to_pdf(report: ProjectReportResponse, file_path: str, include_charts: bool):
        """Export report to PDF format."""
        # Placeholder for PDF export - in production, use a library like reportlab or weasyprint
        with open(file_path, 'w') as f:
            f.write(f"PDF Export for {report.project.name}\n")
            f.write(f"Generated at: {report.generated_at}\n")
            f.write(f"Report type: {report.report_type}\n")
            f.write(f"Include charts: {include_charts}\n")
    
    @staticmethod
    def _export_to_excel(report: ProjectReportResponse, file_path: str, include_charts: bool):
        """Export report to Excel format."""
        # Placeholder for Excel export - in production, use a library like openpyxl or xlsxwriter
        with open(file_path, 'w') as f:
            f.write(f"Excel Export for {report.project.name}\n")
            f.write(f"Generated at: {report.generated_at}\n")
            f.write(f"Report type: {report.report_type}\n")
            f.write(f"Include charts: {include_charts}\n")
    
    @staticmethod
    def get_report_by_id(report_id: str) -> Optional[ProjectReportResponse]:
        """Get a generated report by ID."""
        return ReportsService._generated_reports.get(report_id)
    
    @staticmethod
    def get_export_by_id(export_id: str) -> Optional[ProjectReportExportResponse]:
        """Get an export by ID."""
        export_info = ReportsService._export_files.get(export_id)
        if export_info and export_info["expires_at"] > datetime.now(timezone.utc):
            return export_info["response"]
        return None
    
    @staticmethod
    def cleanup_expired_exports():
        """Clean up expired export files."""
        current_time = datetime.now(timezone.utc)
        expired_exports = []
        
        for export_id, export_info in ReportsService._export_files.items():
            if export_info["expires_at"] <= current_time:
                expired_exports.append(export_id)
                # Remove file if it exists
                if os.path.exists(export_info["file_path"]):
                    try:
                        os.remove(export_info["file_path"])
                    except OSError:
                        logger.warning(f"Failed to remove expired export file: {export_info['file_path']}")
        
        # Remove from memory
        for export_id in expired_exports:
            del ReportsService._export_files[export_id] 

    @staticmethod
    def generate_time_report(
        db: Session,
        report_type: TimeReportType,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        include_details: bool = True
    ) -> TimeReportResponse:
        """
        Generate a comprehensive time report.
        
        Args:
            db: Database session
            report_type: Type of time report to generate
            user_id: Optional user ID for user-specific reports
            project_id: Optional project ID for project-specific reports
            start_date: Optional start date for report period
            end_date: Optional end date for report period
            include_details: Whether to include detailed information
            
        Returns:
            Generated time report
        """
        # Generate report based on type
        if report_type == TimeReportType.GENERAL:
            return ReportsService._generate_general_time_report(
                db, start_date, end_date, include_details
            )
        elif report_type == TimeReportType.BY_USER:
            if not user_id:
                raise ValueError("user_id is required for user-specific time reports")
            return ReportsService._generate_user_time_report(
                db, user_id, start_date, end_date, include_details
            )
        elif report_type == TimeReportType.BY_PROJECT:
            if not project_id:
                raise ValueError("project_id is required for project-specific time reports")
            return ReportsService._generate_project_time_report(
                db, project_id, start_date, end_date, include_details
            )
        else:
            raise ValueError(f"Unsupported time report type: {report_type}")

    @staticmethod
    def _generate_general_time_report(
        db: Session,
        start_date: Optional[date],
        end_date: Optional[date],
        include_details: bool
    ) -> TimeReportResponse:
        """Generate a general time report for all users and projects."""
        # Build query for time entries
        query = db.query(TimeEntry).options(
            joinedload(TimeEntry.user),
            joinedload(TimeEntry.project),
            joinedload(TimeEntry.task)
        )
        
        # Apply date filters
        if start_date:
            query = query.filter(TimeEntry.date >= start_date)
        if end_date:
            query = query.filter(TimeEntry.date <= end_date)
        
        time_entries = query.all()
        
        # Generate report data
        summary = ReportsService._get_time_report_summary(time_entries)
        by_project = ReportsService._get_time_by_project(time_entries)
        by_category = ReportsService._get_time_by_category(time_entries)
        by_user = ReportsService._get_time_by_user(time_entries)
        daily_breakdown = ReportsService._get_time_daily_breakdown(time_entries)
        
        # Create report
        report = TimeReportResponse(
            report_id=str(uuid4()),
            report_type=TimeReportType.GENERAL,
            generated_at=datetime.now(timezone.utc),
            period_start=start_date,
            period_end=end_date,
            summary=summary,
            by_project=by_project,
            by_category=by_category,
            by_user=by_user,
            daily_breakdown=daily_breakdown,
            metadata={"include_details": include_details}
        )
        
        # Store report
        ReportsService._generated_time_reports[report.report_id] = report
        
        return report

    @staticmethod
    def _generate_user_time_report(
        db: Session,
        user_id: str,
        start_date: Optional[date],
        end_date: Optional[date],
        include_details: bool
    ) -> TimeReportResponse:
        """Generate a time report for a specific user."""
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Build query for user's time entries
        query = db.query(TimeEntry).options(
            joinedload(TimeEntry.user),
            joinedload(TimeEntry.project),
            joinedload(TimeEntry.task)
        ).filter(TimeEntry.user_id == user_id)
        
        # Apply date filters
        if start_date:
            query = query.filter(TimeEntry.date >= start_date)
        if end_date:
            query = query.filter(TimeEntry.date <= end_date)
        
        time_entries = query.all()
        
        # Generate report data
        summary = ReportsService._get_time_report_summary(time_entries)
        by_project = ReportsService._get_time_by_project(time_entries)
        by_category = ReportsService._get_time_by_category(time_entries)
        by_user = ReportsService._get_time_by_user(time_entries)
        daily_breakdown = ReportsService._get_time_daily_breakdown(time_entries)
        
        # Create report
        report = TimeReportResponse(
            report_id=str(uuid4()),
            report_type=TimeReportType.BY_USER,
            generated_at=datetime.now(timezone.utc),
            period_start=start_date,
            period_end=end_date,
            summary=summary,
            by_project=by_project,
            by_category=by_category,
            by_user=by_user,
            daily_breakdown=daily_breakdown,
            metadata={"user_id": user_id, "include_details": include_details}
        )
        
        # Store report
        ReportsService._generated_time_reports[report.report_id] = report
        
        return report

    @staticmethod
    def _generate_project_time_report(
        db: Session,
        project_id: str,
        start_date: Optional[date],
        end_date: Optional[date],
        include_details: bool
    ) -> TimeReportResponse:
        """Generate a time report for a specific project."""
        # Verify project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")
        
        # Build query for project's time entries
        query = db.query(TimeEntry).options(
            joinedload(TimeEntry.user),
            joinedload(TimeEntry.project),
            joinedload(TimeEntry.task)
        ).filter(TimeEntry.project_id == project_id)
        
        # Apply date filters
        if start_date:
            query = query.filter(TimeEntry.date >= start_date)
        if end_date:
            query = query.filter(TimeEntry.date <= end_date)
        
        time_entries = query.all()
        
        # Generate report data
        summary = ReportsService._get_time_report_summary(time_entries)
        by_project = ReportsService._get_time_by_project(time_entries)
        by_category = ReportsService._get_time_by_category(time_entries)
        by_user = ReportsService._get_time_by_user(time_entries)
        daily_breakdown = ReportsService._get_time_daily_breakdown(time_entries)
        
        # Create report
        report = TimeReportResponse(
            report_id=str(uuid4()),
            report_type=TimeReportType.BY_PROJECT,
            generated_at=datetime.now(timezone.utc),
            period_start=start_date,
            period_end=end_date,
            summary=summary,
            by_project=by_project,
            by_category=by_category,
            by_user=by_user,
            daily_breakdown=daily_breakdown,
            metadata={"project_id": project_id, "include_details": include_details}
        )
        
        # Store report
        ReportsService._generated_time_reports[report.report_id] = report
        
        return report

    @staticmethod
    def _get_time_report_summary(time_entries: List[TimeEntry]) -> TimeReportSummaryData:
        """Generate summary data for time report."""
        if not time_entries:
            return TimeReportSummaryData(
                total_hours=0.0,
                total_days=0,
                average_hours_per_day=0.0,
                total_entries=0,
                approved_entries=0,
                pending_entries=0,
                approval_rate=0.0
            )
        
        total_hours = sum(entry.hours for entry in time_entries)
        total_entries = len(time_entries)
        approved_entries = sum(1 for entry in time_entries if entry.is_approved)
        pending_entries = total_entries - approved_entries
        
        # Calculate unique days
        unique_dates = set(entry.date for entry in time_entries)
        total_days = len(unique_dates)
        
        # Calculate averages
        average_hours_per_day = total_hours / total_days if total_days > 0 else 0.0
        approval_rate = (approved_entries / total_entries * 100) if total_entries > 0 else 0.0
        
        return TimeReportSummaryData(
            total_hours=total_hours,
            total_days=total_days,
            average_hours_per_day=average_hours_per_day,
            total_entries=total_entries,
            approved_entries=approved_entries,
            pending_entries=pending_entries,
            approval_rate=approval_rate
        )

    @staticmethod
    def _get_time_by_project(time_entries: List[TimeEntry]) -> List[TimeReportByProjectData]:
        """Generate time data grouped by project."""
        if not time_entries:
            return []
        
        # Group by project
        project_data = {}
        total_hours = sum(entry.hours for entry in time_entries)
        
        for entry in time_entries:
            project_id = entry.project_id
            if project_id not in project_data:
                project_data[project_id] = {
                    'project_name': entry.project.name if entry.project else 'Unknown Project',
                    'hours': 0.0,
                    'entries_count': 0
                }
            
            project_data[project_id]['hours'] += entry.hours
            project_data[project_id]['entries_count'] += 1
        
        # Convert to response format
        result = []
        for project_id, data in project_data.items():
            percentage = (data['hours'] / total_hours * 100) if total_hours > 0 else 0.0
            average_hours_per_entry = data['hours'] / data['entries_count'] if data['entries_count'] > 0 else 0.0
            
            result.append(TimeReportByProjectData(
                project_id=project_id,
                project_name=data['project_name'],
                hours=data['hours'],
                percentage=percentage,
                entries_count=data['entries_count'],
                average_hours_per_entry=average_hours_per_entry
            ))
        
        # Sort by hours descending
        result.sort(key=lambda x: x.hours, reverse=True)
        return result

    @staticmethod
    def _get_time_by_category(time_entries: List[TimeEntry]) -> List[TimeReportByCategoryData]:
        """Generate time data grouped by category."""
        if not time_entries:
            return []
        
        # Group by category
        category_data = {}
        total_hours = sum(entry.hours for entry in time_entries)
        
        for entry in time_entries:
            category = entry.category or 'Uncategorized'
            if category not in category_data:
                category_data[category] = {
                    'hours': 0.0,
                    'entries_count': 0
                }
            
            category_data[category]['hours'] += entry.hours
            category_data[category]['entries_count'] += 1
        
        # Convert to response format
        result = []
        for category, data in category_data.items():
            percentage = (data['hours'] / total_hours * 100) if total_hours > 0 else 0.0
            
            result.append(TimeReportByCategoryData(
                category=category,
                hours=data['hours'],
                percentage=percentage,
                entries_count=data['entries_count']
            ))
        
        # Sort by hours descending
        result.sort(key=lambda x: x.hours, reverse=True)
        return result

    @staticmethod
    def _get_time_by_user(time_entries: List[TimeEntry]) -> List[TimeReportByUserData]:
        """Generate time data grouped by user."""
        if not time_entries:
            return []
        
        # Group by user
        user_data = {}
        total_hours = sum(entry.hours for entry in time_entries)
        
        for entry in time_entries:
            user_id = entry.user_id
            if user_id not in user_data:
                user_data[user_id] = {
                    'user_name': entry.user.name if entry.user else 'Unknown User',
                    'hours': 0.0,
                    'entries_count': 0,
                    'dates': set()
                }
            
            user_data[user_id]['hours'] += entry.hours
            user_data[user_id]['entries_count'] += 1
            user_data[user_id]['dates'].add(entry.date)
        
        # Convert to response format
        result = []
        for user_id, data in user_data.items():
            percentage = (data['hours'] / total_hours * 100) if total_hours > 0 else 0.0
            average_hours_per_day = data['hours'] / len(data['dates']) if data['dates'] else 0.0
            
            result.append(TimeReportByUserData(
                user_id=user_id,
                user_name=data['user_name'],
                hours=data['hours'],
                percentage=percentage,
                entries_count=data['entries_count'],
                average_hours_per_day=average_hours_per_day
            ))
        
        # Sort by hours descending
        result.sort(key=lambda x: x.hours, reverse=True)
        return result

    @staticmethod
    def _get_time_daily_breakdown(time_entries: List[TimeEntry]) -> List[TimeReportDailyData]:
        """Generate daily breakdown of time entries."""
        if not time_entries:
            return []
        
        # Group by date
        daily_data = {}
        
        for entry in time_entries:
            date_key = entry.date
            if date_key not in daily_data:
                daily_data[date_key] = {
                    'hours': 0.0,
                    'entries_count': 0,
                    'projects': set()
                }
            
            daily_data[date_key]['hours'] += entry.hours
            daily_data[date_key]['entries_count'] += 1
            if entry.project_id:
                daily_data[date_key]['projects'].add(entry.project_id)
        
        # Convert to response format
        result = []
        for date_key, data in daily_data.items():
            result.append(TimeReportDailyData(
                work_date=date_key,
                hours=data['hours'],
                entries_count=data['entries_count'],
                projects_count=len(data['projects'])
            ))
        
        # Sort by date
        result.sort(key=lambda x: x.date)
        return result

    @staticmethod
    def export_time_report(
        db: Session,
        report_type: TimeReportType,
        format: ReportFormat,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        include_charts: bool = True,
        filename: Optional[str] = None
    ) -> TimeReportExportResponse:
        """
        Export a time report in the specified format.
        
        Args:
            db: Database session
            report_type: Type of time report to export
            format: Export format
            user_id: Optional user ID for user-specific reports
            project_id: Optional project ID for project-specific reports
            start_date: Optional start date for report period
            end_date: Optional end date for report period
            include_charts: Whether to include charts in export
            filename: Optional custom filename
            
        Returns:
            Export response with download information
        """
        # Generate the report
        report = ReportsService.generate_time_report(
            db, report_type, user_id, project_id, start_date, end_date, True
        )
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"time_report_{report_type.value}_{timestamp}"
        
        # Create export directory if it doesn't exist
        export_dir = "exports"
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
        
        # Generate file path
        file_path = os.path.join(export_dir, f"{filename}.{format.value}")
        
        # Export based on format
        if format == ReportFormat.JSON:
            ReportsService._export_time_to_json(report, file_path)
        elif format == ReportFormat.CSV:
            ReportsService._export_time_to_csv(report, file_path)
        elif format == ReportFormat.PDF:
            ReportsService._export_time_to_pdf(report, file_path, include_charts)
        elif format == ReportFormat.EXCEL:
            ReportsService._export_time_to_excel(report, file_path, include_charts)
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        # Get file size
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else None
        
        # Create export response
        export_id = str(uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        
        export_response = TimeReportExportResponse(
            export_id=export_id,
            filename=os.path.basename(file_path),
            format=format,
            download_url=f"/exports/{os.path.basename(file_path)}",
            file_size=file_size,
            expires_at=expires_at,
            metadata={
                "report_id": report.report_id,
                "report_type": report.report_type.value,
                "include_charts": include_charts
            }
        )
        
        # Store export information
        ReportsService._export_files[export_id] = {
            "file_path": file_path,
            "expires_at": expires_at,
            "report_id": report.report_id
        }
        
        return export_response

    @staticmethod
    def _export_time_to_json(report: TimeReportResponse, file_path: str):
        """Export time report to JSON format."""
        with open(file_path, 'w') as f:
            json.dump(report.dict(), f, indent=2, default=str)

    @staticmethod
    def _export_time_to_csv(report: TimeReportResponse, file_path: str):
        """Export time report to CSV format."""
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(['Time Report', report.report_type.value])
            writer.writerow(['Generated At', report.generated_at])
            writer.writerow(['Period Start', report.period_start])
            writer.writerow(['Period End', report.period_end])
            writer.writerow([])
            
            # Write summary
            writer.writerow(['Summary'])
            writer.writerow(['Total Hours', report.summary.total_hours])
            writer.writerow(['Total Days', report.summary.total_days])
            writer.writerow(['Average Hours Per Day', report.summary.average_hours_per_day])
            writer.writerow(['Total Entries', report.summary.total_entries])
            writer.writerow(['Approved Entries', report.summary.approved_entries])
            writer.writerow(['Pending Entries', report.summary.pending_entries])
            writer.writerow(['Approval Rate', f"{report.summary.approval_rate:.2f}%"])
            writer.writerow([])
            
            # Write by project
            if report.by_project:
                writer.writerow(['By Project'])
                writer.writerow(['Project ID', 'Project Name', 'Hours', 'Percentage', 'Entries Count', 'Avg Hours Per Entry'])
                for project in report.by_project:
                    writer.writerow([
                        project.project_id,
                        project.project_name,
                        project.hours,
                        f"{project.percentage:.2f}%",
                        project.entries_count,
                        project.average_hours_per_entry
                    ])
                writer.writerow([])
            
            # Write by category
            if report.by_category:
                writer.writerow(['By Category'])
                writer.writerow(['Category', 'Hours', 'Percentage', 'Entries Count'])
                for category in report.by_category:
                    writer.writerow([
                        category.category,
                        category.hours,
                        f"{category.percentage:.2f}%",
                        category.entries_count
                    ])
                writer.writerow([])
            
            # Write by user
            if report.by_user:
                writer.writerow(['By User'])
                writer.writerow(['User ID', 'User Name', 'Hours', 'Percentage', 'Entries Count', 'Avg Hours Per Day'])
                for user in report.by_user:
                    writer.writerow([
                        user.user_id,
                        user.user_name,
                        user.hours,
                        f"{user.percentage:.2f}%",
                        user.entries_count,
                        user.average_hours_per_day
                    ])
                writer.writerow([])
            
            # Write daily breakdown
            if report.daily_breakdown:
                writer.writerow(['Daily Breakdown'])
                writer.writerow(['Date', 'Hours', 'Entries Count', 'Projects Count'])
                for daily in report.daily_breakdown:
                    writer.writerow([
                        daily.work_date,
                        daily.hours,
                        daily.entries_count,
                        daily.projects_count
                    ])

    @staticmethod
    def _export_time_to_pdf(report: TimeReportResponse, file_path: str, include_charts: bool):
        """Export time report to PDF format."""
        # For now, create a simple text-based PDF
        # In production, use a library like reportlab or weasyprint
        with open(file_path, 'w') as f:
            f.write(f"Time Report: {report.report_type.value}\n")
            f.write(f"Generated: {report.generated_at}\n")
            f.write(f"Period: {report.period_start} to {report.period_end}\n\n")
            f.write(f"Total Hours: {report.summary.total_hours}\n")
            f.write(f"Total Days: {report.summary.total_days}\n")
            f.write(f"Average Hours Per Day: {report.summary.average_hours_per_day}\n")

    @staticmethod
    def _export_time_to_excel(report: TimeReportResponse, file_path: str, include_charts: bool):
        """Export time report to Excel format."""
        # For now, create a CSV file with .xlsx extension
        # In production, use a library like openpyxl or xlsxwriter
        ReportsService._export_time_to_csv(report, file_path)

    @staticmethod
    def get_time_report_by_id(report_id: str) -> Optional[TimeReportResponse]:
        """Get a time report by ID."""
        return ReportsService._generated_time_reports.get(report_id)

    @staticmethod
    def get_time_export_by_id(export_id: str) -> Optional[TimeReportExportResponse]:
        """Get a time export by ID."""
        export_info = ReportsService._export_files.get(export_id)
        if not export_info:
            return None
        
        # Check if export has expired
        if datetime.now(timezone.utc) > export_info['expires_at']:
            return None
        
        # Reconstruct response
        return TimeReportExportResponse(
            export_id=export_id,
            filename=os.path.basename(export_info['file_path']),
            format=ReportFormat.JSON,  # This would need to be stored
            download_url=f"/exports/{os.path.basename(export_info['file_path'])}",
            file_size=os.path.getsize(export_info['file_path']) if os.path.exists(export_info['file_path']) else None,
            expires_at=export_info['expires_at'],
            metadata={"report_id": export_info['report_id']}
        ) 

    @staticmethod
    def generate_performance_report(
        db: Session,
        report_type: PerformanceReportType,
        user_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        include_details: bool = True
    ) -> PerformanceReportResponse:
        """
        Generate a comprehensive performance report.
        
        Args:
            db: Database session
            report_type: Type of performance report to generate
            user_id: Optional user ID for individual performance reports
            start_date: Optional start date for report period
            end_date: Optional end date for report period
            include_details: Whether to include detailed information
            
        Returns:
            Generated performance report
        """
        # Generate report based on type
        if report_type == PerformanceReportType.GENERAL:
            return ReportsService._generate_general_performance_report(
                db, start_date, end_date, include_details
            )
        elif report_type == PerformanceReportType.INDIVIDUAL:
            if not user_id:
                raise ValueError("user_id is required for individual performance reports")
            return ReportsService._generate_individual_performance_report(
                db, user_id, start_date, end_date, include_details
            )
        elif report_type == PerformanceReportType.TEAM:
            return ReportsService._generate_team_performance_report(
                db, start_date, end_date, include_details
            )
        else:
            raise ValueError(f"Unsupported performance report type: {report_type}")

    @staticmethod
    def _generate_general_performance_report(
        db: Session,
        start_date: Optional[date],
        end_date: Optional[date],
        include_details: bool
    ) -> PerformanceReportResponse:
        """Generate a general performance report for all users."""
        # Get all users with their tasks and time entries
        users = db.query(User).options(
            joinedload(User.tasks),
            joinedload(User.time_entries)
        ).all()
        
        # Generate report data
        summary = ReportsService._get_performance_summary(users, start_date, end_date)
        individual_performances = ReportsService._get_individual_performances(users, start_date, end_date)
        team_performance = ReportsService._get_team_performance(users, start_date, end_date)
        performance_metrics = ReportsService._get_performance_metrics(users, start_date, end_date)
        
        # Create report
        report = PerformanceReportResponse(
            report_id=str(uuid4()),
            report_type=PerformanceReportType.GENERAL,
            generated_at=datetime.now(timezone.utc),
            period_start=start_date,
            period_end=end_date,
            summary=summary,
            individual_performances=individual_performances,
            team_performance=team_performance,
            performance_metrics=performance_metrics,
            metadata={"include_details": include_details}
        )
        
        # Store report
        ReportsService._generated_performance_reports[report.report_id] = report
        
        return report

    @staticmethod
    def _generate_individual_performance_report(
        db: Session,
        user_id: str,
        start_date: Optional[date],
        end_date: Optional[date],
        include_details: bool
    ) -> PerformanceReportResponse:
        """Generate a performance report for a specific user."""
        # Verify user exists
        user = db.query(User).options(
            joinedload(User.tasks),
            joinedload(User.time_entries)
        ).filter(User.id == user_id).first()
        
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Generate report data for single user
        users = [user]
        summary = ReportsService._get_performance_summary(users, start_date, end_date)
        individual_performances = ReportsService._get_individual_performances(users, start_date, end_date)
        team_performance = None  # Not applicable for individual reports
        performance_metrics = ReportsService._get_performance_metrics(users, start_date, end_date)
        
        # Create report
        report = PerformanceReportResponse(
            report_id=str(uuid4()),
            report_type=PerformanceReportType.INDIVIDUAL,
            generated_at=datetime.now(timezone.utc),
            period_start=start_date,
            period_end=end_date,
            summary=summary,
            individual_performances=individual_performances,
            team_performance=team_performance,
            performance_metrics=performance_metrics,
            metadata={"user_id": user_id, "include_details": include_details}
        )
        
        # Store report
        ReportsService._generated_performance_reports[report.report_id] = report
        
        return report

    @staticmethod
    def _generate_team_performance_report(
        db: Session,
        start_date: Optional[date],
        end_date: Optional[date],
        include_details: bool
    ) -> PerformanceReportResponse:
        """Generate a team performance report."""
        # Get all users with their tasks and time entries
        users = db.query(User).options(
            joinedload(User.tasks),
            joinedload(User.time_entries)
        ).all()
        
        # Generate report data
        summary = ReportsService._get_performance_summary(users, start_date, end_date)
        individual_performances = ReportsService._get_individual_performances(users, start_date, end_date)
        team_performance = ReportsService._get_team_performance(users, start_date, end_date)
        performance_metrics = ReportsService._get_performance_metrics(users, start_date, end_date)
        
        # Create report
        report = PerformanceReportResponse(
            report_id=str(uuid4()),
            report_type=PerformanceReportType.TEAM,
            generated_at=datetime.now(timezone.utc),
            period_start=start_date,
            period_end=end_date,
            summary=summary,
            individual_performances=individual_performances,
            team_performance=team_performance,
            performance_metrics=performance_metrics,
            metadata={"include_details": include_details}
        )
        
        # Store report
        ReportsService._generated_performance_reports[report.report_id] = report
        
        return report

    @staticmethod
    def _get_performance_summary(users: List[User], start_date: Optional[date], end_date: Optional[date]) -> PerformanceSummaryData:
        """Generate performance summary data."""
        if not users:
            return PerformanceSummaryData(
                total_users=0,
                active_users=0,
                total_tasks_completed=0,
                total_time_logged=0.0,
                average_completion_rate=0.0,
                average_time_per_task=0.0,
                top_performers_count=0,
                improvement_areas_count=0
            )
        
        total_users = len(users)
        active_users = sum(1 for user in users if user.tasks or user.time_entries)
        
        # Calculate task statistics
        total_tasks_completed = 0
        total_time_logged = 0.0
        completion_rates = []
        
        for user in users:
            # Filter tasks by date range
            user_tasks = user.tasks
            if start_date:
                user_tasks = [task for task in user_tasks if task.created_at and task.created_at.date() >= start_date]
            if end_date:
                user_tasks = [task for task in user_tasks if task.created_at and task.created_at.date() <= end_date]
            
            completed_tasks = sum(1 for task in user_tasks if task.status == "completed")
            total_tasks_completed += completed_tasks
            
            if user_tasks:
                completion_rate = (completed_tasks / len(user_tasks)) * 100
                completion_rates.append(completion_rate)
            
            # Filter time entries by date range
            user_time_entries = user.time_entries
            if start_date:
                user_time_entries = [entry for entry in user_time_entries if entry.date >= start_date]
            if end_date:
                user_time_entries = [entry for entry in user_time_entries if entry.date <= end_date]
            
            total_time_logged += sum(entry.hours for entry in user_time_entries)
        
        # Calculate averages
        average_completion_rate = sum(completion_rates) / len(completion_rates) if completion_rates else 0.0
        average_time_per_task = total_time_logged / total_tasks_completed if total_tasks_completed > 0 else 0.0
        
        # Calculate top performers and improvement areas
        top_performers_count = sum(1 for rate in completion_rates if rate >= 80.0)
        improvement_areas_count = sum(1 for rate in completion_rates if rate < 60.0)
        
        return PerformanceSummaryData(
            total_users=total_users,
            active_users=active_users,
            total_tasks_completed=total_tasks_completed,
            total_time_logged=total_time_logged,
            average_completion_rate=average_completion_rate,
            average_time_per_task=average_time_per_task,
            top_performers_count=top_performers_count,
            improvement_areas_count=improvement_areas_count
        )

    @staticmethod
    def _get_individual_performances(users: List[User], start_date: Optional[date], end_date: Optional[date]) -> List[IndividualPerformanceData]:
        """Generate individual performance data for all users."""
        individual_performances = []
        
        for user in users:
            # Filter tasks by date range
            user_tasks = user.tasks
            if start_date:
                user_tasks = [task for task in user_tasks if task.created_at and task.created_at.date() >= start_date]
            if end_date:
                user_tasks = [task for task in user_tasks if task.created_at and task.created_at.date() <= end_date]
            
            # Filter time entries by date range
            user_time_entries = user.time_entries
            if start_date:
                user_time_entries = [entry for entry in user_time_entries if entry.date >= start_date]
            if end_date:
                user_time_entries = [entry for entry in user_time_entries if entry.date <= end_date]
            
            # Calculate task statistics
            tasks_assigned = len(user_tasks)
            tasks_completed = sum(1 for task in user_tasks if task.status == "completed")
            tasks_in_progress = sum(1 for task in user_tasks if task.status == "in_progress")
            tasks_overdue = sum(1 for task in user_tasks if task.due_date and task.due_date < date.today() and task.status != "completed")
            
            completion_rate = (tasks_completed / tasks_assigned * 100) if tasks_assigned > 0 else 0.0
            
            # Calculate time statistics
            total_time_logged = sum(entry.hours for entry in user_time_entries)
            average_time_per_task = total_time_logged / tasks_completed if tasks_completed > 0 else 0.0
            
            # Calculate on-time delivery rate
            on_time_tasks = sum(1 for task in user_tasks if task.status == "completed" and 
                               (not task.due_date or task.completed_at and task.completed_at.date() <= task.due_date))
            on_time_delivery_rate = (on_time_tasks / tasks_completed * 100) if tasks_completed > 0 else 0.0
            
            # Calculate performance score (weighted average of completion rate, on-time delivery, and efficiency)
            performance_score = (completion_rate * 0.4 + on_time_delivery_rate * 0.4 + 
                               (100 - average_time_per_task * 10) * 0.2)  # Simplified scoring
            
            # Calculate skills utilization
            skills_utilization = {}
            for entry in user_time_entries:
                category = entry.category or "General"
                if category not in skills_utilization:
                    skills_utilization[category] = 0.0
                skills_utilization[category] += entry.hours
            
            # Calculate project contributions
            project_contributions = []
            project_hours = {}
            for entry in user_time_entries:
                if entry.project_id:
                    project_id = entry.project_id
                    if project_id not in project_hours:
                        project_hours[project_id] = 0.0
                    project_hours[project_id] += entry.hours
            
            for project_id, hours in project_hours.items():
                project_contributions.append({
                    "project_id": project_id,
                    "hours_contributed": hours,
                    "tasks_completed": sum(1 for task in user_tasks if task.project_id == project_id and task.status == "completed")
                })
            
            # Create individual performance data
            individual_performance = IndividualPerformanceData(
                user=user,
                tasks_assigned=tasks_assigned,
                tasks_completed=tasks_completed,
                tasks_in_progress=tasks_in_progress,
                tasks_overdue=tasks_overdue,
                completion_rate=completion_rate,
                total_time_logged=total_time_logged,
                average_time_per_task=average_time_per_task,
                on_time_delivery_rate=on_time_delivery_rate,
                performance_score=min(100.0, max(0.0, performance_score)),
                skills_utilization=skills_utilization,
                project_contributions=project_contributions
            )
            
            individual_performances.append(individual_performance)
        
        # Sort by performance score descending
        individual_performances.sort(key=lambda x: x.performance_score, reverse=True)
        return individual_performances

    @staticmethod
    def _get_team_performance(users: List[User], start_date: Optional[date], end_date: Optional[date]) -> TeamPerformanceData:
        """Generate team performance data."""
        if not users:
            return TeamPerformanceData(
                team_size=0,
                total_tasks=0,
                completed_tasks=0,
                team_completion_rate=0.0,
                average_performance_score=0.0,
                collaboration_score=0.0,
                top_performers=[],
                improvement_areas=[],
                skill_gaps=[]
            )
        
        team_size = len(users)
        
        # Calculate team task statistics
        total_tasks = 0
        completed_tasks = 0
        
        for user in users:
            user_tasks = user.tasks
            if start_date:
                user_tasks = [task for task in user_tasks if task.created_at and task.created_at.date() >= start_date]
            if end_date:
                user_tasks = [task for task in user_tasks if task.created_at and task.created_at.date() <= end_date]
            
            total_tasks += len(user_tasks)
            completed_tasks += sum(1 for task in user_tasks if task.status == "completed")
        
        team_completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
        
        # Get individual performances for team analysis
        individual_performances = ReportsService._get_individual_performances(users, start_date, end_date)
        
        # Calculate average performance score
        performance_scores = [perf.performance_score for perf in individual_performances]
        average_performance_score = sum(performance_scores) / len(performance_scores) if performance_scores else 0.0
        
        # Calculate collaboration score (simplified - based on shared projects)
        collaboration_score = 75.0  # Placeholder - would need more complex logic
        
        # Get top performers (top 20% or at least 3 users)
        top_count = max(3, len(individual_performances) // 5)
        top_performers = individual_performances[:top_count]
        
        # Identify improvement areas
        improvement_areas = []
        for perf in individual_performances:
            if perf.performance_score < 60.0:
                improvement_areas.append({
                    "user_id": perf.user.id,
                    "user_name": perf.user.name,
                    "performance_score": perf.performance_score,
                    "areas": ["Task completion", "Time management"] if perf.completion_rate < 60.0 else ["Time management"]
                })
        
        # Identify skill gaps (simplified)
        skill_gaps = []
        all_skills = set()
        for perf in individual_performances:
            all_skills.update(perf.skills_utilization.keys())
        
        for skill in all_skills:
            skill_users = [perf for perf in individual_performances if skill in perf.skills_utilization]
            if len(skill_users) < len(individual_performances) * 0.3:  # Less than 30% of team has this skill
                skill_gaps.append({
                    "skill": skill,
                    "users_with_skill": len(skill_users),
                    "total_users": len(individual_performances),
                    "gap_percentage": (len(individual_performances) - len(skill_users)) / len(individual_performances) * 100
                })
        
        return TeamPerformanceData(
            team_size=team_size,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            team_completion_rate=team_completion_rate,
            average_performance_score=average_performance_score,
            collaboration_score=collaboration_score,
            top_performers=top_performers,
            improvement_areas=improvement_areas,
            skill_gaps=skill_gaps
        )

    @staticmethod
    def _get_performance_metrics(users: List[User], start_date: Optional[date], end_date: Optional[date]) -> PerformanceMetricsData:
        """Generate detailed performance metrics."""
        if not users:
            return PerformanceMetricsData(
                productivity_score=0.0,
                efficiency_score=0.0,
                quality_score=0.0,
                reliability_score=0.0,
                collaboration_score=0.0,
                innovation_score=0.0
            )
        
        # Calculate productivity score (based on tasks completed per time period)
        total_tasks_completed = 0
        total_time_logged = 0.0
        
        for user in users:
            user_tasks = user.tasks
            if start_date:
                user_tasks = [task for task in user_tasks if task.created_at and task.created_at.date() >= start_date]
            if end_date:
                user_tasks = [task for task in user_tasks if task.created_at and task.created_at.date() <= end_date]
            
            total_tasks_completed += sum(1 for task in user_tasks if task.status == "completed")
            
            user_time_entries = user.time_entries
            if start_date:
                user_time_entries = [entry for entry in user_time_entries if entry.date >= start_date]
            if end_date:
                user_time_entries = [entry for entry in user_time_entries if entry.date <= end_date]
            
            total_time_logged += sum(entry.hours for entry in user_time_entries)
        
        # Calculate metrics (simplified calculations)
        productivity_score = min(100.0, (total_tasks_completed / max(1, total_time_logged)) * 10)
        efficiency_score = min(100.0, (total_tasks_completed / len(users)) * 5) if users else 0.0
        quality_score = 85.0  # Placeholder - would need quality metrics
        reliability_score = 90.0  # Placeholder - would need reliability metrics
        collaboration_score = 80.0  # Placeholder - would need collaboration metrics
        innovation_score = 75.0  # Placeholder - would need innovation metrics
        
        return PerformanceMetricsData(
            productivity_score=productivity_score,
            efficiency_score=efficiency_score,
            quality_score=quality_score,
            reliability_score=reliability_score,
            collaboration_score=collaboration_score,
            innovation_score=innovation_score
        )

    @staticmethod
    def export_performance_report(
        db: Session,
        report_type: PerformanceReportType,
        format: ReportFormat,
        user_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        include_charts: bool = True,
        filename: Optional[str] = None
    ) -> PerformanceReportExportResponse:
        """
        Export a performance report in the specified format.
        
        Args:
            db: Database session
            report_type: Type of performance report to export
            format: Export format
            user_id: Optional user ID for individual performance reports
            start_date: Optional start date for report period
            end_date: Optional end date for report period
            include_charts: Whether to include charts in export
            filename: Optional custom filename
            
        Returns:
            Export response with download information
        """
        # Generate the report
        report = ReportsService.generate_performance_report(
            db, report_type, user_id, start_date, end_date, True
        )
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_report_{report_type.value}_{timestamp}"
        
        # Create export directory if it doesn't exist
        export_dir = "exports"
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
        
        # Generate file path
        file_path = os.path.join(export_dir, f"{filename}.{format.value}")
        
        # Export based on format
        if format == ReportFormat.JSON:
            ReportsService._export_performance_to_json(report, file_path)
        elif format == ReportFormat.CSV:
            ReportsService._export_performance_to_csv(report, file_path)
        elif format == ReportFormat.PDF:
            ReportsService._export_performance_to_pdf(report, file_path, include_charts)
        elif format == ReportFormat.EXCEL:
            ReportsService._export_performance_to_excel(report, file_path, include_charts)
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        # Get file size
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else None
        
        # Create export response
        export_id = str(uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        
        export_response = PerformanceReportExportResponse(
            export_id=export_id,
            filename=os.path.basename(file_path),
            format=format,
            download_url=f"/exports/{os.path.basename(file_path)}",
            file_size=file_size,
            expires_at=expires_at,
            metadata={
                "report_id": report.report_id,
                "report_type": report.report_type.value,
                "include_charts": include_charts
            }
        )
        
        # Store export information
        ReportsService._export_files[export_id] = {
            "file_path": file_path,
            "expires_at": expires_at,
            "report_id": report.report_id
        }
        
        return export_response

    @staticmethod
    def _export_performance_to_json(report: PerformanceReportResponse, file_path: str):
        """Export performance report to JSON format."""
        with open(file_path, 'w') as f:
            json.dump(report.dict(), f, indent=2, default=str)

    @staticmethod
    def _export_performance_to_csv(report: PerformanceReportResponse, file_path: str):
        """Export performance report to CSV format."""
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(['Performance Report', report.report_type.value])
            writer.writerow(['Generated At', report.generated_at])
            writer.writerow(['Period Start', report.period_start])
            writer.writerow(['Period End', report.period_end])
            writer.writerow([])
            
            # Write summary
            writer.writerow(['Summary'])
            writer.writerow(['Total Users', report.summary.total_users])
            writer.writerow(['Active Users', report.summary.active_users])
            writer.writerow(['Total Tasks Completed', report.summary.total_tasks_completed])
            writer.writerow(['Total Time Logged', report.summary.total_time_logged])
            writer.writerow(['Average Completion Rate', f"{report.summary.average_completion_rate:.2f}%"])
            writer.writerow(['Average Time Per Task', f"{report.summary.average_time_per_task:.2f} hours"])
            writer.writerow(['Top Performers Count', report.summary.top_performers_count])
            writer.writerow(['Improvement Areas Count', report.summary.improvement_areas_count])
            writer.writerow([])
            
            # Write individual performances
            if report.individual_performances:
                writer.writerow(['Individual Performances'])
                writer.writerow(['User ID', 'User Name', 'Tasks Assigned', 'Tasks Completed', 'Completion Rate', 'Performance Score', 'Total Time Logged'])
                for perf in report.individual_performances:
                    writer.writerow([
                        perf.user.id,
                        perf.user.name,
                        perf.tasks_assigned,
                        perf.tasks_completed,
                        f"{perf.completion_rate:.2f}%",
                        f"{perf.performance_score:.2f}%",
                        f"{perf.total_time_logged:.2f} hours"
                    ])
                writer.writerow([])
            
            # Write team performance
            if report.team_performance:
                writer.writerow(['Team Performance'])
                writer.writerow(['Team Size', report.team_performance.team_size])
                writer.writerow(['Total Tasks', report.team_performance.total_tasks])
                writer.writerow(['Completed Tasks', report.team_performance.completed_tasks])
                writer.writerow(['Team Completion Rate', f"{report.team_performance.team_completion_rate:.2f}%"])
                writer.writerow(['Average Performance Score', f"{report.team_performance.average_performance_score:.2f}%"])
                writer.writerow(['Collaboration Score', f"{report.team_performance.collaboration_score:.2f}%"])
                writer.writerow([])
            
            # Write performance metrics
            writer.writerow(['Performance Metrics'])
            writer.writerow(['Productivity Score', f"{report.performance_metrics.productivity_score:.2f}%"])
            writer.writerow(['Efficiency Score', f"{report.performance_metrics.efficiency_score:.2f}%"])
            writer.writerow(['Quality Score', f"{report.performance_metrics.quality_score:.2f}%"])
            writer.writerow(['Reliability Score', f"{report.performance_metrics.reliability_score:.2f}%"])
            writer.writerow(['Collaboration Score', f"{report.performance_metrics.collaboration_score:.2f}%"])
            writer.writerow(['Innovation Score', f"{report.performance_metrics.innovation_score:.2f}%"])

    @staticmethod
    def _export_performance_to_pdf(report: PerformanceReportResponse, file_path: str, include_charts: bool):
        """Export performance report to PDF format."""
        # For now, create a simple text-based PDF
        # In production, use a library like reportlab or weasyprint
        with open(file_path, 'w') as f:
            f.write(f"Performance Report: {report.report_type.value}\n")
            f.write(f"Generated: {report.generated_at}\n")
            f.write(f"Period: {report.period_start} to {report.period_end}\n\n")
            f.write(f"Total Users: {report.summary.total_users}\n")
            f.write(f"Active Users: {report.summary.active_users}\n")
            f.write(f"Total Tasks Completed: {report.summary.total_tasks_completed}\n")
            f.write(f"Average Completion Rate: {report.summary.average_completion_rate:.2f}%\n")

    @staticmethod
    def _export_performance_to_excel(report: PerformanceReportResponse, file_path: str, include_charts: bool):
        """Export performance report to Excel format."""
        # For now, create a CSV file with .xlsx extension
        # In production, use a library like openpyxl or xlsxwriter
        ReportsService._export_performance_to_csv(report, file_path)

    @staticmethod
    def get_performance_report_by_id(report_id: str) -> Optional[PerformanceReportResponse]:
        """Get a performance report by ID."""
        return ReportsService._generated_performance_reports.get(report_id)

    @staticmethod
    def get_performance_export_by_id(export_id: str) -> Optional[PerformanceReportExportResponse]:
        """Get a performance export by ID."""
        export_info = ReportsService._export_files.get(export_id)
        if not export_info:
            return None
        
        # Check if export has expired
        if datetime.now(timezone.utc) > export_info['expires_at']:
            return None
        
        # Reconstruct response
        return PerformanceReportExportResponse(
            export_id=export_id,
            filename=os.path.basename(export_info['file_path']),
            format=ReportFormat.JSON,  # This would need to be stored
            download_url=f"/exports/{os.path.basename(export_info['file_path'])}",
            file_size=os.path.getsize(export_info['file_path']) if os.path.exists(export_info['file_path']) else None,
            expires_at=export_info['expires_at'],
            metadata={"report_id": export_info['report_id']}
        ) 