"""
Unit tests for file upload system functionality.
"""
import pytest
import os
import tempfile
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from pathlib import Path

from app.main import app
from app.services.file_service import FileService
from app.models.file import File
from app.models.user import User
from app.schemas.file import FileUploadRequest, FileUpdateRequest, FileFilterRequest
from app.core.auth import AuthUtils

client = TestClient(app)


class TestFileService:
    """Test cases for file service functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=Session)
        self.mock_user = Mock(spec=User)
        self.mock_user.id = "user-123"
        self.mock_user.name = "Test User"
        self.mock_user.role = "User"
        
        self.mock_file = Mock(spec=File)
        self.mock_file.id = "file-123"
        self.mock_file.file_name = "test_file.txt"
        self.mock_file.original_name = "test_file.txt"
        self.mock_file.file_path = "uploads/files/test_file.txt"
        self.mock_file.file_size = 1024
        self.mock_file.mime_type = "text/plain"
        self.mock_file.description = "Test file"
        self.mock_file.is_public = False
        self.mock_file.is_deleted = False
        self.mock_file.uploaded_by = "user-123"
        self.mock_file.created_at = datetime.now(timezone.utc)
        self.mock_file.updated_at = datetime.now(timezone.utc)
        
        # Mock file properties
        self.mock_file.file_extension = "txt"
        self.mock_file.is_image = False
        self.mock_file.is_document = True
        self.mock_file.is_archive = False
        self.mock_file.human_readable_size = "1.0 KB"
    
    def test_validate_general_file_valid(self):
        """Test validating a valid general file."""
        mock_upload_file = Mock()
        mock_upload_file.size = 1024 * 1024  # 1MB
        mock_upload_file.content_type = "text/plain"
        
        is_valid, error_message = FileService.validate_general_file(mock_upload_file)
        
        assert is_valid is True
        assert error_message == ""
    
    def test_validate_general_file_too_large(self):
        """Test validating a file that's too large."""
        mock_upload_file = Mock()
        mock_upload_file.size = 100 * 1024 * 1024  # 100MB
        mock_upload_file.content_type = "text/plain"
        
        is_valid, error_message = FileService.validate_general_file(mock_upload_file)
        
        assert is_valid is False
        assert "File size exceeds maximum limit" in error_message
    
    def test_validate_general_file_invalid_type(self):
        """Test validating a file with invalid type."""
        mock_upload_file = Mock()
        mock_upload_file.size = 1024 * 1024  # 1MB
        mock_upload_file.content_type = "application/executable"
        
        is_valid, error_message = FileService.validate_general_file(mock_upload_file)
        
        assert is_valid is False
        assert "Invalid file type" in error_message
    
    def test_get_file_by_id_found(self):
        """Test getting file by ID when found."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = self.mock_file
        self.mock_db.query.return_value = mock_query
        
        result = FileService.get_file_by_id(self.mock_db, "file-123")
        
        assert result == self.mock_file
    
    def test_get_file_by_id_not_found(self):
        """Test getting file by ID when not found."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        result = FileService.get_file_by_id(self.mock_db, "file-123")
        
        assert result is None
    
    def test_get_files_with_pagination(self):
        """Test getting files with pagination."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [self.mock_file]
        self.mock_db.query.return_value = mock_query
        
        files, total_count = FileService.get_files(self.mock_db, page=1, page_size=10)
        
        assert len(files) == 1
        assert total_count == 1
        assert files[0] == self.mock_file
    
    def test_get_files_with_filtering(self):
        """Test getting files with filtering."""
        filter_request = FileFilterRequest(
            mime_type="text/plain",
            uploaded_by="user-123",
            is_public=False,
            search="test"
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [self.mock_file]
        self.mock_db.query.return_value = mock_query
        
        files, total_count = FileService.get_files(
            self.mock_db, 
            page=1, 
            page_size=10, 
            filter_request=filter_request
        )
        
        assert len(files) == 1
        assert total_count == 1
    
    def test_update_file_success(self):
        """Test updating file metadata successfully."""
        update_request = FileUpdateRequest(
            description="Updated description",
            is_public=True
        )
        
        # Mock get_file_by_id
        with patch.object(FileService, 'get_file_by_id', return_value=self.mock_file):
            result = FileService.update_file(self.mock_db, "file-123", update_request)
            
            assert result == self.mock_file
            assert self.mock_file.description == "Updated description"
            assert self.mock_file.is_public is True
            self.mock_db.commit.assert_called_once()
            self.mock_db.refresh.assert_called_once_with(self.mock_file)
    
    def test_update_file_not_found(self):
        """Test updating file that doesn't exist."""
        update_request = FileUpdateRequest(description="Updated description")
        
        with patch.object(FileService, 'get_file_by_id', return_value=None):
            result = FileService.update_file(self.mock_db, "file-123", update_request)
            
            assert result is None
    
    def test_delete_file_success(self):
        """Test soft deleting a file successfully."""
        with patch.object(FileService, 'get_file_by_id', return_value=self.mock_file):
            result = FileService.delete_file(self.mock_db, "file-123")
            
            assert result is True
            assert self.mock_file.is_deleted is True
            self.mock_db.commit.assert_called_once()
    
    def test_delete_file_not_found(self):
        """Test deleting a file that doesn't exist."""
        with patch.object(FileService, 'get_file_by_id', return_value=None):
            result = FileService.delete_file(self.mock_db, "file-123")
            
            assert result is False
    
    def test_hard_delete_file_success(self):
        """Test hard deleting a file successfully."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = self.mock_file
        self.mock_db.query.return_value = mock_query
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.unlink'):
                result = FileService.hard_delete_file(self.mock_db, "file-123")
                
                assert result is True
                self.mock_db.delete.assert_called_once_with(self.mock_file)
                self.mock_db.commit.assert_called_once()
    
    def test_get_file_stats(self):
        """Test getting file statistics."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.side_effect = [5, 1024 * 1024]  # 5 files, 1MB total
        
        # Mock group by queries
        mock_group_query = Mock()
        mock_group_query.group_by.return_value = mock_group_query
        mock_group_query.all.return_value = [("text/plain", 3), ("image/jpeg", 2)]
        
        self.mock_db.query.side_effect = [mock_query, mock_group_query, mock_group_query, mock_query]
        
        stats = FileService.get_file_stats(self.mock_db)
        
        assert stats["total_files"] == 5
        assert stats["total_size"] == 1024 * 1024
        assert stats["files_by_type"] == {"text/plain": 3, "image/jpeg": 2}
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        # Test unsafe characters
        unsafe_filename = "file<>:\"/\\|?*.txt"
        sanitized = FileService.sanitize_filename(unsafe_filename)
        assert sanitized == "file_______.txt"
        
        # Test long filename
        long_filename = "a" * 300 + ".txt"
        sanitized = FileService.sanitize_filename(long_filename)
        assert len(sanitized) <= 255
    
    def test_get_file_extension(self):
        """Test getting file extension."""
        # Test with extension
        extension = FileService.get_file_extension("test.txt")
        assert extension == "txt"
        
        # Test without extension
        extension = FileService.get_file_extension("test")
        assert extension == ""
        
        # Test with multiple dots
        extension = FileService.get_file_extension("test.backup.txt")
        assert extension == "txt"


