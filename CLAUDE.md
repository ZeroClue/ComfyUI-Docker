# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Build System & Commands

## Docker Build Commands
```bash
# Build specific variants locally
docker buildx bake base-13-0  # CUDA 13.0 (default, :latest tag)
docker buildx bake base-12-8  # CUDA 12.8 (known-good fallback)
docker buildx bake slim-12-8  # Production optimized

# Build and push all variants
docker buildx bake --push

# Trigger GitHub Actions build (preferred over local builds)
gh workflow run build.yml

# Trigger specific variant
gh workflow run build.yml -f targets=base -f cuda_versions=13-0

# Watch build progress
gh run watch --interval 30

# Test preset configuration
python scripts/preset_validator.py

# Test download functionality
python scripts/test_preset_system.py

# Preview download scripts
python scripts/generate_download_scripts.py

# Update preset configurations from GitHub
python scripts/preset_updater.py update
```

## Image Variants & Matrix Builds
- **base** (~8-12GB): ComfyUI + Manager + custom nodes + dev tools (ONLY VARIANT CURRENTLY BUILT)

**CUDA Support**: 12.4, 12.5, 12.6, 12.8, 12.9, 13.0. Matrix builds defined in `docker-bake.hcl`.

**Active CI Builds** (both build every run):
- `base-13-0`: CUDA 13.0 + PyTorch 2.11.0 — `:latest` tag, Blackwell-native
- `base-12-8`: CUDA 12.8 + PyTorch 2.11.0 — known-good fallback

**Note**: slim and minimal variants temporarily disabled in GitHub Actions while focusing on base stability.

# Architecture Overview

## Multi-Stage Docker Build System
The project uses a 4-stage multi-stage build (`Dockerfile`):
- **Stage 1 (builder-base)**: Ubuntu + CUDA + UV package manager
- **Stage 2 (python-deps)**: Python venv with PyTorch, dependencies, SageAttention
- **Stage 3 (comfyui-core)**: ComfyUI + Manager + custom nodes
- **Stage 4 (runtime)**: Minimal runtime image with artifacts from previous stages
- **Matrix Builds**: Supports multiple CUDA versions and image variants via `docker-bake.hcl`

## Container vs Volume Layout
Apps are baked into container image at `/app/`. Models live on network volume at `/workspace/`.

**Container Volume** (ephemeral, baked in image):
- `/app/dashboard/`: Unified Dashboard (FastAPI + htmx)
- `/app/preset_manager/`: Preset management system
- `/app/venv/`: Python virtual environment
- `/app/comfyui/`: ComfyUI application

**Network Volume** (persistent, attached at `/workspace`):
- `/workspace/models/`: All model files (checkpoints, VAE, LoRA, etc.)
- `/workspace/output/`: Generated content
- `/workspace/workflows/`: User workflow files
- `/workspace/uploads/`: User uploads
- `/workspace/config/`: User configuration

## Persistence Layer

SQLite database at `/workspace/data/dashboard.db` provides persistent storage across pod restarts.

**Database Tables:**
- `settings`: Key-value store for user preferences (theme, HF token, retention days)
- `activity`: Activity log with 30-day auto-cleanup (generations, downloads, errors)
- `download_history`: Permanent record of download operations

**Key Files:**
- `dashboard/core/database.py`: SQLite connection, schema, query helpers
- `dashboard/core/persistence.py`: SettingsManager, ActivityLogger, DownloadHistory classes

**CRITICAL Import Pattern:**
Persistence globals (`settings_manager`, `activity_logger`) are initialized at startup. Import the module, not the variable:
```python
# WRONG - binds to None at import time
from ..core.persistence import settings_manager

# CORRECT - accesses runtime value
from ..core import persistence
persistence.settings_manager.get("key")
```

## Unified Dashboard
FastAPI-based unified interface replacing Preset Manager and Studio.

**Location**: `/app/dashboard/`

### Home Page Data Sources
All sections use real API data (no mockups):
- **Stats Grid**: `/api/dashboard/stats`
- **Download Queue**: `/api/presets/queue/status` + WebSocket `/ws/downloads`
- **System Resources**: `/api/system/resources` (10s auto-refresh)
- **Recent Models**: `/api/presets/?limit=6` (installed first, then available)
- **Recent Activity**: `/api/activity/recent` (combined generations + downloads)

