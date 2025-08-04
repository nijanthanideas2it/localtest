"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('hourly_rate', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)
    op.create_index(op.f('ix_users_is_active'), 'users', ['is_active'], unique=False)
    op.create_index('idx_users_email_active', 'users', ['email', 'is_active'], unique=False)
    op.create_index('idx_users_role_active', 'users', ['role', 'is_active'], unique=False)
    op.create_check_constraint('valid_user_role', 'users', "role IN ('ProjectManager', 'TeamLead', 'Developer', 'QA', 'ProductOwner', 'Executive')")

    # Create user_skills table
    op.create_table('user_skills',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('skill_name', sa.String(length=100), nullable=False),
        sa.Column('proficiency_level', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_skills_user_id'), 'user_skills', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_skills_skill_name'), 'user_skills', ['skill_name'], unique=False)
    op.create_index('idx_user_skills_user_skill', 'user_skills', ['user_id', 'skill_name'], unique=True)
    op.create_check_constraint('valid_proficiency_level', 'user_skills', "proficiency_level IN ('Beginner', 'Intermediate', 'Advanced', 'Expert')")

    # Create projects table
    op.create_table('projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('budget', sa.DECIMAL(precision=15, scale=2), nullable=True),
        sa.Column('actual_cost', sa.DECIMAL(precision=15, scale=2), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('manager_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['manager_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_name'), 'projects', ['name'], unique=False)
    op.create_index(op.f('ix_projects_start_date'), 'projects', ['start_date'], unique=False)
    op.create_index(op.f('ix_projects_end_date'), 'projects', ['end_date'], unique=False)
    op.create_index(op.f('ix_projects_status'), 'projects', ['status'], unique=False)
    op.create_index(op.f('ix_projects_manager_id'), 'projects', ['manager_id'], unique=False)
    op.create_index('idx_projects_status_dates', 'projects', ['status', 'start_date', 'end_date'], unique=False)
    op.create_index('idx_projects_manager_status', 'projects', ['manager_id', 'status'], unique=False)
    op.create_check_constraint('valid_project_status', 'projects', "status IN ('Draft', 'Active', 'OnHold', 'Completed', 'Cancelled')")
    op.create_check_constraint('valid_project_dates', 'projects', 'end_date >= start_date')

    # Create project_team_members table
    op.create_table('project_team_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
        sa.Column('left_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_project_team_members_project_id'), 'project_team_members', ['project_id'], unique=False)
    op.create_index(op.f('ix_project_team_members_user_id'), 'project_team_members', ['user_id'], unique=False)
    op.create_index('idx_project_team_members_project_user', 'project_team_members', ['project_id', 'user_id'], unique=True)
    op.create_index('idx_project_team_members_user_active', 'project_team_members', ['user_id', 'left_at'], unique=False)

    # Create tasks table
    op.create_table('tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assignee_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False),
        sa.Column('estimated_hours', sa.DECIMAL(precision=8, scale=2), nullable=True),
        sa.Column('actual_hours', sa.DECIMAL(precision=8, scale=2), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['assignee_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_title'), 'tasks', ['title'], unique=False)
    op.create_index(op.f('ix_tasks_project_id'), 'tasks', ['project_id'], unique=False)
    op.create_index(op.f('ix_tasks_assignee_id'), 'tasks', ['assignee_id'], unique=False)
    op.create_index(op.f('ix_tasks_status'), 'tasks', ['status'], unique=False)
    op.create_index(op.f('ix_tasks_priority'), 'tasks', ['priority'], unique=False)
    op.create_index(op.f('ix_tasks_due_date'), 'tasks', ['due_date'], unique=False)
    op.create_index('idx_tasks_project_status', 'tasks', ['project_id', 'status'], unique=False)
    op.create_index('idx_tasks_assignee_status', 'tasks', ['assignee_id', 'status'], unique=False)
    op.create_index('idx_tasks_priority_status', 'tasks', ['priority', 'status'], unique=False)
    op.create_check_constraint('valid_task_status', 'tasks', "status IN ('ToDo', 'InProgress', 'Review', 'Done')")
    op.create_check_constraint('valid_task_priority', 'tasks', "priority IN ('Low', 'Medium', 'High', 'Critical')")
    op.create_check_constraint('valid_estimated_hours', 'tasks', 'estimated_hours >= 0')
    op.create_check_constraint('valid_actual_hours', 'tasks', 'actual_hours >= 0')

    # Create task_dependencies table
    op.create_table('task_dependencies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dependent_task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('prerequisite_task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dependency_type', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['dependent_task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['prerequisite_task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_dependencies_dependent_task_id'), 'task_dependencies', ['dependent_task_id'], unique=False)
    op.create_index(op.f('ix_task_dependencies_prerequisite_task_id'), 'task_dependencies', ['prerequisite_task_id'], unique=False)
    op.create_index('idx_task_dependencies_dependent', 'task_dependencies', ['dependent_task_id'], unique=False)
    op.create_index('idx_task_dependencies_prerequisite', 'task_dependencies', ['prerequisite_task_id'], unique=False)
    op.create_index('idx_task_dependencies_unique', 'task_dependencies', ['dependent_task_id', 'prerequisite_task_id'], unique=True)
    op.create_check_constraint('valid_dependency_type', 'task_dependencies', "dependency_type IN ('Blocks', 'DependsOn', 'RelatedTo')")
    op.create_check_constraint('no_self_dependency', 'task_dependencies', 'dependent_task_id != prerequisite_task_id')

    # Create milestones table
    op.create_table('milestones',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_milestones_name'), 'milestones', ['name'], unique=False)
    op.create_index(op.f('ix_milestones_project_id'), 'milestones', ['project_id'], unique=False)
    op.create_index(op.f('ix_milestones_due_date'), 'milestones', ['due_date'], unique=False)
    op.create_index(op.f('ix_milestones_is_completed'), 'milestones', ['is_completed'], unique=False)
    op.create_index('idx_milestones_project_due', 'milestones', ['project_id', 'due_date'], unique=False)
    op.create_index('idx_milestones_project_completed', 'milestones', ['project_id', 'is_completed'], unique=False)

    # Create milestone_dependencies table
    op.create_table('milestone_dependencies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dependent_milestone_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('prerequisite_milestone_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['dependent_milestone_id'], ['milestones.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['prerequisite_milestone_id'], ['milestones.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_milestone_dependencies_dependent_milestone_id'), 'milestone_dependencies', ['dependent_milestone_id'], unique=False)
    op.create_index(op.f('ix_milestone_dependencies_prerequisite_milestone_id'), 'milestone_dependencies', ['prerequisite_milestone_id'], unique=False)
    op.create_index('idx_milestone_dependencies_dependent', 'milestone_dependencies', ['dependent_milestone_id'], unique=False)
    op.create_index('idx_milestone_dependencies_prerequisite', 'milestone_dependencies', ['prerequisite_milestone_id'], unique=False)
    op.create_index('idx_milestone_dependencies_unique', 'milestone_dependencies', ['dependent_milestone_id', 'prerequisite_milestone_id'], unique=True)
    op.create_check_constraint('no_self_milestone_dependency', 'milestone_dependencies', 'dependent_milestone_id != prerequisite_milestone_id')

    # Create time_entries table
    op.create_table('time_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('hours', sa.DECIMAL(precision=6, scale=2), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('category', sa.String(length=20), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_approved', sa.Boolean(), nullable=False),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_time_entries_user_id'), 'time_entries', ['user_id'], unique=False)
    op.create_index(op.f('ix_time_entries_task_id'), 'time_entries', ['task_id'], unique=False)
    op.create_index(op.f('ix_time_entries_project_id'), 'time_entries', ['project_id'], unique=False)
    op.create_index(op.f('ix_time_entries_date'), 'time_entries', ['date'], unique=False)
    op.create_index(op.f('ix_time_entries_category'), 'time_entries', ['category'], unique=False)
    op.create_index(op.f('ix_time_entries_is_approved'), 'time_entries', ['is_approved'], unique=False)
    op.create_index(op.f('ix_time_entries_approved_by'), 'time_entries', ['approved_by'], unique=False)
    op.create_index('idx_time_entries_user_date', 'time_entries', ['user_id', 'date'], unique=False)
    op.create_index('idx_time_entries_project_date', 'time_entries', ['project_id', 'date'], unique=False)
    op.create_index('idx_time_entries_task_date', 'time_entries', ['task_id', 'date'], unique=False)
    op.create_index('idx_time_entries_approved', 'time_entries', ['is_approved'], unique=False)
    op.create_check_constraint('positive_hours', 'time_entries', 'hours > 0')
    op.create_check_constraint('max_hours_per_day', 'time_entries', 'hours <= 24')
    op.create_check_constraint('valid_time_category', 'time_entries', "category IN ('Development', 'Testing', 'Documentation', 'Meeting', 'Other')")

    # Create comments table
    op.create_table('comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_type', sa.String(length=20), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_comment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_comment_id'], ['comments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_comments_author_id'), 'comments', ['author_id'], unique=False)
    op.create_index(op.f('ix_comments_entity_type'), 'comments', ['entity_type'], unique=False)
    op.create_index(op.f('ix_comments_entity_id'), 'comments', ['entity_id'], unique=False)
    op.create_index(op.f('ix_comments_parent_comment_id'), 'comments', ['parent_comment_id'], unique=False)
    op.create_index('idx_comments_entity', 'comments', ['entity_type', 'entity_id'], unique=False)
    op.create_index('idx_comments_author_created', 'comments', ['author_id', 'created_at'], unique=False)
    op.create_index('idx_comments_parent', 'comments', ['parent_comment_id'], unique=False)
    op.create_check_constraint('valid_entity_type', 'comments', "entity_type IN ('Project', 'Task', 'Milestone')")

    # Create comment_mentions table
    op.create_table('comment_mentions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('comment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mentioned_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['comment_id'], ['comments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['mentioned_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_comment_mentions_comment_id'), 'comment_mentions', ['comment_id'], unique=False)
    op.create_index(op.f('ix_comment_mentions_mentioned_user_id'), 'comment_mentions', ['mentioned_user_id'], unique=False)
    op.create_index('idx_comment_mentions_comment', 'comment_mentions', ['comment_id'], unique=False)
    op.create_index('idx_comment_mentions_user', 'comment_mentions', ['mentioned_user_id'], unique=False)
    op.create_index('idx_comment_mentions_unique', 'comment_mentions', ['comment_id', 'mentioned_user_id'], unique=True)

    # Create comment_attachments table
    op.create_table('comment_attachments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('comment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['comment_id'], ['comments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_comment_attachments_comment_id'), 'comment_attachments', ['comment_id'], unique=False)
    op.create_index('idx_comment_attachments_comment', 'comment_attachments', ['comment_id'], unique=False)
    op.create_index('idx_comment_attachments_file_path', 'comment_attachments', ['file_path'], unique=False)

    # Create notifications table
    op.create_table('notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('entity_type', sa.String(length=20), nullable=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)
    op.create_index(op.f('ix_notifications_type'), 'notifications', ['type'], unique=False)
    op.create_index(op.f('ix_notifications_entity_type'), 'notifications', ['entity_type'], unique=False)
    op.create_index(op.f('ix_notifications_entity_id'), 'notifications', ['entity_id'], unique=False)
    op.create_index(op.f('ix_notifications_is_read'), 'notifications', ['is_read'], unique=False)
    op.create_index('idx_notifications_user_read', 'notifications', ['user_id', 'is_read'], unique=False)
    op.create_index('idx_notifications_user_created', 'notifications', ['user_id', 'created_at'], unique=False)
    op.create_index('idx_notifications_entity', 'notifications', ['entity_type', 'entity_id'], unique=False)

    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('old_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity_type'), 'audit_logs', ['entity_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity_id'), 'audit_logs', ['entity_id'], unique=False)
    op.create_index('idx_audit_logs_user_created', 'audit_logs', ['user_id', 'created_at'], unique=False)
    op.create_index('idx_audit_logs_action_created', 'audit_logs', ['action', 'created_at'], unique=False)
    op.create_index('idx_audit_logs_entity', 'audit_logs', ['entity_type', 'entity_id'], unique=False)
    op.create_index('idx_audit_logs_ip_created', 'audit_logs', ['ip_address', 'created_at'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('audit_logs')
    op.drop_table('notifications')
    op.drop_table('comment_attachments')
    op.drop_table('comment_mentions')
    op.drop_table('comments')
    op.drop_table('time_entries')
    op.drop_table('milestone_dependencies')
    op.drop_table('milestones')
    op.drop_table('task_dependencies')
    op.drop_table('tasks')
    op.drop_table('project_team_members')
    op.drop_table('projects')
    op.drop_table('user_skills')
    op.drop_table('users') 