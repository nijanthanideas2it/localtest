"""
Task service layer for task management operations.
"""
from datetime import date, datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, case
from decimal import Decimal
from uuid import UUID

from app.models.task import Task, TaskDependency
from app.models.project import Project
from app.models.user import User
from app.schemas.task import (
    TaskCreateRequest,
    TaskUpdateRequest,
    TaskDependencyRequest
)


class TaskService:
    """Service class for task management operations."""
    
    @staticmethod
    def create_task(
        db: Session,
        project_id: str,
        task_data: TaskCreateRequest,
        current_user_id: str
    ) -> Optional[Task]:
        """
        Create a new task.
        
        Args:
            db: Database session
            project_id: Project ID
            task_data: Task creation data
            current_user_id: ID of the user creating the task
            
        Returns:
            Created task or None if creation fails
        """
        try:
            # Validate project exists
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ValueError("Project not found")
            
            # Validate assignee exists if provided
            if task_data.assignee_id:
                assignee = db.query(User).filter(User.id == task_data.assignee_id).first()
                if not assignee:
                    raise ValueError("Assignee not found")
            
            # Create task
            task = Task(
                title=task_data.title,
                description=task_data.description,
                project_id=project_id,
                assignee_id=task_data.assignee_id,
                priority=task_data.priority,
                estimated_hours=task_data.estimated_hours or Decimal('0.00'),
                due_date=task_data.due_date,
                status='ToDo'
            )
            
            db.add(task)
            db.flush()  # Get the task ID
            
            # Add dependencies if provided
            if task_data.dependencies:
                for dependency_id in task_data.dependencies:
                    # Validate dependency task exists and belongs to same project
                    dependency_task = db.query(Task).filter(
                        and_(
                            Task.id == dependency_id,
                            Task.project_id == project_id
                        )
                    ).first()
                    
                    if not dependency_task:
                        raise ValueError(f"Dependency task {dependency_id} not found")
                    
                    # Check for circular dependencies
                    if TaskService._would_create_circular_dependency(
                        db, task.id, dependency_id
                    ):
                        raise ValueError(f"Circular dependency detected with task {dependency_id}")
                    
                    # Create dependency
                    dependency = TaskDependency(
                        dependent_task_id=task.id,
                        prerequisite_task_id=dependency_id,
                        dependency_type='Blocks'
                    )
                    db.add(dependency)
            
            db.commit()
            db.refresh(task)
            return task
            
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def get_task_by_id(db: Session, task_id: str) -> Optional[Task]:
        """
        Get task by ID with all related data.
        
        Args:
            db: Database session
            task_id: Task ID
            
        Returns:
            Task or None if not found
        """
        return db.query(Task).options(
            joinedload(Task.assignee),
            joinedload(Task.project),
            joinedload(Task.dependent_tasks),
            joinedload(Task.prerequisite_tasks),
            joinedload(Task.time_entries)
        ).filter(Task.id == task_id).first()
    
    @staticmethod
    def get_project_tasks(
        db: Session,
        project_id: str,
        status: Optional[str] = None,
        assignee_id: Optional[str] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Task]:
        """
        Get all tasks for a project with optional filtering.
        
        Args:
            db: Database session
            project_id: Project ID
            status: Optional filter by status
            assignee_id: Optional filter by assignee
            priority: Optional filter by priority
            search: Optional search by title
            
        Returns:
            List of tasks
        """
        query = db.query(Task).options(
            joinedload(Task.assignee),
            joinedload(Task.dependent_tasks)
        ).filter(Task.project_id == project_id)
        
        if status:
            query = query.filter(Task.status == status)
        
        if assignee_id:
            query = query.filter(Task.assignee_id == assignee_id)
        
        if priority:
            query = query.filter(Task.priority == priority)
        
        if search:
            query = query.filter(Task.title.ilike(f"%{search}%"))
        
        return query.order_by(Task.created_at.desc()).all()
    
    @staticmethod
    def update_task(
        db: Session,
        task_id: str,
        update_data: TaskUpdateRequest
    ) -> Optional[Task]:
        """
        Update task details.
        
        Args:
            db: Database session
            task_id: Task ID
            update_data: Update data
            
        Returns:
            Updated task or None if not found
        """
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return None
        
        # Validate assignee exists if provided
        if update_data.assignee_id:
            assignee = db.query(User).filter(User.id == update_data.assignee_id).first()
            if not assignee:
                raise ValueError("Assignee not found")
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(task, field, value)
        
        # Handle status changes
        if update_data.status is not None:
            if update_data.status == 'InProgress' and task.status == 'ToDo':
                # Starting the task
                task.started_at = datetime.now(timezone.utc)
            elif update_data.status == 'Done' and task.status != 'Done':
                # Completing the task
                task.completed_at = datetime.now(timezone.utc)
            elif update_data.status != 'Done' and task.status == 'Done':
                # Reopening the task
                task.completed_at = None
        
        task.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(task)
        return task
    
    @staticmethod
    def delete_task(db: Session, task_id: str) -> bool:
        """
        Delete task.
        
        Args:
            db: Database session
            task_id: Task ID
            
        Returns:
            True if deleted, False if not found
        """
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return False
        
        db.delete(task)
        db.commit()
        return True
    
    @staticmethod
    def get_task_dependencies(db: Session, task_id: str) -> List[TaskDependency]:
        """
        Get all dependencies for a task.
        
        Args:
            db: Database session
            task_id: Task ID
            
        Returns:
            List of task dependencies
        """
        return db.query(TaskDependency).filter(
            TaskDependency.dependent_task_id == task_id
        ).all()
    
    @staticmethod
    def add_task_dependency(
        db: Session,
        task_id: str,
        dependency_data: TaskDependencyRequest
    ) -> Optional[TaskDependency]:
        """
        Add dependency to task.
        
        Args:
            db: Database session
            task_id: Task ID
            dependency_data: Dependency data
            
        Returns:
            Created dependency or None if creation fails
        """
        try:
            # Validate both tasks exist and belong to same project
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                raise ValueError("Task not found")
            
            prerequisite_task = db.query(Task).filter(
                Task.id == dependency_data.prerequisite_task_id
            ).first()
            if not prerequisite_task:
                raise ValueError("Prerequisite task not found")
            
            if task.project_id != prerequisite_task.project_id:
                raise ValueError("Tasks must belong to the same project")
            
            # Check for circular dependencies
            if TaskService._would_create_circular_dependency(
                db, task_id, dependency_data.prerequisite_task_id
            ):
                raise ValueError("Circular dependency detected")
            
            # Check if dependency already exists
            existing_dependency = db.query(TaskDependency).filter(
                and_(
                    TaskDependency.dependent_task_id == task_id,
                    TaskDependency.prerequisite_task_id == dependency_data.prerequisite_task_id
                )
            ).first()
            
            if existing_dependency:
                raise ValueError("Dependency already exists")
            
            # Create dependency
            dependency = TaskDependency(
                dependent_task_id=task_id,
                prerequisite_task_id=dependency_data.prerequisite_task_id,
                dependency_type=dependency_data.dependency_type
            )
            
            db.add(dependency)
            db.commit()
            db.refresh(dependency)
            return dependency
            
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def remove_task_dependency(
        db: Session,
        task_id: str,
        prerequisite_task_id: str
    ) -> bool:
        """
        Remove dependency from task.
        
        Args:
            db: Database session
            task_id: Task ID
            prerequisite_task_id: Prerequisite task ID
            
        Returns:
            True if removed, False if not found
        """
        dependency = db.query(TaskDependency).filter(
            and_(
                TaskDependency.dependent_task_id == task_id,
                TaskDependency.prerequisite_task_id == prerequisite_task_id
            )
        ).first()
        
        if not dependency:
            return False
        
        db.delete(dependency)
        db.commit()
        return True
    
    @staticmethod
    def get_task_statistics(db: Session, project_id: str) -> Dict[str, Any]:
        """
        Get task statistics for a project.
        
        Args:
            db: Database session
            project_id: Project ID
            
        Returns:
            Dictionary with task statistics
        """
        from datetime import date
        
        # Get all tasks for the project
        tasks = db.query(Task).filter(Task.project_id == project_id).all()
        
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == 'Done'])
        in_progress_tasks = len([t for t in tasks if t.status == 'InProgress'])
        todo_tasks = len([t for t in tasks if t.status == 'ToDo'])
        overdue_tasks = len([t for t in tasks if t.due_date and t.due_date < date.today() and t.status != 'Done'])
        
        completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Calculate average completion time for completed tasks
        average_completion_time_hours = None
        if completed_tasks > 0:
            total_completion_time = 0
            for task in tasks:
                if task.status == 'Done' and task.started_at and task.completed_at:
                    completion_time = (task.completed_at - task.started_at).total_seconds() / 3600
                    total_completion_time += completion_time
            
            if total_completion_time > 0:
                average_completion_time_hours = total_completion_time / completed_tasks
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "todo_tasks": todo_tasks,
            "overdue_tasks": overdue_tasks,
            "completion_percentage": completion_percentage,
            "average_completion_time_hours": average_completion_time_hours
        }
    
    @staticmethod
    def _would_create_circular_dependency(
        db: Session,
        dependent_task_id: str,
        prerequisite_task_id: str
    ) -> bool:
        """
        Check if adding a dependency would create a circular dependency.
        
        Args:
            db: Database session
            dependent_task_id: Dependent task ID
            prerequisite_task_id: Prerequisite task ID
            
        Returns:
            True if circular dependency would be created
        """
        # Simple check: if prerequisite depends on dependent, it would create a circle
        existing_dependency = db.query(TaskDependency).filter(
            and_(
                TaskDependency.dependent_task_id == prerequisite_task_id,
                TaskDependency.prerequisite_task_id == dependent_task_id
            )
        ).first()
        
        return existing_dependency is not None
    
    @staticmethod
    def can_access_task(
        task: Task,
        current_user_id: str,
        current_user_role: str
    ) -> bool:
        """
        Check if user can access task.
        
        Args:
            task: Task object
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
    def can_manage_task(
        task: Task,
        current_user_id: str,
        current_user_role: str
    ) -> bool:
        """
        Check if user can manage task.
        
        Args:
            task: Task object
            current_user_id: Current user ID
            current_user_role: Current user role
            
        Returns:
            True if user can manage, False otherwise
        """
        # Task assignee can manage their own tasks
        if task.assignee_id and str(task.assignee_id) == current_user_id:
            return True
        
        # Admins and project managers can manage any task
        if current_user_role in ["Admin", "ProjectManager"]:
            return True
        
        return False
    
    @staticmethod
    def assign_task(
        db: Session,
        task_id: str,
        assignee_id: str
    ) -> Optional[Task]:
        """
        Assign task to a user.
        
        Args:
            db: Database session
            task_id: Task ID
            assignee_id: User ID to assign the task to
            
        Returns:
            Updated task or None if not found
        """
        # Get task
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return None
        
        # Validate assignee exists
        assignee = db.query(User).filter(User.id == assignee_id).first()
        if not assignee:
            raise ValueError("Assignee not found")
        
        # Update task assignment
        task.assignee_id = assignee_id
        task.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(task)
        return task
    
    @staticmethod
    def update_task_status(
        db: Session,
        task_id: str,
        new_status: str
    ) -> Optional[Task]:
        """
        Update task status.
        
        Args:
            db: Database session
            task_id: Task ID
            new_status: New status for the task
            
        Returns:
            Updated task or None if not found
        """
        # Get task
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return None
        
        # Validate status
        valid_statuses = ['ToDo', 'InProgress', 'Review', 'Done']
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        # Handle status transitions
        if new_status == 'InProgress' and task.status == 'ToDo':
            # Starting the task
            task.started_at = datetime.now(timezone.utc)
        elif new_status == 'Done' and task.status != 'Done':
            # Completing the task
            task.completed_at = datetime.now(timezone.utc)
        elif new_status != 'Done' and task.status == 'Done':
            # Reopening the task
            task.completed_at = None
        
        # Update status
        task.status = new_status
        task.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(task)
        return task
    
    @staticmethod
    def get_assigned_tasks(
        db: Session,
        user_id: str,
        status: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> List[Task]:
        """
        Get tasks assigned to a user.
        
        Args:
            db: Database session
            user_id: User ID
            status: Optional filter by status
            project_id: Optional filter by project
            
        Returns:
            List of assigned tasks
        """
        query = db.query(Task).options(
            joinedload(Task.project),
            joinedload(Task.dependent_tasks)
        ).filter(Task.assignee_id == user_id)
        
        if status:
            query = query.filter(Task.status == status)
        
        if project_id:
            query = query.filter(Task.project_id == project_id)
        
        return query.order_by(Task.created_at.desc()).all()
    
    @staticmethod
    def get_tasks_by_status(
        db: Session,
        status: str,
        project_id: Optional[str] = None,
        assignee_id: Optional[str] = None
    ) -> List[Task]:
        """
        Get tasks filtered by status.
        
        Args:
            db: Database session
            status: Task status to filter by
            project_id: Optional filter by project
            assignee_id: Optional filter by assignee
            
        Returns:
            List of tasks with the specified status
        """
        # Validate status
        valid_statuses = ['ToDo', 'InProgress', 'Review', 'Done']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        query = db.query(Task).options(
            joinedload(Task.assignee),
            joinedload(Task.project),
            joinedload(Task.dependent_tasks)
        ).filter(Task.status == status)
        
        if project_id:
            query = query.filter(Task.project_id == project_id)
        
        if assignee_id:
            query = query.filter(Task.assignee_id == assignee_id)
        
        return query.order_by(Task.created_at.desc()).all()
    
    @staticmethod
    def search_tasks(
        db: Session,
        query: str,
        project_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Task]:
        """
        Search tasks by text query.
        
        Args:
            db: Database session
            query: Search query
            project_id: Optional limit to specific project
            limit: Maximum number of results
            
        Returns:
            List of matching tasks
        """
        search_query = db.query(Task).options(
            joinedload(Task.assignee),
            joinedload(Task.project),
            joinedload(Task.dependent_tasks)
        ).filter(
            or_(
                Task.title.ilike(f"%{query}%"),
                Task.description.ilike(f"%{query}%")
            )
        )
        
        if project_id:
            search_query = search_query.filter(Task.project_id == project_id)
        
        return search_query.order_by(Task.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def filter_tasks(
        db: Session,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assignee_id: Optional[str] = None,
        project_id: Optional[str] = None,
        due_date_from: Optional[date] = None,
        due_date_to: Optional[date] = None,
        created_date_from: Optional[date] = None,
        created_date_to: Optional[date] = None,
        has_dependencies: Optional[bool] = None,
        is_overdue: Optional[bool] = None,
        limit: int = 20
    ) -> List[Task]:
        """
        Filter tasks by various criteria.
        
        Args:
            db: Database session
            status: Filter by task status
            priority: Filter by task priority
            assignee_id: Filter by assignee
            project_id: Filter by project
            due_date_from: Filter by due date from
            due_date_to: Filter by due date to
            created_date_from: Filter by creation date from
            created_date_to: Filter by creation date to
            has_dependencies: Filter by tasks with/without dependencies
            is_overdue: Filter by overdue tasks
            limit: Maximum number of results
            
        Returns:
            List of filtered tasks
        """
        from datetime import date
        
        query = db.query(Task).options(
            joinedload(Task.assignee),
            joinedload(Task.project),
            joinedload(Task.dependent_tasks)
        )
        
        # Apply filters
        if status:
            query = query.filter(Task.status == status)
        
        if priority:
            query = query.filter(Task.priority == priority)
        
        if assignee_id:
            query = query.filter(Task.assignee_id == assignee_id)
        
        if project_id:
            query = query.filter(Task.project_id == project_id)
        
        if due_date_from:
            query = query.filter(Task.due_date >= due_date_from)
        
        if due_date_to:
            query = query.filter(Task.due_date <= due_date_to)
        
        if created_date_from:
            query = query.filter(func.date(Task.created_at) >= created_date_from)
        
        if created_date_to:
            query = query.filter(func.date(Task.created_at) <= created_date_to)
        
        if has_dependencies is not None:
            if has_dependencies:
                # Tasks with dependencies
                query = query.filter(Task.dependent_tasks.any())
            else:
                # Tasks without dependencies
                query = query.filter(~Task.dependent_tasks.any())
        
        if is_overdue is not None:
            today = date.today()
            if is_overdue:
                # Overdue tasks (due date in past and not completed)
                query = query.filter(
                    and_(
                        Task.due_date < today,
                        Task.status != 'Done'
                    )
                )
            else:
                # Not overdue tasks (due date in future or completed)
                query = query.filter(
                    or_(
                        Task.due_date >= today,
                        Task.status == 'Done'
                    )
                )
        
        return query.order_by(Task.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def sort_tasks(
        db: Session,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 20
    ) -> List[Task]:
        """
        Sort tasks by specified field.
        
        Args:
            db: Database session
            sort_by: Field to sort by
            sort_order: Sort order (asc or desc)
            limit: Maximum number of results
            
        Returns:
            List of sorted tasks
        """
        query = db.query(Task).options(
            joinedload(Task.assignee),
            joinedload(Task.project),
            joinedload(Task.dependent_tasks)
        )
        
        # Apply sorting
        if sort_by == "title":
            sort_field = Task.title
        elif sort_by == "status":
            sort_field = Task.status
        elif sort_by == "priority":
            sort_field = Task.priority
        elif sort_by == "due_date":
            sort_field = Task.due_date
        elif sort_by == "created_at":
            sort_field = Task.created_at
        elif sort_by == "updated_at":
            sort_field = Task.updated_at
        elif sort_by == "estimated_hours":
            sort_field = Task.estimated_hours
        else:
            sort_field = Task.created_at
        
        if sort_order == "asc":
            query = query.order_by(sort_field.asc())
        else:
            query = query.order_by(sort_field.desc())
        
        return query.limit(limit).all()