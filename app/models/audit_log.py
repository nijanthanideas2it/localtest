"""
AuditLog model for the Project Management Dashboard.
"""
from sqlalchemy import Column, String, DateTime, Text, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class AuditLog(Base):
    """
    AuditLog model representing system audit trail for security and compliance.
    
    Tracks all critical system actions with detailed information.
    """
    __tablename__ = 'audit_logs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), index=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), index=True)
    entity_id = Column(UUID(as_uuid=True), index=True)
    old_values = Column(JSONB)
    new_values = Column(JSONB)
    ip_address = Column(INET)
    user_agent = Column(Text)
    created_at = Column(DateTime, nullable=False, default=func.now())

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index('idx_audit_logs_user_created', 'user_id', 'created_at'),
        Index('idx_audit_logs_action_created', 'action', 'created_at'),
        Index('idx_audit_logs_entity', 'entity_type', 'entity_id'),
        Index('idx_audit_logs_ip_created', 'ip_address', 'created_at'),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action='{self.action}', entity_type='{self.entity_type}')>" 