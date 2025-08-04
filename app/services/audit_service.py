"""
Audit service for managing audit logs and system audit trail.
"""
import logging
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, text
from fastapi import Request

from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogFilterRequest

logger = logging.getLogger(__name__)


class AuditService:
    """Service class for audit log operations."""
    
    @staticmethod
    def create_audit_log(
        db: Session,
        user_id: Optional[str],
        action: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Create an audit log entry.
        
        Args:
            db: Database session
            user_id: User ID who performed the action
            action: Action performed
            entity_type: Type of entity affected
            entity_id: ID of entity affected
            old_values: Previous values before change
            new_values: New values after change
            ip_address: IP address of the user
            user_agent: User agent string
            
        Returns:
            AuditLog object
        """
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                old_values=old_values,
                new_values=new_values,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)
            
            logger.info(f"Audit log created: {action} by user {user_id}")
            return audit_log
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def get_audit_log_by_id(db: Session, log_id: str) -> Optional[AuditLog]:
        """
        Get audit log by ID.
        
        Args:
            db: Database session
            log_id: Audit log ID
            
        Returns:
            AuditLog object or None if not found
        """
        return db.query(AuditLog).filter(AuditLog.id == log_id).first()
    
    @staticmethod
    def get_audit_logs(
        db: Session,
        page: int = 1,
        page_size: int = 10,
        filter_request: Optional[AuditLogFilterRequest] = None
    ) -> Tuple[List[AuditLog], int]:
        """
        Get audit logs with pagination and filtering.
        
        Args:
            db: Database session
            page: Page number
            page_size: Page size
            filter_request: Optional filter parameters
            
        Returns:
            Tuple of (audit_logs, total_count)
        """
        query = db.query(AuditLog)
        
        if filter_request:
            # Apply filters
            if filter_request.user_id:
                query = query.filter(AuditLog.user_id == filter_request.user_id)
            
            if filter_request.action:
                query = query.filter(AuditLog.action == filter_request.action)
            
            if filter_request.entity_type:
                query = query.filter(AuditLog.entity_type == filter_request.entity_type)
            
            if filter_request.entity_id:
                query = query.filter(AuditLog.entity_id == filter_request.entity_id)
            
            if filter_request.ip_address:
                query = query.filter(AuditLog.ip_address == filter_request.ip_address)
            
            if filter_request.date_from:
                query = query.filter(AuditLog.created_at >= filter_request.date_from)
            
            if filter_request.date_to:
                query = query.filter(AuditLog.created_at <= filter_request.date_to)
            
            if filter_request.search:
                search_term = f"%{filter_request.search}%"
                query = query.filter(
                    or_(
                        AuditLog.action.ilike(search_term),
                        AuditLog.entity_type.ilike(search_term),
                        AuditLog.user_agent.ilike(search_term)
                    )
                )
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        audit_logs = query.order_by(desc(AuditLog.created_at)).offset((page - 1) * page_size).limit(page_size).all()
        
        return audit_logs, total_count
    
    @staticmethod
    def get_audit_logs_by_user(
        db: Session,
        user_id: str,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[AuditLog], int]:
        """
        Get audit logs for a specific user.
        
        Args:
            db: Database session
            user_id: User ID
            page: Page number
            page_size: Page size
            
        Returns:
            Tuple of (audit_logs, total_count)
        """
        query = db.query(AuditLog).filter(AuditLog.user_id == user_id)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        audit_logs = query.order_by(desc(AuditLog.created_at)).offset((page - 1) * page_size).limit(page_size).all()
        
        return audit_logs, total_count
    
    @staticmethod
    def get_audit_logs_by_action(
        db: Session,
        action: str,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[AuditLog], int]:
        """
        Get audit logs for a specific action.
        
        Args:
            db: Database session
            action: Action type
            page: Page number
            page_size: Page size
            
        Returns:
            Tuple of (audit_logs, total_count)
        """
        query = db.query(AuditLog).filter(AuditLog.action == action)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        audit_logs = query.order_by(desc(AuditLog.created_at)).offset((page - 1) * page_size).limit(page_size).all()
        
        return audit_logs, total_count
    
    @staticmethod
    def get_audit_logs_by_entity(
        db: Session,
        entity_type: str,
        entity_id: str,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[AuditLog], int]:
        """
        Get audit logs for a specific entity.
        
        Args:
            db: Database session
            entity_type: Entity type
            entity_id: Entity ID
            page: Page number
            page_size: Page size
            
        Returns:
            Tuple of (audit_logs, total_count)
        """
        query = db.query(AuditLog).filter(
            and_(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id
            )
        )
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        audit_logs = query.order_by(desc(AuditLog.created_at)).offset((page - 1) * page_size).limit(page_size).all()
        
        return audit_logs, total_count
    
    @staticmethod
    def get_audit_log_stats(db: Session) -> Dict[str, Any]:
        """
        Get audit log statistics.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with audit log statistics
        """
        # Total logs
        total_logs = db.query(func.count(AuditLog.id)).scalar()
        
        # Logs by action
        logs_by_action = db.query(
            AuditLog.action,
            func.count(AuditLog.id)
        ).group_by(AuditLog.action).all()
        
        # Logs by user
        logs_by_user = db.query(
            AuditLog.user_id,
            func.count(AuditLog.id)
        ).filter(AuditLog.user_id.isnot(None)).group_by(AuditLog.user_id).all()
        
        # Logs by entity type
        logs_by_entity_type = db.query(
            AuditLog.entity_type,
            func.count(AuditLog.id)
        ).filter(AuditLog.entity_type.isnot(None)).group_by(AuditLog.entity_type).all()
        
        # Logs by date (last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        logs_by_date = db.query(
            func.date(AuditLog.created_at),
            func.count(AuditLog.id)
        ).filter(AuditLog.created_at >= thirty_days_ago).group_by(func.date(AuditLog.created_at)).all()
        
        # Recent activity
        recent_activity = db.query(AuditLog).order_by(desc(AuditLog.created_at)).limit(10).all()
        
        # Top actions
        top_actions = db.query(
            AuditLog.action,
            func.count(AuditLog.id).label('count')
        ).group_by(AuditLog.action).order_by(desc('count')).limit(10).all()
        
        # Top users
        top_users = db.query(
            AuditLog.user_id,
            func.count(AuditLog.id).label('count')
        ).filter(AuditLog.user_id.isnot(None)).group_by(AuditLog.user_id).order_by(desc('count')).limit(10).all()
        
        return {
            "total_logs": total_logs,
            "logs_by_action": dict(logs_by_action),
            "logs_by_user": dict(logs_by_user),
            "logs_by_entity_type": dict(logs_by_entity_type),
            "logs_by_date": dict(logs_by_date),
            "recent_activity": recent_activity,
            "top_actions": [{"action": action, "count": count} for action, count in top_actions],
            "top_users": [{"user_id": user_id, "count": count} for user_id, count in top_users]
        }
    
    @staticmethod
    def get_audit_log_summary(db: Session) -> Dict[str, Any]:
        """
        Get audit log summary.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with audit log summary
        """
        # Total logs
        total_logs = db.query(func.count(AuditLog.id)).scalar()
        
        # Unique users
        unique_users = db.query(func.count(func.distinct(AuditLog.user_id))).filter(AuditLog.user_id.isnot(None)).scalar()
        
        # Unique actions
        unique_actions = db.query(func.count(func.distinct(AuditLog.action))).scalar()
        
        # Unique entities
        unique_entities = db.query(func.count(func.distinct(AuditLog.entity_type))).filter(AuditLog.entity_type.isnot(None)).scalar()
        
        # Date range
        first_log = db.query(AuditLog.created_at).order_by(AuditLog.created_at).first()
        last_log = db.query(AuditLog.created_at).order_by(desc(AuditLog.created_at)).first()
        
        date_range = {
            "first": first_log[0] if first_log else None,
            "last": last_log[0] if last_log else None
        }
        
        # Most common actions
        most_common_actions = db.query(
            AuditLog.action,
            func.count(AuditLog.id).label('count')
        ).group_by(AuditLog.action).order_by(desc('count')).limit(5).all()
        
        # Most active users
        most_active_users = db.query(
            AuditLog.user_id,
            func.count(AuditLog.id).label('count')
        ).filter(AuditLog.user_id.isnot(None)).group_by(AuditLog.user_id).order_by(desc('count')).limit(5).all()
        
        # Recent trends (last 7 days vs previous 7 days)
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)
        
        recent_week = db.query(func.count(AuditLog.id)).filter(AuditLog.created_at >= week_ago).scalar()
        previous_week = db.query(func.count(AuditLog.id)).filter(
            and_(
                AuditLog.created_at >= two_weeks_ago,
                AuditLog.created_at < week_ago
            )
        ).scalar()
        
        recent_trends = {
            "recent_week": recent_week,
            "previous_week": previous_week,
            "change_percentage": ((recent_week - previous_week) / previous_week * 100) if previous_week > 0 else 0
        }
        
        return {
            "total_logs": total_logs,
            "unique_users": unique_users,
            "unique_actions": unique_actions,
            "unique_entities": unique_entities,
            "date_range": date_range,
            "most_common_actions": [{"action": action, "count": count} for action, count in most_common_actions],
            "most_active_users": [{"user_id": user_id, "count": count} for user_id, count in most_active_users],
            "recent_trends": recent_trends
        }
    
    @staticmethod
    def export_audit_logs(
        db: Session,
        format: str = "json",
        filter_request: Optional[AuditLogFilterRequest] = None,
        include_details: bool = True
    ) -> str:
        """
        Export audit logs.
        
        Args:
            db: Database session
            format: Export format (json, csv)
            filter_request: Optional filter parameters
            include_details: Whether to include detailed information
            
        Returns:
            Exported data as string
        """
        # Get all logs (no pagination for export)
        query = db.query(AuditLog)
        
        if filter_request:
            # Apply filters
            if filter_request.user_id:
                query = query.filter(AuditLog.user_id == filter_request.user_id)
            
            if filter_request.action:
                query = query.filter(AuditLog.action == filter_request.action)
            
            if filter_request.entity_type:
                query = query.filter(AuditLog.entity_type == filter_request.entity_type)
            
            if filter_request.entity_id:
                query = query.filter(AuditLog.entity_id == filter_request.entity_id)
            
            if filter_request.ip_address:
                query = query.filter(AuditLog.ip_address == filter_request.ip_address)
            
            if filter_request.date_from:
                query = query.filter(AuditLog.created_at >= filter_request.date_from)
            
            if filter_request.date_to:
                query = query.filter(AuditLog.created_at <= filter_request.date_to)
        
        audit_logs = query.order_by(desc(AuditLog.created_at)).all()
        
        if format == "json":
            return AuditService._export_to_json(audit_logs, include_details)
        elif format == "csv":
            return AuditService._export_to_csv(audit_logs, include_details)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    @staticmethod
    def _export_to_json(audit_logs: List[AuditLog], include_details: bool) -> str:
        """Export audit logs to JSON format."""
        data = []
        for log in audit_logs:
            log_data = {
                "id": str(log.id),
                "user_id": str(log.user_id) if log.user_id else None,
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": str(log.entity_id) if log.entity_id else None,
                "ip_address": str(log.ip_address) if log.ip_address else None,
                "user_agent": log.user_agent,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            
            if include_details:
                log_data["old_values"] = log.old_values
                log_data["new_values"] = log.new_values
            
            data.append(log_data)
        
        return json.dumps(data, indent=2, default=str)
    
    @staticmethod
    def _export_to_csv(audit_logs: List[AuditLog], include_details: bool) -> str:
        """Export audit logs to CSV format."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        headers = ["id", "user_id", "action", "entity_type", "entity_id", "ip_address", "user_agent", "created_at"]
        if include_details:
            headers.extend(["old_values", "new_values"])
        writer.writerow(headers)
        
        # Write data
        for log in audit_logs:
            row = [
                str(log.id),
                str(log.user_id) if log.user_id else "",
                log.action,
                log.entity_type or "",
                str(log.entity_id) if log.entity_id else "",
                str(log.ip_address) if log.ip_address else "",
                log.user_agent or "",
                log.created_at.isoformat() if log.created_at else ""
            ]
            
            if include_details:
                row.extend([
                    json.dumps(log.old_values) if log.old_values else "",
                    json.dumps(log.new_values) if log.new_values else ""
                ])
            
            writer.writerow(row)
        
        return output.getvalue()
    
    @staticmethod
    def get_client_ip(request: Request) -> Optional[str]:
        """
        Get client IP address from request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Client IP address or None
        """
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        if request.client:
            return request.client.host
        
        return None
    
    @staticmethod
    def get_user_agent(request: Request) -> Optional[str]:
        """
        Get user agent from request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            User agent string or None
        """
        return request.headers.get("User-Agent")
    
    @staticmethod
    def log_user_action(
        db: Session,
        user_id: Optional[str],
        action: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ) -> AuditLog:
        """
        Log a user action with automatic IP and user agent detection.
        
        Args:
            db: Database session
            user_id: User ID who performed the action
            action: Action performed
            entity_type: Type of entity affected
            entity_id: ID of entity affected
            old_values: Previous values before change
            new_values: New values after change
            request: FastAPI request object for IP and user agent
            
        Returns:
            AuditLog object
        """
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = AuditService.get_client_ip(request)
            user_agent = AuditService.get_user_agent(request)
        
        return AuditService.create_audit_log(
            db=db,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent
        ) 