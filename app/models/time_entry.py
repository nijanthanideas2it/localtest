"""
TimeEntry model for the Project Management Dashboard.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Date, Text, DECIMAL, CheckConstraint, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class TimeEntry(Base):
    """
    TimeEntry model representing time tracking data for tasks and projects.
    
    Stores time tracking information, approvals, and categorization.
    """
    __tablename__ = 'time_entries'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id', ondelete='CASCADE'), index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    hours = Column(DECIMAL(6, 2), nullable=False)
    date = Column(Date, nullable=False, index=True)
    category = Column(String(20), nullable=False, index=True)
    notes = Column(Text)
    is_approved = Column(Boolean, nullable=False, default=False, index=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), index=True)
    approved_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="time_entries", foreign_keys=[user_id])
    task = relationship("Task", back_populates="time_entries")
    project = relationship("Project", back_populates="time_entries")
    approved_by_user = relationship("User", back_populates="approved_time_entries", foreign_keys=[approved_by])

    __table_args__ = (
        CheckConstraint(
            hours > 0,
            name='positive_hours'
        ),
        CheckConstraint(
            hours <= 24,
            name='max_hours_per_day'
        ),
        CheckConstraint(
            category.in_(['Development', 'Testing', 'Documentation', 'Meeting', 'Other']),
            name='valid_time_category'
        ),
        Index('idx_time_entries_user_date', 'user_id', 'date'),
        Index('idx_time_entries_project_date', 'project_id', 'date'),
        Index('idx_time_entries_task_date', 'task_id', 'date'),
        Index('idx_time_entries_approved', 'is_approved'),
    )

    def __repr__(self):
        return f"<TimeEntry(id={self.id}, user_id={self.user_id}, project_id={self.project_id}, hours={self.hours}, date={self.date})>" 