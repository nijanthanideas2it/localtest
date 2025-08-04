"""
Unit tests for task service layer.
"""
import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from uuid import uuid4

from app.services.task_service import TaskService
from app.schemas.task import TaskCreateRequest, TaskUpdateRequest, TaskDependencyRequest, TaskAssignmentRequest, TaskStatusRequest, TaskSearchRequest, TaskFilterRequest, TaskSortRequest
from app.models.task import Task, TaskDependency
from app.models.project import Project
from app.models.user import User
from app.core.auth import AuthUtils


class TestTaskService:
    """Test cases for task service functionality."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return MagicMock()
    
    @pytest.fixture
    def sample_user(self):
        """Sample user object."""
        return User(
            id=uuid4(),
            email="test@example.com",
            password_hash=AuthUtils.get_password_hash("SecurePass123!"),
            first_name="Test",
            last_name="User",
            role="Project Manager",
            hourly_rate=50.0,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
    
    @pytest.fixture
    def sample_project(self, sample_user):
        """Sample project object."""
        return Project(
            id=uuid4(),
            name="Test Project",
            description="A test project",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            budget=Decimal('10000.00'),
            actual_cost=Decimal('5000.00'),
            status="Active",
            manager_id=sample_user.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    @pytest.fixture
    def sample_task(self, sample_project, sample_user):
        """Sample task object."""
        return Task(
            id=uuid4(),
            title="Test Task",
            description="A test task",
            project_id=sample_project.id,
            assignee_id=sample_user.id,
            status="ToDo",
            priority="Medium",
            estimated_hours=Decimal('8.00'),
            actual_hours=Decimal('0.00'),
            due_date=date(2025, 12, 31),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    @pytest.fixture
    def sample_task_data(self):
        """Sample task creation data."""
        return TaskCreateRequest(
            title="Test Task",
            description="A test task",
            priority="Medium",
            estimated_hours=Decimal('8.00'),
            due_date=date(2025, 12, 31),
            dependencies=[]
        )
    
    @pytest.fixture
    def sample_dependency_task(self, sample_project):
        """Sample dependency task object."""
        return Task(
            id=uuid4(),
            title="Dependency Task",
            description="A dependency task",
            project_id=sample_project.id,
            status="ToDo",
            priority="Medium",
            estimated_hours=Decimal('4.00'),
            actual_hours=Decimal('0.00'),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    @pytest.fixture
    def sample_task_dependency(self, sample_task, sample_dependency_task):
        """Sample task dependency object."""
        return TaskDependency(
            id=uuid4(),
            dependent_task_id=sample_task.id,
            prerequisite_task_id=sample_dependency_task.id,
            dependency_type="Blocks",
            created_at=datetime.now(timezone.utc)
        )
    
    def test_create_task_success(self, mock_db_session, sample_project, sample_user, sample_task_data):
        """Test successful task creation."""
        # Mock project query to return sample project
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_project
        
        result = TaskService.create_task(
            mock_db_session,
            str(sample_project.id),
            sample_task_data,
            "test-user-id"
        )
        
        assert result is not None
        assert result.title == "Test Task"
        assert str(result.project_id) == str(sample_project.id)
        assert result.status == "ToDo"
        
        # Verify database operations
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    def test_create_task_project_not_found(self, mock_db_session, sample_task_data):
        """Test task creation when project not found."""
        # Mock project query to return None
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="Project not found"):
            TaskService.create_task(
                mock_db_session,
                "non-existent-project",
                sample_task_data,
                "test-user-id"
            )
    
    def test_create_task_with_assignee(self, mock_db_session, sample_project, sample_user, sample_task_data):
        """Test task creation with assignee."""
        # Add assignee to task data
        sample_task_data.assignee_id = sample_user.id
        
        # Mock project and user queries
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = sample_project
        
        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.first.return_value = sample_user
        
        # Set up mock_db_session.query to return different mocks for different calls
        mock_db_session.query.side_effect = [mock_project_query, mock_user_query]
        
        result = TaskService.create_task(
            mock_db_session,
            str(sample_project.id),
            sample_task_data,
            "test-user-id"
        )
        
        assert result is not None
        assert result.assignee_id == sample_user.id
    
    def test_create_task_assignee_not_found(self, mock_db_session, sample_project, sample_task_data):
        """Test task creation with non-existent assignee."""
        # Add non-existent assignee to task data
        sample_task_data.assignee_id = uuid4()
        
        # Mock project query to return sample project
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = sample_project
        
        # Mock user query to return None
        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.first.return_value = None
        
        # Set up mock_db_session.query to return different mocks for different calls
        mock_db_session.query.side_effect = [mock_project_query, mock_user_query]
        
        with pytest.raises(ValueError, match="Assignee not found"):
            TaskService.create_task(
                mock_db_session,
                str(sample_project.id),
                sample_task_data,
                "test-user-id"
            )
    
    def test_create_task_with_dependencies(self, mock_db_session, sample_project, sample_dependency_task, sample_task_data):
        """Test task creation with dependencies."""
        # Add dependency to task data
        sample_task_data.dependencies = [sample_dependency_task.id]
        
        # Mock project query to return sample project
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = sample_project
        
        # Mock dependency task query to return sample dependency task
        mock_dependency_query = MagicMock()
        mock_dependency_query.filter.return_value.first.return_value = sample_dependency_task
        
        # Set up mock_db_session.query to return different mocks for different calls
        mock_db_session.query.side_effect = [mock_project_query, mock_dependency_query]
        
        result = TaskService.create_task(
            mock_db_session,
            str(sample_project.id),
            sample_task_data,
            "test-user-id"
        )
        
        assert result is not None
        # Verify dependency was added
        assert mock_db_session.add.call_count >= 2  # Task + dependency
    
    def test_create_task_dependency_not_found(self, mock_db_session, sample_project, sample_task_data):
        """Test task creation with non-existent dependency."""
        # Add non-existent dependency to task data
        sample_task_data.dependencies = [uuid4()]
        
        # Mock project query to return sample project
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = sample_project
        
        # Mock dependency task query to return None
        mock_dependency_query = MagicMock()
        mock_dependency_query.filter.return_value.first.return_value = None
        
        # Set up mock_db_session.query to return different mocks for different calls
        mock_db_session.query.side_effect = [mock_project_query, mock_dependency_query]
        
        with pytest.raises(ValueError, match="Dependency task .* not found"):
            TaskService.create_task(
                mock_db_session,
                str(sample_project.id),
                sample_task_data,
                "test-user-id"
            )
    
    def test_get_task_by_id_success(self, mock_db_session, sample_task):
        """Test successful task retrieval by ID."""
        mock_db_session.query.return_value.options.return_value.filter.return_value.first.return_value = sample_task
        
        result = TaskService.get_task_by_id(mock_db_session, str(sample_task.id))
        
        assert result == sample_task
        mock_db_session.query.assert_called_once()
    
    def test_get_task_by_id_not_found(self, mock_db_session):
        """Test task retrieval when task not found."""
        mock_db_session.query.return_value.options.return_value.filter.return_value.first.return_value = None
        
        result = TaskService.get_task_by_id(mock_db_session, "non-existent-id")
        
        assert result is None
    
    def test_get_project_tasks_no_filter(self, mock_db_session, sample_task):
        """Test project tasks retrieval with no filter."""
        # Mock tasks query
        mock_tasks = [sample_task]
        mock_db_session.query.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = mock_tasks
        
        result = TaskService.get_project_tasks(mock_db_session, "test-project-id")
        
        assert len(result) == 1
        assert result[0] == sample_task
        mock_db_session.query.assert_called_once()
    
    def test_get_project_tasks_with_filters(self, mock_db_session, sample_task):
        """Test project tasks retrieval with filters."""
        # Mock tasks query
        mock_tasks = [sample_task]
        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_tasks
        
        mock_db_session.query.return_value = mock_query
        
        result = TaskService.get_project_tasks(
            mock_db_session,
            "test-project-id",
            status="ToDo",
            assignee_id="test-assignee",
            priority="Medium",
            search="test"
        )
        
        assert len(result) == 1
        assert result[0] == sample_task
        mock_db_session.query.assert_called_once()
    
    def test_update_task_success(self, mock_db_session, sample_task):
        """Test successful task update."""
        # Mock task query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_task
        
        update_data = TaskUpdateRequest(
            title="Updated Task",
            status="InProgress"
        )
        
        result = TaskService.update_task(
            mock_db_session,
            str(sample_task.id),
            update_data
        )
        
        assert result == sample_task
        assert sample_task.title == "Updated Task"
        assert sample_task.status == "InProgress"
        assert sample_task.started_at is not None
        assert sample_task.updated_at is not None
        
        # Verify database operations
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    def test_update_task_not_found(self, mock_db_session):
        """Test task update when task not found."""
        # Mock task query to return None
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        update_data = TaskUpdateRequest(title="Updated Task")
        
        result = TaskService.update_task(
            mock_db_session,
            "non-existent-id",
            update_data
        )
        
        assert result is None
    
    def test_update_task_status_to_done(self, mock_db_session, sample_task):
        """Test task update to Done status."""
        # Mock task query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_task
        
        update_data = TaskUpdateRequest(status="Done")
        
        result = TaskService.update_task(
            mock_db_session,
            str(sample_task.id),
            update_data
        )
        
        assert result == sample_task
        assert sample_task.status == "Done"
        assert sample_task.completed_at is not None
    
    def test_update_task_status_from_done(self, mock_db_session, sample_task):
        """Test task update from Done status."""
        # Set task as completed
        sample_task.status = "Done"
        sample_task.completed_at = datetime.now(timezone.utc)
        
        # Mock task query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_task
        
        update_data = TaskUpdateRequest(status="InProgress")
        
        result = TaskService.update_task(
            mock_db_session,
            str(sample_task.id),
            update_data
        )
        
        assert result == sample_task
        assert sample_task.status == "InProgress"
        assert sample_task.completed_at is None
    
    def test_delete_task_success(self, mock_db_session, sample_task):
        """Test successful task deletion."""
        # Mock task query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_task
        
        result = TaskService.delete_task(mock_db_session, str(sample_task.id))
        
        assert result is True
        mock_db_session.delete.assert_called_once_with(sample_task)
        mock_db_session.commit.assert_called_once()
    
    def test_delete_task_not_found(self, mock_db_session):
        """Test task deletion when task not found."""
        # Mock task query to return None
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = TaskService.delete_task(mock_db_session, "non-existent-id")
        
        assert result is False
    
    def test_add_task_dependency_success(self, mock_db_session, sample_task, sample_dependency_task):
        """Test successful task dependency addition."""
        # Mock task queries
        mock_task_query = MagicMock()
        mock_task_query.filter.return_value.first.return_value = sample_task
        
        mock_prerequisite_query = MagicMock()
        mock_prerequisite_query.filter.return_value.first.return_value = sample_dependency_task
        
        # Mock dependency query to return no existing dependency
        mock_existing_dependency_query = MagicMock()
        mock_existing_dependency_query.filter.return_value.first.return_value = None
        
        # Set up mock_db_session.query to return different mocks for different calls
        mock_db_session.query.side_effect = [mock_task_query, mock_prerequisite_query, mock_existing_dependency_query]
        
        dependency_data = TaskDependencyRequest(prerequisite_task_id=sample_dependency_task.id)
        
        result = TaskService.add_task_dependency(
            mock_db_session,
            str(sample_task.id),
            dependency_data
        )
        
        assert result is not None
        assert result.dependent_task_id == sample_task.id
        assert result.prerequisite_task_id == sample_dependency_task.id
        
        # Verify database operations
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    def test_add_task_dependency_task_not_found(self, mock_db_session, sample_dependency_task):
        """Test task dependency addition when task not found."""
        # Mock task query to return None
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        dependency_data = TaskDependencyRequest(prerequisite_task_id=sample_dependency_task.id)
        
        with pytest.raises(ValueError, match="Task not found"):
            TaskService.add_task_dependency(
                mock_db_session,
                "non-existent-task",
                dependency_data
            )
    
    def test_add_task_dependency_prerequisite_not_found(self, mock_db_session, sample_task):
        """Test task dependency addition when prerequisite task not found."""
        # Mock task query to return sample task
        mock_task_query = MagicMock()
        mock_task_query.filter.return_value.first.return_value = sample_task
        
        # Mock prerequisite task query to return None
        mock_prerequisite_query = MagicMock()
        mock_prerequisite_query.filter.return_value.first.return_value = None
        
        # Set up mock_db_session.query to return different mocks for different calls
        mock_db_session.query.side_effect = [mock_task_query, mock_prerequisite_query]
        
        dependency_data = TaskDependencyRequest(prerequisite_task_id=uuid4())
        
        with pytest.raises(ValueError, match="Prerequisite task not found"):
            TaskService.add_task_dependency(
                mock_db_session,
                str(sample_task.id),
                dependency_data
            )
    
    def test_remove_task_dependency_success(self, mock_db_session, sample_task_dependency):
        """Test successful task dependency removal."""
        # Mock dependency query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_task_dependency
        
        result = TaskService.remove_task_dependency(
            mock_db_session,
            str(sample_task_dependency.dependent_task_id),
            str(sample_task_dependency.prerequisite_task_id)
        )
        
        assert result is True
        mock_db_session.delete.assert_called_once_with(sample_task_dependency)
        mock_db_session.commit.assert_called_once()
    
    def test_remove_task_dependency_not_found(self, mock_db_session):
        """Test task dependency removal when dependency not found."""
        # Mock dependency query to return None
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = TaskService.remove_task_dependency(
            mock_db_session,
            "test-dependent-id",
            "test-prerequisite-id"
        )
        
        assert result is False
    
    def test_get_task_statistics_success(self, mock_db_session, sample_task):
        """Test successful task statistics calculation."""
        # Create additional tasks for testing
        completed_task = Task(
            id=uuid4(),
            title="Completed Task",
            project_id=sample_task.project_id,
            status="Done",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc)
        )
        
        overdue_task = Task(
            id=uuid4(),
            title="Overdue Task",
            project_id=sample_task.project_id,
            status="ToDo",
            due_date=date(2023, 12, 31)
        )
        
        mock_tasks = [sample_task, completed_task, overdue_task]
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_tasks
        
        result = TaskService.get_task_statistics(mock_db_session, str(sample_task.project_id))
        
        assert result["total_tasks"] == 3
        assert result["completed_tasks"] == 1
        assert result["in_progress_tasks"] == 0
        assert result["todo_tasks"] == 2
        assert result["overdue_tasks"] == 1
        assert result["completion_percentage"] == pytest.approx(33.33, rel=1e-2)
        assert result["average_completion_time_hours"] is not None
    
    def test_get_task_statistics_empty_project(self, mock_db_session):
        """Test task statistics calculation for empty project."""
        # Mock empty tasks query
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        result = TaskService.get_task_statistics(mock_db_session, "test-project-id")
        
        assert result["total_tasks"] == 0
        assert result["completed_tasks"] == 0
        assert result["in_progress_tasks"] == 0
        assert result["todo_tasks"] == 0
        assert result["overdue_tasks"] == 0
        assert result["completion_percentage"] == 0
        assert result["average_completion_time_hours"] is None
    
    def test_can_access_task_admin(self, sample_task):
        """Test task access for admin user."""
        can_access = TaskService.can_access_task(
            sample_task,
            "admin-user-id",
            "Admin"
        )
        
        assert can_access is True
    
    def test_can_access_task_project_manager(self, sample_task):
        """Test task access for project manager user."""
        can_access = TaskService.can_access_task(
            sample_task,
            "manager-user-id",
            "Project Manager"
        )
        
        assert can_access is True
    
    def test_can_manage_task_assignee(self, sample_task):
        """Test task management for task assignee."""
        can_manage = TaskService.can_manage_task(
            sample_task,
            str(sample_task.assignee_id),
            "Developer"
        )
        
        assert can_manage is True
    
    def test_can_manage_task_admin(self, sample_task):
        """Test task management for admin user."""
        can_manage = TaskService.can_manage_task(
            sample_task,
            "admin-user-id",
            "Admin"
        )
        
        assert can_manage is True
    
    def test_can_manage_task_unauthorized(self, sample_task):
        """Test task management for unauthorized user."""
        can_manage = TaskService.can_manage_task(
            sample_task,
            "unauthorized-user-id",
            "Developer"
        )
        
        assert can_manage is False
    
    def test_get_task_dependencies_success(self, mock_db_session, sample_task_dependency):
        """Test successful task dependencies retrieval."""
        # Mock dependencies query
        mock_db_session.query.return_value.filter.return_value.all.return_value = [sample_task_dependency]
        
        result = TaskService.get_task_dependencies(mock_db_session, str(sample_task_dependency.dependent_task_id))
        
        assert len(result) == 1
        assert result[0] == sample_task_dependency
        mock_db_session.query.assert_called_once()
    
    def test_get_task_dependencies_empty(self, mock_db_session):
        """Test task dependencies retrieval when no dependencies exist."""
        # Mock empty dependencies query
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        result = TaskService.get_task_dependencies(mock_db_session, "test-task-id")
        
        assert len(result) == 0
        mock_db_session.query.assert_called_once()
    
    def test_add_task_dependency_duplicate(self, mock_db_session, sample_task, sample_dependency_task):
        """Test adding duplicate task dependency."""
        # Mock task queries
        mock_task_query = MagicMock()
        mock_task_query.filter.return_value.first.return_value = sample_task
        
        mock_prerequisite_query = MagicMock()
        mock_prerequisite_query.filter.return_value.first.return_value = sample_dependency_task
        
        # Mock circular dependency check to return False (no circular dependency)
        mock_circular_check = MagicMock()
        mock_circular_check.filter.return_value.first.return_value = None
        
        # Mock existing dependency query to return existing dependency
        mock_existing_dependency_query = MagicMock()
        mock_existing_dependency_query.filter.return_value.first.return_value = TaskDependency(
            id=uuid4(),
            dependent_task_id=sample_task.id,
            prerequisite_task_id=sample_dependency_task.id
        )
        
        # Set up mock_db_session.query to return different mocks for different calls
        mock_db_session.query.side_effect = [mock_task_query, mock_prerequisite_query, mock_circular_check, mock_existing_dependency_query]
        
        dependency_data = TaskDependencyRequest(prerequisite_task_id=sample_dependency_task.id)
        
        with pytest.raises(ValueError, match="Dependency already exists"):
            TaskService.add_task_dependency(
                mock_db_session,
                str(sample_task.id),
                dependency_data
            )
    
    def test_add_task_dependency_different_project(self, mock_db_session, sample_task):
        """Test adding task dependency from different project."""
        # Create task from different project
        different_project_task = Task(
            id=uuid4(),
            title="Different Project Task",
            project_id=uuid4(),  # Different project ID
            status="ToDo"
        )
        
        # Mock task queries
        mock_task_query = MagicMock()
        mock_task_query.filter.return_value.first.return_value = sample_task
        
        mock_prerequisite_query = MagicMock()
        mock_prerequisite_query.filter.return_value.first.return_value = different_project_task
        
        # Set up mock_db_session.query to return different mocks for different calls
        mock_db_session.query.side_effect = [mock_task_query, mock_prerequisite_query]
        
        dependency_data = TaskDependencyRequest(prerequisite_task_id=different_project_task.id)
        
        with pytest.raises(ValueError, match="Tasks must belong to the same project"):
            TaskService.add_task_dependency(
                mock_db_session,
                str(sample_task.id),
                dependency_data
            )
    
    def test_assign_task_success(self, mock_db_session, sample_task, sample_user):
        """Test successful task assignment."""
        # Mock task query
        mock_task_query = MagicMock()
        mock_task_query.filter.return_value.first.return_value = sample_task
        
        # Mock user query
        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.first.return_value = sample_user
        
        # Set up mock_db_session.query to return different mocks for different calls
        mock_db_session.query.side_effect = [mock_task_query, mock_user_query]
        
        result = TaskService.assign_task(
            mock_db_session,
            str(sample_task.id),
            str(sample_user.id)
        )
        
        assert result == sample_task
        assert str(sample_task.assignee_id) == str(sample_user.id)
        assert sample_task.updated_at is not None
        
        # Verify database operations
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    def test_assign_task_not_found(self, mock_db_session, sample_user):
        """Test task assignment when task not found."""
        # Mock task query to return None
        mock_task_query = MagicMock()
        mock_task_query.filter.return_value.first.return_value = None
        
        mock_db_session.query.return_value = mock_task_query
        
        result = TaskService.assign_task(
            mock_db_session,
            "non-existent-task",
            str(sample_user.id)
        )
        
        assert result is None
    
    def test_assign_task_assignee_not_found(self, mock_db_session, sample_task):
        """Test task assignment when assignee not found."""
        # Mock task query
        mock_task_query = MagicMock()
        mock_task_query.filter.return_value.first.return_value = sample_task
        
        # Mock user query to return None
        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.first.return_value = None
        
        # Set up mock_db_session.query to return different mocks for different calls
        mock_db_session.query.side_effect = [mock_task_query, mock_user_query]
        
        with pytest.raises(ValueError, match="Assignee not found"):
            TaskService.assign_task(
                mock_db_session,
                str(sample_task.id),
                "non-existent-user"
            )
    
    def test_update_task_status_success(self, mock_db_session, sample_task):
        """Test successful task status update."""
        # Mock task query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_task
        
        result = TaskService.update_task_status(
            mock_db_session,
            str(sample_task.id),
            "InProgress"
        )
        
        assert result == sample_task
        assert sample_task.status == "InProgress"
        assert sample_task.started_at is not None
        assert sample_task.updated_at is not None
        
        # Verify database operations
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    def test_update_task_status_to_done(self, mock_db_session, sample_task):
        """Test task status update to Done."""
        # Mock task query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_task
        
        result = TaskService.update_task_status(
            mock_db_session,
            str(sample_task.id),
            "Done"
        )
        
        assert result == sample_task
        assert sample_task.status == "Done"
        assert sample_task.completed_at is not None
    
    def test_update_task_status_from_done(self, mock_db_session, sample_task):
        """Test task status update from Done."""
        # Set task as completed
        sample_task.status = "Done"
        sample_task.completed_at = datetime.now(timezone.utc)
        
        # Mock task query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_task
        
        result = TaskService.update_task_status(
            mock_db_session,
            str(sample_task.id),
            "InProgress"
        )
        
        assert result == sample_task
        assert sample_task.status == "InProgress"
        assert sample_task.completed_at is None
    
    def test_update_task_status_invalid(self, mock_db_session, sample_task):
        """Test task status update with invalid status."""
        # Mock task query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_task
        
        with pytest.raises(ValueError, match="Invalid status"):
            TaskService.update_task_status(
                mock_db_session,
                str(sample_task.id),
                "InvalidStatus"
            )
    
    def test_update_task_status_not_found(self, mock_db_session):
        """Test task status update when task not found."""
        # Mock task query to return None
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = TaskService.update_task_status(
            mock_db_session,
            "non-existent-task",
            "InProgress"
        )
        
        assert result is None
    
    def test_get_assigned_tasks_success(self, mock_db_session, sample_task):
        """Test successful retrieval of assigned tasks."""
        # Mock tasks query
        mock_db_session.query.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = [sample_task]
        
        result = TaskService.get_assigned_tasks(
            mock_db_session,
            "test-user-id"
        )
        
        assert len(result) == 1
        assert result[0] == sample_task
        mock_db_session.query.assert_called_once()
    
    def test_get_assigned_tasks_with_filters(self, mock_db_session, sample_task):
        """Test retrieval of assigned tasks with filters."""
        # Mock tasks query
        mock_db_session.query.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = [sample_task]
        
        result = TaskService.get_assigned_tasks(
            mock_db_session,
            "test-user-id",
            status="InProgress",
            project_id="test-project-id"
        )
        
        assert len(result) == 1
        assert result[0] == sample_task
        mock_db_session.query.assert_called_once()
    
    def test_get_assigned_tasks_empty(self, mock_db_session):
        """Test retrieval of assigned tasks when none exist."""
        # Mock empty tasks query
        mock_db_session.query.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        result = TaskService.get_assigned_tasks(
            mock_db_session,
            "test-user-id"
        )
        
        assert len(result) == 0
        mock_db_session.query.assert_called_once()
    
    def test_get_tasks_by_status_success(self, mock_db_session, sample_task):
        """Test successful retrieval of tasks by status."""
        # Mock tasks query
        mock_db_session.query.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = [sample_task]
        
        result = TaskService.get_tasks_by_status(
            mock_db_session,
            "InProgress"
        )
        
        assert len(result) == 1
        assert result[0] == sample_task
        mock_db_session.query.assert_called_once()
    
    def test_get_tasks_by_status_with_filters(self, mock_db_session, sample_task):
        """Test retrieval of tasks by status with filters."""
        # Mock tasks query
        mock_db_session.query.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = [sample_task]
        
        result = TaskService.get_tasks_by_status(
            mock_db_session,
            "InProgress",
            project_id="test-project-id",
            assignee_id="test-user-id"
        )
        
        assert len(result) == 1
        assert result[0] == sample_task
        mock_db_session.query.assert_called_once()
    
    def test_get_tasks_by_status_invalid(self, mock_db_session):
        """Test retrieval of tasks by status with invalid status."""
        with pytest.raises(ValueError, match="Invalid status"):
            TaskService.get_tasks_by_status(
                mock_db_session,
                "InvalidStatus"
            )
    
    def test_get_tasks_by_status_empty(self, mock_db_session):
        """Test retrieval of tasks by status when none exist."""
        # Mock empty tasks query
        mock_db_session.query.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        result = TaskService.get_tasks_by_status(
            mock_db_session,
            "InProgress"
        )
        
        assert len(result) == 0
        mock_db_session.query.assert_called_once()
    
    def test_search_tasks_success(self, mock_db_session, sample_task):
        """Test successful task search."""
        # Mock tasks query
        mock_db_session.query.return_value.options.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [sample_task]
        
        result = TaskService.search_tasks(
            mock_db_session,
            "test query",
            limit=10
        )
        
        assert len(result) == 1
        assert result[0] == sample_task
        mock_db_session.query.assert_called_once()
    
    def test_search_tasks_with_project_filter(self, mock_db_session, sample_task):
        """Test task search with project filter."""
        # Mock tasks query
        mock_db_session.query.return_value.options.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [sample_task]
        
        result = TaskService.search_tasks(
            mock_db_session,
            "test query",
            project_id="test-project-id",
            limit=10
        )
        
        assert len(result) == 1
        assert result[0] == sample_task
        mock_db_session.query.assert_called_once()
    
    def test_search_tasks_empty(self, mock_db_session):
        """Test task search with no results."""
        # Mock empty tasks query
        mock_db_session.query.return_value.options.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        result = TaskService.search_tasks(
            mock_db_session,
            "nonexistent query",
            limit=10
        )
        
        assert len(result) == 0
        mock_db_session.query.assert_called_once()
    
    def test_filter_tasks_by_status(self, mock_db_session, sample_task):
        """Test task filtering by status."""
        # Mock tasks query
        mock_db_session.query.return_value.options.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [sample_task]
        
        result = TaskService.filter_tasks(
            mock_db_session,
            status="InProgress",
            limit=10
        )
        
        assert len(result) == 1
        assert result[0] == sample_task
        mock_db_session.query.assert_called_once()
    
    def test_filter_tasks_by_priority(self, mock_db_session, sample_task):
        """Test task filtering by priority."""
        # Mock tasks query
        mock_db_session.query.return_value.options.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [sample_task]
        
        result = TaskService.filter_tasks(
            mock_db_session,
            priority="High",
            limit=10
        )
        
        assert len(result) == 1
        assert result[0] == sample_task
        mock_db_session.query.assert_called_once()
    
    def test_filter_tasks_by_assignee(self, mock_db_session, sample_task):
        """Test task filtering by assignee."""
        # Mock tasks query
        mock_db_session.query.return_value.options.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [sample_task]
        
        result = TaskService.filter_tasks(
            mock_db_session,
            assignee_id="test-user-id",
            limit=10
        )
        
        assert len(result) == 1
        assert result[0] == sample_task
        mock_db_session.query.assert_called_once()
    
    def test_filter_tasks_by_project(self, mock_db_session, sample_task):
        """Test task filtering by project."""
        # Mock tasks query
        mock_db_session.query.return_value.options.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [sample_task]
        
        result = TaskService.filter_tasks(
            mock_db_session,
            project_id="test-project-id",
            limit=10
        )
        
        assert len(result) == 1
        assert result[0] == sample_task
        mock_db_session.query.assert_called_once()
    
    def test_filter_tasks_by_date_range(self, mock_db_session, sample_task):
        """Test task filtering by date range."""
        # Mock tasks query
        mock_db_session.query.return_value.options.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [sample_task]
        
        result = TaskService.filter_tasks(
            mock_db_session,
            due_date_from=date(2025, 1, 1),
            due_date_to=date(2025, 12, 31),
            limit=10
        )
        
        assert len(result) == 1
        assert result[0] == sample_task
        mock_db_session.query.assert_called_once()
    
    def test_filter_tasks_by_dependencies(self, mock_db_session, sample_task):
        """Test task filtering by dependencies."""
        # Mock tasks query
        mock_db_session.query.return_value.options.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [sample_task]
        
        result = TaskService.filter_tasks(
            mock_db_session,
            has_dependencies=True,
            limit=10
        )
        
        assert len(result) == 1
        assert result[0] == sample_task
        mock_db_session.query.assert_called_once()
    
    def test_filter_tasks_by_overdue(self, mock_db_session, sample_task):
        """Test task filtering by overdue status."""
        # Mock tasks query
        mock_db_session.query.return_value.options.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [sample_task]
        
        result = TaskService.filter_tasks(
            mock_db_session,
            is_overdue=True,
            limit=10
        )
        
        assert len(result) == 1
        assert result[0] == sample_task
        mock_db_session.query.assert_called_once()
    
    def test_filter_tasks_empty(self, mock_db_session):
        """Test task filtering with no results."""
        # Mock empty tasks query
        mock_db_session.query.return_value.options.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        result = TaskService.filter_tasks(
            mock_db_session,
            status="Done",
            limit=10
        )
        
        assert len(result) == 0
        mock_db_session.query.assert_called_once()
    
    def test_sort_tasks_by_title(self, mock_db_session, sample_task):
        """Test task sorting by title."""
        # Mock tasks query
        mock_db_session.query.return_value.options.return_value.order_by.return_value.limit.return_value.all.return_value = [sample_task]
        
        result = TaskService.sort_tasks(
            mock_db_session,
            sort_by="title",
            sort_order="asc",
            limit=10
        )
        
        assert len(result) == 1
        assert result[0] == sample_task
        mock_db_session.query.assert_called_once()
    
    def test_sort_tasks_by_status(self, mock_db_session, sample_task):
        """Test task sorting by status."""
        # Mock tasks query
        mock_db_session.query.return_value.options.return_value.order_by.return_value.limit.return_value.all.return_value = [sample_task]
        
        result = TaskService.sort_tasks(
            mock_db_session,
            sort_by="status",
            sort_order="desc",
            limit=10
        )
        
        assert len(result) == 1
        assert result[0] == sample_task
        mock_db_session.query.assert_called_once()
    
    def test_sort_tasks_by_priority(self, mock_db_session, sample_task):
        """Test task sorting by priority."""
        # Mock tasks query
        mock_db_session.query.return_value.options.return_value.order_by.return_value.limit.return_value.all.return_value = [sample_task]
        
        result = TaskService.sort_tasks(
            mock_db_session,
            sort_by="priority",
            sort_order="asc",
            limit=10
        )
        
        assert len(result) == 1
        assert result[0] == sample_task
        mock_db_session.query.assert_called_once()
    
    def test_sort_tasks_by_due_date(self, mock_db_session, sample_task):
        """Test task sorting by due date."""
        # Mock tasks query
        mock_db_session.query.return_value.options.return_value.order_by.return_value.limit.return_value.all.return_value = [sample_task]
        
        result = TaskService.sort_tasks(
            mock_db_session,
            sort_by="due_date",
            sort_order="desc",
            limit=10
        )
        
        assert len(result) == 1
        assert result[0] == sample_task
        mock_db_session.query.assert_called_once()
    
    def test_sort_tasks_by_created_at(self, mock_db_session, sample_task):
        """Test task sorting by created date."""
        # Mock tasks query
        mock_db_session.query.return_value.options.return_value.order_by.return_value.limit.return_value.all.return_value = [sample_task]
        
        result = TaskService.sort_tasks(
            mock_db_session,
            sort_by="created_at",
            sort_order="desc",
            limit=10
        )
        
        assert len(result) == 1
        assert result[0] == sample_task
        mock_db_session.query.assert_called_once()
    
    def test_sort_tasks_empty(self, mock_db_session):
        """Test task sorting with no results."""
        # Mock empty tasks query
        mock_db_session.query.return_value.options.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        result = TaskService.sort_tasks(
            mock_db_session,
            sort_by="title",
            sort_order="asc",
            limit=10
        )
        
        assert len(result) == 0
        mock_db_session.query.assert_called_once()


class TestTaskValidation:
    """Test cases for task validation."""
    
    def test_task_create_request_valid(self):
        """Test valid task creation request."""
        task_data = TaskCreateRequest(
            title="Test Task",
            description="A test task",
            priority="High",
            estimated_hours=Decimal('8.00'),
            due_date=date(2025, 12, 31),
            dependencies=[]
        )
        
        assert task_data.title == "Test Task"
        assert task_data.priority == "High"
        assert task_data.estimated_hours == Decimal('8.00')
    
    def test_task_create_request_invalid_priority(self):
        """Test task creation request with invalid priority."""
        with pytest.raises(ValueError, match="Priority must be one of"):
            TaskCreateRequest(
                title="Test Task",
                priority="Invalid"
            )
    
    def test_task_create_request_past_due_date(self):
        """Test task creation request with past due date."""
        with pytest.raises(ValueError, match="Due date cannot be in the past"):
            TaskCreateRequest(
                title="Test Task",
                due_date=date(2020, 1, 1)
            )
    
    def test_task_update_request_valid(self):
        """Test valid task update request."""
        update_data = TaskUpdateRequest(
            title="Updated Task",
            status="InProgress",
            priority="High"
        )
        
        assert update_data.title == "Updated Task"
        assert update_data.status == "InProgress"
        assert update_data.priority == "High"
    
    def test_task_update_request_invalid_status(self):
        """Test task update request with invalid status."""
        with pytest.raises(ValueError, match="Status must be one of"):
            TaskUpdateRequest(status="Invalid")
    
    def test_task_update_request_invalid_priority(self):
        """Test task update request with invalid priority."""
        with pytest.raises(ValueError, match="Priority must be one of"):
            TaskUpdateRequest(priority="Invalid")
    
    def test_task_dependency_request_valid(self):
        """Test valid task dependency request."""
        dependency_data = TaskDependencyRequest(
            prerequisite_task_id=uuid4(),
            dependency_type="DependsOn"
        )
        
        assert dependency_data.prerequisite_task_id is not None
        assert dependency_data.dependency_type == "DependsOn"
    
    def test_task_dependency_request_invalid_type(self):
        """Test task dependency request with invalid type."""
        with pytest.raises(ValueError, match="Dependency type must be one of"):
            TaskDependencyRequest(
                prerequisite_task_id=uuid4(),
                dependency_type="Invalid"
            )
    
    def test_task_assignment_request_valid(self):
        """Test valid task assignment request."""
        assignee_id = uuid4()
        request = TaskAssignmentRequest(assignee_id=assignee_id)
        
        assert request.assignee_id == assignee_id
    
    def test_task_assignment_request_empty_assignee(self):
        """Test task assignment request with empty assignee ID."""
        with pytest.raises(ValueError, match="Assignee ID cannot be empty"):
            TaskAssignmentRequest(assignee_id="")
    
    def test_task_status_request_valid(self):
        """Test valid task status request."""
        request = TaskStatusRequest(status="InProgress")
        
        assert request.status == "InProgress"
    
    def test_task_status_request_invalid_status(self):
        """Test task status request with invalid status."""
        with pytest.raises(ValueError, match="Status must be one of"):
            TaskStatusRequest(status="InvalidStatus")
    
    def test_task_search_request_valid(self):
        """Test valid task search request."""
        request = TaskSearchRequest(query="test query")
        
        assert request.query == "test query"
        assert request.limit == 20
    
    def test_task_search_request_empty_query(self):
        """Test task search request with empty query."""
        with pytest.raises(ValueError, match="Search query cannot be empty"):
            TaskSearchRequest(query="")
    
    def test_task_search_request_whitespace_query(self):
        """Test task search request with whitespace-only query."""
        with pytest.raises(ValueError, match="Search query cannot be empty"):
            TaskSearchRequest(query="   ")
    
    def test_task_search_request_with_project(self):
        """Test task search request with project filter."""
        project_id = uuid4()
        request = TaskSearchRequest(query="test query", project_id=project_id, limit=50)
        
        assert request.query == "test query"
        assert request.project_id == project_id
        assert request.limit == 50
    
    def test_task_filter_request_valid(self):
        """Test valid task filter request."""
        request = TaskFilterRequest(
            status="InProgress",
            priority="High",
            limit=30
        )
        
        assert request.status == "InProgress"
        assert request.priority == "High"
        assert request.limit == 30
    
    def test_task_filter_request_invalid_status(self):
        """Test task filter request with invalid status."""
        with pytest.raises(ValueError, match="Status must be one of"):
            TaskFilterRequest(status="InvalidStatus")
    
    def test_task_filter_request_invalid_priority(self):
        """Test task filter request with invalid priority."""
        with pytest.raises(ValueError, match="Priority must be one of"):
            TaskFilterRequest(priority="InvalidPriority")
    
    def test_task_filter_request_invalid_date_range(self):
        """Test task filter request with invalid date range."""
        with pytest.raises(ValueError, match="Due date 'to' must be after due date 'from'"):
            TaskFilterRequest(
                due_date_from=date(2025, 12, 31),
                due_date_to=date(2025, 1, 1)
            )
    
    def test_task_filter_request_invalid_created_date_range(self):
        """Test task filter request with invalid created date range."""
        with pytest.raises(ValueError, match="Created date 'to' must be after created date 'from'"):
            TaskFilterRequest(
                created_date_from=date(2025, 12, 31),
                created_date_to=date(2025, 1, 1)
            )
    
    def test_task_sort_request_valid(self):
        """Test valid task sort request."""
        request = TaskSortRequest(
            sort_by="title",
            sort_order="asc",
            limit=25
        )
        
        assert request.sort_by == "title"
        assert request.sort_order == "asc"
        assert request.limit == 25
    
    def test_task_sort_request_invalid_sort_field(self):
        """Test task sort request with invalid sort field."""
        with pytest.raises(ValueError, match="Sort field must be one of"):
            TaskSortRequest(sort_by="InvalidField")
    
    def test_task_sort_request_invalid_sort_order(self):
        """Test task sort request with invalid sort order."""
        with pytest.raises(ValueError, match="Sort order must be 'asc' or 'desc'"):
            TaskSortRequest(sort_order="invalid") 