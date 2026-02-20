"""
Preset management API endpoints
Handles preset listing, installation, and status checking
"""

import asyncio
import aiohttp
import time
from typing import List, Dict, Optional, Any
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from ..core.config import settings
from ..core.downloader import DownloadManager
from ..core.comfyui_client import ComfyUIClient
from ..core import persistence


# Cache for preset configuration and installation status
class PresetCache:
    """Simple cache for preset data to avoid repeated file I/O"""

    def __init__(self, ttl_seconds: int = 60):
        self._config_cache: Optional[Dict] = None
        self._config_timestamp: float = 0
        self._installed_cache: Dict[str, bool] = {}
        self._installed_timestamp: float = 0
        self._ttl = ttl_seconds

    def get_config(self) -> Optional[Dict]:
        """Get cached config if still valid"""
        if self._config_cache and (time.time() - self._config_timestamp) < self._ttl:
            return self._config_cache
        return None

    def set_config(self, config: Dict):
        """Cache the config"""
        self._config_cache = config
        self._config_timestamp = time.time()

    def invalidate_config(self):
        """Invalidate config cache"""
        self._config_cache = None
        self._config_timestamp = 0

    def get_installed_status(self) -> Dict[str, bool]:
        """Get cached installation status if still valid"""
        if (time.time() - self._installed_timestamp) < self._ttl:
            return self._installed_cache.copy()
        return {}

    def set_installed_status(self, status: Dict[str, bool]):
        """Cache installation status"""
        self._installed_cache = status
        self._installed_timestamp = time.time()

    def invalidate_installed(self):
        """Invalidate installation status cache"""
        self._installed_cache = {}
        self._installed_timestamp = 0


# Global cache instance
preset_cache = PresetCache(ttl_seconds=60)


# Request/Response Models
class PresetResponse(BaseModel):
    """Preset information response"""
    id: str
    name: str
    category: str
    type: str
    description: str
    download_size: str
    files: List[Dict[str, Any]]
    use_case: str
    tags: List[str]
    installed: bool = False
    installation_status: Optional[str] = None


class PresetListResponse(BaseModel):
    """Response for preset list endpoint"""
    total: int
    categories: Dict[str, Any]
    presets: List[PresetResponse]


class PresetInstallRequest(BaseModel):
    """Request model for preset installation"""
    preset_id: str
    force_reinstall: bool = False


class PresetInstallResponse(BaseModel):
    """Response for preset installation"""
    preset_id: str
    status: str
    message: str
    download_id: Optional[str] = None


# Initialize router and dependencies
router = APIRouter()

download_manager = DownloadManager()
comfyui_client = ComfyUIClient(base_url=f"http://localhost:{settings.COMFYUI_PORT}")


async def get_presets_from_config() -> Dict:
    """Load presets from configuration file with caching"""
    import yaml

    # Check cache first
    cached = preset_cache.get_config()
    if cached:
        return cached

    config_path = Path(settings.PRESET_CONFIG_PATH)
    if not config_path.exists():
        raise HTTPException(status_code=404, detail="Preset configuration not found")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Cache the result
    preset_cache.set_config(config)
    return config


async def check_preset_installed(preset_id: str, preset_files: List[Dict], use_cache: bool = True) -> bool:
    """Check if all preset files are installed

    Args:
        preset_id: The preset ID
        preset_files: List of file dictionaries
        use_cache: Whether to use cached status (default True)
    """
    # Check cache first if enabled
    if use_cache:
        cached_status = preset_cache.get_installed_status()
        if preset_id in cached_status:
            return cached_status[preset_id]

    base_path = Path(settings.MODEL_BASE_PATH)

    for file_info in preset_files:
        file_path = base_path / file_info.get('path', '')
        if not file_path.exists():
            return False
    return True


async def batch_check_installed(config: Dict) -> Dict[str, bool]:
    """Check installation status for all presets and cache results"""
    base_path = Path(settings.MODEL_BASE_PATH)
    status_map = {}

    for preset_id, preset_data in config.get('presets', {}).items():
        all_installed = True
        for file_info in preset_data.get('files', []):
            file_path = base_path / file_info.get('path', '')
            if not file_path.exists():
                all_installed = False
                break
        status_map[preset_id] = all_installed

    # Cache the results
    preset_cache.set_installed_status(status_map)
    return status_map