**Structure**:
- `main.py`: FastAPI application entry point
- `api/`: REST API endpoints (workflows, models, presets, system)
- `core/`: ComfyUI client, configuration, WebSocket manager, downloader
- `templates/`: htmx + Alpine.js UI templates
- `static/`: Tailwind CSS, JavaScript assets

**Key Features**:
- Workflow execution via ComfyUI API integration
- Model and preset management with download queue
- Real-time progress tracking via WebSocket (`/ws/dashboard`)
- System status monitoring

**API Endpoints** (non-obvious ones — standard CRUD at `/api/models/`, `/api/system/`, etc.):
- `POST /api/generate/start` - Queue workflow for execution, returns prompt_id
- `POST /api/generate/{prompt_id}/cancel` - Interrupt running execution
- `POST /api/workflows/queue/delete/{prompt_id}` - Delete pending item from ComfyUI queue
- `POST /api/presets/registry/sync` - Pull registry.json + model_index.json from GitHub
- `POST /api/llm/enhance` - Optional prompt enhancement via local LLM

**Page Routes**:
- `/` - Home dashboard
- `/generate` - Content generation interface
- `/models` - Model preset management
- `/workflows` - Workflow library
- `/gallery` - Gallery for viewing generated content
- `/settings` - Settings page
- `/pro` - Pro features

## Generate Page

All-in-one workflow consumer with:
- **Workflow-First UI**: Card-based browser with metadata
- **Intent-Based Entry**: Pattern-matched shortcuts
- **Real-Time Progress**: Hybrid WebSocket + REST polling
- **Optional LLM**: Prompt enhancement via local models (Phi-3, Qwen, Llama)

**Backend Components:**
- `dashboard/core/workflow_scanner.py`: Scan workflows, extract metadata
- `dashboard/core/intent_matcher.py`: Pattern-match intent to workflows
- `dashboard/core/generation_manager.py`: Track generations, WebSocket broadcast
- `dashboard/core/llm_service.py`: Optional LLM for prompt enhancement
- `dashboard/api/generate.py`: Generate API endpoints
- `dashboard/api/llm.py`: LLM management endpoints

**Design Docs:** `docs/plans/2026-02-21-generate-page-*.md`

## LLM Integration

Optional prompt enhancement via local LLM models (Phi-3, Qwen, Llama).

**API Endpoint:** `POST /api/llm/enhance`
- Request: `{ prompt, style, model }`
- Response: `{ success, enhanced_prompt }`

**Styles:** detailed, cinematic, artistic, minimal

**Settings:** Configure via `/settings` - `llm_enabled`, `llm_model`

**Fallback:** When LLM disabled or fails, uses static enhancement (quality modifiers)

## Workflow Preset Suggestions

Suggest presets for missing models in user workflows.

**Architecture:**
- **model_index.json**: Maps model filenames → preset IDs (bot-generated in comfyui-presets repo)
- **Sync**: Pulled with registry.json via `/api/presets/registry/sync`
- **Runtime**: WorkflowScanner resolves models → suggested presets

**Key Methods:**
- `WorkflowScanner.resolve_model_to_preset()` - Maps filename to preset info
- `WorkflowScanner._check_model_installed()` - Verifies model exists on disk

**UI:** User workflow cards show suggested presets with install buttons for missing models.

**Edge Cases:**
- Model not in any preset → Added to `unmapped_models`, shows "Manual download required"
- model_index.json not synced → Returns empty mapping, shows sync prompt

## Legacy Preset Manager
Located in `scripts/preset_manager/` — superseded by Unified Dashboard. Still used by CLI tools (`core.py`, `web_interface.py`, `config.py`).

## Preset Registry System

