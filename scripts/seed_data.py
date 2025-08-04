#!/usr/bin/env python3
"""
Database seeding script for Project Management Dashboard
Populates the database with mock data for testing
"""

import sys
import os
from datetime import datetime, timedelta
from typing import List

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import get_sync_db
from app.models.user import User
from app.models.project import Project, ProjectTeamMember
from app.models.task import Task
from app.models.time_entry import TimeEntry
from app.models.comment import Comment
from app.models.file import File
from app.models.milestone import Milestone
from app.models.notification import Notification
from app.core.auth import AuthUtils
from sqlalchemy.orm import Session


def seed_database():
    """Seed the database with mock data"""
    print("🌱 Starting database seeding...")
    
    # Get database session
    db = next(get_sync_db())
    
    try:
        # Create users
        users = create_users(db)
        print(f"✅ Created {len(users)} users")
        
        # Create projects
        projects = create_projects(db, users)
        print(f"✅ Created {len(projects)} projects")
        
        # Create tasks
        tasks = create_tasks(db, projects, users)
        print(f"✅ Created {len(tasks)} tasks")
        
        # Create time entries
        time_entries = create_time_entries(db, tasks, users)
        print(f"✅ Created {len(time_entries)} time entries")
        
        # Create comments
        comments = create_comments(db, tasks, users)
        print(f"✅ Created {len(comments)} comments")
        
        # Create milestones
        milestones = create_milestones(db, projects)
        print(f"✅ Created {len(milestones)} milestones")
        
        # Create notifications
        notifications = create_notifications(db, users)
        print(f"✅ Created {len(notifications)} notifications")
        
        # Create files
        files = create_files(db, projects, tasks, users)
        print(f"✅ Created {len(files)} files")
        
        db.commit()
        print("🎉 Database seeding completed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding database: {e}")
        raise
    finally:
        db.close()


