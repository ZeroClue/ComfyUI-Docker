# Workflow Preset Suggestions Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** When a user selects a workflow, suggest presets that provide the required models with one-click installation.

**Architecture:** Hybrid approach - load model_index.json mapping at runtime, resolve model filenames to preset IDs, enhance workflow metadata with suggested_presets array, update UI to show install buttons.

**Tech Stack:** Python, FastAPI, Alpine.js, existing WorkflowScanner pattern

---

## Task 1: Set Up Worktree

**Step 1: Create feature branch worktree**

```bash
git worktree add .worktrees/preset-suggestions -b feature/preset-suggestions
cd .worktrees/preset-suggestions
```

**Step 2: Verify clean baseline**

```bash
git status
npm test  # or equivalent project test command
```

---

## Task 2: Add Model Index Loading to WorkflowScanner

**Files:**
- Modify: `dashboard/core/workflow_scanner.py:65-70`
- Create: `tests/unit/test_workflow_scanner.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_workflow_scanner.py
import json
import tempfile
from pathlib import Path
from dashboard.core.workflow_scanner import WorkflowScanner

def test_load_model_index():
    """Test that WorkflowScanner loads model_index.json mapping."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create mock model_index.json
        index_path = Path(tmpdir) / "data" / "model_index.json"
        index_path.parent.mkdir(parents=True)

        index_data = {
            "version": "1.0.0",
            "mappings": {
                "checkpoints/flux-dev.safetensors": "FLUX_DEV",
                "text_encoders/t5xxl_fp16.safetensors": "T5_XXL"
            }
        }
        with open(index_path, 'w') as f:
            json.dump(index_data, f)

        # Create scanner with custom index path
        workflow_path = Path(tmpdir) / "workflows"
        workflow_path.mkdir()

        scanner = WorkflowScanner(workflow_path)
        scanner._model_index_path = index_path
        scanner._load_model_index()

        assert "checkpoints/flux-dev.safetensors" in scanner._model_index
        assert scanner._model_index["checkpoints/flux-dev.safetensors"] == "FLUX_DEV"
```

**Step 2: Run test to verify it fails**

Run: `cd /app && PYTHONPATH=/app pytest tests/unit/test_workflow_scanner.py::test_load_model_index -v`
Expected: FAIL with "AttributeError" or "assertion error"

**Step 3: Add model index loading to WorkflowScanner**

```python
# dashboard/core/workflow_scanner.py
# Add after __init__ method (around line 70)

def __init__(self, workflow_base_path: Path):
    self.base_path = Path(workflow_base_path)
    self._registry_path = Path("/workspace/data/registry.json")
    self._models_path = self.base_path.parent / "models"
    self._comfyui_user_path = Path("/workspace/ComfyUI/user")
    # NEW: Model index for preset suggestions
    self._model_index_path = Path("/workspace/data/model_index.json")
    self._model_index: Dict[str, str] = {}
    self._load_model_index()

def _load_model_index(self) -> None:
    """Load model filename → preset_id mapping from cache."""
    if self._model_index_path.exists():
        try:
            with open(self._model_index_path, 'r') as f:
                data = json.load(f)
                self._model_index = data.get("mappings", {})
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load model index: {e}")
            self._model_index = {}
```

**Step 4: Run test to verify it passes**

Run: `cd /app && PYTHONPATH=/app pytest tests/unit/test_workflow_scanner.py::test_load_model_index -v`
Expected: PASS

**Step 5: Commit**

```bash
git add dashboard/core/workflow_scanner.py tests/unit/test_workflow_scanner.py
git commit -m "feat: add model index loading to WorkflowScanner"
```

---

## Task 3: Add resolve_model_to_preset Method

**Files:**
- Modify: `dashboard/core/workflow_scanner.py`
- Modify: `tests/unit/test_workflow_scanner.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_workflow_scanner.py - add to existing file

def test_resolve_model_to_preset_exact_match():
    """Test resolving model filename to preset via exact path match."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workflow_path = Path(tmpdir) / "workflows"
        workflow_path.mkdir()

        scanner = WorkflowScanner(workflow_path)
        scanner._model_index = {
            "checkpoints/flux-dev.safetensors": "FLUX_DEV",
            "text_encoders/t5xxl_fp16.safetensors": "T5_XXL"
        }

        result = scanner.resolve_model_to_preset("flux-dev.safetensors")
        assert result is not None
        assert result["preset_id"] == "FLUX_DEV"

def test_resolve_model_to_preset_not_found():
    """Test resolving model that has no preset mapping."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workflow_path = Path(tmpdir) / "workflows"
        workflow_path.mkdir()

        scanner = WorkflowScanner(workflow_path)
        scanner._model_index = {}

        result = scanner.resolve_model_to_preset("unknown_model.safetensors")
        assert result is None
```

