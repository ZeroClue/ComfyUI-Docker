"""
Workflow management API endpoints
Handles workflow listing, execution, and ComfyUI integration
"""

from typing import List, Dict, Optional
from pathlib import Path
import json

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from ..core.config import settings
from ..core.comfyui_client import ComfyUIClient
from ..core.template_scanner import TemplateScanner


# Request/Response Models
class WorkflowExecutionRequest(BaseModel):
    """Request model for workflow execution"""
    workflow: Dict = Field(..., description="ComfyUI workflow JSON")
    prompt_text: Optional[str] = Field(None, description="Optional prompt text")


class WorkflowExecutionResponse(BaseModel):
    """Response for workflow execution"""
    status: str
    prompt_id: Optional[str] = None
    message: str


class QueueStatusResponse(BaseModel):
    """Response for queue status endpoint"""
    queue_running: List[Dict]
    queue_pending: List[Dict]
    queue_remaining: int


class HistoryResponse(BaseModel):
    """Response for execution history"""
    history: Dict[str, Dict]


# Initialize router and dependencies
router = APIRouter()
comfyui_client = ComfyUIClient(base_url=f"http://localhost:{settings.COMFYUI_PORT}")


@router.get("/", response_model=Dict)
async def list_workflows(
    category: Optional[str] = Query(None, description="Filter by category")
) -> Dict:
    """
    List available ComfyUI workflows

    - **category**: Optional filter for workflow category (video, image, audio)
    """
    workflow_dir = Path(settings.WORKFLOW_BASE_PATH)

    if not workflow_dir.exists():
        return {"workflows": [], "categories": {}}

    workflows = []
    categories = set()

    for workflow_file in workflow_dir.rglob("*.json"):
        try:
            with open(workflow_file, 'r') as f:
                workflow_data = json.load(f)

            # Extract metadata if available
            workflow_name = workflow_file.stem
            workflow_category = workflow_data.get('category', 'uncategorized')

            if category and workflow_category != category:
                continue

            categories.add(workflow_category)

            workflows.append({
                "name": workflow_name,
                "path": str(workflow_file.relative_to(workflow_dir)),
                "category": workflow_category,
                "description": workflow_data.get('description', ''),
                "nodes": len(workflow_data.get('nodes', []))
            })
        except Exception as e:
            continue

    return {
        "workflows": workflows,
        "categories": {cat: cat for cat in categories},
        "total": len(workflows)
    }


@router.get("/{workflow_name}")
async def get_workflow(workflow_name: str):
    """Get specific workflow by name"""
    workflow_dir = Path(settings.WORKFLOW_BASE_PATH)

    if not workflow_dir.exists():
        raise HTTPException(status_code=404, detail="Workflow directory not found")

    # Find workflow file
    workflow_file = None
    for file_path in workflow_dir.rglob(f"{workflow_name}.json"):
        workflow_file = file_path
        break

    if not workflow_file:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_name} not found")

    try:
        with open(workflow_file, 'r') as f:
            workflow_data = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading workflow: {str(e)}")

    return {
        "name": workflow_name,
        "path": str(workflow_file.relative_to(workflow_dir)),
        "workflow": workflow_data
    }


@router.post("/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    request: WorkflowExecutionRequest,
    background_tasks: BackgroundTasks
) -> WorkflowExecutionResponse:
    """
    Execute a ComfyUI workflow

    - **workflow**: ComfyUI workflow JSON
    - **prompt_text**: Optional prompt text to inject into workflow
    """
    try:
        # If prompt text provided, inject into workflow
        workflow = request.workflow
        if request.prompt_text:
            workflow = comfyui_client.inject_prompt(workflow, request.prompt_text)

        # Queue the workflow for execution
        result = await comfyui_client.queue_workflow(workflow)

        return WorkflowExecutionResponse(
            status="queued",
            prompt_id=result.get("prompt_id"),
            message="Workflow queued successfully"
        )

    except Exception as e:
        return WorkflowExecutionResponse(
            status="error",
            prompt_id=None,
            message=f"Error executing workflow: {str(e)}"
        )


