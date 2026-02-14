# RunPod Video Generation Deployment Guide

> AI video generation on RunPod - WAN 2.1/2.2, LTX, Hunyuan, Cosmos

<a href="https://www.buymeacoffee.com/thezeroclue" target="_blank" rel="noopener noreferrer">
<img src="https://www.buymeacoffee.com/assets/img/custom_images/yellow_img.png" alt="Buy me a coffee" width="105px" />
</a>

---

## Quick Start

1. **Deploy**: `zeroclue/comfyui:minimal-torch2.8.0-cu126`
2. **Set Environment**: `PRESET_DOWNLOAD=WAN_2_2_T2V_BASIC`
3. **GPU Choice**: A40 (48GB) or RTX 4090 (24GB minimum)
4. **Access**: ComfyUI port 3000, Studio port 5000

---

## Hardware Recommendations

| GPU | VRAM | Spot Price | Best For |
|-----|------|------------|----------|
| **A40** | 48GB | $0.79/hr | Large video models |
| **L40** | 48GB | ~$0.49/hr | Balanced |
| **RTX 4090** | 24GB | $0.34/hr | Consumer-grade |

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
# Video presets (26 available)
PRESET_DOWNLOAD="WAN_2_2_T2V_BASIC"
ACCESS_PASSWORD="your-secure-password"
ENABLE_STUDIO=true
```

### Preset Combinations

```bash
# Basic Text-to-Video
PRESET_DOWNLOAD="WAN_2_2_T2V_BASIC"

# Lightweight (Consumer GPU)
PRESET_DOWNLOAD="WAN_2_1_LIGHTWEIGHT_1_3B"

# Image-to-Video
PRESET_DOWNLOAD="WAN_2_2_I2V_BASIC"

# Sound-to-Video
PRESET_DOWNLOAD="WAN_2_2_S2V"
```

---

## Video Presets (26 Available)

### WAN 2.2 Series (Latest)
| Preset | Size | Description |
|--------|------|-------------|
| `WAN_2_2_T2V_BASIC` | 15.5GB | Text-to-video |
| `WAN_2_2_I2V_BASIC` | 15.7GB | Image-to-video |
| `WAN_2_2_S2V` | 12.6GB | Sound-to-video |
| `WAN_2_2_FUN_CAMERA` | 16.9GB | Camera control |
| `WAN_2_2_FUN_CONTROL` | 17.7GB | Advanced control |

### WAN 2.1 Series (Lightweight)
| Preset | Size | VRAM | Description |
|--------|------|------|-------------|
| `WAN_2_1_LIGHTWEIGHT_1_3B` | 8.5GB | 6GB+ | Consumer GPU |
| `WAN_2_1_T2V_14B` | 13.5GB | 8GB+ | High quality T2V |
| `WAN_2_1_I2V_14B` | 13.5GB | 8GB+ | High quality I2V |

### Other Video Models
| Preset | Size | Description |
|--------|------|-------------|
| `LTX_VIDEO_T2V` | 14.5GB | LTX text-to-video |
| `LTX_VIDEO_I2V` | 16.1GB | LTX image-to-video |
| `HUNYUAN_T2V_720P` | 7.6GB | Hunyuan 720p |
| `COSMOS_PREDICT2_VIDEO2WORLD` | 31.4GB | NVIDIA physical world |
| `WAN22_LIGHTNING_LORA` | 1.4GB | 2-3x faster |
| `UPSCALE_MODELS` | 2.1GB | Video upscaling |

---

## Network Access

| Port | Service | Purpose |
|------|---------|---------|
| **3000** | ComfyUI | Node-based video workflows |
| **5000** | ComfyUI Studio | Simplified workflow execution |
| **9000** | Preset Manager | Model download management |
| 8080 | Code Server | VS Code IDE |
| 8888 | JupyterLab | Notebook environment |

---

## ComfyUI Studio (Port 5000)

Simplified interface for video generation:

- **Workflow Templates**: Pre-configured T2V, I2V workflows
- **Progress Tracking**: Real-time generation updates
- **Image Upload**: For image-to-video workflows
- **Output Gallery**: View and download videos

Access via **Port 5000** link in RunPod console.

---

## Deployment Steps

### 1. Create Network Volume
- **Storage** > **Network Volumes** > **Create**
- **Size**: 100GB+ (video models are large)

### 2. Deploy Pod
- **Container Image**: `zeroclue/comfyui:minimal-torch2.8.0-cu126`
- **GPU**: A40 (48GB) or RTX 4090 (24GB)

### 3. Configure
```bash
PRESET_DOWNLOAD="WAN_2_2_T2V_BASIC"
ACCESS_PASSWORD="your-password"
```

### 4. Access
- **ComfyUI**: `https://[pod-id]-3000.proxy.runpod.net`
- **Studio**: `https://[pod-id]-5000.proxy.runpod.net`

---

## Video Workflows

### Text-to-Video (T2V)
1. Load WAN 2.2 model via preset
2. Enter text prompt describing video
3. Settings: 720p, 24fps, 5-10 seconds
4. Generate (2-5 minutes)

### Image-to-Video (I2V)
1. Upload image to `/workspace/ComfyUI/input/`
2. Load I2V model preset
3. Configure animation settings
4. Generate (1-3 minutes)

---

## Storage Paths

```
/workspace/ComfyUI/models/     # Video models
/workspace/ComfyUI/output/     # Generated videos
/workspace/ComfyUI/input/      # Reference images/audio
/workspace/config/workflows/   # Studio workflows
```

---

## Tips

- A40 recommended for professional work
- WAN 2.1 Lightweight for consumer GPUs (6GB VRAM)
- Generate at 720p, then upscale
- Lightning LoRA provides 2-3x speed boost
- 100GB+ storage for multiple presets

---

**Resources**: [Main README](RUNPOD-README-5k.md) | [GitHub](https://github.com/ZeroClue/ComfyUI-Docker)
