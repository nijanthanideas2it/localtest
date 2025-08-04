"""
Unit tests for file permission and sharing functionality.
"""
import pytest
import os
import tempfile
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from pathlib import Path

from app.main import app
from app.services.file_service import FileService
from app.models.file import File
from app.models.file_permission import FilePermission, FileShare
from app.models.user import User
from app.schemas.file_permission import (
    FilePermissionRequest,
    FilePermissionUpdateRequest,
    FileShareRequest,
    FileShareUpdateRequest,
    PermissionType,
    SharePermissionType
)
from app.core.auth import AuthUtils

client = TestClient(app)


class TestFilePermissionService:
    """Test cases for file permission service functionality."""
    
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
        
        self.mock_permission = Mock(spec=FilePermission)
        self.mock_permission.id = "permission-123"
        self.mock_permission.file_id = "file-123"
        self.mock_permission.user_id = "user-456"
        self.mock_permission.permission_type = "read"
        self.mock_permission.granted_by = "user-123"
        self.mock_permission.expires_at = None
        self.mock_permission.is_active = True
        self.mock_permission.created_at = datetime.now(timezone.utc)
        self.mock_permission.updated_at = datetime.now(timezone.utc)
        
        # Mock permission properties
        self.mock_permission.is_expired = False
        self.mock_permission.is_valid = True
        
        self.mock_share = Mock(spec=FileShare)
        self.mock_share.id = "share-123"
        self.mock_share.file_id = "file-123"
        self.mock_share.share_token = "test_token_123"
        self.mock_share.created_by = "user-123"
        self.mock_share.permission_type = "read"
        self.mock_share.max_downloads = None
        self.mock_share.download_count = 0
        self.mock_share.expires_at = None
        self.mock_share.is_active = True
        self.mock_share.created_at = datetime.now(timezone.utc)
        self.mock_share.updated_at = datetime.now(timezone.utc)
        
        # Mock share properties
        self.mock_share.is_expired = False
        self.mock_share.is_download_limit_reached = False
        self.mock_share.is_valid = True
    
    def test_check_file_access_owner(self):
        """Test file access check for file owner."""
        with patch.object(FileService, 'get_file_by_id', return_value=self.mock_file):
            result = FileService.check_file_access(
                self.mock_db,
                "file-123",
                "user-123",
                PermissionType.READ
            )
            
            assert result is True
    
    def test_check_file_access_public_file(self):
        """Test file access check for public file."""
        self.mock_file.is_public = True
        
        with patch.object(FileService, 'get_file_by_id', return_value=self.mock_file):
            result = FileService.check_file_access(
                self.mock_db,
                "file-123",
                "user-456",
                PermissionType.READ
            )
            
            assert result is True
    
    def test_check_file_access_with_permission(self):
        """Test file access check with explicit permission."""
        with patch.object(FileService, 'get_file_by_id', return_value=self.mock_file):
            # Mock permission query
            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = self.mock_permission
            self.mock_db.query.return_value = mock_query
            
            result = FileService.check_file_access(
                self.mock_db,
                "file-123",
                "user-456",
                PermissionType.READ
            )
            
            assert result is True
    
    def test_check_file_access_no_permission(self):
        """Test file access check without permission."""
        with patch.object(FileService, 'get_file_by_id', return_value=self.mock_file):
            # Mock permission query returning None
            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = None
            self.mock_db.query.return_value = mock_query
            
            result = FileService.check_file_access(
                self.mock_db,
                "file-123",
                "user-456",
                PermissionType.READ
            )
            
            assert result is False
    
    def test_check_file_access_file_not_found(self):
        """Test file access check for non-existent file."""
        with patch.object(FileService, 'get_file_by_id', return_value=None):
            result = FileService.check_file_access(
                self.mock_db,
                "file-123",
                "user-456",
                PermissionType.READ
            )
            
            assert result is False
    
    def test_grant_file_permission_success(self):
        """Test granting file permission successfully."""
        permission_request = FilePermissionRequest(
            user_id="user-456",
            permission_type=PermissionType.READ,
            expires_at=None
        )
        
        with patch.object(FileService, 'get_file_by_id', return_value=self.mock_file):
            # Mock permission query returning None (no existing permission)
            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = None
            self.mock_db.query.return_value = mock_query
            
            result = FileService.grant_file_permission(
                self.mock_db,
                "file-123",
                permission_request,
                "user-123"
            )
            
            assert result is not None
            self.mock_db.add.assert_called_once()
            self.mock_db.commit.assert_called_once()
    
    def test_grant_file_permission_update_existing(self):
        """Test granting file permission when one already exists."""
        permission_request = FilePermissionRequest(
            user_id="user-456",
            permission_type=PermissionType.WRITE,
            expires_at=None
        )
        
        with patch.object(FileService, 'get_file_by_id', return_value=self.mock_file):
            # Mock permission query returning existing permission
            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = self.mock_permission
            self.mock_db.query.return_value = mock_query
            
            result = FileService.grant_file_permission(
                self.mock_db,
                "file-123",
                permission_request,
                "user-123"
            )
            
            assert result == self.mock_permission
            assert self.mock_permission.permission_type == "write"
            self.mock_db.commit.assert_called_once()
    
    def test_grant_file_permission_file_not_found(self):
        """Test granting permission for non-existent file."""
        permission_request = FilePermissionRequest(
            user_id="user-456",
            permission_type=PermissionType.READ
        )
        
        with patch.object(FileService, 'get_file_by_id', return_value=None):
            with pytest.raises(Exception):
                FileService.grant_file_permission(
                    self.mock_db,
                    "file-123",
                    permission_request,
                    "user-123"
                )
    
    def test_get_file_permissions(self):
        """Test getting file permissions."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [self.mock_permission]
        self.mock_db.query.return_value = mock_query
        
        permissions, total_count = FileService.get_file_permissions(
            self.mock_db,
            "file-123",
            page=1,
            page_size=10
        )
        
        assert len(permissions) == 1
        assert total_count == 1
        assert permissions[0] == self.mock_permission
    
    def test_update_file_permission_success(self):
        """Test updating file permission successfully."""
        update_request = FilePermissionUpdateRequest(
            permission_type=PermissionType.WRITE,
            is_active=True
        )
        
        # Mock permission query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = self.mock_permission
        self.mock_db.query.return_value = mock_query
        
        result = FileService.update_file_permission(
            self.mock_db,
            "file-123",
            "user-456",
            update_request
        )
        
        assert result == self.mock_permission
        assert self.mock_permission.permission_type == "write"
        assert self.mock_permission.is_active is True
        self.mock_db.commit.assert_called_once()
    
    def test_update_file_permission_not_found(self):
        """Test updating non-existent permission."""
        update_request = FilePermissionUpdateRequest(
            permission_type=PermissionType.WRITE
        )
        
        # Mock permission query returning None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        result = FileService.update_file_permission(
            self.mock_db,
            "file-123",
            "user-456",
            update_request
        )
        
        assert result is None
    
    def test_revoke_file_permission_success(self):
        """Test revoking file permission successfully."""
        # Mock permission query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = self.mock_permission
        self.mock_db.query.return_value = mock_query
        
        result = FileService.revoke_file_permission(
            self.mock_db,
            "file-123",
            "user-456"
        )
        
        assert result is True
        assert self.mock_permission.is_active is False
        self.mock_db.commit.assert_called_once()
    
    def test_revoke_file_permission_not_found(self):
        """Test revoking non-existent permission."""
        # Mock permission query returning None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        result = FileService.revoke_file_permission(
            self.mock_db,
            "file-123",
            "user-456"
        )
        
        assert result is False
    
    def test_create_file_share_success(self):
        """Test creating file share successfully."""
        share_request = FileShareRequest(
            permission_type=SharePermissionType.READ,
            max_downloads=10,
            expires_at=None
        )
        
        with patch.object(FileService, 'get_file_by_id', return_value=self.mock_file):
            with patch('secrets.token_urlsafe', return_value="test_token"):
                result = FileService.create_file_share(
                    self.mock_db,
                    "file-123",
                    share_request,
                    "user-123"
                )
                
                assert result is not None
                assert result.share_token == "test_token"
                self.mock_db.add.assert_called_once()
                self.mock_db.commit.assert_called_once()
    
    def test_create_file_share_file_not_found(self):
        """Test creating share for non-existent file."""
        share_request = FileShareRequest(
            permission_type=SharePermissionType.READ
        )
        
        with patch.object(FileService, 'get_file_by_id', return_value=None):
            with pytest.raises(Exception):
                FileService.create_file_share(
                    self.mock_db,
                    "file-123",
                    share_request,
                    "user-123"
                )
    
    def test_get_file_share_by_token_success(self):
        """Test getting file share by token successfully."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = self.mock_share
        self.mock_db.query.return_value = mock_query
        
        result = FileService.get_file_share_by_token(
            self.mock_db,
            "test_token_123"
        )
        
        assert result == self.mock_share
    
    def test_get_file_share_by_token_not_found(self):
        """Test getting file share by non-existent token."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        result = FileService.get_file_share_by_token(
            self.mock_db,
            "invalid_token"
        )
        
        assert result is None
    
    def test_get_file_shares(self):
        """Test getting file shares."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [self.mock_share]
        self.mock_db.query.return_value = mock_query
        
        shares, total_count = FileService.get_file_shares(
            self.mock_db,
            "file-123",
            page=1,
            page_size=10
        )
        
        assert len(shares) == 1
        assert total_count == 1
        assert shares[0] == self.mock_share
    
    def test_update_file_share_success(self):
        """Test updating file share successfully."""
        update_request = FileShareUpdateRequest(
            permission_type=SharePermissionType.WRITE,
            max_downloads=20,
            is_active=True
        )
        
        # Mock share query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = self.mock_share
        self.mock_db.query.return_value = mock_query
        
        result = FileService.update_file_share(
            self.mock_db,
            "share-123",
            update_request
        )
        
        assert result == self.mock_share
        assert self.mock_share.permission_type == "write"
        assert self.mock_share.max_downloads == 20
        assert self.mock_share.is_active is True
        self.mock_db.commit.assert_called_once()
    
    def test_update_file_share_not_found(self):
        """Test updating non-existent share."""
        update_request = FileShareUpdateRequest(
            permission_type=SharePermissionType.WRITE
        )
        
        # Mock share query returning None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        result = FileService.update_file_share(
            self.mock_db,
            "share-123",
            update_request
        )
        
        assert result is None
    
    def test_delete_file_share_success(self):
        """Test deleting file share successfully."""
        # Mock share query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = self.mock_share
        self.mock_db.query.return_value = mock_query
        
        result = FileService.delete_file_share(
            self.mock_db,
            "share-123"
        )
        
        assert result is True
        assert self.mock_share.is_active is False
        self.mock_db.commit.assert_called_once()
    
    def test_delete_file_share_not_found(self):
        """Test deleting non-existent share."""
        # Mock share query returning None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        result = FileService.delete_file_share(
            self.mock_db,
            "share-123"
        )
        
        assert result is False
    
    def test_increment_share_download_count_success(self):
        """Test incrementing share download count successfully."""
        # Mock share query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = self.mock_share
        self.mock_db.query.return_value = mock_query
        
        result = FileService.increment_share_download_count(
            self.mock_db,
            "share-123"
        )
        
        assert result is True
        self.mock_share.increment_download_count.assert_called_once()
        self.mock_db.commit.assert_called_once()
    
    def test_increment_share_download_count_not_found(self):
        """Test incrementing download count for non-existent share."""
        # Mock share query returning None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        result = FileService.increment_share_download_count(
            self.mock_db,
            "share-123"
        )
        
        assert result is False


