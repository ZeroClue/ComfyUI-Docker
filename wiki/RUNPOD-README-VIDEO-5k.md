# RunPod Video Generation Deployment Guide

> 🎬 **Deploy ComfyUI for AI video generation on RunPod**

## 🚀 Quick Start

1. **Deploy**: `zeroclue/comfyui:base-torch2.8.0-cu126`
2. **Set Environment**: `PRESET_DOWNLOAD=WAN_22_5B_TIV2`
3. **GPU Choice**: A40 (48GB VRAM) or RTX 4090 (24GB VRAM minimum)
4. **Access**: ComfyUI port 3000, Preset Manager port 9000

## 🖥️ Hardware Recommendations

| GPU | VRAM | Spot Price | Best For |
|-----|------|------------|-----------|
| **A40** | 48GB | $0.79/hr | Large video models |
| **RTX 4090** | 24GB | $0.34/hr | Consumer-grade speed |
| **L40** | 48GB | ~$0.49/hr | Balance |

**Recommendation**: A40 for serious work, RTX 4090 for experimenting.

## 🐳 Docker Configuration

**Recommended Images**:
- **RunPod Optimized**: `zeroclue/comfyui:minimal-torch2.8.0-cu126`
- **Full Setup**: `zeroclue/comfyui:base-torch2.8.0-cu126`
- **Cost Optimized**: `zeroclue/comfyui:slim-torch2.8.0-cu126`

**Features**: ComfyUI + Manager + WAN 2.2 nodes + CUDA 12.6

## ⚙️ Environment Variables

**Essential Settings**:
```bash
PRESET_DOWNLOAD="WAN_22_5B_TIV2,WAN22_LIGHTNING_LORA"
ACCESS_PASSWORD="your-secure-password"
```

**Popular Combinations**:
```bash
# High-Quality Video
PRESET_DOWNLOAD="WAN_22_5B_TIV2,WAN22_LIGHTNING_LORA,WAN22_S2V_FP8_SCALED"

# Image-to-Video
PRESET_DOWNLOAD="WAN22_I2V_A14B_GGUF_Q8_0,WAN22_LIGHTNING_LORA"

# Complete Setup
PRESET_DOWNLOAD="WAN_22_5B_TIV2,WAN22_LIGHTNING_LORA,UPSCALE_MODELS"
```

## 💾 Network Volume Setup

**Configuration**:
- **Size**: 100GB+ (video models are large)
- **Type**: Secure Cloud (recommended)
- **RAM**: 64GB+ recommended

## 📋 Step-by-Step Deployment

### 1. Create Network Volume
1. **Storage** → **Network Volumes** → **Create**
2. **Size**: 100GB+, **Data Center**: Same region as GPU

### 2. Deploy Pod
1. **Pods** → **Deploy Pod**
2. **Container Image**: `zeroclue/comfyui:base-torch2.8.0-cu126`
3. **GPU**: A40 (48GB) or RTX 4090 (24GB minimum)
4. **Network Volume**: Select your volume
5. **Ports**: Expose 3000, 8080, 8888, 9000

### 3. Configure Environment
```bash
PRESET_DOWNLOAD="WAN_22_5B_TIV2"
ACCESS_PASSWORD="your-password"
```

### 4. Launch and Access
1. Click **Deploy**, wait 5-10 minutes (video models take longer)
2. **ComfyUI**: `https://[pod-id]-3000.proxy.runpod.net`
3. **Preset Manager**: `https://[pod-id]-9000.proxy.runpod.net`

## 💰 Cost Optimization: Template Switching

**Strategy**: Build with base, then switch to slim

**Phase 1**: Use `base` image initially, install video nodes, download models, create workflows

**Phase 2**: Stop pod, change to `slim`, restart with same network volume

**Benefit**: 30-50% cost reduction, same video functionality

**Template Comparison**:
| Template | Size | Use Case |
|----------|------|----------|
| **base** | ~8GB | Initial video setup |
| **slim** | ~6GB | Video slim |

**How to Switch**:
1. **Stop Pod**: Pods → Select → Stop
2. **Change Image**: Edit → `slim-torch2.8.0-cu126`
3. **Restart**: Start with same network volume

## 🎬 Video Generation Presets

**📖 Complete Documentation**: [PRESET_DOWNLOAD Wiki](https://github.com/ZeroClue/ComfyUI-Docker/wiki/PRESET_DOWNLOAD)

**Popular Presets**:
- `WAN_22_5B_TIV2` - Main WAN 2.2 text-to-video model
- `WAN22_I2V_A14B_GGUF_Q8_0` - Image-to-video conversion
- `WAN22_LIGHTNING_LORA` - Faster generation LoRA
- `WAN22_S2V_FP8_SCALED` - Speech-to-video conversion
- `UPSCALE_MODELS` - Video enhancement

**Beginner**: `PRESET_DOWNLOAD="WAN_22_5B_TIV2,WAN22_LIGHTNING_LORA"`

**Pro**: `PRESET_DOWNLOAD="WAN_22_5B_TIV2,WAN22_I2V_A14B_GGUF_Q8_0,WAN22_LIGHTNING_LORA,UPSCALE_MODELS"`

## 🎥 Video Workflows

### Text-to-Video (T2V)
1. **Load WAN 2.2 Model**: Use preset loader
2. **Text Prompt**: Describe your video
3. **Settings**: 720p, 24fps, 5-10 seconds
4. **Generate**: Queue prompt (takes 2-5 minutes)

### Image-to-Video (I2V)
1. **Upload Image**: Place in `/workspace/ComfyUI/input/`
2. **Load Image**: Use image loader node
3. **Connect to WAN I2V**: Select I2V model
4. **Generate**: Animate your image (1-3 minutes)

## 🔌 Web Interfaces

- **ComfyUI**: `https://[pod-id]-3000.proxy.runpod.net` (Main video interface)
- **Preset Manager**: `https://[pod-id]-9000.proxy.runpod.net` (Video model management)

## 📈 Best Practices

**Cost Optimization**:
- Start with `base`, switch to `slim` after setup
- Use shorter video lengths for testing
- Stop pods when not generating video

**Video Quality**:
- Use A40 GPU for best results
- Generate at 720p, then upscale
- Use Lightning LoRA for faster iterations

**Memory Management**:
- Minimum 24GB VRAM for basic video
- 48GB VRAM for professional work
- 64GB+ system RAM recommended

---

Happy video creating! 🎬

**📚 Resources**: [Main README](README.md) | [PRESET_DOWNLOAD Wiki](https://github.com/ZeroClue/ComfyUI-Docker/wiki/PRESET_DOWNLOAD)