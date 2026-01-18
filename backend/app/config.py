"""
Configuration settings for the Fund Analytics Platform backend.
Uses environment variables for sensitive data.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App Settings
    app_name: str = "Fund Analytics Platform"
    app_version: str = "2.0.0"
    debug: bool = False
    
    # API Settings
    api_prefix: str = "/api"
    
    # CORS Settings
    cors_origins: list[str] = [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative dev port
        "https://fund-analytics.vercel.app",  # Production frontend (update this)
    ]
    
    # Supabase Settings
    supabase_url: str = ""
    supabase_key: str = ""
    
    # Redis Settings (optional, for caching)
    redis_url: Optional[str] = None
    
    # GitHub Releases (for data loading)
    github_token: Optional[str] = None
    github_repo: Optional[str] = None
    
    # Cache Settings
    cache_ttl_seconds: int = 300  # 5 minutes default
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export settings instance
settings = get_settings()
