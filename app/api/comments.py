"""
Comments API endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.database import AsyncSessionWrapper, get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.services.comment_service import CommentService
from app.schemas.comment import (
    CommentCreateRequest,
    CommentUpdateRequest,
    CommentListResponse,
    CommentCreateResponseWrapper,
    CommentUpdateResponseWrapper,
    CommentDeleteResponseWrapper,
    CommentDetailResponseWrapper,
    CommentDetailResponse,
    CommentFilterRequest,
    CommentSearchRequest,
    CommentThreadResponse,
    CommentMentionCreateRequest,
    CommentMentionResponse,
    CommentMentionListResponse,
    CommentMentionCreateResponseWrapper,
    CommentMentionDeleteResponseWrapper,
    UserMentionsResponse,
    CommentAttachmentCreateRequest,
    CommentAttachmentResponse,
    CommentAttachmentListResponse,
    CommentAttachmentCreateResponseWrapper,
    CommentAttachmentDeleteResponseWrapper
)
from app.schemas.user import UserResponse

router = APIRouter(prefix="/comments", tags=["Comments"])


@router.get("", response_model=CommentListResponse)
async def get_comments(
    entity_type: Optional[str] = Query(None, description="Filter by entity type (Project, Task, Milestone)"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    author_id: Optional[str] = Query(None, description="Filter by author ID"),
    parent_comment_id: Optional[str] = Query(None, description="Filter by parent comment ID"),
    include_replies: Optional[bool] = Query(True, description="Include replies in results"),
    page: Optional[int] = Query(1, ge=1, description="Page number"),
    limit: Optional[int] = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comments with optional filtering and pagination.
    
    Args:
        entity_type: Optional filter by entity type
        entity_id: Optional filter by entity ID
        author_id: Optional filter by author ID
        parent_comment_id: Optional filter by parent comment ID
        include_replies: Include replies in results
        page: Page number
        limit: Items per page
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of comments with pagination info
    """
    try:
        # Validate entity type if provided
        if entity_type:
            valid_types = ['Project', 'Task', 'Milestone']
            if entity_type not in valid_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid entity_type. Must be one of: {', '.join(valid_types)}"
                )
        
        # Get comments
        comments, pagination_info = CommentService.get_comments(
            db.session,
            entity_type=entity_type,
            entity_id=entity_id,
            author_id=author_id,
            parent_comment_id=parent_comment_id,
            include_replies=include_replies,
            page=page,
            limit=limit
        )
        
        # Convert to response format
        comment_responses = []
        for comment in comments:
            comment_response = CommentDetailResponse(
                id=comment.id,
                content=comment.content,
                author_id=comment.author_id,
                entity_type=comment.entity_type,
                entity_id=comment.entity_id,
                parent_comment_id=comment.parent_comment_id,
                created_at=comment.created_at,
                updated_at=comment.updated_at,
                author=UserResponse(
                    id=comment.author.id,
                    email=comment.author.email,
                    first_name=comment.author.first_name,
                    last_name=comment.author.last_name,
                    role=comment.author.role,
                    is_active=comment.author.is_active,
                    created_at=comment.author.created_at,
                    updated_at=comment.author.updated_at
                ),
                replies_count=len(comment.replies) if comment.replies else 0,
                mentions_count=len(comment.mentions) if comment.mentions else 0,
                attachments_count=len(comment.attachments) if comment.attachments else 0
            )
            comment_responses.append(comment_response)
        
        return CommentListResponse(
            success=True,
            data=comment_responses,
            message="Comments retrieved successfully",
            pagination=pagination_info
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve comments: {str(e)}"
        )