**Step 2: Run test to verify it fails**

Run: `cd /app && PYTHONPATH=/app pytest tests/unit/test_workflow_scanner.py::test_resolve_model_to_preset -v`
Expected: FAIL with "AttributeError"

**Step 3: Implement resolve_model_to_preset**

```python
# dashboard/core/workflow_scanner.py - add after _load_model_index

def resolve_model_to_preset(self, model_filename: str) -> Optional[Dict[str, Any]]:
    """
    Find which preset provides a given model file.

    Args:
        model_filename: The model filename (e.g., "flux-dev.safetensors")

    Returns:
        Dict with preset_id, preset_name, installed status, or None if not found.
    """
    # Try exact path match first (checkpoints/filename.safetensors)
    for model_dir in self.MODEL_DIRECTORIES:
        path_key = f"{model_dir}/{model_filename}"
        if path_key in self._model_index:
            preset_id = self._model_index[path_key]
            return self._build_preset_info(preset_id, model_filename)

    # Fallback: filename-only match
    for path_key, preset_id in self._model_index.items():
        if Path(path_key).name == model_filename:
            return self._build_preset_info(preset_id, model_filename)

    return None

def _build_preset_info(self, preset_id: str, model_file: str) -> Dict[str, Any]:
    """Build preset info dict with installation status."""
    # Get preset details from registry if available
    preset_info = self._get_preset_from_registry(preset_id)

    # Check if the model file is installed
    installed = self._check_model_installed(model_file)

    return {
        "preset_id": preset_id,
        "preset_name": preset_info.get("name", preset_id) if preset_info else preset_id,
        "model_file": model_file,
        "installed": installed,
        "download_size": preset_info.get("download_size") if preset_info else None,
    }

def _get_preset_from_registry(self, preset_id: str) -> Optional[Dict]:
    """Get preset info from cached registry."""
    if not self._registry_path.exists():
        return None
    try:
        with open(self._registry_path, 'r') as f:
            registry = json.load(f)
            return registry.get("presets", {}).get(preset_id)
    except (json.JSONDecodeError, IOError):
        return None

def _check_model_installed(self, model_filename: str) -> bool:
    """Check if a model file exists in any model directory."""
    for model_dir in self.MODEL_DIRECTORIES:
        model_path = self._models_path / model_dir / model_filename
        if model_path.exists():
            return True
    return False
```

**Step 4: Run test to verify it passes**

Run: `cd /app && PYTHONPATH=/app pytest tests/unit/test_workflow_scanner.py::test_resolve_model_to_preset -v`
Expected: PASS

**Step 5: Commit**

```bash
git add dashboard/core/workflow_scanner.py tests/unit/test_workflow_scanner.py
git commit -m "feat: add resolve_model_to_preset method"
```

---

## Task 4: Update scan_workflow to Include Suggested Presets

**Files:**
- Modify: `dashboard/core/workflow_scanner.py:140-170`
- Modify: `tests/unit/test_workflow_scanner.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_workflow_scanner.py - add to existing file

def test_scan_workflow_includes_suggested_presets():
    """Test that scan_workflow returns suggested_presets for missing models."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workflow_path = Path(tmpdir) / "workflows"
        workflow_path.mkdir()

        # Create a workflow with model reference
        workflow_file = workflow_path / "test_workflow.json"
        workflow_data = {
            "1": {
                "class_type": "UNETLoader",
                "inputs": {"unet_name": "flux-dev.safetensors"}
            },
            "_meta": {"name": "Test WF"}
        }
        with open(workflow_file, 'w') as f:
            json.dump(workflow_data, f)

        scanner = WorkflowScanner(workflow_path)
        scanner._model_index = {"checkpoints/flux-dev.safetensors": "FLUX_DEV"}

        result = scanner.scan_workflow(workflow_file)

        assert "suggested_presets" in result
        assert len(result["suggested_presets"]) == 1
        assert result["suggested_presets"][0]["preset_id"] == "FLUX_DEV"
        assert "unmapped_models" in result
```

