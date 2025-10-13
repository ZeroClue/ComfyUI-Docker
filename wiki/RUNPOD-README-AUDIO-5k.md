# RunPod Audio Generation Deployment Guide

> 🎵 **Deploy ComfyUI for AI audio generation on RunPod with music and speech synthesis**

> ⚠️ **Note**: Audio generation is experimental and may have compatibility issues

## 🚀 Quick Start

1. **Deploy**: `zeroclue/comfyui:base-torch2.8.0-cu126`
2. **Set Environment**: `AUDIO_PRESET_DOWNLOAD=MUSICGEN_MEDIUM,BARK_BASIC`
3. **GPU Choice**: RTX 4090 (24GB VRAM) or A40 (48GB VRAM)
4. **Access**: ComfyUI port 3000, Preset Manager port 9000

## 🖥️ Hardware Recommendations

| GPU | VRAM | Spot Price | Best For |
|-----|------|------------|-----------|
| **RTX 4090** | 24GB | $0.34/hr | Audio generation speed |
| **A40** | 48GB | $0.79/hr | Large audio models |
| **L40** | 48GB | ~$0.49/hr | Balance |
| **RTX 3090** | 24GB | $0.26/hr | Budget audio |

**Recommendation**: RTX 4090 is sufficient for most audio generation tasks.

## 🐳 Docker Configuration

**Recommended Images**:
- **Full Setup**: `zeroclue/comfyui:base-torch2.8.0-cu126`
- **Cost Optimized**: `zeroclue/comfyui:slim-torch2.8.0-cu126`

**Features**: ComfyUI + Manager + Audio custom nodes + CUDA 12.6

## ⚙️ Environment Variables

**Essential Settings**:
```bash
AUDIO_PRESET_DOWNLOAD="MUSICGEN_MEDIUM,BARK_BASIC"
ACCESS_PASSWORD="your-secure-password"
```

**Popular Combinations**:
```bash
# Music Generation
AUDIO_PRESET_DOWNLOAD="MUSICGEN_MEDIUM,ACE_STEP"

# Speech Synthesis
AUDIO_PRESET_DOWNLOAD="BARK_BASIC,TTS_AUDIO_SUITE"

# Complete Setup
AUDIO_PRESET_DOWNLOAD="AUDIO_PRODUCTION"
```

## 💾 Network Volume Setup

**Configuration**:
- **Size**: 30GB+ (audio models are smaller than video)
- **Type**: Secure Cloud (recommended)

## 📋 Step-by-Step Deployment

### 1. Create Network Volume
1. **Storage** → **Network Volumes** → **Create**
2. **Size**: 30GB+, **Data Center**: Same region as GPU

### 2. Deploy Pod
1. **Pods** → **Deploy Pod**
2. **Container Image**: `zeroclue/comfyui:base-torch2.8.0-cu126`
3. **GPU**: RTX 4090 or A40
4. **Network Volume**: Select your volume
5. **Ports**: Expose 3000, 8080, 8888, 9000

### 3. Configure Environment
```bash
AUDIO_PRESET_DOWNLOAD="MUSICGEN_MEDIUM,BARK_BASIC"
ACCESS_PASSWORD="your-password"
```

### 4. Launch and Access
1. Click **Deploy**, wait 3-5 minutes
2. **ComfyUI**: `https://[pod-id]-3000.proxy.runpod.net`
3. **Preset Manager**: `https://[pod-id]-9000.proxy.runpod.net`

## 💰 Cost Optimization: Template Switching

**Strategy**: Build with base, then switch to slim

**Phase 1**: Use `base` image initially, install audio nodes, download models, create workflows

**Phase 2**: Stop pod, change to `slim`, restart with same network volume

**Benefit**: 30-50% cost reduction, same audio functionality

**Template Comparison**:
| Template | Size | Use Case |
|----------|------|----------|
| **base** | ~8GB | Initial audio setup |
| **slim** | ~6GB | Audio production |

**How to Switch**:
1. **Stop Pod**: Pods → Select → Stop
2. **Change Image**: Edit → `slim-torch2.8.0-cu126`
3. **Restart**: Start with same network volume

## 🎵 Audio Generation Presets

**📖 Complete Documentation**: [AUDIO_PRESET_DOWNLOAD Wiki](https://github.com/ZeroClue/ComfyUI-Docker/wiki/AUDIO_PRESET_DOWNLOAD)

**Popular Presets**:
- `MUSICGEN_MEDIUM` - Medium-quality music generation
- `BARK_BASIC` - High-quality text-to-speech
- `TTS_AUDIO_SUITE` - Comprehensive TTS models
- `PARLER_TTS` - Advanced voice synthesis

**Beginner Setup**: `AUDIO_PRESET_DOWNLOAD="MUSICGEN_MEDIUM,BARK_BASIC"`

**Music Production**: `AUDIO_PRESET_DOWNLOAD="AUDIO_MUSIC_COMPLETE"`

## 🎤 Audio Workflows

### Text-to-Speech (TTS)
1. **Load TTS Model**: Use BARK or TTS preset
2. **Text Input**: Enter your script or text
3. **Voice Settings**: Choose voice style and parameters
4. **Generate**: Queue prompt (takes 30 seconds - 2 minutes)

### Music Generation
1. **Load Music Model**: Use MusicGen preset
2. **Prompt**: Describe the music style/mood
3. **Duration**: Set desired length (typically 30-120 seconds)
4. **Generate**: Queue prompt (takes 1-5 minutes)

## 🔌 Web Interfaces

- **ComfyUI**: `https://[pod-id]-3000.proxy.runpod.net` (Main audio interface)
- **Preset Manager**: `https://[pod-id]-9000.proxy.runpod.net`

## 📈 Best Practices

**Cost Optimization**:
- Start with `base`, switch to `slim` after setup
- Use shorter audio clips for testing
- Stop pods when not generating audio

**Audio Quality**:
- Use high-quality source text for TTS
- Experiment with different voice models
- Post-process audio for better results

**Experimental Nature**: Audio nodes may have compatibility issues. Report bugs to custom node repositories.

---

**Key Takeaways**:
1. Audio generation is experimental - use with caution
2. RTX 4090 is sufficient for most audio tasks
3. Audio models are smaller than video models
4. Report issues to custom node maintainers

Happy audio creating! 🎵

**📚 Resources**: [Main README](README.md) | [AUDIO_PRESET_DOWNLOAD Wiki](https://github.com/ZeroClue/ComfyUI-Docker/wiki/AUDIO_PRESET_DOWNLOAD)