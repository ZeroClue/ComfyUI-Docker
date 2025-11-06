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

## 🏗️ RunPod Pod Configuration

### Recommended Pod Settings

| Setting | Recommended Value | Notes |
|---------|-------------------|-------|
| **GPU Type** | RTX A4000 / RTX A5000 / RTX A6000 | Higher GPUs = faster generation |
| **CPU Cores** | 4-8 vCPUs | Adequate for preprocessing |
| **Memory** | 16-32 GB RAM | Depends on model size |
| **Storage** | 50-200 GB Network Storage | For models and outputs |
| **Container Image** | See variant table below | Choose based on use case |

### Container Image Selection

#### Development Variants (Full Tooling)
```bash
# Complete development environment with custom nodes
zeroclue/comfyui:base-torch2.8.0-cu126
```

#### Production Variants (Cost Optimized)
```bash
# Production optimized - recommended for most users
zeroclue/comfyui:production-torch2.8.0-cu126
```

---

## 🔧 Environment Variables Configuration

### Required Variables (Add in Pod Settings)

| Variable | Value | Description |
|----------|-------|-------------|
| `ACCESS_PASSWORD` | `your_password` | Optional password protection |

### Optional Variables for Enhanced Features

| Variable | Example Value | When to Use |
|----------|---------------|-------------|
| `TIME_ZONE` | `America/New_York` | Set your local timezone |
| `COMFYUI_EXTRA_ARGS` | `--fast` | ComfyUI performance tweaks |
| `INSTALL_SAGEATTENTION` | `True` | Ampere+ GPUs for speed boost |
| `FORCE_SYNC_ALL` | `True` | Force fresh workspace setup |

### Preset Download Variables

Choose **one or more** of these for automatic model downloads:

```bash
# Video Generation Presets
PRESET_DOWNLOAD=WAN_22_5B_TIV2,WAN22_LIGHTNING_LORA

# Image Generation Presets
IMAGE_PRESET_DOWNLOAD=SDXL_BASE_V1,REALISTIC_VISION_V6

# Audio Generation Presets (Experimental)
AUDIO_PRESET_DOWNLOAD=MUSICGEN_MEDIUM,BARK_BASIC
```

---

## 🎬 Preset System Configuration

### Video Generation Setup

For video generation workflows:

```bash
# WAN Video Models
PRESET_DOWNLOAD=WAN_22_5B_TIV2,WAN22_LIGHTNING_LORA

# Available options:
# WAN_22_5B_TIV2 (Main video model)
# WAN22_I2V_A14B_GGUF_Q8_0 (Image-to-Video)
# WAN22_LIGHTNING_LORA (Faster inference)
# WAINSFW_V140 (Image model for video)
```

### Image Generation Setup

For high-quality image generation:

```bash
# Professional SDXL Setup
IMAGE_PRESET_DOWNLOAD=SDXL_BASE_V1,REALISTIC_VISION_V6,ESRGAN_MODELS

# Flux Models (State-of-the-art)
IMAGE_PRESET_DOWNLOAD=FLUX_DEV_BASIC,FLUX_COMPLETE

# Chinese Text Optimization
IMAGE_PRESET_DOWNLOAD=QWEN_IMAGE_CHINESE,QWEN_IMAGE_COMPLETE
```

### Audio Generation Setup (Experimental)

⚠️ **Note**: Audio generation is experimental and may have stability issues.

```bash
# Music Generation
AUDIO_PRESET_DOWNLOAD=MUSICGEN_MEDIUM,ACE_STEP

# Voice Synthesis
AUDIO_PRESET_DOWNLOAD=BARK_BASIC,TTS_AUDIO_SUITE

# Complete Audio Production
AUDIO_PRESET_DOWNLOAD=AUDIO_PRODUCTION
```

---

## 🌐 Network Access & Port Configuration

### Exposed Ports

| Port | Service | Access Method |
|------|---------|---------------|
| **3000** | ComfyUI | Primary web interface |
| 8080 | code-server | Development IDE (if in image) |
| 8888 | JupyterLab | Notebook environment (if in image) |
| 22 | SSH | Command line access (with SSH key) |

### Accessing Services

1. **ComfyUI**: Click the **Port 3000** link in your RunPod console
2. **SSH Access**: Add your SSH public key as `PUBLIC_KEY` environment variable
3. **Development Tools**: Access via respective port links (8080, 8888)

### Security Considerations

- **Public Access**: All ports are publicly accessible by default
- **Password Protection**: Set `ACCESS_PASSWORD` for web interfaces
- **SSH Keys**: Use SSH keys instead of passwords for CLI access

---

## 💾 Storage Management

### Network Storage Setup

1. **Create Storage Volume**:
   - Go to **Storage → Network Storage**
   - Create volume with 50-200GB space
   - Attach to your pod

2. **Storage Paths**:
   ```
   /workspace/ComfyUI/models/     # AI models
   /workspace/ComfyUI/output/     # Generated content
   /workspace/ComfyUI/input/      # Upload files here
   /workspace/ComfyUI/user/       # Workflows and settings
   ```

### Persistent Data

All important data is automatically stored in network storage:
- ✅ Downloaded models and presets
- ✅ Custom nodes and workflows
- ✅ Generated images and videos
- ✅ Configuration files

### Storage Optimization Tips

- **Clean Outputs**: Regularly clean `/workspace/ComfyUI/output/`
- **Model Management**: Delete unused models from `/workspace/ComfyUI/models/`
- **Monitor Usage**: Check storage consumption in RunPod console

---

## 💰 Cost Optimization Strategies

