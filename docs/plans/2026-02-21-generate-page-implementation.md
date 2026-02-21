# Generate Page Redesign - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Redesign the Generate page as an all-in-one workflow consumer with intent-based shortcuts, real-time progress, and optional AI prompt enhancement.

**Architecture:** Workflow-first UI with card-based browser, hybrid WebSocket/REST for real-time updates, optional local LLM service for prompt enhancement stored on network volume.

**Tech Stack:** FastAPI, Alpine.js, WebSocket, llama-cpp-python (optional), htmx

---

## Phase 1: Backend Foundation

### Task 1: Create Workflow Scanner Service

**Files:**
- Create: `dashboard/core/workflow_scanner.py`
- Create: `tests/test_workflow_scanner.py`

**Step 1: Write the failing test**

```python
# tests/test_workflow_scanner.py
import pytest
from pathlib import Path
import json
from dashboard.core.workflow_scanner import WorkflowScanner

def test_scan_workflow_extracts_metadata(tmp_path):
    """Test that scanner extracts workflow metadata correctly."""
    # Create a sample workflow file
    workflow = {
        "_meta": {
            "name": "Test Workflow",
            "description": "A test workflow",
            "category": "video"
        },
        "nodes": [
            {"type": "KSampler", "inputs": {"text": ""}},
            {"type": "VAEDecode", "inputs": {}}
        ]
    }

    workflow_file = tmp_path / "test_workflow.json"
    workflow_file.write_text(json.dumps(workflow))

    scanner = WorkflowScanner(tmp_path)
    result = scanner.scan_workflow(workflow_file)

    assert result["name"] == "Test Workflow"
    assert result["description"] == "A test workflow"
    assert result["category"] == "video"
    assert result["node_count"] == 2
```

**Step 2: Run test to verify it fails**

