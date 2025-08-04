"""
Authentication API endpoints.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import secrets

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.db.database import AsyncSessionWrapper

from app.core.auth import AuthUtils, add_to_blacklist, get_token_from_header
from app.core.security import SecurityUtils
from app.core.auth_config import (
    get_secret_key,
    get_algorithm,
    get_access_token_expire_minutes,
    get_refresh_token_expire_days,
    get_password_min_length
)
from app.core.dependencies import get_current_user, get_current_user_optional
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import (
    UserLoginRequest,
    UserRegisterRequest,
    TokenRefreshRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
    EmailVerificationRequest,
    ResendVerificationRequest,
    LoginResponse,
    RegisterResponse,
    RefreshResponse,
    LogoutResponse,
    ForgotPasswordResponse,
    ResetPasswordResponse,
    ChangePasswordResponse,
    EmailVerificationResponse,
    ResendVerificationResponse,
    SessionsResponse,
    RevokeSessionResponse,
    UserResponse,
    TokenResponse,
    TokenRefreshResponse,
    SessionInfo,
    ErrorResponse
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# In-memory storage for password reset tokens and email verification tokens
# In production, use Redis or database
password_reset_tokens = {}  # token -> (user_id, expiry)
email_verification_tokens = {}  # token -> (user_id, expiry)
user_sessions = {}  # user_id -> [session_info]


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: UserLoginRequest,
    request: Request,
    db: AsyncSessionWrapper = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.
    
    Args:
        login_data: User login credentials
        request: FastAPI request object
        db: Database session
        
    Returns:
        JWT access and refresh tokens with user information
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Find user by email
        user = db.session.query(User).filter(User.email == login_data.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Verify password
        if not AuthUtils.verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )
        
        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        db.session.commit()
        
        # Create tokens
        access_token = AuthUtils.create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role}
        )
        refresh_token = AuthUtils.create_refresh_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        # Track session
        session_id = secrets.token_urlsafe(32)
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        if str(user.id) not in user_sessions:
            user_sessions[str(user.id)] = []
        
        session_info = {
            "session_id": session_id,
            "created_at": datetime.now(timezone.utc),
            "last_activity": datetime.now(timezone.utc),
            "ip_address": client_ip,
            "user_agent": user_agent,
            "is_current": True
        }
        
        # Mark other sessions as not current
        for session in user_sessions[str(user.id)]:
            session["is_current"] = False
        
        user_sessions[str(user.id)].append(session_info)
        
        # Create response
        user_response = UserResponse(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )
        
        token_data = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=get_access_token_expire_minutes() * 60,
            user=user_response
        )
        
        return LoginResponse(
            success=True,
            data=token_data,
            message="Login successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    register_data: UserRegisterRequest,
    db: AsyncSessionWrapper = Depends(get_db)
):
    """
    Register a new user account.
    
    Args:
        register_data: User registration data
        db: Database session
        
    Returns:
        Created user information
        
    Raises:
        HTTPException: If registration fails
    """
    try:
        # Check if email already exists
        existing_user = db.session.query(User).filter(User.email == register_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Validate password strength
        if not AuthUtils.validate_password_strength(register_data.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not meet security requirements"
            )
        
        # Hash password
        password_hash = AuthUtils.get_password_hash(register_data.password)
        
        # Create new user
        new_user = User(
            email=register_data.email,
            password_hash=password_hash,
            first_name=register_data.first_name,
            last_name=register_data.last_name,
            role=register_data.role,
            is_active=True
        )
        
        db.session.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        # Generate email verification token
        verification_token = SecurityUtils.generate_verification_token()
        email_verification_tokens[verification_token] = (
            str(new_user.id),
            datetime.now(timezone.utc) + timedelta(hours=24)
        )
        
        # In production, send verification email here
        # For now, just return the token in response
        return RegisterResponse(
            success=True,
            data={
                "user": UserResponse.from_orm(new_user),
                "verification_token": verification_token  # Remove in production
            },
            message="User registered successfully. Please check your email for verification."
        )
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during registration"
        )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    refresh_data: TokenRefreshRequest,
    db: AsyncSessionWrapper = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    Args:
        refresh_data: Refresh token data
        db: Database session
        
    Returns:
        New access token
        
    Raises:
        HTTPException: If refresh fails
    """
    try:
        # Verify refresh token
        payload = AuthUtils.verify_token(refresh_data.refresh_token, "refresh")
        
        # Get user
        user_id = payload.get("sub")
        user = db.session.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new access token
        access_token = AuthUtils.create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role}
        )
        
        token_data = TokenRefreshResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=get_access_token_expire_minutes() * 60
        )
        
        return RefreshResponse(
            success=True,
            data=token_data,
            message="Token refreshed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    authorization: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Logout user and invalidate tokens.
    
    Args:
        authorization: Authorization header
        current_user: Current authenticated user
        
    Returns:
        Logout confirmation
        
    Raises:
        HTTPException: If logout fails
    """
    try:
        if authorization:
            token = get_token_from_header(authorization)
            add_to_blacklist(token)
        
        # Remove current session
        if str(current_user.id) in user_sessions:
            user_sessions[str(current_user.id)] = [
                session for session in user_sessions[str(current_user.id)]
                if not session.get("is_current", False)
            ]
        
        return LogoutResponse(
            success=True,
            message="Logout successful"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during logout"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user information
    """
    return UserResponse.from_orm(current_user)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    forgot_data: ForgotPasswordRequest,
    db: AsyncSessionWrapper = Depends(get_db)
):
    """
    Send password reset email.
    
    Args:
        forgot_data: Forgot password request data
        db: Database session
        
    Returns:
        Confirmation message
        
    Raises:
        HTTPException: If request fails
    """
    try:
        # Find user by email
        user = db.session.query(User).filter(User.email == forgot_data.email).first()
        if not user:
            # Don't reveal if email exists or not
            return ForgotPasswordResponse(
                success=True,
                message="If the email exists, a password reset link has been sent."
            )
        
        # Generate password reset token
        reset_token = SecurityUtils.generate_verification_token()
        password_reset_tokens[reset_token] = (
            str(user.id),
            datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        # In production, send email here
        # For now, just return the token in response
        return ForgotPasswordResponse(
            success=True,
            message=f"Password reset email sent. Token: {reset_token}"  # Remove in production
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during password reset request"
        )


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    reset_data: ResetPasswordRequest,
    db: AsyncSessionWrapper = Depends(get_db)
):
    """
    Reset password using reset token.
    
    Args:
        reset_data: Reset password request data
        db: Database session
        
    Returns:
        Confirmation message
        
    Raises:
        HTTPException: If reset fails
    """
    try:
        # Verify reset token
        if reset_data.token not in password_reset_tokens:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        user_id, expiry = password_reset_tokens[reset_data.token]
        if datetime.now(timezone.utc) > expiry:
            del password_reset_tokens[reset_data.token]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired"
            )
        
        # Validate new password strength
        if not AuthUtils.validate_password_strength(reset_data.new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not meet security requirements"
            )
        
        # Update user password
        user = db.session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )
        
        user.password_hash = AuthUtils.get_password_hash(reset_data.new_password)
        await db.commit()
        
        # Remove used token
        del password_reset_tokens[reset_data.token]
        
        # Invalidate all user sessions
        if str(user.id) in user_sessions:
            del user_sessions[str(user.id)]
        
        return ResetPasswordResponse(
            success=True,
            message="Password reset successfully"
        )
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during password reset"
        )


