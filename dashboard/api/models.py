"""
Model management API endpoints
Handles model listing, validation, and disk usage information
"""

from typing import List, Dict, Optional
from pathlib import Path
import shutil

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..core.config import settings
from ..core.comfyui_client import ComfyUIClient


# Request/Response Models
class ModelFile(BaseModel):
    """Individual model file information"""
    path: str
    name: str
    size: float
    size_human: str
    type: str
    modified: str


class ModelsResponse(BaseModel):
    """Response for models list endpoint"""
    total_models: int
    total_size: float
    total_size_human: str
    by_type: Dict[str, List[ModelFile]]


class ModelValidationResponse(BaseModel):
    """Response for model validation endpoint"""
    valid: bool
    missing_files: List[str]
    total_size: float
    file_count: int


class DiskUsageResponse(BaseModel):
    """Response for disk usage endpoint"""
    total: float
    used: float
    available: float
    usage_percent: float
    path: str


# Initialize router and dependencies
router = APIRouter()
comfyui_client = ComfyUIClient(base_url=f"http://localhost:{settings.COMFYUI_PORT}")


def get_file_size_human(bytes_size: float) -> str:
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


def scan_model_directory(base_path: Path) -> Dict[str, List[ModelFile]]:
    """Scan model directory and return organized file information"""
    model_types = {
        'checkpoints': ['.safetensors', '.ckpt', '.pt', '.pth'],
        'text_encoders': ['.safetensors', '.ckpt', '.pt', '.pth', '.bin'],
        'vae': ['.safetensors', '.ckpt', '.pt', '.pth'],
        'clip_vision': ['.safetensors', '.pt', '.pth'],
        'loras': ['.safetensors', '.ckpt', '.pt', '.pth'],
        'upscale_models': ['.safetensors', '.pt', '.pth', '.onnx'],
        'audio_encoders': ['.safetensors', '.pt', '.pth', '.bin'],
        'controlnet': ['.safetensors', '.ckpt', '.pt', '.pth'],
        'ipadapters': ['.safetensors', '.pt', '.pth'],
    }

    models_by_type = {type_name: [] for type_name in model_types.keys()}

    for type_name, extensions in model_types.items():
        type_path = base_path / type_name
        if not type_path.exists():
            continue

        for file_path in type_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in extensions:
                try:
                    stat = file_path.stat()
                    size_bytes = stat.st_size

                    models_by_type[type_name].append(ModelFile(
                        path=str(file_path.relative_to(base_path)),
                        name=file_path.name,
                        size=size_bytes,
                        size_human=get_file_size_human(size_bytes),
                        type=type_name,
                        modified=stat.st_mtime
                    ))
                except Exception:
                    continue

    return models_by_type


@router.get("/", response_model=ModelsResponse)
async def list_models(
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    status: Optional[str] = Query(None, description="Filter by status (installed, available)")
) -> ModelsResponse:
    """
    List all installed models with size information

    - **model_type**: Optional filter for specific model type (checkpoints, vae, etc.)
    - **status**: Optional filter by installation status
    """
    base_path = Path(settings.MODEL_BASE_PATH)

    if not base_path.exists():
        raise HTTPException(status_code=404, detail="Model directory not found")

    models_by_type = scan_model_directory(base_path)

    # Apply type filter if specified
    if model_type and model_type in models_by_type:
        models_by_type = {model_type: models_by_type[model_type]}

    # Calculate totals
    total_models = sum(len(files) for files in models_by_type.values())
    total_size = sum(
        file.size
        for files in models_by_type.values()
        for file in files
    )

    return ModelsResponse(
        total_models=total_models,
        total_size=total_size,
        total_size_human=get_file_size_human(total_size),
        by_type=models_by_type
    )


