"""
File API endpoints for file upload and management functionality.
"""
import logging
from typing import Optional, List
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File as FastAPIFile, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.database import AsyncSessionWrapper, get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.services.file_service import FileService
from app.schemas.file import (
    FileUploadRequest,
    FileResponse as FileResponseSchema,
    FileListResponse,
    FileUpdateRequest,
    FileUploadResponse,
    FileDeleteResponse,
    FileFilterRequest,
    FileStatsResponse
)
from app.schemas.file_permission import (
    FilePermissionRequest,
    FilePermissionResponse,
    FilePermissionListResponse,
    FilePermissionUpdateRequest,
    FileShareRequest,
    FileShareResponse,
    FileShareListResponse,
    FileShareUpdateRequest,
    FilePermissionStatsResponse,
    FileShareStatsResponse,
    FileAccessResponse,
    PermissionType,
    SharePermissionType
)
from app.schemas.file_version import (
    FileVersionRequest,
    FileVersionResponse,
    FileVersionListResponse,
    FileVersionCreateResponse,
    FileVersionRollbackResponse,
    FileVersionStatsResponse
)
from app.models.file import File
from app.models.file_permission import FilePermission, FileShare
from app.models.file_version import FileVersion

router = APIRouter(prefix="/files", tags=["Files"])
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = FastAPIFile(..., description="File to upload"),
    description: Optional[str] = Form(None, description="File description"),
    is_public: bool = Form(False, description="Whether the file is public"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a file.
    
    Args:
        file: File to upload
        description: Optional file description
        is_public: Whether the file is public
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Upload response with file information
    """
    try:
        # Create upload request
        upload_request = FileUploadRequest(
            description=description,
            is_public=is_public
        )
        
        # Upload file
        file_record = await FileService.upload_file(
            db.session,
            file,
            str(current_user.id),
            upload_request
        )
        
        # Create download URL
        download_url = f"/files/{file_record.id}/download"
        
        return FileUploadResponse(
            file=file_record,
            download_url=download_url,
            message="File uploaded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )


@router.get("/{file_id}", response_model=FileResponseSchema)
async def get_file(
    file_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get file information by ID.
    
    Args:
        file_id: File ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        File information
    """
    try:
        file_record = FileService.get_file_by_id(db.session, file_id)
        
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check permissions
        if not file_record.is_public and str(file_record.uploaded_by) != str(current_user.id):
            if current_user.role not in ["Admin", "Manager"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this file"
                )
        
        return file_record
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get file information"
        )


@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download a file.
    
    Args:
        file_id: File ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        File response for download
    """
    try:
        file_record = FileService.get_file_by_id(db.session, file_id)
        
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check permissions
        if not file_record.is_public and str(file_record.uploaded_by) != str(current_user.id):
            if current_user.role not in ["Admin", "Manager"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to download this file"
                )
        
        # Check if file exists on disk
        file_path = Path(file_record.file_path)
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found on disk"
            )
        
        return FileResponse(
            path=file_path,
            filename=file_record.original_name,
            media_type=file_record.mime_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download file"
        )


@router.delete("/{file_id}", response_model=FileDeleteResponse)
async def delete_file(
    file_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a file.
    
    Args:
        file_id: File ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Deletion response
    """
    try:
        file_record = FileService.get_file_by_id(db.session, file_id)
        
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check permissions
        if str(file_record.uploaded_by) != str(current_user.id):
            if current_user.role not in ["Admin", "Manager"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to delete this file"
                )
        
        # Delete file
        success = FileService.delete_file(db.session, file_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete file"
            )
        
        return FileDeleteResponse(
            message="File deleted successfully",
            file_id=file_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file"
        )


