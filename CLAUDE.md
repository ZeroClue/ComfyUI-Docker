# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Dockerized ComfyUI distribution maintained by ZeroClue organization that provides a complete AI image generation environment. The project builds Docker images with ComfyUI, ComfyUI Manager, and optional pre-installed custom nodes, designed for RunPod cloud deployment but also usable locally. Images are built automatically via GitHub Actions and can be built manually using Docker Bake.

## Architecture

### Docker Build System
- **Dockerfile**: Multi-stage build that installs Python 3.13, PyTorch 2.8.0, ComfyUI, and optional custom nodes
- **docker-bake.hcl**: Defines build targets for multiple CUDA versions (12.4-13.0) and three variants:
  - `base`: Includes 23 pre-installed custom nodes
  - `slim`: Only ComfyUI + Manager (no custom nodes)
  - `minimal`: ComfyUI + Manager only (no custom nodes, no code-server)
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
- **/download_presets.sh**: Downloads video generation model presets from HuggingFace
- **/download_image_presets.sh**: Downloads image generation model presets from HuggingFace
- **/download_audio_presets.sh**: Downloads audio generation model presets from HuggingFace
- **/install_custom_nodes.sh**: Installs custom nodes from custom_nodes.txt

### Model Management
Models are organized in `/workspace/ComfyUI/models/` with subdirectories:
- `checkpoints/`: Main AI models
- `diffusion_models/`: Custom diffusion models (e.g., WanVideo)
- `text_encoders/`: Text encoder models
- `vae/`: VAE models
- `loras/`: LoRA adaptation models
- `upscale_models/`: Image upscaling models
- `audio_encoders/`: Audio encoder models (for S2V)
- `TTS/`: Text-to-speech models
- `audio/`: Music and audio generation models

### Workspace Architecture
The container uses a two-phase startup where content from `/venv/` and `/ComfyUI/` is synced to `/workspace/` for persistent storage. This allows updates while preserving user data. Smart sync optimization avoids unnecessary resyncs by checking file integrity and modification times.

## Common Development Tasks

### Building Images
```bash
# Build specific variant and CUDA version using docker bake
docker bake base-12-6    # Build base image with CUDA 12.6
docker bake slim-12-8    # Build slim image with CUDA 12.8
docker bake minimal-12-8 # Build minimal image with CUDA 12.8

# List all available targets
docker bake --list

# Build and push
docker bake base-12-6 --push
```

### Local Development
```bash
# Basic run with GPU support
docker run --gpus all -p 3000:3000 zeroclue/comfyui:base-torch2.8.0-cu126

# With password protection for web interfaces
docker run --gpus all -p 3000:3000 -e ACCESS_PASSWORD=mypassword zeroclue/comfyui:base-torch2.8.0-cu126

# With video generation preset downloads
docker run --gpus all -p 3000:3000 -e PRESET_DOWNLOAD=WAN_22_5B_TIV2,WAN_22_LIGHTNING_LORA zeroclue/comfyui:base-torch2.8.0-cu126

# With image generation preset downloads
docker run --gpus all -p 3000:3000 -e IMAGE_PRESET_DOWNLOAD=SDXL_BASE_V1,REALISTIC_VISION_V6 zeroclue/comfyui:base-torch2.8.0-cu126

# With both image and video generation presets
docker run --gpus all -p 3000:3000 \
  -e IMAGE_PRESET_DOWNLOAD=SDXL_BASE_V1 \
  -e PRESET_DOWNLOAD=WAN_22_5B_TIV2 \
  zeroclue/comfyui:base-torch2.8.0-cu126

# With audio generation preset downloads
docker run --gpus all -p 3000:3000 -e AUDIO_PRESET_DOWNLOAD=MUSICGEN_MEDIUM,BARK_BASIC zeroclue/comfyui:base-torch2.8.0-cu126

# With image, video, and audio generation presets (complete multimedia)
docker run --gpus all -p 3000:3000 \
  -e IMAGE_PRESET_DOWNLOAD=SDXL_BASE_V1,REALISTIC_VISION_V6 \
  -e AUDIO_PRESET_DOWNLOAD=MUSICGEN_MEDIUM,BARK_BASIC \
  -e PRESET_DOWNLOAD=WAN_22_5B_TIV2 \
  zeroclue/comfyui:base-torch2.8.0-cu126

# With SageAttention2 optimization (Ampere+ GPUs only)
docker run --gpus all -p 3000:3000 -e INSTALL_SAGEATTENTION=True zeroclue/comfyui:base-torch2.8.0-cu126

# Force full resync of workspace
docker run --gpus all -p 3000:3000 -e FORCE_SYNC_ALL=True zeroclue/comfyui:base-torch2.8.0-cu126
```

