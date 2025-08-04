"""
Tests for comment attachments functionality.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import uuid4

from app.services.comment_service import CommentService
from app.schemas.comment import CommentAttachmentCreateRequest
from app.models.comment import Comment, CommentAttachment
from app.models.project import Project
from app.models.task import Task
from app.models.milestone import Milestone
from app.models.user import User
from pydantic import ValidationError


class TestCommentAttachments:
    """Test cases for comment attachments functionality."""
    
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
    def sample_attachment(self, sample_comment, sample_user):
        """Sample attachment for testing."""
        attachment = CommentAttachment(
            id=uuid4(),
            comment_id=sample_comment.id,
            file_name="test_document.pdf",
            file_size=1024,
            mime_type="application/pdf",
            file_path="/uploads/attachments/test.pdf",
            created_at=datetime.now(timezone.utc)
        )
        return attachment
    
    @pytest.fixture
    def sample_attachment_data(self):
        """Sample attachment creation data."""
        return CommentAttachmentCreateRequest(
            file_name="test_document.pdf",
            file_size=1024,
            mime_type="application/pdf"
        )
    
    def test_create_comment_attachment_success(self, mock_db_session, sample_comment, sample_attachment_data):
        """Test successful attachment creation."""
        # Mock comment query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_comment
        
        # Mock attachment creation
        mock_attachment = CommentAttachment(
            id=uuid4(),
            comment_id=sample_comment.id,
            file_name=sample_attachment_data.file_name,
            file_size=sample_attachment_data.file_size,
            mime_type=sample_attachment_data.mime_type,
            file_path="/uploads/attachments/test.pdf"
        )
        
        result = CommentService.create_comment_attachment(
            mock_db_session,
            str(sample_comment.id),
            sample_attachment_data.file_name,
            sample_attachment_data.file_size,
            sample_attachment_data.mime_type,
            "/uploads/attachments/test.pdf"
        )
        
        assert result is not None
        assert str(result.comment_id) == str(sample_comment.id)
        assert result.file_name == sample_attachment_data.file_name
        assert result.file_size == sample_attachment_data.file_size
        assert result.mime_type == sample_attachment_data.mime_type
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    def test_create_comment_attachment_comment_not_found(self, mock_db_session, sample_attachment_data):
        """Test attachment creation with non-existent comment."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="Comment not found"):
            CommentService.create_comment_attachment(
                mock_db_session,
                str(uuid4()),
                sample_attachment_data.file_name,
                sample_attachment_data.file_size,
                sample_attachment_data.mime_type,
                "/uploads/attachments/test.pdf"
            )
    
    def test_get_comment_attachments_success(self, mock_db_session, sample_attachment):
        """Test successful attachment retrieval for a comment."""
        # Mock the query chain properly
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_attachment]
        
        attachments, pagination = CommentService.get_comment_attachments(
            mock_db_session,
            str(sample_attachment.comment_id),
            page=1,
            limit=20
        )
        
        assert len(attachments) == 1
        assert attachments[0] == sample_attachment
        assert pagination["total_count"] == 1
        assert pagination["page"] == 1
    
    def test_delete_comment_attachment_success(self, mock_db_session, sample_comment, sample_attachment):
        """Test successful attachment deletion."""
        # Mock attachment and comment queries
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            sample_attachment,  # Attachment exists
            sample_comment   # Comment exists
        ]
        
        result = CommentService.delete_comment_attachment(
            mock_db_session,
            str(sample_comment.id),
            str(sample_attachment.id),
            str(sample_comment.author_id)  # Comment author can delete
        )
        
        assert result is True
        mock_db_session.delete.assert_called_once_with(sample_attachment)
        mock_db_session.commit.assert_called_once()
    
    def test_delete_comment_attachment_not_found(self, mock_db_session):
        """Test attachment deletion when attachment not found."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="Attachment not found"):
            CommentService.delete_comment_attachment(
                mock_db_session,
                str(uuid4()),
                str(uuid4()),
                "test_user_id"
            )
    
    def test_delete_comment_attachment_comment_not_found(self, mock_db_session, sample_attachment):
        """Test attachment deletion when comment not found."""
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            sample_attachment,  # Attachment exists
            None  # Comment doesn't exist
        ]
        
        with pytest.raises(ValueError, match="Comment not found"):
            CommentService.delete_comment_attachment(
                mock_db_session,
                str(uuid4()),
                str(sample_attachment.id),
                "test_user_id"
            )
    
    def test_delete_comment_attachment_unauthorized(self, mock_db_session, sample_comment, sample_attachment):
        """Test attachment deletion by unauthorized user."""
        # Mock attachment and comment queries
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            sample_attachment,  # Attachment exists
            sample_comment   # Comment exists
        ]
        
        with pytest.raises(ValueError, match="You can only delete attachments from your own comments"):
            CommentService.delete_comment_attachment(
                mock_db_session,
                str(sample_comment.id),
                str(sample_attachment.id),
                "different_user_id"  # Different user
            )
    
    def test_can_delete_attachment_comment_author(self, sample_comment, sample_attachment):
        """Test attachment deletion permission for comment author."""
        # Set up the relationship
        sample_attachment.comment = sample_comment
        
        result = CommentService.can_delete_attachment(
            sample_attachment,
            str(sample_comment.author_id)
        )
        assert result is True
    
    def test_can_delete_attachment_comment_author_only(self, sample_comment, sample_attachment):
        """Test attachment deletion permission for comment author only."""
        # Set up the relationship
        sample_attachment.comment = sample_comment
        
        result = CommentService.can_delete_attachment(
            sample_attachment,
            str(sample_comment.author_id)
        )
        assert result is True
    
    def test_can_delete_attachment_unauthorized(self, sample_comment, sample_attachment):
        """Test attachment deletion permission for unauthorized user."""
        # Set up the relationship
        sample_attachment.comment = sample_comment
        
        result = CommentService.can_delete_attachment(
            sample_attachment,
            "different_user_id"
        )
        assert result is False


class TestCommentAttachmentValidation:
    """Test cases for comment attachment validation."""
    
    def test_comment_attachment_create_request_valid(self):
        """Test valid attachment creation request."""
        data = {
            "file_name": "test_document.pdf",
            "file_size": 1024,
            "mime_type": "application/pdf"
        }
        
        request = CommentAttachmentCreateRequest(**data)
        assert request.file_name == data["file_name"]
        assert request.file_size == data["file_size"]
        assert request.mime_type == data["mime_type"]
    
    def test_comment_attachment_create_request_empty_file_name(self):
        """Test attachment creation request with empty file name."""
        data = {
            "file_name": "",
            "file_size": 1024,
            "mime_type": "application/pdf"
        }
        
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            CommentAttachmentCreateRequest(**data)
    
    def test_comment_attachment_create_request_invalid_file_name(self):
        """Test attachment creation request with invalid file name."""
        data = {
            "file_name": "test<file>.pdf",
            "file_size": 1024,
            "mime_type": "application/pdf"
        }
        
        with pytest.raises(ValidationError, match="File name contains invalid characters"):
            CommentAttachmentCreateRequest(**data)
    
    def test_comment_attachment_create_request_invalid_mime_type(self):
        """Test attachment creation request with invalid MIME type."""
        data = {
            "file_name": "test_document.pdf",
            "file_size": 1024,
            "mime_type": "application/invalid"
        }
        
        with pytest.raises(ValidationError, match="MIME type application/invalid is not allowed"):
            CommentAttachmentCreateRequest(**data)
    
    def test_comment_attachment_create_request_file_too_large(self):
        """Test attachment creation request with file too large."""
        data = {
            "file_name": "test_document.pdf",
            "file_size": 10485761,  # 10MB + 1 byte
            "file_type": "application/pdf"
        }
        
        with pytest.raises(ValidationError, match="Input should be less than or equal to 10485760"):
            CommentAttachmentCreateRequest(**data)
    
    def test_comment_attachment_create_request_zero_file_size(self):
        """Test attachment creation request with zero file size."""
        data = {
            "file_name": "test_document.pdf",
            "file_size": 0,
            "file_type": "application/pdf"
        }
        
        with pytest.raises(ValidationError, match="Input should be greater than 0"):
            CommentAttachmentCreateRequest(**data)
    
    def test_comment_attachment_create_request_valid_without_description(self):
        """Test valid attachment creation request without description."""
        data = {
            "file_name": "test_document.pdf",
            "file_size": 1024,
            "mime_type": "application/pdf"
        }
        
        request = CommentAttachmentCreateRequest(**data)
        assert request.file_name == data["file_name"]
        assert request.file_size == data["file_size"]
        assert request.mime_type == data["mime_type"] 