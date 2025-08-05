"""
Main FastAPI application for the Project Management Dashboard.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.middleware.security import create_security_middleware
from contextlib import asynccontextmanager

from app.core.app_config import (
    get_app_name,
    get_app_version,
    get_allowed_hosts
)
from app.db.database import init_db, close_db
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.profile import router as profile_router
from app.api.skills import router as skills_router
from app.api.projects import router as projects_router
from app.api.milestones import router as milestones_router
from app.api.analytics import router as analytics_router
from app.api.tasks import router as tasks_router
from app.api.time_entries import router as time_entries_router
from app.api.comments import router as comments_router
from app.api.files import router as files_router
from app.api.audit import router as audit_router
from app.api.websocket import router as websocket_router
from app.api.reports import router as reports_router
from starlette.middleware.cors import ALL_METHODS  # <-- Add this

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    
    Args:
        app: FastAPI application instance
    """
    print("Starting up Project Management Dashboard API...")
    try:
        await init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        raise
    
    yield
    
    print("Shutting down Project Management Dashboard API...")
    try:
        await close_db()
        print("✅ Database connections closed successfully")
    except Exception as e:
        print(f"❌ Error closing database connections: {e}")


# Create FastAPI application
app = FastAPI(
    title=get_app_name(),
    description="Backend API for Project Management Dashboard",
    version=get_app_version(),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ✅ Add CORS middleware (fixed and clean)
allowed_origins = get_allowed_hosts()
print(f"🚀 Allowed CORS origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=ALL_METHODS,
    allow_headers=["*"],
)

# Add security middleware
create_security_middleware(app)

# Mount static files for avatars
try:
    app.mount("/static", StaticFiles(directory="uploads"), name="static")
except Exception:
    import os
    os.makedirs("uploads", exist_ok=True)
    app.mount("/static", StaticFiles(directory="uploads"), name="static")

# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(profile_router)
app.include_router(skills_router)
app.include_router(projects_router)
app.include_router(milestones_router)
app.include_router(analytics_router)
app.include_router(tasks_router)
app.include_router(time_entries_router)
app.include_router(comments_router)
app.include_router(files_router)
app.include_router(audit_router)
app.include_router(websocket_router)
app.include_router(reports_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Project Management Dashboard API",
        "version": get_app_version(),
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": get_app_version(),
        "app_name": get_app_name()
    }

@app.get("/info")
async def info():
    """Application information endpoint"""
    return {
        "app_name": get_app_name(),
        "version": get_app_version(),
        "debug": False,
        "database_url": "***",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
