"""
Workflow Registry API endpoints
Handles workflow library browsing, sync, and requirement checking.
"""
from typing import List, Dict, Optional, Any
from pathlib import Path
import json
import aiohttp
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.config import settings


router = APIRouter()

# Remote registry URL
REMOTE_REGISTRY_URL = "https://raw.githubusercontent.com/ZeroClue/comfyui-presets/main/registry.json"


class WorkflowPresetStatus(BaseModel):
    """Status of a required preset for a workflow."""
    id: str
    name: str
    installed: bool
    download_size: Optional[str] = None


class WorkflowRegistryItem(BaseModel):
    """A workflow from the registry with local status."""
    id: str
    name: str
    description: str
    category: str
    type: str
    input_types: List[str]
    output_types: List[str]
    tags: List[str]
    author: str
    version: str
    ready: bool
    required_presets: List[WorkflowPresetStatus]


class WorkflowRegistryResponse(BaseModel):
    """Response for workflow registry list."""
    workflows: List[WorkflowRegistryItem]
    categories: Dict[str, int]
    last_synced: Optional[str] = None


class WorkflowRequirementsResponse(BaseModel):
    """Response for workflow requirements check."""
    workflow_id: str
    ready: bool
    missing_presets: List[Dict[str, Any]]
    total_download_size_gb: float
    disk_check: Dict[str, Any]


def load_registry() -> Dict[str, Any]:
    """Load the full registry from local file."""
    registry_path = Path("/workspace/data/registry.json")
    if registry_path.exists():
        with open(registry_path) as f:
            return json.load(f)
    return {"presets": {}, "workflows": {}}


def get_installed_presets() -> set:
    """Get set of installed preset IDs."""
    installed = set()
    models_path = Path(settings.MODEL_BASE_PATH)
    registry = load_registry()

    for preset_id, preset_data in registry.get("presets", {}).items():
        files = preset_data.get("files", [])
        # If no files defined, check if preset has a path (new format)
        if not files:
            preset_path = preset_data.get("path", "")
            if preset_path:
                # For new format, skip file check - use different logic
                continue
        all_installed = True
        for file_info in files:
            file_path = file_info.get("path", "")
            full_path = models_path / file_path
            if not full_path.exists():
                all_installed = False
                break
        if all_installed and files:
            installed.add(preset_id)

    return installed


def parse_size_to_bytes(size_str: str) -> int:
    """Parse size string like '14.5GB' or '450MB' to bytes."""
    size_str = size_str.upper().strip()
    multipliers = {"GB": 1024**3, "MB": 1024**2, "KB": 1024, "B": 1}

    for suffix, mult in multipliers.items():
        if size_str.endswith(suffix):
            try:
                return int(float(size_str[:-len(suffix)]) * mult)
            except ValueError:
                return 0
    return 0


def get_workspace_disk_info() -> Dict[str, float]:
    """Get workspace disk usage and limit in GB."""
    import subprocess
    import os

    # Get actual usage via du
    try:
        result = subprocess.run(
            ["du", "-sb", "/workspace"],
            capture_output=True,
            text=True,
            timeout=30
        )
        used_bytes = int(result.stdout.split()[0])
    except Exception:
        used_bytes = 0

    # Get volume limit from env (RunPod sets this)
    volume_gb = int(os.environ.get("RUNPOD_VOLUME_GB", 100))
    limit_bytes = volume_gb * 1024**3

    return {
        "used_gb": used_bytes / (1024**3),
        "limit_gb": volume_gb,
        "available_gb": (limit_bytes - used_bytes) / (1024**3)
    }