@router.get("/{comment_id}", response_model=CommentDetailResponseWrapper)
async def get_comment(
    comment_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific comment by ID.
    
    Args:
        comment_id: Comment ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Comment details
    """
    try:
        comment = CommentService.get_comment_by_id(db.session, comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        
        # Convert to response format
        comment_response = CommentDetailResponse(
            id=comment.id,
            content=comment.content,
            author_id=comment.author_id,
            entity_type=comment.entity_type,
            entity_id=comment.entity_id,
            parent_comment_id=comment.parent_comment_id,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            author=UserResponse(
                id=comment.author.id,
                email=comment.author.email,
                first_name=comment.author.first_name,
                last_name=comment.author.last_name,
                role=comment.author.role,
                is_active=comment.author.is_active,
                created_at=comment.author.created_at,
                updated_at=comment.author.updated_at
            ),
            replies_count=len(comment.replies) if comment.replies else 0,
            mentions_count=len(comment.mentions) if comment.mentions else 0,
            attachments_count=len(comment.attachments) if comment.attachments else 0
        )
        
        return CommentDetailResponseWrapper(
            success=True,
            data=comment_response,
            message="Comment retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve comment: {str(e)}"
        )


@router.post("", response_model=CommentCreateResponseWrapper, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment_data: CommentCreateRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new comment.
    
    Args:
        comment_data: Comment creation data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created comment details
    """
    try:
        # Create comment
        comment = CommentService.create_comment(
            db.session,
            comment_data,
            str(current_user.id)
        )
        
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create comment"
            )
        
        # Get the created comment with related data
        created_comment = CommentService.get_comment_by_id(db.session, str(comment.id))
        
        # Convert to response format
        comment_response = CommentDetailResponse(
            id=created_comment.id,
            content=created_comment.content,
            author_id=created_comment.author_id,
            entity_type=created_comment.entity_type,
            entity_id=created_comment.entity_id,
            parent_comment_id=created_comment.parent_comment_id,
            created_at=created_comment.created_at,
            updated_at=created_comment.updated_at,
            author=UserResponse(
                id=created_comment.author.id,
                email=created_comment.author.email,
                first_name=created_comment.author.first_name,
                last_name=created_comment.author.last_name,
                role=created_comment.author.role,
                is_active=created_comment.author.is_active,
                created_at=created_comment.author.created_at,
                updated_at=created_comment.author.updated_at
            ),
            replies_count=len(created_comment.replies) if created_comment.replies else 0,
            mentions_count=len(created_comment.mentions) if created_comment.mentions else 0,
            attachments_count=len(created_comment.attachments) if created_comment.attachments else 0
        )
        
        return CommentCreateResponseWrapper(
            success=True,
            data=comment_response,
            message="Comment created successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create comment: {str(e)}"
        )