### Environment Variables
Key environment variables for configuration:
- `ACCESS_PASSWORD`: Sets password for JupyterLab and code-server
- `ENABLE_CODE_SERVER`: Enable/disable code-server (`True`/`False`, default: `True`)
- `COMFYUI_EXTRA_ARGS`: Additional command-line arguments for ComfyUI
- `TIME_ZONE`: Set container timezone (e.g., `Asia/Seoul`)
- `INSTALL_SAGEATTENTION`: Install SageAttention2 optimization (`True`/`False`)
- `INSTALL_CUSTOM_NODES`: Install additional custom nodes at runtime (`True`/`False`)
- `PRESET_DOWNLOAD`: Comma-separated list of video generation model presets to download
- `IMAGE_PRESET_DOWNLOAD`: Comma-separated list of image generation model presets to download
- `AUDIO_PRESET_DOWNLOAD`: Comma-separated list of audio generation model presets to download
- `PUBLIC_KEY`: SSH public key for remote access
- `FORCE_SYNC_ALL`: Force full resync of venv and ComfyUI on startup (`True`/`False`)

### Preset Downloads

#### Video Generation Presets (PRESET_DOWNLOAD)
Use for WAN video generation models:
```bash
# Inside container
bash /download_presets.sh WAN_22_5B_TIV2,WAN_22_LIGHTNING_LORA

# Available presets include:
# WAN video models: WAN_22_5B_TIV2, WAN_22_5B_I2V_GGUF_Q8_0, WAN22_I2V_A14B_GGUF_Q8_0
# Image models: WAINSFW_V140, NTRMIX_V40
# Enhancements: WAN22_LIGHTNING_LORA, WAN22_NSFW_LORA
# Utilities: UPSCALE_MODELS, WAN22_S2V_FP8_SCALED
```

#### Image Generation Presets (IMAGE_PRESET_DOWNLOAD)
Use for SDXL, SD 1.5, Qwen, and other image generation models:
```bash
# Inside container
bash /download_image_presets.sh SDXL_BASE_V1,REALISTIC_VISION_V6

# Available presets include:
# SDXL models: SDXL_BASE_V1, JUGGERNAUT_XL_V8, REALVIS_XL_V4, DREAMSHAPER_XL_V7
# SD 1.5 models: REALISTIC_VISION_V6, DELIBERATE_V6, DREAMSHAPER_V8, PROTOGEN_XL
# Anime models: ANYTHING_V5, MEINAMIX_V12, COUNTERFEIT_V3
# Qwen models: QWEN_IMAGE_BASIC, QWEN_IMAGE_EDIT, QWEN_IMAGE_COMPLETE, QWEN_IMAGE_CHINESE
# Flux models: FLUX_SCHNELL_BASIC, FLUX_DEV_BASIC, FLUX_SCHNELL_FP8, FLUX_DEV_FP8, FLUX_COMPLETE, FLUX_PRODUCTION
# Utility models: ESRGAN_MODELS, SDXL_REFINER, INPAINTING_MODELS
# Complete workflows: SDXL_COMPLETE_WORKFLOW, REALISTIC_COMPLETE_WORKFLOW, ANIME_COMPLETE_WORKFLOW
```

#### Audio Generation Presets (AUDIO_PRESET_DOWNLOAD)
Use for text-to-speech, music generation, and audio processing models:
```bash
# Inside container
bash /download_audio_presets.sh MUSICGEN_MEDIUM,BARK_BASIC

# Available presets include:
# Text-to-speech: BARK_BASIC, TTS_AUDIO_SUITE, PARLER_TTS
# Music generation: MUSICGEN_SMALL, MUSICGEN_MEDIUM, ACE_STEP, SONGBLOOM
# Audio processing: STABLE_AUDIO_OPEN
# Complete workflows: AUDIO_SPEECH_COMPLETE, AUDIO_MUSIC_COMPLETE, AUDIO_PRODUCTION, AUDIO_ALL
```

#### Combined Usage
All three preset systems can be used together for complete multimedia generation:
```bash
# Environment variables
export PRESET_DOWNLOAD="WAN_22_5B_TIV2,WAN22_LIGHTNING_LORA"
export IMAGE_PRESET_DOWNLOAD="SDXL_BASE_V1,REALISTIC_VISION_V6"
export AUDIO_PRESET_DOWNLOAD="MUSICGEN_MEDIUM,BARK_BASIC"

# Container startup
docker run -e PRESET_DOWNLOAD="$PRESET_DOWNLOAD" -e IMAGE_PRESET_DOWNLOAD="$IMAGE_PRESET_DOWNLOAD" -e AUDIO_PRESET_DOWNLOAD="$AUDIO_PRESET_DOWNLOAD" ...
```