### Choose the Right Variant

| Budget Level | Recommended Variant | Savings |
|--------------|---------------------|---------|
| **Premium** | `base-torch2.8.0-cu126` | Full features, higher cost |
| **Balanced** | `production-torch2.8.0-cu126` | 30-50% savings |

### GPU Selection Guide

| GPU Type | Best For | Hourly Cost (Estimate) |
|----------|----------|------------------------|
| **RTX A4000** | Production, video generation | $0.35-0.60 |
| **RTX A5000** | Professional workflows | $0.50-0.80 |
| **RTX A6000** | Heavy workloads, batch processing | $0.80-1.20 |

### Cost Saving Tips

1. **Use Production Variants**: 30-50% cost reduction
2. **Right-Size GPU**: Don't overprovision GPU memory
3. **Monitor Usage**: Stop pods when not in use
4. **Storage Cleanup**: Regular cleanup of generated content
5. **Batch Processing**: Queue multiple jobs for efficiency

---

## 🚀 Ready-to-Use Pod Templates

### Template 1: Professional Video Generation

**Image**: `zeroclue/comfyui:production-torch2.8.0-cu126`
**GPU**: RTX A4000
**Environment Variables**:
```bash
PRESET_DOWNLOAD=WAN_22_5B_TIV2,WAN22_LIGHTNING_LORA,WAN22_NSFW_LORA
TIME_ZONE=America/New_York
ACCESS_PASSWORD=secure_password_123
```

### Template 2: High-Quality Image Generation

**Image**: `zeroclue/comfyui:production-torch2.8.0-cu126`
**GPU**: RTX A4000
**Environment Variables**:
```bash
IMAGE_PRESET_DOWNLOAD=SDXL_BASE_V1,REALISTIC_VISION_V6,ESRGAN_MODELS
TIME_ZONE=America/New_York
ACCESS_PASSWORD=secure_password_123
```

### Template 3: Budget Development

**Image**: `zeroclue/comfyui:base-torch2.8.0-cu126`
**GPU**: RTX A4000
**Environment Variables**:
```bash
TIME_ZONE=America/New_York
ACCESS_PASSWORD=secure_password_123
```

### Template 4: Complete Multimedia Production

**Image**: `zeroclue/comfyui:base-torch2.8.0-cu126`
**GPU**: RTX A5000
**Environment Variables**:
```bash
PRESET_DOWNLOAD=WAN_22_5B_TIV2,WAN22_LIGHTNING_LORA
IMAGE_PRESET_DOWNLOAD=SDXL_BASE_V1,REALISTIC_VISION_V6
AUDIO_PRESET_DOWNLOAD=AUDIO_PRODUCTION
TIME_ZONE=America/New_York
ACCESS_PASSWORD=secure_password_123
```

---

## 🔍 Troubleshooting

### Common Issues & Solutions

#### Pod Won't Start
- **Check GPU Availability**: Try a different GPU type
- **Verify Image Tag**: Ensure correct image name and tag
- **Check Storage**: Ensure network storage is properly attached

#### Models Not Downloading
- **Check Internet**: Verify pod has internet access
- **Storage Space**: Ensure enough disk space available
- **Preset Names**: Verify preset names are correct

#### Slow Performance
- **GPU Upgrade**: Try a more powerful GPU
- **Use Production Variant**: Switch from `base` to `production`
- **Enable SageAttention**: Add `INSTALL_SAGEATTENTION=True` (Ampere+ GPUs)

#### Access Issues
- **Port Not Accessible**: Wait 2-3 minutes after pod start
- **Password Not Working**: Check `ACCESS_PASSWORD` environment variable
- **SSH Connection**: Verify SSH key is correctly configured

### Getting Help

1. **Check Logs**: Use the terminal in RunPod console to view logs
2. **GitHub Issues**: [Report issues here](https://github.com/ZeroClue/ComfyUI-Docker/issues)
3. **Community**: Join the ComfyUI community for general questions
4. **RunPod Support**: Contact RunPod for platform-specific issues

### Log Locations

```bash
# ComfyUI logs
/workspace/ComfyUI/user/comfyui_3000.log

# Service logs
/workspace/logs/code-server.log
/workspace/logs/jupyterlab.log

# System logs (if needed)
docker logs <container_name>
```

---

## 📚 Additional Resources

### Documentation
- [Main Project README](README.md)
- [Environment Variables Reference](README.md#-environment-variables)
- [Preset System Documentation](README.md#-triple-preset-system)
- [Custom Nodes List](README.md#-pre-installed-components)

### External Links
- [RunPod Documentation](https://docs.runpod.io/)
- [ComfyUI Official Repository](https://github.com/comfyanonymous/ComfyUI)
- [ComfyUI Community](https://discord.com/invite/comfyui)

### Model Resources
- [Hugging Face Models](https://huggingface.co/models)
- [CivitAI Models](https://civitai.com/)
- [ComfyUI Workflows](https://openart.ai/workflows/)

---

## 🎉 Getting Started Checklist

- [ ] Choose appropriate image variant for your use case
- [ ] Select suitable GPU type (RTX A4000+ recommended)
- [ ] Configure network storage (50GB+)
- [ ] Set environment variables for presets
- [ ] Deploy pod and wait for initialization
- [ ] Access ComfyUI via Port 3000
- [ ] Test with a simple generation workflow
- [ ] Monitor costs and optimize as needed

**Happy Generating! 🚀**

---

> 💡 **Pro Tip**: Start with the `production` variant for the best balance of features and cost. You can always switch variants later without losing your data.