The preset system now uses a **separate repository**: [comfyui-presets](https://github.com/ZeroClue/comfyui-presets)

**Architecture:**
- **Centralized Management**: Single bot scans for model version changes
- **Distributed Consumption**: Pods pull registry.json (no local scanning)
- **Dual Format Support**: Dashboard reads both old `presets.yaml` and new registry format

**Key Endpoints:**
- `GET /api/presets/registry/sync` - Pull latest registry from GitHub
- `GET /api/presets/registry/status` - Check sync status

**Registry Location:** `/workspace/data/registry.json`

**For preset development**, work in the separate repo:
```bash
cd /home/arminm/projects/qwen-image/comfyui-presets
python scripts/validate.py          # Validate preset schema
python scripts/generate_registry.py # Rebuild registry.json
python scripts/check_urls.py        # Health check all URLs
```

## Triple Preset Architecture
The system supports three independent model categories defined in `config/presets.yaml`:

1. **Video Generation** (PRESET_DOWNLOAD): WAN, LTX, Hunyuan, Cosmos models (26 presets)
2. **Image Generation** (IMAGE_PRESET_DOWNLOAD): SDXL, FLUX, Qwen models (25 presets)
3. **Audio Generation** (AUDIO_PRESET_DOWNLOAD): MusicGen, Bark, TTS models (5 presets)

Each preset contains complete model definitions with URLs, sizes, file paths, and dependencies.

## Key Directory Structure
- `/scripts/`: Startup orchestration, preset management, validation tools
- `/config/`: YAML preset configurations, schemas, and migration utilities
- `/proxy/`: Nginx reverse proxy for service routing
- `/workspace/models/`: Target model storage directory (network volume)
- `/scripts/preset_manager/templates/`: Web UI templates

## Static Assets
- **Favicon**: `dashboard/static/favicon.png` (ZeroClue logo)
- **Screenshots**: `docs/screenshots/unified-dashboard/` and `docs/screenshots/legacy/`
- Linked in `base.html` with proper icon declarations

## Core Services Architecture
**Container orchestration via `scripts/start.sh`:**
- **Unified Dashboard (port 8082)**: PRIMARY INTERFACE - FastAPI + htmx, replaces Preset Manager/Studio
- ComfyUI (port 3000): Main AI generation interface
- Preset Manager (port 9000): Web-based preset management (DISABLED if Unified Dashboard enabled)
- Code Server (port 8080): VS Code development environment
- JupyterLab (port 8888): Notebook interface
- Nginx: Reverse proxy for service routing

## Attention Optimization (SageAttention)
**SageAttention 2.2.0** is compiled from source during build for optimal inference speed:
- **2x faster** than FlashAttention2 on RTX 4090
- **2.7x faster** on RTX 5090
- **CUDA 12.x**: Full CUDA kernel compilation
- **CUDA 13.0+**: Falls back to ComfyUI-Attention-Optimizer

Installation handled by `scripts/install_sageattention.sh` during python-deps stage.

**CRITICAL**: Do NOT use editable install (`pip install -e .`) for SageAttention. The script deletes the source directory after install, which would break an editable install. Use regular install (`pip install .`).

**GPU Architectures (SM versions):**
- SM 8.0: A100
- SM 8.6: RTX 3090, A6000
- SM 8.9: RTX 4090, L40, RTX 4000/2000 Ada
- SM 9.0: H100, H800
- SM 12.0: RTX 5090, B200 (Blackwell)

**CI Build Requirements (CRITICAL):**
GitHub Actions runners have ~14GB RAM and no GPU. SageAttention builds require:
- `FORCE_CUDA=1` - Prevents GPU auto-detection failure
- `MAX_JOBS=2` - Prevents memory exhaustion during compilation
- `TORCH_CUDA_ARCH_LIST` - Space-separated SM versions (not semicolons)

If build fails at ~50min with runner communication loss, reduce parallelism further.

## Preset Configuration Schema
Defined in `config/presets.yaml`. Each preset has: `name`, `category` (Video/Image/Audio), `type`, `download_size`, `files` (with `path`, `url`, `size`), `use_case`, `tags`.

## Automated Build Pipeline
GitHub Actions workflow (`.github/workflows/build.yml`) provides:
- Matrix builds across CUDA versions (12.4-13.0)
- Automatic Docker Hub pushes for successful builds
- Manual build triggers for large variants
- Build status monitoring and reliability optimization

**Known Issue**: GitHub Actions runners have ~14GB disk space. Large builds may fail with
"No space left on device" error. Solution: Retry the build - different runners may have
more free space. Successful builds typically take 25-30 minutes.

## Important Files
- `Dockerfile`: Multi-stage build definition with UV optimization
- `docker-bake.hcl`: Build matrix configuration for all variants
- `scripts/start.sh`: Container entrypoint and service orchestration
- `dashboard/main.py`: FastAPI application entry point for Unified Dashboard
- `dashboard/api/`: REST API endpoints (workflows.py, models.py, presets.py, system.py, settings.py, activity.py)
- `dashboard/core/comfyui_client.py`: ComfyUI API integration for workflow execution
- `dashboard/core/database.py`: SQLite database connection and schema
- `dashboard/core/persistence.py`: SettingsManager, ActivityLogger, DownloadHistory classes
- `dashboard/core/downloader.py`: Background download manager with HF token support
- `scripts/preset_manager/core.py`: Main preset management logic and ModelManager class
- `config/presets.yaml`: Central preset configuration (currently 56 presets)
- `scripts/preset_updater.py`: GitHub-based preset updating system
- `scripts/unified_preset_downloader.py`: Unified download system for all preset types

# Environment Configuration

## Key Environment Variables
- `PRESET_DOWNLOAD`: Video generation models to install (comma-separated)
- `IMAGE_PRESET_DOWNLOAD`: Image generation models to install (comma-separated)
- `AUDIO_PRESET_DOWNLOAD`: Audio generation models to install (comma-separated)
- `ENABLE_UNIFIED_DASHBOARD`: Enable/disable Unified Dashboard (default: true)
- `ENABLE_PRESET_MANAGER`: Enable/disable preset manager web UI (auto-disabled when dashboard enabled)
- `ACCESS_PASSWORD`: Password for web interfaces (code-server, Jupyter, dashboard)
- `ENABLE_CODE_SERVER`: Enable/disable VS Code server (default: true)
- `TIME_ZONE`: Container timezone (default: Etc/UTC)

**User Settings** (configured via Settings page, stored in SQLite):
- `HF Token`: HuggingFace token for downloading gated models (configure at `/settings`)
- `Theme`: Dark/light theme preference

## RunPod Deployment

### Setup
```bash
# Configure API key (one-time)
echo "RUNPOD_API_KEY=your_key_here" > .runpod/.env
```

### Deploy Pod
```bash
# Source environment and deploy
# GPU preference: RTX 2000 Ada > RTX 4000 Ada > RTX 4090
# Region: EU-RO-1 recommended (better CUDA 13.0+ driver support)
source .runpod/.env && curl -X POST "https://rest.runpod.io/v1/pods" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "comfyui-dashboard",
    "imageName": "zeroclue/comfyui:base-py3.13-cu130",
    "computeType": "GPU",
    "gpuTypeIds": ["NVIDIA RTX 2000 Ada Generation"],
    "dataCenterIds": ["EU-RO-1"],
    "volumeInGb": 100,
    "networkVolumeId": "your-volume-id",
    "ports": ["3000/http", "8082/http", "22/tcp"],
    "supportPublicIp": true
  }'
```

### Image Tag Format
**CRITICAL:** Image tags use DOTS in Python version: `py3.13` NOT `py313`
- ✅ Correct: `zeroclue/comfyui:base-py3.13-cu130`
- ❌ Wrong: `zeroclue/comfyui:base-py313-cu130`

## Container Ports
- **8082**: Unified Dashboard (PRIMARY INTERFACE - FastAPI + htmx + Alpine.js)
- **Internal**: Runs on port 8000 inside container (for debugging)
- **3000**: ComfyUI main interface
- **8080**: VS Code server (if enabled)
- **8888**: JupyterLab notebook interface
- **9000**: Preset Manager web UI (auto-disabled when Unified Dashboard enabled)
- **22**: SSH access

## Service Port Conflicts (CRITICAL)

**IMPORTANT:** Unified Dashboard runs on **external port 8082**, not 8081.
- Port 8081 is used by code-server (proxies to 8080)
- Dashboard runs internally on port 8000
- If dashboard shows README page, check: `curl http://localhost:8000/` from inside the pod
- **Preset Manager Auto-Disable**: When `ENABLE_UNIFIED_DASHBOARD` is enabled (default), Preset Manager is automatically disabled to prevent port 8000 conflict. To explicitly enable Preset Manager, set `ENABLE_PRESET_MANAGER=true` (not recommended when using Unified Dashboard).

## Dashboard Startup Requirements

**Module Execution**:
Dashboard runs as a Python module from `/app`:
```bash
cd /app && PYTHONPATH=/app /app/venv/bin/python -m dashboard.main
```

Or with uvicorn:
```bash
cd /app && PYTHONPATH=/app /app/venv/bin/uvicorn dashboard.main:app --host 0.0.0.0 --port 8000
```

## Unified Dashboard Authentication

**Default credentials** (when ACCESS_PASSWORD not set):
- Username: `admin`
- Password: `admin`

**Custom password**: Set `ACCESS_PASSWORD` environment variable

## RunPod Proxy URL Format

Direct IP access doesn't work on RunPod. Use proxy URL format:
```
https://{pod-id}-{port}.proxy.runpod.net/

Example: https://8myhxhyx0ojmq4-8082.proxy.runpod.net/
```

## RunPod Pod Management

API key in `.runpod/.env`. Use GraphQL (`https://api.runpod.io/graphql`) for queries (volumes, GPUs), REST (`https://rest.runpod.io/v1/pods`) for CRUD. Always verify pod status after stop.

# Development & Testing

## Build Debugging
- Check `.github/workflows/build.yml` for matrix configuration
- Review `docker-bake.hcl` for target definitions and CUDA variants
- Monitor GitHub Actions build logs for disk space and timeout issues
- Use manual workflow triggers for specific variants

## Debugging Dependencies

When adding Python dependencies to the Dockerfile:
- Check official ComfyUI requirements.txt: https://raw.githubusercontent.com/comfyanonymous/ComfyUI/master/requirements.txt
- Add missing imports to the "Install ComfyUI requirements" section (around line 119 in Dockerfile)
- Rebuild and test on RunPod CPU pod first (cheaper) before GPU testing

**Note**: ComfyUI-specific packages (comfyui-frontend-package, comfyui-workflow-templates, comfy-aimdo, etc.) must be manually added as they're not in standard PyPI.

## RunPod CPU Debugging

For dependency/startup debugging (no GPU needed):
- Use `computeType: "CPU"` in pod deployment
- Costs ~$0.05-0.10/hour vs $0.24/hour for GPU
- Use for: import errors, missing dependencies, container startup
- Switch to GPU only for final workflow testing

### SSH Log Inspection
```bash
# Connect to pod and inspect logs
ssh root@<pod-ip> -p <ssh-port> -i ~/.ssh/id_ed25519
tail -f /workspace/logs/*.log
cat /workspace/logs/comfyui.log | grep -i error
```

## Core ComfyUI Dependencies (Must-Have)

These packages are required for ComfyUI to start:
- **Core**: aiohttp, yarl, alembic, einops, scipy, psutil, SQLAlchemy
- **ComfyUI-specific**: comfyui-frontend-package, comfyui-workflow-templates, comfyui-embedded-docs, comfy-kitchen, comfy-aimdo, av, torchsde
- **Additional**: tokenizers, sentencepiece, safetensors, kornia, spandrel, pydantic

## Known Custom Node Import Failures (Expected)

Only these custom nodes are expected to fail (require heavy/proprietary dependencies):
- **ComfyUI_TensorRT**: Requires NVIDIA TensorRT SDK (not included in base image)
- **ComfyUI_LayerStyle (dzNodes)**: `guidedFilter` not available in current OpenCV version

All other custom nodes should load successfully with the included dependencies.

## Additional Dependency Warnings

These packages are commonly missing but cause warnings in custom nodes:
- `pydantic-settings` - Required by some custom nodes for config parsing
- `simpleeval` - Required by efficiency-nodes-comfyui

Add to Dockerfile if custom node warnings appear during startup.

## Model Path Structure
All models are installed to `/workspace/models/` with standardized paths:
- `checkpoints/`: Main model files (diffusion models, FLUX, etc.)
- `text_encoders/`: T5, CLIP-L, and other text encoders
- `vae/`: Variational autoencoders
- `clip_vision/`: Image encoders for I2V workflows
- `audio_encoders/`: Audio processing models
- `loras/`: LoRA adapters and enhancement models
- `upscale_models/`: Image upscaling models

## Design Documentation

Major features have design docs in `docs/plans/`:
- `2026-02-18-preset-system-design.md` - Preset system architecture
- `2026-02-18-preset-system-implementation.md` - Implementation tasks (17 bite-sized tasks)

These documents are gitignored but tracked with `git add -f`.

## Dashboard Known Issues

**Known Limitations:**
- ComfyUI does not support pause/resume — only interrupt/cancel. No pause endpoint exposed.
- Gated HuggingFace models require HF token (configure in Settings)
- **Workflow formats**: Only API format workflows can be executed (dict with node IDs as keys, not the `nodes` array format). UI format must be exported via ComfyUI > Dev Mode > "Export (API Format)".
- **Strip `_meta` keys** before sending workflows — ComfyUI rejects them.

**Alpine.js Script Loading:**
Load Alpine.js at end of `<body>`, AFTER `{% block extra_scripts %}` — not with `defer`. Inline scripts must define functions before Alpine initializes.

## Performance Optimizations

### PresetCache System
- **60-second TTL cache** for preset API responses to avoid repeated file I/O
- **Batch installation checks** avoids timeout on large model lists
- **Cache invalidation** triggered on download complete and preset delete
- Location: `dashboard/api/presets.py` - `PresetCache` class

## ComfyUI Queue API

Queue items are arrays: `[number, prompt_id, prompt, extra_data, outputs_to_execute]`.
Use `item[1]` for prompt_id. ComfyUI supports interrupt (`POST /interrupt`) and delete
(`POST /queue` with `{"delete": [prompt_id]}`), but NOT pause/resume.

Frontend queue card polls `GET /api/workflows/queue/status` every 3 seconds. Interval
cleanup via `@alpine:destroyed` on the Alpine root element.

## Docker Tag Versioning

CI resolves latest git tag via `git describe --tags --abbrev=0` and passes it as `EXTRA_TAG`
to docker-bake. The `tag()` function produces both floating (`base-py3.13-cu130`) and pinned
(`base-py3.13-cu130-v1.3.0`) tags when EXTRA_TAG is set. `:latest` tag points to the CUDA 13.0
build. HCL supports ternary in functions.

## Dockerfile Gotchas

**ARGs in FROM must be global scope**: Docker only resolves ARGs in `FROM` if declared *before*
the first `FROM`. ARGs inside a build stage work for `RUN` commands but not `FROM`. Put
`BASE_IMAGE` and `RUNTIME_BASE_IMAGE` at the top of the Dockerfile.

**Quote pip version pins with `<` or `>`**: In Dockerfile `RUN pip install`, unquoted
`starlette<1.0.0` is interpreted as a shell redirect. Use `"starlette<1.0.0"`.

**Pin starlette<1.0.0**: Starlette 1.0.0 broke Jinja2 template caching (`TypeError: unhashable
type: 'dict'`). The dashboard fails on every page load with 1.0.0+.

**ComfyUI-Attention-Optimizer is NOT on PyPI**: It's a custom node (git clone), not a pip
package. `install_sageattention.sh` must skip gracefully for CUDA 13+ instead of trying
`pip install`. Add it to `custom_nodes.txt` instead.

## Network Volume Sharing with Serverless

Pod mounts volume at `/workspace`, serverless endpoints mount at `/runpod-volume` (same disk).
Models live at `{mount}/models/` on the volume. Serverless `start.sh` symlinks
`/comfyui/models/X` → `/runpod-volume/models/X`. Pod uses `/workspace/models/` directly.
Shared models (e.g. `clip/qwen_2.5_vl_7b_fp8_scaled.safetensors`, `vae/qwen_image_vae.safetensors`)
download once, reused by both endpoints.

## Dashboard Development Gotchas

**Alpine.js v3, not v2**: The CDN loads Alpine v3. Use `Alpine.$data(el)` not `app.__x.$data`.
Loops use `<template x-for="item in items" :key="item.id">` not `v-for` (that's Vue.js).

**Jinja2 autoescape is enabled**: `templates.env.autoescape = True` in main.py. Use `| tojson`
for JS string interpolation in x-data attributes, not raw `{{ }}`.

**Single ConnectionManager in core/websocket.py**: All WebSocket endpoints use one manager with
channel routing. Do not create separate connection sets in other modules.

**Database uses persistent SQLite connection**: `execute_commit()` returns `lastrowid` directly.
Don't call `last_insert_rowid()` on a separate query — it returns 0 on a different connection.

**Run blocking calls in executors**: `psutil.cpu_percent()`, `subprocess.run`, SHA256 hashing,
and SQLite writes are synchronous. Wrap in `loop.run_in_executor(None, ...)` or use
`asyncio.create_subprocess_exec` to avoid blocking the event loop.

**Path validation required**: Any user-supplied path must be resolved and checked against
allowed prefixes. Use `Path(path).resolve()` + `startswith(base_path.resolve())`.