### Custom Node Management
For slim images or to add custom nodes:
1. Nodes can be installed via ComfyUI Manager web interface
2. Or manually clone to `/workspace/ComfyUI/custom_nodes/`
3. Each custom node may have additional requirements.txt files that are auto-installed during build

## Image Tagging Convention
Images follow the format: `zeroclue/comfyui:{variant}-torch{version}-{cuda}`
- Variants: `base` (with custom nodes), `slim` (minimal), or `minimal` (ComfyUI only)
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
- **wiki/**: Additional documentation for presets and custom nodes
  - `PRESET_DOWNLOAD.md`: Video generation preset documentation
  - `IMAGE_PRESET_DOWNLOAD.md`: Image generation preset documentation
  - `AUDIO_PRESET_DOWNLOAD.md`: Audio generation preset documentation
- All custom nodes install to `/workspace/ComfyUI/custom_nodes/`
- Workspace is at `/workspace/` with persistent storage for models and outputs

## GitHub Actions Workflow
The project includes an automated build system (`.github/workflows/build.yml`) that:
- Builds images on push to main branch (when Docker-related files change)
- Supports manual workflow dispatch with configurable targets and CUDA versions
- Builds matrix of variants (base, slim, minimal) with CUDA versions (12-6, 12-8)
- Pushes to Docker Hub under `zeroclue/comfyui` repository

## Development Workflow
1. Modify `docker-bake.hcl` to change registry or add new build targets
2. Update `custom_nodes.txt` to modify pre-installed nodes
3. Add new presets to `scripts/download_presets.sh`, `scripts/download_image_presets.sh`, or `scripts/download_audio_presets.sh` for custom model downloads
4. Use environment variables to control runtime behavior
5. All persistent data is stored in `/workspace/` directory
6. Test changes locally with `docker bake` before pushing to trigger CI builds

## Triple Preset System

The container features a triple preset system that separates video, image, and audio generation capabilities:

### Video Generation (PRESET_DOWNLOAD)
- **WAN 2.2 Video Models**: Text-to-Video (T2V) and Image-to-Video (I2V)
- **Multiple Formats**: FP8, GGUF variants with different quantization levels
- **Specialized LoRAs**: Lightning (faster inference) and content filtering
- **Audio-to-Video**: S2V capabilities with appropriate encoder models
- **Documentation**: See `wiki/PRESET_DOWNLOAD.md`

### Image Generation (IMAGE_PRESET_DOWNLOAD)
- **SDXL Models**: High-quality image generation (SDXL_BASE_V1, JUGGERNAUT_XL_V8)
- **SD 1.5 Models**: Versatile and efficient models (REALISTIC_VISION_V6, DELIBERATE_V6)
- **Anime/Art Models**: Specialized for artistic styles (ANYTHING_V5, MEINAMIX_V12)
- **Qwen Models**: Advanced 20B parameter models with superior Chinese text rendering (QWEN_IMAGE_BASIC, QWEN_IMAGE_CHINESE)
- **Flux Models**: State-of-the-art 12B parameter models competing with Midjourney (FLUX_SCHNELL_BASIC, FLUX_DEV_BASIC)
- **Utility Models**: VAE, upscaling, inpainting, and refinement models
- **Complete Workflows**: Bundled presets for specific use cases
- **Documentation**: See `wiki/IMAGE_PRESET_DOWNLOAD.md`

### Audio Generation (AUDIO_PRESET_DOWNLOAD)
- **Text-to-Speech Models**: High-quality voice synthesis (BARK_BASIC, TTS_AUDIO_SUITE, PARLER_TTS)
- **Music Generation Models**: Text-to-music generation (MUSICGEN_SMALL, MUSICGEN_MEDIUM, ACE_STEP, SONGBLOOM)
- **Audio Processing Models**: High-quality audio generation and effects (STABLE_AUDIO_OPEN)
- **Complete Workflows**: Bundled presets for speech, music, and production workflows
- **Custom Node Integration**: Auto-installation of required custom nodes for audio processing
- **Documentation**: See `wiki/AUDIO_PRESET_DOWNLOAD.md`

### Benefits
- **Clean Separation**: Different workflows for different media types
- **Modular Installation**: Install only what you need
- **Independent Usage**: Use any system or combine all three together
- **Focused Presets**: Each preset optimized for specific use cases
- **Complete Multimedia**: Generate videos with custom soundtracks, images with audio narration, and full multimedia productions