**Step 2: Run test to verify it fails**

Run: `cd /app && PYTHONPATH=/app pytest tests/unit/test_workflow_scanner.py::test_scan_workflow_includes_suggested_presets -v`
Expected: FAIL with "AssertionError" or "KeyError"

**Step 3: Update scan_workflow method**

```python
# dashboard/core/workflow_scanner.py - modify scan_workflow method (around line 140)
# Replace the existing return block with enhanced version

def scan_workflow(self, workflow_path: Path) -> Dict[str, Any]:
    """Scan a single workflow file and extract metadata."""
    # ... existing code to extract required_models ...

    # Extract required models from workflow
    required_models = self._extract_required_models(data)

    # Check model availability
    models = self.check_workflow_models(required_models)

    # NEW: Resolve models to presets
    suggested_presets = []
    unmapped_models = []
    seen_presets = set()

    for model_file in required_models:
        preset_info = self.resolve_model_to_preset(model_file)
        if preset_info:
            preset_id = preset_info["preset_id"]
            if preset_id not in seen_presets:
                seen_presets.add(preset_id)
                suggested_presets.append(preset_info)
        else:
            unmapped_models.append(model_file)

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
        # Model availability fields
        "models": models,
        "model_status": {
            "total": len(models),
            "installed": installed_count,
            "missing": missing_count,
        },
        "ready": missing_count == 0 if models else True,
        "source": "user",
        # NEW: Preset suggestion fields
        "suggested_presets": suggested_presets,
        "unmapped_models": unmapped_models,
    }
```

**Step 4: Run test to verify it passes**

Run: `cd /app && PYTHONPATH=/app pytest tests/unit/test_workflow_scanner.py::test_scan_workflow_includes_suggested_presets -v`
Expected: PASS

**Step 5: Commit**

```bash
git add dashboard/core/workflow_scanner.py tests/unit/test_workflow_scanner.py
git commit -m "feat: include suggested_presets in scan_workflow output"
```

---

## Task 5: Update Registry Sync to Pull model_index.json

**Files:**
- Modify: `dashboard/api/presets.py`
- Create: `tests/unit/test_presets_api.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_presets_api.py
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, AsyncMock
import pytest

from dashboard.api.presets import sync_registry

@pytest.mark.asyncio
async def test_sync_registry_downloads_model_index():
    """Test that registry sync also downloads model_index.json."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_path = Path(tmpdir) / "data"
        data_path.mkdir()

        # Mock the fetch function
        with patch('dashboard.api.presets.fetch_github_json') as mock_fetch:
            mock_fetch.side_effect = AsyncMock(side_effect=[
                {"presets": {"FLUX_DEV": {"name": "FLUX Dev"}}},  # registry
                {"mappings": {"checkpoints/flux-dev.safetensors": "FLUX_DEV"}},  # model_index
            ])

            with patch('dashboard.api.presets.MODEL_INDEX_PATH', data_path / "model_index.json"):
                with patch('dashboard.api.presets.REGISTRY_PATH', data_path / "registry.json"):
                    result = await sync_registry()

                    assert result["status"] == "synced"
                    assert mock_fetch.call_count == 2
```

**Step 2: Run test to verify it fails**

Run: `cd /app && PYTHONPATH=/app pytest tests/unit/test_presets_api.py::test_sync_registry_downloads_model_index -v`
Expected: FAIL

**Step 3: Update registry sync endpoint**