@router.post("/change-password", response_model=ChangePasswordResponse)
async def change_password(
    change_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSessionWrapper = Depends(get_db)
):
    """
    Change user password.
    
    Args:
        change_data: Change password request data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Confirmation message
        
    Raises:
        HTTPException: If change fails
    """
    try:
        # Verify current password
        if not AuthUtils.verify_password(change_data.current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password strength
        if not AuthUtils.validate_password_strength(change_data.new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not meet security requirements"
            )
        
        # Update password
        current_user.password_hash = AuthUtils.get_password_hash(change_data.new_password)
        await db.commit()
        
        # Invalidate all user sessions except current
        if str(current_user.id) in user_sessions:
            current_sessions = user_sessions[str(current_user.id)]
            user_sessions[str(current_user.id)] = [
                session for session in current_sessions
                if session.get("is_current", False)
            ]
        
        return ChangePasswordResponse(
            success=True,
            message="Password changed successfully"
        )
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during password change"
        )


@router.post("/verify-email", response_model=EmailVerificationResponse)
async def verify_email(
    verification_data: EmailVerificationRequest,
    db: AsyncSessionWrapper = Depends(get_db)
):
    """
    Verify user email address.
    
    Args:
        verification_data: Email verification request data
        db: Database session
        
    Returns:
        Confirmation message
        
    Raises:
        HTTPException: If verification fails
    """
    try:
        # Verify email verification token
        if verification_data.token not in email_verification_tokens:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
        
        user_id, expiry = email_verification_tokens[verification_data.token]
        if datetime.now(timezone.utc) > expiry:
            del email_verification_tokens[verification_data.token]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token has expired"
            )
        
        # Update user email verification status
        user = db.session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )
        
        # In production, you might have an email_verified field
        # For now, we'll just mark the user as active
        user.is_active = True
        await db.commit()
        
        # Remove used token
        del email_verification_tokens[verification_data.token]
        
        return EmailVerificationResponse(
            success=True,
            message="Email verified successfully"
        )
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during email verification"
        )


