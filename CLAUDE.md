# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Table of Contents

- [Quick Reference](#quick-reference)
- [Project Overview](#project-overview)
- [Build System Architecture](#build-system-architecture)
- [Docker Build Commands](#docker-build-commands)
- [Local Development](#local-development)
- [Environment Variables](#environment-variables)
- [Preset Downloads](#preset-downloads)
- [Custom Node Management](#custom-node-management)
- [Image Tagging Convention](#image-tagging-convention)
- [GitHub Actions Workflow System](#github-actions-workflow-system)
- [Development Workflow](#development-workflow)
- [Troubleshooting and Optimization](#troubleshooting-and-optimization)
- [Web Research Guidelines](#web-research-guidelines)
- [Triple Preset System](#triple-preset-system)

## Quick Reference

### **Essential Commands**
```bash
# Analyze custom nodes for conflicts
python scripts/analyze_requirements.py custom_nodes.txt

# Build optimized image
docker bake -f docker-bake-optimized.hcl base-optimized-12-6

# Run with GPU support
docker run --gpus all -p 3000:3000 zeroclue/comfyui:base-optimized-torch2.8.0-cu126

# Validate installation
python scripts/validate_custom_nodes.py

# Create rollback point
python scripts/node_rollback.py create "Before changes"
```

### **Common Build Targets**
| Variant | Command | Size | Use Case |
|---------|---------|------|----------|
| `base-optimized-12-6` | `docker bake -f docker-bake-optimized.hcl base-optimized-12-6` | ~3GB | Full installation |
| `production-optimized-12-6` | `docker bake -f docker-bake-optimized.hcl production-optimized-12-6` | ~2.5GB | Production |
| `ultra-optimized-12-6` | `docker bake -f docker-bake-optimized.hcl ultra-optimized-12-6` | ~1.8GB | Minimal |

### **Emergency Recovery**
```bash
# Use legacy build if optimization fails
docker bake base-12-6

# Rollback problematic changes
python scripts/node_rollback.py rollback <backup-id>

# Check build logs
# GitHub Actions → Select workflow → View logs
```

## Project Overview

This is a Dockerized ComfyUI distribution maintained by ZeroClue organization that provides a complete AI image generation environment. The project builds Docker images with ComfyUI, ComfyUI Manager, and optional pre-installed custom nodes, designed for RunPod cloud deployment but also usable locally. Images are built automatically via GitHub Actions and can be built manually using Docker Bake.

## Architecture

### Docker Build System
The project features a dual build system with both legacy and optimized approaches:

#### **Legacy Build System**
- **Dockerfile**: Original multi-stage build that installs Python 3.13, PyTorch 2.8.0, ComfyUI, and optional custom nodes
- **docker-bake.hcl**: Sophisticated build system with inheritance patterns:
  - **Development Images**: Use `nvidia/cuda:*-devel-*` base images with build tools
  - **Runtime Images**: Use `nvidia/cuda:*-runtime-*` base images for production (30-50% smaller)
  - **CUDA Versions**: Supports 12.4, 12.5, 12.6, 12.8, 12.9, 13.0
  - **Target Inheritance**: Modular build configuration with reusable components
- **Use Case**: Emergency builds, testing, fallbacks
- **Trigger**: Manual dispatch only

#### **Optimized Build System** (NEW)
- **Dockerfile.optimized**: Advanced multi-stage build with dependency conflict resolution
- **docker-bake-optimized.hcl**: Optimized build targets with size and performance improvements
- **Benefits**: 60-80% size reduction, better layer caching, conflict prevention
- **Trigger**: Automatic on push to main branch
- **Use Case**: Production, normal development

#### **Custom Node Analysis System**
- **custom_nodes.txt**: List of custom node repositories for base images
- **Automated Analysis**: Detects dependency conflicts before building
- **Resolution Strategies**: Generates compatible version combinations
- **Validation Pipeline**: Tests installation integrity and performance

### Container Services Architecture
The container runs multiple services with sophisticated orchestration:

#### **Service Port Mapping**
| Service | Internal Port | External Port | Purpose | Access Via |
|---------|---------------|---------------|---------|------------|
| ComfyUI | 3000 | 3001 | Main AI interface | Nginx proxy: port 3000 |
| code-server | 8080 | 8081 | VS Code web IDE | Nginx proxy: port 8080 |
| JupyterLab | 8888 | 8889 | Notebook environment | Nginx proxy: port 8888 |
| SSH | 22 | 22 | Remote access | Direct (if PUBLIC_KEY set) |

#### **Service Orchestration**
- **Nginx Reverse Proxy**: Handles external routing and load balancing
- **Service Startup Sequence**: Defined in `/scripts/start.sh` with ordered initialization
- **Health Management**: Each service runs in background with dedicated logging
- **Graceful Shutdown**: Proper signal handling for service cleanup

### Key Scripts

#### **Container Management**
- **/start.sh**: Main entrypoint that starts all services (nginx, SSH, JupyterLab, code-server)
- **/pre_start.sh**: Runs environment setup, workspace synchronization, optional SageAttention2 installation
- **/post_start.sh**: Launches ComfyUI with configurable arguments

#### **Preset Management**
- **/download_presets.sh**: Downloads video generation model presets from HuggingFace
- **/download_image_presets.sh**: Downloads image generation model presets from HuggingFace
- **/download_audio_presets.sh**: Downloads audio generation model presets from HuggingFace

#### **Custom Node Management (Enhanced)**
- **/install_custom_nodes.sh**: Enhanced script with multiple installation modes:
  - `standard`: Traditional installation method
  - `optimized`: Uses dependency conflict resolution
  - `validation`: Includes comprehensive testing and validation

#### **Analysis and Optimization Tools (NEW)**
- **scripts/analyze_requirements.py**: Analyzes custom nodes for dependency conflicts and generates reports
- **scripts/dependency_resolver.py**: Creates resolution strategies for dependency conflicts
- **scripts/validate_custom_nodes.py**: Validates custom node installation, integration, and performance
- **scripts/node_rollback.py**: Manages safe rollback of problematic custom node additions

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
The container implements a sophisticated two-phase startup system with intelligent synchronization:

#### **Source-to-Workspace Synchronization**
- **Source Directories**: `/venv/` (Python environment) and `/ComfyUI/` (application) - read-only
- **Workspace Target**: `/workspace/` - persistent storage for user data and modifications
- **Smart Sync Algorithm**:
  - Checks file integrity using checksums
  - Compares modification timestamps to avoid unnecessary transfers
  - Preserves user customizations and models
  - Handles partial updates efficiently

#### **Startup Sequence**
1. **pre_start.sh**: Environment setup and workspace synchronization
2. **Service Initialization**: Ordered startup of nginx, SSH, JupyterLab, code-server
3. **post_start.sh**: ComfyUI launch with configurable arguments
4. **Runtime**: All services run in background with proper signal handling

#### **Data Persistence**
- **Models**: Stored in `/workspace/ComfyUI/models/` with subdirectories by type
- **User Data**: Workflows, outputs, and customizations preserved across container restarts
- **Logs**: Centralized in `/workspace/logs/` for all services
- **Configuration**: Environment variables and settings maintained in workspace

## Docker Build Commands

### **Build Variants**

#### **Optimized Builds** (Recommended)
```bash
# Build optimized variants with dependency conflict resolution
docker bake -f docker-bake-optimized.hcl base-optimized-12-6    # Full installation
docker bake -f docker-bake-optimized.hcl slim-optimized-12-8    # No custom nodes
docker bake -f docker-bake-optimized.hcl production-optimized-12-6 # Production-ready
docker bake -f docker-bake-optimized.hcl ultra-optimized-12-6   # Minimal size

# Build all optimized variants
docker bake -f docker-bake-optimized.hcl optimized-all

# Build production-optimized variants only
docker bake -f docker-bake-optimized.hcl production-optimized
```

#### **Legacy Builds** (Emergency/Testing)
```bash
# Build using original Dockerfile
docker bake base-12-6     # Full installation
docker bake slim-12-8     # No custom nodes
docker bake production-12-6 # Production-ready
docker bake ultra-slim-12-8 # Minimal size

# List all available targets
docker bake --list

# Build and push
docker bake base-12-6 --push
```

### **Build System Commands**
```bash
# List all available build targets
docker bake --list

# Build specific variants
docker bake base-12-6     # Base image with CUDA 12.6
docker bake slim-12-8     # Slim image with CUDA 12.8
docker bake minimal-12-8  # Minimal image with CUDA 12.8
docker bake production-12-6  # Production-optimized with runtime CUDA
docker bake ultra-slim-12-8   # Ultra-minimal with runtime CUDA

# Build and push to registry
docker bake base-12-6 --push

# Build with custom arguments
docker bake base-12-6 --set PYTHON_VERSION=3.13
```

### **Pre-Build Analysis**
```bash
# Analyze custom nodes for conflicts before building
python scripts/analyze_requirements.py custom_nodes.txt

# Generate resolution strategies
python scripts/dependency_resolver.py custom_nodes_analysis.json

# Check for critical conflicts
cat custom_nodes_analysis.json | jq '.summary.high_severity_conflicts'
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

#### **Safe Custom Node Addition** (NEW)
```bash
# 1. Create backup before making changes
python scripts/node_rollback.py create "Before adding new node"

# 2. Add node to custom_nodes.txt
echo "https://github.com/user/new-node.git" >> custom_nodes.txt

# 3. Analyze for conflicts
python scripts/analyze_requirements.py custom_nodes.txt

# 4. If no conflicts, install with optimization
./scripts/install_custom_nodes.sh optimized

# 5. Validate installation
python scripts/validate_custom_nodes.py

# 6. If problems occur, rollback
python scripts/node_rollback.py rollback <backup-id>
```

#### **Traditional Node Management**
For slim images or to add custom nodes:
1. Nodes can be installed via ComfyUI Manager web interface
2. Or manually clone to `/workspace/ComfyUI/custom_nodes/`
3. Each custom node may have additional requirements.txt files that are auto-installed during build

#### **Rollback Management**
```bash
# List available rollback points
python scripts/node_rollback.py list

# Create rollback point
python scripts/node_rollback.py create "Description of changes"

# Rollback to specific point
python scripts/node_rollback.py rollback 20241201_143022

# Remove problematic node safely
python scripts/node_rollback.py remove problematic-node

# Clean up old backups
python scripts/node_rollback.py cleanup --keep 5
```

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

## Image Tagging Convention

### **Legacy Image Tags**
Images follow the format: `zeroclue/comfyui:{variant}-torch{version}-{cuda}`
- Variants: `base`, `slim`, `minimal`, `production`, `ultra-slim`
- PyTorch version: `2.8.0`
- CUDA versions: `cu124`, `cu126`, `cu128`, `cu129`, `cu130`

### **Optimized Image Tags** (NEW)
Optimized images follow the format: `zeroclue/comfyui:{variant}-torch{version}-{cuda}`
- Variants: `base-optimized`, `slim-optimized`, `production-optimized`, `ultra-optimized`
- PyTorch version: `2.8.0`
- CUDA versions: `cu126`, `cu128`
- Benefits: 60-80% size reduction, dependency conflict resolution, better performance

## Pre-installed Custom Nodes (Base Images)

The base image includes 24 custom nodes covering:
- **Video generation**: ComfyUI-WanVideoWrapper, ComfyUI-Frame-Interpolation
- **Model optimization**: ComfyUI-GGUF, ComfyUI-TensorRT, ComfyUI-MultiGPU
- **Image processing**: ComfyUI_UltimateSDUpscale, ComfyUI-Image-Saver
- **Workflow enhancement**: efficiency-nodes, rgthree-comfy, ComfyUI-Easy-Use
- **Development tools**: ComfyUI-Impact-Pack, comfy-ex-tagcomplete
- **Communication**: ComfyUI-Openrouter_node (NEW)

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
- **docs/**: Comprehensive documentation (NEW)
  - `OPTIMIZED_BUILD_SYSTEM.md`: Complete technical documentation for optimization system
  - `QUICK_START_GUIDE.md`: 5-minute getting started guide
  - `WORKFLOW_GUIDE.md`: Dual workflow system documentation
- All custom nodes install to `/workspace/ComfyUI/custom_nodes/`
- Workspace is at `/workspace/` with persistent storage for models and outputs

## GitHub Actions Workflow System (NEW)

### **Dual Workflow Architecture**
The project includes two separate GitHub Actions workflows:

#### **1. Optimized Workflow** (`.github/workflows/build.yml`)
- **Trigger**: Automatic on push to main branch
- **Features**: Dependency analysis, conflict resolution, multi-stage builds
- **Benefits**: Prevents build failures, optimizes images, ensures compatibility
- **Build Targets**: `base-optimized`, `slim-optimized`, `production-optimized`, `ultra-optimized`

#### **2. Legacy Workflow** (`.github/workflows/build-legacy.yml`)
- **Trigger**: Manual dispatch only
- **Features**: Original build process, no analysis
- **Purpose**: Emergency builds, testing, fallbacks
- **Build Targets**: `base`, `slim`, `minimal`, `production`, `ultra-slim`

### **Workflow Process**
1. **Dependency Analysis** (Optimized only): Detects conflicts before building
2. **Build Matrix**: Multiple variants with different CUDA versions
3. **Automated Validation**: Ensures build quality and functionality
4. **Docker Hub Push**: All images pushed to `zeroclue/comfyui` repository

### **When to Use Each Workflow**
- **Normal Development**: Use optimized workflow (automatic)
- **Testing/Emergency**: Use legacy workflow (manual)
- **Production**: Always use optimized workflow

## Development Workflow

### **Standard Development Process**
1. **Before Making Changes**: Create rollback point
   ```bash
   python scripts/node_rollback.py create "Before development changes"
   ```

2. **Analyze Changes**: Check for dependency conflicts
   ```bash
   python scripts/analyze_requirements.py custom_nodes.txt
   ```

3. **Make Changes**:
   - Modify `docker-bake.hcl` or `docker-bake-optimized.hcl` to change registry or add new build targets
   - Update `custom_nodes.txt` to modify pre-installed nodes
   - Add new presets to `scripts/download_presets.sh`, `scripts/download_image_presets.sh`, or `scripts/download_audio_presets.sh` for custom model downloads
   - Update optimization scripts as needed

4. **Test Locally**: Validate changes before pushing
   ```bash
   # Test optimized build
   docker bake -f docker-bake-optimized.hcl base-optimized-12-6

   # Validate installation
   python scripts/validate_custom_nodes.py

   # Test container startup
   docker run --rm -it zeroclue/comfyui:base-optimized-torch2.8.0-cu126 bash

   # Verify service health
   curl http://localhost:3000  # ComfyUI
   curl http://localhost:8080  # code-server
   curl http://localhost:8888  # JupyterLab
   ```

5. **Push Changes**: Trigger automated optimized build
   ```bash
   git add .
   git commit -m "Add optimization improvements"
   git push origin main
   ```

6. **Monitor Results**: Check GitHub Actions for build status
   - Automatic dependency analysis runs
   - Optimized builds with conflict resolution
   - Validation and reporting

### **Best Practices for Development**
- Use environment variables to control runtime behavior
- All persistent data is stored in `/workspace/` directory
- Always test with both legacy and optimized builds when possible
- Use rollback system for safe experimentation
- Monitor build artifacts for analysis results

## Web Research Guidelines
When performing web searches for research, documentation updates, or staying current with latest features:
- **Always use `mcp__web-search-prime__webSearchPrime`** for web searches instead of generic search tools
- This provides more accurate, up-to-date results with better source credibility
- Use specific, targeted search queries for best results
- Cross-reference information from multiple sources when researching technical details
- Prioritize official documentation and recent community resources

## Troubleshooting and Optimization

### **Common Issues and Solutions**

#### **Build Failures**
```bash
# Check for dependency conflicts
python scripts/analyze_requirements.py custom_nodes.txt

# Review conflict details
cat custom_nodes_analysis.json | jq '.conflicts'

# Use legacy build if optimization fails
docker bake base-12-6  # Uses original Dockerfile
```

#### **Import Errors**
```bash
# Validate installation to identify problematic nodes
python scripts/validate_custom_nodes.py --output report.json

# Check failed imports
cat report.json | jq '.nodes | to_entries[] | select(.value.failed > 0)'

# Rollback problematic changes
python scripts/node_rollback.py rollback <last-working-id>
```

#### **Performance Issues**
```bash
# Check node sizes and complexity
python scripts/validate_custom_nodes.py | grep "performance"

# Remove large nodes if needed
python scripts/node_rollback.py remove large-node

# Use ultra-optimized variant for production
docker run zeroclue/comfyui:ultra-optimized
```

### **Optimization Best Practices**

#### **Before Adding Custom Nodes**
1. Always create a rollback point
2. Run dependency analysis first
3. Check for known conflicts
4. Test in development environment

#### **During Development**
1. Use validation mode for testing
2. Monitor performance impact
3. Keep rollback points organized
4. Document any manual interventions

#### **For Production**
1. Use production-optimized variants
2. Validate before deployment
3. Monitor runtime performance
4. Keep backup rollback points

### **Performance Optimization Results**

| Image Type | Original Size | Optimized Size | Reduction | Build Time Impact |
|------------|---------------|----------------|-----------|------------------|
| Base | ~8GB | ~3GB | 62% | +2-3 minutes |
| Production | ~6GB | ~2.5GB | 58% | +2-3 minutes |
| Ultra-optimized | ~4GB | ~1.8GB | 55% | +2-3 minutes |

**Note**: Initial optimized builds take longer due to analysis, but subsequent builds benefit from better layer caching.

### **Getting Help**

```bash
# Check script help for detailed options
python scripts/analyze_requirements.py --help
python scripts/validate_custom_nodes.py --help
python scripts/node_rollback.py --help

# Review logs and artifacts
ls -la /tmp/custom_nodes_*.json
cat /tmp/custom_nodes_install.log

# Check GitHub Actions build logs
# Actions tab → Select workflow → View build logs
```
- trim the commit message