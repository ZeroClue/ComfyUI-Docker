# RunPod Audio Generation Deployment Guide

> AI audio generation on RunPod - Music, speech synthesis, and more

> Note: Audio generation is experimental and may have compatibility issues

<a href="https://www.buymeacoffee.com/thezeroclue" target="_blank" rel="noopener noreferrer">
<img src="https://www.buymeacoffee.com/assets/img/custom_images/yellow_img.png" alt="Buy me a coffee" width="105px" />
</a>

---

## Quick Start

1. **Deploy**: `zeroclue/comfyui:minimal-torch2.8.0-cu126`
2. **Set Environment**: `AUDIO_PRESET_DOWNLOAD=ACE_STEP_V1_3_5B`
3. **GPU Choice**: RTX 4090 (24GB) or A40 (48GB)
4. **Access**: ComfyUI port 3000, Studio port 5000

---

## Hardware Recommendations

| GPU | VRAM | Spot Price | Best For |
|-----|------|------------|----------|
| **RTX 4090** | 24GB | $0.34/hr | Speed & value |
| **A40** | 48GB | $0.79/hr | Large models |
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
# Audio presets (5 available)
AUDIO_PRESET_DOWNLOAD="ACE_STEP_V1_3_5B"

# Security
ACCESS_PASSWORD="your-secure-password"
```

### Preset Combinations

```bash
# Music Generation
AUDIO_PRESET_DOWNLOAD="ACE_STEP_V1_3_5B"

# Multi-track Composition
AUDIO_PRESET_DOWNLOAD="ACE_STEP_MULTI_TRACK"

# Complete Audio Suite
AUDIO_PRESET_DOWNLOAD="COMPLETE_AUDIO_SUITE"
```

---

## Audio Presets (5 Available)

### ACE Step Series
| Preset | Size | Description |
|--------|------|-------------|
| `ACE_STEP_V1_3_5B` | 7.2GB | Music & lyrics generation |
| `ACE_STEP_AUDIO_TO_AUDIO` | 7.2GB | Audio transformation & remixing |
| `ACE_STEP_MUSIC_EXTENSION` | 7.3GB | Extend/continue music pieces |
| `ACE_STEP_MULTI_TRACK` | 7.8GB | Multi-track composition |

### Complete Suite
| Preset | Size | Description |
|--------|------|-------------|
| `COMPLETE_AUDIO_SUITE` | 10.9GB | MusicGen + Bark + TTS |

---

## Network Access

| Port | Service | Purpose |
|------|---------|---------|
| **3000** | ComfyUI | Node-based audio workflows |
| **8082** | Unified Dashboard | Primary management interface |
| 8080 | Code Server | VS Code IDE |
| 8888 | JupyterLab | Notebook environment |

---

## Deployment Steps

### 1. Create Network Volume
- **Storage** > **Network Volumes** > **Create**
- **Size**: 30GB+ (audio models are smaller)
- **Data Center**: Same region as GPU

### 2. Deploy Pod
- **Pods** > **Deploy Pod**
- **Container Image**: `zeroclue/comfyui:minimal-torch2.8.0-cu126`
- **GPU**: RTX 4090 or A40
- **Network Volume**: Select your volume

### 3. Configure
```bash
AUDIO_PRESET_DOWNLOAD="ACE_STEP_V1_3_5B"
ACCESS_PASSWORD="your-password"
```

### 4. Access
- **ComfyUI**: `https://[pod-id]-3000.proxy.runpod.net`
- **Studio**: `https://[pod-id]-5000.proxy.runpod.net`
- **Preset Manager**: `https://[pod-id]-9000.proxy.runpod.net`

---

## Audio Workflows

### Music Generation
1. Load ACE Step model via preset
2. Enter prompt describing music style/mood
3. Set duration (30-120 seconds typical)
4. Generate (1-5 minutes)

### Audio Transformation
1. Upload audio sample
2. Load ACE_STEP_AUDIO_TO_AUDIO preset
3. Apply transformation settings
4. Generate remix/variation

---

## Cost Optimization

**Template Switching Strategy**:
1. Use `base` image for initial setup
2. Download models, create workflows
3. Stop pod, switch to `slim`
4. Restart with same network volume

**Benefit**: 30-50% cost reduction

---

## Storage Paths

```
/workspace/ComfyUI/models/     # Audio models
/workspace/ComfyUI/output/     # Generated audio
/workspace/ComfyUI/input/      # Upload samples
/workspace/config/workflows/   # Studio workflows
```

---

## Tips

- RTX 4090 sufficient for most audio tasks
- Audio models smaller than video (30GB storage enough)
- Use Studio for simple generation, ComfyUI for complex
- Report custom node issues to maintainers

---

**Resources**: [Main README](RUNPOD-README-5k.md) | [GitHub](https://github.com/ZeroClue/ComfyUI-Docker)
