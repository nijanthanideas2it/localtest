"""
File service for handling file uploads and management.
"""
import os
import uuid
import mimetypes
import secrets
import shutil
from datetime import datetime, timezone
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path
import logging

from fastapi import UploadFile, HTTPException, status
from PIL import Image
import aiofiles
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc


from app.models.file import File
from app.models.file_permission import FilePermission, FileShare
from app.models.file_version import FileVersion
from app.models.user import User
from app.schemas.file import FileUploadRequest, FileUpdateRequest, FileFilterRequest
from app.schemas.file_permission import (
    FilePermissionRequest,
    FilePermissionUpdateRequest,
    FileShareRequest,
    FileShareUpdateRequest,
    PermissionType,
    SharePermissionType
)
from app.schemas.file_version import FileVersionRequest

logger = logging.getLogger(__name__)


class FileService:
    """Service class for file operations."""
    
    # Allowed image types for avatars
    ALLOWED_IMAGE_TYPES = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg", 
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp"
    }
    
    # Allowed file types for general uploads
    ALLOWED_FILE_TYPES = {
        # Images
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/svg+xml": ".svg",
        # Documents
        "application/pdf": ".pdf",
        "application/msword": ".doc",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "application/vnd.ms-excel": ".xls",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
        "text/plain": ".txt",
        "text/csv": ".csv",
        # Archives
        "application/zip": ".zip",
        "application/x-rar-compressed": ".rar",
        "application/x-7z-compressed": ".7z",
        "application/gzip": ".gz",
        "application/x-tar": ".tar"
    }
    
    # Maximum file sizes
    MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5MB for avatars
    MAX_FILE_SIZE = 50 * 1024 * 1024   # 50MB for general files
    
    # Avatar dimensions
    AVATAR_WIDTH = 200
    AVATAR_HEIGHT = 200
    
    @staticmethod
    def validate_image_file(file: UploadFile) -> Tuple[bool, str]:
        """
        Validate uploaded image file.
        
        Args:
            file: Uploaded file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file size
        if file.size and file.size > FileService.MAX_AVATAR_SIZE:
            return False, f"File size exceeds maximum limit of {FileService.MAX_AVATAR_SIZE // (1024*1024)}MB"
        
        # Check content type
        if file.content_type not in FileService.ALLOWED_IMAGE_TYPES:
            return False, f"Invalid file type. Allowed types: {', '.join(FileService.ALLOWED_IMAGE_TYPES.keys())}"
        
        return True, ""
    
    @staticmethod
    def validate_general_file(file: UploadFile) -> Tuple[bool, str]:
        """
        Validate uploaded general file.
        
        Args:
            file: Uploaded file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file size
        if file.size and file.size > FileService.MAX_FILE_SIZE:
            return False, f"File size exceeds maximum limit of {FileService.MAX_FILE_SIZE // (1024*1024)}MB"
        
        # Check content type
        if file.content_type not in FileService.ALLOWED_FILE_TYPES:
            return False, f"Invalid file type. Allowed types: {', '.join(FileService.ALLOWED_FILE_TYPES.keys())}"
        
        return True, ""
    
    @staticmethod
    async def save_avatar(file: UploadFile, user_id: str) -> str:
        """
        Save avatar file and return the file path.
        
        Args:
            file: Uploaded avatar file
            user_id: User ID for file naming
            
        Returns:
            File path relative to uploads directory
            
        Raises:
            HTTPException: If file processing fails
        """
        try:
            # Validate file
            is_valid, error_message = FileService.validate_image_file(file)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_message
                )
            
            # Create uploads directory if it doesn't exist
            uploads_dir = Path("uploads/avatars")
            uploads_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename
            file_extension = FileService.ALLOWED_IMAGE_TYPES[file.content_type]
            filename = f"{user_id}_{uuid.uuid4().hex}{file_extension}"
            file_path = uploads_dir / filename
            
            # Save file temporarily
            temp_path = uploads_dir / f"temp_{filename}"
            async with aiofiles.open(temp_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # Process image (resize and optimize)
            try:
                with Image.open(temp_path) as img:
                    # Convert to RGB if necessary
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    
                    # Resize image
                    img.thumbnail((FileService.AVATAR_WIDTH, FileService.AVATAR_HEIGHT), Image.Resampling.LANCZOS)
                    
                    # Save processed image
                    img.save(file_path, 'JPEG', quality=85, optimize=True)
                
                # Remove temporary file
                temp_path.unlink()
                
                return str(file_path)
                
            except Exception as e:
                # Clean up on error
                if temp_path.exists():
                    temp_path.unlink()
                if file_path.exists():
                    file_path.unlink()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to process image: {str(e)}"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save avatar: {str(e)}"
            )
    
    @staticmethod
    async def upload_file(
        db: Session,
        file: UploadFile,
        user_id: str,
        upload_request: FileUploadRequest
    ) -> File:
        """
        Upload a general file and save metadata to database.
        
        Args:
            db: Database session
            file: Uploaded file
            user_id: User ID who uploaded the file
            upload_request: Upload request parameters
            
        Returns:
            File object with metadata
            
        Raises:
            HTTPException: If upload fails
        """
        try:
            # Validate file
            is_valid, error_message = FileService.validate_general_file(file)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_message
                )
            
            # Create uploads directory if it doesn't exist
            uploads_dir = Path("uploads/files")
            uploads_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename
            file_extension = FileService.ALLOWED_FILE_TYPES.get(file.content_type, "")
            if not file_extension and '.' in file.filename:
                file_extension = '.' + file.filename.rsplit('.', 1)[1].lower()
            
            unique_filename = f"{uuid.uuid4().hex}{file_extension}"
            file_path = uploads_dir / unique_filename
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # Get file size
            file_size = file_path.stat().st_size
            
            # Create file record in database
            file_record = File(
                file_name=unique_filename,
                original_name=file.filename,
                file_path=str(file_path),
                file_size=file_size,
                mime_type=file.content_type,
                description=upload_request.description,
                uploaded_by=user_id,
                is_public=upload_request.is_public
            )
            
            db.add(file_record)
            db.commit()
            db.refresh(file_record)
            
            # Create initial version
            FileService.create_initial_version(db, file_record, user_id)
            
            return file_record
            
        except HTTPException:
            raise
        except Exception as e:
            # Clean up on error
            if 'file_path' in locals() and file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}"
            )
    
    @staticmethod
    def get_file_by_id(db: Session, file_id: str) -> Optional[File]:
        """
        Get file by ID.
        
        Args:
            db: Database session
            file_id: File ID
            
        Returns:
            File object or None if not found
        """
        return db.query(File).filter(
            and_(
                File.id == file_id,
                File.is_deleted == False
            )
        ).first()
    
    @staticmethod
    def get_files(
        db: Session,
        page: int = 1,
        page_size: int = 10,
        filter_request: Optional[FileFilterRequest] = None
    ) -> Tuple[List[File], int]:
        """
        Get files with pagination and filtering.
        
        Args:
            db: Database session
            page: Page number
            page_size: Page size
            filter_request: Optional filter parameters
            
        Returns:
            Tuple of (files, total_count)
        """
        query = db.query(File).filter(File.is_deleted == False)
        
        if filter_request:
            # Apply filters
            if filter_request.mime_type:
                query = query.filter(File.mime_type == filter_request.mime_type)
            
            if filter_request.uploaded_by:
                query = query.filter(File.uploaded_by == filter_request.uploaded_by)
            
            if filter_request.is_public is not None:
                query = query.filter(File.is_public == filter_request.is_public)
            
            if filter_request.search:
                search_term = f"%{filter_request.search}%"
                query = query.filter(
                    or_(
                        File.original_name.ilike(search_term),
                        File.description.ilike(search_term)
                    )
                )
            
            if filter_request.date_from:
                query = query.filter(File.created_at >= filter_request.date_from)
            
            if filter_request.date_to:
                query = query.filter(File.created_at <= filter_request.date_to)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        files = query.order_by(desc(File.created_at)).offset((page - 1) * page_size).limit(page_size).all()
        
        return files, total_count
    
    @staticmethod
    def update_file(
        db: Session,
        file_id: str,
        update_request: FileUpdateRequest
    ) -> Optional[File]:
        """
        Update file metadata.
        
        Args:
            db: Database session
            file_id: File ID
            update_request: Update request parameters
            
        Returns:
            Updated file object or None if not found
        """
        file_record = FileService.get_file_by_id(db, file_id)
        if not file_record:
            return None
        
        # Update fields
        if update_request.description is not None:
            file_record.description = update_request.description
        
        if update_request.is_public is not None:
            file_record.is_public = update_request.is_public
        
        file_record.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(file_record)
        
        return file_record
    
    @staticmethod
    def delete_file(db: Session, file_id: str) -> bool:
        """
        Soft delete a file.
        
        Args:
            db: Database session
            file_id: File ID
            
        Returns:
            True if deleted successfully, False if not found
        """
        file_record = FileService.get_file_by_id(db, file_id)
        if not file_record:
            return False
        
        # Soft delete
        file_record.is_deleted = True
        file_record.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        
        return True
    
    @staticmethod
    def hard_delete_file(db: Session, file_id: str) -> bool:
        """
        Hard delete a file (remove from storage and database).
        
        Args:
            db: Database session
            file_id: File ID
            
        Returns:
            True if deleted successfully, False if not found
        """
        file_record = db.query(File).filter(File.id == file_id).first()
        if not file_record:
            return False
        
        # Remove file from storage
        file_path = Path(file_record.file_path)
        if file_path.exists():
            file_path.unlink()
        
        # Remove from database
        db.delete(file_record)
        db.commit()
        
        return True
    
    @staticmethod
    def get_file_stats(db: Session) -> Dict[str, Any]:
        """
        Get file statistics.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with file statistics
        """
        # Total files and size
        total_files = db.query(func.count(File.id)).filter(File.is_deleted == False).scalar()
        total_size = db.query(func.sum(File.file_size)).filter(File.is_deleted == False).scalar() or 0
        
        # Files by type
        files_by_type = db.query(
            File.mime_type,
            func.count(File.id)
        ).filter(File.is_deleted == False).group_by(File.mime_type).all()
        
        # Files by uploader
        files_by_uploader = db.query(
            File.uploaded_by,
            func.count(File.id)
        ).filter(File.is_deleted == False).group_by(File.uploaded_by).all()
        
        # Recent uploads
        recent_uploads = db.query(File).filter(
            File.is_deleted == False
        ).order_by(desc(File.created_at)).limit(10).all()
        
        return {
            "total_files": total_files,
            "total_size": total_size,
            "files_by_type": dict(files_by_type),
            "files_by_uploader": dict(files_by_uploader),
            "recent_uploads": recent_uploads
        }
    
    # File Permission Methods
    
    @staticmethod
    def check_file_access(
        db: Session,
        file_id: str,
        user_id: str,
        required_permission: PermissionType = PermissionType.READ
    ) -> bool:
        """
        Check if a user has access to a file.
        
        Args:
            db: Database session
            file_id: File ID
            user_id: User ID
            required_permission: Required permission level
            
        Returns:
            True if user has access, False otherwise
        """
        # Get file
        file_record = FileService.get_file_by_id(db, file_id)
        if not file_record:
            return False
        
        # Check if user is the owner
        if str(file_record.uploaded_by) == user_id:
            return True
        
        # Check if file is public
        if file_record.is_public and required_permission == PermissionType.READ:
            return True
        
        # Check explicit permissions
        permission = db.query(FilePermission).filter(
            and_(
                FilePermission.file_id == file_id,
                FilePermission.user_id == user_id,
                FilePermission.is_active == True
            )
        ).first()
        
        if not permission or not permission.is_valid:
            return False
        
        # Check permission level
        permission_hierarchy = {
            PermissionType.READ: 1,
            PermissionType.WRITE: 2,
            PermissionType.ADMIN: 3
        }
        
        user_level = permission_hierarchy.get(permission.permission_type, 0)
        required_level = permission_hierarchy.get(required_permission, 0)
        
        return user_level >= required_level
    
    @staticmethod
    def grant_file_permission(
        db: Session,
        file_id: str,
        permission_request: FilePermissionRequest,
        granted_by: str
    ) -> FilePermission:
        """
        Grant permission to a user for a file.
        
        Args:
            db: Database session
            file_id: File ID
            permission_request: Permission request
            granted_by: User ID who is granting the permission
            
        Returns:
            FilePermission object
            
        Raises:
            HTTPException: If operation fails
        """
        # Check if file exists
        file_record = FileService.get_file_by_id(db, file_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check if permission already exists
        existing_permission = db.query(FilePermission).filter(
            and_(
                FilePermission.file_id == file_id,
                FilePermission.user_id == permission_request.user_id
            )
        ).first()
        
        if existing_permission:
            # Update existing permission
            existing_permission.permission_type = permission_request.permission_type
            existing_permission.expires_at = permission_request.expires_at
            existing_permission.is_active = True
            existing_permission.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing_permission)
            return existing_permission
        
        # Create new permission
        permission = FilePermission(
            file_id=file_id,
            user_id=permission_request.user_id,
            permission_type=permission_request.permission_type,
            granted_by=granted_by,
            expires_at=permission_request.expires_at
        )
        
        db.add(permission)
        db.commit()
        db.refresh(permission)
        
        return permission
    
    @staticmethod
    def get_file_permissions(
        db: Session,
        file_id: str,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[FilePermission], int]:
        """
        Get permissions for a file.
        
        Args:
            db: Database session
            file_id: File ID
            page: Page number
            page_size: Page size
            
        Returns:
            Tuple of (permissions, total_count)
        """
        query = db.query(FilePermission).filter(FilePermission.file_id == file_id)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        permissions = query.order_by(desc(FilePermission.created_at)).offset((page - 1) * page_size).limit(page_size).all()
        
        return permissions, total_count
    
    @staticmethod
    def update_file_permission(
        db: Session,
        file_id: str,
        user_id: str,
        update_request: FilePermissionUpdateRequest
    ) -> Optional[FilePermission]:
        """
        Update a file permission.
        
        Args:
            db: Database session
            file_id: File ID
            user_id: User ID
            update_request: Update request parameters
            
        Returns:
            Updated FilePermission object or None if not found
        """
        permission = db.query(FilePermission).filter(
            and_(
                FilePermission.file_id == file_id,
                FilePermission.user_id == user_id
            )
        ).first()
        
        if not permission:
            return None
        
        # Update fields
        if update_request.permission_type is not None:
            permission.permission_type = update_request.permission_type
        
        if update_request.expires_at is not None:
            permission.expires_at = update_request.expires_at
        
        if update_request.is_active is not None:
            permission.is_active = update_request.is_active
        
        permission.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(permission)
        
        return permission
    
    @staticmethod
    def revoke_file_permission(db: Session, file_id: str, user_id: str) -> bool:
        """
        Revoke a file permission.
        
        Args:
            db: Database session
            file_id: File ID
            user_id: User ID
            
        Returns:
            True if revoked successfully, False if not found
        """
        permission = db.query(FilePermission).filter(
            and_(
                FilePermission.file_id == file_id,
                FilePermission.user_id == user_id
            )
        ).first()
        
        if not permission:
            return False
        
        # Soft delete by setting is_active to False
        permission.is_active = False
        permission.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        
        return True
    
    # File Sharing Methods
    
    @staticmethod
    def create_file_share(
        db: Session,
        file_id: str,
        share_request: FileShareRequest,
        created_by: str
    ) -> FileShare:
        """
        Create a file share.
        
        Args:
            db: Database session
            file_id: File ID
            share_request: Share request parameters
            created_by: User ID who is creating the share
            
        Returns:
            FileShare object
            
        Raises:
            HTTPException: If operation fails
        """
        # Check if file exists
        file_record = FileService.get_file_by_id(db, file_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Generate unique share token
        share_token = secrets.token_urlsafe(32)
        
        # Create share
        share = FileShare(
            file_id=file_id,
            share_token=share_token,
            created_by=created_by,
            permission_type=share_request.permission_type,
            max_downloads=share_request.max_downloads,
            expires_at=share_request.expires_at
        )
        
        db.add(share)
        db.commit()
        db.refresh(share)
        
        return share
    
    @staticmethod
    def get_file_share_by_token(db: Session, share_token: str) -> Optional[FileShare]:
        """
        Get file share by token.
        
        Args:
            db: Database session
            share_token: Share token
            
        Returns:
            FileShare object or None if not found
        """
        return db.query(FileShare).filter(
            and_(
                FileShare.share_token == share_token,
                FileShare.is_active == True
            )
        ).first()
    
    @staticmethod
    def get_file_shares(
        db: Session,
        file_id: str,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[FileShare], int]:
        """
        Get shares for a file.
        
        Args:
            db: Database session
            file_id: File ID
            page: Page number
            page_size: Page size
            
        Returns:
            Tuple of (shares, total_count)
        """
        query = db.query(FileShare).filter(FileShare.file_id == file_id)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        shares = query.order_by(desc(FileShare.created_at)).offset((page - 1) * page_size).limit(page_size).all()
        
        return shares, total_count
    
    @staticmethod
    def update_file_share(
        db: Session,
        share_id: str,
        update_request: FileShareUpdateRequest
    ) -> Optional[FileShare]:
        """
        Update a file share.
        
        Args:
            db: Database session
            share_id: Share ID
            update_request: Update request parameters
            
        Returns:
            Updated FileShare object or None if not found
        """
        share = db.query(FileShare).filter(FileShare.id == share_id).first()
        
        if not share:
            return None
        
        # Update fields
        if update_request.permission_type is not None:
            share.permission_type = update_request.permission_type
        
        if update_request.max_downloads is not None:
            share.max_downloads = update_request.max_downloads
        
        if update_request.expires_at is not None:
            share.expires_at = update_request.expires_at
        
        if update_request.is_active is not None:
            share.is_active = update_request.is_active
        
        share.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(share)
        
        return share
    
    @staticmethod
    def delete_file_share(db: Session, share_id: str) -> bool:
        """
        Delete a file share.
        
        Args:
            db: Database session
            share_id: Share ID
            
        Returns:
            True if deleted successfully, False if not found
        """
        share = db.query(FileShare).filter(FileShare.id == share_id).first()
        
        if not share:
            return False
        
        # Soft delete by setting is_active to False
        share.is_active = False
        share.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        
        return True
    
    @staticmethod
    def increment_share_download_count(db: Session, share_id: str) -> bool:
        """
        Increment download count for a share.
        
        Args:
            db: Database session
            share_id: Share ID
            
        Returns:
            True if incremented successfully, False if not found
        """
        share = db.query(FileShare).filter(FileShare.id == share_id).first()
        
        if not share:
            return False
        
        share.increment_download_count()
        db.commit()
        
        return True
    
    # File Versioning Methods
    
    @staticmethod
    def create_initial_version(db: Session, file_record: File, user_id: str) -> FileVersion:
        """
        Create initial version for a file.
        
        Args:
            db: Database session
            file_record: File record
            user_id: User ID who created the file
            
        Returns:
            FileVersion object
        """
        version = FileVersion(
            file_id=str(file_record.id),
            version_number="1.0",
            file_name=file_record.file_name,
            original_name=file_record.original_name,
            file_path=file_record.file_path,
            file_size=file_record.file_size,
            mime_type=file_record.mime_type,
            description=file_record.description,
            change_description="Initial version",
            created_by=user_id,
            is_current=True
        )
        
        db.add(version)
        db.commit()
        db.refresh(version)
        
        return version
    
    @staticmethod
    def get_next_version_number(db: Session, file_id: str) -> str:
        """
        Get the next version number for a file.
        
        Args:
            db: Database session
            file_id: File ID
            
        Returns:
            Next version number as string
        """
        # Get the latest version
        latest_version = db.query(FileVersion).filter(
            FileVersion.file_id == file_id
        ).order_by(desc(FileVersion.version_number)).first()
        
        if not latest_version:
            return "1.0"
        
        # Parse version number and increment
        try:
            version_parts = latest_version.version_number.split('.')
            major = int(version_parts[0])
            minor = int(version_parts[1]) if len(version_parts) > 1 else 0
            return f"{major}.{minor + 1}"
        except (ValueError, IndexError):
            # Fallback to simple increment
            return f"{latest_version.version_number}.1"
    
    @staticmethod
    def create_file_version(
        db: Session,
        file_id: str,
        file: UploadFile,
        version_request: FileVersionRequest,
        created_by: str
    ) -> FileVersion:
        """
        Create a new version of a file.
        
        Args:
            db: Database session
            file_id: File ID
            file: Uploaded file
            version_request: Version request parameters
            created_by: User ID who is creating the version
            
        Returns:
            FileVersion object
            
        Raises:
            HTTPException: If operation fails
        """
        # Check if file exists
        file_record = FileService.get_file_by_id(db, file_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Validate uploaded file
        is_valid, error_message = FileService.validate_general_file(file)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # Get next version number
        version_number = FileService.get_next_version_number(db, file_id)
        
        # Create version directory
        version_dir = Path("uploads/files/versions")
        version_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate version filename
        file_extension = FileService.ALLOWED_FILE_TYPES.get(file.content_type, "")
        if not file_extension and '.' in file.filename:
            file_extension = '.' + file.filename.rsplit('.', 1)[1].lower()
        
        version_filename = f"{file_id}_{version_number.replace('.', '_')}{file_extension}"
        version_path = version_dir / version_filename
        
        try:
            # Save version file
            with open(version_path, 'wb') as f:
                content = file.file.read()
                f.write(content)
            
            # Get file size
            file_size = version_path.stat().st_size
            
            # Mark current version as not current
            db.query(FileVersion).filter(
                and_(
                    FileVersion.file_id == file_id,
                    FileVersion.is_current == True
                )
            ).update({"is_current": False})
            
            # Create version record
            version = FileVersion(
                file_id=file_id,
                version_number=version_number,
                file_name=version_filename,
                original_name=file.filename,
                file_path=str(version_path),
                file_size=file_size,
                mime_type=file.content_type,
                description=file_record.description,
                change_description=version_request.change_description,
                created_by=created_by,
                is_current=True
            )
            
            db.add(version)
            db.commit()
            db.refresh(version)
            
            return version
            
        except Exception as e:
            # Clean up on error
            if version_path.exists():
                version_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create file version: {str(e)}"
            )
    
    @staticmethod
    def get_file_versions(
        db: Session,
        file_id: str,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[FileVersion], int]:
        """
        Get versions for a file.
        
        Args:
            db: Database session
            file_id: File ID
            page: Page number
            page_size: Page size
            
        Returns:
            Tuple of (versions, total_count)
        """
        query = db.query(FileVersion).filter(FileVersion.file_id == file_id)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        versions = query.order_by(desc(FileVersion.version_number)).offset((page - 1) * page_size).limit(page_size).all()
        
        return versions, total_count
    
    @staticmethod
    def get_file_version_by_id(db: Session, version_id: str) -> Optional[FileVersion]:
        """
        Get file version by ID.
        
        Args:
            db: Database session
            version_id: Version ID
            
        Returns:
            FileVersion object or None if not found
        """
        return db.query(FileVersion).filter(FileVersion.id == version_id).first()
    
    @staticmethod
    def get_current_version(db: Session, file_id: str) -> Optional[FileVersion]:
        """
        Get current version of a file.
        
        Args:
            db: Database session
            file_id: File ID
            
        Returns:
            Current FileVersion object or None if not found
        """
        return db.query(FileVersion).filter(
            and_(
                FileVersion.file_id == file_id,
                FileVersion.is_current == True
            )
        ).first()
    
    @staticmethod
    def rollback_to_version(db: Session, file_id: str, version_id: str) -> Optional[FileVersion]:
        """
        Rollback file to a specific version.
        
        Args:
            db: Database session
            file_id: File ID
            version_id: Version ID to rollback to
            
        Returns:
            New current FileVersion object or None if rollback failed
        """
        # Get target version
        target_version = FileService.get_file_version_by_id(db, version_id)
        if not target_version or str(target_version.file_id) != file_id:
            return None
        
        # Get current version
        current_version = FileService.get_current_version(db, file_id)
        if not current_version:
            return None
        
        # Get file record
        file_record = FileService.get_file_by_id(db, file_id)
        if not file_record:
            return None
        
        try:
            # Mark current version as not current
            current_version.is_current = False
            
            # Mark target version as current
            target_version.is_current = True
            
            # Update file record with target version info
            file_record.file_name = target_version.file_name
            file_record.original_name = target_version.original_name
            file_record.file_path = target_version.file_path
            file_record.file_size = target_version.file_size
            file_record.mime_type = target_version.mime_type
            file_record.updated_at = datetime.now(timezone.utc)
            
            db.commit()
            db.refresh(target_version)
            
            return target_version
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to rollback file version: {e}")
            return None
    
    @staticmethod
    def delete_file_version(db: Session, version_id: str) -> bool:
        """
        Delete a file version.
        
        Args:
            db: Database session
            version_id: Version ID
            
        Returns:
            True if deleted successfully, False if not found
        """
        version = FileService.get_file_version_by_id(db, version_id)
        if not version:
            return False
        
        # Don't allow deletion of current version
        if version.is_current:
            return False
        
        try:
            # Remove version file from storage
            version_path = Path(version.file_path)
            if version_path.exists():
                version_path.unlink()
            
            # Remove from database
            db.delete(version)
            db.commit()
            
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete file version: {e}")
            return False
    
    @staticmethod
    def get_file_version_stats(db: Session, file_id: str) -> Dict[str, Any]:
        """
        Get file version statistics.
        
        Args:
            db: Database session
            file_id: File ID
            
        Returns:
            Dictionary with version statistics
        """
        # Get all versions for the file
        versions = db.query(FileVersion).filter(FileVersion.file_id == file_id).all()
        
        if not versions:
            return {
                "total_versions": 0,
                "current_version_number": None,
                "first_version_date": None,
                "last_version_date": None,
                "versions_by_creator": {},
                "total_size_all_versions": 0,
                "human_readable_total_size": "0 B"
            }
        
        # Calculate statistics
        total_versions = len(versions)
        current_version = next((v for v in versions if v.is_current), None)
        current_version_number = current_version.version_number if current_version else None
        
        # Get date range
        created_dates = [v.created_at for v in versions if v.created_at]
        first_version_date = min(created_dates) if created_dates else None
        last_version_date = max(created_dates) if created_dates else None
        
        # Group by creator
        versions_by_creator = {}
        for version in versions:
            creator_id = str(version.created_by)
            if creator_id not in versions_by_creator:
                versions_by_creator[creator_id] = 0
            versions_by_creator[creator_id] += 1
        
        # Calculate total size
        total_size_all_versions = sum(v.file_size for v in versions)
        
        # Convert to human readable
        human_readable_total_size = ""
        size = total_size_all_versions
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                human_readable_total_size = f"{size:.1f} {unit}"
                break
            size /= 1024.0
        else:
            human_readable_total_size = f"{size:.1f} TB"
        
        return {
            "total_versions": total_versions,
            "current_version_number": current_version_number,
            "first_version_date": first_version_date,
            "last_version_date": last_version_date,
            "versions_by_creator": versions_by_creator,
            "total_size_all_versions": total_size_all_versions,
            "human_readable_total_size": human_readable_total_size
        }
    
    @staticmethod
    def delete_avatar(avatar_url: str) -> bool:
        """
        Delete avatar file.
        
        Args:
            avatar_url: Avatar file path
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            if avatar_url and os.path.exists(avatar_url):
                os.remove(avatar_url)
                return True
            return False
        except Exception:
            return False
    
    @staticmethod
    def get_avatar_url(avatar_path: str) -> str:
        """
        Get avatar URL for serving.
        
        Args:
            avatar_path: Avatar file path
            
        Returns:
            Avatar URL
        """
        if not avatar_path:
            return ""
        
        # Convert file path to URL
        if avatar_path.startswith("uploads/"):
            return f"/static/{avatar_path}"
        
        return avatar_path
    
    @staticmethod
    def validate_file_size(file_size: int, max_size: int) -> bool:
        """
        Validate file size.
        
        Args:
            file_size: File size in bytes
            max_size: Maximum allowed size in bytes
            
        Returns:
            True if valid, False otherwise
        """
        return file_size <= max_size
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """
        Get file extension from filename.
        
        Args:
            filename: File name
            
        Returns:
            File extension (without dot)
        """
        if '.' in filename:
            return filename.rsplit('.', 1)[1].lower()
        return ""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename for safe storage.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove or replace unsafe characters
        unsafe_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        for char in unsafe_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:255-len(ext)-1] + '.' + ext if ext else name[:255]
        
        return filename 
