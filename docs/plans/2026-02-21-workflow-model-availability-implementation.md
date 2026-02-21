# Workflow Model Availability System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable the generate page to detect missing workflow models, map them to presets, and provide installation paths.

**Architecture:** Enhance the workflow scanner to extract models from node inputs, widgets_values, and MarkdownNote. Add availability checking against installed models and preset matching. Expose via enhanced API and updated generate page UI.

**Tech Stack:** Python, FastAPI, Alpine.js, htmx

---

## Task 1: Extract Models from widgets_values

**Files:**
- Modify: `dashboard/core/workflow_scanner.py`
- Test: Manual testing via API

**Context:** Workflows with packed/composite nodes store model filenames in `widgets_values` array. Need to detect these.

**Step 1: Add widgets_values extraction to scan_workflow**

In `workflow_scanner.py`, add a new method `_extract_models_from_widgets`:

```python
def _extract_models_from_widgets(self, node: Dict) -> List[str]:
    """Extract model filenames from widgets_values array."""
    models = []
    widgets_values = node.get("widgets_values", [])

    if not isinstance(widgets_values, list):
        return models

    for value in widgets_values:
        if isinstance(value, str) and any(
            ext in value.lower()
            for ext in [".safetensors", ".pt", ".pth", ".bin", ".ckpt"]
        ):
            models.append(value)

    return models
```

**Step 2: Update _extract_required_models to include widgets_values**

Modify `_extract_required_models` to also check widgets_values:

```python
def _extract_required_models(self, data: Dict) -> List[str]:
    """Extract required model filenames from workflow."""
    models = []

    # Handle both UI and API formats
    nodes = data.get("nodes", data) if "nodes" in data else data

    for node_data in (nodes.values() if isinstance(nodes, dict) else nodes):
        if isinstance(node_data, dict):
            # Check inputs (API format: dict, UI format: list)
            inputs = node_data.get("inputs", {})
            if isinstance(inputs, dict):
                for key, value in inputs.items():
                    if isinstance(value, str) and any(
                        ext in value.lower()
                        for ext in [".safetensors", ".pt", ".pth", ".bin", ".ckpt"]
                    ):
                        models.append(value)
            elif isinstance(inputs, list):
                for input_item in inputs:
                    if isinstance(input_item, dict):
                        value = input_item.get("value", "")
                        if isinstance(value, str) and any(
                            ext in value.lower()
                            for ext in [".safetensors", ".pt", ".pth", ".bin", ".ckpt"]
                        ):
                            models.append(value)

            # Check widgets_values (packed nodes)
            models.extend(self._extract_models_from_widgets(node_data))

    return list(set(models))
```

**Step 3: Test the extraction**

Run: `curl -s http://localhost:8000/api/generate/workflows/synced | jq '.workflows[0].required_models'`

Expected: `["z_image_turbo_bf16.safetensors", "qwen_3_4b.safetensors", "ae.safetensors"]`

**Step 4: Commit**

```bash
git add dashboard/core/workflow_scanner.py
git commit -m "feat: extract models from widgets_values in workflow scanner"
```

---

## Task 2: Add Model Type Inference

**Files:**
- Modify: `dashboard/core/workflow_scanner.py`

**Context:** Need to infer model type (checkpoints, diffusion_models, etc.) from filename patterns for availability checking.

**Step 1: Add model type inference constants and method**

Add to `WorkflowScanner` class:

```python
# Model type inference patterns
MODEL_TYPE_PATTERNS = {
    "diffusion_models": ["flux", "unet", "diffusion", "_turbo", "sdxl", "sd15"],
    "text_encoders": ["clip", "t5", "qwen", "llama", "text_encoder"],
    "vae": ["vae", "ae.safetensors"],
    "loras": ["lora"],
    "checkpoints": ["checkpoint", "inpaint", "dreamshaper"],
}

def _infer_model_type(self, filename: str) -> str:
    """Infer model type from filename patterns."""
    filename_lower = filename.lower()

    for model_type, patterns in self.MODEL_TYPE_PATTERNS.items():
        for pattern in patterns:
            if pattern in filename_lower:
                return model_type

    # Default to checkpoints for unknown models
    return "checkpoints"
```

**Step 2: Test model type inference**

Run: Test via Python REPL or add a quick test in the scanner.

**Step 3: Commit**

```bash
git add dashboard/core/workflow_scanner.py
git commit -m "feat: add model type inference from filename patterns"
```

---

## Task 3: Add Model Availability Checker

**Files:**
- Modify: `dashboard/core/workflow_scanner.py`

**Context:** Check if extracted models exist in `/workspace/models/` directories.

**Step 1: Add availability check method**

Add to `WorkflowScanner` class:

```python
# Model directories to search (in order)
MODEL_DIRECTORIES = [
    "checkpoints",
    "diffusion_models",
    "text_encoders",
    "vae",
    "loras",
    "clip_vision",
    "controlnet",
    "upscale_models",
]

def check_model_availability(self, model_filename: str) -> Dict[str, Any]:
    """Check if a model is installed and return its info."""
    for model_type in self.MODEL_DIRECTORIES:
        path = self.base_path.parent / "models" / model_type / model_filename
        if path.exists():
            return {
                "name": model_filename,
                "installed": True,
                "type": model_type,
                "path": str(path),
            }

    # Not found - infer type from filename
    inferred_type = self._infer_model_type(model_filename)
    return {
        "name": model_filename,
        "installed": False,
        "type": inferred_type,
        "path": None,
    }
```

**Step 2: Add batch availability check method**

```python
def check_workflow_models(self, required_models: List[str]) -> List[Dict[str, Any]]:
    """Check availability for all required models."""
    return [self.check_model_availability(model) for model in required_models]
```

**Step 3: Commit**

```bash
git add dashboard/core/workflow_scanner.py
git commit -m "feat: add model availability checker to workflow scanner"
```

---

## Task 4: Enhance Workflow Metadata with Model Status

**Files:**
- Modify: `dashboard/core/workflow_scanner.py`

**Context:** Update scan_workflow to include model availability info.

**Step 1: Update scan_workflow return structure**

Modify `scan_workflow` method to include model availability:

```python
def scan_workflow(self, workflow_path: Path) -> Dict[str, Any]:
    """Scan a single workflow file and extract metadata."""
    # ... existing code ...

    # Extract required models from workflow
    required_models = self._extract_required_models(data)

    # Check model availability
    models = self.check_workflow_models(required_models)

    # Calculate model status
    installed_count = sum(1 for m in models if m["installed"])
    missing_count = len(models) - installed_count

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
        # New fields
        "models": models,
        "model_status": {
            "total": len(models),
            "installed": installed_count,
            "missing": missing_count,
        },
        "ready": missing_count == 0 if models else True,  # Ready if no models or all installed
    }
```

**Step 2: Test enhanced workflow metadata**

Run: `curl -s http://localhost:8000/api/generate/workflows/synced | jq '.workflows[0] | {id, ready, model_status, models}'`

Expected: Workflow with ready=false, model_status showing missing models.

**Step 3: Commit**

```bash
git add dashboard/core/workflow_scanner.py
git commit -m "feat: enhance workflow metadata with model availability status"
```

---

## Task 5: Add Preset Matching for Missing Models

**Files:**
- Modify: `dashboard/api/generate.py`

**Context:** For missing models, check if a preset exists that can install them.

**Step 1: Add preset matching function**

Add to `generate.py`:

```python
from ..core.config import settings
import yaml
import json

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
            return yaml.safe_load(f)

    return {"presets": {}}

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
```

**Step 2: Add action URLs generation**

```python
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
```

**Step 3: Commit**

```bash
git add dashboard/api/generate.py
git commit -m "feat: add preset matching and request URL generation"
```

---

## Task 6: Enhance API Response with Model Actions

**Files:**
- Modify: `dashboard/api/generate.py`

**Context:** Update the synced workflows endpoint to include preset info and action URLs.

**Step 1: Add model actions enrichment**

Add helper function:

```python
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
```

**Step 2: Update get_synced_workflows endpoint**

Modify the endpoint to enrich models:

```python
@router.get("/workflows/synced", response_model=WorkflowSyncedResponse)
async def get_synced_workflows(
    category: Optional[str] = Query(None, description="Filter by category"),
    input_type: Optional[str] = Query(None, description="Filter by input type"),
    output_type: Optional[str] = Query(None, description="Filter by output type"),
) -> WorkflowSyncedResponse:
    """List all synced workflows with metadata and model availability."""
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

    # Apply filters (existing code)
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
```

**Step 3: Test enhanced API response**

Run: `curl -s http://localhost:8000/api/generate/workflows/synced | jq '.workflows[0].models'`

Expected: Models with preset info and action URLs.

**Step 4: Commit**

```bash
git add dashboard/api/generate.py
git commit -m "feat: enrich workflow API response with preset info and actions"
```

---

## Task 7: Update Generate Page UI - Workflow Card Status

**Files:**
- Modify: `dashboard/templates/generate.html`

**Context:** Show workflow readiness status on workflow cards.

**Step 1: Add status badge to workflow card template**

Find the workflow card section and add status indicator:

