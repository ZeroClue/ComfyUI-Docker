# Workflow Model Availability System Design

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Close the loop between workflow requirements and actual generation by detecting missing models, mapping them to presets, and providing clear installation paths.

**Problem:** Users can sync workflows from ComfyUI and try to generate, but generation fails silently because required models aren't installed. The generate page shows workflows as "ready" without checking model availability.

**Solution:** Detect model requirements from workflows, check if they're installed, map to presets when available, and provide clear installation paths.

---

## Architecture

### Data Flow

```
1. Workflow Scan
   └─> Extract model filenames from nodes + widgets_values
   └─> Fallback to MarkdownNote parsing

2. Availability Check
   └─> For each model, check /workspace/models/{type}/{filename}
   └─> Build installed/missing list

3. Preset Matching
   └─> For missing models, search preset registry for matches
   └─> Attach preset info + download action

4. Generate Page Display
   └─> Show readiness status on workflow cards
   └─> Expandable model requirements panel
   └─> Install/Request buttons for missing models

5. User Action
   └─> Install preset → existing download queue
   └─> Request preset → GitHub issue
   └─> Manual install → re-scan button
```

---

## Components

### 1. Model Extraction (workflow_scanner.py)

**Detection sources (priority order):**

1. **Standard loader nodes** - Check `inputs` dict for `.safetensors`, `.pt`, `.pth`, `.bin`, `.ckpt` values
2. **Packed/composite nodes** - Check `widgets_values` array for model filenames
3. **MarkdownNote fallback** - Regex parse for model URLs/filenames (only if 1 & 2 yield nothing)

**Output:** List of `{filename, model_type, source}` where:
- `filename`: e.g., `z_image_turbo_bf16.safetensors`
- `model_type`: `diffusion_models`, `text_encoders`, `vae`, `loras`, `checkpoints`, etc.
- `source`: `inputs`, `widgets_values`, or `markdown`

### 2. Availability Checker (workflow_scanner.py)

**Model type inference from directory structure:**
- `checkpoints/` → CheckpointLoader nodes
- `diffusion_models/` → UNETLoader nodes
- `text_encoders/` → CLIPLoader nodes
- `vae/` → VAELoader nodes
- `loras/` → LoraLoader nodes

**Check logic:**
```python
def check_model_availability(required_models: List[str]) -> Dict[str, Any]:
    # Search each standard directory for the filename
    for model_type in ["checkpoints", "diffusion_models", "text_encoders", "vae", "loras"]:
        path = f"/workspace/models/{model_type}/{filename}"
        if exists(path):
            return {"installed": True, "path": path, "type": model_type}

    # Not found - infer type from filename patterns
    return {"installed": False, "type": infer_type_from_filename(filename)}
```

### 3. Preset Matcher (generate.py or new module)

**Preset matching:**
```python
def find_preset_for_model(filename: str) -> Optional[PresetInfo]:
    for preset in presets:
        for file in preset.files:
            if file.path.endswith(filename):
                return {
                    "preset_id": preset.id,
                    "preset_name": preset.name,
                    "download_size": preset.download_size
                }
    return None
```

### 4. User Actions

**Action types for missing models:**

| Action | When | Implementation |
|--------|------|----------------|
| One-click install | Model has preset | Trigger preset download via existing queue |
| Manual install | No preset, known type | Show expected path + re-scan button |
| Request preset | No preset available | Link to GitHub issue template |

**GitHub issue template URL:**
```
https://github.com/ZeroClue/comfyui-presets/issues/new?title=Add preset for {model_name}&body=Model: {model_name}%0AType: {model_type}%0AWorkflow: {workflow_id}
```

---

## API Changes

### Enhanced `/api/generate/workflows/synced`

```json
{
  "workflows": [
    {
      "id": "image_z_image_turbo",
      "name": "image_z_image_turbo",
      "description": "",
      "category": "imported",
      "path": "imported/image_z_image_turbo.json",
      "node_count": 3,
      "input_types": [],
      "output_types": ["image"],
      "ready": false,
      "model_status": {
        "total": 3,
        "installed": 1,
        "missing": 2,
        "with_presets": 1
      },
      "models": [
        {
          "name": "z_image_turbo_bf16.safetensors",
          "installed": false,
          "type": "diffusion_models",
          "preset": {
            "id": "Z_IMAGE_TURBO",
            "name": "Z Image Turbo",
            "download_size": "14.5GB"
          },
          "actions": {
            "install": "/api/presets/Z_IMAGE_TURBO/install",
            "manual_path": "/workspace/models/diffusion_models/",
            "request_preset_url": "https://github.com/ZeroClue/comfyui-presets/issues/new?..."
          }
        },
        {
          "name": "qwen_3_4b.safetensors",
          "installed": false,
          "type": "text_encoders",
          "preset": null,
          "actions": {
            "install": null,
            "manual_path": "/workspace/models/text_encoders/",
            "request_preset_url": "https://github.com/ZeroClue/comfyui-presets/issues/new?..."
          }
        },
        {
          "name": "ae.safetensors",
          "installed": true,
          "type": "vae",
          "preset": null,
          "actions": null
        }
      ]
    }
  ],
  "categories": {"imported": 1},
  "total": 1
}
```

### New: `GET /api/generate/workflows/{id}/models`

Returns detailed model availability for a specific workflow.

---

## UI Changes

### Workflow Card Status

1. **Status indicator** - Show workflow readiness at a glance:
   - ✅ Ready (all models installed)
   - ⚠️ 2 models needed (click to expand)
   - ❓ Unknown (no model requirements detected)

2. **Model requirements panel** - Expandable section showing:
   - List of required models with status badges (installed/missing)
   - Install buttons for models with presets
   - "Request preset" links for models without presets
   - "Start generation anyway" option for advanced users

---

## Files to Modify

| File | Changes |
|------|---------|
| `dashboard/core/workflow_scanner.py` | Enhance model extraction from nodes + widgets_values; Add availability checker |
| `dashboard/api/generate.py` | Add preset matching logic; Enhance workflow response with model status |
| `dashboard/templates/generate.html` | UI for readiness status + model requirements panel |

---

## Implementation Notes

- Model extraction should handle both UI format (nodes array) and API format (node dict)
- `widgets_values` model detection: look for strings ending in model extensions
- MarkdownNote parsing: regex for `.safetensors`, `.pt`, `.pth`, `.bin`, `.ckpt` in text
- Cache preset registry lookup for performance
- Consider lazy-loading detailed model info (only on card expansion)
