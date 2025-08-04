"""
Tests for comment service layer.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import uuid4

from app.services.comment_service import CommentService
from app.schemas.comment import CommentCreateRequest, CommentUpdateRequest
from app.models.comment import Comment
from app.models.project import Project
from app.models.task import Task
from app.models.milestone import Milestone
from app.models.user import User
from pydantic import ValidationError


class TestCommentService:
    """Test cases for comment service."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return MagicMock()
    
    @pytest.fixture
    def sample_user(self):
        """Sample user for testing."""
        user = User(
            id=uuid4(),
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password_hash="hashed_password",
            role="Developer",
            is_active=True
        )
        return user
    
    @pytest.fixture
    def sample_project(self, sample_user):
        """Sample project for testing."""
        project = Project(
            id=uuid4(),
            name="Test Project",
            description="A test project",
            manager_id=sample_user.id,
            status="Active",
            start_date=datetime.now().date(),
            end_date=datetime.now().date() + timedelta(days=30)
        )
        return project
    
    @pytest.fixture
    def sample_task(self, sample_project, sample_user):
        """Sample task for testing."""
        task = Task(
            id=uuid4(),
            title="Test Task",
            description="A test task",
            project_id=sample_project.id,
            assignee_id=sample_user.id,
            priority="Medium",
            status="ToDo",
            estimated_hours=Decimal('8.00'),
            due_date=datetime.now().date() + timedelta(days=7)
        )
        return task
    
    @pytest.fixture
    def sample_milestone(self, sample_project):
        """Sample milestone for testing."""
        milestone = Milestone(
            id=uuid4(),
            name="Test Milestone",
            description="A test milestone",
            project_id=sample_project.id,
            due_date=datetime.now().date() + timedelta(days=14),
            is_completed=False
        )
        return milestone
    
    @pytest.fixture
    def sample_comment(self, sample_user, sample_project):
        """Sample comment for testing."""
        comment = Comment(
            id=uuid4(),
            content="Test comment content",
            author_id=sample_user.id,
            entity_type="Project",
            entity_id=sample_project.id,
            parent_comment_id=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        return comment
    
    @pytest.fixture
    def sample_comment_data(self, sample_project):
        """Sample comment creation data."""
        return CommentCreateRequest(
            content="Test comment content",
            entity_type="Project",
            entity_id=sample_project.id,
            parent_comment_id=None
        )
    
    def test_create_comment_success(self, mock_db_session, sample_comment_data, sample_project):
        """Test successful comment creation."""
        # Mock project query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_project
        
        # Mock comment creation
        mock_comment = Comment(
            id=uuid4(),
            content=sample_comment_data.content,
            author_id="test_user_id",
            entity_type=sample_comment_data.entity_type,
            entity_id=sample_comment_data.entity_id,
            parent_comment_id=sample_comment_data.parent_comment_id
        )
        
        with patch('app.services.comment_service.CommentService._validate_entity_exists', return_value=True):
            result = CommentService.create_comment(
                mock_db_session,
                sample_comment_data,
                "test_user_id"
            )
        
        assert result is not None
        assert result.content == sample_comment_data.content
        assert result.entity_type == sample_comment_data.entity_type
        assert result.entity_id == sample_comment_data.entity_id
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    def test_create_comment_entity_not_found(self, mock_db_session, sample_comment_data):
        """Test comment creation with non-existent entity."""
        with patch('app.services.comment_service.CommentService._validate_entity_exists', return_value=False):
            with pytest.raises(ValueError, match="Project not found"):
                CommentService.create_comment(
                    mock_db_session,
                    sample_comment_data,
                    "test_user_id"
                )
    
    def test_create_comment_with_parent(self, mock_db_session, sample_comment_data, sample_project):
        """Test comment creation with parent comment."""
        # Mock project query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_project
        
        # Mock parent comment
        parent_comment = Comment(
            id=uuid4(),
            content="Parent comment",
            author_id="test_user_id",
            entity_type="Project",
            entity_id=sample_project.id,
            parent_comment_id=None
        )
        
        # Update comment data to include parent
        sample_comment_data.parent_comment_id = parent_comment.id
        
        with patch('app.services.comment_service.CommentService._validate_entity_exists', return_value=True):
            with patch.object(mock_db_session, 'query') as mock_query:
                # Mock parent comment query
                mock_query.return_value.filter.return_value.first.return_value = parent_comment
                
                result = CommentService.create_comment(
                    mock_db_session,
                    sample_comment_data,
                    "test_user_id"
                )
        
        assert result is not None
        assert result.parent_comment_id == parent_comment.id
    
    def test_create_comment_parent_wrong_entity(self, mock_db_session, sample_comment_data, sample_project):
        """Test comment creation with parent comment from different entity."""
        # Mock project query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_project
        
        # Mock parent comment from different entity
        parent_comment = Comment(
            id=uuid4(),
            content="Parent comment",
            author_id="test_user_id",
            entity_type="Task",  # Different entity type
            entity_id=uuid4(),   # Different entity ID
            parent_comment_id=None
        )
        
        # Update comment data to include parent
        sample_comment_data.parent_comment_id = parent_comment.id
        
        with patch('app.services.comment_service.CommentService._validate_entity_exists', return_value=True):
            with patch.object(mock_db_session, 'query') as mock_query:
                # Mock parent comment query
                mock_query.return_value.filter.return_value.first.return_value = parent_comment
                
                with pytest.raises(ValueError, match="Parent comment must belong to the same entity"):
                    CommentService.create_comment(
                        mock_db_session,
                        sample_comment_data,
                        "test_user_id"
                    )
    
    def test_get_comment_by_id_success(self, mock_db_session, sample_comment):
        """Test successful comment retrieval by ID."""
        mock_db_session.query.return_value.options.return_value.filter.return_value.first.return_value = sample_comment
        
        result = CommentService.get_comment_by_id(mock_db_session, str(sample_comment.id))
        
        assert result == sample_comment
        mock_db_session.query.assert_called_once()
    
    def test_get_comment_by_id_not_found(self, mock_db_session):
        """Test comment retrieval by ID when not found."""
        mock_db_session.query.return_value.options.return_value.filter.return_value.first.return_value = None
        
        result = CommentService.get_comment_by_id(mock_db_session, str(uuid4()))
        
        assert result is None
    
    def test_get_comments_success(self, mock_db_session, sample_comment):
        """Test successful comment retrieval with filters."""
        # Mock the query chain properly
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_comment]
        
        comments, pagination = CommentService.get_comments(
            mock_db_session,
            entity_type="Project",
            entity_id=str(uuid4()),
            page=1,
            limit=20
        )
        
        assert len(comments) == 1
        assert comments[0] == sample_comment
        assert pagination["total_count"] == 1
        assert pagination["page"] == 1
    
    def test_search_comments_success(self, mock_db_session, sample_comment):
        """Test successful comment search."""
        # Mock the query chain properly
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_comment]
        
        comments, pagination = CommentService.search_comments(
            mock_db_session,
            "test query",
            entity_type="Project",
            page=1,
            limit=20
        )
        
        assert len(comments) == 1
        assert comments[0] == sample_comment
        assert pagination["total_count"] == 1
    
    def test_get_comment_thread_success(self, mock_db_session, sample_comment):
        """Test successful comment thread retrieval."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_comment
        mock_db_session.query.return_value.options.return_value.filter.return_value.count.return_value = 1
        mock_db_session.query.return_value.options.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [sample_comment]
        mock_db_session.query.return_value.filter.return_value.count.return_value = 0
        
        comments, pagination, thread_info = CommentService.get_comment_thread(
            mock_db_session,
            str(sample_comment.id),
            page=1,
            limit=20
        )
        
        assert len(comments) == 1
        assert comments[0] == sample_comment
        assert pagination["total_count"] == 1
        assert thread_info["root_comment_id"] == str(sample_comment.id)
    
    def test_get_comment_thread_not_found(self, mock_db_session):
        """Test comment thread retrieval when root comment not found."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="Comment not found"):
            CommentService.get_comment_thread(
                mock_db_session,
                str(uuid4()),
                page=1,
                limit=20
            )
    
    def test_update_comment_success(self, mock_db_session, sample_comment):
        """Test successful comment update."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_comment
        
        update_data = CommentUpdateRequest(content="Updated comment content")
        
        result = CommentService.update_comment(
            mock_db_session,
            str(sample_comment.id),
            update_data,
            str(sample_comment.author_id)
        )
        
        assert result is not None
        assert result.content == "Updated comment content"
        mock_db_session.commit.assert_called_once()
    
    def test_update_comment_not_found(self, mock_db_session):
        """Test comment update when comment not found."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        update_data = CommentUpdateRequest(content="Updated comment content")
        
        with pytest.raises(ValueError, match="Comment not found"):
            CommentService.update_comment(
                mock_db_session,
                str(uuid4()),
                update_data,
                "test_user_id"
            )
    
    def test_update_comment_unauthorized(self, mock_db_session, sample_comment):
        """Test comment update by unauthorized user."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_comment
        
        update_data = CommentUpdateRequest(content="Updated comment content")
        
        with pytest.raises(ValueError, match="You can only update your own comments"):
            CommentService.update_comment(
                mock_db_session,
                str(sample_comment.id),
                update_data,
                "different_user_id"
            )
    
    def test_update_comment_outside_editable_period(self, mock_db_session, sample_comment):
        """Test comment update outside editable period."""
        # Set comment creation time to more than 24 hours ago
        sample_comment.created_at = datetime.now(timezone.utc) - timedelta(hours=25)
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_comment
        
        update_data = CommentUpdateRequest(content="Updated comment content")
        
        with pytest.raises(ValueError, match="Comment can only be edited within 24 hours of creation"):
            CommentService.update_comment(
                mock_db_session,
                str(sample_comment.id),
                update_data,
                str(sample_comment.author_id)
            )
    
    def test_delete_comment_success(self, mock_db_session, sample_comment):
        """Test successful comment deletion."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_comment
        
        result = CommentService.delete_comment(
            mock_db_session,
            str(sample_comment.id),
            str(sample_comment.author_id)
        )
        
        assert result is True
        mock_db_session.delete.assert_called_once_with(sample_comment)
        mock_db_session.commit.assert_called_once()
    
    def test_delete_comment_not_found(self, mock_db_session):
        """Test comment deletion when comment not found."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="Comment not found"):
            CommentService.delete_comment(
                mock_db_session,
                str(uuid4()),
                "test_user_id"
            )
    
    def test_delete_comment_unauthorized(self, mock_db_session, sample_comment):
        """Test comment deletion by unauthorized user."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_comment
        
        with pytest.raises(ValueError, match="You can only delete your own comments"):
            CommentService.delete_comment(
                mock_db_session,
                str(sample_comment.id),
                "different_user_id"
            )
    
    def test_delete_comment_outside_editable_period(self, mock_db_session, sample_comment):
        """Test comment deletion outside editable period."""
        # Set comment creation time to more than 24 hours ago
        sample_comment.created_at = datetime.now(timezone.utc) - timedelta(hours=25)
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_comment
        
        with pytest.raises(ValueError, match="Comment can only be deleted within 24 hours of creation"):
            CommentService.delete_comment(
                mock_db_session,
                str(sample_comment.id),
                str(sample_comment.author_id)
            )
    
    def test_can_update_comment_owner(self, sample_comment):
        """Test comment update permission for owner."""
        result = CommentService.can_update_comment(
            sample_comment,
            str(sample_comment.author_id)
        )
        assert result is True
    
    def test_can_update_comment_unauthorized(self, sample_comment):
        """Test comment update permission for non-owner."""
        result = CommentService.can_update_comment(
            sample_comment,
            "different_user_id"
        )
        assert result is False
    
    def test_can_delete_comment_owner(self, sample_comment):
        """Test comment deletion permission for owner."""
        result = CommentService.can_delete_comment(
            sample_comment,
            str(sample_comment.author_id)
        )
        assert result is True
    
    def test_can_delete_comment_unauthorized(self, sample_comment):
        """Test comment deletion permission for non-owner."""
        result = CommentService.can_delete_comment(
            sample_comment,
            "different_user_id"
        )
        assert result is False
    
    def test_is_within_editable_period_recent(self, sample_comment):
        """Test editable period check for recent comment."""
        result = CommentService.is_within_editable_period(sample_comment)
        assert result is True
    
    def test_is_within_editable_period_old(self, sample_comment):
        """Test editable period check for old comment."""
        # Set comment creation time to more than 24 hours ago
        sample_comment.created_at = datetime.now(timezone.utc) - timedelta(hours=25)
        result = CommentService.is_within_editable_period(sample_comment)
        assert result is False
    
    def test_get_comment_statistics_success(self, mock_db_session, sample_comment):
        """Test successful comment statistics retrieval."""
        mock_db_session.query.return_value.filter.return_value.count.return_value = 1
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [sample_comment]
        mock_db_session.query.return_value.group_by.return_value.all.return_value = []
        
        stats = CommentService.get_comment_statistics(
            mock_db_session,
            entity_type="Project"
        )
        
        assert "total_comments" in stats
        assert "total_replies" in stats
        assert "top_level_comments" in stats
        assert "comments_by_entity" in stats
        assert "recent_activity" in stats
    
    def test_validate_entity_exists_project(self, mock_db_session, sample_project):
        """Test entity validation for project."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_project
        
        result = CommentService._validate_entity_exists(
            mock_db_session,
            "Project",
            str(sample_project.id)
        )
        
        assert result is True
    
    def test_validate_entity_exists_task(self, mock_db_session, sample_task):
        """Test entity validation for task."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_task
        
        result = CommentService._validate_entity_exists(
            mock_db_session,
            "Task",
            str(sample_task.id)
        )
        
        assert result is True
    
    def test_validate_entity_exists_milestone(self, mock_db_session, sample_milestone):
        """Test entity validation for milestone."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_milestone
        
        result = CommentService._validate_entity_exists(
            mock_db_session,
            "Milestone",
            str(sample_milestone.id)
        )
        
        assert result is True
    
    def test_validate_entity_exists_invalid_type(self, mock_db_session):
        """Test entity validation for invalid entity type."""
        result = CommentService._validate_entity_exists(
            mock_db_session,
            "InvalidType",
            str(uuid4())
        )
        
        assert result is False


class TestCommentValidation:
    """Test cases for comment validation."""
    
    def test_comment_create_request_valid(self):
        """Test valid comment creation request."""
        data = {
            "content": "Valid comment content",
            "entity_type": "Project",
            "entity_id": str(uuid4()),
            "parent_comment_id": None
        }
        
        request = CommentCreateRequest(**data)
        assert request.content == "Valid comment content"
        assert request.entity_type == "Project"
    
    def test_comment_create_request_invalid_entity_type(self):
        """Test comment creation request with invalid entity type."""
        data = {
            "content": "Valid comment content",
            "entity_type": "InvalidType",
            "entity_id": str(uuid4()),
            "parent_comment_id": None
        }
        
        with pytest.raises(ValidationError, match="Entity type must be one of"):
            CommentCreateRequest(**data)
    
    def test_comment_create_request_empty_content(self):
        """Test comment creation request with empty content."""
        data = {
            "content": "",
            "entity_type": "Project",
            "entity_id": str(uuid4()),
            "parent_comment_id": None
        }
        
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            CommentCreateRequest(**data)
    
    def test_comment_create_request_long_content(self):
        """Test comment creation request with content too long."""
        data = {
            "content": "x" * 5001,  # Exceeds 5000 character limit
            "entity_type": "Project",
            "entity_id": str(uuid4()),
            "parent_comment_id": None
        }
        
        with pytest.raises(ValidationError, match="String should have at most 5000 characters"):
            CommentCreateRequest(**data)
    
    def test_comment_update_request_valid(self):
        """Test valid comment update request."""
        data = {
            "content": "Updated comment content"
        }
        
        request = CommentUpdateRequest(**data)
        assert request.content == "Updated comment content"
    
    def test_comment_update_request_empty_content(self):
        """Test comment update request with empty content."""
        data = {
            "content": ""
        }
        
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            CommentUpdateRequest(**data)
    
    def test_comment_update_request_long_content(self):
        """Test comment update request with content too long."""
        data = {
            "content": "x" * 5001  # Exceeds 5000 character limit
        }
        
        with pytest.raises(ValidationError, match="String should have at most 5000 characters"):
            CommentUpdateRequest(**data) 