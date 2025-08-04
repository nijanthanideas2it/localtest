"""
Unit tests for profile service layer.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import tempfile
import shutil

from app.services.user_service import UserService
from app.services.file_service import FileService
from app.schemas.profile import ProfileUpdateRequest
from app.models.user import User
from app.core.auth import AuthUtils


class TestProfileService:
    """Test cases for profile service functionality."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return MagicMock()
    
    @pytest.fixture
    def sample_user(self):
        """Sample user object."""
        return User(
            id="test-user-id",
            email="test@example.com",
            password_hash=AuthUtils.get_password_hash("SecurePass123!"),
            first_name="Test",
            last_name="User",
            role="Developer",
            hourly_rate=50.0,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
    
    @pytest.fixture
    def sample_profile_data(self):
        """Sample profile update data."""
        return ProfileUpdateRequest(
            first_name="Updated",
            last_name="Name",
            hourly_rate=75.0,
            bio="Test bio",
            phone="+1234567890",
            location="Test City",
            website="https://example.com",
            linkedin="https://linkedin.com/in/test",
            github="https://github.com/test",
            twitter="https://twitter.com/test"
        )
    
    @pytest.fixture
    def temp_upload_dir(self):
        """Temporary upload directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_update_user_profile_success(self, mock_db_session, sample_user, sample_profile_data):
        """Test successful profile update."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_user
        
        result = UserService.update_user_profile(mock_db_session, "test-user-id", sample_profile_data)
        
        assert result == sample_user
        assert sample_user.first_name == "Updated"
        assert sample_user.last_name == "Name"
        assert sample_user.hourly_rate == 75.0
        assert sample_user.bio == "Test bio"
        assert sample_user.phone == "+1234567890"
        assert sample_user.location == "Test City"
        assert sample_user.website == "https://example.com"
        assert sample_user.linkedin == "https://linkedin.com/in/test"
        assert sample_user.github == "https://github.com/test"
        assert sample_user.twitter == "https://twitter.com/test"
        assert sample_user.updated_at is not None
        
        # Verify database operations
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    def test_update_user_profile_user_not_found(self, mock_db_session, sample_profile_data):
        """Test profile update when user not found."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = UserService.update_user_profile(mock_db_session, "non-existent-id", sample_profile_data)
        
        assert result is None
    
    def test_update_user_avatar_success(self, mock_db_session, sample_user):
        """Test successful avatar update."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_user
        
        # Mock file service
        with patch('app.services.file_service.FileService.delete_avatar') as mock_delete:
            result = UserService.update_user_avatar(mock_db_session, "test-user-id", "new_avatar.jpg")
        
        assert result == sample_user
        assert sample_user.avatar_url == "new_avatar.jpg"
        assert sample_user.updated_at is not None
        
        # Verify database operations
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    def test_update_user_avatar_with_existing_avatar(self, mock_db_session, sample_user):
        """Test avatar update when user already has an avatar."""
        sample_user.avatar_url = "old_avatar.jpg"
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_user
        
        # Mock file service
        with patch('app.services.file_service.FileService.delete_avatar') as mock_delete:
            result = UserService.update_user_avatar(mock_db_session, "test-user-id", "new_avatar.jpg")
        
        assert result == sample_user
        assert sample_user.avatar_url == "new_avatar.jpg"
        
        # Verify old avatar was deleted
        mock_delete.assert_called_once_with("old_avatar.jpg")
    
    def test_update_user_avatar_user_not_found(self, mock_db_session):
        """Test avatar update when user not found."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = UserService.update_user_avatar(mock_db_session, "non-existent-id", "new_avatar.jpg")
        
        assert result is None


class TestFileService:
    """Test cases for file service functionality."""
    
    @pytest.fixture
    def mock_upload_file(self):
        """Mock upload file."""
        mock_file = MagicMock()
        mock_file.filename = "test_avatar.jpg"
        mock_file.content_type = "image/jpeg"
        mock_file.size = 1024 * 1024  # 1MB
        return mock_file
    
    @pytest.fixture
    def temp_upload_dir(self):
        """Temporary upload directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_validate_image_file_valid(self, mock_upload_file):
        """Test valid image file validation."""
        is_valid, error_message = FileService.validate_image_file(mock_upload_file)
        
        assert is_valid is True
        assert error_message == ""
    
    def test_validate_image_file_invalid_type(self, mock_upload_file):
        """Test invalid file type validation."""
        mock_upload_file.content_type = "text/plain"
        
        is_valid, error_message = FileService.validate_image_file(mock_upload_file)
        
        assert is_valid is False
        assert "Invalid file type" in error_message
    
    def test_validate_image_file_too_large(self, mock_upload_file):
        """Test file size validation."""
        mock_upload_file.size = 10 * 1024 * 1024  # 10MB
        
        is_valid, error_message = FileService.validate_image_file(mock_upload_file)
        
        assert is_valid is False
        assert "File size exceeds" in error_message
    
    def test_validate_file_size_valid(self):
        """Test valid file size validation."""
        is_valid = FileService.validate_file_size(1024 * 1024, 5 * 1024 * 1024)
        assert is_valid is True
    
    def test_validate_file_size_invalid(self):
        """Test invalid file size validation."""
        is_valid = FileService.validate_file_size(10 * 1024 * 1024, 5 * 1024 * 1024)
        assert is_valid is False
    
    def test_get_file_extension(self):
        """Test file extension extraction."""
        extension = FileService.get_file_extension("test_image.jpg")
        assert extension == ".jpg"
        
        extension = FileService.get_file_extension("test_image.PNG")
        assert extension == ".png"
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        # Test unsafe characters
        sanitized = FileService.sanitize_filename("test<>file.jpg")
        assert sanitized == "test__file.jpg"
        
        # Test long filename
        long_filename = "a" * 200 + ".jpg"
        sanitized = FileService.sanitize_filename(long_filename)
        assert len(sanitized) <= 100
        assert sanitized.endswith(".jpg")
    
    def test_get_avatar_url(self):
        """Test avatar URL generation."""
        url = FileService.get_avatar_url("uploads/avatars/test.jpg")
        assert url == "/static/uploads/avatars/test.jpg"
        
        url = FileService.get_avatar_url("")
        assert url == ""
        
        url = FileService.get_avatar_url(None)
        assert url == ""
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.unlink')
    def test_delete_avatar_success(self, mock_unlink, mock_exists):
        """Test successful avatar deletion."""
        mock_exists.return_value = True
        
        result = FileService.delete_avatar("uploads/avatars/test.jpg")
        
        assert result is True
        mock_unlink.assert_called_once()
    
    @patch('pathlib.Path.exists')
    def test_delete_avatar_not_found(self, mock_exists):
        """Test avatar deletion when file doesn't exist."""
        mock_exists.return_value = False
        
        result = FileService.delete_avatar("uploads/avatars/test.jpg")
        
        assert result is False
    
    def test_delete_avatar_empty_path(self):
        """Test avatar deletion with empty path."""
        result = FileService.delete_avatar("")
        assert result is False
        
        result = FileService.delete_avatar(None)
        assert result is False
    
    @pytest.mark.asyncio
    @patch('aiofiles.open')
    @patch('PIL.Image.open')
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.unlink')
    async def test_save_avatar_success(self, mock_unlink, mock_exists, mock_mkdir, mock_pil_open, mock_aiofiles_open):
        """Test successful avatar save."""
        # Mock file operations
        mock_file = MagicMock()
        mock_file.filename = "test_avatar.jpg"
        mock_file.content_type = "image/jpeg"
        mock_file.size = 1024 * 1024
        
        # Mock async file operations
        mock_aiofiles_context = AsyncMock()
        mock_aiofiles_open.return_value.__aenter__.return_value = mock_aiofiles_context
        
        # Mock PIL image operations
        mock_image = MagicMock()
        mock_image.mode = "RGB"
        mock_pil_open.return_value.__enter__.return_value = mock_image
        
        # Mock path operations
        mock_exists.return_value = False
        
        result = await FileService.save_avatar(mock_file, "test-user-id")
        
        assert result.startswith("uploads/avatars/")
        assert result.endswith(".jpg")
        assert "test-user-id" in result
        
        # Verify operations were called
        mock_mkdir.assert_called_once()
        mock_aiofiles_open.assert_called_once()
        mock_pil_open.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('aiofiles.open')
    @patch('pathlib.Path.mkdir')
    async def test_save_avatar_invalid_file(self, mock_mkdir, mock_aiofiles_open):
        """Test avatar save with invalid file."""
        # Mock file with invalid type
        mock_file = MagicMock()
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"
        mock_file.size = 1024
        
        with pytest.raises(Exception):
            await FileService.save_avatar(mock_file, "test-user-id")
    
    @pytest.mark.asyncio
    @patch('aiofiles.open')
    @patch('pathlib.Path.mkdir')
    async def test_save_avatar_file_too_large(self, mock_mkdir, mock_aiofiles_open):
        """Test avatar save with file too large."""
        # Mock file with large size
        mock_file = MagicMock()
        mock_file.filename = "test_avatar.jpg"
        mock_file.content_type = "image/jpeg"
        mock_file.size = 10 * 1024 * 1024  # 10MB
        
        with pytest.raises(Exception):
            await FileService.save_avatar(mock_file, "test-user-id") 