def create_users(db: Session) -> List[User]:
    """Create mock users"""
    users_data = [
        {
            "email": "admin@example.com",
            "first_name": "Admin",
            "last_name": "User",
            "is_active": True,
            "role": "ProjectManager"
        },
        {
            "email": "john.doe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "is_active": True,
            "role": "ProjectManager"
        },
        {
            "email": "jane.smith@example.com",
            "first_name": "Jane",
            "last_name": "Smith",
            "is_active": True,
            "role": "Developer"
        },
        {
            "email": "mike.wilson@example.com",
            "first_name": "Mike",
            "last_name": "Wilson",
            "is_active": True,
            "role": "Developer"
        },
        {
            "email": "sarah.jones@example.com",
            "first_name": "Sarah",
            "last_name": "Jones",
            "is_active": True,
            "role": "QA"
        }
    ]
    
    users = []
    for user_data in users_data:
        user = User(
            email=user_data["email"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            password_hash=AuthUtils.get_password_hash("password123"),
            is_active=user_data["is_active"],
            role=user_data["role"]
        )
        db.add(user)
        users.append(user)
    
    db.commit()
    return users


def create_projects(db: Session, users: List[User]) -> List[Project]:
    """Create mock projects"""
    projects_data = [
        {
            "name": "E-commerce Platform",
            "description": "A modern e-commerce platform with advanced features",
            "status": "Active",
            "start_date": datetime.now() - timedelta(days=30),
            "end_date": datetime.now() + timedelta(days=60),
            "budget": 50000.00,
            "manager_id": users[1].id,  # John Doe
            "team_members": [users[0], users[2], users[3], users[4]]  # Admin, Jane, Mike, Sarah
        },
        {
            "name": "Mobile App Development",
            "description": "Cross-platform mobile application for task management",
            "status": "Draft",
            "start_date": datetime.now() + timedelta(days=7),
            "end_date": datetime.now() + timedelta(days=90),
            "budget": 35000.00,
            "manager_id": users[2].id,  # Jane Smith
            "team_members": [users[3], users[4]]  # Mike, Sarah
        },
        {
            "name": "Website Redesign",
            "description": "Complete redesign of company website with modern UI/UX",
            "status": "Completed",
            "start_date": datetime.now() - timedelta(days=90),
            "end_date": datetime.now() - timedelta(days=10),
            "budget": 25000.00,
            "manager_id": users[4].id,  # Sarah Jones
            "team_members": [users[2]]  # Jane
        },
        {
            "name": "API Integration Project",
            "description": "Integration of third-party APIs for payment processing",
            "status": "Active",
            "start_date": datetime.now() - timedelta(days=15),
            "end_date": datetime.now() + timedelta(days=30),
            "budget": 20000.00,
            "manager_id": users[3].id,  # Mike Wilson
            "team_members": [users[1], users[2]]  # John, Jane
        }
    ]
    
    projects = []
    for project_data in projects_data:
        project = Project(
            name=project_data["name"],
            description=project_data["description"],
            status=project_data["status"],
            start_date=project_data["start_date"],
            end_date=project_data["end_date"],
            budget=project_data["budget"],
            manager_id=project_data["manager_id"]
        )
        db.add(project)
        db.flush()  # Get the ID
        
        # Add team members
        for user in project_data["team_members"]:
            team_member = ProjectTeamMember(
                project_id=project.id,
                user_id=user.id,
                role=user.role
            )
            db.add(team_member)
        
        projects.append(project)
    
    db.commit()
    return projects


def create_tasks(db: Session, projects: List[Project], users: List[User]) -> List[Task]:
    """Create mock tasks"""
    tasks_data = [
        # E-commerce Platform tasks
        {
            "title": "Design User Interface",
            "description": "Create wireframes and mockups for the e-commerce platform",
            "status": "in_progress",
            "priority": "high",
            "project_id": projects[0].id,
            "assigned_to_id": users[4].id,  # Sarah (designer)
            "created_by_id": users[1].id,
            "due_date": datetime.now() + timedelta(days=10),
            "estimated_hours": 16
        },
        {
            "title": "Implement User Authentication",
            "description": "Set up JWT authentication and user registration",
            "status": "completed",
            "priority": "high",
            "project_id": projects[0].id,
            "assigned_to_id": users[2].id,  # Jane
            "created_by_id": users[1].id,
            "due_date": datetime.now() - timedelta(days=5),
            "estimated_hours": 24
        },
        {
            "title": "Database Schema Design",
            "description": "Design and implement the database schema for products and orders",
            "status": "in_progress",
            "priority": "medium",
            "project_id": projects[0].id,
            "assigned_to_id": users[3].id,  # Mike
            "created_by_id": users[1].id,
            "due_date": datetime.now() + timedelta(days=7),
            "estimated_hours": 20
        },
        {
            "title": "Payment Gateway Integration",
            "description": "Integrate Stripe payment gateway for processing payments",
            "status": "todo",
            "priority": "high",
            "project_id": projects[0].id,
            "assigned_to_id": users[2].id,  # Jane
            "created_by_id": users[1].id,
            "due_date": datetime.now() + timedelta(days=15),
            "estimated_hours": 32
        },
        
        # Mobile App tasks
        {
            "title": "Project Planning",
            "description": "Create detailed project plan and timeline",
            "status": "completed",
            "priority": "medium",
            "project_id": projects[1].id,
            "assigned_to_id": users[2].id,  # Jane
            "created_by_id": users[2].id,
            "due_date": datetime.now() - timedelta(days=2),
            "estimated_hours": 8
        },
        {
            "title": "UI/UX Design",
            "description": "Design mobile app interface and user experience",
            "status": "in_progress",
            "priority": "high",
            "project_id": projects[1].id,
            "assigned_to_id": users[4].id,  # Sarah
            "created_by_id": users[2].id,
            "due_date": datetime.now() + timedelta(days=14),
            "estimated_hours": 40
        },
        
        # Website Redesign tasks
        {
            "title": "Homepage Design",
            "description": "Design new homepage layout and content",
            "status": "completed",
            "priority": "high",
            "project_id": projects[2].id,
            "assigned_to_id": users[4].id,  # Sarah
            "created_by_id": users[4].id,
            "due_date": datetime.now() - timedelta(days=20),
            "estimated_hours": 16
        },
        {
            "title": "Content Migration",
            "description": "Migrate existing content to new design",
            "status": "completed",
            "priority": "medium",
            "project_id": projects[2].id,
            "assigned_to_id": users[2].id,  # Jane
            "created_by_id": users[4].id,
            "due_date": datetime.now() - timedelta(days=15),
            "estimated_hours": 12
        },
        
        # API Integration tasks
        {
            "title": "Stripe API Setup",
            "description": "Set up Stripe API credentials and basic integration",
            "status": "in_progress",
            "priority": "high",
            "project_id": projects[3].id,
            "assigned_to_id": users[3].id,  # Mike
            "created_by_id": users[3].id,
            "due_date": datetime.now() + timedelta(days=5),
            "estimated_hours": 16
        },
        {
            "title": "Payment Processing Logic",
            "description": "Implement payment processing and error handling",
            "status": "todo",
            "priority": "high",
            "project_id": projects[3].id,
            "assigned_to_id": users[2].id,  # Jane
            "created_by_id": users[3].id,
            "due_date": datetime.now() + timedelta(days=12),
            "estimated_hours": 24
        }
    ]
    
    tasks = []
    for task_data in tasks_data:
        task = Task(
            title=task_data["title"],
            description=task_data["description"],
            status=task_data["status"],
            priority=task_data["priority"],
            project_id=task_data["project_id"],
            assigned_to_id=task_data["assigned_to_id"],
            created_by_id=task_data["created_by_id"],
            due_date=task_data["due_date"],
            estimated_hours=task_data["estimated_hours"]
        )
        db.add(task)
        tasks.append(task)
    
    db.commit()
    return tasks


def create_time_entries(db: Session, tasks: List[Task], users: List[User]) -> List[TimeEntry]:
    """Create mock time entries"""
    time_entries_data = [
        # Time entries for completed tasks
        {
            "task_id": tasks[1].id,  # User Authentication
            "user_id": users[2].id,  # Jane
            "hours_spent": 6.5,
            "date": datetime.now() - timedelta(days=7),
            "description": "Implemented JWT authentication system"
        },
        {
            "task_id": tasks[1].id,
            "user_id": users[2].id,
            "hours_spent": 4.0,
            "date": datetime.now() - timedelta(days=6),
            "description": "Added user registration and login forms"
        },
        {
            "task_id": tasks[4].id,  # Project Planning
            "user_id": users[2].id,
            "hours_spent": 8.0,
            "date": datetime.now() - timedelta(days=3),
            "description": "Completed project planning and timeline"
        },
        {
            "task_id": tasks[6].id,  # Homepage Design
            "user_id": users[4].id,  # Sarah
            "hours_spent": 5.5,
            "date": datetime.now() - timedelta(days=25),
            "description": "Designed homepage layout and components"
        },
        {
            "task_id": tasks[6].id,
            "user_id": users[4].id,
            "hours_spent": 3.0,
            "date": datetime.now() - timedelta(days=24),
            "description": "Created responsive design mockups"
        },
        {
            "task_id": tasks[7].id,  # Content Migration
            "user_id": users[2].id,
            "hours_spent": 6.0,
            "date": datetime.now() - timedelta(days=18),
            "description": "Migrated homepage content"
        },
        {
            "task_id": tasks[7].id,
            "user_id": users[2].id,
            "hours_spent": 4.5,
            "date": datetime.now() - timedelta(days=17),
            "description": "Migrated about and contact pages"
        },
        
        # Time entries for in-progress tasks
        {
            "task_id": tasks[0].id,  # Design User Interface
            "user_id": users[4].id,  # Sarah
            "hours_spent": 4.0,
            "date": datetime.now() - timedelta(days=2),
            "description": "Started wireframe design"
        },
        {
            "task_id": tasks[0].id,
            "user_id": users[4].id,
            "hours_spent": 3.5,
            "date": datetime.now() - timedelta(days=1),
            "description": "Created product listing page mockups"
        },
        {
            "task_id": tasks[2].id,  # Database Schema Design
            "user_id": users[3].id,  # Mike
            "hours_spent": 5.0,
            "date": datetime.now() - timedelta(days=3),
            "description": "Designed product and order tables"
        },
        {
            "task_id": tasks[5].id,  # UI/UX Design
            "user_id": users[4].id,  # Sarah
            "hours_spent": 6.0,
            "date": datetime.now() - timedelta(days=1),
            "description": "Created mobile app wireframes"
        },
        {
            "task_id": tasks[8].id,  # Stripe API Setup
            "user_id": users[3].id,  # Mike
            "hours_spent": 4.5,
            "date": datetime.now() - timedelta(days=2),
            "description": "Set up Stripe API credentials"
        }
    ]
    
    time_entries = []
    for entry_data in time_entries_data:
        time_entry = TimeEntry(
            task_id=entry_data["task_id"],
            user_id=entry_data["user_id"],
            hours_spent=entry_data["hours_spent"],
            date=entry_data["date"],
            description=entry_data["description"],
            is_approved=True
        )
        db.add(time_entry)
        time_entries.append(time_entry)
    
    db.commit()
    return time_entries


def create_comments(db: Session, tasks: List[Task], users: List[User]) -> List[Comment]:
    """Create mock comments"""
    comments_data = [
        {
            "task_id": tasks[0].id,  # Design User Interface
            "user_id": users[1].id,  # John
            "content": "Great start on the wireframes! Can you also include the checkout flow?",
            "created_at": datetime.now() - timedelta(days=1)
        },
        {
            "task_id": tasks[0].id,
            "user_id": users[4].id,  # Sarah
            "content": "Thanks! I'll add the checkout flow to the next iteration.",
            "created_at": datetime.now() - timedelta(hours=12)
        },
        {
            "task_id": tasks[1].id,  # User Authentication
            "user_id": users[1].id,  # John
            "content": "Authentication looks good! Ready for testing.",
            "created_at": datetime.now() - timedelta(days=6)
        },
        {
            "task_id": tasks[2].id,  # Database Schema Design
            "user_id": users[1].id,  # John
            "content": "Can you add indexes for the product search functionality?",
            "created_at": datetime.now() - timedelta(days=2)
        },
        {
            "task_id": tasks[2].id,
            "user_id": users[3].id,  # Mike
            "content": "Sure! I'll add the necessary indexes for better performance.",
            "created_at": datetime.now() - timedelta(days=1)
        },
        {
            "task_id": tasks[5].id,  # UI/UX Design
            "user_id": users[2].id,  # Jane
            "content": "The mobile app design looks fantastic! When can we start development?",
            "created_at": datetime.now() - timedelta(hours=6)
        },
        {
            "task_id": tasks[8].id,  # Stripe API Setup
            "user_id": users[1].id,  # John
            "content": "API credentials are set up. Ready to proceed with payment processing.",
            "created_at": datetime.now() - timedelta(hours=3)
        }
    ]
    
    comments = []
    for comment_data in comments_data:
        comment = Comment(
            task_id=comment_data["task_id"],
            user_id=comment_data["user_id"],
            content=comment_data["content"],
            created_at=comment_data["created_at"]
        )
        db.add(comment)
        comments.append(comment)
    
    db.commit()
    return comments


def create_milestones(db: Session, projects: List[Project]) -> List[Milestone]:
    """Create mock milestones"""
    milestones_data = [
        {
            "project_id": projects[0].id,  # E-commerce Platform
            "title": "Design Phase Complete",
            "description": "All UI/UX designs approved and ready for development",
            "due_date": datetime.now() + timedelta(days=5),
            "status": "in_progress"
        },
        {
            "project_id": projects[0].id,
            "title": "Core Features Complete",
            "description": "User authentication, product catalog, and basic checkout",
            "due_date": datetime.now() + timedelta(days=25),
            "status": "todo"
        },
        {
            "project_id": projects[0].id,
            "title": "Payment Integration Complete",
            "description": "Full payment processing with Stripe integration",
            "due_date": datetime.now() + timedelta(days=40),
            "status": "todo"
        },
        {
            "project_id": projects[1].id,  # Mobile App
            "title": "Design Approval",
            "description": "Mobile app design approved by stakeholders",
            "due_date": datetime.now() + timedelta(days=10),
            "status": "in_progress"
        },
        {
            "project_id": projects[1].id,
            "title": "MVP Development",
            "description": "Minimum viable product ready for testing",
            "due_date": datetime.now() + timedelta(days=45),
            "status": "todo"
        },
        {
            "project_id": projects[2].id,  # Website Redesign
            "title": "Design Complete",
            "description": "All website designs completed and approved",
            "due_date": datetime.now() - timedelta(days=25),
            "status": "completed"
        },
        {
            "project_id": projects[2].id,
            "title": "Content Migration",
            "description": "All content migrated to new design",
            "due_date": datetime.now() - timedelta(days=15),
            "status": "completed"
        },
        {
            "project_id": projects[3].id,  # API Integration
            "title": "API Setup Complete",
            "description": "Stripe API credentials configured and tested",
            "due_date": datetime.now() + timedelta(days=3),
            "status": "in_progress"
        },
        {
            "project_id": projects[3].id,
            "title": "Payment Processing Live",
            "description": "Payment processing fully functional in production",
            "due_date": datetime.now() + timedelta(days=20),
            "status": "todo"
        }
    ]
    
    milestones = []
    for milestone_data in milestones_data:
        milestone = Milestone(
            project_id=milestone_data["project_id"],
            title=milestone_data["title"],
            description=milestone_data["description"],
            due_date=milestone_data["due_date"],
            status=milestone_data["status"]
        )
        db.add(milestone)
        milestones.append(milestone)
    
    db.commit()
    return milestones


def create_notifications(db: Session, users: List[User]) -> List[Notification]:
    """Create mock notifications"""
    notifications_data = [
        {
            "user_id": users[1].id,  # John
            "title": "New Task Assigned",
            "message": "You have been assigned to 'Payment Gateway Integration' task",
            "type": "task_assigned",
            "is_read": False
        },
        {
            "user_id": users[2].id,  # Jane
            "title": "Task Completed",
            "message": "Task 'User Authentication' has been marked as completed",
            "type": "task_completed",
            "is_read": True
        },
        {
            "user_id": users[3].id,  # Mike
            "title": "Comment Added",
            "message": "John Doe commented on your task 'Database Schema Design'",
            "type": "comment_added",
            "is_read": False
        },
        {
            "user_id": users[4].id,  # Sarah
            "title": "Project Update",
            "message": "Project 'E-commerce Platform' status updated to 'In Progress'",
            "type": "project_update",
            "is_read": False
        },
        {
            "user_id": users[1].id,  # John
            "title": "Time Entry Approved",
            "message": "Your time entry for 'User Authentication' has been approved",
            "type": "time_approved",
            "is_read": True
        },
        {
            "user_id": users[2].id,  # Jane
            "title": "Milestone Due Soon",
            "message": "Milestone 'Design Phase Complete' is due in 3 days",
            "type": "milestone_due",
            "is_read": False
        }
    ]
    
    notifications = []
    for notification_data in notifications_data:
        notification = Notification(
            user_id=notification_data["user_id"],
            title=notification_data["title"],
            message=notification_data["message"],
            type=notification_data["type"],
            is_read=notification_data["is_read"]
        )
        db.add(notification)
        notifications.append(notification)
    
    db.commit()
    return notifications


def create_files(db: Session, projects: List[Project], tasks: List[Task], users: List[User]) -> List[File]:
    """Create mock files"""
    files_data = [
        {
            "filename": "wireframes.pdf",
            "original_filename": "ecommerce_wireframes.pdf",
            "file_path": "/uploads/wireframes.pdf",
            "file_size": 2048576,  # 2MB
            "mime_type": "application/pdf",
            "project_id": projects[0].id,  # E-commerce Platform
            "task_id": tasks[0].id,  # Design User Interface
            "uploaded_by_id": users[4].id,  # Sarah
            "description": "Initial wireframes for e-commerce platform"
        },
        {
            "filename": "design_mockups.zip",
            "original_filename": "mobile_app_designs.zip",
            "file_path": "/uploads/design_mockups.zip",
            "file_size": 5242880,  # 5MB
            "mime_type": "application/zip",
            "project_id": projects[1].id,  # Mobile App
            "task_id": tasks[5].id,  # UI/UX Design
            "uploaded_by_id": users[4].id,  # Sarah
            "description": "Complete design mockups for mobile app"
        },
        {
            "filename": "api_documentation.md",
            "original_filename": "stripe_api_docs.md",
            "file_path": "/uploads/api_documentation.md",
            "file_size": 15360,  # 15KB
            "mime_type": "text/markdown",
            "project_id": projects[3].id,  # API Integration
            "task_id": tasks[8].id,  # Stripe API Setup
            "uploaded_by_id": users[3].id,  # Mike
            "description": "Stripe API integration documentation"
        },
        {
            "filename": "project_plan.docx",
            "original_filename": "mobile_app_project_plan.docx",
            "file_path": "/uploads/project_plan.docx",
            "file_size": 512000,  # 500KB
            "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "project_id": projects[1].id,  # Mobile App
            "task_id": tasks[4].id,  # Project Planning
            "uploaded_by_id": users[2].id,  # Jane
            "description": "Detailed project plan and timeline"
        },
        {
            "filename": "database_schema.sql",
            "original_filename": "ecommerce_schema.sql",
            "file_path": "/uploads/database_schema.sql",
            "file_size": 25600,  # 25KB
            "mime_type": "application/sql",
            "project_id": projects[0].id,  # E-commerce Platform
            "task_id": tasks[2].id,  # Database Schema Design
            "uploaded_by_id": users[3].id,  # Mike
            "description": "Database schema for e-commerce platform"
        }
    ]
    
    files = []
    for file_data in files_data:
        file_obj = File(
            filename=file_data["filename"],
            original_filename=file_data["original_filename"],
            file_path=file_data["file_path"],
            file_size=file_data["file_size"],
            mime_type=file_data["mime_type"],
            project_id=file_data["project_id"],
            task_id=file_data["task_id"],
            uploaded_by_id=file_data["uploaded_by_id"],
            description=file_data["description"]
        )
        db.add(file_obj)
        files.append(file_obj)
    
    db.commit()
    return files


if __name__ == "__main__":
    seed_database() 