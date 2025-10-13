# RUNPOD README: LTXV_COMPLETE_WORKFLOW

## Quick Start
**Model**: Complete LTX-Video Setup with Upscalers
**Size**: 8GB | **VRAM**: 12GB+ | **Type**: Production-ready Real-time Video

```bash
# RunPod Template Configuration
Container Image: zeroclue/comfyui:base-torch2.8.0-cu126
Environment Variables:
  - PRESET_DOWNLOAD=LTXV_COMPLETE_WORKFLOW
GPU Selection: RTX 4090 (24GB) or A100 (40GB)
Disk Space: 30GB minimum
```

## RunPod Configuration

### Container Settings
- **Image**: `zeroclue/comfyui:base-torch2.8.0-cu126`
- **GPU**: RTX 4090 recommended for optimal performance
- **CPU**: 6+ cores
- **Memory**: 24GB+ system RAM
- **Storage**: 30GB+ SSD

### Port Mapping
- **3000** → ComfyUI Web Interface
- **8080** → VS Code (optional)
- **8888** → JupyterLab (optional)

### Environment Variables
```bash
PRESET_DOWNLOAD=LTXV_COMPLETE_WORKFLOW
ACCESS_PASSWORD=your_password  # Optional
COMFYUI_EXTRA_ARGS=--fast      # Recommended for production
```

### Volume Mount (Recommended)
```bash
/workspace → Persistent storage for workflows and outputs
```

## Model Details

### Included Models
- **LTX-Video 2B DiT**: Main generation model (4.5GB)
- **Temporal Upscaler**: Frame interpolation upscaler (1.6GB)
- **Spatial Upscaler**: Resolution enhancement upscaler (1.6GB)
- **Format**: FP8 scaled for optimal performance
- **Resolution**: 768x512 → up to 4K with upscalers

### File Organization
```
/workspace/ComfyUI/models/diffusion_models/
├── ltx-video-2b-v0.9.8-distilled-fp8.safetensors (4.5GB)
├── ltx-video-temporal-upscaler-v0.9.8.safetensors (1.6GB)
└── ltx-video-spatial-upscaler-v0.9.8.safetensors (1.6GB)
```

### Performance Characteristics
- **Base Generation**: ~2-3 seconds per frame (RTX 4090)
- **Temporal Upscaling**: 2x frame rate enhancement
- **Spatial Upscaling**: 2x resolution enhancement
- **Combined Output**: Up to 4K at 60 FPS

## Usage Examples

### Production Workflow
```python
# Complete Production Pipeline
# 1. Generate base video at 768x512, 30fps
# 2. Apply temporal upscaling for smooth motion
# 3. Apply spatial upscaling for high resolution
# 4. Export at 4K, 60fps
```

### High-Quality Output
```bash
# Recommended settings for best quality
prompt: "Cinematic 4K footage of [detailed scene]"
resolution: [768, 512]  # Base generation
upscaling_factor: 2x     # To 1536x1024
frame_enhancement: 60fps # Enhanced from 30fps
```

### Batch Production
```bash
# For commercial video production
# Use production-optimized image variant
# Container: zeroclue/comfyui:production-torch2.8.0-cu126
# Reduces memory overhead, faster startup
```

## Technical Specifications

### Supported Resolutions
- **Base**: 768x512 @ 30 FPS
- **Temporal Upscaled**: Same resolution, 60 FPS
- **Spatial Upscaled**: 1536x1024 @ 30 FPS
- **Combined**: 1536x1024 @ 60 FPS

### Performance Tiers
| GPU | Base Speed | Temporal Upscaling | Spatial Upscaling |
|-----|------------|-------------------|-------------------|
| RTX 3060 (12GB) | ~5s/frame | ~8s/frame | ~10s/frame |
| RTX 4090 (24GB) | ~2s/frame | ~3s/frame | ~4s/frame |
| A100 (40GB) | ~1.5s/frame | ~2s/frame | ~3s/frame |

### Memory Usage
- **Base Generation**: ~6GB VRAM
- **Temporal Upscaling**: +4GB VRAM
- **Spatial Upscaling**: +6GB VRAM
- **Total**: ~16GB VRAM peak

## Production Optimization

### Recommended Settings
```bash
# For production workloads
COMFYUI_EXTRA_ARGS=--fast --output-format mp4 --output-quality high

# For batch processing
# Consider using production image variant
# Container: zeroclue/comfyui:production-torch2.8.0-cu126
```

### Workflow Automation
```python
# Automated production pipeline
# 1. Queue multiple prompts
# 2. Apply upscaling automatically
# 3. Export in desired format
# 4. Archive results
```

### Quality Control
```bash
# Monitor output quality
# Use reference frames for consistency
# Validate motion smoothness
# Check resolution and frame rate
```

## Troubleshooting

### Memory Issues
**Out of Memory with Upscalers**:
- Use RTX 4090 or A100
- Reduce batch size to 1
- Close other applications
- Consider base model only if needed

### Performance Optimization
```bash
# Monitor GPU utilization
nvidia-smi -l 1

# Optimize for throughput
COMFYUI_EXTRA_ARGS=--fast --disable-vae-slicing

# Clear cache between jobs
rm -rf /workspace/ComfyUI/temp/*
```

### Quality Issues
**Upscaling Artifacts**:
- Ensure clean base generation
- Use appropriate upscaling strength
- Verify input resolution compatibility
- Test with different content types

### Model Loading
```bash
# Verify all models loaded
ls -la /workspace/ComfyUI/models/diffusion_models/ltx-*

# Check ComfyUI logs for errors
tail -f /workspace/ComfyUI/user/comfyui_3000.log
```

## Production Deployment

### Container Optimization
```bash
# Production-ready configuration
Container Image: zeroclue/comfyui:production-torch2.8.0-cu126
Environment: PRESET_DOWNLOAD=LTXV_COMPLETE_WORKFLOW
GPU: A100 (40GB) for best performance
Storage: High-throughput SSD
```

### Scaling Considerations
- **Horizontal**: Deploy multiple containers for parallel processing
- **Vertical**: Use higher-tier GPUs for faster generation
- **Storage**: Ensure sufficient I/O for large video files

### Cost Optimization
```bash
# For budget-conscious production
# Use base model only, external upscaling
PRESET_DOWNLOAD=LTXV_2B_FP8_SCALED

# For premium quality
# Use complete workflow as intended
PRESET_DOWNLOAD=LTXV_COMPLETE_WORKFLOW
```

## Use Case Recommendations

### Ideal For
- **Commercial Production**: High-quality video content
- **Content Creation**: Professional video generation
- **Film Industry**: Pre-visualization and concept work
- **Marketing**: High-resolution promotional content

### Output Examples
- **Social Media**: 1080p @ 60fps content
- **Web Content**: 4K @ 30fps cinematic footage
- **Advertising**: High-resolution product videos
- **Creative Projects**: Artistic video generation

## Support

**Documentation**: [LTX-Video Official](https://huggingface.co/Lightricks/LTX-Video)
**Community**: [ComfyUI Community Discord](https://discord.gg/comfyui)
**Issues**: [ZeroClue GitHub Issues](https://github.com/ZeroClue/ComfyUI-Docker/issues)

---

*Last Updated: 2025-01-13 | ZeroClue ComfyUI-Docker*