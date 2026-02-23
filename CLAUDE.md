# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Build System & Commands

## Docker Build Commands
```bash
# Build specific variants locally
docker buildx bake base-12-6  # Full installation with custom nodes
docker buildx bake slim-12-6  # Production optimized

# Build and push all variants
docker buildx bake --push

# Trigger GitHub Actions build (preferred over local builds)
gh workflow run build.yml

# Trigger specific variant
gh workflow run build.yml -f targets=minimal -f cuda_versions=12-8

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

**Note**: slim and minimal variants temporarily disabled in GitHub Actions while focusing on base stability.

# Architecture Overview

## Multi-Stage Docker Build System
The project uses a 4-stage multi-stage build (`Dockerfile`):
- **Stage 1 (builder-base)**: Ubuntu + CUDA + UV package manager
- **Stage 2 (python-deps)**: Python venv with PyTorch, dependencies, SageAttention
- **Stage 3 (comfyui-core)**: ComfyUI + Manager + custom nodes
- **Stage 4 (runtime)**: Minimal runtime image with artifacts from previous stages
- **Matrix Builds**: Supports multiple CUDA versions and image variants via `docker-bake.hcl`

## Revolutionary Architecture
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

**Key Benefits**:
- No rsync needed → instant startup
- Easy updates → replace container, keep models
- Follows 12-factor app principles
- Native RunPod architecture alignment

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

**API Endpoints:**
- `GET /api/settings` - Get settings (HF token masked)
- `PATCH /api/settings` - Update setting
- `POST /api/settings/hf-token` - Save HF token
- `POST /api/settings/hf-token/validate` - Validate token against HuggingFace API
- `GET /api/activity/recent` - Get activity log
- `POST /api/activity/clear` - Clear activity history

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

**API Endpoints**:
- `/api/dashboard/stats` - Home page statistics
- `/api/activity/recent` - Combined activity feed (generations + downloads)
- `/api/activity/clear` - Clear activity history
- `/api/models/` - List installed models
- `/api/models/presets` - Presets with installation status
- `/api/presets/` - Preset management (list, refresh, install, pause, cancel)
- `/api/presets/queue/status` - Download queue status
- `/api/presets/refresh` - Fetch latest presets.yaml from GitHub
- `/api/workflows/` - Workflow management and execution
- `/api/system/status` - System health check
- `/api/system/resources` - CPU, memory, disk, GPU usage
- `/api/generate` - Content generation endpoint
- `/api/presets/recommendations` - Filter presets by GPU VRAM compatibility
- `/api/presets/updates` - Check for preset version updates
- `/api/presets/registry/sync` - Sync from remote registry.json

**Page Routes**:
- `/` - Home dashboard
- `/generate` - Content generation interface
- `/models` - Model preset management
- `/workflows` - Workflow library
- `/gallery` - Gallery for viewing generated content
- `/settings` - Settings page
- `/pro` - Pro features

**Feature Status**:
- ✅ Preset management (downloads, status)
- ✅ Model listing/validation with installation status
- ✅ Workflow execution via ComfyUI API
- ✅ System monitoring (CPU, memory, disk, GPU)
- ✅ System metrics: Container-aware memory (cgroups), workspace disk usage (du)
- ✅ WebSocket real-time updates
- ✅ Dashboard stats (connected to real data)
- ✅ Page routes (/generate, /models, /workflows, /gallery, /settings, /pro)
- ✅ Gallery view (implemented 2026-02-19)
- ✅ Persistence layer - SQLite database for settings, activity, history (2026-02-20)
- ✅ HF token support for gated model downloads (2026-02-20)
- ✅ Per-file download progress display (2026-02-20)
- ✅ Download pause/resume functionality (2026-02-20)
- ✅ HTTP error messages (401 auth, 403 license, 404 not found) (2026-02-20)
- ✅ Workflow Registry System - dual-source workflows, preset linking, disk space checks (2026-02-22)
- ✅ ComfyUI Bridge - workflow execution via /api/generate endpoint (2026-02-22)
- ✅ LLM Integration - prompt enhancement with style selector (2026-02-22)
- ✅ Workflow Preset Suggestions - model-to-preset mapping for user workflows (2026-02-23)

## Generate Page Redesign (2026-02-21)

Redesigned as all-in-one workflow consumer with:
- **Workflow-First UI**: Card-based browser with metadata
- **Intent-Based Entry**: Pattern-matched shortcuts
- **Real-Time Progress**: Hybrid WebSocket + REST polling
- **Optional LLM**: Prompt enhancement via local models (Phi-3, Qwen, Llama)

**New Backend Components:**
- `dashboard/core/workflow_scanner.py`: Scan workflows, extract metadata
- `dashboard/core/intent_matcher.py`: Pattern-match intent to workflows
- `dashboard/core/generation_manager.py`: Track generations, WebSocket broadcast
- `dashboard/core/llm_service.py`: Optional LLM for prompt enhancement
- `dashboard/api/generate.py`: Generate API endpoints
- `dashboard/api/llm.py`: LLM management endpoints

**Design Docs:** `docs/plans/2026-02-21-generate-page-*.md`

## LLM Integration (2026-02-22)

Optional prompt enhancement via local LLM models (Phi-3, Qwen, Llama).

**API Endpoint:** `POST /api/llm/enhance`
- Request: `{ prompt, style, model }`
- Response: `{ success, enhanced_prompt }`

**Styles:** detailed, cinematic, artistic, minimal

**Settings:** Configure via `/settings` - `llm_enabled`, `llm_model`

**Fallback:** When LLM disabled or fails, uses static enhancement (quality modifiers)

## Workflow Preset Suggestions (2026-02-23)

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

## Preset Management System
Located in `scripts/preset_manager/` with three core components:

1. **core.py**: ModelManager class handling CRUD operations for 56+ presets
2. **web_interface.py**: Flask web UI on port 9000 for visual preset management
3. **config.py**: Configuration mappings and model path definitions

## Preset Registry System (2026-02-20)

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
cd /mnt/wsl/SharedData/projects/comfyui-presets
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
```yaml
presets:
  PRESET_ID:
    name: Display Name
    category: Video Generation|Image Generation|Audio Generation
    type: video|image|audio
    description: Model description
    download_size: 14.5GB
    files:
      - path: checkpoints/model.safetensors
        url: https://huggingface.co/...
        size: 4.8GB
    use_case: Primary use case
    tags: [tag1, tag2]
