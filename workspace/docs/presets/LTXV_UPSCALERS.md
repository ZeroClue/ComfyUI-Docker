# RUNPOD README: LTXV_UPSCALERS

## Quick Start
**Model**: LTX-Video Temporal & Spatial Upscalers
**Size**: 3.2GB | **VRAM**: 8GB+ | **Type**: Enhancement Models Only

```bash
# RunPod Template Configuration
Container Image: zeroclue/comfyui:base-torch2.8.0-cu126
Environment Variables:
  - PRESET_DOWNLOAD=LTXV_UPSCALERS
GPU Selection: RTX 3060 (12GB) or better
Disk Space: 15GB minimum
```

## Important Notice
**This preset contains upscaler models ONLY** - it does not include a base generation model. You must use this with an LTX-Video base model (like LTXV_2B_FP8_SCALED) for complete functionality.

## RunPod Configuration

### Container Settings
- **Image**: `zeroclue/comfyui:base-torch2.8.0-cu126`
- **GPU**: RTX 3060+ recommended
- **CPU**: 4+ cores
- **Memory**: 16GB+ system RAM
- **Storage**: 15GB+ SSD

### Port Mapping
- **3000** → ComfyUI Web Interface
- **8080** → VS Code (optional)
- **8888** → JupyterLab (optional)

### Environment Variables
```bash
# Use with base model for complete workflow
PRESET_DOWNLOAD="LTXV_2B_FP8_SCALED,LTXV_UPSCALERS"
ACCESS_PASSWORD=your_password  # Optional
COMFYUI_EXTRA_ARGS=--fast      # Recommended
```

### Volume Mount (Recommended)
```bash
/workspace → Persistent storage for enhanced video outputs
```

## Model Details

### Included Models
- **Temporal Upscaler**: Frame interpolation (1.6GB)
- **Spatial Upscaler**: Resolution enhancement (1.6GB)
- **Format**: FP8 for optimal performance
- **Compatibility**: Works with LTX-Video base models
- **Enhancement**: 2x frame rate, 2x resolution

### File Organization
```
/workspace/ComfyUI/models/diffusion_models/
├── ltx-video-temporal-upscaler-v0.9.8.safetensors (1.6GB)
└── ltx-video-spatial-upscaler-v0.9.8.safetensors (1.6GB)
```

### Enhancement Capabilities
- **Temporal Upscaling**: 30 FPS → 60 FPS
- **Spatial Upscaling**: 768x512 → 1536x1024
- **Combined Enhancement**: 4x quality improvement
- **Memory Usage**: +8GB VRAM during upscaling

## Usage Examples

### Complete Production Workflow
```bash
# Recommended: Use with base model
PRESET_DOWNLOAD="LTXV_2B_FP8_SCALED,LTXV_UPSCALERS"

# Workflow:
# 1. Generate base video at 768x512, 30fps
# 2. Apply temporal upscaling for smooth motion
# 3. Apply spatial upscaling for high resolution
# 4. Export enhanced result
```

### Enhancement Process
```python
# ComfyUI Workflow Enhancement
# Base Model Output: 768x512 @ 30fps
# Temporal Upscaling: 768x512 @ 60fps
# Spatial Upscaling: 1536x1024 @ 30fps
# Combined: 1536x1024 @ 60fps (recommended)
```

### Quality Improvement
```bash
# Enhancement Examples:
# Social Media: 768x512 → 1080p content
# Web Content: Standard → HD quality
# Professional: Base → Production-ready
```

## Technical Specifications

### Supported Enhancements
- **Temporal Enhancement**: 2x frame rate improvement
- **Spatial Enhancement**: 2x resolution improvement
- **Quality Enhancement**: 4x overall quality gain
- **Compatibility**: Works with all LTX-Video base models

### Performance Impact
| Enhancement | VRAM Impact | Processing Time | Quality Gain |
|-------------|-------------|-----------------|--------------|
| Temporal Only | +4GB | +50% time | Smoother motion |
| Spatial Only | +4GB | +100% time | Higher resolution |
| Combined | +8GB | +150% time | Maximum quality |

### Requirements
- **Base Model**: Required (not included in this preset)
- **Memory**: Additional 8GB VRAM for upscaling
- **Processing**: Extra time for enhancement steps
- **Storage**: Larger output files

## Troubleshooting

### Common Issues
**Missing Base Model**:
- This preset only contains upscalers
- Use with LTXV_2B_FP8_SCALED or other base models
- Check that base model loads successfully

**Memory Issues with Upscaling**:
- Requires additional 8GB VRAM
- Use RTX 4090 or better for combined upscaling
- Consider using only one upscaler if memory limited

**Quality Problems**:
- Ensure base model quality is good
- Check upscaler parameters
- Verify workflow connections in ComfyUI

### Model Verification
```bash
# Check upscaler models loaded
ls -la /workspace/ComfyUI/models/diffusion_models/ltx-video-*-upscaler*

# Verify in ComfyUI
grep "upscaler" /workspace/ComfyUI/user/comfyui_3000.log
```

### Performance Optimization
```bash
# For best performance
COMFYUI_EXTRA_ARGS=--fast

# Monitor memory during upscaling
nvidia-smi -l 1

# Clear cache between jobs
rm -rf /workspace/ComfyUI/temp/*
```

## Recommended Combinations

### Complete Workflow
```bash
# Full LTX-Video ecosystem
PRESET_DOWNLOAD=LTXV_COMPLETE_WORKFLOW

# Equivalent manual combination:
PRESET_DOWNLOAD="LTXV_2B_FP8_SCALED,LTXV_UPSCALERS"
```

### Premium Quality
```bash
# Best available quality
PRESET_DOWNLOAD="LTXV_13B_FP8_SCALED,LTXV_UPSCALERS"

# Requires A100 (40GB) GPU
# Ultimate quality for professional work
```

### Budget-Friendly
```bash
# Good quality, reasonable cost
PRESET_DOWNLOAD="LTXV_2B_GGUF_Q8_0,LTXV_UPSCALERS"

# Requires RTX 3080+ GPU
# Balanced quality and performance
```

## Use Case Recommendations

### Ideal For
- **Content Enhancement**: Improving existing LTX-Video output
- **Professional Production**: Adding upscaling to workflow
- **Quality Improvement**: Enhancing base model results
- **Commercial Use**: Production-ready video enhancement

### Enhancement Scenarios
- **Social Media**: Create HD content from base generation
- **Web Content**: Upgrade standard quality to premium
- **Professional Work**: Add professional polish to videos
- **Client Projects**: Deliver higher quality results

### Performance Considerations
- **Time Investment**: 50-150% additional processing time
- **Memory Investment**: Additional 8GB VRAM requirement
- **Quality Return**: 2-4x quality improvement
- **Cost-Benefit**: Excellent for professional applications

## Support

**Documentation**: [LTX-Video Enhancement Guide](https://huggingface.co/Lightricks/LTX-Video)
**Community**: [ComfyUI Community Discord](https://discord.gg/comfyui)
**Issues**: [ZeroClue GitHub Issues](https://github.com/ZeroClue/ComfyUI-Docker/issues)

---

*Last Updated: 2025-01-13 | ZeroClue ComfyUI-Docker*