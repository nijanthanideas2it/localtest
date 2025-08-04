"""
Project service layer for project management operations.
"""
from datetime import date, datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from uuid import UUID

from app.models.project import Project, ProjectTeamMember
from app.models.user import User
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectQueryParams,
    TeamMemberRequest
)
from app.core.auth import AuthUtils


class ProjectService:
    """Service class for project management operations."""
    
    @staticmethod
    def create_project(
        db: Session,
        project_data: ProjectCreateRequest,
        current_user_id: str
    ) -> Optional[Project]:
        """
        Create a new project.
        
        Args:
            db: Database session
            project_data: Project creation data
            current_user_id: ID of the user creating the project
            
        Returns:
            Created project or None if creation fails
        """
        try:
            # Validate manager exists
            manager = db.query(User).filter(User.id == project_data.manager_id).first()
            if not manager:
                raise ValueError("Manager not found")
            
            # Create project
            project = Project(
                name=project_data.name,
                description=project_data.description,
                start_date=project_data.start_date,
                end_date=project_data.end_date,
                budget=project_data.budget or Decimal('0.00'),
                manager_id=project_data.manager_id,
                status='Draft'
            )
            
            db.add(project)
            db.flush()  # Get the project ID
            
            # Add team members if provided
            if project_data.team_members:
                for member_data in project_data.team_members:
                    # Validate user exists
                    user = db.query(User).filter(User.id == member_data.user_id).first()
                    if not user:
                        raise ValueError(f"User {member_data.user_id} not found")
                    
                    # Check if user is already a team member
                    existing_member = db.query(ProjectTeamMember).filter(
                        and_(
                            ProjectTeamMember.project_id == project.id,
                            ProjectTeamMember.user_id == member_data.user_id,
                            ProjectTeamMember.left_at.is_(None)
                        )
                    ).first()
                    
                    if existing_member:
                        raise ValueError(f"User {member_data.user_id} is already a team member")
                    
                    team_member = ProjectTeamMember(
                        project_id=project.id,
                        user_id=member_data.user_id,
                        role=member_data.role
                    )
                    db.add(team_member)
            
            # Add manager as team member if not already included
            manager_member = db.query(ProjectTeamMember).filter(
                and_(
                    ProjectTeamMember.project_id == project.id,
                    ProjectTeamMember.user_id == project_data.manager_id,
                    ProjectTeamMember.left_at.is_(None)
                )
            ).first()
            
            if not manager_member:
                manager_member = ProjectTeamMember(
                    project_id=project.id,
                    user_id=project_data.manager_id,
                    role="Project Manager"
                )
                db.add(manager_member)
            
            db.commit()
            db.refresh(project)
            return project
            
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def get_project_by_id(db: Session, project_id: str) -> Optional[Project]:
        """
        Get project by ID with team members.
        
        Args:
            db: Database session
            project_id: Project ID
            
        Returns:
            Project or None if not found
        """
        return db.query(Project).options(
            joinedload(Project.manager),
            joinedload(Project.team_members).joinedload(ProjectTeamMember.user)
        ).filter(Project.id == project_id).first()
    
    @staticmethod
    def get_projects_with_pagination(
        db: Session,
        query_params: ProjectQueryParams,
        current_user_id: str,
        current_user_role: str
    ) -> Tuple[List[Project], int]:
        """
        Get paginated list of projects with filtering.
        
        Args:
            db: Database session
            query_params: Query parameters for filtering and pagination
            current_user_id: Current user ID
            current_user_role: Current user role
            
        Returns:
            Tuple of (projects, total_count)
        """
        query = db.query(Project).options(
            joinedload(Project.manager),
            joinedload(Project.team_members).joinedload(ProjectTeamMember.user)
        )
        
        # Apply filters
        if query_params.status:
            query = query.filter(Project.status == query_params.status)
        
        if query_params.manager_id:
            query = query.filter(Project.manager_id == query_params.manager_id)
        
        if query_params.search:
            search_term = f"%{query_params.search}%"
            query = query.filter(
                or_(
                    Project.name.ilike(search_term),
                    Project.description.ilike(search_term)
                )
            )
        
        # Filter by user's projects if requested
        if query_params.my_projects:
            if current_user_role in ["Admin", "ProjectManager"]:
                # Admins and Project Managers can see projects they manage
                query = query.filter(Project.manager_id == current_user_id)
            else:
                # Other users can see projects they're team members of
                query = query.join(ProjectTeamMember).filter(
                    and_(
                        ProjectTeamMember.user_id == current_user_id,
                        ProjectTeamMember.left_at.is_(None)
                    )
                )
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        offset = (query_params.page - 1) * query_params.limit
        projects = query.offset(offset).limit(query_params.limit).all()
        
        return projects, total_count
    
    @staticmethod
    def update_project(
        db: Session,
        project_id: str,
        update_data: ProjectUpdateRequest
    ) -> Optional[Project]:
        """
        Update project details.
        
        Args:
            db: Database session
            project_id: Project ID
            update_data: Update data
            
        Returns:
            Updated project or None if not found
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(project, field, value)
        
        project.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(project)
        return project
    
    @staticmethod
    def delete_project(db: Session, project_id: str) -> bool:
        """
        Delete project.
        
        Args:
            db: Database session
            project_id: Project ID
            
        Returns:
            True if deleted, False if not found
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False
        
        db.delete(project)
        db.commit()
        return True
    
    @staticmethod
    def add_team_member(
        db: Session,
        project_id: str,
        user_id: str,
        role: str
    ) -> Optional[ProjectTeamMember]:
        """
        Add team member to project.
        
        Args:
            db: Database session
            project_id: Project ID
            user_id: User ID
            role: Role in the project
            
        Returns:
            Team member or None if addition fails
        """
        # Check if project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError("Project not found")
        
        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Check if user is already a team member
        existing_member = db.query(ProjectTeamMember).filter(
            and_(
                ProjectTeamMember.project_id == project_id,
                ProjectTeamMember.user_id == user_id,
                ProjectTeamMember.left_at.is_(None)
            )
        ).first()
        
        if existing_member:
            raise ValueError("User is already a team member")
        
        # Add team member
        team_member = ProjectTeamMember(
            project_id=project_id,
            user_id=user_id,
            role=role
        )
        
        db.add(team_member)
        db.commit()
        db.refresh(team_member)
        return team_member
    
    @staticmethod
    def remove_team_member(
        db: Session,
        project_id: str,
        user_id: str
    ) -> bool:
        """
        Remove team member from project.
        
        Args:
            db: Database session
            project_id: Project ID
            user_id: User ID
            
        Returns:
            True if removed, False if not found
        """
        team_member = db.query(ProjectTeamMember).filter(
            and_(
                ProjectTeamMember.project_id == project_id,
                ProjectTeamMember.user_id == user_id,
                ProjectTeamMember.left_at.is_(None)
            )
        ).first()
        
        if not team_member:
            return False
        
        # Mark as left instead of deleting
        team_member.left_at = datetime.now(timezone.utc)
        db.commit()
        return True
    
    @staticmethod
    def calculate_pagination_info(
        total_count: int,
        page: int,
        limit: int
    ) -> Dict[str, Any]:
        """
        Calculate pagination information.
        
        Args:
            total_count: Total number of items
            page: Current page number
            limit: Items per page
            
        Returns:
            Pagination information dictionary
        """
        total_pages = (total_count + limit - 1) // limit
        
        return {
            "page": page,
            "limit": limit,
            "total": total_count,
            "pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    
    @staticmethod
    def can_access_project(
        project: Project,
        current_user_id: str,
        current_user_role: str
    ) -> bool:
        """
        Check if user can access project.
        
        Args:
            project: Project object
            current_user_id: Current user ID
            current_user_role: Current user role
            
        Returns:
            True if user can access, False otherwise
        """
        # Admins can access all projects
        if current_user_role == "Admin":
            return True
        
        # Project managers can access all projects
        if current_user_role == "ProjectManager":
            return True
        
        # Check if user is a team member
        team_member = next(
            (member for member in project.team_members if str(member.user_id) == current_user_id and member.left_at is None),
            None
        )
        
        return team_member is not None
    
    @staticmethod
    def can_manage_project(
        project: Project,
        current_user_id: str,
        current_user_role: str
    ) -> bool:
        """
        Check if user can manage project.
        
        Args:
            project: Project object
            current_user_id: Current user ID
            current_user_role: Current user role
            
        Returns:
            True if user can manage, False otherwise
        """
        # Project managers can manage all projects (they are like admins)
        if current_user_role == "ProjectManager":
            return True
        
        # Project managers can manage projects they manage
        if current_user_role == "ProjectManager" and str(project.manager_id) == current_user_id:
            return True
        
        return False
    
    @staticmethod
    def get_project_team_members(db: Session, project_id: str) -> List[ProjectTeamMember]:
        """
        Get all team members for a project.
        
        Args:
            db: Database session
            project_id: Project ID
            
        Returns:
            List of team members
        """
        return db.query(ProjectTeamMember).options(
            joinedload(ProjectTeamMember.user)
        ).filter(ProjectTeamMember.project_id == project_id).all()
    
    @staticmethod
    def get_project_team_member(
        db: Session,
        project_id: str,
        member_id: str
    ) -> Optional[ProjectTeamMember]:
        """
        Get specific team member by ID.
        
        Args:
            db: Database session
            project_id: Project ID
            member_id: Team member ID
            
        Returns:
            Team member or None if not found
        """
        return db.query(ProjectTeamMember).options(
            joinedload(ProjectTeamMember.user)
        ).filter(
            and_(
                ProjectTeamMember.project_id == project_id,
                ProjectTeamMember.id == member_id
            )
        ).first()
    
    @staticmethod
    def update_team_member_role(
        db: Session,
        project_id: str,
        member_id: str,
        new_role: str
    ) -> Optional[ProjectTeamMember]:
        """
        Update team member role.
        
        Args:
            db: Database session
            project_id: Project ID
            member_id: Team member ID
            new_role: New role for the team member
            
        Returns:
            Updated team member or None if not found
        """
        team_member = ProjectService.get_project_team_member(db, project_id, member_id)
        
        if not team_member:
            return None
        
        team_member.role = new_role
        db.commit()
        db.refresh(team_member)
        return team_member
    
    @staticmethod
    def get_team_statistics(db: Session, project_id: str) -> Dict[str, Any]:
        """
        Get team statistics for a project.
        
        Args:
            db: Database session
            project_id: Project ID
            
        Returns:
            Dictionary with team statistics
        """
        from datetime import datetime, timezone
        
        # Get all team members
        team_members = ProjectService.get_project_team_members(db, project_id)
        
        total_members = len(team_members)
        active_members = len([m for m in team_members if m.left_at is None])
        inactive_members = total_members - active_members
        
        # Calculate roles distribution
        roles_distribution = {}
        for member in team_members:
            role = member.role
            roles_distribution[role] = roles_distribution.get(role, 0) + 1
        
        # Calculate average tenure for active members
        average_tenure_days = None
        if active_members > 0:
            total_tenure_days = 0
            current_time = datetime.now(timezone.utc)
            
            for member in team_members:
                if member.left_at is None:
                    tenure = (current_time - member.joined_at).days
                    total_tenure_days += tenure
            
            average_tenure_days = total_tenure_days / active_members
        
        return {
            "total_members": total_members,
            "active_members": active_members,
            "inactive_members": inactive_members,
            "roles_distribution": roles_distribution,
            "average_tenure_days": average_tenure_days
        } 