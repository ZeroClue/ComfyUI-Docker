"""
Configuration for ComfyUI Studio
"""
import os


class Config:
    """Studio configuration"""

    # ComfyUI connection
    COMFYUI_HOST = os.getenv("COMFYUI_HOST", "127.0.0.1")
    COMFYUI_PORT = int(os.getenv("COMFYUI_PORT", "3000"))

    # Studio settings
    STUDIO_PORT = int(os.getenv("STUDIO_PORT", "5000"))
    STUDIO_HOST = os.getenv("STUDIO_HOST", "0.0.0.0")

    # Workspace paths
    WORKSPACE_ROOT = os.getenv("WORKSPACE_ROOT", "/workspace")
    WORKFLOWS_FOLDER = os.path.join(WORKSPACE_ROOT, "config/workflows")
    UPLOAD_FOLDER = os.path.join(WORKSPACE_ROOT, "uploads")
    OUTPUT_FOLDER = os.path.join(WORKSPACE_ROOT, "ComfyUI/output")

    # ComfyUI paths (for syncing)
    COMFYUI_WORKFLOWS_FOLDER = os.path.join(
        WORKSPACE_ROOT, "ComfyUI/user/default/workflows"
    )

    # Authentication
    ACCESS_PASSWORD = os.getenv("ACCESS_PASSWORD", "password")
    SECRET_KEY = os.getenv("SECRET_KEY", "comfyui-studio-secret-key-change-in-production")

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @property
    def comfyui_url(self) -> str:
        """Get ComfyUI HTTP URL"""
        return f"http://{self.COMFYUI_HOST}:{self.COMFYUI_PORT}"

    @property
    def comfyui_ws_url(self) -> str:
        """Get ComfyUI WebSocket URL"""
        return f"ws://{self.COMFYUI_HOST}:{self.COMFYUI_PORT}"

    def ensure_directories(self):
        """Ensure required directories exist"""
        for folder in [self.WORKFLOWS_FOLDER, self.UPLOAD_FOLDER]:
            os.makedirs(folder, exist_ok=True)


# Global config instance
config = Config()