@router.get("/presets")
async def list_model_presets(
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by installation status")
):
    """
    List all presets with their installation status.
    This is the main endpoint for the Models page UI.
    """
    import yaml

    config_path = Path(settings.PRESET_CONFIG_PATH)
    base_path = Path(settings.MODEL_BASE_PATH)

    models = []

    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        for preset_id, preset_data in config.get('presets', {}).items():
            # Apply category filter
            if category and preset_data.get('type') != category:
                continue

            # Check installation status
            preset_files = preset_data.get('files', [])
            installed_count = 0
            for file_info in preset_files:
                file_path = base_path / file_info.get('path', '')
                if file_path.exists():
                    installed_count += 1

            if installed_count == len(preset_files) and len(preset_files) > 0:
                install_status = 'installed'
            elif installed_count > 0:
                install_status = 'partial'
            else:
                install_status = 'available'

            # Apply status filter
            if status and install_status != status:
                continue

            # Map category to type
            category_map = {
                'Video Generation': 'video',
                'Image Generation': 'image',
                'Audio Generation': 'audio'
            }

            models.append({
                'id': preset_id,
                'name': preset_data.get('name', preset_id),
                'description': preset_data.get('description', ''),
                'size': preset_data.get('download_size', 'Unknown'),
                'category': preset_data.get('category', 'Unknown'),
                'type': category_map.get(preset_data.get('category'), 'unknown'),
                'status': install_status,
                'progress': 100 if install_status == 'installed' else 0,
                'tags': preset_data.get('tags', [])
            })

    return {'models': models, 'total': len(models)}


@router.get("/validate", response_model=ModelValidationResponse)
async def validate_models(
    preset_id: Optional[str] = Query(None, description="Validate specific preset")
) -> ModelValidationResponse:
    """
    Validate model files and check for missing or corrupted files

    - **preset_id**: Optional preset ID to validate specific preset models
    """
    import yaml

    base_path = Path(settings.MODEL_BASE_PATH)
    config_path = Path(settings.PRESET_CONFIG_PATH)

    if preset_id:
        # Validate specific preset
        if not config_path.exists():
            raise HTTPException(status_code=404, detail="Preset configuration not found")

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        if preset_id not in config.get('presets', {}):
            raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")

        files_to_check = config['presets'][preset_id].get('files', [])
    else:
        # Validate all installed models
        models_by_type = scan_model_directory(base_path)
        files_to_check = [
            {'path': file.path}
            for files in models_by_type.values()
            for file in files
        ]

    missing_files = []
    total_size = 0

    for file_info in files_to_check:
        file_path = base_path / file_info.get('path', '')
        if not file_path.exists():
            missing_files.append(file_info.get('path', ''))
        else:
            total_size += file_path.stat().st_size

    return ModelValidationResponse(
        valid=len(missing_files) == 0,
        missing_files=missing_files,
        total_size=total_size,
        file_count=len(files_to_check) - len(missing_files)
    )


@router.get("/disk-usage", response_model=DiskUsageResponse)
async def get_disk_usage(
    path: Optional[str] = Query(None, description="Path to check (default: model base path)")
) -> DiskUsageResponse:
    """
    Get disk usage information for model storage

    - **path**: Optional path to check (defaults to model base path)
    """
    check_path = Path(path) if path else Path(settings.MODEL_BASE_PATH)

    if not check_path.exists():
        raise HTTPException(status_code=404, detail="Path not found")

    usage = shutil.disk_usage(check_path)

    return DiskUsageResponse(
        total=usage.total,
        used=usage.used,
        available=usage.free,
        usage_percent=(usage.used / usage.total) * 100,
        path=str(check_path)
    )


@router.get("/types")
async def list_model_types():
    """List available model types/directories"""
    base_path = Path(settings.MODEL_BASE_PATH)

    if not base_path.exists():
        raise HTTPException(status_code=404, detail="Model directory not found")

    types = []
    for item in base_path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            types.append({
                "name": item.name,
                "path": str(item.relative_to(base_path)),
                "model_count": len(list(item.glob('*')))
            })

    return {"types": types}


@router.delete("/cleanup")
async def cleanup_models(
    dry_run: bool = Query(True, description="Preview changes without deleting")
) -> Dict:
    """
    Remove unused or duplicate model files

    - **dry_run**: Preview changes without actually deleting files
    """
    # This would implement logic to find unused/duplicate models
    # For now, return a placeholder response
    return {
        "status": "not_implemented",
        "message": "Model cleanup feature not yet implemented",
        "dry_run": dry_run
    }
