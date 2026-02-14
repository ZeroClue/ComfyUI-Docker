# FLUX_SCHNELL_BASIC - Fast Image Generation

Black Forest Labs FLUX.1-schnell model for rapid image generation with 4-step inference.

## Quick Start

```bash
docker run -e IMAGE_PRESET_DOWNLOAD=FLUX_SCHNELL_BASIC --gpus all -p 3000:3000 zeroclue/comfyui:base-torch2.8.0-cu126
```

## Model Details

- **Size**: 12GB
- **Parameters**: 12 billion
- **Type**: Text-to-Image
- **Steps**: 4 (optimal)
- **Quality**: High with fast generation
- **Resolution**: Up to 1024x1024

## RunPod Requirements

### Recommended GPU
- **RTX 4000 Ada (16GB)** - Minimum requirement
- **RTX 6000 Ada (48GB)** - Recommended
- **A100 (40GB)** - Best performance

### Storage
- **Minimum**: 20GB
- **Recommended**: 25GB

### Cost Estimate
- **RTX 4000 Ada**: ~$0.60/hour
- **RTX 6000 Ada**: ~$1.00/hour
- **A100**: ~$2.00/hour

## Performance

### Speed
- **Generation**: 4-8 seconds per image
- **Inference**: Very fast
- **Memory Usage**: ~12GB VRAM

### Quality
- **Visual Quality**: Excellent
- **Prompt Adherence**: Very good
- **Detail Level**: High
- **Style Versatility**: Outstanding

## Use Cases

### Best For
- Rapid prototyping
- Batch image generation
- Real-time applications
- Cost-effective slim
- Quick iterations

### Good For
- Social media content
- Blog illustrations
- Concept development
- Testing workflows

### Not Ideal For
- Maximum quality requirements
- Fine artistic control
- Complex detailed scenes

## Example Prompts

```text
A photorealistic portrait of a woman in a vintage cafe
An epic fantasy landscape with dragons and castles
A futuristic city with flying cars at sunset
Abstract geometric patterns in vibrant colors
A cute robot reading a book in a cozy library
```

## Advanced Usage

### Complete FLUX Setup
```bash
docker run -e IMAGE_PRESET_DOWNLOAD=FLUX_COMPLETE \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Production Setup
```bash
docker run -e IMAGE_PRESET_DOWNLOAD=FLUX_SCHNELL_BASIC \
  -e ACCESS_PASSWORD=mypassword \
  --gpus all -p 3000:3000 -p 8080:8080 -p 8888:8888 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### With Upscaling
```bash
docker run -e IMAGE_PRESET_DOWNLOAD="FLUX_SCHNELL_BASIC,ESRGAN_MODELS" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Comparison with Other Models

### vs FLUX_DEV_BASIC
- **This Model**: Much faster (4 steps), simpler quality
- **FLUX Dev**: Higher quality, more steps (20-50)

### vs SDXL_BASE_V1
- **This Model**: Faster, better prompt adherence
- **SDXL**: More established, cheaper

### vs QWEN_IMAGE_BASIC
- **This Model**: Faster generation
- **Qwen**: Better text rendering

## Tips for Best Results

### Prompt Engineering
- Be descriptive and specific
- Include artistic style keywords
- Specify lighting and composition
- Use professional photography terms
- Describe mood and atmosphere

### Technical Settings
- 4 steps is optimal
- CFG scale 7-12 recommended
- 1024x1024 resolution
- Batch size 2-4 for efficiency

### Workflow Optimization
- Test with different CFG scales
- Use appropriate sampler
- Monitor VRAM usage
- Batch similar prompts together

## Advanced Features

### Professional Workflow
```bash
# Complete professional setup
docker run -e IMAGE_PRESET_DOWNLOAD="FLUX_COMPLETE,ESRGAN_MODELS" \
  -e ACCESS_PASSWORD=mypassword \
  --gpus all -p 3000:3000 -p 8080:8080 -p 8888:8888 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Development Environment
```bash
# Development with multiple models
docker run -e IMAGE_PRESET_DOWNLOAD="FLUX_SCHNELL_BASIC,SDXL_BASE_V1,REALISTIC_VISION_V6" \
  -e ACCESS_PASSWORD=mypassword \
  --gpus all -p 3000:3000 -p 8080:8080 -p 8888:8888 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Troubleshooting

### Common Issues
1. **Memory errors**: Use smaller batch sizes
2. **Slow generation**: Check GPU utilization
3. **Quality issues**: Adjust CFG scale
4. **Prompt issues**: Be more specific and descriptive

### Performance Tips
- Use RTX 4000 Ada as minimum
- Batch similar prompts together
- Monitor GPU memory usage
- Use 4 steps for optimal speed

## Integration Examples

### With Video Generation
```bash
docker run -e IMAGE_PRESET_DOWNLOAD=FLUX_SCHNELL_BASIC \
  -e PRESET_DOWNLOAD=WAN_22_5B_TIV2 \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### With Audio Generation
```bash
docker run -e IMAGE_PRESET_DOWNLOAD=FLUX_SCHNELL_BASIC \
  -e AUDIO_PRESET_DOWNLOAD=MUSICGEN_MEDIUM \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Production Considerations

### Cost Management
- Use spot instances for testing
- Batch generations when possible
- Monitor usage closely
- Scale up for slim only

### Quality Assurance
- Test prompts thoroughly
- Use development environment first
- Review outputs before scaling
- Maintain consistent settings

## Variations

### Complete Package
- **FLUX_COMPLETE** - Both Schnell and Dev models (12GB)

### FP8 Versions (More Efficient)
- **FLUX_SCHNELL_FP8** - Memory-efficient Schnell (6GB)
- **FLUX_DEV_FP8** - Memory-efficient Dev (6GB)
- **FLUX_PRODUCTION** - Production-optimized setup (6GB)

### High Quality Version
- **FLUX_DEV_BASIC** - Higher quality, more steps (12GB)

## Next Steps

1. **Deploy RunPod** with RTX 4000 Ada (minimum)
2. **Set environment variable** `IMAGE_PRESET_DOWNLOAD=FLUX_SCHNELL_BASIC`
3. **Access ComfyUI** at port 3000
4. **Start with 4-step generations**
5. **Adjust CFG scale** for desired quality

## Alternatives

- **FLUX_DEV_FP8** - More efficient, higher quality (6GB)
- **SDXL_BASE_V1** - More affordable (5GB)
- **QWEN_IMAGE_BASIC** - Better for text (12GB)
- **REALISTIC_VISION_V6** - Photorealistic focus (4GB)