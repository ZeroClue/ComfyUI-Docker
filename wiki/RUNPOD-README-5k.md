# ZeroClue ComfyUI-Docker - RunPod Deployment Guide

> Optimized for RunPod Cloud GPU - Deploy ComfyUI with one click.

> Support: [GitHub Issues](https://github.com/ZeroClue/ComfyUI-Docker/issues)

<a href="https://www.buymeacoffee.com/thezeroclue" target="_blank" rel="noopener noreferrer">
<img src="https://www.buymeacoffee.com/assets/img/custom_images/yellow_img.png" alt="Buy me a coffee" width="105px" />
</a>

---

## Quick Start

### 1. Choose Your Image

| Use Case | Image | GPU | Cost/hr |
|----------|-------|-----|---------|
| **RunPod Optimized** | `zeroclue/comfyui:minimal-torch2.8.0-cu126` | RTX A4000+ | $0.40-0.70 |
| Development | `zeroclue/comfyui:base-torch2.8.0-cu126` | RTX A4000+ | $0.50-1.00 |
| Production | `zeroclue/comfyui:slim-torch2.8.0-cu126` | RTX A4000+ | $0.35-0.60 |

### 2. Create Pod

1. Go to [RunPod Console](https://runpod.io/console) > **Deploy > Secure Cloud**
2. **GPU**: RTX A4000 or better
3. **Container Image**: Enter image from table above
4. **Storage**: Add 50GB+ network storage
5. Click **Deploy**

### 3. Configure Presets (Optional)

Add environment variables in **Pod Settings > Environment Variables**:

```bash
# Video Generation (26 presets available)
PRESET_DOWNLOAD=WAN_2_2_T2V_BASIC,WAN_2_1_LIGHTWEIGHT_1_3B

# Image Generation (25 presets available)
IMAGE_PRESET_DOWNLOAD=SDXL_BASE_V1,FLUX_DEV_BASIC,SD3_5_LARGE_BASIC

# Audio Generation (5 presets available)
AUDIO_PRESET_DOWNLOAD=ACE_STEP_V1_3_5B,COMPLETE_AUDIO_SUITE
```

### 4. Access Services

Click port links in RunPod console to access interfaces.

---

## Environment Variables

### Core Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `ACCESS_PASSWORD` | - | Password for web UIs |
| `TIME_ZONE` | UTC | Container timezone |
| `ENABLE_STUDIO` | true | Enable ComfyUI Studio |
| `INSTALL_SAGEATTENTION` | false | Speed boost for Ampere+ GPUs |

---

## Preset Systems (56 Total)

### Video Generation (26 Presets)

**WAN 2.2 Series** - Latest video models:
- `WAN_2_2_T2V_BASIC` - Text-to-video (15.5GB)
- `WAN_2_2_I2V_BASIC` - Image-to-video (15.7GB)
- `WAN_2_2_S2V` - Sound-to-video (12.6GB)
- `WAN_2_2_FUN_CAMERA` - Camera control (16.9GB)

**WAN 2.1 Series** - Lightweight alternatives:
- `WAN_2_1_LIGHTWEIGHT_1_3B` - Consumer GPU friendly (8.5GB)
- `WAN_2_1_T2V_14B` / `WAN_2_1_I2V_14B` - High quality (13.5GB)

**Other Video Models**:
- `LTX_VIDEO_T2V` / `LTX_VIDEO_I2V` - LTX-Video (14-16GB)
- `HUNYUAN_T2V_720P` / `HUNYUAN_I2V_*` - Tencent Hunyuan (7-11GB)
- `COSMOS_PREDICT2_VIDEO2WORLD` - NVIDIA physical world (31GB)

### Image Generation (25 Presets)

**SDXL/SD3.5 Series**:
- `SDXL_BASE_V1` / `SDXL_TURBO_BASIC` - SDXL models
- `SD3_5_LARGE_BASIC` / `SD3_5_LARGE_TURBO` / `SD3_5_MEDIUM_BASIC`

**FLUX Series**:
- `FLUX_DEV_BASIC` - High quality (24GB)
- `FLUX_SCHNELL_BASIC` - Fast generation (24GB)

**Qwen 20B** - Superior text rendering:
- `QWEN_IMAGE_BASIC` / `QWEN_IMAGE_EDIT` / `QWEN_IMAGE_CHINESE`

**Realistic/Photorealistic**:
- `REALISTIC_VISION_V6` / `REALVIS_XL_V4` / `JUGGERNAUT_XL_V8`

### Audio Generation (5 Presets)

- `ACE_STEP_V1_3_5B` - Music & lyrics generation (7.2GB)
- `ACE_STEP_MULTI_TRACK` - Multi-track composition
- `COMPLETE_AUDIO_SUITE` - MusicGen + Bark + TTS (10.9GB)

---

## Network Access

| Port | Service | Purpose |
|------|---------|---------|
| **3000** | ComfyUI | Node-based workflow editor |
| **5000** | ComfyUI Studio | Simplified workflow UI |
| **9000** | Preset Manager | Model download manager |
| 8080 | Code Server | VS Code IDE (if in image) |
| 8888 | JupyterLab | Notebook environment |
| 22 | SSH | Command line access |

---

## ComfyUI Studio (Port 5000)

A simplified interface for executing pre-configured workflows without node editing:

- **Workflow Templates**: Execute saved workflows with auto-generated forms
- **Progress Tracking**: Real-time updates during generation
- **Image Upload**: Upload images for img2img workflows
- **Output Gallery**: View and download generated content

Access via **Port 5000** link in RunPod console. Uses same `ACCESS_PASSWORD` as other services.

---

## Storage

### Paths
```
/workspace/ComfyUI/models/     # AI models
/workspace/ComfyUI/output/     # Generated content
/workspace/ComfyUI/input/      # Upload files
/workspace/config/workflows/   # Studio workflows
```

### Persistent Data
- Downloaded models and presets
- Custom nodes and workflows
- Generated images/videos

---

## Tips

- **GPU**: RTX A4000 minimum, A5000/A6000 for faster generation
- **Storage**: 100GB+ recommended for multiple presets
- **Security**: Always set `ACCESS_PASSWORD` for production
- **Studio vs ComfyUI**: Use Studio for simple tasks, ComfyUI for complex workflows