```python
# dashboard/api/presets.py - add constants at top of file

MODEL_INDEX_URL = "https://raw.githubusercontent.com/ZeroClue/comfyui-presets/main/model_index.json"
MODEL_INDEX_PATH = Path("/workspace/data/model_index.json")

# Update existing sync_registry function
@router.post("/registry/sync")
async def sync_registry():
    """
    Sync preset registry and model index from GitHub.
    Downloads both registry.json and model_index.json.
    """
    results = {
        "registry": None,
        "model_index": None,
        "errors": []
    }

    # Download registry.json
    try:
        registry_data = await fetch_github_json(REGISTRY_URL)
        REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(REGISTRY_PATH, 'w') as f:
            json.dump(registry_data, f)
        results["registry"] = {
            "status": "synced",
            "presets": len(registry_data.get("presets", {}))
        }
    except Exception as e:
        results["errors"].append(f"Registry sync failed: {str(e)}")

    # Download model_index.json
    try:
        index_data = await fetch_github_json(MODEL_INDEX_URL)
        with open(MODEL_INDEX_PATH, 'w') as f:
            json.dump(index_data, f)
        results["model_index"] = {
            "status": "synced",
            "mappings": len(index_data.get("mappings", {}))
        }
    except Exception as e:
        # Non-fatal - model index is optional
        results["errors"].append(f"Model index sync failed: {str(e)}")

    return {
        "status": "synced" if not results["errors"] else "partial",
        **results
    }
```

**Step 4: Run test to verify it passes**

Run: `cd /app && PYTHONPATH=/app pytest tests/unit/test_presets_api.py::test_sync_registry_downloads_model_index -v`
Expected: PASS

**Step 5: Commit**

```bash
git add dashboard/api/presets.py tests/unit/test_presets_api.py
git commit -m "feat: sync model_index.json with registry"
```

---

## Task 6: Add UI for Preset Suggestions in generate.html

**Files:**
- Modify: `dashboard/templates/generate.html`

**Step 1: Add preset suggestions panel**

Find the existing "Model Requirements Panel" comment (around line 190) and add after the existing model display code:

```html
<!-- Preset Suggestions Panel (for user/comfyui workflows with missing models) -->
<div x-show="selectedWorkflow?.id === workflow.id &&
             workflow.source !== 'library' &&
             (workflow.suggested_presets?.length || workflow.unmapped_models?.length)"
     class="mt-3 pt-3 border-t border-border-primary">

    <h4 class="text-sm font-medium text-text-secondary mb-2">Required Models</h4>

    <!-- Suggested Presets -->
    <template x-for="preset in workflow.suggested_presets" :key="preset.preset_id">
        <div class="flex items-center justify-between py-1.5">
            <div class="flex items-center gap-2">
                <span x-show="preset.installed" class="text-accent-success">✓</span>
                <span x-show="!preset.installed" class="text-accent-warning">⚠</span>
                <div>
                    <div class="text-sm" x-text="preset.preset_name"></div>
                    <div class="text-xs text-text-tertiary" x-text="preset.model_file"></div>
                </div>
            </div>
            <div>
                <span x-show="preset.installed" class="text-xs text-accent-success">Installed</span>
                <button x-show="!preset.installed"
                        @click.stop="installPreset(preset.preset_id)"
                        class="px-2 py-1 text-xs bg-accent-primary text-white rounded hover:opacity-80">
                    <span x-text="preset.download_size || 'Install'"></span>
                </button>
            </div>
        </div>
    </template>

    <!-- Unmapped Models (no preset found) -->
    <template x-for="model in workflow.unmapped_models" :key="model">
        <div class="flex items-center justify-between py-1.5 bg-bg-tertiary rounded px-2 mt-1">
            <div class="flex items-center gap-2">
                <span class="text-text-tertiary">?</span>
                <span class="text-sm text-text-secondary" x-text="model"></span>
            </div>
            <span class="text-xs text-text-tertiary">Manual download required</span>
        </div>
    </template>

    <!-- Install All & Generate Button -->
    <div class="mt-4 flex justify-end gap-2">
        <button x-show="hasMissingUserPresets(workflow)"
                @click.stop="installAllUserPresets(workflow)"
                class="px-3 py-1.5 text-sm bg-accent-warning text-white rounded hover:opacity-80 flex items-center gap-1">
            <span>↓</span>
            <span>Install Missing & Generate</span>
        </button>
        <button x-show="workflow.ready"
                @click.stop="selectAndGenerate(workflow)"
                class="px-4 py-2 text-sm bg-accent-primary text-white rounded hover:opacity-80">
            Generate
        </button>
    </div>
</div>
```

**Step 2: Update status badges**

Find the existing status badge (around line 149) and update:

