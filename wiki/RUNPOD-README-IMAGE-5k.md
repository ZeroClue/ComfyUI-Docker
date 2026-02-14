# RunPod Image Generation Deployment Guide

> 🎨 **Deploy ComfyUI for AI image generation on RunPod with cost optimization**

## 🚀 Quick Start

1. **Deploy**: `zeroclue/comfyui:base-torch2.8.0-cu126`
2. **Set Environment**: `IMAGE_PRESET_DOWNLOAD=SDXL_BASE_V1`
3. **GPU Choice**: RTX 4090 (speed) or A40 (VRAM)
4. **Access**: ComfyUI port 3000, Preset Manager port 9000

## 🖥️ Hardware Recommendations

| GPU | VRAM | Spot Price | Best For |
|-----|------|------------|-----------|
| **RTX 4090** | 24GB | $0.34/hr | Speed & value |
| **A40** | 48GB | $0.79/hr | Large models |
| **L40** | 48GB | ~$0.49/hr | Balance |
| **RTX 3090** | 24GB | $0.26/hr | Budget |

**Recommendation**: Start with RTX 4090.

## 🐳 Docker Configuration

**Recommended Images**:
- **RunPod Optimized**: `zeroclue/comfyui:minimal-torch2.8.0-cu126`
- **Full Setup**: `zeroclue/comfyui:base-torch2.8.0-cu126`
- **Cost Optimized**: `zeroclue/comfyui:slim-torch2.8.0-cu126`

**Features**: ComfyUI + Manager + Preset Manager + 24 custom nodes + CUDA 12.6

## ⚙️ Environment Variables

**Essential Settings**:
```bash
IMAGE_PRESET_DOWNLOAD="SDXL_BASE_V1,REALISTIC_VISION_V6"
ACCESS_PASSWORD="your-secure-password"
ENABLE_PRESET_MANAGER=true
```

**Popular Combinations**:
```bash
# High-Quality Photorealistic
IMAGE_PRESET_DOWNLOAD="SDXL_BASE_V1,REALISTIC_VISION_V6,ESRGAN_MODELS"

# State-of-the-Art (12B Parameters)
IMAGE_PRESET_DOWNLOAD="FLUX_DEV_BASIC,FLUX_COMPLETE"

# Complete Workflow
IMAGE_PRESET_DOWNLOAD="SDXL_COMPLETE_WORKFLOW"
```

## 💾 Network Volume Setup

**Configuration**:
- **Size**: 50GB+ (models are large)
- **Type**: Secure Cloud (recommended)

**Directory Structure**:
```
/workspace/ComfyUI/
├── models/    # Downloaded models
├── input/     # Your reference images
├── output/    # Generated images (persistent!)
└── user/      # Workflows & settings
```

## 📋 Step-by-Step Deployment

### 1. Create Network Volume
1. **Storage** → **Network Volumes** → **Create**
2. **Size**: 50GB+, **Data Center**: Same region as GPU

### 2. Deploy Pod
1. **Pods** → **Deploy Pod**
2. **Container Image**: `zeroclue/comfyui:base-torch2.8.0-cu126`
3. **GPU**: RTX 4090 or A40
4. **Network Volume**: Select your volume
5. **Ports**: Expose 3000, 8080, 8888, 9000

### 3. Configure Environment
```bash
IMAGE_PRESET_DOWNLOAD="SDXL_BASE_V1"
ACCESS_PASSWORD="your-password"
ENABLE_PRESET_MANAGER=true
```

### 4. Launch and Access
1. Click **Deploy**, wait 2-5 minutes
2. **ComfyUI**: `https://[pod-id]-3000.proxy.runpod.net`
3. **Preset Manager**: `https://[pod-id]-9000.proxy.runpod.net`

## 💰 Cost Optimization: Template Switching

**Strategy**: Build with base, then switch to slim

**Phase 1**: Use `base` image initially, install custom nodes, download models, create workflows

**Phase 2**: Stop pod, change to `slim`, restart with same network volume

**Benefit**: 30-50% cost reduction, same functionality

**Template Comparison**:
| Template | Size | Use Case |
|----------|------|----------|
| **base** | ~8GB | Initial setup |
| **slim** | ~4GB | Production |

**How to Switch**:
1. **Stop Pod**: Pods → Select → Stop
2. **Change Image**: Edit → `slim-torch2.8.0-cu126`
3. **Restart**: Start with same network volume

**Why This Works**: Custom nodes, models, and workflows are stored in your network volume.

## 🎨 Image Presets

**📖 Complete Documentation**: [IMAGE_PRESET_DOWNLOAD Wiki](https://github.com/ZeroClue/ComfyUI-Docker/wiki/IMAGE_PRESET_DOWNLOAD)

**Popular Presets**:
- `SDXL_BASE_V1` - High-quality base model
- `REALISTIC_VISION_V6` - Photorealistic portraits
- `FLUX_DEV_BASIC` - 12B parameter (competing with Midjourney)
- `JUGGERNAUT_XL_V8` - Artistic excellence
- `ESRGAN_MODELS` - Image upscaling

**Beginner Setup**: `IMAGE_PRESET_DOWNLOAD="SDXL_COMPLETE_WORKFLOW"`

**Photography Setup**: `IMAGE_PRESET_DOWNLOAD="SDXL_BASE_V1,REALISTIC_VISION_V6,ESRGAN_MODELS"`

## 🔌 Web Interfaces

- **ComfyUI**: `https://[pod-id]-3000.proxy.runpod.net` (Main interface)
- **Preset Manager**: `https://[pod-id]-9000.proxy.runpod.net` (Model management)
- **Code-Server**: `https://[pod-id]-8080.proxy.runpod.net` (VS Code)
- **JupyterLab**: `https://[pod-id]-8888.proxy.runpod.net` (Notebooks)

## 📈 Best Practices

**Cost Optimization**:
- Start with `base`, switch to `slim` after setup
- Use spot instances when possible
- Stop pods when not in use

**Quality Results**:
- Use appropriate model resolution
- Experiment with different samplers
- Optimize prompts for your chosen model

---

**Key Takeaways**:
1. Start with `base` template for setup
2. Switch to `slim` for cost savings
3. Use Preset Manager for model management
4. Monitor costs and storage usage

Happy image generating! 🎨

**📚 Resources**: [Main README](README.md) | [IMAGE_PRESET_DOWNLOAD Wiki](https://github.com/ZeroClue/ComfyUI-Docker/wiki/IMAGE_PRESET_DOWNLOAD) | [GitHub](https://github.com/ZeroClue/ComfyUI-Docker)