@router.get("", response_model=WorkflowRegistryResponse)
async def get_workflow_registry() -> WorkflowRegistryResponse:
    """List all workflows from registry with local availability status."""
    registry = load_registry()
    workflows_data = registry.get("workflows", {})
    installed_presets = get_installed_presets()

    workflows = []
    categories = {}

    for wf_id, wf_data in workflows_data.items():
        required = wf_data.get("required_presets", [])
        preset_statuses = []

        for preset_id in required:
            preset_info = registry.get("presets", {}).get(preset_id, {})
            preset_statuses.append(WorkflowPresetStatus(
                id=preset_id,
                name=preset_info.get("name", preset_id),
                installed=preset_id in installed_presets,
                download_size=preset_info.get("download_size")
            ))

        ready = all(ps.installed for ps in preset_statuses)

        workflows.append(WorkflowRegistryItem(
            id=wf_id,
            name=wf_data.get("name", wf_id),
            description=wf_data.get("description", ""),
            category=wf_data.get("category", "General"),
            type=wf_data.get("type", "image"),
            input_types=wf_data.get("input_types", []),
            output_types=wf_data.get("output_types", []),
            tags=wf_data.get("tags", []),
            author=wf_data.get("author", "Unknown"),
            version=wf_data.get("version", "1.0.0"),
            ready=ready,
            required_presets=preset_statuses
        ))

        cat = wf_data.get("category", "General")
        categories[cat] = categories.get(cat, 0) + 1

    registry_path = Path("/workspace/data/registry.json")
    last_synced = None
    if registry_path.exists():
        mtime = registry_path.stat().st_mtime
        last_synced = datetime.fromtimestamp(mtime).isoformat()

    return WorkflowRegistryResponse(
        workflows=workflows,
        categories=categories,
        last_synced=last_synced
    )


@router.post("/sync")
async def sync_workflow_registry() -> Dict[str, Any]:
    """Sync workflow registry from remote repository."""
    registry_path = Path("/workspace/data/registry.json")
    registry_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(REMOTE_REGISTRY_URL) as response:
                if response.status != 200:
                    raise HTTPException(502, f"Failed to fetch registry: HTTP {response.status}")

                text = await response.text()
                registry = json.loads(text)

        with open(registry_path, "w") as f:
            json.dump(registry, f, indent=2)

        return {
            "synced": True,
            "workflows_count": len(registry.get("workflows", {})),
            "presets_count": len(registry.get("presets", {})),
            "version": registry.get("version", "unknown")
        }

    except aiohttp.ClientError as e:
        raise HTTPException(502, f"Network error: {str(e)}")
    except json.JSONDecodeError as e:
        raise HTTPException(502, f"Invalid JSON: {str(e)}")


@router.post("/{workflow_id}/check-requirements", response_model=WorkflowRequirementsResponse)
async def check_workflow_requirements(workflow_id: str) -> WorkflowRequirementsResponse:
    """Check workflow requirements including disk space."""
    registry = load_registry()
    installed_presets = get_installed_presets()

    wf_data = registry.get("workflows", {}).get(workflow_id)
    if not wf_data:
        raise HTTPException(404, f"Workflow {workflow_id} not found in registry")

    required = wf_data.get("required_presets", [])
    missing = []
    total_size_bytes = 0

    for preset_id in required:
        if preset_id not in installed_presets:
            preset_info = registry.get("presets", {}).get(preset_id, {})
            size_str = preset_info.get("download_size", "0GB")
            size_bytes = parse_size_to_bytes(size_str)
            total_size_bytes += size_bytes

            missing.append({
                "id": preset_id,
                "name": preset_info.get("name", preset_id),
                "download_size": size_str
            })

    disk_info = get_workspace_disk_info()
    safety_margin_bytes = 5 * 1024**3  # 5GB buffer
    required_bytes = total_size_bytes + safety_margin_bytes
    available_bytes = disk_info["available_gb"] * 1024**3

    return WorkflowRequirementsResponse(
        workflow_id=workflow_id,
        ready=len(missing) == 0,
        missing_presets=missing,
        total_download_size_gb=total_size_bytes / (1024**3),
        disk_check={
            "can_proceed": available_bytes >= required_bytes,
            "required_gb": total_size_bytes / (1024**3),
            "available_gb": disk_info["available_gb"],
            "safety_margin_gb": 5.0,
            "shortfall_gb": max(0, (required_bytes - available_bytes) / (1024**3))
        }
    )


__all__ = ["router"]
