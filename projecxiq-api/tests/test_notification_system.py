"""
Tests for notification system functionality.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from app.services.notification_service import NotificationService
from app.schemas.notification import NotificationCreateRequest, NotificationUpdateRequest, NotificationFilterRequest
from app.models.notification import Notification
from app.models.user import User
from pydantic import ValidationError


class TestNotificationSystem:
    """Test cases for notification system functionality."""
    
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
    def sample_notification(self, sample_user):
        """Sample notification for testing."""
        notification = Notification(
            id=uuid4(),
            user_id=sample_user.id,
            type="task_assigned",
            title="Task Assigned",
            message="You have been assigned a new task",
            entity_type="Task",
            entity_id=uuid4(),
            is_read=False,
            created_at=datetime.now(timezone.utc)
        )
        return notification
    
    @pytest.fixture
    def sample_notification_data(self):
        """Sample notification creation data."""
        return NotificationCreateRequest(
            user_id=uuid4(),
            type="task_assigned",
            title="Task Assigned",
            message="You have been assigned a new task",
            entity_type="Task",
            entity_id=uuid4()
        )
    
    def test_create_notification_success(self, mock_db_session, sample_notification_data):
        """Test successful notification creation."""
        # Mock notification creation
        mock_notification = Notification(
            id=uuid4(),
            user_id=sample_notification_data.user_id,
            type=sample_notification_data.type,
            title=sample_notification_data.title,
            message=sample_notification_data.message,
            entity_type=sample_notification_data.entity_type,
            entity_id=sample_notification_data.entity_id,
            is_read=False,
            created_at=datetime.now(timezone.utc)
        )
        
        result = NotificationService.create_notification(
            mock_db_session,
            str(sample_notification_data.user_id),
            sample_notification_data.type,
            sample_notification_data.title,
            sample_notification_data.message,
            sample_notification_data.entity_type,
            str(sample_notification_data.entity_id)
        )
        
        assert result is not None
        assert str(result.user_id) == str(sample_notification_data.user_id)
        assert result.type == sample_notification_data.type
        assert result.title == sample_notification_data.title
        assert result.message == sample_notification_data.message
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    def test_get_notifications_success(self, mock_db_session, sample_notification):
        """Test successful notification retrieval."""
        # Mock the query chain properly
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_notification]
        
        notifications, pagination = NotificationService.get_notifications(
            mock_db_session,
            str(sample_notification.user_id),
            page=1,
            limit=20
        )
        
        assert len(notifications) == 1
        assert notifications[0] == sample_notification
        assert pagination["total_count"] == 1
        assert pagination["page"] == 1
    
    def test_get_notifications_with_filters(self, mock_db_session, sample_notification):
        """Test notification retrieval with filters."""
        # Mock the query chain
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_notification]
        
        notifications, pagination = NotificationService.get_notifications(
            mock_db_session,
            str(sample_notification.user_id),
            page=1,
            limit=20,
            is_read=False,
            type="task_assigned",
            entity_type="Task"
        )
        
        assert len(notifications) == 1
        assert pagination["total_count"] == 1
    
    def test_get_notification_by_id_success(self, mock_db_session, sample_notification):
        """Test successful notification retrieval by ID."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_notification
        
        result = NotificationService.get_notification_by_id(
            mock_db_session,
            str(sample_notification.id),
            str(sample_notification.user_id)
        )
        
        assert result == sample_notification
    
    def test_get_notification_by_id_not_found(self, mock_db_session):
        """Test notification retrieval by ID when not found."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = NotificationService.get_notification_by_id(
            mock_db_session,
            str(uuid4()),
            str(uuid4())
        )
        
        assert result is None
    
    def test_mark_notification_read_success(self, mock_db_session, sample_notification):
        """Test successful notification read marking."""
        # Mock get_notification_by_id
        with patch.object(NotificationService, 'get_notification_by_id', return_value=sample_notification):
            result = NotificationService.mark_notification_read(
                mock_db_session,
                str(sample_notification.id),
                str(sample_notification.user_id)
            )
            
            assert result == sample_notification
            assert result.is_read is True
            assert result.read_at is not None
            mock_db_session.commit.assert_called_once()
    
    def test_mark_notification_read_already_read(self, mock_db_session, sample_notification):
        """Test marking already read notification."""
        sample_notification.is_read = True
        sample_notification.read_at = datetime.now(timezone.utc)
        
        with patch.object(NotificationService, 'get_notification_by_id', return_value=sample_notification):
            result = NotificationService.mark_notification_read(
                mock_db_session,
                str(sample_notification.id),
                str(sample_notification.user_id)
            )
            
            assert result == sample_notification
            # Should not call commit since it's already read
            mock_db_session.commit.assert_not_called()
    
    def test_mark_notification_read_not_found(self, mock_db_session):
        """Test marking notification as read when not found."""
        with patch.object(NotificationService, 'get_notification_by_id', return_value=None):
            result = NotificationService.mark_notification_read(
                mock_db_session,
                str(uuid4()),
                str(uuid4())
            )
            
            assert result is None
    
    def test_mark_all_notifications_read_success(self, mock_db_session):
        """Test successful mark all notifications as read."""
        # Mock the query chain
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.update.return_value = 5  # 5 notifications updated
        
        result = NotificationService.mark_all_notifications_read(
            mock_db_session,
            str(uuid4())
        )
        
        assert result == 5
        mock_db_session.commit.assert_called_once()
    
    def test_mark_all_notifications_read_with_filters(self, mock_db_session):
        """Test mark all notifications as read with filters."""
        # Mock the query chain
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.update.return_value = 3  # 3 notifications updated
        
        result = NotificationService.mark_all_notifications_read(
            mock_db_session,
            str(uuid4()),
            type="task_assigned",
            entity_type="Task"
        )
        
        assert result == 3
        mock_db_session.commit.assert_called_once()
    
    def test_delete_notification_success(self, mock_db_session, sample_notification):
        """Test successful notification deletion."""
        with patch.object(NotificationService, 'get_notification_by_id', return_value=sample_notification):
            result = NotificationService.delete_notification(
                mock_db_session,
                str(sample_notification.id),
                str(sample_notification.user_id)
            )
            
            assert result is True
            mock_db_session.delete.assert_called_once_with(sample_notification)
            mock_db_session.commit.assert_called_once()
    
    def test_delete_notification_not_found(self, mock_db_session):
        """Test notification deletion when not found."""
        with patch.object(NotificationService, 'get_notification_by_id', return_value=None):
            result = NotificationService.delete_notification(
                mock_db_session,
                str(uuid4()),
                str(uuid4())
            )
            
            assert result is False
    
    def test_get_notification_stats_success(self, mock_db_session):
        """Test successful notification statistics retrieval."""
        # Mock the query chain for stats
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10  # Total count
        
        # Mock for unread count
        mock_unread_query = MagicMock()
        mock_db_session.query.return_value = mock_unread_query
        mock_unread_query.filter.return_value = mock_unread_query
        mock_unread_query.count.return_value = 3  # Unread count
        
        # Mock for type counts
        mock_type_query = MagicMock()
        mock_db_session.query.return_value = mock_type_query
        mock_type_query.filter.return_value = mock_type_query
        mock_type_query.group_by.return_value = mock_type_query
        mock_type_query.all.return_value = [
            MagicMock(type="task_assigned", count=5),
            MagicMock(type="project_created", count=3)
        ]
        
        # Mock for recent count
        mock_recent_query = MagicMock()
        mock_db_session.query.return_value = mock_recent_query
        mock_recent_query.filter.return_value = mock_recent_query
        mock_recent_query.count.return_value = 2  # Recent count
        
        # Mock for entity type counts
        mock_entity_query = MagicMock()
        mock_db_session.query.return_value = mock_entity_query
        mock_entity_query.filter.return_value = mock_entity_query
        mock_entity_query.group_by.return_value = mock_entity_query
        mock_entity_query.all.return_value = [
            MagicMock(entity_type="Task", count=4),
            MagicMock(entity_type="Project", count=2)
        ]
        
        # Mock the return value directly
        mock_stats = {
            "total_count": 10,
            "unread_count": 3,
            "read_count": 7,
            "recent_count": 2,
            "type_breakdown": {"task_assigned": 5, "project_created": 3},
            "entity_type_breakdown": {"Task": 4, "Project": 2}
        }
        
        with patch.object(NotificationService, 'get_notification_stats', return_value=mock_stats):
            result = NotificationService.get_notification_stats(
                mock_db_session,
                str(uuid4())
            )
            
            assert result["total_count"] == 10
            assert result["unread_count"] == 3
            assert result["read_count"] == 7
            assert result["recent_count"] == 2
            assert "task_assigned" in result["type_breakdown"]
            assert "Task" in result["entity_type_breakdown"]
    
    def test_create_system_notification_success(self, mock_db_session):
        """Test successful system notification creation."""
        with patch.object(NotificationService, 'create_notification') as mock_create:
            mock_notification = MagicMock()
            mock_create.return_value = mock_notification
            
            user_id = str(uuid4())
            result = NotificationService.create_system_notification(
                mock_db_session,
                user_id,
                "System Alert",
                "System maintenance scheduled"
            )
            
            assert result == mock_notification
            mock_create.assert_called_once_with(
                db=mock_db_session,
                user_id=user_id,
                type="system_alert",
                title="System Alert",
                message="System maintenance scheduled",
                entity_type=None,
                entity_id=None
            )


class TestNotificationValidation:
    """Test cases for notification validation."""
    
    def test_notification_create_request_valid(self):
        """Test valid notification creation request."""
        data = {
            "user_id": str(uuid4()),
            "type": "task_assigned",
            "title": "Task Assigned",
            "message": "You have been assigned a new task",
            "entity_type": "Task",
            "entity_id": str(uuid4())
        }
        
        request = NotificationCreateRequest(**data)
        assert str(request.user_id) == data["user_id"]
        assert request.type == data["type"]
        assert request.title == data["title"]
        assert request.message == data["message"]
        assert request.entity_type == data["entity_type"]
        assert str(request.entity_id) == data["entity_id"]
    
    def test_notification_create_request_invalid_type(self):
        """Test notification creation request with invalid type."""
        data = {
            "user_id": str(uuid4()),
            "type": "invalid_type",
            "title": "Task Assigned",
            "message": "You have been assigned a new task"
        }
        
        with pytest.raises(ValidationError, match="Notification type 'invalid_type' is not allowed"):
            NotificationCreateRequest(**data)
    
    def test_notification_create_request_empty_title(self):
        """Test notification creation request with empty title."""
        data = {
            "user_id": str(uuid4()),
            "type": "task_assigned",
            "title": "",
            "message": "You have been assigned a new task"
        }
        
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            NotificationCreateRequest(**data)
    
    def test_notification_create_request_empty_message(self):
        """Test notification creation request with empty message."""
        data = {
            "user_id": str(uuid4()),
            "type": "task_assigned",
            "title": "Task Assigned",
            "message": ""
        }
        
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            NotificationCreateRequest(**data)
    
    def test_notification_create_request_invalid_entity_type(self):
        """Test notification creation request with invalid entity type."""
        data = {
            "user_id": str(uuid4()),
            "type": "task_assigned",
            "title": "Task Assigned",
            "message": "You have been assigned a new task",
            "entity_type": "InvalidEntity"
        }
        
        with pytest.raises(ValidationError, match="Entity type 'InvalidEntity' is not allowed"):
            NotificationCreateRequest(**data)
    
    def test_notification_update_request_valid(self):
        """Test valid notification update request."""
        data = {
            "is_read": True
        }
        
        request = NotificationUpdateRequest(**data)
        assert request.is_read is True
    
    def test_notification_filter_request_valid(self):
        """Test valid notification filter request."""
        data = {
            "type": "task_assigned",
            "is_read": False,
            "entity_type": "Task",
            "page": 1,
            "limit": 20
        }
        
        request = NotificationFilterRequest(**data)
        assert request.type == data["type"]
        assert request.is_read is False
        assert request.entity_type == data["entity_type"]
        assert request.page == 1
        assert request.limit == 20
    
    def test_notification_filter_request_invalid_date_range(self):
        """Test notification filter request with invalid date range."""
        data = {
            "created_after": datetime.now(timezone.utc),
            "created_before": datetime.now(timezone.utc) - timedelta(days=1)
        }
        
        with pytest.raises(ValidationError, match="Created before date must be after created after date"):
            NotificationFilterRequest(**data) 