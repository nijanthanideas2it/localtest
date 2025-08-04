"""
Comment service layer for comment management operations.
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, text
from uuid import UUID

from app.models.comment import Comment, CommentMention, CommentAttachment
from app.models.project import Project
from app.models.task import Task
from app.models.milestone import Milestone
from app.models.user import User
from app.schemas.comment import (
    CommentCreateRequest,
    CommentUpdateRequest
)


class CommentService:
    """Service class for comment management operations."""
    
    @staticmethod
    def create_comment(
        db: Session,
        comment_data: CommentCreateRequest,
        current_user_id: str
    ) -> Optional[Comment]:
        """
        Create a new comment.
        
        Args:
            db: Database session
            comment_data: Comment creation data
            current_user_id: ID of the user creating the comment
            
        Returns:
            Created comment or None if creation fails
        """
        try:
            # Validate entity exists
            entity = CommentService._validate_entity_exists(
                db, comment_data.entity_type, comment_data.entity_id
            )
            if not entity:
                raise ValueError(f"{comment_data.entity_type} not found")
            
            # Validate parent comment exists if provided
            if comment_data.parent_comment_id:
                parent_comment = db.query(Comment).filter(
                    Comment.id == comment_data.parent_comment_id
                ).first()
                if not parent_comment:
                    raise ValueError("Parent comment not found")
                
                # Validate parent comment belongs to the same entity
                if (parent_comment.entity_type != comment_data.entity_type or 
                    parent_comment.entity_id != comment_data.entity_id):
                    raise ValueError("Parent comment must belong to the same entity")
            
            # Create comment
            comment = Comment(
                content=comment_data.content,
                author_id=current_user_id,
                entity_type=comment_data.entity_type,
                entity_id=comment_data.entity_id,
                parent_comment_id=comment_data.parent_comment_id
            )
            
            db.add(comment)
            db.commit()
            db.refresh(comment)
            return comment
            
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def get_comment_by_id(db: Session, comment_id: str) -> Optional[Comment]:
        """
        Get comment by ID with all related data.
        
        Args:
            db: Database session
            comment_id: Comment ID
            
        Returns:
            Comment with related data or None if not found
        """
        return db.query(Comment).options(
            joinedload(Comment.author),
            joinedload(Comment.replies),
            joinedload(Comment.mentions),
            joinedload(Comment.attachments)
        ).filter(Comment.id == comment_id).first()
    
    @staticmethod
    def get_comments(
        db: Session,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        author_id: Optional[str] = None,
        parent_comment_id: Optional[str] = None,
        include_replies: bool = True,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Comment], Dict[str, Any]]:
        """
        Get comments with filtering and pagination.
        
        Args:
            db: Database session
            entity_type: Filter by entity type
            entity_id: Filter by entity ID
            author_id: Filter by author ID
            parent_comment_id: Filter by parent comment ID
            include_replies: Include replies in results
            page: Page number
            limit: Items per page
            
        Returns:
            Tuple of (comments, pagination_info)
        """
        query = db.query(Comment).options(
            joinedload(Comment.author),
            joinedload(Comment.replies),
            joinedload(Comment.mentions),
            joinedload(Comment.attachments)
        )
        
        # Apply filters
        if entity_type:
            query = query.filter(Comment.entity_type == entity_type)
        if entity_id:
            query = query.filter(Comment.entity_id == entity_id)
        if author_id:
            query = query.filter(Comment.author_id == author_id)
        if parent_comment_id:
            query = query.filter(Comment.parent_comment_id == parent_comment_id)
        elif not include_replies:
            # Only top-level comments (no parent)
            query = query.filter(Comment.parent_comment_id.is_(None))
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        comments = query.order_by(Comment.created_at.desc()).offset(offset).limit(limit).all()
        
        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit
        pagination_info = {
            "page": page,
            "limit": limit,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
        
        return comments, pagination_info
    
    @staticmethod
    def search_comments(
        db: Session,
        query: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        author_id: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Comment], Dict[str, Any]]:
        """
        Search comments by content.
        
        Args:
            db: Database session
            query: Search query
            entity_type: Filter by entity type
            entity_id: Filter by entity ID
            author_id: Filter by author ID
            page: Page number
            limit: Items per page
            
        Returns:
            Tuple of (comments, pagination_info)
        """
        search_query = db.query(Comment).options(
            joinedload(Comment.author),
            joinedload(Comment.replies),
            joinedload(Comment.mentions),
            joinedload(Comment.attachments)
        ).filter(
            Comment.content.ilike(f"%{query}%")
        )
        
        # Apply additional filters
        if entity_type:
            search_query = search_query.filter(Comment.entity_type == entity_type)
        if entity_id:
            search_query = search_query.filter(Comment.entity_id == entity_id)
        if author_id:
            search_query = search_query.filter(Comment.author_id == author_id)
        
        # Get total count
        total_count = search_query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        comments = search_query.order_by(Comment.created_at.desc()).offset(offset).limit(limit).all()
        
        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit
        pagination_info = {
            "page": page,
            "limit": limit,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
        
        return comments, pagination_info
    
    @staticmethod
    def get_comment_thread(
        db: Session,
        comment_id: str,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Comment], Dict[str, Any], Dict[str, Any]]:
        """
        Get a comment thread with all replies.
        
        Args:
            db: Database session
            comment_id: Root comment ID
            page: Page number
            limit: Items per page
            
        Returns:
            Tuple of (comments, pagination_info, thread_info)
        """
        # Get the root comment
        root_comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not root_comment:
            raise ValueError("Comment not found")
        
        # Get all comments in the thread (root + all replies)
        thread_query = db.query(Comment).options(
            joinedload(Comment.author),
            joinedload(Comment.replies),
            joinedload(Comment.mentions),
            joinedload(Comment.attachments)
        ).filter(
            or_(
                Comment.id == comment_id,
                Comment.parent_comment_id == comment_id,
                Comment.parent_comment_id.in_(
                    db.query(Comment.id).filter(Comment.parent_comment_id == comment_id)
                )
            )
        )
        
        # Get total count
        total_count = thread_query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        comments = thread_query.order_by(Comment.created_at.asc()).offset(offset).limit(limit).all()
        
        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit
        pagination_info = {
            "page": page,
            "limit": limit,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
        
        # Calculate thread info
        total_replies = db.query(Comment).filter(
            Comment.parent_comment_id == comment_id
        ).count()
        
        # Calculate max depth (simplified - could be enhanced for deeper nesting)
        max_depth = 1
        if total_replies > 0:
            max_depth = 2  # For now, assume max depth of 2 levels
        
        thread_info = {
            "total_comments": total_count,
            "total_replies": total_replies,
            "max_depth": max_depth,
            "root_comment_id": comment_id
        }
        
        return comments, pagination_info, thread_info
    
    @staticmethod
    def update_comment(
        db: Session,
        comment_id: str,
        update_data: CommentUpdateRequest,
        current_user_id: str
    ) -> Optional[Comment]:
        """
        Update an existing comment.
        
        Args:
            db: Database session
            comment_id: Comment ID to update
            update_data: Update data
            current_user_id: ID of the user updating the comment
            
        Returns:
            Updated comment or None if update fails
        """
        try:
            comment = db.query(Comment).filter(Comment.id == comment_id).first()
            if not comment:
                raise ValueError("Comment not found")
            
            # Check if user can update the comment
            if not CommentService.can_update_comment(comment, current_user_id):
                raise ValueError("You can only update your own comments")
            
            # Check if comment is within editable period (e.g., 24 hours)
            if not CommentService.is_within_editable_period(comment):
                raise ValueError("Comment can only be edited within 24 hours of creation")
            
            # Update comment
            comment.content = update_data.content
            comment.updated_at = datetime.now(timezone.utc)
            
            db.commit()
            db.refresh(comment)
            return comment
            
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def delete_comment(
        db: Session,
        comment_id: str,
        current_user_id: str
    ) -> bool:
        """
        Delete a comment.
        
        Args:
            db: Database session
            comment_id: Comment ID to delete
            current_user_id: ID of the user deleting the comment
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            comment = db.query(Comment).filter(Comment.id == comment_id).first()
            if not comment:
                raise ValueError("Comment not found")
            
            # Check if user can delete the comment
            if not CommentService.can_delete_comment(comment, current_user_id):
                raise ValueError("You can only delete your own comments")
            
            # Check if comment is within deletable period (e.g., 24 hours)
            if not CommentService.is_within_editable_period(comment):
                raise ValueError("Comment can only be deleted within 24 hours of creation")
            
            # Delete comment (cascade will handle replies, mentions, attachments)
            db.delete(comment)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def can_update_comment(comment: Comment, current_user_id: str) -> bool:
        """
        Check if user can update a comment.
        
        Args:
            comment: Comment to check
            current_user_id: ID of the current user
            
        Returns:
            True if user can update, False otherwise
        """
        return str(comment.author_id) == current_user_id
    
    @staticmethod
    def can_delete_comment(comment: Comment, current_user_id: str) -> bool:
        """
        Check if user can delete a comment.
        
        Args:
            comment: Comment to check
            current_user_id: ID of the current user
            
        Returns:
            True if user can delete, False otherwise
        """
        return str(comment.author_id) == current_user_id
    
    @staticmethod
    def is_within_editable_period(comment: Comment) -> bool:
        """
        Check if comment is within the editable period (24 hours).
        
        Args:
            comment: Comment to check
            
        Returns:
            True if within editable period, False otherwise
        """
        now = datetime.now(timezone.utc)
        time_diff = now - comment.created_at
        return time_diff.total_seconds() <= 24 * 60 * 60  # 24 hours
    
    @staticmethod
    def get_comment_statistics(
        db: Session,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        author_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comment statistics.
        
        Args:
            db: Database session
            entity_type: Filter by entity type
            entity_id: Filter by entity ID
            author_id: Filter by author ID
            
        Returns:
            Dictionary with comment statistics
        """
        query = db.query(Comment)
        
        # Apply filters
        if entity_type:
            query = query.filter(Comment.entity_type == entity_type)
        if entity_id:
            query = query.filter(Comment.entity_id == entity_id)
        if author_id:
            query = query.filter(Comment.author_id == author_id)
        
        # Calculate statistics
        total_comments = query.count()
        total_replies = query.filter(Comment.parent_comment_id.isnot(None)).count()
        top_level_comments = query.filter(Comment.parent_comment_id.is_(None)).count()
        
        # Get comments by entity type
        comments_by_entity = db.query(
            Comment.entity_type,
            func.count(Comment.id).label('count')
        ).group_by(Comment.entity_type).all()
        
        # Get recent activity
        recent_comments = query.order_by(Comment.created_at.desc()).limit(5).all()
        
        return {
            "total_comments": total_comments,
            "total_replies": total_replies,
            "top_level_comments": top_level_comments,
            "comments_by_entity": {item.entity_type: item.count for item in comments_by_entity},
            "recent_activity": [
                {
                    "id": str(comment.id),
                    "content": comment.content[:100] + "..." if len(comment.content) > 100 else comment.content,
                    "created_at": comment.created_at.isoformat(),
                    "entity_type": comment.entity_type,
                    "entity_id": str(comment.entity_id)
                }
                for comment in recent_comments
            ]
        }
    
    @staticmethod
    def _validate_entity_exists(db: Session, entity_type: str, entity_id: str) -> bool:
        """
        Validate that the entity exists in the database.
        
        Args:
            db: Database session
            entity_type: Type of entity
            entity_id: Entity ID
            
        Returns:
            True if entity exists, False otherwise
        """
        if entity_type == 'Project':
            return db.query(Project).filter(Project.id == entity_id).first() is not None
        elif entity_type == 'Task':
            return db.query(Task).filter(Task.id == entity_id).first() is not None
        elif entity_type == 'Milestone':
            return db.query(Milestone).filter(Milestone.id == entity_id).first() is not None
        else:
            return False

    @staticmethod
    def create_comment_mention(
        db: Session,
        comment_id: str,
        mentioned_user_id: str,
        current_user_id: str
    ) -> Optional[CommentMention]:
        """
        Create a mention in a comment.
        
        Args:
            db: Database session
            comment_id: Comment ID
            mentioned_user_id: ID of the user being mentioned
            current_user_id: ID of the user creating the mention
            
        Returns:
            Created mention or None if creation fails
        """
        try:
            # Validate comment exists
            comment = db.query(Comment).filter(Comment.id == comment_id).first()
            if not comment:
                raise ValueError("Comment not found")
            
            # Validate mentioned user exists
            mentioned_user = db.query(User).filter(User.id == mentioned_user_id).first()
            if not mentioned_user:
                raise ValueError("Mentioned user not found")
            
            # Check if mention already exists
            existing_mention = db.query(CommentMention).filter(
                and_(
                    CommentMention.comment_id == comment_id,
                    CommentMention.mentioned_user_id == mentioned_user_id
                )
            ).first()
            
            if existing_mention:
                raise ValueError("User is already mentioned in this comment")
            
            # Create mention
            mention = CommentMention(
                comment_id=comment_id,
                mentioned_user_id=mentioned_user_id
            )
            
            db.add(mention)
            db.commit()
            db.refresh(mention)
            return mention
            
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def get_comment_mentions(
        db: Session,
        comment_id: str,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[CommentMention], Dict[str, Any]]:
        """
        Get mentions for a specific comment.
        
        Args:
            db: Database session
            comment_id: Comment ID
            page: Page number
            limit: Items per page
            
        Returns:
            Tuple of (mentions, pagination_info)
        """
        query = db.query(CommentMention).options(
            joinedload(CommentMention.mentioned_user)
        ).filter(CommentMention.comment_id == comment_id)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        mentions = query.order_by(CommentMention.created_at.desc()).offset(offset).limit(limit).all()
        
        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit
        pagination_info = {
            "page": page,
            "limit": limit,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
        
        return mentions, pagination_info

    @staticmethod
    def get_user_mentions(
        db: Session,
        user_id: str,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[CommentMention], Dict[str, Any]]:
        """
        Get all mentions for a specific user.
        
        Args:
            db: Database session
            user_id: User ID
            page: Page number
            limit: Items per page
            
        Returns:
            Tuple of (mentions, pagination_info)
        """
        query = db.query(CommentMention).options(
            joinedload(CommentMention.mentioned_user),
            joinedload(CommentMention.comment)
        ).filter(CommentMention.mentioned_user_id == user_id)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        mentions = query.order_by(CommentMention.created_at.desc()).offset(offset).limit(limit).all()
        
        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit
        pagination_info = {
            "page": page,
            "limit": limit,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
        
        return mentions, pagination_info

    @staticmethod
    def delete_comment_mention(
        db: Session,
        comment_id: str,
        mention_id: str,
        current_user_id: str
    ) -> bool:
        """
        Delete a mention from a comment.
        
        Args:
            db: Database session
            comment_id: Comment ID
            mention_id: Mention ID to delete
            current_user_id: ID of the user deleting the mention
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            # Get the mention
            mention = db.query(CommentMention).filter(
                and_(
                    CommentMention.id == mention_id,
                    CommentMention.comment_id == comment_id
                )
            ).first()
            
            if not mention:
                raise ValueError("Mention not found")
            
            # Get the comment to check permissions
            comment = db.query(Comment).filter(Comment.id == comment_id).first()
            if not comment:
                raise ValueError("Comment not found")
            
            # Check if user can delete the mention (comment author or mention creator)
            if not (str(comment.author_id) == current_user_id or 
                   CommentService.can_update_comment(comment, current_user_id)):
                raise ValueError("You can only delete mentions from your own comments")
            
            # Delete mention
            db.delete(mention)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def can_delete_mention(mention: CommentMention, current_user_id: str) -> bool:
        """
        Check if user can delete a mention.
        
        Args:
            mention: Mention to check
            current_user_id: ID of the current user
            
        Returns:
            True if user can delete, False otherwise
        """
        # Get the comment to check permissions
        comment = mention.comment
        return str(comment.author_id) == current_user_id

    @staticmethod
    def create_comment_attachment(
        db: Session,
        comment_id: str,
        file_name: str,
        file_size: int,
        mime_type: str,
        file_path: str
    ) -> Optional[CommentAttachment]:
        """
        Create an attachment for a comment.
        
        Args:
            db: Database session
            comment_id: Comment ID
            file_name: Name of the file
            file_size: Size of the file in bytes
            mime_type: MIME type of the file
            file_path: Path where the file is stored
            
        Returns:
            Created attachment or None if creation fails
        """
        try:
            # Validate comment exists
            comment = db.query(Comment).filter(Comment.id == comment_id).first()
            if not comment:
                raise ValueError("Comment not found")
            
            # Create attachment
            attachment = CommentAttachment(
                comment_id=comment_id,
                file_name=file_name,
                file_size=file_size,
                mime_type=mime_type,
                file_path=file_path
            )
            
            db.add(attachment)
            db.commit()
            db.refresh(attachment)
            return attachment
            
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def get_comment_attachments(
        db: Session,
        comment_id: str,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[CommentAttachment], Dict[str, Any]]:
        """
        Get attachments for a specific comment.
        
        Args:
            db: Database session
            comment_id: Comment ID
            page: Page number
            limit: Items per page
            
        Returns:
            Tuple of (attachments, pagination_info)
        """
        query = db.query(CommentAttachment).filter(CommentAttachment.comment_id == comment_id)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        attachments = query.order_by(CommentAttachment.created_at.desc()).offset(offset).limit(limit).all()
        
        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit
        pagination_info = {
            "page": page,
            "limit": limit,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
        
        return attachments, pagination_info

    @staticmethod
    def delete_comment_attachment(
        db: Session,
        comment_id: str,
        attachment_id: str,
        current_user_id: str
    ) -> bool:
        """
        Delete an attachment from a comment.
        
        Args:
            db: Database session
            comment_id: Comment ID
            attachment_id: Attachment ID to delete
            current_user_id: ID of the user deleting the attachment
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            # Get the attachment
            attachment = db.query(CommentAttachment).filter(
                and_(
                    CommentAttachment.id == attachment_id,
                    CommentAttachment.comment_id == comment_id
                )
            ).first()
            
            if not attachment:
                raise ValueError("Attachment not found")
            
            # Get the comment to check permissions
            comment = db.query(Comment).filter(Comment.id == comment_id).first()
            if not comment:
                raise ValueError("Comment not found")
            
            # Check if user can delete the attachment (comment author)
            if not str(comment.author_id) == current_user_id:
                raise ValueError("You can only delete attachments from your own comments")
            
            # Delete attachment
            db.delete(attachment)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def can_delete_attachment(attachment: CommentAttachment, current_user_id: str) -> bool:
        """
        Check if user can delete an attachment.
        
        Args:
            attachment: Attachment to check
            current_user_id: ID of the current user
            
        Returns:
            True if user can delete, False otherwise
        """
        # Get the comment to check permissions
        comment = attachment.comment
        return str(comment.author_id) == current_user_id 