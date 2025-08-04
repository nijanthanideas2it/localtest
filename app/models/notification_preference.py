"""
Notification Preference model for the Project Management Dashboard.
"""
from sqlalchemy import Column, String, Boolean, DateTime, CheckConstraint, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class NotificationPreference(Base):
    """
    NotificationPreference model representing user notification settings.
    
    Stores user preferences for different types of notifications.
    """
    __tablename__ = 'notification_preferences'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    notification_type = Column(String(50), nullable=False, index=True)
    email_enabled = Column(Boolean, nullable=False, default=True)
    push_enabled = Column(Boolean, nullable=False, default=True)
    in_app_enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="notification_preferences")

    __table_args__ = (
        Index('idx_notification_preferences_user_type', 'user_id', 'notification_type'),
        CheckConstraint(
            "notification_type IN ('task_assigned', 'task_completed', 'task_overdue', 'task_updated', 'project_created', 'project_updated', 'project_completed', 'comment_added', 'mention_added', 'time_entry_approved', 'time_entry_rejected', 'milestone_reached', 'deadline_approaching', 'system_alert')",
            name='valid_notification_type'
        ),
    )

    def __repr__(self):
        return f"<NotificationPreference(id={self.id}, user_id={self.user_id}, type='{self.notification_type}', email={self.email_enabled}, push={self.push_enabled}, in_app={self.in_app_enabled})>" 