# app/config/settings.py
"""
Centralized configuration using Pydantic BaseSettings.
All configuration is loaded from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./app.db",
        description="Async database URL (use postgresql+asyncpg:// or sqlite+aiosqlite://)",
    )

    # Security
    secret_key: str = Field(default="supersecretkey")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    
    # Encryption
    fernet_key: Optional[str] = Field(default=None)

    # Attachments
    attachments_dir: str = Field(default="attachments")
    attachment_base_url: str = Field(default="/attachments")

    # VBLOG Integration
    vblog_cnpj: Optional[str] = Field(default=None)
    vblog_token: Optional[str] = Field(default=None)
    vblog_base: Optional[str] = Field(default=None)

    # Brudam Tracking
    brudam_usuario: Optional[str] = Field(default=None)
    brudam_senha: Optional[str] = Field(default=None)
    brudam_url_tracking: Optional[str] = Field(default=None)
    brudam_cliente: Optional[str] = Field(default=None)

    # CORS - stored as string, accessed as property for list
    cors_origins_str: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="cors_origins"
    )

    @property
    def cors_origins(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins_str.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


# Convenience exports for backward compatibility
settings = get_settings()

# Legacy exports (deprecated - use settings.* instead)
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
SQLALCHEMY_DATABASE_URL = settings.database_url
FERNET_KEY = settings.fernet_key
ATTACHMENTS_DIR = settings.attachments_dir
ATTACHMENT_BASE_URL = settings.attachment_base_url
