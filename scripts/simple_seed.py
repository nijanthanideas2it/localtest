#!/usr/bin/env python3
"""
Simple database seeding script for Project Management Dashboard
Populates the database with basic mock data for testing
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


def seed_database():
    """Seed the database with basic mock data"""
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


def create_tasks(db: Session, projects: List[Project], users: List[User]) -> List[Task]:
    """Create mock tasks"""
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


def create_time_entries(db: Session, tasks: List[Task], users: List[User]) -> List[TimeEntry]:
    """Create mock time entries"""
    time_entries_data = [
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
            "task_id": tasks[3].id,  # Project Planning
            "user_id": users[2].id,
            "hours_spent": 8.0,
            "date": datetime.now() - timedelta(days=3),
            "description": "Completed project planning and timeline"
        },
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


if __name__ == "__main__":
    seed_database() 