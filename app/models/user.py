"""
User and UserSkill models for the Project Management Dashboard.
"""
from sqlalchemy import Column, String, Boolean, DateTime, DECIMAL, CheckConstraint, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class User(Base):
    """
    User model representing application users.
    
    Stores user account information, profile data, and authentication details.
    """
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, index=True)
    hourly_rate = Column(DECIMAL(10, 2), default=0.00)
    avatar_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    managed_projects = relationship("Project", back_populates="manager", foreign_keys="[Project.manager_id]")
    assigned_tasks = relationship("Task", back_populates="assignee", foreign_keys="[Task.assignee_id]")
    time_entries = relationship("TimeEntry", back_populates="user", foreign_keys="[TimeEntry.user_id]")
    comments = relationship("Comment", back_populates="author")
    skills = relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")
    project_team_memberships = relationship("ProjectTeamMember", back_populates="user", cascade="all, delete-orphan")
    approved_time_entries = relationship("TimeEntry", back_populates="approved_by_user", foreign_keys="[TimeEntry.approved_by]")
    audit_logs = relationship("AuditLog", back_populates="user")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    notification_preferences = relationship("NotificationPreference", back_populates="user", cascade="all, delete-orphan")
    comment_mentions = relationship("CommentMention", back_populates="mentioned_user", cascade="all, delete-orphan")
    uploaded_files = relationship("File", back_populates="uploader", cascade="all, delete-orphan")
    file_permissions = relationship("FilePermission", foreign_keys="[FilePermission.user_id]", back_populates="user", cascade="all, delete-orphan")
    granted_file_permissions = relationship("FilePermission", foreign_keys="[FilePermission.granted_by]", back_populates="granter", cascade="all, delete-orphan")
    created_file_shares = relationship("FileShare", back_populates="creator", cascade="all, delete-orphan")
    created_file_versions = relationship("FileVersion", back_populates="creator", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            role.in_(['ProjectManager', 'TeamLead', 'Developer', 'QA', 'ProductOwner', 'Executive']),
            name='valid_user_role'
        ),
        Index('idx_users_email_active', 'email', 'is_active'),
        Index('idx_users_role_active', 'role', 'is_active'),
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"


class UserSkill(Base):
    """
    UserSkill model representing user skills and proficiency levels.
    
    Implements many-to-many relationship between users and skills.
    """
    __tablename__ = 'user_skills'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    skill_name = Column(String(100), nullable=False, index=True)
    proficiency_level = Column(String(20), nullable=False, default='Intermediate')
    created_at = Column(DateTime, nullable=False, default=func.now())

    # Relationships
    user = relationship("User", back_populates="skills")

    __table_args__ = (
        CheckConstraint(
            proficiency_level.in_(['Beginner', 'Intermediate', 'Advanced', 'Expert']),
            name='valid_proficiency_level'
        ),
        Index('idx_user_skills_user_skill', 'user_id', 'skill_name', unique=True),
    )

    def __repr__(self):
        return f"<UserSkill(id={self.id}, user_id={self.user_id}, skill='{self.skill_name}', level='{self.proficiency_level}')>" 