@router.get("/", response_model=PresetListResponse)
async def list_presets(
    category: Optional[str] = None,
    type_filter: Optional[str] = None
) -> PresetListResponse:
    """
    List all available presets with optional filtering

    - **category**: Filter by category (Video Generation, Image Generation, Audio Generation)
    - **type_filter**: Filter by type (video, image, audio)
    """
    config = await get_presets_from_config()

    # Batch check all installation status (uses cache if available)
    installed_status = await batch_check_installed(config)

    presets_data = []
    for preset_id, preset_data in config.get('presets', {}).items():
        # Apply filters
        if category and preset_data.get('category') != category:
            continue
        if type_filter and preset_data.get('type') != type_filter:
            continue

        # Use pre-computed installation status
        is_installed = installed_status.get(preset_id, False)

        presets_data.append(PresetResponse(
            id=preset_id,
            name=preset_data.get('name', preset_id),
            category=preset_data.get('category', 'Unknown'),
            type=preset_data.get('type', 'unknown'),
            description=preset_data.get('description', ''),
            download_size=preset_data.get('download_size', 'Unknown'),
            files=preset_data.get('files', []),
            use_case=preset_data.get('use_case', ''),
            tags=preset_data.get('tags', []),
            installed=is_installed,
            installation_status='installed' if is_installed else 'not_installed'
        ))

    return PresetListResponse(
        total=len(presets_data),
        categories=config.get('categories', {}),
        presets=presets_data
    )


@router.get("/{preset_id}", response_model=PresetResponse)
async def get_preset(preset_id: str) -> PresetResponse:
    """Get detailed information about a specific preset"""
    config = await get_presets_from_config()

    if preset_id not in config.get('presets', {}):
        raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")

    preset_data = config['presets'][preset_id]
    is_installed = await check_preset_installed(
        preset_id,
        preset_data.get('files', [])
    )

    return PresetResponse(
        id=preset_id,
        name=preset_data.get('name', preset_id),
        category=preset_data.get('category', 'Unknown'),
        type=preset_data.get('type', 'unknown'),
        description=preset_data.get('description', ''),
        download_size=preset_data.get('download_size', 'Unknown'),
        files=preset_data.get('files', []),
        use_case=preset_data.get('use_case', ''),
        tags=preset_data.get('tags', []),
        installed=is_installed,
        installation_status='installed' if is_installed else 'not_installed'
    )


@router.post("/{preset_id}/download", response_model=PresetInstallResponse)
async def download_preset(
    preset_id: str,
    background_tasks: BackgroundTasks,
    force_reinstall: bool = False
) -> PresetInstallResponse:
    """
    Start download for a specific preset

    - **preset_id**: The ID of the preset to download
    - **force_reinstall**: Force reinstallation even if files exist
    """
    config = await get_presets_from_config()

    if preset_id not in config.get('presets', {}):
        raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")

    preset_data = config['presets'][preset_id]

    # Check if already installed
    if not force_reinstall:
        is_installed = await check_preset_installed(
            preset_id,
            preset_data.get('files', [])
        )
        if is_installed:
            return PresetInstallResponse(
                preset_id=preset_id,
                status="already_installed",
                message="Preset is already installed"
            )

    # Start background download
    download_id = await download_manager.start_download(
        preset_id=preset_id,
        files=preset_data.get('files', []),
        force=force_reinstall
    )

    return PresetInstallResponse(
        preset_id=preset_id,
        status="downloading",
        message="Download started in background",
        download_id=download_id
    )


@router.get("/queue/status")
async def get_queue_status():
    """Get current download queue status"""
    return download_manager.get_queue_status()


@router.get("/{preset_id}/status")
async def get_preset_status(preset_id: str):
    """Get installation status for a specific preset"""
    config = await get_presets_from_config()

    if preset_id not in config.get('presets', {}):
        raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")

    preset_data = config['presets'][preset_id]
    is_installed = await check_preset_installed(
        preset_id,
        preset_data.get('files', [])
    )

    # Get download status if active
    download_status = await download_manager.get_download_status(preset_id)

    return {
        "preset_id": preset_id,
        "installed": is_installed,
        "download_status": download_status,
        "files": preset_data.get('files', [])
    }


@router.delete("/{preset_id}")
async def delete_preset(preset_id: str):
    """Delete installed files for a preset"""
    config = await get_presets_from_config()

    if preset_id not in config.get('presets', {}):
        raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")

    preset_data = config['presets'][preset_id]
    base_path = Path(settings.MODEL_BASE_PATH)

    deleted_files = []
    errors = []

    for file_info in preset_data.get('files', []):
        file_path = base_path / file_info.get('path', '')
        try:
            if file_path.exists():
                file_path.unlink()
                deleted_files.append(str(file_path))
        except Exception as e:
            errors.append(f"{file_path}: {str(e)}")

    # Invalidate installation status cache since files changed
    preset_cache.invalidate_installed()

    return {
        "preset_id": preset_id,
        "deleted_files": deleted_files,
        "errors": errors,
        "status": "completed" if not errors else "completed_with_errors"
    }