@router.put("/{comment_id}", response_model=CommentUpdateResponseWrapper)
async def update_comment(
    comment_id: str,
    update_data: CommentUpdateRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing comment.
    
    Args:
        comment_id: Comment ID to update
        update_data: Update data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated comment details
    """
    try:
        # Update comment
        comment = CommentService.update_comment(
            db.session,
            comment_id,
            update_data,
            str(current_user.id)
        )
        
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        
        # Get the updated comment with related data
        updated_comment = CommentService.get_comment_by_id(db.session, comment_id)
        
        # Convert to response format
        comment_response = CommentDetailResponse(
            id=updated_comment.id,
            content=updated_comment.content,
            author_id=updated_comment.author_id,
            entity_type=updated_comment.entity_type,
            entity_id=updated_comment.entity_id,
            parent_comment_id=updated_comment.parent_comment_id,
            created_at=updated_comment.created_at,
            updated_at=updated_comment.updated_at,
            author=UserResponse(
                id=updated_comment.author.id,
                email=updated_comment.author.email,
                first_name=updated_comment.author.first_name,
                last_name=updated_comment.author.last_name,
                role=updated_comment.author.role,
                is_active=updated_comment.author.is_active,
                created_at=updated_comment.author.created_at,
                updated_at=updated_comment.author.updated_at
            ),
            replies_count=len(updated_comment.replies) if updated_comment.replies else 0,
            mentions_count=len(updated_comment.mentions) if updated_comment.mentions else 0,
            attachments_count=len(updated_comment.attachments) if updated_comment.attachments else 0
        )
        
        return CommentUpdateResponseWrapper(
            success=True,
            data=comment_response,
            message="Comment updated successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update comment: {str(e)}"
        )


@router.delete("/{comment_id}", response_model=CommentDeleteResponseWrapper)
async def delete_comment(
    comment_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a comment.
    
    Args:
        comment_id: Comment ID to delete
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Deletion confirmation
    """
    try:
        # Delete comment
        success = CommentService.delete_comment(
            db.session,
            comment_id,
            str(current_user.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        
        return CommentDeleteResponseWrapper(
            success=True,
            message="Comment deleted successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete comment: {str(e)}"
        )


@router.post("/search", response_model=CommentListResponse)
async def search_comments(
    search_data: CommentSearchRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search comments by content.
    
    Args:
        search_data: Search parameters
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Search results with pagination
    """
    try:
        # Search comments
        comments, pagination_info = CommentService.search_comments(
            db.session,
            search_data.query,
            entity_type=search_data.entity_type,
            entity_id=search_data.entity_id,
            author_id=search_data.author_id,
            page=search_data.page,
            limit=search_data.limit
        )
        
        # Convert to response format
        comment_responses = []
        for comment in comments:
            comment_response = CommentDetailResponse(
                id=comment.id,
                content=comment.content,
                author_id=comment.author_id,
                entity_type=comment.entity_type,
                entity_id=comment.entity_id,
                parent_comment_id=comment.parent_comment_id,
                created_at=comment.created_at,
                updated_at=comment.updated_at,
                author=UserResponse(
                    id=comment.author.id,
                    email=comment.author.email,
                    first_name=comment.author.first_name,
                    last_name=comment.author.last_name,
                    role=comment.author.role,
                    is_active=comment.author.is_active,
                    created_at=comment.author.created_at,
                    updated_at=comment.author.updated_at
                ),
                replies_count=len(comment.replies) if comment.replies else 0,
                mentions_count=len(comment.mentions) if comment.mentions else 0,
                attachments_count=len(comment.attachments) if comment.attachments else 0
            )
            comment_responses.append(comment_response)
        
        return CommentListResponse(
            success=True,
            data=comment_responses,
            message=f"Found {len(comment_responses)} comments matching '{search_data.query}'",
            pagination=pagination_info
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search comments: {str(e)}"
        )


@router.get("/{comment_id}/thread", response_model=CommentThreadResponse)
async def get_comment_thread(
    comment_id: str,
    page: Optional[int] = Query(1, ge=1, description="Page number"),
    limit: Optional[int] = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a comment thread with all replies.
    
    Args:
        comment_id: Root comment ID
        page: Page number
        limit: Items per page
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Comment thread with replies
    """
    try:
        # Get comment thread
        comments, pagination_info, thread_info = CommentService.get_comment_thread(
            db.session,
            comment_id,
            page=page,
            limit=limit
        )
        
        # Convert to response format
        comment_responses = []
        for comment in comments:
            comment_response = CommentDetailResponse(
                id=comment.id,
                content=comment.content,
                author_id=comment.author_id,
                entity_type=comment.entity_type,
                entity_id=comment.entity_id,
                parent_comment_id=comment.parent_comment_id,
                created_at=comment.created_at,
                updated_at=comment.updated_at,
                author=UserResponse(
                    id=comment.author.id,
                    email=comment.author.email,
                    first_name=comment.author.first_name,
                    last_name=comment.author.last_name,
                    role=comment.author.role,
                    is_active=comment.author.is_active,
                    created_at=comment.author.created_at,
                    updated_at=comment.author.updated_at
                ),
                replies_count=len(comment.replies) if comment.replies else 0,
                mentions_count=len(comment.mentions) if comment.mentions else 0,
                attachments_count=len(comment.attachments) if comment.attachments else 0
            )
            comment_responses.append(comment_response)
        
        return CommentThreadResponse(
            success=True,
            data=comment_responses,
            message="Comment thread retrieved successfully",
            pagination=pagination_info,
            thread_info=thread_info
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve comment thread: {str(e)}"
        )


@router.get("/stats/summary")
async def get_comment_statistics(
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    author_id: Optional[str] = Query(None, description="Filter by author ID"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comment statistics.
    
    Args:
        entity_type: Filter by entity type
        entity_id: Filter by entity ID
        author_id: Filter by author ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Comment statistics
    """
    try:
        # Validate entity type if provided
        if entity_type:
            valid_types = ['Project', 'Task', 'Milestone']
            if entity_type not in valid_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid entity_type. Must be one of: {', '.join(valid_types)}"
                )
        
        # Get statistics
        stats = CommentService.get_comment_statistics(
            db.session,
            entity_type=entity_type,
            entity_id=entity_id,
            author_id=author_id
        )
        
        return {
            "success": True,
            "data": stats,
            "message": "Comment statistics retrieved successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve comment statistics: {str(e)}"
        )


@router.post("/{comment_id}/mentions", response_model=CommentMentionCreateResponseWrapper, status_code=status.HTTP_201_CREATED)
async def create_comment_mention(
    comment_id: str,
    mention_data: CommentMentionCreateRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a mention in a comment.
    
    Args:
        comment_id: Comment ID
        mention_data: Mention creation data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created mention details
    """
    try:
        # Create mention
        mention = CommentService.create_comment_mention(
            db.session,
            comment_id,
            str(mention_data.mentioned_user_id),
            str(current_user.id)
        )
        
        if not mention:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create mention"
            )
        
        # Get the created mention with related data
        mentions, _ = CommentService.get_comment_mentions(db.session, comment_id, page=1, limit=1)
        created_mention = mentions[0] if mentions else None
        
        if not created_mention:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created mention"
            )
        
        # Convert to response format
        mention_response = CommentMentionResponse(
            id=created_mention.id,
            comment_id=created_mention.comment_id,
            mentioned_user_id=created_mention.mentioned_user_id,
            created_at=created_mention.created_at,
            mentioned_user=UserResponse(
                id=created_mention.mentioned_user.id,
                email=created_mention.mentioned_user.email,
                first_name=created_mention.mentioned_user.first_name,
                last_name=created_mention.mentioned_user.last_name,
                role=created_mention.mentioned_user.role,
                is_active=created_mention.mentioned_user.is_active,
                created_at=created_mention.mentioned_user.created_at,
                updated_at=created_mention.mentioned_user.updated_at
            )
        )
        
        return CommentMentionCreateResponseWrapper(
            success=True,
            data=mention_response,
            message="Mention created successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create mention: {str(e)}"
        )


@router.get("/{comment_id}/mentions", response_model=CommentMentionListResponse)
async def get_comment_mentions(
    comment_id: str,
    page: Optional[int] = Query(1, ge=1, description="Page number"),
    limit: Optional[int] = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get mentions for a specific comment.
    
    Args:
        comment_id: Comment ID
        page: Page number
        limit: Items per page
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of mentions with pagination
    """
    try:
        # Get mentions
        mentions, pagination_info = CommentService.get_comment_mentions(
            db.session,
            comment_id,
            page=page,
            limit=limit
        )
        
        # Convert to response format
        mention_responses = []
        for mention in mentions:
            mention_response = CommentMentionResponse(
                id=mention.id,
                comment_id=mention.comment_id,
                mentioned_user_id=mention.mentioned_user_id,
                created_at=mention.created_at,
                mentioned_user=UserResponse(
                    id=mention.mentioned_user.id,
                    email=mention.mentioned_user.email,
                    first_name=mention.mentioned_user.first_name,
                    last_name=mention.mentioned_user.last_name,
                    role=mention.mentioned_user.role,
                    is_active=mention.mentioned_user.is_active,
                    created_at=mention.mentioned_user.created_at,
                    updated_at=mention.mentioned_user.updated_at
                )
            )
            mention_responses.append(mention_response)
        
        return CommentMentionListResponse(
            success=True,
            data=mention_responses,
            message="Comment mentions retrieved successfully",
            pagination=pagination_info
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve comment mentions: {str(e)}"
        )


@router.delete("/{comment_id}/mentions/{mention_id}", response_model=CommentMentionDeleteResponseWrapper)
async def delete_comment_mention(
    comment_id: str,
    mention_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a mention from a comment.
    
    Args:
        comment_id: Comment ID
        mention_id: Mention ID to delete
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Deletion confirmation
    """
    try:
        # Delete mention
        success = CommentService.delete_comment_mention(
            db.session,
            comment_id,
            mention_id,
            str(current_user.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mention not found"
            )
        
        return CommentMentionDeleteResponseWrapper(
            success=True,
            message="Mention deleted successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete mention: {str(e)}"
        )


@router.post("/{comment_id}/attachments", response_model=CommentAttachmentCreateResponseWrapper, status_code=status.HTTP_201_CREATED)
async def create_comment_attachment(
    comment_id: str,
    attachment_data: CommentAttachmentCreateRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create an attachment for a comment.
    
    Args:
        comment_id: Comment ID
        attachment_data: Attachment creation data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created attachment details
    """
    try:
        # For now, we'll use a placeholder file path
        # In a real implementation, this would handle actual file upload
        file_path = f"/uploads/attachments/{comment_id}/{attachment_data.file_name}"
        
        # Create attachment
        attachment = CommentService.create_comment_attachment(
            db.session,
            comment_id,
            attachment_data.file_name,
            attachment_data.file_size,
            attachment_data.mime_type,
            file_path
        )
        
        if not attachment:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create attachment"
            )
        
        # Get the created attachment with related data
        attachments, _ = CommentService.get_comment_attachments(db.session, comment_id, page=1, limit=1)
        created_attachment = attachments[0] if attachments else None
        
        if not created_attachment:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created attachment"
            )
        
        # Convert to response format
        attachment_response = CommentAttachmentResponse(
            id=created_attachment.id,
            comment_id=created_attachment.comment_id,
            file_name=created_attachment.file_name,
            file_size=created_attachment.file_size,
            mime_type=created_attachment.mime_type,
            file_path=created_attachment.file_path,
            created_at=created_attachment.created_at
        )
        
        return CommentAttachmentCreateResponseWrapper(
            success=True,
            data=attachment_response,
            message="Attachment created successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create attachment: {str(e)}"
        )


@router.get("/{comment_id}/attachments", response_model=CommentAttachmentListResponse)
async def get_comment_attachments(
    comment_id: str,
    page: Optional[int] = Query(1, ge=1, description="Page number"),
    limit: Optional[int] = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get attachments for a specific comment.
    
    Args:
        comment_id: Comment ID
        page: Page number
        limit: Items per page
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of attachments with pagination
    """
    try:
        # Get attachments
        attachments, pagination_info = CommentService.get_comment_attachments(
            db.session,
            comment_id,
            page=page,
            limit=limit
        )
        
        # Convert to response format
        attachment_responses = []
        for attachment in attachments:
            attachment_response = CommentAttachmentResponse(
                id=attachment.id,
                comment_id=attachment.comment_id,
                file_name=attachment.file_name,
                file_size=attachment.file_size,
                mime_type=attachment.mime_type,
                file_path=attachment.file_path,
                created_at=attachment.created_at
            )
            attachment_responses.append(attachment_response)
        
        return CommentAttachmentListResponse(
            success=True,
            data=attachment_responses,
            message="Comment attachments retrieved successfully",
            pagination=pagination_info
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve comment attachments: {str(e)}"
        )


@router.delete("/{comment_id}/attachments/{attachment_id}", response_model=CommentAttachmentDeleteResponseWrapper)
async def delete_comment_attachment(
    comment_id: str,
    attachment_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an attachment from a comment.
    
    Args:
        comment_id: Comment ID
        attachment_id: Attachment ID to delete
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Deletion confirmation
    """
    try:
        # Delete attachment
        success = CommentService.delete_comment_attachment(
            db.session,
            comment_id,
            attachment_id,
            str(current_user.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found"
            )
        
        return CommentAttachmentDeleteResponseWrapper(
            success=True,
            message="Attachment deleted successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete attachment: {str(e)}"
        ) 