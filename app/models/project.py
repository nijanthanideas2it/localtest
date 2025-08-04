"""
Project and ProjectTeamMember models for the Project Management Dashboard.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Date, Text, DECIMAL, CheckConstraint, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class Project(Base):
    """
    Project model representing projects in the system.
    
    Stores project information, metadata, and status tracking.
    """
    __tablename__ = 'projects'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, index=True)
    budget = Column(DECIMAL(15, 2), default=0.00)
    actual_cost = Column(DECIMAL(15, 2), default=0.00)
    status = Column(String(20), nullable=False, default='Draft', index=True)
    manager_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='RESTRICT'), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    manager = relationship("User", back_populates="managed_projects", foreign_keys=[manager_id])
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    milestones = relationship("Milestone", back_populates="project", cascade="all, delete-orphan")
    time_entries = relationship("TimeEntry", back_populates="project", cascade="all, delete-orphan")
    team_members = relationship("ProjectTeamMember", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            status.in_(['Draft', 'Active', 'OnHold', 'Completed', 'Cancelled']),
            name='valid_project_status'
        ),
        CheckConstraint(
            end_date >= start_date,
            name='valid_project_dates'
        ),
        Index('idx_projects_status_dates', 'status', 'start_date', 'end_date'),
        Index('idx_projects_manager_status', 'manager_id', 'status'),
    )

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', status='{self.status}')>"


class ProjectTeamMember(Base):
    """
    ProjectTeamMember model representing team member assignments to projects.
    
    Implements many-to-many relationship between projects and users.
    """
    __tablename__ = 'project_team_members'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    role = Column(String(50), nullable=False)
    joined_at = Column(DateTime, nullable=False, default=func.now())
    left_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=func.now())

    # Relationships
    project = relationship("Project", back_populates="team_members")
    user = relationship("User", back_populates="project_team_memberships")

    __table_args__ = (
        Index('idx_project_team_members_project_user', 'project_id', 'user_id', unique=True),
        Index('idx_project_team_members_user_active', 'user_id', 'left_at'),
    )

    def __repr__(self):
        return f"<ProjectTeamMember(id={self.id}, project_id={self.project_id}, user_id={self.user_id}, role='{self.role}')>" 