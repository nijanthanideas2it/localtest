"""
File model for the Project Management Dashboard.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, CheckConstraint, Index, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class File(Base):
    """
    File model representing uploaded files in the system.
    
    Stores file metadata and storage information for general file management.
    """
    __tablename__ = 'files'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_name = Column(String(255), nullable=False, index=True)
    original_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False, index=True)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=False, index=True)
    is_public = Column(Boolean, nullable=False, default=False, index=True)
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    uploader = relationship("User", back_populates="uploaded_files")
    permissions = relationship("FilePermission", back_populates="file", cascade="all, delete-orphan")
    shares = relationship("FileShare", back_populates="file", cascade="all, delete-orphan")
    versions = relationship("FileVersion", back_populates="file", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_files_uploaded_by_created', 'uploaded_by', 'created_at'),
        Index('idx_files_mime_type', 'mime_type'),
        Index('idx_files_is_public', 'is_public'),
        Index('idx_files_is_deleted', 'is_deleted'),
    )

    def __repr__(self):
        return f"<File(id={self.id}, file_name='{self.file_name}', uploaded_by={self.uploaded_by})>"

    @property
    def file_extension(self) -> str:
        """Get file extension from original filename."""
        if '.' in self.original_name:
            return self.original_name.rsplit('.', 1)[1].lower()
        return ''

    @property
    def is_image(self) -> bool:
        """Check if file is an image based on MIME type."""
        return self.mime_type.startswith('image/')

    @property
    def is_document(self) -> bool:
        """Check if file is a document based on MIME type."""
        document_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/plain',
            'text/csv'
        ]
        return self.mime_type in document_types

    @property
    def is_archive(self) -> bool:
        """Check if file is an archive based on MIME type."""
        archive_types = [
            'application/zip',
            'application/x-rar-compressed',
            'application/x-7z-compressed',
            'application/gzip',
            'application/x-tar'
        ]
        return self.mime_type in archive_types

    @property
    def human_readable_size(self) -> str:
        """Get human-readable file size."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB" 