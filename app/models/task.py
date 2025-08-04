"""
Task and TaskDependency models for the Project Management Dashboard.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Date, Text, DECIMAL, CheckConstraint, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class Task(Base):
    """
    Task model representing tasks within projects.
    
    Stores task information, assignments, and progress tracking.
    """
    __tablename__ = 'tasks'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    assignee_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), index=True)
    status = Column(String(20), nullable=False, default='ToDo', index=True)
    priority = Column(String(20), nullable=False, default='Medium', index=True)
    estimated_hours = Column(DECIMAL(8, 2), default=0.00)
    actual_hours = Column(DECIMAL(8, 2), default=0.00)
    due_date = Column(Date, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", back_populates="assigned_tasks", foreign_keys=[assignee_id])
    time_entries = relationship("TimeEntry", back_populates="task", cascade="all, delete-orphan")
    dependent_tasks = relationship(
        "TaskDependency",
        back_populates="dependent_task",
        foreign_keys="[TaskDependency.dependent_task_id]",
        cascade="all, delete-orphan"
    )
    prerequisite_tasks = relationship(
        "TaskDependency",
        back_populates="prerequisite_task",
        foreign_keys="[TaskDependency.prerequisite_task_id]",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            status.in_(['ToDo', 'InProgress', 'Review', 'Done']),
            name='valid_task_status'
        ),
        CheckConstraint(
            priority.in_(['Low', 'Medium', 'High', 'Critical']),
            name='valid_task_priority'
        ),
        CheckConstraint(
            estimated_hours >= 0,
            name='valid_estimated_hours'
        ),
        CheckConstraint(
            actual_hours >= 0,
            name='valid_actual_hours'
        ),
        Index('idx_tasks_project_status', 'project_id', 'status'),
        Index('idx_tasks_assignee_status', 'assignee_id', 'status'),
        Index('idx_tasks_due_date', 'due_date'),
        Index('idx_tasks_priority_status', 'priority', 'status'),
    )

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}', project_id={self.project_id})>"


class TaskDependency(Base):
    """
    TaskDependency model representing dependencies between tasks.
    
    Implements many-to-many relationship for task dependencies.
    """
    __tablename__ = 'task_dependencies'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dependent_task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False, index=True)
    prerequisite_task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False, index=True)
    dependency_type = Column(String(20), nullable=False, default='Blocks')
    created_at = Column(DateTime, nullable=False, default=func.now())

    # Relationships
    dependent_task = relationship("Task", back_populates="dependent_tasks", foreign_keys=[dependent_task_id])
    prerequisite_task = relationship("Task", back_populates="prerequisite_tasks", foreign_keys=[prerequisite_task_id])

    __table_args__ = (
        CheckConstraint(
            dependency_type.in_(['Blocks', 'DependsOn', 'RelatedTo']),
            name='valid_dependency_type'
        ),
        CheckConstraint(
            dependent_task_id != prerequisite_task_id,
            name='no_self_dependency'
        ),
        Index('idx_task_dependencies_dependent', 'dependent_task_id'),
        Index('idx_task_dependencies_prerequisite', 'prerequisite_task_id'),
        Index('idx_task_dependencies_unique', 'dependent_task_id', 'prerequisite_task_id', unique=True),
    )

    def __repr__(self):
        return f"<TaskDependency(id={self.id}, dependent={self.dependent_task_id}, prerequisite={self.prerequisite_task_id}, type='{self.dependency_type}')>" 