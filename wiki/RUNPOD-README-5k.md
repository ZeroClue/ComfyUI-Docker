# ZeroClue ComfyUI-Docker - RunPod Deployment Guide

> 🚀 **Optimized for RunPod Cloud GPU Platform** - Deploy ComfyUI with one click using our pre-configured Docker images.

> 💬 **Questions & Support** → [GitHub Issues](https://github.com/ZeroClue/ComfyUI-Docker/issues)

---

## 🎯 Quick Start - 5 Minute Setup

### 1. Choose Your Image Variant

| Use Case | Recommended Image | GPU | Cost Estimate |
| -------- | ----------------- | --- | ------------- |
| **Development** | `zeroclue/comfyui:base-torch2.8.0-cu126` | RTX A4000+ | $0.50-1.00/hr |
| **Production** | `zeroclue/comfyui:production-torch2.8.0-cu126` | RTX A4000+ | $0.35-0.60/hr |

### 2. Create RunPod Pod

1. Go to [RunPod Console](https://runpod.io/console)
2. Click **Deploy → Secure Cloud**
3. **GPU Selection**: Choose `NVIDIA RTX A4000` or better
4. **Container Image**: Enter your chosen image from table above
5. **Storage**: Add 50GB+ network storage
6. Click **Deploy**

### 3. Configure Presets (Optional)

Add these environment variables in **Pod Settings → Environment Variables**:

```bash
# For Video Generation
PRESET_DOWNLOAD=WAN_22_5B_TIV2

# For Image Generation
IMAGE_PRESET_DOWNLOAD=SDXL_BASE_V1,REALISTIC_VISION_V6

# For Audio Generation (Experimental)
AUDIO_PRESET_DOWNLOAD=MUSICGEN_MEDIUM,BARK_BASIC
```

### 4. Access ComfyUI

After pod starts, click the **Port 3000** link to access ComfyUI web interface.

---

## 🏗️ Pod Configuration

### Recommended Settings

| Setting | Recommended Value | Notes |
|---------|-------------------|-------|
| **GPU Type** | RTX A4000 / RTX A5000 / RTX A6000 | Higher GPUs = faster generation |
| **CPU Cores** | 4-8 vCPUs | Adequate for preprocessing |
| **Memory** | 16-32 GB RAM | Depends on model size |
| **Storage** | 50-200 GB Network Storage | For models and outputs |

### Container Images

```bash
# Development (full tooling)
zeroclue/comfyui:base-torch2.8.0-cu126

# Production (cost optimized)
zeroclue/comfyui:production-torch2.8.0-cu126
```

---

## 🔧 Environment Variables

### Required Variables
- `ACCESS_PASSWORD`: Optional password protection

### Optional Variables
- `TIME_ZONE`: Set your local timezone
- `COMFYUI_EXTRA_ARGS`: ComfyUI performance tweaks
- `INSTALL_SAGEATTENTION`: Ampere+ GPUs for speed boost
- `FORCE_SYNC_ALL`: Force fresh workspace setup

### Preset Downloads
```bash
# Video Generation
PRESET_DOWNLOAD=WAN_22_5B_TIV2,WAN22_LIGHTNING_LORA

# Image Generation
IMAGE_PRESET_DOWNLOAD=SDXL_BASE_V1,REALISTIC_VISION_V6,ESRGAN_MODELS

# Audio Generation (Experimental)
AUDIO_PRESET_DOWNLOAD=MUSICGEN_MEDIUM,BARK_BASIC
```

---

## 🎬 Preset Systems

### Video Generation
- **WAN_22_5B_TIV2**: Main video model
- **WAN22_LIGHTNING_LORA**: Faster inference
- **WAN22_I2V_A14B_GGUF_Q8_0**: Image-to-Video
- **WAINSFW_V140**: Image model for video

### Image Generation
- **SDXL_BASE_V1**: Professional SDXL base
- **REALISTIC_VISION_V6**: High-quality realistic images
- **FLUX_DEV_BASIC**: State-of-the-art 12B model
- **QWEN_IMAGE_CHINESE**: Chinese text optimization
- **ESRGAN_MODELS**: Image upscaling

### Audio Generation (Experimental)
- **MUSICGEN_MEDIUM**: Music generation
- **BARK_BASIC**: Voice synthesis
- **AUDIO_PRODUCTION**: Complete audio workflow

---

## 🌐 Network Access

### Exposed Ports
| Port | Service | Access Method |
|------|---------|---------------|
| **3000** | ComfyUI | Primary web interface |
| 8080 | code-server | Development IDE (if in image) |
| 8888 | JupyterLab | Notebook environment (if in image) |
| 22 | SSH | Command line access (with SSH key) |

### Access Services
1. **ComfyUI**: Click **Port 3000** link in RunPod console
2. **SSH Access**: Add SSH public key as `PUBLIC_KEY` environment variable
3. **Security**: Set `ACCESS_PASSWORD` for web interfaces

---

## 💾 Storage Management

### Network Storage Setup
1. Go to **Storage → Network Storage**
2. Create volume with 50-200GB space
3. Attach to your pod

### Storage Paths
```
/workspace/ComfyUI/models/     # AI models
/workspace/ComfyUI/output/     # Generated content
/workspace/ComfyUI/input/      # Upload files here
/workspace/ComfyUI/user/       # Workflows and settings
```

### Persistent Data
- ✅ Downloaded models and presets
- ✅ Custom nodes and workflows
- ✅ Generated images and videos
- ✅ Configuration files

---

## 💰 Cost Optimization

### Variant Selection
| Budget Level | Recommended Variant | Savings |
|--------------|---------------------|---------|
| **Premium** | `base-torch2.8.0-cu126` | Full features, higher cost |
| **Balanced** | `production-torch2.8.0-cu126` | 30-50% savings |

### GPU Selection
| GPU Type | Best For | Hourly Cost |
|----------|----------|-------------|
| **RTX A4000** | Production, development | $0.35-0.60 |
| 
