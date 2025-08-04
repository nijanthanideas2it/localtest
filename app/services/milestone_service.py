"""
Milestone service layer for milestone management operations.
"""
from datetime import date, datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from uuid import UUID

from app.models.milestone import Milestone, MilestoneDependency
from app.models.project import Project
from app.schemas.milestone import (
    MilestoneCreateRequest,
    MilestoneUpdateRequest,
    MilestoneDependencyRequest
)


class MilestoneService:
    """Service class for milestone management operations."""
    
    @staticmethod
    def create_milestone(
        db: Session,
        project_id: str,
        milestone_data: MilestoneCreateRequest,
        current_user_id: str
    ) -> Optional[Milestone]:
        """
        Create a new milestone.
        
        Args:
            db: Database session
            project_id: Project ID
            milestone_data: Milestone creation data
            current_user_id: ID of the user creating the milestone
            
        Returns:
            Created milestone or None if creation fails
        """
        try:
            # Validate project exists
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ValueError("Project not found")
            
            # Create milestone
            milestone = Milestone(
                name=milestone_data.name,
                description=milestone_data.description,
                project_id=project_id,
                due_date=milestone_data.due_date,
                is_completed=False
            )
            
            db.add(milestone)
            db.flush()  # Get the milestone ID
            
            # Add dependencies if provided
            if milestone_data.dependencies:
                for dependency_id in milestone_data.dependencies:
                    # Validate dependency milestone exists and belongs to same project
                    dependency_milestone = db.query(Milestone).filter(
                        and_(
                            Milestone.id == dependency_id,
                            Milestone.project_id == project_id
                        )
                    ).first()
                    
                    if not dependency_milestone:
                        raise ValueError(f"Dependency milestone {dependency_id} not found")
                    
                    # Check for circular dependencies
                    if MilestoneService._would_create_circular_dependency(
                        db, milestone.id, dependency_id
                    ):
                        raise ValueError(f"Circular dependency detected with milestone {dependency_id}")
                    
                    # Create dependency
                    dependency = MilestoneDependency(
                        dependent_milestone_id=milestone.id,
                        prerequisite_milestone_id=dependency_id
                    )
                    db.add(dependency)
            
            db.commit()
            db.refresh(milestone)
            return milestone
            
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def get_milestone_by_id(db: Session, milestone_id: str) -> Optional[Milestone]:
        """
        Get milestone by ID with dependencies.
        
        Args:
            db: Database session
            milestone_id: Milestone ID
            
        Returns:
            Milestone or None if not found
        """
        return db.query(Milestone).options(
            joinedload(Milestone.dependent_milestones),
            joinedload(Milestone.prerequisite_milestones)
        ).filter(Milestone.id == milestone_id).first()
    
    @staticmethod
    def get_project_milestones(
        db: Session,
        project_id: str,
        is_completed: Optional[bool] = None
    ) -> List[Milestone]:
        """
        Get all milestones for a project with optional filtering.
        
        Args:
            db: Database session
            project_id: Project ID
            is_completed: Optional filter by completion status
            
        Returns:
            List of milestones
        """
        query = db.query(Milestone).options(
            joinedload(Milestone.dependent_milestones),
            joinedload(Milestone.prerequisite_milestones)
        ).filter(Milestone.project_id == project_id)
        
        if is_completed is not None:
            query = query.filter(Milestone.is_completed == is_completed)
        
        return query.order_by(Milestone.due_date).all()
    
    @staticmethod
    def update_milestone(
        db: Session,
        milestone_id: str,
        update_data: MilestoneUpdateRequest
    ) -> Optional[Milestone]:
        """
        Update milestone details.
        
        Args:
            db: Database session
            milestone_id: Milestone ID
            update_data: Update data
            
        Returns:
            Updated milestone or None if not found
        """
        milestone = db.query(Milestone).filter(Milestone.id == milestone_id).first()
        if not milestone:
            return None
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(milestone, field, value)
        
        # Handle completion status
        if update_data.is_completed is not None:
            if update_data.is_completed and not milestone.is_completed:
                # Marking as completed
                milestone.completed_at = datetime.now(timezone.utc)
            elif not update_data.is_completed and milestone.is_completed:
                # Marking as not completed
                milestone.completed_at = None
        
        milestone.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(milestone)
        return milestone
    
    @staticmethod
    def delete_milestone(db: Session, milestone_id: str) -> bool:
        """
        Delete milestone.
        
        Args:
            db: Database session
            milestone_id: Milestone ID
            
        Returns:
            True if deleted, False if not found
        """
        milestone = db.query(Milestone).filter(Milestone.id == milestone_id).first()
        if not milestone:
            return False
        
        db.delete(milestone)
        db.commit()
        return True
    
    @staticmethod
    def add_milestone_dependency(
        db: Session,
        milestone_id: str,
        dependency_data: MilestoneDependencyRequest
    ) -> Optional[MilestoneDependency]:
        """
        Add dependency to milestone.
        
        Args:
            db: Database session
            milestone_id: Milestone ID
            dependency_data: Dependency data
            
        Returns:
            Created dependency or None if creation fails
        """
        try:
            # Validate both milestones exist and belong to same project
            milestone = db.query(Milestone).filter(Milestone.id == milestone_id).first()
            if not milestone:
                raise ValueError("Milestone not found")
            
            prerequisite_milestone = db.query(Milestone).filter(
                Milestone.id == dependency_data.prerequisite_milestone_id
            ).first()
            if not prerequisite_milestone:
                raise ValueError("Prerequisite milestone not found")
            
            if milestone.project_id != prerequisite_milestone.project_id:
                raise ValueError("Milestones must belong to the same project")
            
            # Check for circular dependencies
            if MilestoneService._would_create_circular_dependency(
                db, milestone_id, dependency_data.prerequisite_milestone_id
            ):
                raise ValueError("Circular dependency detected")
            
            # Check if dependency already exists
            existing_dependency = db.query(MilestoneDependency).filter(
                and_(
                    MilestoneDependency.dependent_milestone_id == milestone_id,
                    MilestoneDependency.prerequisite_milestone_id == dependency_data.prerequisite_milestone_id
                )
            ).first()
            
            if existing_dependency:
                raise ValueError("Dependency already exists")
            
            # Create dependency
            dependency = MilestoneDependency(
                dependent_milestone_id=milestone_id,
                prerequisite_milestone_id=dependency_data.prerequisite_milestone_id
            )
            
            db.add(dependency)
            db.commit()
            db.refresh(dependency)
            return dependency
            
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def remove_milestone_dependency(
        db: Session,
        milestone_id: str,
        prerequisite_milestone_id: str
    ) -> bool:
        """
        Remove dependency from milestone.
        
        Args:
            db: Database session
            milestone_id: Milestone ID
            prerequisite_milestone_id: Prerequisite milestone ID
            
        Returns:
            True if removed, False if not found
        """
        dependency = db.query(MilestoneDependency).filter(
            and_(
                MilestoneDependency.dependent_milestone_id == milestone_id,
                MilestoneDependency.prerequisite_milestone_id == prerequisite_milestone_id
            )
        ).first()
        
        if not dependency:
            return False
        
        db.delete(dependency)
        db.commit()
        return True
    
    @staticmethod
    def get_milestone_statistics(db: Session, project_id: str) -> Dict[str, Any]:
        """
        Get milestone statistics for a project.
        
        Args:
            db: Database session
            project_id: Project ID
            
        Returns:
            Dictionary with milestone statistics
        """
        from datetime import date
        
        # Get all milestones for the project
        milestones = db.query(Milestone).filter(Milestone.project_id == project_id).all()
        
        total_milestones = len(milestones)
        completed_milestones = len([m for m in milestones if m.is_completed])
        overdue_milestones = len([m for m in milestones if not m.is_completed and m.due_date < date.today()])
        upcoming_milestones = len([m for m in milestones if not m.is_completed and m.due_date >= date.today()])
        
        completion_percentage = (completed_milestones / total_milestones * 100) if total_milestones > 0 else 0
        
        # Calculate average completion time for completed milestones
        average_completion_time_days = None
        if completed_milestones > 0:
            total_completion_time = 0
            for milestone in milestones:
                if milestone.is_completed and milestone.completed_at:
                    completion_time = (milestone.completed_at.date() - milestone.created_at.date()).days
                    total_completion_time += completion_time
            
            average_completion_time_days = total_completion_time / completed_milestones
        
        return {
            "total_milestones": total_milestones,
            "completed_milestones": completed_milestones,
            "overdue_milestones": overdue_milestones,
            "upcoming_milestones": upcoming_milestones,
            "completion_percentage": completion_percentage,
            "average_completion_time_days": average_completion_time_days
        }
    
    @staticmethod
    def _would_create_circular_dependency(
        db: Session,
        dependent_milestone_id: str,
        prerequisite_milestone_id: str
    ) -> bool:
        """
        Check if adding a dependency would create a circular dependency.
        
        Args:
            db: Database session
            dependent_milestone_id: Dependent milestone ID
            prerequisite_milestone_id: Prerequisite milestone ID
            
        Returns:
            True if circular dependency would be created
        """
        # Simple check: if prerequisite depends on dependent, it would create a circle
        existing_dependency = db.query(MilestoneDependency).filter(
            and_(
                MilestoneDependency.dependent_milestone_id == prerequisite_milestone_id,
                MilestoneDependency.prerequisite_milestone_id == dependent_milestone_id
            )
        ).first()
        
        return existing_dependency is not None
    
    @staticmethod
    def can_access_milestone(
        milestone: Milestone,
        current_user_id: str,
        current_user_role: str
    ) -> bool:
        """
        Check if user can access milestone.
        
        Args:
            milestone: Milestone object
            current_user_id: Current user ID
            current_user_role: Current user role
            
        Returns:
            True if user can access, False otherwise
        """
        # This would typically check if user is part of the project team
        # For now, we'll use a simple check based on role
        if current_user_role in ["Admin", "ProjectManager"]:
            return True
        
        # TODO: Add project team membership check
        return True
    
    @staticmethod
    def can_manage_milestone(
        milestone: Milestone,
        current_user_id: str,
        current_user_role: str
    ) -> bool:
        """
        Check if user can manage milestone.
        
        Args:
            milestone: Milestone object
            current_user_id: Current user ID
            current_user_role: Current user role
            
        Returns:
            True if user can manage, False otherwise
        """
        # Only admins and project managers can manage milestones
        if current_user_role in ["Admin", "ProjectManager"]:
            return True
        
        return False 