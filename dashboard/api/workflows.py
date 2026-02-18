"""
Workflow management API endpoints
Handles workflow listing, execution, and ComfyUI integration
"""

from typing import List, Dict, Optional
from pathlib import Path
import json
import shutil

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, UploadFile, File, Form
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
    # Validate template_id does not contain path traversal
    if ".." in template_id or template_id.startswith("/") or template_id.startswith("\\"):
        raise HTTPException(status_code=400, detail="Invalid template ID")

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


class WorkflowImportRequest(BaseModel):
    """Request model for workflow import"""
    name: str = Field(..., description="Name for the workflow")
    workflow: Dict = Field(..., description="ComfyUI workflow JSON")
    category: Optional[str] = Field("imported", description="Category for the workflow")
    description: Optional[str] = Field("", description="Description of the workflow")


class WorkflowImportResponse(BaseModel):
    """Response for workflow import"""
    status: str
    name: str
    path: str
    message: str


@router.post("/import", response_model=WorkflowImportResponse)
async def import_workflow(request: WorkflowImportRequest) -> WorkflowImportResponse:
    """
    Import a workflow JSON to the workflows directory

    - **name**: Name for the workflow file (without .json extension)
    - **workflow**: ComfyUI workflow JSON object
    - **category**: Optional category (default: "imported")
    - **description**: Optional description
    """
    workflow_dir = Path(settings.WORKFLOW_BASE_PATH)

    # Create workflow directory if it doesn't exist
    workflow_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize name - remove dangerous characters
    safe_name = "".join(c for c in request.name if c.isalnum() or c in ('_', '-', ' ')).strip()
    if not safe_name:
        safe_name = "imported_workflow"

    # Sanitize category to prevent path traversal
    safe_category = "".join(c for c in (request.category or "imported") if c.isalnum() or c in ('_', '-')).strip()
    if not safe_category:
        safe_category = "imported"

    # Create category subdirectory if specified
    if safe_category and safe_category != "uncategorized":
        target_dir = workflow_dir / safe_category
        target_dir.mkdir(parents=True, exist_ok=True)
    else:
        target_dir = workflow_dir

    # Check if file already exists
    workflow_file = target_dir / f"{safe_name}.json"
    counter = 1
    while workflow_file.exists():
        workflow_file = target_dir / f"{safe_name}_{counter}.json"
        counter += 1

    # Add metadata to workflow
    workflow_with_meta = request.workflow.copy()
    workflow_with_meta['_meta'] = {
        'name': safe_name,
        'category': request.category or 'imported',
        'description': request.description or ''
    }

    try:
        with open(workflow_file, 'w') as f:
            json.dump(workflow_with_meta, f, indent=2)

        relative_path = str(workflow_file.relative_to(workflow_dir))

        return WorkflowImportResponse(
            status="imported",
            name=safe_name,
            path=relative_path,
            message=f"Workflow imported successfully as {workflow_file.name}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving workflow: {str(e)}")


@router.post("/upload")
async def upload_workflow(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    category: Optional[str] = Form("imported")
):
    """
    Upload a workflow JSON file

    - **file**: Workflow JSON file
    - **name**: Optional name (uses filename if not provided)
    - **category**: Optional category (default: "imported")
    """
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files are accepted")

    try:
        content = await file.read()
        workflow_data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

    # Use provided name or filename
    workflow_name = name or Path(file.filename).stem

    # Create import request and delegate to import endpoint logic
    import_request = WorkflowImportRequest(
        name=workflow_name,
        workflow=workflow_data,
        category=category,
        description=workflow_data.get('_meta', {}).get('description', '')
    )

    return await import_workflow(import_request)


@router.delete("/{workflow_name}")
async def delete_workflow(workflow_name: str):
    """Delete a workflow file"""
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
        workflow_file.unlink()
        return {"status": "deleted", "name": workflow_name, "message": f"Workflow {workflow_name} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting workflow: {str(e)}")
