# SDXL_BASE_V1 - Reliable High-Quality Image Generation

Stability AI Stable Diffusion XL Base 1.0 - the industry standard for high-quality image generation.

## Quick Start

```bash
docker run -e IMAGE_PRESET_DOWNLOAD=SDXL_BASE_V1 --gpus all -p 3000:3000 zeroclue/comfyui:base-torch2.8.0-cu126
```

## Model Details

- **Size**: 5GB
- **Parameters**: 2.6 billion (base) + text encoders
- **Type**: Text-to-Image
- **Resolution**: Up to 1024x1024
- **Quality**: Excellent and reliable
- **Maturity**: Industry standard

## RunPod Requirements

### Recommended GPU
- **RTX 4000 Ada (16GB)** - Perfect fit
- **RTX 6000 Ada (48GB)** - For larger workflows
- **RTX 3090 (24GB)** - Works well

### Storage
- **Minimum**: 15GB
- **Recommended**: 20GB

### Cost Estimate
- **RTX 4000 Ada**: ~$0.50/hour
- **RTX 6000 Ada**: ~$1.20/hour
- **Spot instance**: ~$0.25/hour

## Performance

### Speed
- **Generation**: 4-8 seconds per image
- **Inference**: Fast and reliable
- **Memory Usage**: ~8GB VRAM

### Quality
- **Visual Quality**: Excellent
- **Prompt Adherence**: Very good
- **Consistency**: Highly reliable
- **Community Support**: Extensive

## Use Cases

### Best For
- Professional artwork
- Commercial applications
- Reliable slim workflows
- Educational purposes
- Beginners and experts

### Good For
- Social media content
- Blog illustrations
- Marketing materials
- Personal projects
- Testing and development

### Not Ideal For
- Ultra-high resolution needs
- Specialized text rendering
- Real-time generation

## Example Prompts

```text
A beautiful landscape painting of mountains at sunset
Professional headshot of a business person
Cute cartoon animal character design
Futuristic sci-fi city with flying vehicles
Vintage photograph of a street in Paris
```

## Advanced Usage

### Complete SDXL Setup
```bash
docker run -e IMAGE_PRESET_DOWNLOAD=SDXL_COMPLETE_WORKFLOW \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Development Setup
```bash
docker run -e IMAGE_PRESET_DOWNLOAD=SDXL_BASE_V1 \
  -e ACCESS_PASSWORD=mypassword \
  --gpus all -p 3000:3000 -p 8080:8080 -p 8888:8888 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### With Refiner
```bash
docker run -e IMAGE_PRESET_DOWNLOAD="SDXL_BASE_V1,SDXL_REFINER" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Comparison with Other Models

### vs FLUX_DEV_BASIC
- **This Model**: More established, faster, cheaper
- **FLUX Dev**: Higher quality, better prompt adherence

### vs SD 1.5 Models
- **This Model**: Higher resolution, better quality
- **SD 1.5**: Faster, less memory, lower resolution

### vs REALISTIC_VISION_V6
- **This Model**: More versatile, general purpose
- **Realistic Vision**: Specialized for photorealism

## Tips for Best Results

### Prompt Engineering
- Clear, descriptive prompts work best
- Include style and quality keywords
- Specify composition and lighting
- Use natural language
- Be specific but not overly complex

### Technical Settings
- 20-30 steps optimal
- CFG scale 7-10 recommended
- 1024x1024 native resolution
- DPM++ family samplers work well

### Workflow Optimization
- Start with basic prompts
- Gradually increase complexity
- Use refiner for final polish
- Batch similar prompts together

## Advanced Features

### Professional Workflow
```bash
# Complete professional setup
docker run -e IMAGE_PRESET_DOWNLOAD="SDXL_COMPLETE_WORKFLOW,ESRGAN_MODELS" \
  -e ACCESS_PASSWORD=mypassword \
  --gpus all -p 3000:3000 -p 8080:8080 -p 8888:8888 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Development Environment
```bash
# Development with multiple models
docker run -e IMAGE_PRESET_DOWNLOAD="SDXL_BASE_V1,REALISTIC_VISION_V6,JUGGERNAUT_XL_V8" \
  -e ACCESS_PASSWORD=mypassword \
  --gpus all -p 3000:3000 -p 8080:8080 -p 8888:8888 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Troubleshooting

### Common Issues
1. **Slow generation**: Reduce batch size or resolution
2. **Quality issues**: Increase step count to 30-50
3. **Memory issues**: Use smaller resolution
4. **Prompt issues**: Simplify and be more specific

### Performance Tips
- Use RTX 4000 Ada for cost efficiency
- Start with 20 steps for testing
- Use appropriate sampler settings
- Monitor GPU memory usage

## Integration Examples

### With Video Generation
```bash
docker run -e IMAGE_PRESET_DOWNLOAD=SDXL_BASE_V1 \
  -e PRESET_DOWNLOAD=WAN_22_5B_TIV2 \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### With Audio Generation
```bash
docker run -e IMAGE_PRESET_DOWNLOAD=SDXL_BASE_V1 \
  -e AUDIO_PRESET_DOWNLOAD=MUSICGEN_SMALL \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Production Considerations

### Cost Management
- Very cost-effective for slim
- Use spot instances for testing
- Batch generations when possible
- Monitor usage but costs are reasonable

### Quality Assurance
- Highly reliable and consistent
- Extensive community documentation
- Well-understood behavior
- Proven in slim environments

## Variations

### Complete Workflow
- **SDXL_COMPLETE_WORKFLOW** - Base + refiner + VAE (8GB)

### Refiner
- **SDXL_REFINER** - For detail enhancement (3GB)

### Other SDXL Models
- **JUGGERNAUT_XL_V8** - Artistic focus (6GB)
- **REALVIS_XL_V4** - Photorealistic focus (6GB)
- **DREAMSHAPER_XL_V7** - Dreamy artistic style (5GB)

## Community and Resources

### Strengths
- Largest community support
- Extensive tutorials and guides
- Compatible with most tools
- Reliable performance history

### Documentation
- Comprehensive official documentation
- Active community forums
- Many integration examples
- Regular updates and improvements

## Next Steps

1. **Deploy RunPod** with RTX 4000 Ada (recommended)
2. **Set environment variable** `IMAGE_PRESET_DOWNLOAD=SDXL_BASE_V1`
3. **Access ComfyUI** at port 3000
4. **Start with simple prompts** to test
5. **Explore advanced features** as needed

## Alternatives

- **FLUX_SCHNELL_FP8** - Faster generation (6GB)
- **REALISTIC_VISION_V6** - Photorealistic focus (4GB)
- **JUGGERNAUT_XL_V8** - Artistic focus (6GB)
- **SDXL_COMPLETE_WORKFLOW** - Complete setup (8GB)