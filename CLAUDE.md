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

## Unified Dashboard
FastAPI-based unified interface replacing Preset Manager and Studio.

**Location**: `/app/dashboard/`

**Structure**:
- `main.py`: FastAPI application entry point
- `api/`: REST API endpoints (workflows, models, presets, system)
- `core/`: ComfyUI client, configuration, WebSocket manager
- `templates/`: htmx + Alpine.js UI templates
- `static/`: Tailwind CSS, JavaScript assets

**Key Features**:
- Workflow execution via ComfyUI API integration
- Model and preset management
- Real-time progress tracking via WebSocket
- System status monitoring

**API Endpoints**:
- `POST /api/workflows/execute` - Execute ComfyUI workflow
- `GET /api/workflows/history` - View execution history
- `GET /api/workflows/queue/status` - Monitor queue
- `GET /api/models` - List installed models
- `GET /api/presets` - List available presets

## Preset Management System
Located in `scripts/preset_manager/` with three core components:

1. **core.py**: ModelManager class handling CRUD operations for 56+ presets
2. **web_interface.py**: Flask web UI on port 9000 for visual preset management
3. **config.py**: Configuration mappings and model path definitions

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

## Important Files
- `Dockerfile`: Multi-stage build definition with UV optimization
- `docker-bake.hcl`: Build matrix configuration for all variants
- `scripts/start.sh`: Container entrypoint and service orchestration
- `dashboard/main.py`: FastAPI application entry point for Unified Dashboard
- `dashboard/api/`: REST API endpoints (workflows.py, models.py, presets.py, system.py)
- `dashboard/core/comfyui_client.py`: ComfyUI API integration for workflow execution
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

```bash
# List all pods
source .runpod/.env && curl -s "https://rest.runpod.io/v1/pods" -H "Authorization: Bearer $RUNPOD_API_KEY"

# Get pod details
source .runpod/.env && curl -s "https://rest.runpod.io/v1/pods/{pod-id}" -H "Authorization: Bearer $RUNPOD_API_KEY"

# Stop a pod
source .runpod/.env && curl -X POST "https://rest.runpod.io/v1/pods/{pod-id}/stop" -H "Authorization: Bearer $RUNPOD_API_KEY"

# Terminate a pod
source .runpod/.env && curl -X POST "https://rest.runpod.io/v1/pods/{pod-id}/terminate" -H "Authorization: Bearer $RUNPOD_API_KEY"
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

## Dashboard Module Structure

The dashboard runs as a Python module from `/app`:
```bash
cd /app && PYTHONPATH=/app uvicorn dashboard.main:app --host 0.0.0.0 --port 8000
```

**Key files:**
- `dashboard/main.py`: FastAPI application entry point
- `dashboard/core/websocket.py`: WebSocket handlers for real-time updates
- `dashboard/core/config.py`: Settings (MODEL_BASE_PATH=/workspace/models)
- `dashboard/core/comfyui_client.py`: ComfyUI REST API client
- `dashboard/api/*.py`: REST API endpoints

**API Endpoints:**
- `/api/dashboard/stats` - Home page statistics
- `/api/models/presets` - Presets with installation status (for Models page)
- `/api/models/` - Installed model files
- `/api/workflows/` - Workflow management
- `/api/presets/` - Preset download management
- `/api/system/` - System status and resources
- `/api/generate` - Content generation endpoint

**Page Routes:**
- `/` - Home dashboard
- `/generate` - Content generation interface
- `/models` - Model preset management
- `/workflows` - Workflow library
- `/settings` - Settings page
- `/pro` - Pro features

**Startup command in start.sh:**
```bash
cd /app && PYTHONPATH=/app /app/venv/bin/python3 -m uvicorn dashboard.main:app --host 0.0.0.0 --port 8000
```

**Feature Status**:
- ✅ Preset management (downloads, status)
- ✅ Model listing/validation with installation status
- ✅ Workflow execution via ComfyUI API
- ✅ System monitoring (CPU, memory, disk, GPU)
- ✅ WebSocket real-time updates
- ✅ Dashboard stats (connected to real data)
- ✅ Page routes (/generate, /models, /workflows, /settings, /pro)
- ❌ Gallery view (not implemented)

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