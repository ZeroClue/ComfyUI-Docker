# RunPod Image Generation Deployment Guide

> AI image generation on RunPod - SDXL, FLUX, SD3.5, Qwen, and more

<a href="https://www.buymeacoffee.com/thezeroclue" target="_blank" rel="noopener noreferrer">
<img src="https://www.buymeacoffee.com/assets/img/custom_images/yellow_img.png" alt="Buy me a coffee" width="105px" />
</a>

---

## Quick Start

1. **Deploy**: `zeroclue/comfyui:minimal-torch2.8.0-cu126`
2. **Set Environment**: `IMAGE_PRESET_DOWNLOAD=SDXL_BASE_V1,FLUX_DEV_BASIC`
3. **GPU Choice**: RTX 4090 (speed) or A40 (large models)
4. **Access**: ComfyUI port 3000, Studio port 5000

---

## Hardware Recommendations

| GPU | VRAM | Spot Price | Best For |
|-----|------|------------|----------|
| **RTX 4090** | 24GB | $0.34/hr | Speed & value |
| **A40** | 48GB | $0.79/hr | FLUX, Qwen 20B |
| **L40** | 48GB | ~$0.49/hr | Balanced |
| **RTX 3090** | 24GB | $0.26/hr | Budget |

---

## Docker Images

| Image | Use Case |
|-------|----------|
| `minimal-torch2.8.0-cu126` | RunPod optimized (recommended) |
| `base-torch2.8.0-cu126` | Full development setup |
| `slim-torch2.8.0-cu126` | Production, cost optimized |

---

## Environment Variables

```bash
# Image presets (25 available)
IMAGE_PRESET_DOWNLOAD="SDXL_BASE_V1,FLUX_DEV_BASIC"

# Security
ACCESS_PASSWORD="your-secure-password"

# Enable Studio interface
ENABLE_STUDIO=true
```

### Preset Combinations

```bash
# High-Quality Photorealistic
IMAGE_PRESET_DOWNLOAD="SDXL_BASE_V1,REALISTIC_VISION_V6"

# State-of-the-Art (FLUX 12B)
IMAGE_PRESET_DOWNLOAD="FLUX_DEV_BASIC"

# SD3.5 Professional
IMAGE_PRESET_DOWNLOAD="SD3_5_LARGE_BASIC,SD3_5_LARGE_TURBO"

# Chinese Text Rendering
IMAGE_PRESET_DOWNLOAD="QWEN_IMAGE_CHINESE"
```

---

## Image Presets (25 Available)

### SDXL Series
| Preset | Size | Description |
|--------|------|-------------|
| `SDXL_BASE_V1` | 6.9GB | High-quality base model |
| `SDXL_TURBO_BASIC` | 6.9GB | Real-time generation (1-4 steps) |

### SD3.5 Series (8B Parameters)
| Preset | Size | Description |
|--------|------|-------------|
| `SD3_5_LARGE_BASIC` | 12.5GB | Professional quality |
| `SD3_5_LARGE_TURBO` | 9.5GB | Fast generation (2-4x) |
| `SD3_5_MEDIUM_BASIC` | 6.5GB | Balanced performance |

### FLUX Series (12B Parameters)
| Preset | Size | Description |
|--------|------|-------------|
| `FLUX_DEV_BASIC` | 24GB | Highest quality |
| `FLUX_SCHNELL_BASIC` | 24GB | Fast generation |

### Qwen 20B (Text Rendering)
| Preset | Size | Description |
|--------|------|-------------|
| `QWEN_IMAGE_BASIC` | 38GB | Superior text in images |
| `QWEN_IMAGE_EDIT` | 38GB | Image editing |
| `QWEN_IMAGE_CHINESE` | 38GB | Chinese text optimization |

### Photorealistic
| Preset | Size | Description |
|--------|------|-------------|
| `REALISTIC_VISION_V6` | 5.1GB | SD 1.5 photorealistic |
| `REALVIS_XL_V4` | 6.9GB | XL realistic |
| `JUGGERNAUT_XL_V8` | 6.9GB | Artistic excellence |

### SD1.5 Workflows
| Preset | Description |
|--------|-------------|
| `SD1_5_TEXT_TO_IMAGE_BASIC` | Basic generation |
| `SD1_5_IMAGE_TO_IMAGE_BASIC` | Transform images |
| `SD1_5_INPAINT_BASIC` | Inpainting |
| `SD1_5_UPSCALE_BASIC` | Image upscaling |

---

## Network Access

| Port | Service | Purpose |
|------|---------|---------|
| **3000** | ComfyUI | Node-based workflow editor |
| **5000** | ComfyUI Studio | Simplified workflow execution |
| **9000** | Preset Manager | Model download management |
| 8080 | Code Server | VS Code IDE |
| 8888 | JupyterLab | Notebook environment |

---

## ComfyUI Studio (Port 5000)

Simplified interface for image generation:

- **Workflow Templates**: txt2img, img2img, upscale presets
- **Auto-Generated Forms**: Prompts, steps, CFG, dimensions
- **Image Upload**: For img2img and inpainting
- **Output Gallery**: View and download images

Access via **Port 5000** link in RunPod console.

---

## Deployment Steps

### 1. Create Network Volume
- **Storage** > **Network Volumes** > **Create**
- **Size**: 50GB+ (models are large)
- **Data Center**: Same region as GPU

### 2. Deploy Pod
- **Pods** > **Deploy Pod**
- **Container Image**: `zeroclue/comfyui:minimal-torch2.8.0-cu126`
- **GPU**: RTX 4090 or A40
- **Network Volume**: Select your volume

### 3. Configure
```bash
IMAGE_PRESET_DOWNLOAD="SDXL_BASE_V1,FLUX_DEV_BASIC"
ACCESS_PASSWORD="your-password"
```

### 4. Access
- **ComfyUI**: `https://[pod-id]-3000.proxy.runpod.net`
- **Studio**: `https://[pod-id]-5000.proxy.runpod.net`

---

## Storage Paths

```
/workspace/ComfyUI/models/     # Image models
/workspace/ComfyUI/output/     # Generated images
/workspace/ComfyUI/input/      # Reference images
/workspace/config/workflows/   # Studio workflows
```

---

## Tips

- Start with SDXL for quality, FLUX for best results
- RTX 4090 works for most; A40 for FLUX/Qwen 20B
- Use Studio for simple generation, ComfyUI for complex
- 100GB+ storage recommended for multiple presets

---

**Resources**: [Main README](RUNPOD-README-5k.md) | [GitHub](https://github.com/ZeroClue/ComfyUI-Docker)
