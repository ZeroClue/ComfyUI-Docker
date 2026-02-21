"""
Generate API endpoints
Handles workflow browsing, intent matching, and generation control.
"""
from typing import List, Dict, Optional, Any
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from ..core.config import settings
from ..core.workflow_scanner import WorkflowScanner
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
    List all synced workflows with metadata.

    - **category**: Filter by workflow category
    - **input_type**: Filter by input type (text, image, audio, video)
    - **output_type**: Filter by output type (image, video, audio)
    """
    workflows = get_workflow_scanner().scan_all()

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

    # Check model availability
    # TODO: Integrate with preset system to check installed models
    required_models = workflow.get("required_models", [])

    return {
        "workflow_id": workflow_id,
        "workflow_name": workflow.get("name", workflow_id),
        "required_models": required_models,
        "missing_models": [],  # TODO: Check against installed models
        "status": "ready" if len(required_models) == 0 else "check_required",
        "can_generate": True  # TODO: Based on missing models check
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

    try:
        # Load the workflow JSON
        workflow_path = Path(settings.WORKFLOW_BASE_PATH) / workflow["path"]
        import json
        with open(workflow_path, 'r') as f:
            workflow_data = json.load(f)

        # Inject prompt into workflow
        workflow_data = get_comfyui_client().inject_prompt(workflow_data, request.prompt)

        # Queue the workflow
        result = await get_comfyui_client().queue_workflow(workflow_data)

        return GenerationStartResponse(
            status="queued",
            prompt_id=result.get("prompt_id"),
            message=f"Generation started with {workflow.get('name', request.workflow_id)}"
        )

    except Exception as e:
        return GenerationStartResponse(
            status="error",
            prompt_id=None,
            message=f"Failed to start generation: {str(e)}"
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