class TestFileAPI:
    """Test cases for file API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_user = {
            "id": "user-123",
            "email": "test@example.com",
            "name": "Test User",
            "role": "User"
        }
        
        # Create access token
        self.access_token = AuthUtils.create_access_token(data={"sub": self.test_user["email"]})
        self.headers = {"Authorization": f"Bearer {self.access_token}"}
    
    @patch('app.api.files.FileService.upload_file')
    def test_upload_file_success(self, mock_upload_file):
        """Test successful file upload."""
        # Mock the service response
        mock_file_record = Mock(spec=File)
        mock_file_record.id = "file-123"
        mock_upload_file.return_value = mock_file_record
        
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp_file:
            temp_file.write(b"test content")
            temp_file.flush()
            
            with open(temp_file.name, 'rb') as f:
                response = client.post(
                    "/files/upload",
                    headers=self.headers,
                    files={"file": ("test.txt", f, "text/plain")},
                    data={"description": "Test file", "is_public": "false"}
                )
        
        # Clean up
        os.unlink(temp_file.name)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "File uploaded successfully"
        assert data["file"]["id"] == "file-123"
        assert "download_url" in data
    
    def test_upload_file_unauthorized(self):
        """Test file upload without authentication."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp_file:
            temp_file.write(b"test content")
            temp_file.flush()
            
            with open(temp_file.name, 'rb') as f:
                response = client.post(
                    "/files/upload",
                    files={"file": ("test.txt", f, "text/plain")}
                )
        
        # Clean up
        os.unlink(temp_file.name)
        
        assert response.status_code == 401
    
    @patch('app.api.files.FileService.get_file_by_id')
    def test_get_file_success(self, mock_get_file):
        """Test getting file information successfully."""
        # Mock the service response
        mock_file_record = Mock(spec=File)
        mock_file_record.id = "file-123"
        mock_file_record.file_name = "test.txt"
        mock_file_record.original_name = "test.txt"
        mock_file_record.file_size = 1024
        mock_file_record.mime_type = "text/plain"
        mock_file_record.is_public = False
        mock_file_record.is_deleted = False
        mock_file_record.uploaded_by = "user-123"
        mock_file_record.created_at = datetime.now(timezone.utc)
        mock_file_record.updated_at = datetime.now(timezone.utc)
        
        # Mock properties
        mock_file_record.file_extension = "txt"
        mock_file_record.is_image = False
        mock_file_record.is_document = True
        mock_file_record.is_archive = False
        mock_file_record.human_readable_size = "1.0 KB"
        
        mock_get_file.return_value = mock_file_record
        
        response = client.get("/files/file-123", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "file-123"
        assert data["file_name"] == "test.txt"
    
    @patch('app.api.files.FileService.get_file_by_id')
    def test_get_file_not_found(self, mock_get_file):
        """Test getting file that doesn't exist."""
        mock_get_file.return_value = None
        
        response = client.get("/files/file-123", headers=self.headers)
        
        assert response.status_code == 404
        assert "File not found" in response.json()["detail"]
    
    @patch('app.api.files.FileService.get_file_by_id')
    def test_get_file_unauthorized(self, mock_get_file):
        """Test getting file without proper authorization."""
        # Mock file owned by different user
        mock_file_record = Mock(spec=File)
        mock_file_record.id = "file-123"
        mock_file_record.is_public = False
        mock_file_record.uploaded_by = "other-user-123"
        
        mock_get_file.return_value = mock_file_record
        
        response = client.get("/files/file-123", headers=self.headers)
        
        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]
    
    @patch('app.api.files.FileService.get_file_by_id')
    @patch('pathlib.Path.exists')
    def test_download_file_success(self, mock_exists, mock_get_file):
        """Test downloading file successfully."""
        # Mock file record
        mock_file_record = Mock(spec=File)
        mock_file_record.id = "file-123"
        mock_file_record.is_public = False
        mock_file_record.uploaded_by = "user-123"
        mock_file_record.file_path = "uploads/files/test.txt"
        mock_file_record.original_name = "test.txt"
        mock_file_record.mime_type = "text/plain"
        
        mock_get_file.return_value = mock_file_record
        mock_exists.return_value = True
        
        response = client.get("/files/file-123/download", headers=self.headers)
        
        assert response.status_code == 200
    
    @patch('app.api.files.FileService.get_file_by_id')
    def test_delete_file_success(self, mock_get_file):
        """Test deleting file successfully."""
        # Mock file record
        mock_file_record = Mock(spec=File)
        mock_file_record.id = "file-123"
        mock_file_record.uploaded_by = "user-123"
        
        mock_get_file.return_value = mock_file_record
        
        # Mock delete operation
        with patch.object(FileService, 'delete_file', return_value=True):
            response = client.delete("/files/file-123", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "File deleted successfully"
        assert data["file_id"] == "file-123"
    
    @patch('app.api.files.FileService.get_file_by_id')
    def test_delete_file_not_found(self, mock_get_file):
        """Test deleting file that doesn't exist."""
        mock_get_file.return_value = None
        
        response = client.delete("/files/file-123", headers=self.headers)
        
        assert response.status_code == 404
        assert "File not found" in response.json()["detail"]
    
    @patch('app.api.files.FileService.get_files')
    def test_list_files_success(self, mock_get_files):
        """Test listing files successfully."""
        # Mock service response
        mock_file_record = Mock(spec=File)
        mock_file_record.id = "file-123"
        mock_file_record.file_name = "test.txt"
        mock_file_record.is_public = False
        mock_file_record.uploaded_by = "user-123"
        
        mock_get_files.return_value = ([mock_file_record], 1)
        
        response = client.get("/files/list", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["files"]) == 1
        assert data["total_count"] == 1
        assert data["page"] == 1
        assert data["page_size"] == 10
    
    @patch('app.api.files.FileService.update_file')
    @patch('app.api.files.FileService.get_file_by_id')
    def test_update_file_success(self, mock_get_file, mock_update_file):
        """Test updating file successfully."""
        # Mock file record
        mock_file_record = Mock(spec=File)
        mock_file_record.id = "file-123"
        mock_file_record.uploaded_by = "user-123"
        
        mock_get_file.return_value = mock_file_record
        mock_update_file.return_value = mock_file_record
        
        update_data = {
            "description": "Updated description",
            "is_public": True
        }
        
        response = client.put("/files/file-123", headers=self.headers, json=update_data)
        
        assert response.status_code == 200
    
    @patch('app.api.files.FileService.get_file_stats')
    def test_get_file_stats_success(self, mock_get_stats):
        """Test getting file statistics successfully."""
        # Mock stats response
        mock_stats = {
            "total_files": 5,
            "total_size": 1024 * 1024,
            "files_by_type": {"text/plain": 3, "image/jpeg": 2},
            "files_by_uploader": {"user-123": 5},
            "recent_uploads": []
        }
        
        mock_get_stats.return_value = mock_stats
        
        response = client.get("/files/stats", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_files"] == 5
        assert data["total_size"] == 1024 * 1024


class TestFileValidation:
    """Test cases for file validation."""
    
    def test_file_upload_request_validation(self):
        """Test FileUploadRequest validation."""
        from app.schemas.file import FileUploadRequest
        
        # Valid request
        valid_request = FileUploadRequest(
            description="Test file",
            is_public=False
        )
        assert valid_request.description == "Test file"
        assert valid_request.is_public is False
        
        # Test description length validation
        with pytest.raises(ValueError, match="Description cannot exceed 1000 characters"):
            FileUploadRequest(
                description="a" * 1001,
                is_public=False
            )
    
    def test_file_update_request_validation(self):
        """Test FileUpdateRequest validation."""
        from app.schemas.file import FileUpdateRequest
        
        # Valid request
        valid_request = FileUpdateRequest(
            description="Updated description",
            is_public=True
        )
        assert valid_request.description == "Updated description"
        assert valid_request.is_public is True
        
        # Test description length validation
        with pytest.raises(ValueError, match="Description cannot exceed 1000 characters"):
            FileUpdateRequest(
                description="a" * 1001,
                is_public=True
            )
    
    def test_file_filter_request_validation(self):
        """Test FileFilterRequest validation."""
        from app.schemas.file import FileFilterRequest
        
        # Valid request
        valid_request = FileFilterRequest(
            mime_type="text/plain",
            uploaded_by="user-123",
            is_public=False,
            search="test"
        )
        assert valid_request.mime_type == "text/plain"
        assert valid_request.search == "test"
        
        # Test search term length validation
        with pytest.raises(ValueError, match="Search term cannot exceed 100 characters"):
            FileFilterRequest(
                search="a" * 101
            )
        
        # Test date range validation
        with pytest.raises(ValueError, match="End date must be after start date"):
            FileFilterRequest(
                date_from=datetime(2024, 1, 31),
                date_to=datetime(2024, 1, 1)
            )


class TestFileEdgeCases:
    """Test cases for file edge cases."""
    
    def test_file_with_special_characters(self):
        """Test file with special characters in filename."""
        filename = "file<>:\"/\\|?*.txt"
        sanitized = FileService.sanitize_filename(filename)
        assert sanitized == "file_______.txt"
    
    def test_file_without_extension(self):
        """Test file without extension."""
        extension = FileService.get_file_extension("testfile")
        assert extension == ""
    
    def test_file_with_multiple_extensions(self):
        """Test file with multiple extensions."""
        extension = FileService.get_file_extension("test.backup.txt")
        assert extension == "txt"
    
    def test_large_filename(self):
        """Test filename that's too long."""
        long_filename = "a" * 300 + ".txt"
        sanitized = FileService.sanitize_filename(long_filename)
        assert len(sanitized) <= 255
        assert sanitized.endswith(".txt")
    
    def test_empty_filename(self):
        """Test empty filename."""
        sanitized = FileService.sanitize_filename("")
        assert sanitized == ""
        
        extension = FileService.get_file_extension("")
        assert extension == "" 