```

## Automated Build Pipeline
GitHub Actions workflow (`.github/workflows/build.yml`) provides:
- Matrix builds across CUDA versions (12.4-13.0)
- Automatic Docker Hub pushes for successful builds
- Manual build triggers for large variants (base-12-8)
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
# Region: EU-RO-1 recommended (better CUDA 12.8+ driver support)
source .runpod/.env && curl -X POST "https://rest.runpod.io/v1/pods" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "comfyui-dashboard",
    "imageName": "zeroclue/comfyui:base-py3.13-cu128",
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
- ✅ Correct: `zeroclue/comfyui:base-py3.13-cu128`
- ❌ Wrong: `zeroclue/comfyui:base-py313-cu128`

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
cd /app && PYTHONPATH=/app python3 -m dashboard.main
```

Or with uvicorn:
```bash
cd /app && PYTHONPATH=/app uvicorn dashboard.main:app --host 0.0.0.0 --port 8000
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

**GraphQL API** (preferred for queries):
```bash
# Query network volumes
source .runpod/.env && curl -s "https://api.runpod.io/graphql" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -d '{"query": "{ myself { networkVolumes { id name size dataCenter { id } } } }"}'

# Query available GPUs
source .runpod/.env && curl -s "https://api.runpod.io/graphql" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -d '{"query": "{ gpuTypes { id displayName memoryInGb } }"}'
```

**REST API** (for pod creation/deletion):
```bash
# List all pods
source .runpod/.env && curl -s "https://rest.runpod.io/v1/pods" -H "Authorization: Bearer $RUNPOD_API_KEY"

# Get pod details
source .runpod/.env && curl -s "https://rest.runpod.io/v1/pods/{pod-id}" -H "Authorization: Bearer $RUNPOD_API_KEY"

# Stop a pod
source .runpod/.env && curl -X POST "https://rest.runpod.io/v1/pods/{pod-id}/stop" -H "Authorization: Bearer $RUNPOD_API_KEY"

# Terminate (delete) a pod
source .runpod/.env && curl -X DELETE "https://rest.runpod.io/v1/pods/{pod-id}" -H "Authorization: Bearer $RUNPOD_API_KEY"
```

# Development & Testing

## Preset System Validation
```bash
# Validate preset configuration syntax and completeness
python scripts/preset_validator.py

# Test download functionality and URL availability
python scripts/test_preset_system.py

# Generate and preview download scripts for debugging
python scripts/generate_download_scripts.py