Run: `cd /app && PYTHONPATH=/app pytest tests/test_workflow_scanner.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'dashboard.core.workflow_scanner'"

**Step 3: Write minimal implementation**

```python
# dashboard/core/workflow_scanner.py
"""
Workflow Scanner Service
Scans workflow JSON files and extracts metadata for the Generate page.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class WorkflowMetadata:
    """Metadata extracted from a workflow file."""
    id: str
    name: str
    description: str
    category: str
    path: str
    node_count: int
    input_types: List[str]
    output_types: List[str]
    required_models: List[str]


class WorkflowScanner:
    """Scans workflow files and extracts metadata."""

    # Node types that indicate input type
    INPUT_NODES = {
        "CLIPTextEncode": "text",
        "LoadImage": "image",
        "LoadAudio": "audio",
        "VHS_LoadVideo": "video",
    }

    # Node types that indicate output type
    OUTPUT_NODES = {
        "SaveImage": "image",
        "VHS_SaveVideo": "video",
        "SaveAudio": "audio",
    }

    def __init__(self, workflow_base_path: Path):
        self.base_path = Path(workflow_base_path)

    def scan_workflow(self, workflow_path: Path) -> Dict[str, Any]:
        """Scan a single workflow file and extract metadata."""
        with open(workflow_path, 'r') as f:
            data = json.load(f)

        # Handle both API format and UI format
        if "nodes" in data:
            # UI format
            nodes = data.get("nodes", [])
            meta = data.get("_meta", {})
            node_count = len(nodes)

            # Scan for input/output types
            input_types = set()
            output_types = set()

            for node in nodes:
                node_type = node.get("type", "")
                if node_type in self.INPUT_NODES:
                    input_types.add(self.INPUT_NODES[node_type])
                if node_type in self.OUTPUT_NODES:
                    output_types.add(self.OUTPUT_NODES[node_type])
        else:
            # API format (dict of nodes)
            nodes = data
            meta = data.get("_meta", {})
            node_count = len([k for k in nodes.keys() if not k.startswith("_")])
            input_types = set()
            output_types = set()

            for node_id, node_data in nodes.items():
                if node_id.startswith("_"):
                    continue
                class_type = node_data.get("class_type", "")
                if class_type in self.INPUT_NODES:
                    input_types.add(self.INPUT_NODES[class_type])
                if class_type in self.OUTPUT_NODES:
                    output_types.add(self.OUTPUT_NODES[class_type])

        # Extract required models from workflow
        required_models = self._extract_required_models(data)

        return {
            "id": workflow_path.stem,
            "name": meta.get("name", workflow_path.stem),
            "description": meta.get("description", ""),
            "category": meta.get("category", self._infer_category(workflow_path)),
            "path": str(workflow_path.relative_to(self.base_path)) if workflow_path.is_relative_to(self.base_path) else str(workflow_path),
            "node_count": node_count,
            "input_types": list(input_types),
            "output_types": list(output_types),
            "required_models": required_models,
        }

    def scan_all(self) -> List[Dict[str, Any]]:
        """Scan all workflow files in the base path."""
        workflows = []

        if not self.base_path.exists():
            return workflows

        for workflow_file in self.base_path.rglob("*.json"):
            try:
                metadata = self.scan_workflow(workflow_file)
                workflows.append(metadata)
            except Exception as e:
                print(f"Warning: Failed to scan {workflow_file}: {e}")
                continue

        return workflows

    def _infer_category(self, workflow_path: Path) -> str:
        """Infer category from path structure."""
        parts = workflow_path.relative_to(self.base_path).parts
        if len(parts) > 1:
            return parts[0]
        return "general"

    def _extract_required_models(self, data: Dict) -> List[str]:
        """Extract required model filenames from workflow."""
        models = []

        # Handle both UI and API formats
        nodes = data.get("nodes", data) if "nodes" in data else data

        for node_data in (nodes.values() if isinstance(nodes, dict) else nodes):
            if isinstance(node_data, dict):
                inputs = node_data.get("inputs", {})
                for key, value in inputs.items():
                    if isinstance(value, str) and any(
                        ext in value.lower()
                        for ext in [".safetensors", ".pt", ".pth", ".bin", ".ckpt"]
                    ):
                        models.append(value)

        return list(set(models))


__all__ = ["WorkflowScanner", "WorkflowMetadata"]
```

**Step 4: Run test to verify it passes**

Run: `cd /app && PYTHONPATH=/app pytest tests/test_workflow_scanner.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add dashboard/core/workflow_scanner.py tests/test_workflow_scanner.py
git commit -m "feat: add workflow scanner service for metadata extraction"
```

---

### Task 2: Create Intent Matcher Service

**Files:**
- Create: `dashboard/core/intent_matcher.py`
- Create: `tests/test_intent_matcher.py`

**Step 1: Write the failing test**

```python
# tests/test_intent_matcher.py
import pytest
from dashboard.core.intent_matcher import IntentMatcher

def test_match_intent_returns_workflow_suggestions():
    """Test that intent matcher suggests workflows based on keywords."""
    matcher = IntentMatcher()

    # Test video from text intent
    result = matcher.match("I want to create a video from text")
    assert result["matched"] == True
    assert result["suggested_type"] == "t2v"
    assert len(result["suggestions"]) > 0

def test_match_intent_handles_image_to_video():
    """Test image to video intent detection."""
    matcher = IntentMatcher()

    result = matcher.match("turn this image into a video")
    assert result["matched"] == True
    assert result["suggested_type"] == "i2v"

def test_match_intent_handles_no_match():
    """Test that unclear intent returns no match."""
    matcher = IntentMatcher()

    result = matcher.match("hello world")
    assert result["matched"] == False
```

**Step 2: Run test to verify it fails**

Run: `cd /app && PYTHONPATH=/app pytest tests/test_intent_matcher.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# dashboard/core/intent_matcher.py
"""
Intent Matcher Service
Pattern-matches user intent to suggest workflows.
"""
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class IntentPattern:
    """Pattern for matching user intent."""
    keywords: List[str]
    suggested_type: str
    suggested_input_types: List[str]
    suggested_output_types: List[str]


class IntentMatcher:
    """Matches user intent to workflow types using pattern matching."""

    PATTERNS = [
        # Text to Video
        IntentPattern(
            keywords=["video from text", "text to video", "generate video", "create video", "make a video"],
            suggested_type="t2v",
            suggested_input_types=["text"],
            suggested_output_types=["video"]
        ),
        # Image to Video
        IntentPattern(
            keywords=["image to video", "animate image", "turn image into video", "photo to video", "picture to video"],
            suggested_type="i2v",
            suggested_input_types=["image"],
            suggested_output_types=["video"]
        ),
        # Text to Image
        IntentPattern(
            keywords=["image from text", "text to image", "generate image", "create image", "make an image", "picture of"],
            suggested_type="t2i",
            suggested_input_types=["text"],
            suggested_output_types=["image"]
        ),
        # Image to Image
        IntentPattern(
            keywords=["image to image", "transform image", "style transfer", "edit image", "modify image"],
            suggested_type="i2i",
            suggested_input_types=["image"],
            suggested_output_types=["image"]
        ),
        # Upscale
        IntentPattern(
            keywords=["upscale", "enhance resolution", "improve quality", "super resolution"],
            suggested_type="upscale",
            suggested_input_types=["image", "video"],
            suggested_output_types=["image", "video"]
        ),
        # Audio
        IntentPattern(
            keywords=["music", "audio", "sound", "generate audio", "create music"],
            suggested_type="audio",
            suggested_input_types=["text"],
            suggested_output_types=["audio"]
        ),
    ]

    def match(self, intent_text: str) -> Dict[str, Any]:
        """
        Match user intent to workflow suggestions.

        Args:
            intent_text: User's intent description

        Returns:
            Dict with matched status and suggestions
        """
        intent_lower = intent_text.lower().strip()

        for pattern in self.PATTERNS:
            for keyword in pattern.keywords:
                if keyword in intent_lower:
                    return {
                        "matched": True,
                        "suggested_type": pattern.suggested_type,
                        "suggested_input_types": pattern.suggested_input_types,
                        "suggested_output_types": pattern.suggested_output_types,
                        "matched_keyword": keyword,
                        "suggestions": self._get_suggestion_descriptions(pattern),
                    }

        return {
            "matched": False,
            "suggested_type": None,
            "suggestions": [],
        }

    def _get_suggestion_descriptions(self, pattern: IntentPattern) -> List[str]:
        """Get human-readable suggestions for a pattern."""
        descriptions = {
            "t2v": ["Text-to-Video workflows like WAN 2.2, LTX-Video"],
            "i2v": ["Image-to-Video workflows like WAN I2V, Hunyuan I2V"],
            "t2i": ["Text-to-Image workflows like FLUX, SDXL, SD3.5"],
            "i2i": ["Image-to-Image workflows like SDXL Img2Img"],
            "upscale": ["Upscaling workflows for images and videos"],
            "audio": ["Audio generation workflows like ACE Step, MusicGen"],
        }
        return descriptions.get(pattern.suggested_type, [])

    def get_quick_actions(self) -> List[Dict[str, str]]:
        """Get list of quick action buttons for the intent bar."""
        return [
            {"id": "t2v", "label": "Video from text", "icon": "🎬"},
            {"id": "i2v", "label": "Image to video", "icon": "🎥"},
            {"id": "t2i", "label": "Image from text", "icon": "🖼️"},
            {"id": "upscale", "label": "Upscale", "icon": "🔍"},
            {"id": "audio", "label": "Generate audio", "icon": "🎵"},
        ]


__all__ = ["IntentMatcher"]
```

**Step 4: Run test to verify it passes**

Run: `cd /app && PYTHONPATH=/app pytest tests/test_intent_matcher.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add dashboard/core/intent_matcher.py tests/test_intent_matcher.py
git commit -m "feat: add intent matcher for workflow suggestions"
```

---

### Task 3: Create Generate API Router

**Files:**
- Create: `dashboard/api/generate.py`
- Modify: `dashboard/main.py`

**Step 1: Write the generate API router**

```python
# dashboard/api/generate.py
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
workflow_scanner = WorkflowScanner(Path(settings.WORKFLOW_BASE_PATH))
intent_matcher = IntentMatcher()
comfyui_client = ComfyUIClient(base_url=f"http://localhost:{settings.COMFYUI_PORT}")


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
    workflows = workflow_scanner.scan_all()

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
    workflows = workflow_scanner.scan_all()

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
    workflows = workflow_scanner.scan_all()
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
        workflow_data = comfyui_client.inject_prompt(workflow_data, request.prompt)

        # Queue the workflow
        result = await comfyui_client.queue_workflow(workflow_data)

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
        await comfyui_client.interrupt_execution()
        return {"status": "cancelled", "prompt_id": prompt_id, "message": "Generation cancelled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel: {str(e)}")


__all__ = ["router"]
```

**Step 2: Register router in main.py**

Find the router registration section in `dashboard/main.py` and add:

```python
# Add to imports
from .api import generate

# Add to router registrations
app.include_router(generate.router, prefix="/api/generate", tags=["generate"])
```

**Step 3: Commit**

```bash
git add dashboard/api/generate.py dashboard/main.py
git commit -m "feat: add generate API router with workflow sync and intent matching"
```

---

### Task 4: Create Generation WebSocket Handler

**Files:**
- Create: `dashboard/core/generation_manager.py`
- Modify: `dashboard/main.py`

**Step 1: Create generation manager**

```python
# dashboard/core/generation_manager.py
"""
Generation Manager
Manages active generations and broadcasts progress via WebSocket.
"""
import asyncio
import json
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
import weakref


@dataclass
class ActiveGeneration:
    """Tracks an active generation."""
    prompt_id: str
    workflow_name: str
    workflow_id: str
    prompt: str
    status: str = "running"
    progress: float = 0.0
    current_node: str = ""
    started_at: datetime = field(default_factory=datetime.now)
    eta_seconds: int = 0


class GenerationManager:
    """Manages generations and WebSocket broadcasts."""

    def __init__(self):
        self.active_generations: Dict[str, ActiveGeneration] = {}
        self.connections: Set = weakref.WeakSet()
        self._comfyui_client = None

    @property
    def comfyui_client(self):
        """Lazy load ComfyUI client."""
        if self._comfyui_client is None:
            from .comfyui_client import ComfyUIClient
            from .config import settings
            self._comfyui_client = ComfyUIClient(base_url=f"http://localhost:{settings.COMFYUI_PORT}")
        return self._comfyui_client

    def register_connection(self, websocket):
        """Register a WebSocket connection."""
        self.connections.add(websocket)

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """Broadcast event to all connected clients."""
        message = json.dumps({
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            **data
        })

        dead_connections = set()
        for ws in self.connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead_connections.add(ws)

        # Clean up dead connections
        for ws in dead_connections:
            self.connections.discard(ws)

    async def start_generation(self, prompt_id: str, workflow_id: str, workflow_name: str, prompt: str):
        """Start tracking a generation."""
        generation = ActiveGeneration(
            prompt_id=prompt_id,
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            prompt=prompt,
            status="running"
        )
        self.active_generations[prompt_id] = generation

        await self.broadcast("generation_started", {
            "prompt_id": prompt_id,
            "workflow_id": workflow_id,
            "workflow_name": workflow_name
        })

    async def update_progress(self, prompt_id: str, progress: float, current_node: str = "", eta: int = 0):
        """Update generation progress."""
        if prompt_id in self.active_generations:
            gen = self.active_generations[prompt_id]
            gen.progress = progress
            gen.current_node = current_node
            gen.eta_seconds = eta

            await self.broadcast("generation_progress", {
                "prompt_id": prompt_id,
                "progress": progress,
                "current_node": current_node,
                "eta": eta
            })

    async def complete_generation(self, prompt_id: str, outputs: List[str]):
        """Mark generation as complete."""
        if prompt_id in self.active_generations:
            gen = self.active_generations[prompt_id]
            gen.status = "completed"
            gen.progress = 100.0

            await self.broadcast("generation_complete", {
                "prompt_id": prompt_id,
                "outputs": outputs,
                "duration_seconds": (datetime.now() - gen.started_at).total_seconds()
            })

            # Remove after a delay
            await asyncio.sleep(60)
            self.active_generations.pop(prompt_id, None)

    async def fail_generation(self, prompt_id: str, error: str):
        """Mark generation as failed."""
        if prompt_id in self.active_generations:
            gen = self.active_generations[prompt_id]
            gen.status = "failed"

            await self.broadcast("generation_error", {
                "prompt_id": prompt_id,
                "error": error
            })

            # Remove after a delay
            await asyncio.sleep(60)
            self.active_generations.pop(prompt_id, None)

    def get_active(self) -> List[Dict[str, Any]]:
        """Get all active generations."""
        return [
            {
                "prompt_id": gen.prompt_id,
                "workflow_name": gen.workflow_name,
                "status": gen.status,
                "progress": gen.progress,
                "current_node": gen.current_node,
                "eta": gen.eta_seconds
            }
            for gen in self.active_generations.values()
        ]


# Global instance
generation_manager = GenerationManager()


__all__ = ["GenerationManager", "generation_manager"]
```

**Step 2: Add WebSocket endpoint to main.py**

```python
# Add to main.py imports
from fastapi import WebSocket, WebSocketDisconnect
from .core.generation_manager import generation_manager

# Add WebSocket endpoint
@app.websocket("/ws/generate")
async def websocket_generate(websocket: WebSocket):
    """WebSocket for real-time generation updates."""
    await websocket.accept()
    generation_manager.register_connection(websocket)

    try:
        # Send initial state
        await websocket.send_text(json.dumps({
            "type": "connected",
            "active_generations": generation_manager.get_active()
        }))

        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            # Handle any client messages if needed
            try:
                message = json.loads(data)
                # Echo back for keepalive
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        pass
```

**Step 3: Commit**

```bash
git add dashboard/core/generation_manager.py dashboard/main.py
git commit -m "feat: add generation manager with WebSocket broadcasting"
```

---

## Phase 2: Frontend Redesign

### Task 5: Create New Generate Page Template

**Files:**
- Modify: `dashboard/templates/generate.html`

**Step 1: Rewrite generate.html with new layout**

This is a large file - create the complete new template with:
- Three-column responsive layout
- Workflow browser (left)
- Generation panel (right)
- Output/queue panel (bottom)
- Intent bar (top, collapsible)
- Alpine.js for interactivity
- WebSocket integration for real-time updates

**Step 2: Test page loads**

Visit: `https://{pod-id}-8082.proxy.runpod.net/generate`
Expected: New layout renders, no JS errors

**Step 3: Commit**

```bash
git add dashboard/templates/generate.html
git commit -m "feat: redesign generate page with workflow browser layout"
```

---

### Task 6: Update Sidebar with Queue Badge

**Files:**
- Modify: `dashboard/templates/components/sidebar.html`

**Step 1: Add queue count badge to Generate nav item**

```html
<a href="/generate"
   class="nav-item ..."
   :class="{ ... }">
    <div class="nav-item-icon ...">⚡</div>
    <span class="nav-item-label ...">Generate</span>
    <span class="nav-item-badge ml-auto bg-accent-primary text-text-inverse text-xs font-semibold px-2 py-0.5 rounded-full"
          x-show="queueCount > 0"
          x-text="queueCount"></span>
</a>
```

**Step 2: Add queueCount to dashboardApp() in base.html**

```javascript
// Add to dashboardApp() return
queueCount: 0,

// Add handler in handleWebSocketMessage
case 'queue_updated':
    this.queueCount = data.pending_count || 0;
    break;
```

**Step 3: Commit**

```bash
git add dashboard/templates/components/sidebar.html dashboard/templates/base.html
git commit -m "feat: add queue count badge to generate nav item"
```

---

## Phase 3: LLM Integration (Optional)

### Task 7: Create LLM Service

**Files:**
- Create: `dashboard/core/llm_service.py`
- Create: `dashboard/api/llm.py`
- Modify: `dashboard/main.py`

**Step 1: Create LLM service with lazy loading**

```python
# dashboard/core/llm_service.py
"""
LLM Service for Prompt Enhancement
Manages local LLM loading, inference, and unloading.
"""
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import threading


# LLM Model configurations
LLM_MODELS = {
    "phi-3-mini": {
        "name": "Phi-3 Mini",
        "size_gb": 2.0,
        "url": "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf",
        "filename": "phi-3-mini-q4.gguf",
    },
    "qwen-2.5-1.5b": {
        "name": "Qwen 2.5 1.5B",
        "size_gb": 1.5,
        "url": "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf",
        "filename": "qwen-2.5-1.5b-q4.gguf",
    },
    "llama-3.2-3b": {
        "name": "Llama 3.2 3B",
        "size_gb": 3.0,
        "url": "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "filename": "llama-3.2-3b-q4.gguf",
    },
}


class LLMService:
    """Manages local LLM for prompt enhancement."""

    def __init__(self, model_base_path: Path):
        self.model_base_path = Path(model_base_path)
        self.llm_dir = self.model_base_path / "llm"
        self.llm_dir.mkdir(parents=True, exist_ok=True)

        self._model = None
        self._current_model_id: Optional[str] = None
        self._last_used: Optional[datetime] = None
        self._lock = threading.Lock()
        self._unload_task: Optional[asyncio.Task] = None

    def get_model_path(self, model_id: str) -> Path:
        """Get the path to a model file."""
        return self.llm_dir / model_id / LLM_MODELS[model_id]["filename"]

    def is_installed(self, model_id: str) -> bool:
        """Check if a model is installed."""
        return self.get_model_path(model_id).exists()

    def get_status(self) -> Dict[str, Any]:
        """Get LLM service status."""
        installed = {}
        for model_id, config in LLM_MODELS.items():
            installed[model_id] = {
                "name": config["name"],
                "size_gb": config["size_gb"],
                "installed": self.is_installed(model_id),
            }

        return {
            "available_models": LLM_MODELS.keys(),
            "installed": installed,
            "current_model": self._current_model_id,
            "is_loaded": self._model is not None,
        }

    def _load_model(self, model_id: str):
        """Load a model into memory (lazy)."""
        if self._model is not None and self._current_model_id == model_id:
            return self._model

        try:
            from llama_cpp import Llama

            model_path = self.get_model_path(model_id)
            if not model_path.exists():
                raise FileNotFoundError(f"Model not installed: {model_id}")

            self._model = Llama(
                model_path=str(model_path),
                n_ctx=2048,
                n_threads=4,
                verbose=False,
            )
            self._current_model_id = model_id
            self._last_used = datetime.now()

            return self._model

        except ImportError:
            raise RuntimeError("llama-cpp-python not installed")

    async def enhance_prompt(
        self,
        prompt: str,
        style: str = "detailed",
        model_id: str = "phi-3-mini"
    ) -> Dict[str, Any]:
        """
        Enhance a prompt using the local LLM.

        Args:
            prompt: Original prompt to enhance
            style: Enhancement style (detailed, cinematic, artistic, minimal)
            model_id: Model to use for enhancement

        Returns:
            Dict with enhanced prompt and metadata
        """
        style_prompts = {
            "detailed": "Add quality tags, lighting details, and composition suggestions.",
            "cinematic": "Add film terminology, camera angles, and mood descriptors.",
            "artistic": "Add art style references, techniques, and artistic elements.",
            "minimal": "Fix grammar and lightly improve clarity only.",
        }

        system_prompt = f"""You are a prompt enhancement assistant for AI image/video generation.
