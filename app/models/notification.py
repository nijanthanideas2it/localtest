"""
Notification model for the Project Management Dashboard.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, CheckConstraint, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class Notification(Base):
    """
    Notification model representing system notifications for users.
    
    Stores notification information, read status, and entity references.
    """
    __tablename__ = 'notifications'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    entity_type = Column(String(20), index=True)
    entity_id = Column(UUID(as_uuid=True), index=True)
    is_read = Column(Boolean, nullable=False, default=False, index=True)
    read_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=func.now())

    # Relationships
    user = relationship("User", back_populates="notifications")

    __table_args__ = (
        Index('idx_notifications_user_read', 'user_id', 'is_read'),
        Index('idx_notifications_user_created', 'user_id', 'created_at'),
        Index('idx_notifications_entity', 'entity_type', 'entity_id'),
        Index('idx_notifications_type', 'type'),
    )

    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, type='{self.type}', is_read={self.is_read})>" 