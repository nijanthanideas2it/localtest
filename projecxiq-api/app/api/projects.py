"""
Projects API endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.database import AsyncSessionWrapper, get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.services.project_service import ProjectService
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectQueryParams,
    TeamMemberRequest,
    ProjectCreateResponseWrapper,
    ProjectUpdateResponseWrapper,
    ProjectDeleteResponseWrapper,
    ProjectListResponseWrapper,
    ProjectResponseWrapper,
    ProjectListResponse,
    ProjectResponse
)
from app.schemas.team import (
    TeamMemberRoleUpdateRequest,
    TeamListResponse,
    TeamMemberUpdateResponse,
    TeamMemberAddResponse,
    TeamMemberRemoveResponse,
    TeamStatsWrapper
)
from app.models.project import Project
from sqlalchemy.orm import joinedload

router = APIRouter(prefix="/projects", tags=["Project Management"])


@router.get("/debug")
async def debug_projects(
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Debug endpoint to test project queries."""
    try:
        # Simple query to test
        projects = db.session.query(Project).limit(5).all()
        return {
            "success": True,
            "count": len(projects),
            "projects": [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "status": p.status,
                    "manager_id": str(p.manager_id)
                }
                for p in projects
            ]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }



@router.get("", response_model=ProjectListResponseWrapper)
async def get_projects(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    manager_id: Optional[str] = Query(None, description="Filter by manager"),
    search: Optional[str] = Query(None, description="Search by name"),
    my_projects: Optional[bool] = Query(None, description="Show only user's projects"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get paginated list of projects with filtering.
    """
    try:
        # Very simple query without relationships
        query = db.session.query(Project)
        
        # Apply basic filters
        if status:
            query = query.filter(Project.status == status)
        
        if manager_id:
            query = query.filter(Project.manager_id == manager_id)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        projects = query.offset(offset).limit(limit).all()
        
        # Convert to response models
        project_list = []
        for project in projects:
            project_response = ProjectListResponse(
                id=project.id,
                name=project.name,
                description=project.description,
                start_date=project.start_date,
                end_date=project.end_date,
                budget=project.budget,
                actual_cost=project.actual_cost,
                status=project.status,
                manager=None,  # Don't load manager for now
                team_size=0,
                progress_percentage=None,
                created_at=project.created_at
            )
            project_list.append(project_response)
        
        # Simple pagination info
        pagination_info = {
            "page": page,
            "limit": limit,
            "total": total_count,
            "pages": (total_count + limit - 1) // limit
        }
        
        return ProjectListResponseWrapper(
            success=True,
            data=project_list,
            pagination=pagination_info,
            message="Projects retrieved successfully"
        )
        
    except Exception as e:
        import traceback
        print(f"Error in get_projects: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/assigned", response_model=ProjectListResponseWrapper)
async def get_assigned_projects(
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get projects assigned to the current user (developer).
    """
    try:
        projects = ProjectService.get_projects_for_user(db.session, current_user.id)
        return ProjectListResponseWrapper(
            success=True,
            data=[ProjectResponse.from_orm(project) for project in projects],
            message="Assigned projects retrieved successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{project_id}", response_model=ProjectResponseWrapper)
async def get_project(
    project_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific project details.
    
    Args:
        project_id: Project ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Project details
    """
    try:
        project = ProjectService.get_project_by_id(db.session, project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check access permissions
        if not ProjectService.can_access_project(project, str(current_user.id), current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project"
            )
        
        # Convert to response model
        project_response = ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            start_date=project.start_date,
            end_date=project.end_date,
            budget=project.budget,
            actual_cost=project.actual_cost,
            status=project.status,
            manager_id=project.manager_id,
            manager=project.manager,
            team_members=project.team_members,
            created_at=project.created_at,
            updated_at=project.updated_at
        )
        
        return ProjectResponseWrapper(
            success=True,
            data=project_response,
            message="Project retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("", response_model=ProjectCreateResponseWrapper, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreateRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "ProjectManager"]))
):
    """
    Create new project.
    
    Args:
        project_data: Project creation data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created project details
    """
    try:
        project = ProjectService.create_project(
            db.session,
            project_data,
            str(current_user.id)
        )
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create project"
            )
        
        # Convert to response model
        project_response = ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            start_date=project.start_date,
            end_date=project.end_date,
            budget=project.budget,
            actual_cost=project.actual_cost,
            status=project.status,
            manager_id=project.manager_id,
            manager=project.manager,
            team_members=project.team_members,
            created_at=project.created_at,
            updated_at=project.updated_at
        )
        
        return ProjectCreateResponseWrapper(
            success=True,
            data=project_response,
            message="Project created successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.put("/{project_id}", response_model=ProjectUpdateResponseWrapper)
async def update_project(
    project_id: str,
    update_data: ProjectUpdateRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update project details.
    
    Args:
        project_id: Project ID
        update_data: Project update data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated project details
    """
    try:
        # Get project and check permissions
        project = ProjectService.get_project_by_id(db.session, project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check management permissions
        if not ProjectService.can_manage_project(project, str(current_user.id), current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this project"
            )
        
        updated_project = ProjectService.update_project(
            db.session,
            project_id,
            update_data
        )
        
        if not updated_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Convert to response model
        project_response = ProjectResponse(
            id=updated_project.id,
            name=updated_project.name,
            description=updated_project.description,
            start_date=updated_project.start_date,
            end_date=updated_project.end_date,
            budget=updated_project.budget,
            actual_cost=updated_project.actual_cost,
            status=updated_project.status,
            manager_id=updated_project.manager_id,
            manager=updated_project.manager,
            team_members=updated_project.team_members,
            created_at=updated_project.created_at,
            updated_at=updated_project.updated_at
        )
        
        return ProjectUpdateResponseWrapper(
            success=True,
            data=project_response,
            message="Project updated successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/{project_id}", response_model=ProjectDeleteResponseWrapper)
async def delete_project(
    project_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "ProjectManager"]))
):
    """
    Delete project.
    
    Args:
        project_id: Project ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Deletion confirmation
    """
    try:
        # Get project and check permissions
        project = ProjectService.get_project_by_id(db.session, project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check management permissions
        if not ProjectService.can_manage_project(project, str(current_user.id), current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this project"
            )
        
        success = ProjectService.delete_project(db.session, project_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        return ProjectDeleteResponseWrapper(
            success=True,
            message="Project deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/{project_id}/team-members", response_model=ProjectResponseWrapper)
async def add_team_member(
    project_id: str,
    member_data: TeamMemberRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add team member to project.
    
    Args:
        project_id: Project ID
        member_data: Team member data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated project details
    """
    try:
        # Get project and check permissions
        project = ProjectService.get_project_by_id(db.session, project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check management permissions
        if not ProjectService.can_manage_project(project, str(current_user.id), current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to add team members to this project"
            )
        
        team_member = ProjectService.add_team_member(
            db.session,
            project_id,
            str(member_data.user_id),
            member_data.role
        )
        
        if not team_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add team member"
            )
        
        # Get updated project
        updated_project = ProjectService.get_project_by_id(db.session, project_id)
        
        # Convert to response model
        project_response = ProjectResponse(
            id=updated_project.id,
            name=updated_project.name,
            description=updated_project.description,
            start_date=updated_project.start_date,
            end_date=updated_project.end_date,
            budget=updated_project.budget,
            actual_cost=updated_project.actual_cost,
            status=updated_project.status,
            manager_id=updated_project.manager_id,
            manager=updated_project.manager,
            team_members=updated_project.team_members,
            created_at=updated_project.created_at,
            updated_at=updated_project.updated_at
        )
        
        return ProjectResponseWrapper(
            success=True,
            data=project_response,
            message="Team member added successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/{project_id}/team-members/{user_id}", response_model=ProjectDeleteResponseWrapper)
async def remove_team_member(
    project_id: str,
    user_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove team member from project.
    
    Args:
        project_id: Project ID
        user_id: User ID to remove
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Removal confirmation
    """
    try:
        # Get project and check permissions
        project = ProjectService.get_project_by_id(db.session, project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check management permissions
        if not ProjectService.can_manage_project(project, str(current_user.id), current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to remove team members from this project"
            )
        
        success = ProjectService.remove_team_member(db.session, project_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team member not found"
            )
        
        return ProjectDeleteResponseWrapper(
            success=True,
            message="Team member removed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{project_id}/team", response_model=TeamListResponse)
async def get_project_team(
    project_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get project team members.
    
    Args:
        project_id: Project ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of team members
    """
    try:
        # Get project and check access permissions
        project = ProjectService.get_project_by_id(db.session, project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check access permissions
        if not ProjectService.can_access_project(project, str(current_user.id), current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project"
            )
        
        # Get team members
        team_members = ProjectService.get_project_team_members(db.session, project_id)
        
        return TeamListResponse(
            success=True,
            data=team_members,
            message="Team members retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.put("/{project_id}/team/{member_id}", response_model=TeamMemberUpdateResponse)
async def update_team_member_role(
    project_id: str,
    member_id: str,
    role_data: TeamMemberRoleUpdateRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update team member role.
    
    Args:
        project_id: Project ID
        member_id: Team member ID
        role_data: New role data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated team member details
    """
    try:
        # Get project and check permissions
        project = ProjectService.get_project_by_id(db.session, project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check management permissions
        if not ProjectService.can_manage_project(project, str(current_user.id), current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update team members in this project"
            )
        
        updated_member = ProjectService.update_team_member_role(
            db.session,
            project_id,
            member_id,
            role_data.role
        )
        
        if not updated_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team member not found"
            )
        
        return TeamMemberUpdateResponse(
            success=True,
            data=updated_member,
            message="Team member role updated successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{project_id}/team/stats", response_model=TeamStatsWrapper)
async def get_project_team_stats(
    project_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get project team statistics.
    
    Args:
        project_id: Project ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Team statistics
    """
    try:
        # Get project and check access permissions
        project = ProjectService.get_project_by_id(db.session, project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check access permissions
        if not ProjectService.can_access_project(project, str(current_user.id), current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project"
            )
        
        # Get team statistics
        team_stats = ProjectService.get_team_statistics(db.session, project_id)
        
        return TeamStatsWrapper(
            success=True,
            data=team_stats,
            message="Team statistics retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        ) 