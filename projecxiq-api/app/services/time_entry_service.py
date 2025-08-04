"""
Time entry service layer for time tracking operations.
"""
from datetime import date, datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from decimal import Decimal
from uuid import UUID

from app.models.time_entry import TimeEntry
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.schemas.time_entry import (
    TimeEntryCreateRequest,
    TimeEntryUpdateRequest
)


class TimeEntryService:
    """Service class for time entry management operations."""
    
    @staticmethod
    def create_time_entry(
        db: Session,
        time_entry_data: TimeEntryCreateRequest,
        current_user_id: str
    ) -> Optional[TimeEntry]:
        """
        Create a new time entry.
        
        Args:
            db: Database session
            time_entry_data: Time entry creation data
            current_user_id: ID of the user creating the time entry
            
        Returns:
            Created time entry or None if creation fails
        """
        try:
            # Validate project exists
            project = db.query(Project).filter(Project.id == time_entry_data.project_id).first()
            if not project:
                raise ValueError("Project not found")
            
            # Validate task exists if provided
            if time_entry_data.task_id:
                task = db.query(Task).filter(Task.id == time_entry_data.task_id).first()
                if not task:
                    raise ValueError("Task not found")
                
                # Validate task belongs to the same project
                if task.project_id != time_entry_data.project_id:
                    raise ValueError("Task must belong to the specified project")
            
            # Check for duplicate time entry for the same user, project, task, and date
            existing_entry = db.query(TimeEntry).filter(
                and_(
                    TimeEntry.user_id == current_user_id,
                    TimeEntry.project_id == time_entry_data.project_id,
                    TimeEntry.task_id == time_entry_data.task_id,
                    TimeEntry.date == time_entry_data.work_date
                )
            ).first()
            
            if existing_entry:
                raise ValueError("Time entry already exists for this user, project, task, and date")
            
            # Create time entry
            time_entry = TimeEntry(
                user_id=current_user_id,
                task_id=time_entry_data.task_id,
                project_id=time_entry_data.project_id,
                hours=time_entry_data.hours,
                date=time_entry_data.work_date,
                category=time_entry_data.category,
                notes=time_entry_data.notes,
                is_approved=False
            )
            
            db.add(time_entry)
            db.commit()
            db.refresh(time_entry)
            return time_entry
            
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def get_time_entry_by_id(db: Session, time_entry_id: str) -> Optional[TimeEntry]:
        """
        Get time entry by ID with all related data.
        
        Args:
            db: Database session
            time_entry_id: Time entry ID
            
        Returns:
            Time entry or None if not found
        """
        return db.query(TimeEntry).options(
            joinedload(TimeEntry.user),
            joinedload(TimeEntry.task),
            joinedload(TimeEntry.project),
            joinedload(TimeEntry.approved_by_user)
        ).filter(TimeEntry.id == time_entry_id).first()
    
    @staticmethod
    def get_user_time_entries(
        db: Session,
        user_id: str,
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category: Optional[str] = None,
        is_approved: Optional[bool] = None,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[TimeEntry], Dict[str, Any]]:
        """
        Get time entries for a user with optional filtering and pagination.
        
        Args:
            db: Database session
            user_id: User ID
            project_id: Optional filter by project
            task_id: Optional filter by task
            start_date: Optional filter by start date
            end_date: Optional filter by end date
            category: Optional filter by category
            is_approved: Optional filter by approval status
            page: Page number
            limit: Items per page
            
        Returns:
            Tuple of (time entries list, pagination info)
        """
        query = db.query(TimeEntry).options(
            joinedload(TimeEntry.user),
            joinedload(TimeEntry.task),
            joinedload(TimeEntry.project),
            joinedload(TimeEntry.approved_by_user)
        ).filter(TimeEntry.user_id == user_id)
        
        # Apply filters
        if project_id:
            query = query.filter(TimeEntry.project_id == project_id)
        
        if task_id:
            query = query.filter(TimeEntry.task_id == task_id)
        
        if start_date:
            query = query.filter(TimeEntry.date >= start_date)
        
        if end_date:
            query = query.filter(TimeEntry.date <= end_date)
        
        if category:
            query = query.filter(TimeEntry.category == category)
        
        if is_approved is not None:
            query = query.filter(TimeEntry.is_approved == is_approved)
        
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        time_entries = query.order_by(TimeEntry.date.desc(), TimeEntry.created_at.desc()).offset(offset).limit(limit).all()
        
        # Calculate pagination info
        pages = (total + limit - 1) // limit
        
        pagination_info = {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": pages
        }
        
        return time_entries, pagination_info
    
    @staticmethod
    def update_time_entry(
        db: Session,
        time_entry_id: str,
        update_data: TimeEntryUpdateRequest,
        current_user_id: str
    ) -> Optional[TimeEntry]:
        """
        Update time entry details.
        
        Args:
            db: Database session
            time_entry_id: Time entry ID
            update_data: Update data
            current_user_id: ID of the user updating the time entry
            
        Returns:
            Updated time entry or None if not found
        """
        time_entry = db.query(TimeEntry).filter(TimeEntry.id == time_entry_id).first()
        if not time_entry:
            return None
        
        # Check if user can update this time entry
        if not TimeEntryService.can_update_time_entry(time_entry, current_user_id):
            raise ValueError("Not authorized to update this time entry")
        
        # Check if time entry is within editable period (7 days)
        if not TimeEntryService.is_within_editable_period(time_entry):
            raise ValueError("Time entry can only be updated within 7 days of creation")
        
        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(time_entry, field, value)
        
        time_entry.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(time_entry)
        return time_entry
    
    @staticmethod
    def delete_time_entry(
        db: Session,
        time_entry_id: str,
        current_user_id: str
    ) -> bool:
        """
        Delete time entry.
        
        Args:
            db: Database session
            time_entry_id: Time entry ID
            current_user_id: ID of the user deleting the time entry
            
        Returns:
            True if deleted, False if not found
        """
        time_entry = db.query(TimeEntry).filter(TimeEntry.id == time_entry_id).first()
        if not time_entry:
            return False
        
        # Check if user can delete this time entry
        if not TimeEntryService.can_delete_time_entry(time_entry, current_user_id):
            raise ValueError("Not authorized to delete this time entry")
        
        # Check if time entry is within editable period (7 days)
        if not TimeEntryService.is_within_editable_period(time_entry):
            raise ValueError("Time entry can only be deleted within 7 days of creation")
        
        db.delete(time_entry)
        db.commit()
        return True
    
    @staticmethod
    def can_update_time_entry(
        time_entry: TimeEntry,
        current_user_id: str
    ) -> bool:
        """
        Check if user can update time entry.
        
        Args:
            time_entry: Time entry object
            current_user_id: Current user ID
            
        Returns:
            True if user can update, False otherwise
        """
        # User can update their own time entries
        if str(time_entry.user_id) == current_user_id:
            return True
        
        # TODO: Add project manager/admin checks
        return False
    
    @staticmethod
    def can_delete_time_entry(
        time_entry: TimeEntry,
        current_user_id: str
    ) -> bool:
        """
        Check if user can delete time entry.
        
        Args:
            time_entry: Time entry object
            current_user_id: Current user ID
            
        Returns:
            True if user can delete, False otherwise
        """
        # User can delete their own time entries
        if str(time_entry.user_id) == current_user_id:
            return True
        
        # TODO: Add project manager/admin checks
        return False
    
    @staticmethod
    def is_within_editable_period(time_entry: TimeEntry) -> bool:
        """
        Check if time entry is within editable period (7 days).
        
        Args:
            time_entry: Time entry object
            
        Returns:
            True if within editable period, False otherwise
        """
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        return time_entry.created_at >= seven_days_ago
    
    @staticmethod
    def get_time_entry_statistics(
        db: Session,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get time entry statistics for a user.
        
        Args:
            db: Database session
            user_id: User ID
            start_date: Optional start date for statistics
            end_date: Optional end date for statistics
            
        Returns:
            Dictionary with time entry statistics
        """
        query = db.query(TimeEntry).filter(TimeEntry.user_id == user_id)
        
        if start_date:
            query = query.filter(TimeEntry.date >= start_date)
        
        if end_date:
            query = query.filter(TimeEntry.date <= end_date)
        
        # Get all time entries for the period
        time_entries = query.all()
        
        total_hours = sum(entry.hours for entry in time_entries)
        total_entries = len(time_entries)
        approved_entries = len([entry for entry in time_entries if entry.is_approved])
        pending_entries = total_entries - approved_entries
        
        # Calculate hours by category
        hours_by_category = {}
        for entry in time_entries:
            category = entry.category
            if category not in hours_by_category:
                hours_by_category[category] = 0
            hours_by_category[category] += entry.hours
        
        # Calculate average hours per day
        if time_entries:
            unique_dates = len(set(entry.date for entry in time_entries))
            avg_hours_per_day = total_hours / unique_dates if unique_dates > 0 else 0
        else:
            avg_hours_per_day = 0
        
        return {
            "total_hours": total_hours,
            "total_entries": total_entries,
            "approved_entries": approved_entries,
            "pending_entries": pending_entries,
            "hours_by_category": hours_by_category,
            "avg_hours_per_day": avg_hours_per_day
        }
    
    @staticmethod
    def get_pending_time_entries(
        db: Session,
        approver_id: str,
        project_id: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[TimeEntry], Dict[str, Any]]:
        """
        Get pending time entries for approval.
        
        Args:
            db: Database session
            approver_id: ID of the approver
            project_id: Optional filter by project
            page: Page number
            limit: Items per page
            
        Returns:
            Tuple of (time entries list, pagination info)
        """
        # Get projects where user is manager or admin
        # For now, we'll get all pending entries - this can be enhanced with proper role checking
        query = db.query(TimeEntry).options(
            joinedload(TimeEntry.user),
            joinedload(TimeEntry.task),
            joinedload(TimeEntry.project),
            joinedload(TimeEntry.approved_by_user)
        ).filter(TimeEntry.is_approved == False)
        
        # Apply project filter if provided
        if project_id:
            query = query.filter(TimeEntry.project_id == project_id)
        
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        time_entries = query.order_by(TimeEntry.created_at.desc()).offset(offset).limit(limit).all()
        
        # Calculate pagination info
        pages = (total + limit - 1) // limit
        
        pagination_info = {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": pages
        }
        
        return time_entries, pagination_info
    
    @staticmethod
    def get_approved_time_entries(
        db: Session,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[TimeEntry], Dict[str, Any]]:
        """
        Get approved time entries.
        
        Args:
            db: Database session
            user_id: Optional filter by user
            project_id: Optional filter by project
            start_date: Optional filter by start date
            end_date: Optional filter by end date
            page: Page number
            limit: Items per page
            
        Returns:
            Tuple of (time entries list, pagination info)
        """
        query = db.query(TimeEntry).options(
            joinedload(TimeEntry.user),
            joinedload(TimeEntry.task),
            joinedload(TimeEntry.project),
            joinedload(TimeEntry.approved_by_user)
        ).filter(TimeEntry.is_approved == True)
        
        # Apply filters
        if user_id:
            query = query.filter(TimeEntry.user_id == user_id)
        
        if project_id:
            query = query.filter(TimeEntry.project_id == project_id)
        
        if start_date:
            query = query.filter(TimeEntry.date >= start_date)
        
        if end_date:
            query = query.filter(TimeEntry.date <= end_date)
        
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        time_entries = query.order_by(TimeEntry.approved_at.desc()).offset(offset).limit(limit).all()
        
        # Calculate pagination info
        pages = (total + limit - 1) // limit
        
        pagination_info = {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": pages
        }
        
        return time_entries, pagination_info
    
    @staticmethod
    def approve_time_entry(
        db: Session,
        time_entry_id: str,
        approver_id: str,
        approval_notes: Optional[str] = None
    ) -> Optional[TimeEntry]:
        """
        Approve a time entry.
        
        Args:
            db: Database session
            time_entry_id: Time entry ID
            approver_id: ID of the approver
            approval_notes: Optional approval notes
            
        Returns:
            Approved time entry or None if not found
        """
        time_entry = db.query(TimeEntry).filter(TimeEntry.id == time_entry_id).first()
        if not time_entry:
            return None
        
        # Check if time entry is already approved
        if time_entry.is_approved:
            raise ValueError("Time entry is already approved")
        
        # TODO: Add proper authorization check for approver
        # For now, allow any user to approve (this should be enhanced with role checking)
        
        # Update time entry
        time_entry.is_approved = True
        time_entry.approved_by = approver_id
        time_entry.approved_at = datetime.now(timezone.utc)
        if approval_notes:
            time_entry.notes = f"{time_entry.notes or ''}\n\nApproval Notes: {approval_notes}"
        
        db.commit()
        db.refresh(time_entry)
        return time_entry
    
    @staticmethod
    def reject_time_entry(
        db: Session,
        time_entry_id: str,
        rejector_id: str,
        rejection_reason: str
    ) -> Optional[TimeEntry]:
        """
        Reject a time entry.
        
        Args:
            db: Database session
            time_entry_id: Time entry ID
            rejector_id: ID of the rejector
            rejection_reason: Reason for rejection
            
        Returns:
            Rejected time entry or None if not found
        """
        time_entry = db.query(TimeEntry).filter(TimeEntry.id == time_entry_id).first()
        if not time_entry:
            return None
        
        # Check if time entry is already approved
        if time_entry.is_approved:
            raise ValueError("Cannot reject an already approved time entry")
        
        # TODO: Add proper authorization check for rejector
        # For now, allow any user to reject (this should be enhanced with role checking)
        
        # Add rejection reason to notes
        rejection_note = f"\n\nRejection Notes: {rejection_reason}"
        time_entry.notes = f"{time_entry.notes or ''}{rejection_note}"
        
        # Mark as not approved (in case it was previously approved and then rejected)
        time_entry.is_approved = False
        time_entry.approved_by = None
        time_entry.approved_at = None
        
        db.commit()
        db.refresh(time_entry)
        return time_entry
    
    @staticmethod
    def can_approve_time_entry(
        time_entry: TimeEntry,
        approver_id: str
    ) -> bool:
        """
        Check if user can approve time entry.
        
        Args:
            time_entry: Time entry object
            approver_id: Approver user ID
            
        Returns:
            True if user can approve, False otherwise
        """
        # TODO: Implement proper role-based authorization
        # For now, allow any user to approve (this should be enhanced)
        return True
    
    @staticmethod
    def can_reject_time_entry(
        time_entry: TimeEntry,
        rejector_id: str
    ) -> bool:
        """
        Check if user can reject time entry.
        
        Args:
            time_entry: Time entry object
            rejector_id: Rejector user ID
            
        Returns:
            True if user can reject, False otherwise
        """
        # TODO: Implement proper role-based authorization
        # For now, allow any user to reject (this should be enhanced)
        return True 

    @staticmethod
    def get_time_analytics(
        db: Session,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive time analytics data.
        
        Args:
            db: Database session
            user_id: Optional filter by user ID
            project_id: Optional filter by project ID
            start_date: Optional start date for analytics
            end_date: Optional end date for analytics
            
        Returns:
            Dictionary with comprehensive analytics data
        """
        query = db.query(TimeEntry)
        
        if user_id:
            query = query.filter(TimeEntry.user_id == user_id)
        
        if project_id:
            query = query.filter(TimeEntry.project_id == project_id)
        
        if start_date:
            query = query.filter(TimeEntry.date >= start_date)
        
        if end_date:
            query = query.filter(TimeEntry.date <= end_date)
        
        time_entries = query.all()
        
        if not time_entries:
            return {
                "total_hours": Decimal('0.00'),
                "total_entries": 0,
                "average_hours_per_day": Decimal('0.00'),
                "average_hours_per_entry": Decimal('0.00'),
                "hours_by_category": {},
                "hours_by_project": {},
                "hours_by_user": {},
                "entries_by_status": {"approved": 0, "pending": 0},
                "top_productive_days": [],
                "weekly_trends": [],
                "monthly_summary": {}
            }
        
        # Calculate basic statistics
        total_hours = sum(entry.hours for entry in time_entries)
        total_entries = len(time_entries)
        average_hours_per_entry = total_hours / total_entries if total_entries > 0 else Decimal('0.00')
        
        # Calculate hours by category
        hours_by_category = {}
        for entry in time_entries:
            category = entry.category
            hours_by_category[category] = hours_by_category.get(category, Decimal('0.00')) + entry.hours
        
        # Calculate hours by project
        hours_by_project = {}
        for entry in time_entries:
            project_id_str = str(entry.project_id)
            hours_by_project[project_id_str] = hours_by_project.get(project_id_str, Decimal('0.00')) + entry.hours
        
        # Calculate hours by user
        hours_by_user = {}
        for entry in time_entries:
            user_id_str = str(entry.user_id)
            hours_by_user[user_id_str] = hours_by_user.get(user_id_str, Decimal('0.00')) + entry.hours
        
        # Calculate entries by status
        entries_by_status = {"approved": 0, "pending": 0}
        for entry in time_entries:
            if entry.is_approved:
                entries_by_status["approved"] += 1
            else:
                entries_by_status["pending"] += 1
        
        # Calculate top productive days
        daily_hours = {}
        for entry in time_entries:
            date_str = entry.date.isoformat()
            daily_hours[date_str] = daily_hours.get(date_str, Decimal('0.00')) + entry.hours
        
        top_productive_days = [
            {"date": date_str, "hours": hours, "entries": len([e for e in time_entries if e.date.isoformat() == date_str])}
            for date_str, hours in sorted(daily_hours.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        # Calculate weekly trends
        weekly_trends = []
        if time_entries:
            from datetime import timedelta
            current_date = min(entry.date for entry in time_entries)
            end_date_analytics = max(entry.date for entry in time_entries)
            
            while current_date <= end_date_analytics:
                week_start = current_date - timedelta(days=current_date.weekday())
                week_end = week_start + timedelta(days=6)
                
                week_entries = [e for e in time_entries if week_start <= e.date <= week_end]
                week_hours = sum(e.hours for e in week_entries)
                
                weekly_trends.append({
                    "week_start": week_start.isoformat(),
                    "week_end": week_end.isoformat(),
                    "hours": week_hours,
                    "entries": len(week_entries)
                })
                
                current_date += timedelta(days=7)
        
        # Calculate monthly summary
        monthly_summary = {}
        if time_entries:
            for entry in time_entries:
                month_key = f"{entry.date.year}-{entry.date.month:02d}"
                if month_key not in monthly_summary:
                    monthly_summary[month_key] = {
                        "hours": Decimal('0.00'),
                        "entries": 0,
                        "approved_hours": Decimal('0.00'),
                        "pending_hours": Decimal('0.00')
                    }
                
                monthly_summary[month_key]["hours"] += entry.hours
                monthly_summary[month_key]["entries"] += 1
                
                if entry.is_approved:
                    monthly_summary[month_key]["approved_hours"] += entry.hours
                else:
                    monthly_summary[month_key]["pending_hours"] += entry.hours
        
        # Calculate average hours per day
        unique_days = len(set(entry.date for entry in time_entries))
        average_hours_per_day = total_hours / unique_days if unique_days > 0 else Decimal('0.00')
        
        return {
            "total_hours": total_hours,
            "total_entries": total_entries,
            "average_hours_per_day": average_hours_per_day,
            "average_hours_per_entry": average_hours_per_entry,
            "hours_by_category": hours_by_category,
            "hours_by_project": hours_by_project,
            "hours_by_user": hours_by_user,
            "entries_by_status": entries_by_status,
            "top_productive_days": top_productive_days,
            "weekly_trends": weekly_trends,
            "monthly_summary": monthly_summary
        }
    
    @staticmethod
    def generate_time_report(
        db: Session,
        report_type: str,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Generate time tracking report.
        
        Args:
            db: Database session
            report_type: Type of report (daily, weekly, monthly, project, user)
            user_id: Optional filter by user ID
            project_id: Optional filter by project ID
            start_date: Optional start date for report
            end_date: Optional end date for report
            
        Returns:
            Dictionary with report data
        """
        from uuid import uuid4
        from datetime import datetime, timezone
        
        # Get time entries based on filters
        query = db.query(TimeEntry)
        
        if user_id:
            query = query.filter(TimeEntry.user_id == user_id)
        
        if project_id:
            query = query.filter(TimeEntry.project_id == project_id)
        
        if start_date:
            query = query.filter(TimeEntry.date >= start_date)
        
        if end_date:
            query = query.filter(TimeEntry.date <= end_date)
        
        time_entries = query.all()
        
        # Generate report based on type
        if report_type == "daily":
            detailed_data = []
            for entry in time_entries:
                detailed_data.append({
                    "date": entry.date.isoformat(),
                    "user": str(entry.user_id),
                    "project": str(entry.project_id),
                    "task": str(entry.task_id) if entry.task_id else None,
                    "hours": float(entry.hours),
                    "category": entry.category,
                    "status": "approved" if entry.is_approved else "pending"
                })
            
            summary = {
                "total_hours": float(sum(entry.hours for entry in time_entries)),
                "total_entries": len(time_entries),
                "unique_users": len(set(str(entry.user_id) for entry in time_entries)),
                "unique_projects": len(set(str(entry.project_id) for entry in time_entries))
            }
        
        elif report_type == "weekly":
            from datetime import timedelta
            
            weekly_data = {}
            for entry in time_entries:
                week_start = entry.date - timedelta(days=entry.date.weekday())
                week_key = week_start.isoformat()
                
                if week_key not in weekly_data:
                    weekly_data[week_key] = {
                        "week_start": week_start.isoformat(),
                        "hours": Decimal('0.00'),
                        "entries": 0,
                        "users": set(),
                        "projects": set()
                    }
                
                weekly_data[week_key]["hours"] += entry.hours
                weekly_data[week_key]["entries"] += 1
                weekly_data[week_key]["users"].add(str(entry.user_id))
                weekly_data[week_key]["projects"].add(str(entry.project_id))
            
            detailed_data = [
                {
                    "week_start": data["week_start"],
                    "hours": float(data["hours"]),
                    "entries": data["entries"],
                    "unique_users": len(data["users"]),
                    "unique_projects": len(data["projects"])
                }
                for data in weekly_data.values()
            ]
            
            summary = {
                "total_weeks": len(weekly_data),
                "total_hours": float(sum(data["hours"] for data in weekly_data.values())),
                "total_entries": sum(data["entries"] for data in weekly_data.values()),
                "average_hours_per_week": float(sum(data["hours"] for data in weekly_data.values()) / len(weekly_data)) if weekly_data else 0
            }
        
        elif report_type == "monthly":
            monthly_data = {}
            for entry in time_entries:
                month_key = f"{entry.date.year}-{entry.date.month:02d}"
                
                if month_key not in monthly_data:
                    monthly_data[month_key] = {
                        "month": month_key,
                        "hours": Decimal('0.00'),
                        "entries": 0,
                        "approved_hours": Decimal('0.00'),
                        "pending_hours": Decimal('0.00')
                    }
                
                monthly_data[month_key]["hours"] += entry.hours
                monthly_data[month_key]["entries"] += 1
                
                if entry.is_approved:
                    monthly_data[month_key]["approved_hours"] += entry.hours
                else:
                    monthly_data[month_key]["pending_hours"] += entry.hours
            
            detailed_data = [
                {
                    "month": data["month"],
                    "hours": float(data["hours"]),
                    "entries": data["entries"],
                    "approved_hours": float(data["approved_hours"]),
                    "pending_hours": float(data["pending_hours"]),
                    "approval_rate": float(data["approved_hours"] / data["hours"] * 100) if data["hours"] > 0 else 0
                }
                for data in monthly_data.values()
            ]
            
            summary = {
                "total_months": len(monthly_data),
                "total_hours": float(sum(data["hours"] for data in monthly_data.values())),
                "total_entries": sum(data["entries"] for data in monthly_data.values()),
                "average_approval_rate": float(sum(data["approved_hours"] for data in monthly_data.values()) / sum(data["hours"] for data in monthly_data.values()) * 100) if sum(data["hours"] for data in monthly_data.values()) > 0 else 0
            }
        
        else:  # Default to general report
            detailed_data = [
                {
                    "id": str(entry.id),
                    "date": entry.date.isoformat(),
                    "user": str(entry.user_id),
                    "project": str(entry.project_id),
                    "task": str(entry.task_id) if entry.task_id else None,
                    "hours": float(entry.hours),
                    "category": entry.category,
                    "status": "approved" if entry.is_approved else "pending",
                    "created_at": entry.created_at.isoformat()
                }
                for entry in time_entries
            ]
            
            summary = {
                "total_hours": float(sum(entry.hours for entry in time_entries)),
                "total_entries": len(time_entries),
                "unique_users": len(set(str(entry.user_id) for entry in time_entries)),
                "unique_projects": len(set(str(entry.project_id) for entry in time_entries)),
                "approval_rate": float(len([e for e in time_entries if e.is_approved]) / len(time_entries) * 100) if time_entries else 0
            }
        
        return {
            "report_id": str(uuid4()),
            "report_type": report_type,
            "generated_at": datetime.now(timezone.utc),
            "date_range": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            },
            "summary": summary,
            "detailed_data": detailed_data,
            "export_url": None  # TODO: Implement export functionality
        }
    
    @staticmethod
    def get_time_summary(
        db: Session,
        period: str = "current_month",
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get time summary for a specific period.
        
        Args:
            db: Database session
            period: Period for summary (current_month, current_week, current_year, all_time)
            user_id: Optional filter by user ID
            project_id: Optional filter by project ID
            
        Returns:
            Dictionary with summary data
        """
        from datetime import date, timedelta
        
        # Calculate date range based on period
        today = date.today()
        
        if period == "current_week":
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        elif period == "current_month":
            start_date = today.replace(day=1)
            if today.month == 12:
                end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        elif period == "current_year":
            start_date = today.replace(month=1, day=1)
            end_date = today.replace(month=12, day=31)
        else:  # all_time
            start_date = None
            end_date = None
        
        # Get time entries
        query = db.query(TimeEntry)
        
        if user_id:
            query = query.filter(TimeEntry.user_id == user_id)
        
        if project_id:
            query = query.filter(TimeEntry.project_id == project_id)
        
        if start_date:
            query = query.filter(TimeEntry.date >= start_date)
        
        if end_date:
            query = query.filter(TimeEntry.date <= end_date)
        
        time_entries = query.all()
        
        if not time_entries:
            return {
                "period": period,
                "total_hours": Decimal('0.00'),
                "total_entries": 0,
                "approved_hours": Decimal('0.00'),
                "pending_hours": Decimal('0.00'),
                "rejected_hours": Decimal('0.00'),
                "average_hours_per_day": Decimal('0.00'),
                "most_productive_category": "N/A",
                "most_productive_project": "N/A",
                "completion_rate": Decimal('0.00')
            }
        
        # Calculate basic statistics
        total_hours = sum(entry.hours for entry in time_entries)
        total_entries = len(time_entries)
        
        approved_hours = sum(entry.hours for entry in time_entries if entry.is_approved)
        pending_hours = sum(entry.hours for entry in time_entries if not entry.is_approved)
        rejected_hours = Decimal('0.00')  # No rejection field in current model
        
        # Calculate average hours per day
        unique_days = len(set(entry.date for entry in time_entries))
        average_hours_per_day = total_hours / unique_days if unique_days > 0 else Decimal('0.00')
        
        # Find most productive category
        category_hours = {}
        for entry in time_entries:
            category_hours[entry.category] = category_hours.get(entry.category, Decimal('0.00')) + entry.hours
        
        most_productive_category = max(category_hours.items(), key=lambda x: x[1])[0] if category_hours else "N/A"
        
        # Find most productive project
        project_hours = {}
        for entry in time_entries:
            project_id_str = str(entry.project_id)
            project_hours[project_id_str] = project_hours.get(project_id_str, Decimal('0.00')) + entry.hours
        
        most_productive_project = max(project_hours.items(), key=lambda x: x[1])[0] if project_hours else "N/A"
        
        # Calculate completion rate (approved hours / total hours)
        completion_rate = (approved_hours / total_hours * 100) if total_hours > 0 else Decimal('0.00')
        
        return {
            "period": period,
            "total_hours": total_hours,
            "total_entries": total_entries,
            "approved_hours": approved_hours,
            "pending_hours": pending_hours,
            "rejected_hours": rejected_hours,
            "average_hours_per_day": average_hours_per_day,
            "most_productive_category": most_productive_category,
            "most_productive_project": most_productive_project,
            "completion_rate": completion_rate
        } 