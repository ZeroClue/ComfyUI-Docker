# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Dockerized ComfyUI distribution that provides a complete AI image generation environment. The project builds Docker images with ComfyUI, ComfyUI Manager, and optional pre-installed custom nodes, designed for RunPod cloud deployment but also usable locally. The repository is maintained by ZeroClue organization and builds automatically every 8 hours.

## Architecture

### Docker Build System
- **Dockerfile**: Multi-stage build that installs Python 3.13, PyTorch 2.8.0, ComfyUI, and optional custom nodes
- **docker-bake.hcl**: Defines build targets for multiple CUDA versions (12.4-13.0) and two variants:
  - `base`: Includes 23 pre-installed custom nodes
  - `slim`: Only ComfyUI + Manager (no custom nodes)
- **custom_nodes.txt**: List of custom node repositories for base images

### Container Services
The container runs multiple services exposed on different ports:
- **Port 3000**: ComfyUI (main AI image generation interface)
- **Port 8080**: code-server (VS Code-like web editor)
- **Port 8888**: JupyterLab (notebook environment)
- **Port 22**: SSH (if PUBLIC_KEY environment variable is set)
- **Port 3001/8081/8889**: Nginx reverse proxies for the above services

### Key Scripts
- **/start.sh**: Main entrypoint that starts all services (nginx, SSH, JupyterLab, code-server)
- **/pre_start.sh**: Runs environment setup, workspace synchronization, optional SageAttention2 installation
- **/post_start.sh**: Launches ComfyUI with configurable arguments
- **/download_presets.sh**: Downloads pre-defined model presets from HuggingFace
- **/install_custom_nodes.sh**: Installs custom nodes from custom_nodes.txt

### Model Management
Models are organized in `/workspace/ComfyUI/models/` with subdirectories:
- `checkpoints/`: Main AI models
- `diffusion_models/`: Custom diffusion models (e.g., WanVideo)
- `text_encoders/`: Text encoder models
- `vae/`: VAE models
- `loras/`: LoRA adaptation models
- `upscale_models/`: Image upscaling models

### Workspace Architecture
The container uses a two-phase startup where content from `/venv/` and `/ComfyUI/` is synced to `/workspace/` for persistent storage. This allows updates while preserving user data.

## Common Development Tasks

### Building Images
```bash
# Build specific variant and CUDA version using docker bake
docker bake base-12-6    # Build base image with CUDA 12.6
docker bake slim-12-8    # Build slim image with CUDA 12.8

# List all available targets
docker bake --list

# Build and push
docker bake base-12-6 --push
```

### Local Development
```bash
# Basic run with GPU support
docker run --gpus all -p 3000:3000 sombi/comfyui:base-torch2.8.0-cu126

# With password protection for web interfaces
docker run --gpus all -p 3000:3000 -e ACCESS_PASSWORD=mypassword sombi/comfyui:base-torch2.8.0-cu126

# With preset model downloads
docker run --gpus all -p 3000:3000 -e PRESET_DOWNLOAD=WAN22_I2V_A14B_GGUF_Q8_0,UPSCALE_MODELS sombi/comfyui:base-torch2.8.0-cu126

# With SageAttention2 optimization (Ampere+ GPUs only)
docker run --gpus all -p 3000:3000 -e INSTALL_SAGEATTENTION=True sombi/comfyui:base-torch2.8.0-cu126
```

### Environment Variables
Key environment variables for configuration:
- `ACCESS_PASSWORD`: Sets password for JupyterLab and code-server
- `COMFYUI_EXTRA_ARGS`: Additional command-line arguments for ComfyUI
- `TIME_ZONE`: Set container timezone (e.g., `Asia/Seoul`)
- `INSTALL_SAGEATTENTION`: Install SageAttention2 optimization (`True`/`False`)
- `INSTALL_CUSTOM_NODES`: Install additional custom nodes at runtime (`True`/`False`)
- `PRESET_DOWNLOAD`: Comma-separated list of model presets to download
- `PUBLIC_KEY`: SSH public key for remote access

### Preset Downloads
Use the preset system for automatic model downloads:
```bash
# Inside container
bash /download_presets.sh WAN22_I2V_A14B_GGUF_Q8_0,WAN22_LIGHTNING_LORA

# Available presets include:
# WAN video models: WAN22_I2V_A14B_GGUF_Q8_0, WAN22_T2V_A14B, WAN22_TI2V_5B
# Image models: WAINSFW_V140, NTRMIX_V40
# Enhancements: WAN22_LIGHTNING_LORA, WAN22_NSFW_LORA
# Utilities: UPSCALE_MODELS
```

### Custom Node Management
For slim images or to add custom nodes:
1. Nodes can be installed via ComfyUI Manager web interface
2. Or manually clone to `/workspace/ComfyUI/custom_nodes/`
3. Each custom node may have additional requirements.txt files that are auto-installed during build

## Image Tagging Convention
Images follow the format: `sombi/comfyui:{variant}-torch{version}-{cuda}`
- Variants: `base` (with custom nodes) or `slim` (minimal)
- PyTorch version: `2.8.0`
- CUDA versions: `cu124`, `cu126`, `cu128`, `cu129`, `cu130`

## Pre-installed Custom Nodes (Base Images)
The base image includes 23 custom nodes covering:
- Video generation: ComfyUI-WanVideoWrapper, ComfyUI-Frame-Interpolation
- Model optimization: ComfyUI-GGUF, ComfyUI-TensorRT, ComfyUI-MultiGPU
- Image processing: ComfyUI_UltimateSDUpscale, ComfyUI-Image-Saver
- Workflow enhancement: efficiency-nodes, rgthree-comfy, ComfyUI-Easy-Use
- Development tools: ComfyUI-Impact-Pack, comfy-ex-tagcomplete

## Logs Location
- ComfyUI: `/workspace/ComfyUI/user/comfyui_3000.log`
- code-server: `/workspace/logs/code-server.log`
- JupyterLab: `/workspace/logs/jupyterlab.log`

## Key File Locations
- **proxy/**: Nginx configuration for reverse proxy setup
- **scripts/**: Container startup and utility scripts
- **custom_nodes.txt**: Source repositories for custom nodes (base images only)
- All custom nodes install to `/workspace/ComfyUI/custom_nodes/`
- Workspace is at `/workspace/` with persistent storage for models and outputs

## Development Workflow
1. Modify `docker-bake.hcl` to change registry or add new build targets
2. Update `custom_nodes.txt` to modify pre-installed nodes
3. Add new presets to `scripts/download_presets.sh` for custom model downloads
4. Use environment variables to control runtime behavior
5. All persistent data is stored in `/workspace/` directory