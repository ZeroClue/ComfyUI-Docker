"""
Configuration settings for the ComfyUI Preset Manager
"""

# File paths
README_BASE_PATH = "/workspace/docs/presets"
WORKSPACE_DIR = "/workspace"

# Default model paths
MODEL_PATHS = {
    "checkpoints": "/workspace/ComfyUI/models/checkpoints",
    "diffusion_models": "/workspace/ComfyUI/models/diffusion_models",
    "text_encoders": "/workspace/ComfyUI/models/text_encoders",
    "vae": "/workspace/ComfyUI/models/vae",
    "loras": "/workspace/ComfyUI/models/loras",
    "upscale_models": "/workspace/ComfyUI/models/upscale_models",
    "audio_encoders": "/workspace/ComfyUI/models/audio_encoders",
    "TTS": "/workspace/ComfyUI/models/TTS",
    "audio": "/workspace/ComfyUI/models/audio"
}

# Flask configuration
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000
SECRET_KEY = "your-secret-key-change-in-production"

# Default categories
DEFAULT_CATEGORIES = {
    "Video Generation": ["video", "animation", "motion"],
    "Image Generation": ["image", "picture", "photo", "art"],
    "Audio Generation": ["audio", "sound", "music", "speech", "tts", "voice"],
    "Utility": ["enhancement", "upscale", "utility", "tool"]
}

# Logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"