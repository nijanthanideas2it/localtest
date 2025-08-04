"""
Main FastAPI application for the Project Management Dashboard.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.middleware.security import create_security_middleware
from contextlib import asynccontextmanager

from app.core.config import settings
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    
    Args:
        app: FastAPI application instance
    """
    # Startup
    print("Starting up Project Management Dashboard API...")
    try:
        await init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        raise
    
    yield
    
    # Shutdown
    print("Shutting down Project Management Dashboard API...")
    try:
        await close_db()
        print("✅ Database connections closed successfully")
    except Exception as e:
        print(f"❌ Error closing database connections: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for Project Management Dashboard",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add security middleware
create_security_middleware(app)

# Mount static files for avatars
try:
    app.mount("/static", StaticFiles(directory="uploads"), name="static")
except Exception:
    # Create uploads directory if it doesn't exist
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
        "version": settings.VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "app_name": settings.APP_NAME
    }


@app.get("/info")
async def info():
    """Application information endpoint"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "debug": settings.DEBUG,
        "database_url": settings.DATABASE_URL.replace(
            settings.DATABASE_URL.split('@')[0].split('://')[1], 
            "***:***"
        ) if '@' in settings.DATABASE_URL else "***",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    ) 