# Update preset configurations from GitHub (runtime updates)
python scripts/preset_updater.py update
```

## Preset Management Tools
```bash
# Command-line preset management
python scripts/preset_manager_cli.py list
python scripts/preset_manager_cli.py install WAN_22_5B_TIV2
python scripts/preset_manager_cli.py status

# Unified downloader with environment variable support
python scripts/unified_preset_downloader.py download
python scripts/unified_preset_downloader.py list
python scripts/unified_preset_downloader.py status
```

## Build Debugging
- Check `.github/workflows/build.yml` for matrix configuration
- Review `docker-bake.hcl` for target definitions and CUDA variants
- Monitor GitHub Actions build logs for disk space and timeout issues
- Use manual workflow triggers for large variants (base-12-8 requires manual build)

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

## Dashboard Known Issues (2026-02-22)

All major dashboard features working. See Feature Status section for details.

**Known Limitations:**
- Generate page queue card not connected to ComfyUI queue (UI only)
- Gated HuggingFace models require HF token (configure in Settings)
- **Workflow formats**: Only API format workflows can be executed via dashboard. UI format workflows with subgraphs require manual export from ComfyUI.

**Workflow Format Requirements:**
ComfyUI's `/prompt` endpoint requires **API format** workflows (dict with node IDs as keys):
```json
// API format (WORKS)
{
  "1": {"class_type": "KSampler", "inputs": {...}},
  "2": {"class_type": "CLIPTextEncode", "inputs": {...}}
}

// UI format (DOES NOT WORK - has "nodes" array)
{
  "nodes": [{"id": 1, "type": "KSampler", ...}],
  "links": [...]
}
```

To convert UI format to API format:
1. Open workflow in ComfyUI
2. Enable Dev Mode in Settings
3. Click "Export (API Format)" from menu
4. Save the exported workflow

**Alpine.js Script Loading:**
Alpine.js must load AFTER page-specific function definitions. Load it at end of `<body>`:
```html
<!-- WRONG - defer causes race condition with inline scripts -->
<script defer src="alpine.js"></script>
{% block extra_scripts %}{% endblock %}