```html
<!-- Status Badge -->
<span x-show="workflow.ready"
      class="px-2 py-0.5 text-xs rounded-full bg-accent-success/20 text-accent-success">
    Ready
</span>
<span x-show="!workflow.ready && workflow.suggested_presets?.filter(p => !p.installed).length"
      class="px-2 py-0.5 text-xs rounded-full bg-accent-warning/20 text-accent-warning">
    <span x-text="workflow.suggested_presets?.filter(p => !p.installed).length"></span> presets needed
</span>
<span x-show="!workflow.ready && workflow.unmapped_models?.length && !workflow.suggested_presets?.length"
      class="px-2 py-0.5 text-xs rounded-full bg-accent-error/20 text-accent-error">
    <span x-text="workflow.unmapped_models.length"></span> manual
</span>
```

**Step 3: Commit**

```bash
git add dashboard/templates/generate.html
git commit -m "feat: add preset suggestions UI to generate page"
```

---

## Task 7: Add JavaScript Helpers

**Files:**
- Modify: `dashboard/templates/generate.html`

**Step 1: Add helper functions to generatePage()**

Find the `generatePage()` Alpine component and add these methods:

```javascript
// Add inside generatePage() return block, after existing methods

hasMissingUserPresets(workflow) {
    return workflow.suggested_presets?.some(p => !p.installed);
},

async installAllUserPresets(workflow) {
    const missing = workflow.suggested_presets?.filter(p => !p.installed) || [];
    if (missing.length === 0) return;

    this.isInstalling = true;
    try {
        for (const preset of missing) {
            const response = await fetch('/api/presets/install', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({preset_id: preset.preset_id})
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `Failed to install ${preset.preset_name}`);
            }
        }

        window.showToast('success', 'Downloads Started',
            `Installing ${missing.length} preset${missing.length > 1 ? 's' : ''}`);

        // Refresh workflow to update status
        await this.loadWorkflows();

    } catch (error) {
        window.showToast('error', 'Install Failed', error.message);
    } finally {
        this.isInstalling = false;
    }
},

async installPreset(presetId) {
    try {
        const response = await fetch('/api/presets/install', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({preset_id: presetId})
        });

        if (response.ok) {
            window.showToast('success', 'Download Started', 'Preset installation queued');
            await this.loadWorkflows();
        } else {
            const error = await response.json();
            window.showToast('error', 'Install Failed', error.detail);
        }
    } catch (error) {
        window.showToast('error', 'Install Failed', error.message);
    }
},
```

**Step 2: Commit**

```bash
git add dashboard/templates/generate.html
git commit -m "feat: add installAllUserPresets helper for preset suggestions"
```

---

## Task 8: Run All Tests and Final Verification

**Step 1: Run all workflow scanner tests**

Run: `cd /app && PYTHONPATH=/app pytest tests/unit/test_workflow_scanner.py -v`
Expected: All tests PASS

**Step 2: Run all preset API tests**

Run: `cd /app && PYTHONPATH=/app pytest tests/unit/test_presets_api.py -v`
Expected: All tests PASS

**Step 3: Verify changes**

```bash
git status
git log --oneline -8
```

**Step 4: Push to remote**

```bash
git push -u origin feature/preset-suggestions
```

**Step 5: Create PR**

```bash
gh pr create --title "feat: Workflow Preset Suggestions" --body "..."
```

---

## Summary

| Task | Description | Files Changed |
|------|-------------|---------------|
| 1 | Set up worktree | - |
| 2 | Add model index loading | workflow_scanner.py, test_workflow_scanner.py |
| 3 | Add resolve_model_to_preset | workflow_scanner.py, test_workflow_scanner.py |
| 4 | Update scan_workflow | workflow_scanner.py, test_workflow_scanner.py |
| 5 | Update registry sync | presets.py, test_presets_api.py |
| 6 | Add preset suggestions UI | generate.html |
| 7 | Add JavaScript helpers | generate.html |
| 8 | Final verification and push | - |

---

## External Dependency

This feature requires `model_index.json` to be generated in the `comfyui-presets` repository. The bot that generates `registry.json` should also output:

```json
{
  "version": "1.0.0",
  "mappings": {
    "checkpoints/{filename}": "PRESET_ID",
    ...
  }
}
```

Until this is available, the feature gracefully degrades (no preset suggestions shown).
