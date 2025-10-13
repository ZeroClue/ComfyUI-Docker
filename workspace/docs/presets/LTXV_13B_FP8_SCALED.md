# RUNPOD README: LTXV_13B_FP8_SCALED

## Quick Start
**Model**: LTX-Video 13B DiT (FP8 scaled, highest quality)
**Size**: 24GB | **VRAM**: 32GB+ | **Type**: Premium Real-time Video Generation

```bash
# RunPod Template Configuration
Container Image: zeroclue/comfyui:base-torch2.8.0-cu126
Environment Variables:
  - PRESET_DOWNLOAD=LTXV_13B_FP8_SCALED
GPU Selection: A100 (40GB) or H100 (80GB) REQUIRED
Disk Space: 60GB minimum
```

## RunPod Configuration

### Container Settings
- **Image**: `zeroclue/comfyui:base-torch2.8.0-cu126`
- **GPU**: A100 (40GB) minimum, H100 (80GB) recommended
- **CPU**: 8+ cores
- **Memory**: 64GB+ system RAM
- **Storage**: 60GB+ high-speed SSD

### Port Mapping
- **3000** → ComfyUI Web Interface
- **8080** → VS Code (optional)
- **8888** → JupyterLab (optional)

### Environment Variables
```bash
PRESET_DOWNLOAD=LTXV_13B_FP8_SCALED
ACCESS_PASSWORD=your_password  # Optional
COMFYUI_EXTRA_ARGS=--fast      # Recommended for premium performance
```

### Volume Mount (Recommended)
```bash
/workspace → Persistent storage for premium video outputs
```

## Model Details

### Included Models
- **LTX-Video 13B DiT**: Highest quality generation model
- **Format**: FP8 scaled for memory efficiency
- **Resolution**: Native 768x512, supports upscaling
- **Quality**: State-of-the-art video generation
- **Parameters**: 13 billion parameters

### File Organization
```
/workspace/ComfyUI/models/diffusion_models/
└── ltx-video-13b-v0.9.8-dev-fp8.safetensors (24GB)
```

### Performance Characteristics
- **Generation Speed**: ~4-6 seconds per frame (A100)
- **Quality Level**: Cinematic, film-grade output
- **Memory Usage**: ~28GB VRAM during generation
- **Output Quality**: Superior motion consistency and detail

## Usage Examples

### Premium Content Creation
```python
# High-End Production Workflow
prompt: "Ultra-realistic cinematic footage of [detailed scene], 8K quality, professional lighting"
resolution: [768, 512]  # Base generation
frames: 300  # 10 seconds at 30fps
quality: "cinematic_premium"
```

### Commercial Production
```bash
# For professional video production
# Ideal for:
- Film pre-visualization
- High-end commercial content
- Premium social media content
- Professional creative projects
```

### Quality Comparison
```bash
# 13B vs 2B Model Comparison:
# Detail: 3x higher fidelity
# Motion: 2x smoother transitions
# Consistency: Superior temporal coherence
# Prompt Following: Enhanced understanding
```

## Technical Specifications

### Performance Tiers
| GPU | Generation Speed | VRAM Usage | Cost Efficiency |
|-----|------------------|------------|-----------------|
| A100 (40GB) | ~5s/frame | 28GB | Optimal |
| H100 (80GB) | ~3s/frame | 28GB | Premium |
| A6000 (48GB) | ~8s/frame | 32GB | Alternative |

### Quality Metrics
- **Resolution**: 768x512 native (upscale to 4K+)
- **Framerate**: 30 FPS native (supports interpolation)
- **Detail Level**: Photorealistic quality
- **Motion Quality**: Natural, smooth motion
- **Prompt Adherence**: Advanced text understanding

### Memory Requirements
- **Model Loading**: 24GB VRAM
- **Generation Buffer**: 4GB VRAM
- **System Overhead**: 2GB VRAM
- **Total Recommended**: 32GB+ VRAM

## Production Deployment

### Enterprise Configuration
```bash
# Production-ready setup
Container Image: zeroclue/comfyui:base-torch2.8.0-cu126
GPU: H100 (80GB) for best performance
CPU: 16+ cores
Memory: 128GB+ RAM
Storage: NVMe SSD, 100GB+
```

### Cost Optimization
```bash
# For cost-effective premium quality:
# Use A100 instead of H100 (slower but cheaper)
# Batch process multiple prompts
# Use production image variant for efficiency
```

### Quality Workflow
```python
# Professional production pipeline
# 1. Generate with 13B model
# 2. Apply temporal upscaling (if available)
# 3. Post-process color grading
# 4. Export in desired format
```

## Troubleshooting

### Critical Requirements
**Insufficient VRAM**:
- A100 (40GB) minimum requirement
- No alternatives - model is 24GB
- Consider LTXV_2B variants if budget limited

**Performance Issues**:
- Verify GPU utilization with `nvidia-smi`
- Ensure sufficient system RAM
- Check for memory leaks in long-running sessions

### Memory Management
```bash
# Monitor memory usage
nvidia-smi -l 1

# Clear VRAM between jobs
# Restart container if needed
docker restart <container_id>
```

### Quality Validation
```bash
# Verify output quality
# Check for artifacts or inconsistencies
# Validate motion smoothness
# Ensure prompt adherence
```

### Model Loading
```bash
# Verify model integrity
ls -lh /workspace/ComfyUI/models/diffusion_models/ltx-video-13b*

# Check for successful loading
grep "ltx-video-13b" /workspace/ComfyUI/user/comfyui_3000.log
```

## Use Case Recommendations

### Ideal For
- **Film Industry**: Pre-visualization, concept art
- **Advertising**: Premium commercial content
- **Creative Agencies**: High-end client work
- **Content Studios**: Professional video production
- **Research**: Advanced video generation studies

### Output Examples
- **Cinematic Previews**: Film-quality concept videos
- **Premium Ads**: High-end commercial content
- **Art Projects**: Professional creative works
- **Prototype Content**: High-quality mockups

### Investment Justification
- **Quality Premium**: 3x better than 2B models
- **Professional Use**: Commercial-grade output
- **Client Satisfaction**: Superior results for clients
- **Competitive Edge**: Best available quality

## Alternatives and Considerations

### When to Use 13B Model
- **Quality Critical**: When output quality is paramount
- **Professional Work**: Commercial applications
- **Client Projects**: When reputation matters
- **Research**: When exploring model capabilities

### When to Consider Alternatives
```bash
# Budget constraints (660MB)
PRESET_DOWNLOAD=LTXV_2B_GGUF_Q4_NL

# Balanced quality (4.8GB)
PRESET_DOWNLOAD=LTXV_2B_FP8_SCALED

# Complete workflow (8GB)
PRESET_DOWNLOAD=LTXV_COMPLETE_WORKFLOW
```

### Hybrid Approach
```bash
# Use 2B for prototyping
# Switch to 13B for final renders
# Cost-effective workflow
```

## Support

**Documentation**: [LTX-Video 13B Guide](https://huggingface.co/Lightricks/LTX-Video)
**Community**: [ComfyUI Community Discord](https://discord.gg/comfyui)
**Enterprise Support**: [ZeroClue GitHub Issues](https://github.com/ZeroClue/ComfyUI-Docker/issues)

---

*Last Updated: 2025-01-13 | ZeroClue ComfyUI-Docker*