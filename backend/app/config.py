"""
Application Configuration
Manages environment variables and application settings.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Doctor Appointment Assistant"
    debug: bool = True
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/doctor_assistant"
    database_url_sync: str = "postgresql://postgres:password@localhost:5432/doctor_assistant"
    
    # Security
    secret_key: str = "your-super-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Mistral AI (Free tier available!)
    mistral_api_key: str = ""
    mistral_model: str = "mistral-small-latest"
    
    # Google APIs
    google_credentials_file: str = "credentials.json"
    google_token_file: str = "token.json"
    
    # SendGrid
    sendgrid_api_key: str = ""
    from_email: str = "noreply@doctorapp.com"
    
    # Slack
    slack_webhook_url: str = ""
    slack_bot_token: str = ""
    
    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
