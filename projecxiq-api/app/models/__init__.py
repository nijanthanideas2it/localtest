# Import all models here for Alembic to detect them
from .user import User, UserSkill
from .project import Project, ProjectTeamMember
from .task import Task, TaskDependency
from .milestone import Milestone, MilestoneDependency
from .time_entry import TimeEntry
from .comment import Comment, CommentMention, CommentAttachment
from .file import File
from .file_permission import FilePermission, FileShare
from .file_version import FileVersion
from .notification import Notification
from .notification_preference import NotificationPreference
from .audit_log import AuditLog

__all__ = [
    'User',
    'UserSkill', 
    'Project',
    'ProjectTeamMember',
    'Task',
    'TaskDependency',
    'Milestone',
    'MilestoneDependency',
    'TimeEntry',
    'Comment',
    'CommentMention',
    'CommentAttachment',
    'File',
    'FilePermission',
    'FileShare',
    'FileVersion',
    'Notification',
    'NotificationPreference',
    'AuditLog',
]
