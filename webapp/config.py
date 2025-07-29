"""
FacultyFinder FastAPI Configuration
Centralized configuration management for the application
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application settings
    app_name: str = "FacultyFinder API"
    app_version: str = "2.0.0"
    app_description: str = "High-performance API for discovering academic faculty and research collaborators worldwide"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server settings
    host: str = Field(default="127.0.0.1", env="HOST")
    port: int = Field(default=8008, env="PORT")
    workers: int = Field(default=4, env="WORKERS")
    
    # Database settings
    db_host: str = Field(default="localhost", env="DB_HOST")
    db_port: int = Field(default=5432, env="DB_PORT")
    db_user: str = Field(default="test_user", env="DB_USER")
    db_password: str = Field(default="test_password", env="DB_PASSWORD")
    db_name: str = Field(default="test_db", env="DB_NAME")
    
    # Database pool settings
    db_min_connections: int = Field(default=5, env="DB_MIN_CONNECTIONS")
    db_max_connections: int = Field(default=20, env="DB_MAX_CONNECTIONS")
    db_command_timeout: int = Field(default=60, env="DB_COMMAND_TIMEOUT")
    
    # API settings
    api_v1_prefix: str = "/api/v1"
    docs_url: str = "/api/docs"
    redoc_url: str = "/api/redoc"
    openapi_url: str = "/api/openapi.json"
    
    # CORS settings
    cors_origins: List[str] = Field(
        default=["*"], 
        env="CORS_ORIGINS",
        description="Comma-separated list of allowed origins"
    )
    cors_credentials: bool = Field(default=True, env="CORS_CREDENTIALS")
    cors_methods: List[str] = Field(default=["*"], env="CORS_METHODS")
    cors_headers: List[str] = Field(default=["*"], env="CORS_HEADERS")
    
    # Security settings
    secret_key: Optional[str] = Field(default=None, env="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Pagination settings
    default_page_size: int = Field(default=20, env="DEFAULT_PAGE_SIZE")
    max_page_size: int = Field(default=100, env="MAX_PAGE_SIZE")
    
    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # Static files
    static_dir: str = Field(default="webapp/static", env="STATIC_DIR")
    
    # Rate limiting (for nginx)
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    @property
    def database_url(self) -> str:
        """Construct database URL from components"""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return os.getenv("ENVIRONMENT", "development").lower() == "production"
    
    class Config:
        env_file = ".env.test"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


# Database configuration for asyncpg
DATABASE_CONFIG = {
    "host": settings.db_host,
    "port": settings.db_port,
    "user": settings.db_user,
    "password": settings.db_password,
    "database": settings.db_name,
    "min_size": settings.db_min_connections,
    "max_size": settings.db_max_connections,
    "command_timeout": settings.db_command_timeout,
}


# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": settings.log_format,
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        },
    },
    "handlers": {
        "default": {
            "level": settings.log_level,
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "level": "INFO",
            "formatter": "detailed",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "facultyfinder.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["default"],
            "level": settings.log_level,
            "propagate": False,
        },
        "facultyfinder": {
            "handlers": ["default", "file"] if settings.is_production else ["default"],
            "level": settings.log_level,
            "propagate": False,
        },
        "uvicorn": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False,
        },
        "asyncpg": {
            "handlers": ["default"],
            "level": "WARNING",  # Reduce asyncpg verbosity
            "propagate": False,
        },
    },
}


# FastAPI application configuration
FASTAPI_CONFIG = {
    "title": settings.app_name,
    "description": settings.app_description,
    "version": settings.app_version,
    "docs_url": settings.docs_url,
    "redoc_url": settings.redoc_url,
    "openapi_url": settings.openapi_url,
}


# CORS middleware configuration
CORS_CONFIG = {
    "allow_origins": settings.cors_origins,
    "allow_credentials": settings.cors_credentials,
    "allow_methods": settings.cors_methods,
    "allow_headers": settings.cors_headers,
}


def get_settings() -> Settings:
    """Get application settings (can be used for dependency injection)"""
    return settings 