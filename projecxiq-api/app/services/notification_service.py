"""
Notification service for the Project Management Dashboard.
"""
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from uuid import UUID

from app.models.notification import Notification
from app.models.user import User


class NotificationService:
    """Service class for notification operations."""

    @staticmethod
    def create_notification(
        db: Session,
        user_id: str,
        type: str,
        title: str,
        message: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None
    ) -> Optional[Notification]:
        """
        Create a new notification.
        
        Args:
            db: Database session
            user_id: ID of the user to notify
            type: Type of notification
            title: Notification title
            message: Notification message
            entity_type: Type of related entity
            entity_id: ID of related entity
            
        Returns:
            Created notification or None if creation fails
        """
        try:
            notification = Notification(
                user_id=user_id,
                type=type,
                title=title,
                message=message,
                entity_type=entity_type,
                entity_id=entity_id
            )
            
            db.add(notification)
            db.commit()
            db.refresh(notification)
            return notification
            
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def get_notifications(
        db: Session,
        user_id: str,
        page: int = 1,
        limit: int = 20,
        is_read: Optional[bool] = None,
        type: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None
    ) -> Tuple[List[Notification], Dict[str, Any]]:
        """
        Get notifications for a user with filtering and pagination.
        
        Args:
            db: Database session
            user_id: ID of the user
            page: Page number
            limit: Items per page
            is_read: Filter by read status
            type: Filter by notification type
            entity_type: Filter by entity type
            entity_id: Filter by entity ID
            created_after: Filter by creation date (after)
            created_before: Filter by creation date (before)
            
        Returns:
            Tuple of (notifications, pagination_info)
        """
        query = db.query(Notification).filter(Notification.user_id == user_id)
        
        # Apply filters
        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)
        
        if type:
            query = query.filter(Notification.type == type)
        
        if entity_type:
            query = query.filter(Notification.entity_type == entity_type)
        
        if entity_id:
            query = query.filter(Notification.entity_id == entity_id)
        
        if created_after:
            query = query.filter(Notification.created_at >= created_after)
        
        if created_before:
            query = query.filter(Notification.created_at <= created_before)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        notifications = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()
        
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
        
        return notifications, pagination_info

    @staticmethod
    def get_notification_by_id(
        db: Session,
        notification_id: str,
        user_id: str
    ) -> Optional[Notification]:
        """
        Get a specific notification by ID for a user.
        
        Args:
            db: Database session
            notification_id: ID of the notification
            user_id: ID of the user
            
        Returns:
            Notification or None if not found
        """
        return db.query(Notification).filter(
            and_(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        ).first()

    @staticmethod
    def mark_notification_read(
        db: Session,
        notification_id: str,
        user_id: str
    ) -> Optional[Notification]:
        """
        Mark a notification as read.
        
        Args:
            db: Database session
            notification_id: ID of the notification
            user_id: ID of the user
            
        Returns:
            Updated notification or None if not found
        """
        try:
            notification = NotificationService.get_notification_by_id(db, notification_id, user_id)
            
            if not notification:
                return None
            
            if not notification.is_read:
                notification.is_read = True
                notification.read_at = datetime.now(timezone.utc)
                db.commit()
                db.refresh(notification)
            
            return notification
            
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def mark_all_notifications_read(
        db: Session,
        user_id: str,
        type: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None
    ) -> int:
        """
        Mark all notifications as read for a user.
        
        Args:
            db: Database session
            user_id: ID of the user
            type: Filter by notification type
            entity_type: Filter by entity type
            entity_id: Filter by entity ID
            
        Returns:
            Number of notifications updated
        """
        try:
            query = db.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False
                )
            )
            
            # Apply filters
            if type:
                query = query.filter(Notification.type == type)
            
            if entity_type:
                query = query.filter(Notification.entity_type == entity_type)
            
            if entity_id:
                query = query.filter(Notification.entity_id == entity_id)
            
            # Update all matching notifications
            updated_count = query.update({
                Notification.is_read: True,
                Notification.read_at: datetime.now(timezone.utc)
            })
            
            db.commit()
            return updated_count
            
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def delete_notification(
        db: Session,
        notification_id: str,
        user_id: str
    ) -> bool:
        """
        Delete a notification.
        
        Args:
            db: Database session
            notification_id: ID of the notification
            user_id: ID of the user
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            notification = NotificationService.get_notification_by_id(db, notification_id, user_id)
            
            if not notification:
                return False
            
            db.delete(notification)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def get_notification_stats(
        db: Session,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get notification statistics for a user.
        
        Args:
            db: Database session
            user_id: ID of the user
            
        Returns:
            Dictionary with notification statistics
        """
        try:
            # Total notifications
            total_count = db.query(Notification).filter(Notification.user_id == user_id).count()
            
            # Unread notifications
            unread_count = db.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False
                )
            ).count()
            
            # Notifications by type
            type_counts = db.query(
                Notification.type,
                func.count(Notification.id).label('count')
            ).filter(Notification.user_id == user_id).group_by(Notification.type).all()
            
            # Recent notifications (last 7 days)
            week_ago = datetime.now(timezone.utc) - timedelta(days=7)
            recent_count = db.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.created_at >= week_ago
                )
            ).count()
            
            # Notifications by entity type
            entity_type_counts = db.query(
                Notification.entity_type,
                func.count(Notification.id).label('count')
            ).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.entity_type.isnot(None)
                )
            ).group_by(Notification.entity_type).all()
            
            return {
                "total_count": total_count,
                "unread_count": unread_count,
                "read_count": total_count - unread_count,
                "recent_count": recent_count,
                "type_breakdown": {item.type: item.count for item in type_counts},
                "entity_type_breakdown": {item.entity_type: item.count for item in entity_type_counts if item.entity_type}
            }
            
        except Exception as e:
            raise e

    @staticmethod
    def create_system_notification(
        db: Session,
        user_id: str,
        title: str,
        message: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None
    ) -> Optional[Notification]:
        """
        Create a system notification for a user.
        
        Args:
            db: Database session
            user_id: ID of the user
            title: Notification title
            message: Notification message
            entity_type: Type of related entity
            entity_id: ID of related entity
            
        Returns:
            Created notification or None if creation fails
        """
        return NotificationService.create_notification(
            db=db,
            user_id=user_id,
            type="system_alert",
            title=title,
            message=message,
            entity_type=entity_type,
            entity_id=entity_id
        ) 