"""
FileVersion model for the Project Management Dashboard.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, CheckConstraint, Index, ForeignKey, BigInteger, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class FileVersion(Base):
    """
    FileVersion model representing file versions.
    
    Manages version history and rollback capabilities for files.
    """
    __tablename__ = 'file_versions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey('files.id', ondelete='CASCADE'), nullable=False, index=True)
    version_number = Column(String(20), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False, index=True)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    change_description = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=False, index=True)
    is_current = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    file = relationship("File", back_populates="versions")
    creator = relationship("User", back_populates="created_file_versions")

    __table_args__ = (
        UniqueConstraint('file_id', 'version_number', name='unique_file_version'),
        Index('idx_file_versions_file_version', 'file_id', 'version_number'),
        Index('idx_file_versions_current', 'file_id', 'is_current'),
        Index('idx_file_versions_created', 'created_at'),
    )

    def __repr__(self):
        return f"<FileVersion(id={self.id}, file_id={self.file_id}, version_number='{self.version_number}')>"

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

    @property
    def version_info(self) -> dict:
        """Get version information."""
        return {
            "version_number": self.version_number,
            "file_name": self.file_name,
            "original_name": self.original_name,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "change_description": self.change_description,
            "created_by": str(self.created_by),
            "created_at": self.created_at.isoformat() if self.created_at else None
        } 