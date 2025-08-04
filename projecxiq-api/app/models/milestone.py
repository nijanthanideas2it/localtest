"""
Milestone and MilestoneDependency models for the Project Management Dashboard.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Date, Text, CheckConstraint, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class Milestone(Base):
    """
    Milestone model representing project milestones.
    
    Stores milestone information and completion tracking.
    """
    __tablename__ = 'milestones'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    due_date = Column(Date, nullable=False, index=True)
    is_completed = Column(Boolean, nullable=False, default=False, index=True)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="milestones")
    dependent_milestones = relationship(
        "MilestoneDependency",
        back_populates="dependent_milestone",
        foreign_keys="[MilestoneDependency.dependent_milestone_id]",
        cascade="all, delete-orphan"
    )
    prerequisite_milestones = relationship(
        "MilestoneDependency",
        back_populates="prerequisite_milestone",
        foreign_keys="[MilestoneDependency.prerequisite_milestone_id]",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index('idx_milestones_project_due', 'project_id', 'due_date'),
        Index('idx_milestones_project_completed', 'project_id', 'is_completed'),
    )

    def __repr__(self):
        return f"<Milestone(id={self.id}, name='{self.name}', project_id={self.project_id}, completed={self.is_completed})>"


class MilestoneDependency(Base):
    """
    MilestoneDependency model representing dependencies between milestones.
    
    Implements many-to-many relationship for milestone dependencies.
    """
    __tablename__ = 'milestone_dependencies'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dependent_milestone_id = Column(UUID(as_uuid=True), ForeignKey('milestones.id', ondelete='CASCADE'), nullable=False, index=True)
    prerequisite_milestone_id = Column(UUID(as_uuid=True), ForeignKey('milestones.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=func.now())

    # Relationships
    dependent_milestone = relationship("Milestone", back_populates="dependent_milestones", foreign_keys=[dependent_milestone_id])
    prerequisite_milestone = relationship("Milestone", back_populates="prerequisite_milestones", foreign_keys=[prerequisite_milestone_id])

    __table_args__ = (
        CheckConstraint(
            dependent_milestone_id != prerequisite_milestone_id,
            name='no_self_milestone_dependency'
        ),
        Index('idx_milestone_dependencies_dependent', 'dependent_milestone_id'),
        Index('idx_milestone_dependencies_prerequisite', 'prerequisite_milestone_id'),
        Index('idx_milestone_dependencies_unique', 'dependent_milestone_id', 'prerequisite_milestone_id', unique=True),
    )

    def __repr__(self):
        return f"<MilestoneDependency(id={self.id}, dependent={self.dependent_milestone_id}, prerequisite={self.prerequisite_milestone_id})>" 