Enhance the user's prompt by {style_prompts.get(style, style_prompts['detailed'])}
Keep the enhanced prompt concise (under 200 words).
Only output the enhanced prompt, nothing else."""

        try:
            # Load model in thread pool to avoid blocking
            loop = asyncio.get_event_loop()

            def run_inference():
                with self._lock:
                    model = self._load_model(model_id)
                    response = model.create_chat_completion(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt},
                        ],
                        max_tokens=200,
                        temperature=0.7,
                    )
                    return response["choices"][0]["message"]["content"]

            enhanced = await loop.run_in_executor(None, run_inference)
            self._last_used = datetime.now()

            return {
                "success": True,
                "original_prompt": prompt,
                "enhanced_prompt": enhanced.strip(),
                "style": style,
                "model": model_id,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "original_prompt": prompt,
            }

    async def download_model(self, model_id: str) -> Dict[str, Any]:
        """Download a model from HuggingFace."""
        if model_id not in LLM_MODELS:
            return {"success": False, "error": f"Unknown model: {model_id}"}

        config = LLM_MODELS[model_id]
        model_dir = self.llm_dir / model_id
        model_dir.mkdir(parents=True, exist_ok=True)
        model_path = model_dir / config["filename"]

        if model_path.exists():
            return {"success": True, "message": "Model already installed", "path": str(model_path)}

        # Download using aiohttp
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(config["url"]) as response:
                    if response.status != 200:
                        raise Exception(f"Download failed: HTTP {response.status}")

                    total_size = int(response.headers.get("content-length", 0))
                    downloaded = 0

                    with open(model_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                            downloaded += len(chunk)
                            # TODO: Broadcast progress via WebSocket

            return {
                "success": True,
                "message": f"Downloaded {config['name']}",
                "path": str(model_path),
                "size_mb": downloaded / (1024 * 1024),
            }

        except Exception as e:
            # Clean up partial download
            if model_path.exists():
                model_path.unlink()
            return {"success": False, "error": str(e)}


# Global instance
llm_service = LLMService(Path("/workspace/models"))


__all__ = ["LLMService", "llm_service", "LLM_MODELS"]
```

**Step 2: Create LLM API router**

```python
# dashboard/api/llm.py
"""
LLM API endpoints
Handles prompt enhancement and model management.
"""
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..core.llm_service import llm_service, LLM_MODELS


# Request/Response Models
class EnhanceRequest(BaseModel):
    """Request for prompt enhancement."""
    prompt: str = Field(..., description="Prompt to enhance")
    style: str = Field("detailed", description="Enhancement style")
    model: str = Field("phi-3-mini", description="Model to use")


class EnhanceResponse(BaseModel):
    """Response for prompt enhancement."""
    success: bool
    original_prompt: str
    enhanced_prompt: Optional[str] = None
    style: Optional[str] = None
    model: Optional[str] = None
    error: Optional[str] = None


class DownloadRequest(BaseModel):
    """Request to download a model."""
    model_id: str = Field(..., description="Model ID to download")


class DownloadResponse(BaseModel):
    """Response for model download."""
    success: bool
    message: str
    path: Optional[str] = None
    error: Optional[str] = None


# Initialize router
router = APIRouter()


@router.get("/status")
async def get_llm_status():
    """Get LLM service status and installed models."""
    return llm_service.get_status()


@router.get("/models")
async def list_available_models():
    """List all available LLM models."""
    return {
        "models": [
            {
                "id": model_id,
                "name": config["name"],
                "size_gb": config["size_gb"],
                "installed": llm_service.is_installed(model_id),
            }
            for model_id, config in LLM_MODELS.items()
        ]
    }


@router.post("/enhance", response_model=EnhanceResponse)
async def enhance_prompt(request: EnhanceRequest) -> EnhanceResponse:
    """
    Enhance a prompt using the local LLM.

    Requires LLM to be enabled and model installed.
    """
    # Check if model is installed
    if not llm_service.is_installed(request.model):
        raise HTTPException(
            status_code=400,
            detail=f"Model {request.model} not installed. Download it first."
        )

    result = await llm_service.enhance_prompt(
        prompt=request.prompt,
        style=request.style,
        model_id=request.model
    )

    return EnhanceResponse(**result)


@router.post("/download", response_model=DownloadResponse)
async def download_model(request: DownloadRequest) -> DownloadResponse:
    """
    Download an LLM model.

    Models are stored in /workspace/models/llm/{model_id}/
    """
    if request.model_id not in LLM_MODELS:
        raise HTTPException(status_code=400, detail=f"Unknown model: {request.model_id}")

    result = await llm_service.download_model(request.model_id)
    return DownloadResponse(**result)


__all__ = ["router"]
```

**Step 3: Register LLM router in main.py**

```python
# Add to imports
from .api import llm

# Add to router registrations
app.include_router(llm.router, prefix="/api/llm", tags=["llm"])
```

**Step 4: Commit**

```bash
git add dashboard/core/llm_service.py dashboard/api/llm.py dashboard/main.py
git commit -m "feat: add LLM service for prompt enhancement with model selection"
```

---

### Task 8: Add LLM Settings to Settings Page

**Files:**
- Modify: `dashboard/templates/settings.html`

**Step 1: Add AI Features section to settings**

Add section with:
- Enable/disable toggle
- Model selection radio buttons
- Download button
- Status indicator
- Tooltip explaining the feature

**Step 2: Test settings page**

Visit: `https://{pod-id}-8082.proxy.runpod.net/settings`
Expected: AI Features section appears, model options show

**Step 3: Commit**

```bash
git add dashboard/templates/settings.html
git commit -m "feat: add LLM settings section with model selection"
```

---

## Phase 4: Integration & Testing

### Task 9: Add Cross-Page Navigation

**Files:**
- Modify: `dashboard/templates/models.html`
- Modify: `dashboard/templates/workflows.html`

**Step 1: Add Generate button to installed model cards**

On Models page, for installed presets, add a "Generate" button that links to `/generate?workflow={workflow_id}`.

**Step 2: Add Generate button to workflow cards**

On Workflows page, add a "Generate" button that links to `/generate?workflow={workflow_id}`.

**Step 3: Commit**

```bash
git add dashboard/templates/models.html dashboard/templates/workflows.html
git commit -m "feat: add generate buttons to models and workflows pages"
```

---

### Task 10: End-to-End Testing

**Step 1: Test workflow browser loads**

- Visit `/generate`
- Verify workflows appear in browser
- Verify filters work
- Verify search works

**Step 2: Test intent matching**

- Type intent in quick bar
- Verify suggestions appear
- Click suggestion, verify workflow selected

**Step 3: Test generation flow**

- Select workflow
- Enter prompt
- Click Generate
- Verify WebSocket progress updates
- Verify output appears

**Step 4: Test LLM enhancement (if enabled)**

- Enable in settings
- Download model
- Use enhance prompt feature
- Verify enhanced prompt appears

**Step 5: Final commit**

```bash
git add -A
git commit -m "feat: complete generate page redesign with all features"
```

---

## Summary

| Phase | Tasks | Est. Time |
|-------|-------|-----------|
| Phase 1: Backend Foundation | Tasks 1-4 | Core APIs |
| Phase 2: Frontend Redesign | Tasks 5-6 | UI rebuild |
| Phase 3: LLM Integration | Tasks 7-8 | Optional AI |
| Phase 4: Integration | Tasks 9-10 | Polish & test |

**Total: 10 tasks, ~20-30 bite-sized steps**
