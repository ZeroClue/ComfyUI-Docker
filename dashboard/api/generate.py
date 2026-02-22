"""
Generate API endpoints
Handles workflow browsing, intent matching, and generation control.
"""
from typing import List, Dict, Optional, Any
from pathlib import Path
import yaml
import json

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from ..core.config import settings
from ..core.workflow_scanner import WorkflowScanner


# Preset matching utilities
def load_preset_registry() -> Dict[str, Any]:
    """Load preset registry from file."""
    registry_path = Path("/workspace/data/registry.json")
    if registry_path.exists():
        with open(registry_path) as f:
            return json.load(f)

    # Fallback to presets.yaml
    presets_path = Path(settings.PRESET_CONFIG_PATH)
    if presets_path.exists():
        with open(presets_path) as f:
            return {"presets": yaml.safe_load(f), "workflows": {}}

    return {"presets": {}, "workflows": {}}


def find_preset_for_model(model_filename: str, registry: Dict) -> Optional[Dict[str, Any]]:
    """Find a preset that contains the given model filename."""
    presets = registry.get("presets", {})

    for preset_id, preset_data in presets.items():
        files = preset_data.get("files", [])
        for file_info in files:
            file_path = file_info.get("path", "")
            if file_path.endswith(model_filename):
                return {
                    "id": preset_id,
                    "name": preset_data.get("name", preset_id),
                    "download_size": preset_data.get("download_size", "Unknown"),
                }

    return None


GITHUB_ISSUE_URL = "https://github.com/ZeroClue/comfyui-presets/issues/new"


def generate_request_preset_url(model_name: str, model_type: str, workflow_id: str) -> str:
    """Generate GitHub issue URL for requesting a new preset."""
    from urllib.parse import urlencode

    title = f"Add preset for {model_name}"
    body = f"Model: {model_name}\nType: {model_type}\nWorkflow: {workflow_id}"

    params = {
        "title": title,
        "body": body
    }

    return f"{GITHUB_ISSUE_URL}?{urlencode(params)}"


def enrich_model_with_actions(model: Dict, workflow_id: str, registry: Dict) -> Dict:
    """Add preset info and action URLs to a model entry."""
    result = model.copy()

    if model["installed"]:
        result["preset"] = None
        result["actions"] = None
        return result

    # Check for preset
    preset = find_preset_for_model(model["name"], registry)
    result["preset"] = preset

    # Generate actions
    actions = {
        "install": f"/api/presets/{preset['id']}/install" if preset else None,
        "manual_path": f"/workspace/models/{model['type']}/",
        "request_preset_url": generate_request_preset_url(
            model["name"], model["type"], workflow_id
        ),
    }
    result["actions"] = actions

    return result


from ..core.intent_matcher import IntentMatcher
from ..core.comfyui_client import ComfyUIClient


# Request/Response Models
class IntentRequest(BaseModel):
    """Request for intent matching."""
    text: str = Field(..., description="User's intent text")


class IntentResponse(BaseModel):
    """Response for intent matching."""
    matched: bool
    suggested_type: Optional[str] = None
    suggested_input_types: List[str] = []
    suggested_output_types: List[str] = []
    suggestions: List[str] = []
    matched_keyword: Optional[str] = None

    class Config:
        extra = "ignore"  # Ignore any extra fields from IntentMatcher


class WorkflowSyncedResponse(BaseModel):
    """Response for synced workflows list."""
    workflows: List[Dict[str, Any]]
    categories: Dict[str, int]
    total: int


class GenerationStartRequest(BaseModel):
    """Request to start a generation."""
    workflow_id: str = Field(..., description="Workflow ID to execute")
    prompt: str = Field(..., description="Main prompt text")
    negative_prompt: Optional[str] = Field("", description="Negative prompt")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Generation settings")
    input_image: Optional[str] = Field(None, description="Base64 input image for I2V/I2I")


class GenerationStartResponse(BaseModel):
    """Response for generation start."""
    status: str
    prompt_id: Optional[str] = None
    message: str


# Initialize router and services
router = APIRouter()
intent_matcher = IntentMatcher()

# Lazy initialization to avoid issues with settings not being loaded at import time
_workflow_scanner = None
_comfyui_client = None


def get_workflow_scanner():
    global _workflow_scanner
    if _workflow_scanner is None:
        _workflow_scanner = WorkflowScanner(Path(settings.WORKFLOW_BASE_PATH))
    return _workflow_scanner


def get_comfyui_client():
    global _comfyui_client
    if _comfyui_client is None:
        _comfyui_client = ComfyUIClient(base_url=f"http://localhost:{settings.COMFYUI_PORT}")
    return _comfyui_client


@router.get("/workflows/synced", response_model=WorkflowSyncedResponse)
async def get_synced_workflows(
    category: Optional[str] = Query(None, description="Filter by category"),
    input_type: Optional[str] = Query(None, description="Filter by input type"),
    output_type: Optional[str] = Query(None, description="Filter by output type"),
) -> WorkflowSyncedResponse:
    """
    List all synced workflows with metadata and model availability.

    - **category**: Filter by workflow category
    - **input_type**: Filter by input type (text, image, audio, video)
    - **output_type**: Filter by output type (image, video, audio)
    """
    workflows = get_workflow_scanner().scan_all()

    # Load preset registry for matching
    registry = load_preset_registry()

    # Enrich workflows with model actions
    for workflow in workflows:
        if "models" in workflow:
            workflow["models"] = [
                enrich_model_with_actions(model, workflow["id"], registry)
                for model in workflow["models"]
            ]

    # Apply filters
    if category:
        workflows = [w for w in workflows if w.get("category") == category]
    if input_type:
        workflows = [w for w in workflows if input_type in w.get("input_types", [])]
    if output_type:
        workflows = [w for w in workflows if output_type in w.get("output_types", [])]

    # Count by category
    categories = {}
    for w in workflows:
        cat = w.get("category", "general")
        categories[cat] = categories.get(cat, 0) + 1

    return WorkflowSyncedResponse(
        workflows=workflows,
        categories=categories,
        total=len(workflows)
    )


