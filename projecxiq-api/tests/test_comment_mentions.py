"""
Tests for comment mentions functionality.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import uuid4

from app.services.comment_service import CommentService
from app.schemas.comment import CommentMentionCreateRequest
from app.models.comment import Comment, CommentMention
from app.models.project import Project
from app.models.task import Task
from app.models.milestone import Milestone
from app.models.user import User
from pydantic import ValidationError


class TestCommentMentions:
    """Test cases for comment mentions functionality."""
    
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
    def sample_mentioned_user(self):
        """Sample mentioned user for testing."""
        user = User(
            id=uuid4(),
            email="mentioned@example.com",
            first_name="Mentioned",
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
    def sample_mention(self, sample_comment, sample_mentioned_user):
        """Sample mention for testing."""
        mention = CommentMention(
            id=uuid4(),
            comment_id=sample_comment.id,
            mentioned_user_id=sample_mentioned_user.id,
            created_at=datetime.now(timezone.utc)
        )
        return mention
    
    @pytest.fixture
    def sample_mention_data(self, sample_mentioned_user):
        """Sample mention creation data."""
        return CommentMentionCreateRequest(
            mentioned_user_id=sample_mentioned_user.id
        )
    
    def test_create_comment_mention_success(self, mock_db_session, sample_comment, sample_mentioned_user, sample_mention_data):
        """Test successful mention creation."""
        # Mock comment query
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            sample_comment,  # Comment exists
            sample_mentioned_user,  # Mentioned user exists
            None  # No existing mention
        ]
        
        # Mock mention creation
        mock_mention = CommentMention(
            id=uuid4(),
            comment_id=sample_comment.id,
            mentioned_user_id=sample_mentioned_user.id
        )
        
        result = CommentService.create_comment_mention(
            mock_db_session,
            str(sample_comment.id),
            str(sample_mentioned_user.id),
            "test_user_id"
        )
        
        assert result is not None
        assert str(result.comment_id) == str(sample_comment.id)
        assert str(result.mentioned_user_id) == str(sample_mentioned_user.id)
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    def test_create_comment_mention_comment_not_found(self, mock_db_session, sample_mention_data):
        """Test mention creation with non-existent comment."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="Comment not found"):
            CommentService.create_comment_mention(
                mock_db_session,
                str(uuid4()),
                str(uuid4()),
                "test_user_id"
            )
    
    def test_create_comment_mention_user_not_found(self, mock_db_session, sample_comment, sample_mention_data):
        """Test mention creation with non-existent user."""
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            sample_comment,  # Comment exists
            None  # Mentioned user doesn't exist
        ]
        
        with pytest.raises(ValueError, match="Mentioned user not found"):
            CommentService.create_comment_mention(
                mock_db_session,
                str(sample_comment.id),
                str(uuid4()),
                "test_user_id"
            )
    
    def test_create_comment_mention_duplicate(self, mock_db_session, sample_comment, sample_mentioned_user, sample_mention_data):
        """Test mention creation with duplicate mention."""
        # Mock existing mention
        existing_mention = CommentMention(
            id=uuid4(),
            comment_id=sample_comment.id,
            mentioned_user_id=sample_mentioned_user.id
        )
        
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            sample_comment,  # Comment exists
            sample_mentioned_user,  # Mentioned user exists
            existing_mention  # Mention already exists
        ]
        
        with pytest.raises(ValueError, match="User is already mentioned in this comment"):
            CommentService.create_comment_mention(
                mock_db_session,
                str(sample_comment.id),
                str(sample_mentioned_user.id),
                "test_user_id"
            )
    
    def test_get_comment_mentions_success(self, mock_db_session, sample_mention):
        """Test successful mention retrieval for a comment."""
        # Mock the query chain properly
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_mention]
        
        mentions, pagination = CommentService.get_comment_mentions(
            mock_db_session,
            str(sample_mention.comment_id),
            page=1,
            limit=20
        )
        
        assert len(mentions) == 1
        assert mentions[0] == sample_mention
        assert pagination["total_count"] == 1
        assert pagination["page"] == 1
    
    def test_get_user_mentions_success(self, mock_db_session, sample_mention):
        """Test successful mention retrieval for a user."""
        # Mock the query chain properly
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_mention]
        
        mentions, pagination = CommentService.get_user_mentions(
            mock_db_session,
            str(sample_mention.mentioned_user_id),
            page=1,
            limit=20
        )
        
        assert len(mentions) == 1
        assert mentions[0] == sample_mention
        assert pagination["total_count"] == 1
        assert pagination["page"] == 1
    
    def test_delete_comment_mention_success(self, mock_db_session, sample_comment, sample_mention):
        """Test successful mention deletion."""
        # Mock mention and comment queries
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            sample_mention,  # Mention exists
            sample_comment   # Comment exists
        ]
        
        result = CommentService.delete_comment_mention(
            mock_db_session,
            str(sample_comment.id),
            str(sample_mention.id),
            str(sample_comment.author_id)  # Comment author can delete
        )
        
        assert result is True
        mock_db_session.delete.assert_called_once_with(sample_mention)
        mock_db_session.commit.assert_called_once()
    
    def test_delete_comment_mention_not_found(self, mock_db_session):
        """Test mention deletion when mention not found."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="Mention not found"):
            CommentService.delete_comment_mention(
                mock_db_session,
                str(uuid4()),
                str(uuid4()),
                "test_user_id"
            )
    
    def test_delete_comment_mention_comment_not_found(self, mock_db_session, sample_mention):
        """Test mention deletion when comment not found."""
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            sample_mention,  # Mention exists
            None  # Comment doesn't exist
        ]
        
        with pytest.raises(ValueError, match="Comment not found"):
            CommentService.delete_comment_mention(
                mock_db_session,
                str(uuid4()),
                str(sample_mention.id),
                "test_user_id"
            )
    
    def test_delete_comment_mention_unauthorized(self, mock_db_session, sample_comment, sample_mention):
        """Test mention deletion by unauthorized user."""
        # Mock mention and comment queries
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            sample_mention,  # Mention exists
            sample_comment   # Comment exists
        ]
        
        with pytest.raises(ValueError, match="You can only delete mentions from your own comments"):
            CommentService.delete_comment_mention(
                mock_db_session,
                str(sample_comment.id),
                str(sample_mention.id),
                "different_user_id"  # Different user
            )
    
    def test_can_delete_mention_authorized(self, sample_comment, sample_mention):
        """Test mention deletion permission for comment author."""
        # Set up the relationship
        sample_mention.comment = sample_comment
        
        result = CommentService.can_delete_mention(
            sample_mention,
            str(sample_comment.author_id)
        )
        assert result is True
    
    def test_can_delete_mention_unauthorized(self, sample_comment, sample_mention):
        """Test mention deletion permission for non-author."""
        # Set up the relationship
        sample_mention.comment = sample_comment
        
        result = CommentService.can_delete_mention(
            sample_mention,
            "different_user_id"
        )
        assert result is False


class TestCommentMentionValidation:
    """Test cases for comment mention validation."""
    
    def test_comment_mention_create_request_valid(self):
        """Test valid mention creation request."""
        user_id = uuid4()
        data = {
            "mentioned_user_id": str(user_id)
        }
        
        request = CommentMentionCreateRequest(**data)
        assert str(request.mentioned_user_id) == str(user_id)
    
    def test_comment_mention_create_request_empty_user_id(self):
        """Test mention creation request with empty user ID."""
        data = {
            "mentioned_user_id": ""
        }
        
        with pytest.raises(ValidationError, match="Input should be a valid UUID"):
            CommentMentionCreateRequest(**data)
    
    def test_comment_mention_create_request_invalid_uuid(self):
        """Test mention creation request with invalid UUID."""
        data = {
            "mentioned_user_id": "invalid-uuid"
        }
        
        with pytest.raises(ValidationError, match="Input should be a valid UUID"):
            CommentMentionCreateRequest(**data) 