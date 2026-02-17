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
gh run watch --interval 30s

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
- **base** (~8-12GB): ComfyUI + Manager + custom nodes + dev tools
- **slim** (~4-5GB): ComfyUI + Manager, optimized for serving

**CUDA Support**: 12.4, 12.5, 12.6, 12.8, 12.9, 13.0. Matrix builds defined in `docker-bake.hcl`.

# Architecture Overview

## Multi-Stage Docker Build System
The project uses a sophisticated multi-stage build (`Dockerfile`):
- **Builder Stage**: Compiles PyTorch, builds heavy dependencies using UV package manager
- **Runtime Stage**: Production-optimized final image with minimal footprint
- **Matrix Builds**: Supports multiple CUDA versions and image variants via `docker-bake.hcl`

## Revolutionary Architecture
Apps are baked into container image at `/app/`. Models live on network volume at `/workspace/`.

**Container Volume** (ephemeral, baked in image):
- `/app/dashboard/`: Unified Dashboard (FastAPI + htmx)
- `/app/preset_manager/`: Preset management system
- `/venv/`: Python virtual environment
- `/ComfyUI/`: ComfyUI application

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
- `/workspace/ComfyUI/models/`: Target model storage directory
- `/scripts/preset_manager/templates/`: Web UI templates

## Core Services Architecture
**Container orchestration via `scripts/start.sh`:**
- **Unified Dashboard (port 8082)**: PRIMARY INTERFACE - FastAPI + htmx, replaces Preset Manager/Studio
- ComfyUI (port 3000): Main AI generation interface
- Preset Manager (port 9000): Web-based preset management (DISABLED if Unified Dashboard enabled)
- Code Server (port 8080): VS Code development environment
- JupyterLab (port 8888): Notebook interface
- Nginx: Reverse proxy for service routing

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
- `ENABLE_UNIFIED_DASHBOARD`: Enable/disable Unified Dashboard (default: true). When enabled, Preset Manager and Studio are automatically disabled.
- `ENABLE_PRESET_MANAGER`: Enable/disable preset manager web UI (default: true)
- `ACCESS_PASSWORD`: Password for web interfaces (code-server, Jupyter, preset manager)
- `ENABLE_CODE_SERVER`: Enable/disable VS Code server (default: true)
- `TIME_ZONE`: Container timezone (default: Etc/UTC)
- `FORCE_SYNC_ALL`: Force full resync of venv and ComfyUI on startup (default: false)

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
    "imageName": "zeroclue/comfyui:minimal-py3.13-cu128",
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
- ✅ Correct: `zeroclue/comfyui:minimal-py3.13-cu128`
- ❌ Wrong: `zeroclue/comfyui:minimal-py313-cu128`

## Container Ports
- **8082**: Unified Dashboard (PRIMARY INTERFACE - FastAPI + htmx + Alpine.js)
- **Internal**: Runs on port 8000 inside container (for debugging)
- **3000**: ComfyUI main interface
- **8080**: VS Code server (if enabled)
- **8888**: JupyterLab notebook interface
- **9000**: Preset Manager web UI (being replaced by dashboard)
- **22**: SSH access

## Service Port Conflicts (CRITICAL)

**IMPORTANT:** Unified Dashboard runs on **external port 8082**, not 8081.
- Port 8081 is used by code-server (proxies to 8080)
- Dashboard runs internally on port 8000
- If dashboard shows README page, check: `curl http://localhost:8000/` from inside the pod
- **Preset Manager is DISABLED automatically when Unified Dashboard is enabled** (both use port 8000)

## Dashboard Startup Requirements

**PYTHONPATH Configuration**:
The dashboard requires `/scripts` in Python path for imports:
```bash
export PYTHONPATH="/scripts:/app:$PYTHONPATH"
```

**Module Execution**:
Dashboard runs as Python module (not direct script):
```bash
cd /app/dashboard
python3 -m main  # Required for relative imports
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

## Model Path Structure
All models are installed to `/workspace/ComfyUI/models/` with standardized paths:
- `checkpoints/`: Main model files (diffusion models, FLUX, etc.)
- `text_encoders/`: T5, CLIP-L, and other text encoders
- `vae/`: Variational autoencoders
- `clip_vision/`: Image encoders for I2V workflows
- `audio_encoders/`: Audio processing models
- `loras/`: LoRA adapters and enhancement models
- `upscale_models/`: Image upscaling models
- you can always ask to connect to the runpod cpu node by asking for the ssh connection
- runpod documentation for building docker images: https://docs.runpod.io/tutorials/pods/build-docker-images
- example github repository for building docker images on runpod: https://github.com/therealadityashankar/build-docker-in-runpod.git