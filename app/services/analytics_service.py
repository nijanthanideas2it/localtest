"""
Analytics service layer for project analytics and reporting.
"""
from datetime import date, datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, case
from decimal import Decimal

from app.models.project import Project, ProjectTeamMember
from app.models.milestone import Milestone
from app.models.user import User
from app.schemas.analytics import (
    TaskSummaryResponse,
    TimeSummaryResponse,
    TeamPerformanceResponse,
    MilestoneProgressResponse,
    ProjectProgressResponse,
    ProjectAnalyticsResponse,
    TimelineEventResponse,
    ProjectTimelineResponse,
    DashboardSummaryResponse
)


class AnalyticsService:
    """Service class for project analytics and reporting."""
    
    @staticmethod
    def get_project_analytics(
        db: Session,
        project_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Optional[ProjectAnalyticsResponse]:
        """
        Get comprehensive project analytics.
        
        Args:
            db: Database session
            project_id: Project ID
            start_date: Optional start date for analytics period
            end_date: Optional end date for analytics period
            
        Returns:
            Project analytics data or None if project not found
        """
        # Get project with team members
        project = db.query(Project).options(
            joinedload(Project.team_members),
            joinedload(Project.milestones)
        ).filter(Project.id == project_id).first()
        
        if not project:
            return None
        
        # Calculate project progress
        project_progress = AnalyticsService._calculate_project_progress(project)
        
        # Calculate task summary (placeholder - would need Task model)
        task_summary = AnalyticsService._calculate_task_summary(db, project_id)
        
        # Calculate time summary (placeholder - would need TimeEntry model)
        time_summary = AnalyticsService._calculate_time_summary(db, project_id)
        
        # Calculate team performance
        team_performance = AnalyticsService._calculate_team_performance(db, project_id)
        
        # Calculate milestone progress
        milestones = AnalyticsService._calculate_milestone_progress(project.milestones)
        
        # Calculate budget utilization
        budget_utilization = AnalyticsService._calculate_budget_utilization(project)
        
        # Calculate risk score
        risk_score = AnalyticsService._calculate_risk_score(project, milestones)
        
        return ProjectAnalyticsResponse(
            project=project_progress,
            tasks_summary=task_summary,
            time_summary=time_summary,
            team_performance=team_performance,
            milestones=milestones,
            budget_utilization=budget_utilization,
            risk_score=risk_score
        )
    
    @staticmethod
    def get_project_timeline(
        db: Session,
        project_id: str
    ) -> Optional[ProjectTimelineResponse]:
        """
        Get project timeline with events and phases.
        
        Args:
            db: Database session
            project_id: Project ID
            
        Returns:
            Project timeline data or None if project not found
        """
        # Get project with milestones
        project = db.query(Project).options(
            joinedload(Project.milestones)
        ).filter(Project.id == project_id).first()
        
        if not project:
            return None
        
        # Get timeline events (milestones and other events)
        events = AnalyticsService._get_timeline_events(db, project)
        
        # Define project phases
        phases = AnalyticsService._get_project_phases(project)
        
        return ProjectTimelineResponse(
            project_id=project.id,
            project_name=project.name,
            start_date=project.start_date,
            end_date=project.end_date,
            events=events,
            phases=phases
        )
    
    @staticmethod
    def get_dashboard_summary(
        db: Session,
        user_id: str,
        user_role: str
    ) -> DashboardSummaryResponse:
        """
        Get dashboard summary for user.
        
        Args:
            db: Database session
            user_id: User ID
            user_role: User role
            
        Returns:
            Dashboard summary data
        """
        # Get projects based on user role
        if user_role == "Admin":
            projects = db.query(Project).all()
        elif user_role == "ProjectManager":
            projects = db.query(Project).filter(Project.manager_id == user_id).all()
        else:
            # Get projects where user is team member
            team_projects = db.query(Project).join(ProjectTeamMember).filter(
                ProjectTeamMember.user_id == user_id
            ).all()
            projects = team_projects
        
        # Calculate summary statistics
        total_projects = len(projects)
        active_projects = len([p for p in projects if p.status == "Active"])
        completed_projects = len([p for p in projects if p.status == "Completed"])
        overdue_projects = len([p for p in projects if p.end_date and p.end_date < date.today()])
        
        # Placeholder values for tasks and hours (would need Task and TimeEntry models)
        total_tasks = 0  # Would calculate from Task model
        completed_tasks = 0  # Would calculate from Task model
        total_hours_logged = 0.0  # Would calculate from TimeEntry model
        
        # Get team members count
        team_members = db.query(User).filter(User.is_active == True).count()
        
        # Get upcoming deadlines
        upcoming_deadlines = AnalyticsService._get_upcoming_deadlines(db, projects)
        
        return DashboardSummaryResponse(
            total_projects=total_projects,
            active_projects=active_projects,
            completed_projects=completed_projects,
            overdue_projects=overdue_projects,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            total_hours_logged=total_hours_logged,
            team_members=team_members,
            upcoming_deadlines=upcoming_deadlines
        )
    
    @staticmethod
    def _calculate_project_progress(project: Project) -> ProjectProgressResponse:
        """Calculate project progress metrics."""
        current_date = date.today()
        days_elapsed = (current_date - project.start_date).days
        
        days_remaining = None
        if project.end_date:
            days_remaining = (project.end_date - current_date).days
        
        # Calculate progress percentage based on milestones
        if project.milestones:
            completed_milestones = len([m for m in project.milestones if m.is_completed])
            progress_percentage = (completed_milestones / len(project.milestones)) * 100
        else:
            progress_percentage = 0.0
        
        return ProjectProgressResponse(
            id=project.id,
            name=project.name,
            status=project.status,
            progress_percentage=progress_percentage,
            start_date=project.start_date,
            end_date=project.end_date,
            days_elapsed=days_elapsed,
            days_remaining=days_remaining
        )
    
    @staticmethod
    def _calculate_task_summary(db: Session, project_id: str) -> TaskSummaryResponse:
        """Calculate task summary (placeholder implementation)."""
        # This would be implemented when Task model is available
        # For now, return placeholder data
        return TaskSummaryResponse(
            total=0,
            completed=0,
            in_progress=0,
            todo=0,
            overdue=0,
            completion_percentage=0.0
        )
    
    @staticmethod
    def _calculate_time_summary(db: Session, project_id: str) -> TimeSummaryResponse:
        """Calculate time summary (placeholder implementation)."""
        # This would be implemented when TimeEntry model is available
        # For now, return placeholder data
        return TimeSummaryResponse(
            total_estimated=0.0,
            total_actual=0.0,
            variance=0.0,
            variance_percentage=0.0
        )
    
    @staticmethod
    def _calculate_team_performance(
        db: Session,
        project_id: str
    ) -> List[TeamPerformanceResponse]:
        """Calculate team performance metrics."""
        # Get team members for the project
        team_members = db.query(ProjectTeamMember).filter(
            ProjectTeamMember.project_id == project_id
        ).all()
        
        performance_data = []
        for member in team_members:
            # Get user details
            user = db.query(User).filter(User.id == member.user_id).first()
            if not user:
                continue
            
            # Placeholder values (would calculate from Task and TimeEntry models)
            tasks_completed = 0  # Would calculate from Task model
            hours_logged = 0.0  # Would calculate from TimeEntry model
            efficiency_score = None  # Would calculate based on performance metrics
            
            performance_data.append(TeamPerformanceResponse(
                user_id=member.user_id,
                name=f"{user.first_name} {user.last_name}",
                tasks_completed=tasks_completed,
                hours_logged=hours_logged,
                efficiency_score=efficiency_score
            ))
        
        return performance_data
    
    @staticmethod
    def _calculate_milestone_progress(
        milestones: List[Milestone]
    ) -> List[MilestoneProgressResponse]:
        """Calculate milestone progress metrics."""
        progress_data = []
        current_date = date.today()
        
        for milestone in milestones:
            days_remaining = None
            if not milestone.is_completed and milestone.due_date:
                days_remaining = (milestone.due_date - current_date).days
            
            completion_percentage = 100.0 if milestone.is_completed else 0.0
            
            progress_data.append(MilestoneProgressResponse(
                id=milestone.id,
                name=milestone.name,
                due_date=milestone.due_date,
                is_completed=milestone.is_completed,
                completion_percentage=completion_percentage,
                days_remaining=days_remaining
            ))
        
        return progress_data
    
    @staticmethod
    def _calculate_budget_utilization(project: Project) -> Optional[float]:
        """Calculate budget utilization percentage."""
        if not project.budget or project.budget == 0:
            return None
        
        if not project.actual_cost:
            return 0.0
        
        utilization = (project.actual_cost / project.budget) * 100
        return float(utilization)
    
    @staticmethod
    def _calculate_risk_score(
        project: Project,
        milestones: List[MilestoneProgressResponse]
    ) -> Optional[float]:
        """Calculate project risk score."""
        risk_factors = 0
        total_factors = 0
        
        # Factor 1: Overdue milestones
        overdue_milestones = [m for m in milestones if m.days_remaining and m.days_remaining < 0]
        if milestones:
            risk_factors += len(overdue_milestones) / len(milestones)
            total_factors += 1
        
        # Factor 2: Project timeline
        if project.end_date:
            current_date = date.today()
            days_remaining = (project.end_date - current_date).days
            if days_remaining < 0:
                risk_factors += 1
            elif days_remaining < 30:
                risk_factors += 0.5
            total_factors += 1
        
        # Factor 3: Budget overrun
        if project.budget and project.actual_cost:
            if project.actual_cost > project.budget:
                risk_factors += 1
                total_factors += 1
        
        if total_factors == 0:
            return None
        
        risk_score = (risk_factors / total_factors) * 100
        return min(risk_score, 100.0)  # Cap at 100%
    
    @staticmethod
    def _get_timeline_events(
        db: Session,
        project: Project
    ) -> List[TimelineEventResponse]:
        """Get timeline events for project."""
        events = []
        
        # Add milestone events
        for milestone in project.milestones:
            events.append(TimelineEventResponse(
                id=milestone.id,
                type="milestone",
                title=milestone.name,
                description=milestone.description,
                date=milestone.due_date,
                status="completed" if milestone.is_completed else "pending",
                category="milestone"
            ))
        
        # Add project start and end events
        events.append(TimelineEventResponse(
            id=project.id,
            type="event",
            title="Project Start",
            description="Project officially started",
            date=project.start_date,
            status="completed",
            category="project"
        ))
        
        if project.end_date:
            events.append(TimelineEventResponse(
                id=project.id,
                type="event",
                title="Project End",
                description="Project scheduled to end",
                date=project.end_date,
                status="pending",
                category="project"
            ))
        
        # Sort events by date
        events.sort(key=lambda x: x.date)
        return events
    
    @staticmethod
    def _get_project_phases(project: Project) -> List[Dict[str, Any]]:
        """Get project phases."""
        phases = []
        
        if project.start_date and project.end_date:
            total_duration = (project.end_date - project.start_date).days
            
            # Define phases based on project duration
            if total_duration <= 30:
                # Short project: Planning, Execution, Closure
                phases = [
                    {"name": "Planning", "start": 0, "end": 20},
                    {"name": "Execution", "start": 20, "end": 80},
                    {"name": "Closure", "start": 80, "end": 100}
                ]
            else:
                # Longer project: Planning, Development, Testing, Deployment, Closure
                phases = [
                    {"name": "Planning", "start": 0, "end": 15},
                    {"name": "Development", "start": 15, "end": 60},
                    {"name": "Testing", "start": 60, "end": 80},
                    {"name": "Deployment", "start": 80, "end": 90},
                    {"name": "Closure", "start": 90, "end": 100}
                ]
        
        return phases
    
    @staticmethod
    def _get_upcoming_deadlines(
        db: Session,
        projects: List[Project]
    ) -> List[Dict[str, Any]]:
        """Get upcoming deadlines across projects."""
        deadlines = []
        current_date = date.today()
        
        for project in projects:
            # Project end date
            if project.end_date and project.end_date >= current_date:
                days_until = (project.end_date - current_date).days
                if days_until <= 30:  # Only show deadlines within 30 days
                    deadlines.append({
                        "type": "project_end",
                        "title": f"Project: {project.name}",
                        "date": project.end_date,
                        "days_until": days_until
                    })
            
            # Milestone deadlines
            for milestone in project.milestones:
                if not milestone.is_completed and milestone.due_date >= current_date:
                    days_until = (milestone.due_date - current_date).days
                    if days_until <= 30:  # Only show deadlines within 30 days
                        deadlines.append({
                            "type": "milestone",
                            "title": f"Milestone: {milestone.name}",
                            "date": milestone.due_date,
                            "days_until": days_until,
                            "project": project.name
                        })
        
        # Sort by date
        deadlines.sort(key=lambda x: x["date"])
        return deadlines[:10]  # Return top 10 upcoming deadlines 