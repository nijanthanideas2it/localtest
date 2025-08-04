#!/usr/bin/env python3
"""
Check and seed database script for Project Management Dashboard
Checks existing data and only adds missing data
"""

import sys
import os
from datetime import datetime, timedelta
from typing import List

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import get_sync_db
from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from app.models.time_entry import TimeEntry
from app.models.comment import Comment
from app.core.auth import AuthUtils
from sqlalchemy.orm import Session


def check_and_seed_database():
    """Check existing data and seed missing data"""
    print("🔍 Checking existing data and seeding missing data...")
    
    # Get database session
    db = next(get_sync_db())
    
    try:
        # Check and create users
        users = check_and_create_users(db)
        print(f"✅ Users: {len(users)} total")
        
        # Check and create projects
        projects = check_and_create_projects(db, users)
        print(f"✅ Projects: {len(projects)} total")
        
        # Check and create tasks
        tasks = check_and_create_tasks(db, projects, users)
        print(f"✅ Tasks: {len(tasks)} total")
        
        # Check and create time entries
        time_entries = check_and_create_time_entries(db, tasks, users)
        print(f"✅ Time Entries: {len(time_entries)} total")
        
        # Check and create comments
        comments = check_and_create_comments(db, tasks, users)
        print(f"✅ Comments: {len(comments)} total")
        
        db.commit()
        print("🎉 Database check and seed completed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()


def check_and_create_users(db: Session) -> List[User]:
    """Check existing users and create missing ones"""
    # Check if users already exist
    existing_users = db.query(User).all()
    if existing_users:
        print(f"📋 Found {len(existing_users)} existing users")
        return existing_users
    
    print("👥 Creating users...")
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


def check_and_create_projects(db: Session, users: List[User]) -> List[Project]:
    """Check existing projects and create missing ones"""
    existing_projects = db.query(Project).all()
    if existing_projects:
        print(f"📋 Found {len(existing_projects)} existing projects")
        return existing_projects
    
    print("📁 Creating projects...")
    projects_data = [
        {
            "name": "E-commerce Platform",
            "description": "A modern e-commerce platform with advanced features",
            "status": "Active",
            "start_date": datetime.now() - timedelta(days=30),
            "end_date": datetime.now() + timedelta(days=60),
            "budget": 50000.00,
            "manager_id": users[1].id,  # John Doe
        },
        {
            "name": "Mobile App Development",
            "description": "Cross-platform mobile application for task management",
            "status": "Draft",
            "start_date": datetime.now() + timedelta(days=7),
            "end_date": datetime.now() + timedelta(days=90),
            "budget": 35000.00,
            "manager_id": users[2].id,  # Jane Smith
        },
        {
            "name": "Website Redesign",
            "description": "Complete redesign of company website with modern UI/UX",
            "status": "Completed",
            "start_date": datetime.now() - timedelta(days=90),
            "end_date": datetime.now() - timedelta(days=10),
            "budget": 25000.00,
            "manager_id": users[4].id,  # Sarah Jones
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
        projects.append(project)
    
    db.commit()
    return projects


def check_and_create_tasks(db: Session, projects: List[Project], users: List[User]) -> List[Task]:
    """Check existing tasks and create missing ones"""
    existing_tasks = db.query(Task).all()
    if existing_tasks:
        print(f"📋 Found {len(existing_tasks)} existing tasks")
        return existing_tasks
    
    print("📝 Creating tasks...")
    tasks_data = [
        {
            "title": "Design User Interface",
            "description": "Create wireframes and mockups for the e-commerce platform",
            "status": "InProgress",
            "priority": "High",
            "project_id": projects[0].id,  # E-commerce Platform
            "assignee_id": users[4].id,  # Sarah (designer)
            "due_date": datetime.now() + timedelta(days=10),
            "estimated_hours": 16
        },
        {
            "title": "Implement User Authentication",
            "description": "Set up JWT authentication and user registration",
            "status": "Done",
            "priority": "High",
            "project_id": projects[0].id,  # E-commerce Platform
            "assignee_id": users[2].id,  # Jane
            "due_date": datetime.now() - timedelta(days=5),
            "estimated_hours": 24
        },
        {
            "title": "Database Schema Design",
            "description": "Design and implement the database schema for products and orders",
            "status": "InProgress",
            "priority": "Medium",
            "project_id": projects[0].id,  # E-commerce Platform
            "assignee_id": users[3].id,  # Mike
            "due_date": datetime.now() + timedelta(days=7),
            "estimated_hours": 20
        },
        {
            "title": "Project Planning",
            "description": "Create detailed project plan and timeline",
            "status": "Done",
            "priority": "Medium",
            "project_id": projects[1].id,  # Mobile App
            "assignee_id": users[2].id,  # Jane
            "due_date": datetime.now() - timedelta(days=2),
            "estimated_hours": 8
        },
        {
            "title": "UI/UX Design",
            "description": "Design mobile app interface and user experience",
            "status": "InProgress",
            "priority": "High",
            "project_id": projects[1].id,  # Mobile App
            "assignee_id": users[4].id,  # Sarah
            "due_date": datetime.now() + timedelta(days=14),
            "estimated_hours": 40
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
            assignee_id=task_data["assignee_id"],
            due_date=task_data["due_date"],
            estimated_hours=task_data["estimated_hours"]
        )
        db.add(task)
        tasks.append(task)
    
    db.commit()
    return tasks


def check_and_create_time_entries(db: Session, tasks: List[Task], users: List[User]) -> List[TimeEntry]:
    """Check existing time entries and create missing ones"""
    existing_entries = db.query(TimeEntry).all()
    if existing_entries:
        print(f"📋 Found {len(existing_entries)} existing time entries")
        return existing_entries
    
    print("⏱️ Creating time entries...")
    time_entries_data = [
        {
            "task_id": tasks[1].id,  # User Authentication
            "project_id": tasks[1].project_id,  # E-commerce Platform
            "user_id": users[2].id,  # Jane
            "hours": 6.5,
            "date": datetime.now() - timedelta(days=7),
            "category": "Development",
            "notes": "Implemented JWT authentication system"
        },
        {
            "task_id": tasks[1].id,
            "project_id": tasks[1].project_id,
            "user_id": users[2].id,
            "hours": 4.0,
            "date": datetime.now() - timedelta(days=6),
            "category": "Development",
            "notes": "Added user registration and login forms"
        },
        {
            "task_id": tasks[3].id,  # Project Planning
            "project_id": tasks[3].project_id,  # Mobile App
            "user_id": users[2].id,
            "hours": 8.0,
            "date": datetime.now() - timedelta(days=3),
            "category": "Documentation",
            "notes": "Completed project planning and timeline"
        },
        {
            "task_id": tasks[0].id,  # Design User Interface
            "project_id": tasks[0].project_id,  # E-commerce Platform
            "user_id": users[4].id,  # Sarah
            "hours": 4.0,
            "date": datetime.now() - timedelta(days=2),
            "category": "Development",
            "notes": "Started wireframe design"
        },
        {
            "task_id": tasks[0].id,
            "project_id": tasks[0].project_id,
            "user_id": users[4].id,
            "hours": 3.5,
            "date": datetime.now() - timedelta(days=1),
            "category": "Development",
            "notes": "Created product listing page mockups"
        }
    ]
    
    time_entries = []
    for entry_data in time_entries_data:
        time_entry = TimeEntry(
            task_id=entry_data["task_id"],
            project_id=entry_data["project_id"],
            user_id=entry_data["user_id"],
            hours=entry_data["hours"],
            date=entry_data["date"],
            category=entry_data["category"],
            notes=entry_data["notes"],
            is_approved=True
        )
        db.add(time_entry)
        time_entries.append(time_entry)
    
    db.commit()
    return time_entries


def check_and_create_comments(db: Session, tasks: List[Task], users: List[User]) -> List[Comment]:
    """Check existing comments and create missing ones"""
    existing_comments = db.query(Comment).all()
    if existing_comments:
        print(f"📋 Found {len(existing_comments)} existing comments")
        return existing_comments
    
    print("💬 Creating comments...")
    comments_data = [
        {
            "entity_id": tasks[0].id,  # Design User Interface
            "entity_type": "Task",
            "author_id": users[1].id,  # John
            "content": "Great start on the wireframes! Can you also include the checkout flow?",
            "created_at": datetime.now() - timedelta(days=1)
        },
        {
            "entity_id": tasks[0].id,
            "entity_type": "Task",
            "author_id": users[4].id,  # Sarah
            "content": "Thanks! I'll add the checkout flow to the next iteration.",
            "created_at": datetime.now() - timedelta(hours=12)
        },
        {
            "entity_id": tasks[1].id,  # User Authentication
            "entity_type": "Task",
            "author_id": users[1].id,  # John
            "content": "Authentication looks good! Ready for testing.",
            "created_at": datetime.now() - timedelta(days=6)
        },
        {
            "entity_id": tasks[2].id,  # Database Schema Design
            "entity_type": "Task",
            "author_id": users[1].id,  # John
            "content": "Can you add indexes for the product search functionality?",
            "created_at": datetime.now() - timedelta(days=2)
        },
        {
            "entity_id": tasks[2].id,
            "entity_type": "Task",
            "author_id": users[3].id,  # Mike
            "content": "Sure! I'll add the necessary indexes for better performance.",
            "created_at": datetime.now() - timedelta(days=1)
        }
    ]
    
    comments = []
    for comment_data in comments_data:
        comment = Comment(
            entity_id=comment_data["entity_id"],
            entity_type=comment_data["entity_type"],
            author_id=comment_data["author_id"],
            content=comment_data["content"],
            created_at=comment_data["created_at"]
        )
        db.add(comment)
        comments.append(comment)
    
    db.commit()
    return comments


if __name__ == "__main__":
    check_and_seed_database() 