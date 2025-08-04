"""
Notification Preference service for the Project Management Dashboard.
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from uuid import UUID

from app.models.notification_preference import NotificationPreference
from app.models.user import User


class NotificationPreferenceService:
    """Service class for notification preference operations."""

    @staticmethod
    def create_notification_preference(
        db: Session,
        user_id: str,
        notification_type: str,
        email_enabled: bool = True,
        push_enabled: bool = True,
        in_app_enabled: bool = True
    ) -> Optional[NotificationPreference]:
        """
        Create a new notification preference.
        
        Args:
            db: Database session
            user_id: ID of the user
            notification_type: Type of notification
            email_enabled: Enable email notifications
            push_enabled: Enable push notifications
            in_app_enabled: Enable in-app notifications
            
        Returns:
            Created notification preference or None if creation fails
        """
        try:
            # Check if preference already exists
            existing_preference = NotificationPreferenceService.get_notification_preference_by_type(
                db, user_id, notification_type
            )
            
            if existing_preference:
                raise ValueError(f"Notification preference for type '{notification_type}' already exists")
            
            preference = NotificationPreference(
                user_id=user_id,
                notification_type=notification_type,
                email_enabled=email_enabled,
                push_enabled=push_enabled,
                in_app_enabled=in_app_enabled
            )
            
            db.add(preference)
            db.commit()
            db.refresh(preference)
            return preference
            
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def get_notification_preferences(
        db: Session,
        user_id: str
    ) -> List[NotificationPreference]:
        """
        Get all notification preferences for a user.
        
        Args:
            db: Database session
            user_id: ID of the user
            
        Returns:
            List of notification preferences
        """
        return db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).order_by(NotificationPreference.notification_type).all()

    @staticmethod
    def get_notification_preference_by_type(
        db: Session,
        user_id: str,
        notification_type: str
    ) -> Optional[NotificationPreference]:
        """
        Get a specific notification preference by type for a user.
        
        Args:
            db: Database session
            user_id: ID of the user
            notification_type: Type of notification
            
        Returns:
            Notification preference or None if not found
        """
        return db.query(NotificationPreference).filter(
            and_(
                NotificationPreference.user_id == user_id,
                NotificationPreference.notification_type == notification_type
            )
        ).first()

    @staticmethod
    def update_notification_preference(
        db: Session,
        user_id: str,
        notification_type: str,
        email_enabled: Optional[bool] = None,
        push_enabled: Optional[bool] = None,
        in_app_enabled: Optional[bool] = None
    ) -> Optional[NotificationPreference]:
        """
        Update a notification preference.
        
        Args:
            db: Database session
            user_id: ID of the user
            notification_type: Type of notification
            email_enabled: Enable email notifications
            push_enabled: Enable push notifications
            in_app_enabled: Enable in-app notifications
            
        Returns:
            Updated notification preference or None if not found
        """
        try:
            preference = NotificationPreferenceService.get_notification_preference_by_type(
                db, user_id, notification_type
            )
            
            if not preference:
                return None
            
            # Update only provided fields
            if email_enabled is not None:
                preference.email_enabled = email_enabled
            if push_enabled is not None:
                preference.push_enabled = push_enabled
            if in_app_enabled is not None:
                preference.in_app_enabled = in_app_enabled
            
            preference.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(preference)
            return preference
            
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def delete_notification_preference(
        db: Session,
        user_id: str,
        notification_type: str
    ) -> bool:
        """
        Delete a notification preference.
        
        Args:
            db: Database session
            user_id: ID of the user
            notification_type: Type of notification
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            preference = NotificationPreferenceService.get_notification_preference_by_type(
                db, user_id, notification_type
            )
            
            if not preference:
                return False
            
            db.delete(preference)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def bulk_update_notification_preferences(
        db: Session,
        user_id: str,
        preferences: List[Dict[str, Any]]
    ) -> List[NotificationPreference]:
        """
        Bulk update notification preferences for a user.
        
        Args:
            db: Database session
            user_id: ID of the user
            preferences: List of preference dictionaries
            
        Returns:
            List of updated notification preferences
        """
        try:
            updated_preferences = []
            
            for pref_data in preferences:
                notification_type = pref_data.get('notification_type')
                email_enabled = pref_data.get('email_enabled', True)
                push_enabled = pref_data.get('push_enabled', True)
                in_app_enabled = pref_data.get('in_app_enabled', True)
                
                # Check if preference exists
                existing_preference = NotificationPreferenceService.get_notification_preference_by_type(
                    db, user_id, notification_type
                )
                
                if existing_preference:
                    # Update existing preference
                    existing_preference.email_enabled = email_enabled
                    existing_preference.push_enabled = push_enabled
                    existing_preference.in_app_enabled = in_app_enabled
                    existing_preference.updated_at = datetime.now(timezone.utc)
                    updated_preferences.append(existing_preference)
                else:
                    # Create new preference
                    new_preference = NotificationPreference(
                        user_id=user_id,
                        notification_type=notification_type,
                        email_enabled=email_enabled,
                        push_enabled=push_enabled,
                        in_app_enabled=in_app_enabled
                    )
                    db.add(new_preference)
                    updated_preferences.append(new_preference)
            
            db.commit()
            
            # Refresh all preferences
            for preference in updated_preferences:
                db.refresh(preference)
            
            return updated_preferences
            
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def get_notification_preference_stats(
        db: Session,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get notification preference statistics for a user.
        
        Args:
            db: Database session
            user_id: ID of the user
            
        Returns:
            Dictionary with notification preference statistics
        """
        try:
            # Total preferences
            total_count = db.query(NotificationPreference).filter(
                NotificationPreference.user_id == user_id
            ).count()
            
            # Preferences by type
            type_counts = db.query(
                NotificationPreference.notification_type,
                func.count(NotificationPreference.id).label('count')
            ).filter(NotificationPreference.user_id == user_id).group_by(
                NotificationPreference.notification_type
            ).all()
            
            # Email enabled count
            email_enabled_count = db.query(NotificationPreference).filter(
                and_(
                    NotificationPreference.user_id == user_id,
                    NotificationPreference.email_enabled == True
                )
            ).count()
            
            # Push enabled count
            push_enabled_count = db.query(NotificationPreference).filter(
                and_(
                    NotificationPreference.user_id == user_id,
                    NotificationPreference.push_enabled == True
                )
            ).count()
            
            # In-app enabled count
            in_app_enabled_count = db.query(NotificationPreference).filter(
                and_(
                    NotificationPreference.user_id == user_id,
                    NotificationPreference.in_app_enabled == True
                )
            ).count()
            
            # All enabled count
            all_enabled_count = db.query(NotificationPreference).filter(
                and_(
                    NotificationPreference.user_id == user_id,
                    NotificationPreference.email_enabled == True,
                    NotificationPreference.push_enabled == True,
                    NotificationPreference.in_app_enabled == True
                )
            ).count()
            
            return {
                "total_count": total_count,
                "type_breakdown": {item.notification_type: item.count for item in type_counts},
                "email_enabled_count": email_enabled_count,
                "push_enabled_count": push_enabled_count,
                "in_app_enabled_count": in_app_enabled_count,
                "all_enabled_count": all_enabled_count,
                "partially_enabled_count": total_count - all_enabled_count
            }
            
        except Exception as e:
            raise e

    @staticmethod
    def create_default_preferences(
        db: Session,
        user_id: str
    ) -> List[NotificationPreference]:
        """
        Create default notification preferences for a user.
        
        Args:
            db: Database session
            user_id: ID of the user
            
        Returns:
            List of created notification preferences
        """
        try:
            default_types = [
                'task_assigned', 'task_completed', 'task_overdue', 'task_updated',
                'project_created', 'project_updated', 'project_completed',
                'comment_added', 'mention_added', 'time_entry_approved', 'time_entry_rejected',
                'milestone_reached', 'deadline_approaching', 'system_alert'
            ]
            
            created_preferences = []
            
            for notification_type in default_types:
                # Check if preference already exists
                existing = NotificationPreferenceService.get_notification_preference_by_type(
                    db, user_id, notification_type
                )
                
                if not existing:
                    preference = NotificationPreference(
                        user_id=user_id,
                        notification_type=notification_type,
                        email_enabled=True,
                        push_enabled=True,
                        in_app_enabled=True
                    )
                    db.add(preference)
                    created_preferences.append(preference)
            
            db.commit()
            
            # Refresh all created preferences
            for preference in created_preferences:
                db.refresh(preference)
            
            return created_preferences
            
        except Exception as e:
            db.rollback()
            raise e 