@router.get("/queue/status", response_model=QueueStatusResponse)
async def get_queue_status() -> QueueStatusResponse:
    """Get current queue status from ComfyUI"""
    try:
        status = await comfyui_client.get_queue_status()
        return QueueStatusResponse(
            queue_running=status.get("queue_running", []),
            queue_pending=status.get("queue_pending", []),
            queue_remaining=len(status.get("queue_pending", []))
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting queue status: {str(e)}")


@router.get("/history", response_model=HistoryResponse)
async def get_execution_history(
    limit: int = Query(50, description="Maximum number of history items")
) -> HistoryResponse:
    """
    Get workflow execution history from ComfyUI

    - **limit**: Maximum number of history items to return
    """
    try:
        history = await comfyui_client.get_history()

        # Limit results if specified
        if limit and len(history) > limit:
            history_items = list(history.items())[:limit]
            history = dict(history_items)

        return HistoryResponse(history=history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting history: {str(e)}")


@router.get("/history/{prompt_id}")
async def get_execution_result(prompt_id: str):
    """Get specific execution result by prompt ID"""
    try:
        result = await comfyui_client.get_history()

        if prompt_id not in result:
            raise HTTPException(status_code=404, detail=f"Prompt {prompt_id} not found in history")

        return result[prompt_id]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting execution result: {str(e)}")


@router.post("/queue/interrupt")
async def interrupt_queue():
    """Interrupt current execution and clear queue"""
    try:
        result = await comfyui_client.interrupt_execution()
        return {"status": "interrupted", "message": "Execution interrupted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interrupting execution: {str(e)}")


@router.post("/queue/clear")
async def clear_queue():
    """Clear all pending items from queue"""
    try:
        result = await comfyui_client.clear_queue()
        return {"status": "cleared", "message": "Queue cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing queue: {str(e)}")


@router.get("/outputs")
async def get_outputs():
    """Get list of generated outputs from ComfyUI"""
    try:
        outputs = await comfyui_client.get_outputs()
        return {"outputs": outputs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting outputs: {str(e)}")


@router.get("/system/metrics")
async def get_system_metrics():
    """Get ComfyUI system metrics and performance data"""
    try:
        metrics = await comfyui_client.get_system_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting system metrics: {str(e)}")


@router.get("/templates")
async def list_templates():
    """List ComfyUI templates with model compatibility info"""
    # ComfyUI templates location
    template_paths = [
        Path("/app/comfyui/web/assets"),
        Path("/workspace/workflows"),
    ]

    scanner = TemplateScanner(settings.MODEL_BASE_PATH)
    templates = []

    for base_path in template_paths:
        if not base_path.exists():
            continue

        for template_file in base_path.glob("**/*.json"):
            try:
                missing = scanner.get_missing_models(template_file)

                templates.append({
                    "id": str(template_file.relative_to(base_path)),
                    "name": template_file.stem,
                    "path": str(template_file),
                    "compatible": len(missing) == 0,
                    "missing_models": missing,
                    "missing_count": len(missing)
                })
            except Exception:
                continue

    return {"templates": templates, "total": len(templates)}


@router.get("/templates/{template_id:path}/missing-models")
async def get_template_missing_models(template_id: str):
    """Get missing models for a specific template"""
    # Find template
    template_paths = [
        Path("/app/comfyui/web/assets") / template_id,
        Path("/workspace/workflows") / template_id,
    ]

    template_file = None
    for path in template_paths:
        if path.exists():
            template_file = path
            break

    if not template_file:
        raise HTTPException(status_code=404, detail="Template not found")

    scanner = TemplateScanner(settings.MODEL_BASE_PATH)
    missing = scanner.get_missing_models(template_file)

    return {
        "template_id": template_id,
        "missing_models": missing,
        "can_generate": len(missing) == 0
    }