@router.get("/list", response_model=FileListResponse)
async def list_files(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    mime_type: Optional[str] = Query(None, description="Filter by MIME type"),
    uploaded_by: Optional[str] = Query(None, description="Filter by uploader ID"),
    is_public: Optional[bool] = Query(None, description="Filter by public status"),
    search: Optional[str] = Query(None, description="Search in file names and descriptions"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List files with pagination and filtering.
    
    Args:
        page: Page number
        page_size: Page size
        mime_type: Filter by MIME type
        uploaded_by: Filter by uploader ID
        is_public: Filter by public status
        search: Search term
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of files with pagination information
    """
    try:
        # Create filter request
        filter_request = FileFilterRequest(
            mime_type=mime_type,
            uploaded_by=uploaded_by,
            is_public=is_public,
            search=search
        )
        
        # Get files
        files, total_count = FileService.get_files(
            db.session,
            page,
            page_size,
            filter_request
        )
        
        # Filter files based on permissions
        accessible_files = []
        for file_record in files:
            if file_record.is_public or str(file_record.uploaded_by) == str(current_user.id):
                accessible_files.append(file_record)
            elif current_user.role in ["Admin", "Manager"]:
                accessible_files.append(file_record)
        
        # Calculate pagination info
        has_next = (page * page_size) < total_count
        has_previous = page > 1
        
        return FileListResponse(
            files=accessible_files,
            total_count=len(accessible_files),
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous
        )
        
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list files"
        )


@router.put("/{file_id}", response_model=FileResponseSchema)
async def update_file(
    file_id: str,
    update_request: FileUpdateRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update file metadata.
    
    Args:
        file_id: File ID
        update_request: Update request parameters
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated file information
    """
    try:
        file_record = FileService.get_file_by_id(db.session, file_id)
        
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check permissions
        if str(file_record.uploaded_by) != str(current_user.id):
            if current_user.role not in ["Admin", "Manager"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to update this file"
                )
        
        # Update file
        updated_file = FileService.update_file(db.session, file_id, update_request)
        
        if not updated_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        return updated_file
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update file"
        )


@router.get("/stats", response_model=FileStatsResponse)
async def get_file_stats(
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Manager"]))
):
    """
    Get file statistics.
    
    Args:
        db: Database session
        current_user: Current authenticated user (Admin/Manager only)
        
    Returns:
        File statistics
    """
    try:
        stats = FileService.get_file_stats(db.session)
        
        # Convert human readable size
        total_size = stats["total_size"]
        human_readable_total_size = ""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if total_size < 1024.0:
                human_readable_total_size = f"{total_size:.1f} {unit}"
                break
            total_size /= 1024.0
        else:
            human_readable_total_size = f"{total_size:.1f} TB"
        
        return FileStatsResponse(
            total_files=stats["total_files"],
            total_size=stats["total_size"],
            human_readable_total_size=human_readable_total_size,
            files_by_type=stats["files_by_type"],
            files_by_uploader=stats["files_by_uploader"],
            recent_uploads=stats["recent_uploads"]
        )
        
    except Exception as e:
        logger.error(f"Error getting file stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get file statistics"
        )


# File Permission Endpoints

@router.get("/{file_id}/permissions", response_model=FilePermissionListResponse)
async def get_file_permissions(
    file_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get permissions for a file.
    
    Args:
        file_id: File ID
        page: Page number
        page_size: Page size
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of file permissions
    """
    try:
        # Check if user has access to manage permissions
        file_record = FileService.get_file_by_id(db.session, file_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check permissions - only owner or admin/manager can view permissions
        if str(file_record.uploaded_by) != str(current_user.id):
            if current_user.role not in ["Admin", "Manager"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view file permissions"
                )
        
        # Get permissions
        permissions, total_count = FileService.get_file_permissions(
            db.session,
            file_id,
            page,
            page_size
        )
        
        # Calculate pagination info
        has_next = (page * page_size) < total_count
        has_previous = page > 1
        
        return FilePermissionListResponse(
            permissions=permissions,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file permissions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get file permissions"
        )


@router.put("/{file_id}/permissions", response_model=FilePermissionResponse)
async def update_file_permission(
    file_id: str,
    user_id: str,
    update_request: FilePermissionUpdateRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a file permission.
    
    Args:
        file_id: File ID
        user_id: User ID whose permission to update
        update_request: Update request parameters
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated permission information
    """
    try:
        # Check if user has access to manage permissions
        file_record = FileService.get_file_by_id(db.session, file_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check permissions - only owner or admin/manager can update permissions
        if str(file_record.uploaded_by) != str(current_user.id):
            if current_user.role not in ["Admin", "Manager"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to update file permissions"
                )
        
        # Update permission
        updated_permission = FileService.update_file_permission(
            db.session,
            file_id,
            user_id,
            update_request
        )
        
        if not updated_permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permission not found"
            )
        
        return updated_permission
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating file permission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update file permission"
        )


@router.post("/{file_id}/permissions", response_model=FilePermissionResponse)
async def grant_file_permission(
    file_id: str,
    permission_request: FilePermissionRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Grant permission to a user for a file.
    
    Args:
        file_id: File ID
        permission_request: Permission request parameters
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Granted permission information
    """
    try:
        # Check if user has access to manage permissions
        file_record = FileService.get_file_by_id(db.session, file_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check permissions - only owner or admin/manager can grant permissions
        if str(file_record.uploaded_by) != str(current_user.id):
            if current_user.role not in ["Admin", "Manager"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to grant file permissions"
                )
        
        # Grant permission
        permission = FileService.grant_file_permission(
            db.session,
            file_id,
            permission_request,
            str(current_user.id)
        )
        
        return permission
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error granting file permission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to grant file permission"
        )


@router.delete("/{file_id}/permissions/{user_id}")
async def revoke_file_permission(
    file_id: str,
    user_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Revoke a file permission.
    
    Args:
        file_id: File ID
        user_id: User ID whose permission to revoke
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    try:
        # Check if user has access to manage permissions
        file_record = FileService.get_file_by_id(db.session, file_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check permissions - only owner or admin/manager can revoke permissions
        if str(file_record.uploaded_by) != str(current_user.id):
            if current_user.role not in ["Admin", "Manager"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to revoke file permissions"
                )
        
        # Revoke permission
        success = FileService.revoke_file_permission(db.session, file_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permission not found"
            )
        
        return {"message": "Permission revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking file permission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke file permission"
        )


# File Sharing Endpoints

@router.post("/{file_id}/share", response_model=FileShareResponse)
async def create_file_share(
    file_id: str,
    share_request: FileShareRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a file share.
    
    Args:
        file_id: File ID
        share_request: Share request parameters
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created share information
    """
    try:
        # Check if user has access to share the file
        file_record = FileService.get_file_by_id(db.session, file_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check permissions - only owner or users with write/admin permission can share
        if str(file_record.uploaded_by) != str(current_user.id):
            if not FileService.check_file_access(db.session, file_id, str(current_user.id), PermissionType.WRITE):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to share this file"
                )
        
        # Create share
        share = FileService.create_file_share(
            db.session,
            file_id,
            share_request,
            str(current_user.id)
        )
        
        # Add share URL
        share.share_url = f"/files/share/{share.share_token}"
        
        return share
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating file share: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create file share"
        )


@router.get("/share/{share_token}", response_model=FileResponseSchema)
async def access_shared_file(
    share_token: str,
    db: AsyncSessionWrapper = Depends(get_db)
):
    """
    Access a file via share token.
    
    Args:
        share_token: Share token
        db: Database session
        
    Returns:
        File information
    """
    try:
        # Get share by token
        share = FileService.get_file_share_by_token(db.session, share_token)
        if not share:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share not found or expired"
            )
        
        # Check if share is valid
        if not share.is_valid:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Share has expired or download limit reached"
            )
        
        # Get file
        file_record = FileService.get_file_by_id(db.session, str(share.file_id))
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Increment download count
        FileService.increment_share_download_count(db.session, str(share.id))
        
        return file_record
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accessing shared file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to access shared file"
        )