@router.post("/resend-verification", response_model=ResendVerificationResponse)
async def resend_verification(
    resend_data: ResendVerificationRequest,
    db: AsyncSessionWrapper = Depends(get_db)
):
    """
    Resend email verification.
    
    Args:
        resend_data: Resend verification request data
        db: Database session
        
    Returns:
        Confirmation message
        
    Raises:
        HTTPException: If request fails
    """
    try:
        # Find user by email
        user = db.session.query(User).filter(User.email == resend_data.email).first()
        if not user:
            # Don't reveal if email exists or not
            return ResendVerificationResponse(
                success=True,
                message="If the email exists, a verification link has been sent."
            )
        
        # Generate new verification token
        verification_token = SecurityUtils.generate_verification_token()
        email_verification_tokens[verification_token] = (
            str(user.id),
            datetime.now(timezone.utc) + timedelta(hours=24)
        )
        
        # In production, send email here
        # For now, just return the token in response
        return ResendVerificationResponse(
            success=True,
            message=f"Verification email sent. Token: {verification_token}"  # Remove in production
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during verification resend"
        )


@router.get("/sessions", response_model=SessionsResponse)
async def get_user_sessions(
    current_user: User = Depends(get_current_user)
):
    """
    Get user's active sessions.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        List of user sessions
    """
    try:
        sessions = user_sessions.get(str(current_user.id), [])
        session_info_list = [
            SessionInfo(**session) for session in sessions
        ]
        
        return SessionsResponse(
            success=True,
            data=session_info_list,
            message="Sessions retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error retrieving sessions"
        )


@router.delete("/sessions/{session_id}", response_model=RevokeSessionResponse)
async def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Revoke a specific user session.
    
    Args:
        session_id: Session ID to revoke
        current_user: Current authenticated user
        
    Returns:
        Confirmation message
        
    Raises:
        HTTPException: If revocation fails
    """
    try:
        if str(current_user.id) not in user_sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        sessions = user_sessions[str(current_user.id)]
        original_count = len(sessions)
        
        # Remove the specified session
        user_sessions[str(current_user.id)] = [
            session for session in sessions
            if session["session_id"] != session_id
        ]
        
        if len(user_sessions[str(current_user.id)]) == original_count:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return RevokeSessionResponse(
            success=True,
            message="Session revoked successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error revoking session"
        ) 
