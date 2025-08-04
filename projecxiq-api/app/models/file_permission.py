"""
FilePermission model for the Project Management Dashboard.
"""
from sqlalchemy import Column, String, Boolean, DateTime, CheckConstraint, Index, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class FilePermission(Base):
    """
    FilePermission model representing file access permissions.
    
    Manages who can access specific files and what level of access they have.
    """
    __tablename__ = 'file_permissions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey('files.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    permission_type = Column(String(20), nullable=False, index=True)
    granted_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    file = relationship("File", back_populates="permissions")
    user = relationship("User", foreign_keys=[user_id], back_populates="file_permissions")
    granter = relationship("User", foreign_keys=[granted_by], back_populates="granted_file_permissions")

    __table_args__ = (
        CheckConstraint(
            permission_type.in_(['read', 'write', 'admin']),
            name='valid_permission_type'
        ),
        UniqueConstraint('file_id', 'user_id', name='unique_file_user_permission'),
        Index('idx_file_permissions_file_user', 'file_id', 'user_id'),
        Index('idx_file_permissions_user_active', 'user_id', 'is_active'),
        Index('idx_file_permissions_expires', 'expires_at'),
    )

    def __repr__(self):
        return f"<FilePermission(id={self.id}, file_id={self.file_id}, user_id={self.user_id}, permission_type='{self.permission_type}')>"

    @property
    def is_expired(self) -> bool:
        """Check if the permission has expired."""
        if not self.expires_at:
            return False
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if the permission is valid (active and not expired)."""
        return self.is_active and not self.is_expired


class FileShare(Base):
    """
    FileShare model representing file sharing links.
    
    Manages temporary sharing links for files with optional expiration.
    """
    __tablename__ = 'file_shares'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey('files.id', ondelete='CASCADE'), nullable=False, index=True)
    share_token = Column(String(255), nullable=False, unique=True, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    permission_type = Column(String(20), nullable=False, default='read', index=True)
    max_downloads = Column(String(10), nullable=True)  # NULL for unlimited
    download_count = Column(String(10), nullable=False, default=0)
    expires_at = Column(DateTime, nullable=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    file = relationship("File", back_populates="shares")
    creator = relationship("User", back_populates="created_file_shares")

    __table_args__ = (
        CheckConstraint(
            permission_type.in_(['read', 'write']),
            name='valid_share_permission_type'
        ),
        Index('idx_file_shares_token', 'share_token'),
        Index('idx_file_shares_file_active', 'file_id', 'is_active'),
        Index('idx_file_shares_expires', 'expires_at'),
    )

    def __repr__(self):
        return f"<FileShare(id={self.id}, file_id={self.file_id}, share_token='{self.share_token}')>"

    @property
    def is_expired(self) -> bool:
        """Check if the share has expired."""
        if not self.expires_at:
            return False
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_download_limit_reached(self) -> bool:
        """Check if the download limit has been reached."""
        if not self.max_downloads:
            return False
        return int(self.download_count) >= int(self.max_downloads)

    @property
    def is_valid(self) -> bool:
        """Check if the share is valid (active, not expired, and download limit not reached)."""
        return self.is_active and not self.is_expired and not self.is_download_limit_reached

    def increment_download_count(self):
        """Increment the download count."""
        self.download_count = str(int(self.download_count) + 1)
        self.updated_at = func.now() 