<!-- CORRECT - Alpine loads after all page functions defined -->
{% block extra_scripts %}{% endblock %}
<script src="alpine.js"></script>
```

## Performance Optimizations (2026-02-19)

### PresetCache System
- **60-second TTL cache** for preset API responses to avoid repeated file I/O
- **Batch installation checks** avoids timeout on large model lists
- **Cache invalidation** triggered on download complete and preset delete
- Location: `dashboard/api/presets.py` - `PresetCache` class

## Bug Fixes & Learnings (Consolidated)

### 2026-02-22
- **Workflow format handling**: ComfyUI `/prompt` endpoint only accepts API format workflows. UI format (with `nodes` array) must be exported as API format from ComfyUI. Workflows with subgraphs (composite nodes) cannot be directly executed.
- **Strip `_meta` keys**: ComfyUI rejects workflows with `_meta` keys at root level. Strip them before sending: `{k: v for k, v in workflow.items() if not k.startswith("_")}`
- **Prompt injection**: Only replace positive prompts, preserve negative prompts. Check for "negative" in node title before replacing text in CLIPTextEncode nodes.
- **Alpine.js initialization**: Alpine must load AFTER inline script definitions. Do not use `defer` on Alpine script if it's at end of body - the inline scripts need to define functions before Alpine initializes.

### 2026-02-21
- **Subprocess security**: Always use `shutil.which()` to resolve executable paths before `subprocess.run()` - prevents shell injection
- **Semantic versioning**: Use `packaging.version.parse()` for version comparisons, not string comparison
- **SHA256 chunk size**: Use 1MB chunks (not 8KB) for hashing large model files - significantly faster
- **SHA256 validation**: Validate hash format is 64 hex characters before comparison
- **Constant extraction**: Extract repeated URLs to module-level constants (e.g., `REMOTE_REGISTRY_URL`)
- **GitHub raw content-type**: GitHub raw URLs return `text/plain; charset=utf-8` instead of `application/json`. Use `response.text()` + `json.loads()` instead of `response.json()`.
- **Alpine.js variable initialization**: Variables used in templates (modelCount, gpuUsage, memoryUsage, unreadCount) must be declared in dashboardApp() with initial values and fetched via API in fetchSidebarStats().
- **Favicon 404**: Add favicon.ico to dashboard/static/ to prevent console errors.
- **Lazy initialization for settings-dependent services**: Services like WorkflowScanner that need settings values at init time should use lazy initialization via getter functions. Module-level initialization can happen before settings are loaded, causing path resolution failures.
  ```python
  # WRONG - settings.WORKFLOW_BASE_PATH may not be set yet
  _workflow_scanner = WorkflowScanner(Path(settings.WORKFLOW_BASE_PATH))

  # CORRECT - lazy initialization
  _workflow_scanner = None
  def get_workflow_scanner():
      global _workflow_scanner
      if _workflow_scanner is None:
          _workflow_scanner = WorkflowScanner(Path(settings.WORKFLOW_BASE_PATH))
      return _workflow_scanner
  ```
- **Alpine.js null safety**: Use optional chaining (`?.`) and nullish coalescing (`||`) when accessing potentially null objects in templates:
  ```html
  <!-- WRONG - crashes if intentResult is null -->
  <span x-text="intentResult.matched_keyword"></span>

  <!-- CORRECT - safe null handling -->
  <span x-text="intentResult?.matched_keyword || ''"></span>
  ```

### 2026-02-20
- **Runtime imports for globals**: Persistence globals (`settings_manager`, `activity_logger`) are None at module load time. Import the module (`from ..core import persistence`) and access the attribute at runtime (`persistence.settings_manager`), not the variable directly.
- **FastAPI router prefixes**: Avoid duplicate prefixes. If router has `prefix="/activity"` and `include_router()` also has `prefix="/activity"`, the route becomes `/api/activity/activity/recent`. Only define prefix in one place.
- **Asyncio.Queue lazy init**: Create queues inside async context, not at class instantiation time (no event loop yet). Use property with lazy initialization.
- **Download pause bug**: When pausing download, the loop breaks but code continues to set `status="completed"`. Add explicit check for pause/cancel status before marking complete.
- **Container memory metrics**: `psutil.virtual_memory()` returns host memory in containers. Read from `/sys/fs/cgroup/memory.max` (cgroup v2) or `/sys/fs/cgroup/memory/memory.limit_in_bytes` (cgroup v1) for container limit.
- **Network volume disk metrics**: `psutil.disk_usage('/workspace')` returns host filesystem size on RunPod network volumes. Use `du -sb /workspace` for actual usage and `RUNPOD_VOLUME_GB` env var for total size.
- **add_activity() signature**: Only supports `activity_type`, `status`, `title`, `subtitle`, `details`. Does NOT support `link` parameter - will raise TypeError if passed.

### 2026-02-19
- **FastAPI route ordering**: Literal routes must come BEFORE parameterized routes. `/queue/status` must be defined before `/{preset_id}/status` or FastAPI matches `preset_id="queue"`
- **psutil.version_info**: It's a tuple, not namedtuple. Use `sys.version_info` for Python version
- **activity.py current**: `get_queue_status()` returns `current` as string (preset_id), not dict with properties

### 2026-02-18
- **psutil.uname()**: Use `.sysname` not `.system` (posix.uname_result has no 'system' attribute)
- **WebSocket endpoint**: Dashboard templates expect `/ws/dashboard`, not just `/ws`
- **Dashboard port**: Internal port 8000, external 8082 (via nginx)
- **Pydantic validation**: Preset `files` and `categories` need `Dict[str, Any]` not `Dict[str, str]` (preset YAML has boolean `optional: false` and nested category objects)

### RunPod Pod Management
**CRITICAL**: Always verify pod status after stop command:
```bash
# Stop pod
curl -X POST "https://rest.runpod.io/v1/pods/{pod-id}/stop" -H "Authorization: Bearer $RUNPOD_API_KEY"

# Verify it stopped (check desiredStatus = "EXITED")
curl -s "https://rest.runpod.io/v1/pods/{pod-id}" -H "Authorization: Bearer $RUNPOD_API_KEY"
```

### CPU Pod Debugging
CPU pods require `--cpu` flag for ComfyUI to disable GPU check:
```bash
# ComfyUI won't start on CPU pods without this flag
python main.py --cpu --listen 0.0.0.0
```

### Communication Pattern
Use ntfy for user notifications during long-running tasks:
```bash
# Send notification via MCP tool
mcp__ntfy-me-mcp-extended__ntfy_me(taskTitle="Build Complete", taskSummary="...")

# Ask question with action buttons
mcp__ntfy-me-mcp-extended__ntfy_me_ask(question="Continue?", options=["Yes", "No"])
```