@router.get("/workflows/{workflow_id}/compatibility")
async def get_workflow_compatibility(workflow_id: str) -> Dict[str, Any]:
    """
    Check model compatibility for a workflow.

    Returns which required models are installed and which are missing.
    """
    workflows = get_workflow_scanner().scan_all()

    workflow = next((w for w in workflows if w["id"] == workflow_id), None)
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")

    # Get model availability from scanner (already includes installed status)
    models = workflow.get("models", [])
    missing_models = [m["name"] for m in models if not m["installed"]]
    installed_count = sum(1 for m in models if m["installed"])
    total_count = len(models)

    # Determine status
    if total_count == 0:
        status = "ready"
    elif len(missing_models) == 0:
        status = "ready"
    else:
        status = "check_required"

    return {
        "workflow_id": workflow_id,
        "workflow_name": workflow.get("name", workflow_id),
        "required_models": workflow.get("required_models", []),
        "missing_models": missing_models,
        "model_status": {
            "total": total_count,
            "installed": installed_count,
            "missing": len(missing_models)
        },
        "status": status,
        "can_generate": len(missing_models) == 0
    }


@router.post("/intent", response_model=IntentResponse)
async def match_intent(request: IntentRequest) -> IntentResponse:
    """
    Match user intent to workflow suggestions.

    Uses pattern matching to suggest appropriate workflow types.
    """
    result = intent_matcher.match(request.text)
    return IntentResponse(**result)


@router.get("/quick-actions")
async def get_quick_actions() -> List[Dict[str, str]]:
    """Get quick action buttons for the intent bar."""
    return intent_matcher.get_quick_actions()


@router.post("/start", response_model=GenerationStartResponse)
async def start_generation(
    request: GenerationStartRequest,
    background_tasks: BackgroundTasks
) -> GenerationStartResponse:
    """
    Start a generation with the selected workflow.

    - **workflow_id**: ID of the workflow to execute
    - **prompt**: Main generation prompt
    - **negative_prompt**: Negative prompt (optional)
    - **settings**: Generation settings (steps, cfg, seed, etc.)
    - **input_image**: Base64 encoded input image for I2V/I2I
    """
    # Find the workflow
    workflows = get_workflow_scanner().scan_all()
    workflow = next((w for w in workflows if w["id"] == request.workflow_id), None)

    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow {request.workflow_id} not found")

    # Load the workflow JSON
    workflow_path = Path(settings.WORKFLOW_BASE_PATH) / workflow["path"]
    with open(workflow_path, 'r') as f:
        workflow_data = json.load(f)

    # Check workflow format and handle accordingly
    is_ui_format = "nodes" in workflow_data and isinstance(workflow_data["nodes"], list)
    has_subgraphs = "definitions" in workflow_data and workflow_data.get("definitions", {}).get("subgraphs")

    if is_ui_format and has_subgraphs:
        # UI format with subgraphs cannot be directly executed via API
        raise HTTPException(
            status_code=400,
            detail={
                "error": "workflow_format_not_supported",
                "message": "This workflow uses UI format with composite nodes (subgraphs).",
                "solution": "To execute this workflow:\n"
                           "1. Open the workflow in ComfyUI\n"
                           "2. Enable Dev Mode in Settings\n"
                           "3. Click 'Export (API Format)' from the menu\n"
                           "4. Save the exported workflow\n\n"
                           "API format workflows can be executed directly from the dashboard."
            }
        )

    if is_ui_format:
        # UI format without subgraphs still needs conversion
        # For now, require API format workflows
        raise HTTPException(
            status_code=400,
            detail={
                "error": "workflow_format_not_supported",
                "message": "This workflow is in UI format.",
                "solution": "To execute this workflow:\n"
                           "1. Open the workflow in ComfyUI\n"
                           "2. Enable Dev Mode in Settings\n"
                           "3. Click 'Export (API Format)' from the menu\n"
                           "4. Save the exported workflow\n\n"
                           "API format workflows can be executed directly from the dashboard."
            }
        )

    # Already in API format - strip _meta keys before sending to ComfyUI
    api_workflow = {k: v for k, v in workflow_data.items() if not k.startswith("_")}

    # Inject prompt into workflow
    api_workflow = get_comfyui_client().inject_prompt(api_workflow, request.prompt)

    # Queue the workflow
    try:
        result = await get_comfyui_client().queue_workflow(api_workflow)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue workflow: {str(e)}")

    return GenerationStartResponse(
        status="queued",
        prompt_id=result.get("prompt_id"),
        message=f"Generation started with {workflow.get('name', request.workflow_id)}"
    )


@router.post("/{prompt_id}/pause")
async def pause_generation(prompt_id: str) -> Dict[str, str]:
    """Pause an active generation."""
    # TODO: Implement pause functionality
    return {"status": "paused", "prompt_id": prompt_id, "message": "Generation paused"}


@router.post("/{prompt_id}/cancel")
async def cancel_generation(prompt_id: str) -> Dict[str, str]:
    """Cancel a generation."""
    try:
        await get_comfyui_client().interrupt_execution()
        return {"status": "cancelled", "prompt_id": prompt_id, "message": "Generation cancelled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel: {str(e)}")


__all__ = ["router"]
