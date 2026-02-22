"""Tests for dashboard configuration."""

import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import directly from the config module file to avoid circular imports
# triggered by dashboard.core.__init__.py
import importlib.util

config_path = Path(__file__).parent.parent / "dashboard" / "core" / "config.py"
spec = importlib.util.spec_from_file_location("dashboard.core.config", config_path)
config_module = importlib.util.module_from_spec(spec)
sys.modules["dashboard.core.config"] = config_module
spec.loader.exec_module(config_module)

settings = config_module.settings


def test_comfyui_user_path_exists():
    """Verify COMFYUI_USER_PATH is configured."""
    assert hasattr(settings, 'COMFYUI_USER_PATH')
    assert settings.COMFYUI_USER_PATH == '/workspace/ComfyUI/user'
