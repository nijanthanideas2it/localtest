"""
Comment, CommentMention, and CommentAttachment models for the Project Management Dashboard.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, CheckConstraint, Index, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class Comment(Base):
    """
    Comment model representing comments and discussions on projects, tasks, and milestones.
    
    Supports threaded discussions with parent-child relationships.
    """
    __tablename__ = 'comments'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    entity_type = Column(String(20), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    parent_comment_id = Column(UUID(as_uuid=True), ForeignKey('comments.id', ondelete='CASCADE'), index=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    author = relationship("User", back_populates="comments")
    parent_comment = relationship("Comment", back_populates="replies", remote_side=[id])
    replies = relationship("Comment", back_populates="parent_comment", cascade="all, delete-orphan")
    mentions = relationship("CommentMention", back_populates="comment", cascade="all, delete-orphan")
    attachments = relationship("CommentAttachment", back_populates="comment", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            entity_type.in_(['Project', 'Task', 'Milestone']),
            name='valid_entity_type'
        ),
        Index('idx_comments_entity', 'entity_type', 'entity_id'),
        Index('idx_comments_author_created', 'author_id', 'created_at'),
        Index('idx_comments_parent', 'parent_comment_id'),
    )

    def __repr__(self):
        return f"<Comment(id={self.id}, author_id={self.author_id}, entity_type='{self.entity_type}', entity_id={self.entity_id})>"


class CommentMention(Base):
    """
    CommentMention model representing user mentions in comments.
    
    Tracks when users are mentioned in comments for notifications.
    """
    __tablename__ = 'comment_mentions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    comment_id = Column(UUID(as_uuid=True), ForeignKey('comments.id', ondelete='CASCADE'), nullable=False, index=True)
    mentioned_user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=func.now())

    # Relationships
    comment = relationship("Comment", back_populates="mentions")
    mentioned_user = relationship("User", back_populates="comment_mentions")

    __table_args__ = (
        Index('idx_comment_mentions_comment', 'comment_id'),
        Index('idx_comment_mentions_user', 'mentioned_user_id'),
        Index('idx_comment_mentions_unique', 'comment_id', 'mentioned_user_id', unique=True),
    )

    def __repr__(self):
        return f"<CommentMention(id={self.id}, comment_id={self.comment_id}, mentioned_user_id={self.mentioned_user_id})>"


class CommentAttachment(Base):
    """
    CommentAttachment model representing file attachments for comments.
    
    Stores file metadata and storage information.
    """
    __tablename__ = 'comment_attachments'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    comment_id = Column(UUID(as_uuid=True), ForeignKey('comments.id', ondelete='CASCADE'), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())

    # Relationships
    comment = relationship("Comment", back_populates="attachments")

    __table_args__ = (
        Index('idx_comment_attachments_comment', 'comment_id'),
        Index('idx_comment_attachments_file_path', 'file_path'),
    )

    def __repr__(self):
        return f"<CommentAttachment(id={self.id}, comment_id={self.comment_id}, file_name='{self.file_name}')>" 