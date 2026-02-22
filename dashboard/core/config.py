"""
Configuration management for ComfyUI Unified Dashboard
Handles environment variables and application settings
"""

from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application settings
    APP_NAME: str = "ComfyUI Unified Dashboard"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Port settings
    DASHBOARD_PORT: int = 8080
    COMFYUI_PORT: int = 3000

    # Path settings
    BASE_DIR: Path = Path("/workspace")
    MODEL_BASE_PATH: str = "/workspace/models"
    PRESET_CONFIG_PATH: str = "/workspace/config/presets.yaml"
    WORKFLOW_BASE_PATH: str = "/workspace/workflows"
    COMFYUI_USER_PATH: str = "/workspace/ComfyUI/user"

    # Download settings
    DOWNLOAD_TIMEOUT: int = 3600  # 1 hour
    MAX_CONCURRENT_DOWNLOADS: int = 3
    DOWNLOAD_CHUNK_SIZE: int = 8192

    # Security settings
    ACCESS_PASSWORD: Optional[str] = None
    SECRET_KEY: str = "your-secret-key-change-in-production"

    # CORS settings
    ALLOWED_ORIGINS: list = ["*"]

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "/workspace/logs/dashboard.log"

    # WebSocket settings
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS: int = 100

    # Background task settings
    ENABLE_BACKGROUND_DOWNLOADS: bool = True
    DOWNLOAD_STATUS_CHECK_INTERVAL: int = 5  # seconds

    class Config:
        env_file = "/workspace/.env"
        case_sensitive = True


# Global settings instance
settings = Settings()


__all__ = ["settings"]