```html
<!-- Workflow Card Status Badge -->
<template x-for="workflow in workflows" :key="workflow.id">
    <div class="workflow-card ...">
        <div class="flex items-center justify-between mb-2">
            <h3 class="font-medium" x-text="workflow.name"></h3>
            <!-- Status Badge -->
            <div class="flex items-center gap-1">
                <template x-if="workflow.ready">
                    <span class="px-2 py-0.5 text-xs rounded-full bg-accent-success/20 text-accent-success">
                        Ready
                    </span>
                </template>
                <template x-if="!workflow.ready && workflow.model_status">
                    <span class="px-2 py-0.5 text-xs rounded-full bg-accent-warning/20 text-accent-warning">
                        <span x-text="workflow.model_status.missing"></span> models needed
                    </span>
                </template>
            </div>
        </div>
        <!-- Rest of card content -->
    </div>
</template>
```

**Step 2: Commit**

```bash
git add dashboard/templates/generate.html
git commit -m "feat: add workflow readiness status badge to generate page"
```

---

## Task 8: Update Generate Page UI - Model Requirements Panel

**Files:**
- Modify: `dashboard/templates/generate.html`

**Context:** Add expandable panel showing model requirements with install/request buttons.

**Step 1: Add model requirements panel to workflow card**

Add expandable section to workflow card:

```html
<!-- Model Requirements Panel -->
<div x-show="selectedWorkflow && selectedWorkflow.id === workflow.id" class="mt-3 pt-3 border-t border-border-primary">
    <h4 class="text-sm font-medium text-text-secondary mb-2">Required Models</h4>

    <template x-for="model in workflow.models" :key="model.name">
        <div class="flex items-center justify-between py-1.5">
            <div class="flex items-center gap-2">
                <!-- Status Icon -->
                <template x-if="model.installed">
                    <svg class="w-4 h-4 text-accent-success" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                    </svg>
                </template>
                <template x-if="!model.installed">
                    <svg class="w-4 h-4 text-accent-warning" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                    </svg>
                </template>
                <span class="text-sm" x-text="model.name"></span>
            </div>

            <!-- Actions -->
            <div class="flex items-center gap-2">
                <template x-if="model.installed">
                    <span class="text-xs text-accent-success">Installed</span>
                </template>
                <template x-if="!model.installed && model.preset">
                    <button @click="installPreset(model.preset.id)"
                            class="px-2 py-1 text-xs bg-accent-primary text-white rounded hover:bg-accent-primary/80">
                        Install <span x-text="model.preset.download_size"></span>
                    </button>
                </template>
                <template x-if="!model.installed && !model.preset">
                    <a :href="model.actions.request_preset_url" target="_blank"
                       class="px-2 py-1 text-xs bg-bg-elevated text-text-secondary rounded hover:bg-bg-hover">
                        Request Preset
                    </a>
                </template>
            </div>
        </div>
    </template>

    <!-- Start Generation Button -->
    <div class="mt-4 flex justify-end gap-2">
        <button x-show="!workflow.ready"
                class="px-3 py-1.5 text-sm text-text-secondary hover:text-text-primary">
            Start Anyway
        </button>
        <button @click="selectWorkflow(workflow)"
                :class="workflow.ready ? 'bg-accent-primary' : 'bg-accent-warning'"
                class="px-4 py-2 text-sm text-white rounded hover:opacity-80">
            <span x-text="workflow.ready ? 'Start Generation' : 'Generate (Missing Models)'"></span>
        </button>
    </div>
</div>
```

**Step 2: Add installPreset function to Alpine.js**

Add to the Alpine.js component:

```javascript
installPreset(presetId) {
    // Use existing preset install API
    fetch(`/api/presets/${presetId}/install`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            // Refresh workflow list after install starts
            this.fetchWorkflows();
        });
}
```

**Step 3: Commit**

```bash
git add dashboard/templates/generate.html
git commit -m "feat: add model requirements panel with install/request buttons"
```

---

## Task 9: Integration Testing

**Files:**
- None (testing only)

**Context:** Verify the complete flow works end-to-end.

**Step 1: Test API endpoint**

```bash
curl -s http://localhost:8000/api/generate/workflows/synced | jq '.workflows[0]'
```

Expected: Workflow with ready=false, model_status, models with actions.

**Step 2: Test in browser**

1. Navigate to `/generate`
2. Verify workflow cards show status badges
3. Click on a workflow to expand model requirements
4. Verify install/request buttons appear for missing models
5. Test "Install" button triggers download

**Step 3: Test preset install flow**

1. Click "Install" for a model with preset
2. Verify download starts in preset system
3. Wait for completion
4. Refresh page, verify model shows as installed

**Step 4: Final commit**

```bash
git add -A
git commit -m "feat: complete workflow model availability system"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Extract models from widgets_values | workflow_scanner.py |
| 2 | Add model type inference | workflow_scanner.py |
| 3 | Add model availability checker | workflow_scanner.py |
| 4 | Enhance workflow metadata | workflow_scanner.py |
| 5 | Add preset matching | generate.py |
| 6 | Enhance API response | generate.py |
| 7 | Add status badges | generate.html |
| 8 | Add model requirements panel | generate.html |
| 9 | Integration testing | - |
