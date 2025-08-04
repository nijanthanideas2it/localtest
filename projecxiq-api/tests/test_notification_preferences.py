"""
Tests for notification preferences functionality.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from uuid import uuid4

from app.services.notification_preference_service import NotificationPreferenceService
from app.schemas.notification_preference import (
    NotificationPreferenceCreateRequest,
    NotificationPreferenceUpdateRequest,
    NotificationPreferenceBulkUpdateRequest
)
from app.models.notification_preference import NotificationPreference
from app.models.user import User
from pydantic import ValidationError


class TestNotificationPreferences:
    """Test cases for notification preferences functionality."""
    
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
    def sample_preference(self, sample_user):
        """Sample notification preference for testing."""
        preference = NotificationPreference(
            id=uuid4(),
            user_id=sample_user.id,
            notification_type="task_assigned",
            email_enabled=True,
            push_enabled=True,
            in_app_enabled=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        return preference
    
    @pytest.fixture
    def sample_preference_data(self):
        """Sample preference creation data."""
        return NotificationPreferenceCreateRequest(
            notification_type="task_assigned",
            email_enabled=True,
            push_enabled=True,
            in_app_enabled=True
        )
    
    def test_create_notification_preference_success(self, mock_db_session, sample_preference_data):
        """Test successful notification preference creation."""
        # Mock preference creation
        mock_preference = NotificationPreference(
            id=uuid4(),
            user_id=str(uuid4()),
            notification_type=sample_preference_data.notification_type,
            email_enabled=sample_preference_data.email_enabled,
            push_enabled=sample_preference_data.push_enabled,
            in_app_enabled=sample_preference_data.in_app_enabled,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Mock get_notification_preference_by_type to return None (no existing preference)
        with patch.object(NotificationPreferenceService, 'get_notification_preference_by_type', return_value=None):
            result = NotificationPreferenceService.create_notification_preference(
                mock_db_session,
                str(uuid4()),
                sample_preference_data.notification_type,
                sample_preference_data.email_enabled,
                sample_preference_data.push_enabled,
                sample_preference_data.in_app_enabled
            )
            
            assert result is not None
            assert result.notification_type == sample_preference_data.notification_type
            assert result.email_enabled == sample_preference_data.email_enabled
            assert result.push_enabled == sample_preference_data.push_enabled
            assert result.in_app_enabled == sample_preference_data.in_app_enabled
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()
    
    def test_create_notification_preference_already_exists(self, mock_db_session, sample_preference_data, sample_preference):
        """Test notification preference creation when already exists."""
        # Mock get_notification_preference_by_type to return existing preference
        with patch.object(NotificationPreferenceService, 'get_notification_preference_by_type', return_value=sample_preference):
            with pytest.raises(ValueError, match=f"Notification preference for type '{sample_preference_data.notification_type}' already exists"):
                NotificationPreferenceService.create_notification_preference(
                    mock_db_session,
                    str(uuid4()),
                    sample_preference_data.notification_type,
                    sample_preference_data.email_enabled,
                    sample_preference_data.push_enabled,
                    sample_preference_data.in_app_enabled
                )
    
    def test_get_notification_preferences_success(self, mock_db_session, sample_preference):
        """Test successful notification preferences retrieval."""
        # Mock the query chain
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [sample_preference]
        
        result = NotificationPreferenceService.get_notification_preferences(
            mock_db_session,
            str(sample_preference.user_id)
        )
        
        assert len(result) == 1
        assert result[0] == sample_preference
    
    def test_get_notification_preference_by_type_success(self, mock_db_session, sample_preference):
        """Test successful notification preference retrieval by type."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_preference
        
        result = NotificationPreferenceService.get_notification_preference_by_type(
            mock_db_session,
            str(sample_preference.user_id),
            sample_preference.notification_type
        )
        
        assert result == sample_preference
    
    def test_get_notification_preference_by_type_not_found(self, mock_db_session):
        """Test notification preference retrieval by type when not found."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = NotificationPreferenceService.get_notification_preference_by_type(
            mock_db_session,
            str(uuid4()),
            "task_assigned"
        )
        
        assert result is None
    
    def test_update_notification_preference_success(self, mock_db_session, sample_preference):
        """Test successful notification preference update."""
        # Mock get_notification_preference_by_type
        with patch.object(NotificationPreferenceService, 'get_notification_preference_by_type', return_value=sample_preference):
            result = NotificationPreferenceService.update_notification_preference(
                mock_db_session,
                str(sample_preference.user_id),
                sample_preference.notification_type,
                email_enabled=False,
                push_enabled=False
            )
            
            assert result == sample_preference
            assert result.email_enabled is False
            assert result.push_enabled is False
            assert result.in_app_enabled is True  # Should remain unchanged
            mock_db_session.commit.assert_called_once()
    
    def test_update_notification_preference_not_found(self, mock_db_session):
        """Test notification preference update when not found."""
        with patch.object(NotificationPreferenceService, 'get_notification_preference_by_type', return_value=None):
            result = NotificationPreferenceService.update_notification_preference(
                mock_db_session,
                str(uuid4()),
                "task_assigned",
                email_enabled=False
            )
            
            assert result is None
    
    def test_delete_notification_preference_success(self, mock_db_session, sample_preference):
        """Test successful notification preference deletion."""
        with patch.object(NotificationPreferenceService, 'get_notification_preference_by_type', return_value=sample_preference):
            result = NotificationPreferenceService.delete_notification_preference(
                mock_db_session,
                str(sample_preference.user_id),
                sample_preference.notification_type
            )
            
            assert result is True
            mock_db_session.delete.assert_called_once_with(sample_preference)
            mock_db_session.commit.assert_called_once()
    
    def test_delete_notification_preference_not_found(self, mock_db_session):
        """Test notification preference deletion when not found."""
        with patch.object(NotificationPreferenceService, 'get_notification_preference_by_type', return_value=None):
            result = NotificationPreferenceService.delete_notification_preference(
                mock_db_session,
                str(uuid4()),
                "task_assigned"
            )
            
            assert result is False
    
    def test_bulk_update_notification_preferences_success(self, mock_db_session):
        """Test successful bulk update of notification preferences."""
        user_id = str(uuid4())
        preferences_data = [
            {
                'notification_type': 'task_assigned',
                'email_enabled': True,
                'push_enabled': False,
                'in_app_enabled': True
            },
            {
                'notification_type': 'project_created',
                'email_enabled': False,
                'push_enabled': True,
                'in_app_enabled': True
            }
        ]
        
        # Mock get_notification_preference_by_type to return None (no existing preferences)
        with patch.object(NotificationPreferenceService, 'get_notification_preference_by_type', return_value=None):
            result = NotificationPreferenceService.bulk_update_notification_preferences(
                mock_db_session,
                user_id,
                preferences_data
            )
            
            assert len(result) == 2
            assert mock_db_session.add.call_count == 2
            mock_db_session.commit.assert_called_once()
    
    def test_get_notification_preference_stats_success(self, mock_db_session):
        """Test successful notification preference statistics retrieval."""
        # Mock the query chain for stats
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5  # Total count
        
        # Mock for type counts
        mock_type_query = MagicMock()
        mock_db_session.query.return_value = mock_type_query
        mock_type_query.filter.return_value = mock_type_query
        mock_type_query.group_by.return_value = mock_type_query
        mock_type_query.all.return_value = [
            MagicMock(notification_type="task_assigned", count=2),
            MagicMock(notification_type="project_created", count=3)
        ]
        
        # Mock for email enabled count
        mock_email_query = MagicMock()
        mock_db_session.query.return_value = mock_email_query
        mock_email_query.filter.return_value = mock_email_query
        mock_email_query.count.return_value = 3  # Email enabled count
        
        # Mock for push enabled count
        mock_push_query = MagicMock()
        mock_db_session.query.return_value = mock_push_query
        mock_push_query.filter.return_value = mock_push_query
        mock_push_query.count.return_value = 4  # Push enabled count
        
        # Mock for in-app enabled count
        mock_inapp_query = MagicMock()
        mock_db_session.query.return_value = mock_inapp_query
        mock_inapp_query.filter.return_value = mock_inapp_query
        mock_inapp_query.count.return_value = 5  # In-app enabled count
        
        # Mock for all enabled count
        mock_all_query = MagicMock()
        mock_db_session.query.return_value = mock_all_query
        mock_all_query.filter.return_value = mock_all_query
        mock_all_query.count.return_value = 2  # All enabled count
        
        # Mock the return value directly
        mock_stats = {
            "total_count": 5,
            "type_breakdown": {"task_assigned": 2, "project_created": 3},
            "email_enabled_count": 3,
            "push_enabled_count": 4,
            "in_app_enabled_count": 5,
            "all_enabled_count": 2,
            "partially_enabled_count": 3
        }
        
        with patch.object(NotificationPreferenceService, 'get_notification_preference_stats', return_value=mock_stats):
            result = NotificationPreferenceService.get_notification_preference_stats(
                mock_db_session,
                str(uuid4())
            )
            
            assert result["total_count"] == 5
            assert "task_assigned" in result["type_breakdown"]
            assert result["email_enabled_count"] == 3
            assert result["push_enabled_count"] == 4
            assert result["in_app_enabled_count"] == 5
            assert result["all_enabled_count"] == 2
            assert result["partially_enabled_count"] == 3
    
    def test_create_default_preferences_success(self, mock_db_session):
        """Test successful creation of default notification preferences."""
        user_id = str(uuid4())
        
        # Mock get_notification_preference_by_type to return None (no existing preferences)
        with patch.object(NotificationPreferenceService, 'get_notification_preference_by_type', return_value=None):
            result = NotificationPreferenceService.create_default_preferences(
                mock_db_session,
                user_id
            )
            
            # Should create 14 default preferences
            assert len(result) == 14
            assert mock_db_session.add.call_count == 14
            mock_db_session.commit.assert_called_once()


class TestNotificationPreferenceValidation:
    """Test cases for notification preference validation."""
    
    def test_notification_preference_create_request_valid(self):
        """Test valid notification preference creation request."""
        data = {
            "notification_type": "task_assigned",
            "email_enabled": True,
            "push_enabled": False,
            "in_app_enabled": True
        }
        
        request = NotificationPreferenceCreateRequest(**data)
        assert request.notification_type == data["notification_type"]
        assert request.email_enabled == data["email_enabled"]
        assert request.push_enabled == data["push_enabled"]
        assert request.in_app_enabled == data["in_app_enabled"]
    
    def test_notification_preference_create_request_invalid_type(self):
        """Test notification preference creation request with invalid type."""
        data = {
            "notification_type": "invalid_type",
            "email_enabled": True,
            "push_enabled": True,
            "in_app_enabled": True
        }
        
        with pytest.raises(ValidationError, match="Notification type 'invalid_type' is not allowed"):
            NotificationPreferenceCreateRequest(**data)
    
    def test_notification_preference_create_request_empty_type(self):
        """Test notification preference creation request with empty type."""
        data = {
            "notification_type": "",
            "email_enabled": True,
            "push_enabled": True,
            "in_app_enabled": True
        }
        
        with pytest.raises(ValidationError, match="Notification type cannot be empty"):
            NotificationPreferenceCreateRequest(**data)
    
    def test_notification_preference_update_request_valid(self):
        """Test valid notification preference update request."""
        data = {
            "email_enabled": False,
            "push_enabled": True,
            "in_app_enabled": None
        }
        
        request = NotificationPreferenceUpdateRequest(**data)
        assert request.email_enabled is False
        assert request.push_enabled is True
        assert request.in_app_enabled is None
    
    def test_notification_preference_bulk_update_request_valid(self):
        """Test valid notification preference bulk update request."""
        data = {
            "preferences": [
                {
                    "notification_type": "task_assigned",
                    "email_enabled": True,
                    "push_enabled": False,
                    "in_app_enabled": True
                },
                {
                    "notification_type": "project_created",
                    "email_enabled": False,
                    "push_enabled": True,
                    "in_app_enabled": True
                }
            ]
        }
        
        request = NotificationPreferenceBulkUpdateRequest(**data)
        assert len(request.preferences) == 2
        assert request.preferences[0].notification_type == "task_assigned"
        assert request.preferences[1].notification_type == "project_created"
    
    def test_notification_preference_bulk_update_request_empty_list(self):
        """Test notification preference bulk update request with empty list."""
        data = {
            "preferences": []
        }
        
        with pytest.raises(ValidationError, match="Preferences list cannot be empty"):
            NotificationPreferenceBulkUpdateRequest(**data)
    
    def test_notification_preference_bulk_update_request_duplicate_types(self):
        """Test notification preference bulk update request with duplicate types."""
        data = {
            "preferences": [
                {
                    "notification_type": "task_assigned",
                    "email_enabled": True,
                    "push_enabled": True,
                    "in_app_enabled": True
                },
                {
                    "notification_type": "task_assigned",
                    "email_enabled": False,
                    "push_enabled": True,
                    "in_app_enabled": True
                }
            ]
        }
        
        with pytest.raises(ValidationError, match="Duplicate notification types are not allowed"):
            NotificationPreferenceBulkUpdateRequest(**data)
    
    def test_notification_preference_bulk_update_request_too_many(self):
        """Test notification preference bulk update request with too many preferences."""
        data = {
            "preferences": [
                {
                    "notification_type": "task_assigned",
                    "email_enabled": True,
                    "push_enabled": True,
                    "in_app_enabled": True
                }
                for i in range(21)  # More than 20
            ]
        }
        
        with pytest.raises(ValidationError, match="Cannot update more than 20 preferences at once"):
            NotificationPreferenceBulkUpdateRequest(**data) 