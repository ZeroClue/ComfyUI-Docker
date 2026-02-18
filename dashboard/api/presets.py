"""
Preset management API endpoints
Handles preset listing, installation, and status checking
"""

import asyncio
import aiohttp
from typing import List, Dict, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from ..core.config import settings
from ..core.downloader import DownloadManager
from ..core.comfyui_client import ComfyUIClient


# Request/Response Models
class PresetResponse(BaseModel):
    """Preset information response"""
    id: str
    name: str
    category: str
    type: str
    description: str
    download_size: str
    files: List[Dict[str, str]]
    use_case: str
    tags: List[str]
    installed: bool = False
    installation_status: Optional[str] = None


class PresetListResponse(BaseModel):
    """Response for preset list endpoint"""
    total: int
    categories: Dict[str, str]
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
    """Load presets from configuration file"""
    import yaml

    config_path = Path(settings.PRESET_CONFIG_PATH)
    if not config_path.exists():
        raise HTTPException(status_code=404, detail="Preset configuration not found")

    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


async def check_preset_installed(preset_id: str, preset_files: List[Dict]) -> bool:
    """Check if all preset files are installed"""
    base_path = Path(settings.MODEL_BASE_PATH)

    for file_info in preset_files:
        file_path = base_path / file_info.get('path', '')
        if not file_path.exists():
            return False
    return True


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

    presets_data = []
    for preset_id, preset_data in config.get('presets', {}).items():
        # Apply filters
        if category and preset_data.get('category') != category:
            continue
        if type_filter and preset_data.get('type') != type_filter:
            continue

        # Check installation status
        is_installed = await check_preset_installed(
            preset_id,
            preset_data.get('files', [])
        )

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


@router.get("/queue/status")
async def get_queue_status():
    """Get current download queue status"""
    return download_manager.get_queue_status()