@router.get("/share/{share_token}/download")
async def download_shared_file(
    share_token: str,
    db: AsyncSessionWrapper = Depends(get_db)
):
    """
    Download a file via share token.
    
    Args:
        share_token: Share token
        db: Database session
        
    Returns:
        File response for download
    """
    try:
        # Get share by token
        share = FileService.get_file_share_by_token(db.session, share_token)
        if not share:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share not found or expired"
            )
        
        # Check if share is valid
        if not share.is_valid:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Share has expired or download limit reached"
            )
        
        # Get file
        file_record = FileService.get_file_by_id(db.session, str(share.file_id))
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check if file exists on disk
        file_path = Path(file_record.file_path)
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found on disk"
            )
        
        # Increment download count
        FileService.increment_share_download_count(db.session, str(share.id))
        
        return FileResponse(
            path=file_path,
            filename=file_record.original_name,
            media_type=file_record.mime_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading shared file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download shared file"
        )


@router.get("/{file_id}/shares", response_model=FileShareListResponse)
async def get_file_shares(
    file_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get shares for a file.
    
    Args:
        file_id: File ID
        page: Page number
        page_size: Page size
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of file shares
    """
    try:
        # Check if user has access to view shares
        file_record = FileService.get_file_by_id(db.session, file_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check permissions - only owner or users with write/admin permission can view shares
        if str(file_record.uploaded_by) != str(current_user.id):
            if not FileService.check_file_access(db.session, file_id, str(current_user.id), PermissionType.WRITE):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view file shares"
                )
        
        # Get shares
        shares, total_count = FileService.get_file_shares(
            db.session,
            file_id,
            page,
            page_size
        )
        
        # Add share URLs
        for share in shares:
            share.share_url = f"/files/share/{share.share_token}"
        
        # Calculate pagination info
        has_next = (page * page_size) < total_count
        has_previous = page > 1
        
        return FileShareListResponse(
            shares=shares,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file shares: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get file shares"
        )


@router.delete("/shares/{share_id}")
async def delete_file_share(
    share_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a file share.
    
    Args:
        share_id: Share ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    try:
        # Get share
        share = db.session.query(FileShare).filter(FileShare.id == share_id).first()
        if not share:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share not found"
            )
        
        # Check permissions - only creator or file owner can delete share
        file_record = FileService.get_file_by_id(db.session, str(share.file_id))
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        if str(share.created_by) != str(current_user.id) and str(file_record.uploaded_by) != str(current_user.id):
            if current_user.role not in ["Admin", "Manager"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to delete this share"
                )
        
        # Delete share
        success = FileService.delete_file_share(db.session, share_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete share"
            )
        
        return {"message": "Share deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file share: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file share"
        )


@router.get("/{file_id}/access", response_model=FileAccessResponse)
async def check_file_access(
    file_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check current user's access to a file.
    
    Args:
        file_id: File ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        File access information
    """
    try:
        file_record = FileService.get_file_by_id(db.session, file_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check if user is owner
        is_owner = str(file_record.uploaded_by) == str(current_user.id)
        
        # Check permissions
        can_read = FileService.check_file_access(db.session, file_id, str(current_user.id), PermissionType.READ)
        can_write = FileService.check_file_access(db.session, file_id, str(current_user.id), PermissionType.WRITE)
        can_delete = is_owner or current_user.role in ["Admin", "Manager"]
        can_share = can_write or is_owner
        can_manage_permissions = is_owner or current_user.role in ["Admin", "Manager"]
        
        # Get permission type
        permission_type = None
        if not is_owner:
            permission = db.session.query(FilePermission).filter(
                and_(
                    FilePermission.file_id == file_id,
                    FilePermission.user_id == str(current_user.id),
                    FilePermission.is_active == True
                )
            ).first()
            if permission and permission.is_valid:
                permission_type = permission.permission_type
        
        return FileAccessResponse(
            file_id=file_id,
            user_id=str(current_user.id),
            has_access=can_read,
            permission_type=permission_type,
            is_owner=is_owner,
            can_read=can_read,
            can_write=can_write,
            can_delete=can_delete,
            can_share=can_share,
            can_manage_permissions=can_manage_permissions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking file access: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check file access"
        )


# File Version Endpoints

@router.get("/{file_id}/versions", response_model=FileVersionListResponse)
async def get_file_versions(
    file_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get versions for a file.
    
    Args:
        file_id: File ID
        page: Page number
        page_size: Page size
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of file versions
    """
    try:
        # Check if user has access to the file
        file_record = FileService.get_file_by_id(db.session, file_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check permissions - user needs read access
        if not FileService.check_file_access(db.session, file_id, str(current_user.id), PermissionType.READ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this file"
            )
        
        # Get versions
        versions, total_count = FileService.get_file_versions(
            db.session,
            file_id,
            page,
            page_size
        )
        
        # Get current version
        current_version = FileService.get_current_version(db.session, file_id)
        
        # Calculate pagination info
        has_next = (page * page_size) < total_count
        has_previous = page > 1
        
        return FileVersionListResponse(
            versions=versions,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous,
            current_version=current_version
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file versions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get file versions"
        )


@router.post("/{file_id}/versions", response_model=FileVersionCreateResponse)
async def create_file_version(
    file_id: str,
    file: UploadFile = FastAPIFile(..., description="New version file"),
    change_description: Optional[str] = Form(None, description="Description of changes"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new version of a file.
    
    Args:
        file_id: File ID
        file: New version file
        change_description: Description of changes
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created version information
    """
    try:
        # Check if user has access to create versions
        file_record = FileService.get_file_by_id(db.session, file_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check permissions - user needs write access
        if not FileService.check_file_access(db.session, file_id, str(current_user.id), PermissionType.WRITE):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create versions for this file"
            )
        
        # Create version request
        version_request = FileVersionRequest(
            change_description=change_description
        )
        
        # Create version
        version = FileService.create_file_version(
            db.session,
            file_id,
            file,
            version_request,
            str(current_user.id)
        )
        
        # Create download URL
        download_url = f"/files/{file_id}/versions/{version.id}/download"
        
        return FileVersionCreateResponse(
            version=version,
            message="File version created successfully",
            download_url=download_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating file version: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create file version"
        )


@router.get("/{file_id}/versions/{version_id}", response_model=FileVersionResponse)
async def get_file_version(
    file_id: str,
    version_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific file version.
    
    Args:
        file_id: File ID
        version_id: Version ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        File version information
    """
    try:
        # Check if user has access to the file
        file_record = FileService.get_file_by_id(db.session, file_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check permissions - user needs read access
        if not FileService.check_file_access(db.session, file_id, str(current_user.id), PermissionType.READ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this file"
            )
        
        # Get version
        version = FileService.get_file_version_by_id(db.session, version_id)
        if not version or str(version.file_id) != file_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found"
            )
        
        return version
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file version: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get file version"
        )


@router.get("/{file_id}/versions/{version_id}/download")
async def download_file_version(
    file_id: str,
    version_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download a specific file version.
    
    Args:
        file_id: File ID
        version_id: Version ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        File response for download
    """
    try:
        # Check if user has access to the file
        file_record = FileService.get_file_by_id(db.session, file_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check permissions - user needs read access
        if not FileService.check_file_access(db.session, file_id, str(current_user.id), PermissionType.READ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to download this file"
            )
        
        # Get version
        version = FileService.get_file_version_by_id(db.session, version_id)
        if not version or str(version.file_id) != file_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found"
            )
        
        # Check if version file exists on disk
        version_path = Path(version.file_path)
        if not version_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version file not found on disk"
            )
        
        return FileResponse(
            path=version_path,
            filename=version.original_name,
            media_type=version.mime_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file version: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download file version"
        )


@router.post("/{file_id}/versions/{version_id}/rollback", response_model=FileVersionRollbackResponse)
async def rollback_to_version(
    file_id: str,
    version_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Rollback file to a specific version.
    
    Args:
        file_id: File ID
        version_id: Version ID to rollback to
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Rollback response with version information
    """
    try:
        # Check if user has access to rollback
        file_record = FileService.get_file_by_id(db.session, file_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check permissions - user needs write access
        if not FileService.check_file_access(db.session, file_id, str(current_user.id), PermissionType.WRITE):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to rollback this file"
            )
        
        # Get current version before rollback
        previous_version = FileService.get_current_version(db.session, file_id)
        if not previous_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Current version not found"
            )
        
        # Perform rollback
        new_current_version = FileService.rollback_to_version(db.session, file_id, version_id)
        if not new_current_version:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to rollback to specified version"
            )
        
        return FileVersionRollbackResponse(
            message="File rolled back successfully",
            current_version=new_current_version,
            previous_version=previous_version
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rolling back file version: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rollback file version"
        )


@router.get("/{file_id}/versions/stats", response_model=FileVersionStatsResponse)
async def get_file_version_stats(
    file_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get file version statistics.
    
    Args:
        file_id: File ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        File version statistics
    """
    try:
        # Check if user has access to the file
        file_record = FileService.get_file_by_id(db.session, file_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check permissions - user needs read access
        if not FileService.check_file_access(db.session, file_id, str(current_user.id), PermissionType.READ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this file"
            )
        
        # Get version statistics
        stats = FileService.get_file_version_stats(db.session, file_id)
        
        return FileVersionStatsResponse(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file version stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get file version statistics"
        ) 