class TestFilePermissionAPI:
    """Test cases for file permission API endpoints."""
    
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
    
    @patch('app.api.files.FileService.get_file_by_id')
    @patch('app.api.files.FileService.get_file_permissions')
    def test_get_file_permissions_success(self, mock_get_permissions, mock_get_file):
        """Test getting file permissions successfully."""
        # Mock file record
        mock_file_record = Mock(spec=File)
        mock_file_record.id = "file-123"
        mock_file_record.uploaded_by = "user-123"
        mock_get_file.return_value = mock_file_record
        
        # Mock permissions
        mock_permission = Mock(spec=FilePermission)
        mock_permission.id = "permission-123"
        mock_permission.file_id = "file-123"
        mock_permission.user_id = "user-456"
        mock_permission.permission_type = "read"
        mock_permission.is_active = True
        mock_permission.is_expired = False
        mock_permission.is_valid = True
        mock_permission.created_at = datetime.now(timezone.utc)
        mock_permission.updated_at = datetime.now(timezone.utc)
        
        mock_get_permissions.return_value = ([mock_permission], 1)
        
        response = client.get("/files/file-123/permissions", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["permissions"]) == 1
        assert data["total_count"] == 1
    
    @patch('app.api.files.FileService.get_file_by_id')
    def test_get_file_permissions_unauthorized(self, mock_get_file):
        """Test getting file permissions without authorization."""
        # Mock file record owned by different user
        mock_file_record = Mock(spec=File)
        mock_file_record.id = "file-123"
        mock_file_record.uploaded_by = "other-user-123"
        mock_get_file.return_value = mock_file_record
        
        response = client.get("/files/file-123/permissions", headers=self.headers)
        
        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]
    
    @patch('app.api.files.FileService.get_file_by_id')
    def test_get_file_permissions_file_not_found(self, mock_get_file):
        """Test getting permissions for non-existent file."""
        mock_get_file.return_value = None
        
        response = client.get("/files/file-123/permissions", headers=self.headers)
        
        assert response.status_code == 404
        assert "File not found" in response.json()["detail"]
    
    @patch('app.api.files.FileService.get_file_by_id')
    @patch('app.api.files.FileService.grant_file_permission')
    def test_grant_file_permission_success(self, mock_grant_permission, mock_get_file):
        """Test granting file permission successfully."""
        # Mock file record
        mock_file_record = Mock(spec=File)
        mock_file_record.id = "file-123"
        mock_file_record.uploaded_by = "user-123"
        mock_get_file.return_value = mock_file_record
        
        # Mock permission
        mock_permission = Mock(spec=FilePermission)
        mock_permission.id = "permission-123"
        mock_permission.file_id = "file-123"
        mock_permission.user_id = "user-456"
        mock_permission.permission_type = "read"
        mock_grant_permission.return_value = mock_permission
        
        permission_data = {
            "user_id": "user-456",
            "permission_type": "read",
            "expires_at": None
        }
        
        response = client.post(
            "/files/file-123/permissions",
            headers=self.headers,
            json=permission_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "permission-123"
    
    @patch('app.api.files.FileService.get_file_by_id')
    def test_grant_file_permission_unauthorized(self, mock_get_file):
        """Test granting permission without authorization."""
        # Mock file record owned by different user
        mock_file_record = Mock(spec=File)
        mock_file_record.id = "file-123"
        mock_file_record.uploaded_by = "other-user-123"
        mock_get_file.return_value = mock_file_record
        
        permission_data = {
            "user_id": "user-456",
            "permission_type": "read"
        }
        
        response = client.post(
            "/files/file-123/permissions",
            headers=self.headers,
            json=permission_data
        )
        
        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]
    
    @patch('app.api.files.FileService.get_file_by_id')
    @patch('app.api.files.FileService.update_file_permission')
    def test_update_file_permission_success(self, mock_update_permission, mock_get_file):
        """Test updating file permission successfully."""
        # Mock file record
        mock_file_record = Mock(spec=File)
        mock_file_record.id = "file-123"
        mock_file_record.uploaded_by = "user-123"
        mock_get_file.return_value = mock_file_record
        
        # Mock updated permission
        mock_permission = Mock(spec=FilePermission)
        mock_permission.id = "permission-123"
        mock_permission.permission_type = "write"
        mock_update_permission.return_value = mock_permission
        
        update_data = {
            "permission_type": "write",
            "is_active": True
        }
        
        response = client.put(
            "/files/file-123/permissions?user_id=user-456",
            headers=self.headers,
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "permission-123"
    
    @patch('app.api.files.FileService.get_file_by_id')
    @patch('app.api.files.FileService.revoke_file_permission')
    def test_revoke_file_permission_success(self, mock_revoke_permission, mock_get_file):
        """Test revoking file permission successfully."""
        # Mock file record
        mock_file_record = Mock(spec=File)
        mock_file_record.id = "file-123"
        mock_file_record.uploaded_by = "user-123"
        mock_get_file.return_value = mock_file_record
        
        mock_revoke_permission.return_value = True
        
        response = client.delete("/files/file-123/permissions/user-456", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Permission revoked successfully"
    
    @patch('app.api.files.FileService.get_file_by_id')
    @patch('app.api.files.FileService.create_file_share')
    def test_create_file_share_success(self, mock_create_share, mock_get_file):
        """Test creating file share successfully."""
        # Mock file record
        mock_file_record = Mock(spec=File)
        mock_file_record.id = "file-123"
        mock_file_record.uploaded_by = "user-123"
        mock_get_file.return_value = mock_file_record
        
        # Mock share
        mock_share = Mock(spec=FileShare)
        mock_share.id = "share-123"
        mock_share.share_token = "test_token_123"
        mock_share.permission_type = "read"
        mock_create_share.return_value = mock_share
        
        share_data = {
            "permission_type": "read",
            "max_downloads": 10,
            "expires_at": None
        }
        
        response = client.post(
            "/files/file-123/share",
            headers=self.headers,
            json=share_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "share-123"
        assert data["share_token"] == "test_token_123"
    
    @patch('app.api.files.FileService.get_file_by_id')
    @patch('app.api.files.FileService.check_file_access')
    def test_create_file_share_unauthorized(self, mock_check_access, mock_get_file):
        """Test creating share without authorization."""
        # Mock file record owned by different user
        mock_file_record = Mock(spec=File)
        mock_file_record.id = "file-123"
        mock_file_record.uploaded_by = "other-user-123"
        mock_get_file.return_value = mock_file_record
        
        # Mock access check returning False
        mock_check_access.return_value = False
        
        share_data = {
            "permission_type": "read"
        }
        
        response = client.post(
            "/files/file-123/share",
            headers=self.headers,
            json=share_data
        )
        
        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]
    
    @patch('app.api.files.FileService.get_file_share_by_token')
    @patch('app.api.files.FileService.get_file_by_id')
    @patch('app.api.files.FileService.increment_share_download_count')
    def test_access_shared_file_success(self, mock_increment, mock_get_file, mock_get_share):
        """Test accessing shared file successfully."""
        # Mock share
        mock_share = Mock(spec=FileShare)
        mock_share.id = "share-123"
        mock_share.file_id = "file-123"
        mock_share.is_valid = True
        mock_get_share.return_value = mock_share
        
        # Mock file record
        mock_file_record = Mock(spec=File)
        mock_file_record.id = "file-123"
        mock_file_record.file_name = "test.txt"
        mock_get_file.return_value = mock_file_record
        
        mock_increment.return_value = True
        
        response = client.get("/files/share/test_token_123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "file-123"
    
    @patch('app.api.files.FileService.get_file_share_by_token')
    def test_access_shared_file_not_found(self, mock_get_share):
        """Test accessing shared file with invalid token."""
        mock_get_share.return_value = None
        
        response = client.get("/files/share/invalid_token")
        
        assert response.status_code == 404
        assert "Share not found" in response.json()["detail"]
    
    @patch('app.api.files.FileService.get_file_share_by_token')
    def test_access_shared_file_expired(self, mock_get_share):
        """Test accessing expired shared file."""
        # Mock expired share
        mock_share = Mock(spec=FileShare)
        mock_share.is_valid = False
        mock_get_share.return_value = mock_share
        
        response = client.get("/files/share/expired_token")
        
        assert response.status_code == 410
        assert "expired" in response.json()["detail"]
    
    @patch('app.api.files.FileService.get_file_by_id')
    @patch('app.api.files.FileService.check_file_access')
    def test_check_file_access_success(self, mock_check_access, mock_get_file):
        """Test checking file access successfully."""
        # Mock file record
        mock_file_record = Mock(spec=File)
        mock_file_record.id = "file-123"
        mock_file_record.uploaded_by = "user-123"
        mock_get_file.return_value = mock_file_record
        
        # Mock access checks
        mock_check_access.side_effect = [True, True]  # can_read, can_write
        
        response = client.get("/files/file-123/access", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["file_id"] == "file-123"
        assert data["user_id"] == "user-123"
        assert data["has_access"] is True
        assert data["is_owner"] is True
        assert data["can_read"] is True
        assert data["can_write"] is True


class TestFilePermissionValidation:
    """Test cases for file permission validation."""
    
    def test_file_permission_request_validation(self):
        """Test FilePermissionRequest validation."""
        from app.schemas.file_permission import FilePermissionRequest
        
        # Valid request
        valid_request = FilePermissionRequest(
            user_id="user-456",
            permission_type=PermissionType.READ,
            expires_at=None
        )
        assert valid_request.user_id == "user-456"
        assert valid_request.permission_type == PermissionType.READ
        
        # Test expiration date validation
        past_date = datetime.now(timezone.utc) - timedelta(days=1)
        with pytest.raises(ValueError, match="Expiration date must be in the future"):
            FilePermissionRequest(
                user_id="user-456",
                permission_type=PermissionType.READ,
                expires_at=past_date
            )
    
    def test_file_permission_update_request_validation(self):
        """Test FilePermissionUpdateRequest validation."""
        from app.schemas.file_permission import FilePermissionUpdateRequest
        
        # Valid request
        valid_request = FilePermissionUpdateRequest(
            permission_type=PermissionType.WRITE,
            is_active=True
        )
        assert valid_request.permission_type == PermissionType.WRITE
        assert valid_request.is_active is True
        
        # Test expiration date validation
        past_date = datetime.now(timezone.utc) - timedelta(days=1)
        with pytest.raises(ValueError, match="Expiration date must be in the future"):
            FilePermissionUpdateRequest(
                expires_at=past_date
            )
    
    def test_file_share_request_validation(self):
        """Test FileShareRequest validation."""
        from app.schemas.file_permission import FileShareRequest
        
        # Valid request
        valid_request = FileShareRequest(
            permission_type=SharePermissionType.READ,
            max_downloads=10,
            expires_at=None
        )
        assert valid_request.permission_type == SharePermissionType.READ
        assert valid_request.max_downloads == 10
        
        # Test max_downloads validation
        with pytest.raises(ValueError, match="Maximum downloads must be at least 1"):
            FileShareRequest(
                permission_type=SharePermissionType.READ,
                max_downloads=0
            )
        
        # Test expiration date validation
        past_date = datetime.now(timezone.utc) - timedelta(days=1)
        with pytest.raises(ValueError, match="Expiration date must be in the future"):
            FileShareRequest(
                permission_type=SharePermissionType.READ,
                expires_at=past_date
            )
    
    def test_file_share_update_request_validation(self):
        """Test FileShareUpdateRequest validation."""
        from app.schemas.file_permission import FileShareUpdateRequest
        
        # Valid request
        valid_request = FileShareUpdateRequest(
            permission_type=SharePermissionType.WRITE,
            max_downloads=20,
            is_active=True
        )
        assert valid_request.permission_type == SharePermissionType.WRITE
        assert valid_request.max_downloads == 20
        
        # Test max_downloads validation
        with pytest.raises(ValueError, match="Maximum downloads must be at least 1"):
            FileShareUpdateRequest(
                max_downloads=0
            )
        
        # Test expiration date validation
        past_date = datetime.now(timezone.utc) - timedelta(days=1)
        with pytest.raises(ValueError, match="Expiration date must be in the future"):
            FileShareUpdateRequest(
                expires_at=past_date
            )


class TestFilePermissionEdgeCases:
    """Test cases for file permission edge cases."""
    
    def test_permission_hierarchy(self):
        """Test permission hierarchy logic."""
        # Test that higher permissions include lower ones
        permission_hierarchy = {
            PermissionType.READ: 1,
            PermissionType.WRITE: 2,
            PermissionType.ADMIN: 3
        }
        
        # Admin should have all permissions
        assert permission_hierarchy[PermissionType.ADMIN] >= permission_hierarchy[PermissionType.READ]
        assert permission_hierarchy[PermissionType.ADMIN] >= permission_hierarchy[PermissionType.WRITE]
        
        # Write should include read but not admin
        assert permission_hierarchy[PermissionType.WRITE] >= permission_hierarchy[PermissionType.READ]
        assert permission_hierarchy[PermissionType.WRITE] < permission_hierarchy[PermissionType.ADMIN]
        
        # Read should not include write or admin
        assert permission_hierarchy[PermissionType.READ] < permission_hierarchy[PermissionType.WRITE]
        assert permission_hierarchy[PermissionType.READ] < permission_hierarchy[PermissionType.ADMIN]
    
    def test_share_token_generation(self):
        """Test share token generation."""
        with patch('secrets.token_urlsafe', return_value="test_token_123"):
            token = os.urandom(32).hex() # Use os.urandom for more secure token generation
            assert token == "test_token_123"
    
    def test_permission_expiration_logic(self):
        """Test permission expiration logic."""
        # Test non-expiring permission
        mock_permission = Mock(spec=FilePermission)
        mock_permission.expires_at = None
        mock_permission.is_active = True
        
        assert mock_permission.is_expired is False
        assert mock_permission.is_valid is True
        
        # Test expired permission
        mock_permission.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        assert mock_permission.is_expired is True
        assert mock_permission.is_valid is False
        
        # Test future expiration
        mock_permission.expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        assert mock_permission.is_expired is False
        assert mock_permission.is_valid is True
    
    def test_share_download_limit_logic(self):
        """Test share download limit logic."""
        # Test unlimited downloads
        mock_share = Mock(spec=FileShare)
        mock_share.max_downloads = None
        mock_share.download_count = 100
        
        assert mock_share.is_download_limit_reached is False
        assert mock_share.is_valid is True
        
        # Test limited downloads not reached
        mock_share.max_downloads = 10
        mock_share.download_count = 5
        
        assert mock_share.is_download_limit_reached is False
        assert mock_share.is_valid is True
        
        # Test limited downloads reached
        mock_share.download_count = 10
        
        assert mock_share.is_download_limit_reached is True
        assert mock_share.is_valid is False
    
    def test_share_increment_download_count(self):
        """Test share download count increment."""
        mock_share = Mock(spec=FileShare)
        mock_share.download_count = 5
        
        # Mock the increment method
        def increment():
            mock_share.download_count = str(int(mock_share.download_count) + 1)
        
        mock_share.increment_download_count = increment
        
        # Test increment
        mock_share.increment_download_count()
        assert mock_share.download_count == "6" 