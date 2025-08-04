"""
User service layer for business logic.
"""
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.user import User
from app.models.user import UserSkill
from app.core.auth import AuthUtils
from app.schemas.user import UserCreateRequest, UserUpdateRequest, UserQueryParams
from app.schemas.profile import ProfileUpdateRequest


class UserService:
    """Service class for user operations."""
    
    @staticmethod
    def create_user(db: Session, user_data: UserCreateRequest) -> User:
        """
        Create a new user.
        
        Args:
            db: Database session
            user_data: User creation data
            
        Returns:
            Created user
            
        Raises:
            ValueError: If email already exists
        """
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise ValueError("Email already registered")
        
        # Validate password strength
        if not AuthUtils.validate_password_strength(user_data.password):
            raise ValueError("Password does not meet security requirements")
        
        # Hash password
        password_hash = AuthUtils.get_password_hash(user_data.password)
        
        # Create new user
        new_user = User(
            email=user_data.email,
            password_hash=password_hash,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role,
            hourly_rate=user_data.hourly_rate,
            is_active=user_data.is_active,
            created_at=datetime.now(timezone.utc)
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_user
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User if found, None otherwise
        """
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_users_with_pagination(
        db: Session, 
        query_params: UserQueryParams
    ) -> Tuple[List[User], int]:
        """
        Get users with pagination and filtering.
        
        Args:
            db: Database session
            query_params: Query parameters for filtering and pagination
            
        Returns:
            Tuple of (users, total_count)
        """
        # Build query
        query = db.query(User)
        
        # Apply filters
        if query_params.role:
            query = query.filter(User.role == query_params.role)
        
        if query_params.is_active is not None:
            query = query.filter(User.is_active == query_params.is_active)
        
        if query_params.search:
            search_term = f"%{query_params.search}%"
            query = query.filter(
                or_(
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                    User.email.ilike(search_term)
                )
            )
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (query_params.page - 1) * query_params.limit
        users = query.offset(offset).limit(query_params.limit).all()
        
        return users, total_count
    
    @staticmethod
    def update_user(
        db: Session, 
        user_id: str, 
        update_data: UserUpdateRequest
    ) -> Optional[User]:
        """
        Update user information.
        
        Args:
            db: Database session
            user_id: User ID
            update_data: Update data
            
        Returns:
            Updated user if found, None otherwise
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        
        for field, value in update_dict.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def delete_user(db: Session, user_id: str) -> bool:
        """
        Delete user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            True if user was deleted, False if not found
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Check if user is the last admin
        if user.role == "Admin":
            admin_count = db.query(User).filter(User.role == "Admin").count()
            if admin_count <= 1:
                raise ValueError("Cannot delete the last admin user")
        
        db.delete(user)
        db.commit()
        
        return True
    
    @staticmethod
    def add_user_skill(
        db: Session, 
        user_id: str, 
        skill_name: str, 
        proficiency_level: str
    ) -> Optional[UserSkill]:
        """
        Add skill to user.
        
        Args:
            db: Database session
            user_id: User ID
            skill_name: Skill name
            proficiency_level: Proficiency level
            
        Returns:
            Created user skill if user found, None otherwise
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Check if skill already exists for user
        existing_skill = db.query(UserSkill).filter(
            and_(
                UserSkill.user_id == user_id,
                UserSkill.skill_name == skill_name
            )
        ).first()
        
        if existing_skill:
            raise ValueError("Skill already exists for this user")
        
        # Create new skill
        user_skill = UserSkill(
            user_id=user_id,
            skill_name=skill_name,
            proficiency_level=proficiency_level,
            created_at=datetime.now(timezone.utc)
        )
        
        db.add(user_skill)
        db.commit()
        db.refresh(user_skill)
        
        return user_skill
    
    @staticmethod
    def update_user_skill(
        db: Session, 
        user_id: str, 
        skill_id: str, 
        skill_name: str, 
        proficiency_level: str
    ) -> Optional[UserSkill]:
        """
        Update user skill.
        
        Args:
            db: Database session
            user_id: User ID
            skill_id: Skill ID
            skill_name: Skill name
            proficiency_level: Proficiency level
            
        Returns:
            Updated user skill if found, None otherwise
        """
        user_skill = db.query(UserSkill).filter(
            and_(
                UserSkill.id == skill_id,
                UserSkill.user_id == user_id
            )
        ).first()
        
        if not user_skill:
            return None
        
        # Check if skill name already exists for user (excluding current skill)
        existing_skill = db.query(UserSkill).filter(
            and_(
                UserSkill.user_id == user_id,
                UserSkill.skill_name == skill_name,
                UserSkill.id != skill_id
            )
        ).first()
        
        if existing_skill:
            raise ValueError("Skill already exists for this user")
        
        # Update skill
        user_skill.skill_name = skill_name
        user_skill.proficiency_level = proficiency_level
        user_skill.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(user_skill)
        
        return user_skill
    
    @staticmethod
    def delete_user_skill(db: Session, user_id: str, skill_id: str) -> bool:
        """
        Delete user skill.
        
        Args:
            db: Database session
            user_id: User ID
            skill_id: Skill ID
            
        Returns:
            True if skill was deleted, False if not found
        """
        user_skill = db.query(UserSkill).filter(
            and_(
                UserSkill.id == skill_id,
                UserSkill.user_id == user_id
            )
        ).first()
        
        if not user_skill:
            return False
        
        db.delete(user_skill)
        db.commit()
        
        return True
    
    @staticmethod
    def get_user_skills(db: Session, user_id: str) -> List[UserSkill]:
        """
        Get user skills.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            List of user skills
        """
        return db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    
    @staticmethod
    def get_user_with_skills(db: Session, user_id: str) -> Optional[User]:
        """
        Get user with skills by ID.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User with skills if found, None otherwise
        """
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_assignable_users(db: Session) -> List[User]:
        """
        Get users that can be assigned to tasks (developers and team leads).
        
        Args:
            db: Database session
            
        Returns:
            List of assignable users
        """
        return db.query(User).filter(
            and_(
                User.is_active == True,
                User.role.in_(['Developer', 'TeamLead'])
            )
        ).order_by(User.first_name, User.last_name).all()
    
    @staticmethod
    def calculate_pagination_info(total: int, page: int, limit: int) -> dict:
        """
        Calculate pagination information.
        
        Args:
            total: Total number of items
            page: Current page
            limit: Items per page
            
        Returns:
            Pagination information dictionary
        """
        pages = (total + limit - 1) // limit  # Ceiling division
        
        return {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": pages
        }
    
    @staticmethod
    def update_user_profile(
        db: Session, 
        user_id: str, 
        profile_data: ProfileUpdateRequest
    ) -> Optional[User]:
        """
        Update user profile information.
        
        Args:
            db: Database session
            user_id: User ID
            profile_data: Profile update data
            
        Returns:
            Updated user if found, None otherwise
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Update fields
        update_dict = profile_data.dict(exclude_unset=True)
        
        for field, value in update_dict.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def update_user_avatar(db: Session, user_id: str, avatar_url: str) -> Optional[User]:
        """
        Update user avatar URL.
        
        Args:
            db: Database session
            user_id: User ID
            avatar_url: New avatar URL
            
        Returns:
            Updated user if found, None otherwise
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Delete old avatar if it exists
        if user.avatar_url:
            from app.services.file_service import FileService
            FileService.delete_avatar(user.avatar_url)
        
        # Update avatar URL
        user.avatar_url = avatar_url
        user.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(user)
        
        return user 