@router.get("/categories/list")
async def list_categories():
    """List all available preset categories"""
    config = await get_presets_from_config()
    return config.get('categories', {})


@router.post("/refresh")
async def refresh_presets():
    """
    Fetch latest presets.yaml from GitHub

    Smart refresh: updates preset definitions without interrupting active downloads
    """
    import yaml
    import shutil

    github_url = "https://raw.githubusercontent.com/ZeroClue/ComfyUI-Docker/main/config/presets.yaml"
    local_path = Path(settings.PRESET_CONFIG_PATH)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(github_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"GitHub returned {response.status}"
                    )

                content = await response.text()

        # Validate YAML before saving
        try:
            new_config = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise HTTPException(status_code=400, detail=f"Invalid YAML: {str(e)}")

        # Backup existing config
        if local_path.exists():
            backup_path = local_path.with_suffix('.yaml.bak')
            shutil.copy(local_path, backup_path)

        # Write new config
        local_path.parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, 'w') as f:
            f.write(content)

        return {
            "status": "success",
            "message": "Presets refreshed successfully",
            "total_presets": len(new_config.get('presets', {})),
            "version": new_config.get('metadata', {}).get('version', 'unknown')
        }

    except aiohttp.ClientError as e:
        raise HTTPException(status_code=503, detail=f"Failed to fetch from GitHub: {str(e)}")


@router.post("/{preset_id}/install")
async def install_preset(preset_id: str, force: bool = False):
    """
    Queue preset for installation

    - **preset_id**: The ID of the preset to install
    - **force**: Force re-download even if files exist
    """
    config = await get_presets_from_config()

    if preset_id not in config.get('presets', {}):
        raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")

    preset_data = config['presets'][preset_id]

    # Check for HF token if preset has huggingface URLs
    has_hf_urls = any(
        "huggingface.co" in f.get("url", "")
        for f in preset_data.get("files", [])
    )
    if has_hf_urls and not persistence.settings_manager.has_hf_token():
        return {
            "preset_id": preset_id,
            "status": "token_required",
            "message": "This model requires a HuggingFace token"
        }

    download_id = await download_manager.start_download(
        preset_id=preset_id,
        files=preset_data.get('files', []),
        force=force
    )

    return {
        "preset_id": preset_id,
        "status": "queued",
        "download_id": download_id
    }


@router.post("/{preset_id}/pause")
async def pause_preset_download(preset_id: str):
    """Pause active download"""
    success = await download_manager.pause_download(preset_id)
    if not success:
        raise HTTPException(status_code=404, detail="No active download for this preset")
    return {"preset_id": preset_id, "status": "paused"}


@router.post("/{preset_id}/resume")
async def resume_preset_download(preset_id: str):
    """Resume paused download"""
    success = await download_manager.resume_download(preset_id)
    if not success:
        raise HTTPException(status_code=404, detail="No paused download for this preset")
    return {"preset_id": preset_id, "status": "resumed"}


@router.post("/{preset_id}/cancel")
async def cancel_preset_download(preset_id: str, keep_partial: bool = True):
    """Cancel download"""
    success = await download_manager.cancel_download(preset_id, keep_partial)
    if not success:
        raise HTTPException(status_code=404, detail="No download to cancel")
    return {"preset_id": preset_id, "status": "cancelled"}


@router.post("/{preset_id}/retry")
async def retry_preset_download(preset_id: str):
    """Retry failed download"""
    config = await get_presets_from_config()

    if preset_id not in config.get('presets', {}):
        raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")

    preset_data = config['presets'][preset_id]

    # Force re-download
    download_id = await download_manager.start_download(
        preset_id=preset_id,
        files=preset_data.get('files', []),
        force=True
    )

    return {
        "preset_id": preset_id,
        "status": "retrying",
        "download_id": download_id
    }


@router.delete("/{preset_id}/files")
async def uninstall_preset(preset_id: str):
    """Delete all files for an installed preset"""
    config = await get_presets_from_config()

    if preset_id not in config.get('presets', {}):
        raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")

    preset_data = config['presets'][preset_id]
    files = preset_data.get('files', [])
    base_path = Path(settings.MODEL_BASE_PATH)

    deleted_files = []
    errors = []

    for file_info in files:
        file_path = file_info.get('path', '')
        if not file_path:
            continue

        full_path = base_path / file_path
        if full_path.exists():
            try:
                full_path.unlink()
                deleted_files.append(file_path)
            except Exception as e:
                errors.append({"file": file_path, "error": str(e)})

    # Invalidate installation status cache since files changed
    preset_cache.invalidate_installed()

    return {
        "preset_id": preset_id,
        "status": "uninstalled",
        "deleted_files": deleted_files,
        "deleted_count": len(deleted_files),
        "errors": errors
    }
