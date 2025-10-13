# FLUX_DEV_BASIC - State-of-the-Art Image Generation

Black Forest Labs FLUX.1-dev model for exceptional image generation quality.

## Quick Start

```bash
docker run -e IMAGE_PRESET_DOWNLOAD=FLUX_DEV_BASIC --gpus all -p 3000:3000 zeroclue/comfyui:base-torch2.8.0-cu126
```

## Model Details

- **Size**: 12GB
- **Parameters**: 12 billion
- **Type**: Text-to-Image
- **Quality**: State-of-the-art
- **Steps**: 20-50 (optimal)
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
- **RTX 4000 Ada**: ~$0.70/hour
- **RTX 6000 Ada**: ~$1.20/hour
- **A100**: ~$2.50/hour

## Performance

### Speed
- **Generation**: 8-15 seconds per image
- **Inference**: Medium speed
- **Memory Usage**: ~14GB VRAM

### Quality
- **Visual Quality**: Exceptional
- **Prompt Adherence**: Excellent
- **Detail Level**: Very high
- **Style Versatility**: Outstanding

## Use Cases

### Best For
- Professional artwork
- High-end marketing materials
- Concept art
- Premium content creation
- Artistic projects

### Good For
- Social media content
- Blog illustrations
- Presentations
- Personal art projects

### Not Ideal For
- Rapid generation needs
- Budget-constrained projects
- Simple graphics

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
docker run -e IMAGE_PRESET_DOWNLOAD=FLUX_DEV_BASIC \
  -e ACCESS_PASSWORD=mypassword \
  --gpus all -p 3000:3000 -p 8080:8080 -p 8888:8888 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### With Upscaling
```bash
docker run -e IMAGE_PRESET_DOWNLOAD="FLUX_DEV_BASIC,ESRGAN_MODELS" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Comparison with Other Models

### vs SDXL_BASE_V1
- **This Model**: Superior quality, better prompt adherence
- **SDXL**: Faster, more established, cheaper

### vs FLUX_SCHNELL_BASIC
- **This Model**: Higher quality, more steps
- **Schnell**: Faster (4 steps), simpler quality

### vs QWEN_IMAGE_BASIC
- **This Model**: Better artistic quality
- **Qwen**: Superior text rendering

## Tips for Best Results

### Prompt Engineering
- Be descriptive and specific
- Include artistic style keywords
- Specify lighting and composition
- Use professional photography terms
- Describe mood and atmosphere

### Technical Settings
- 20-30 steps optimal
- CFG scale 7-12 recommended
- 1024x1024 resolution
- Batch size 1-2 for quality

### Workflow Optimization
- Test with 20 steps first
- Increase steps for final images
- Use appropriate sampler
- Monitor VRAM usage

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
docker run -e IMAGE_PRESET_DOWNLOAD="FLUX_DEV_BASIC,SDXL_BASE_V1,REALISTIC_VISION_V6" \
  -e ACCESS_PASSWORD=mypassword \
  --gpus all -p 3000:3000 -p 8080:8080 -p 8888:8888 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Troubleshooting

### Common Issues
1. **Memory errors**: Use RTX 6000 Ada or A100
2. **Slow generation**: Normal for this quality level
3. **Quality issues**: Increase step count to 30-50
4. **Prompt issues**: Be more specific and descriptive

### Performance Tips
- Use RTX 6000 Ada for best experience
- Start with 20 steps, increase as needed
- Batch similar prompts together
- Monitor GPU memory usage

## Integration Examples

### With Video Generation
```bash
docker run -e IMAGE_PRESET_DOWNLOAD=FLUX_DEV_BASIC \
  -e PRESET_DOWNLOAD=WAN_22_5B_TIV2 \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### With Audio Generation
```bash
docker run -e IMAGE_PRESET_DOWNLOAD=FLUX_DEV_BASIC \
  -e AUDIO_PRESET_DOWNLOAD=MUSICGEN_MEDIUM \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Production Considerations

### Cost Management
- Use spot instances for testing
- Batch generations when possible
- Monitor usage closely
- Consider FLUX_SCHNELL for rapid iterations

### Quality Assurance
- Test prompts thoroughly
- Use development environment first
- Review outputs before scaling
- Maintain consistent settings

## Variations

### Complete Package
- **FLUX_COMPLETE** - Both Schnell and Dev models (12GB)

### FP8 Versions (More Efficient)
- **FLUX_DEV_FP8** - Memory-efficient Dev version (6GB)
- **FLUX_SCHNELL_FP8** - Memory-efficient Schnell (6GB)
- **FLUX_PRODUCTION** - Production-optimized setup (6GB)

### Fast Version
- **FLUX_SCHNELL_BASIC** - 4-step generation (12GB)

## Next Steps

1. **Deploy RunPod** with RTX 4000 Ada (minimum)
2. **Set environment variable** `IMAGE_PRESET_DOWNLOAD=FLUX_DEV_BASIC`
3. **Access ComfyUI** at port 3000
4. **Start with 20-step generations**
5. **Increase steps** for final images

## Alternatives

- **FLUX_SCHNELL_FP8** - Faster, more efficient (6GB)
- **SDXL_BASE_V1** - More affordable (5GB)
- **QWEN_IMAGE_BASIC** - Better for text (12GB)
- **REALISTIC_VISION_V6** - Photorealistic focus (4GB)