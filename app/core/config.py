from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Project Management Dashboard API"
    VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Server
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # CORS
    ALLOWED_HOSTS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "http://localhost:3004", "http://localhost:8080"],
        env="ALLOWED_HOSTS"
    )
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_REQUESTS_PER_MINUTE")
    RATE_LIMIT_REQUESTS_PER_HOUR: int = Field(default=1000, env="RATE_LIMIT_REQUESTS_PER_HOUR")
    RATE_LIMIT_BURST_SIZE: int = Field(default=10, env="RATE_LIMIT_BURST_SIZE")
    
    # Security Headers
    SECURITY_HEADERS_ENABLED: bool = Field(default=True, env="SECURITY_HEADERS_ENABLED")
    CONTENT_SECURITY_POLICY: str = Field(
        default="default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; font-src 'self' https://cdn.jsdelivr.net; img-src 'self' data: https:;",
        env="CONTENT_SECURITY_POLICY"
    )
    STRICT_TRANSPORT_SECURITY: str = Field(
        default="max-age=31536000; includeSubDomains",
        env="STRICT_TRANSPORT_SECURITY"
    )
    X_FRAME_OPTIONS: str = Field(default="DENY", env="X_FRAME_OPTIONS")
    X_CONTENT_TYPE_OPTIONS: str = Field(default="nosniff", env="X_CONTENT_TYPE_OPTIONS")
    X_XSS_PROTECTION: str = Field(default="1; mode=block", env="X_XSS_PROTECTION")
    REFERRER_POLICY: str = Field(default="strict-origin-when-cross-origin", env="REFERRER_POLICY")
    
    # Input Sanitization
    INPUT_SANITIZATION_ENABLED: bool = Field(default=True, env="INPUT_SANITIZATION_ENABLED")
    MAX_REQUEST_SIZE: int = Field(default=10 * 1024 * 1024, env="MAX_REQUEST_SIZE")  # 10MB
    MAX_HEADER_SIZE: int = Field(default=8192, env="MAX_HEADER_SIZE")
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://project_management_eaoe_user:EnNCBCl069GPZUOHFrAZBN9qO2NzNhCv@dpg-d285ofc9c44c73a3ng5g-a.oregon-postgres.render.com/project_management_eaoe",
        env="DATABASE_URL"
    )
    DATABASE_ECHO: bool = Field(default=False, env="DATABASE_ECHO")
    
    # Security
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Password
    PASSWORD_MIN_LENGTH: int = Field(default=8, env="PASSWORD_MIN_LENGTH")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings() 
