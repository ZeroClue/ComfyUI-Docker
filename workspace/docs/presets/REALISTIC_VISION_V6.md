# REALISTIC_VISION_V6 - Photorealistic Portrait Generation

Specialized model for creating photorealistic images, particularly portraits and realistic scenes.

## Quick Start

```bash
docker run -e IMAGE_PRESET_DOWNLOAD=REALISTIC_VISION_V6 --gpus all -p 3000:3000 zeroclue/comfyui:base-torch2.8.0-cu126
```

## Model Details

- **Size**: 4GB
- **Base**: Stable Diffusion 1.5
- **Type**: Text-to-Image (Photorealism focused)
- **Resolution**: Up to 512x512 (native)
- **Quality**: Photorealistic excellence
- **Specialty**: Portraits and realistic scenes

## RunPod Requirements

### Recommended GPU
- **RTX 4000 Ada (16GB)** - Perfect fit
- **RTX 3060 (12GB)** - Works well
- **RTX 3090 (24GB)** - Overkill but fine

### Storage
- **Minimum**: 12GB
- **Recommended**: 15GB

### Cost Estimate
- **RTX 4000 Ada**: ~$0.50/hour
- **RTX 3060**: ~$0.35/hour
- **Spot instance**: ~$0.20/hour

## Performance

### Speed
- **Generation**: 2-4 seconds per image
- **Inference**: Very fast
- **Memory Usage**: ~6GB VRAM

### Quality
- **Visual Quality**: Exceptional photorealism
- **Portrait Quality**: Industry-leading
- **Detail Level**: Very high
- **Skin Texture**: Outstanding

## Use Cases

### Best For
- Photorealistic portraits
- Professional headshots
- Character design
- Fashion photography
- Realistic human subjects

### Good For
- Product photography
- Interior design visualization
- Architectural renders
- Stock photo creation
- Marketing materials

### Not Ideal For
- Artistic/stylized images
- Fantasy/sci-fi content
- High resolution (512x512 native)
- Text-heavy images

## Example Prompts

```text
Professional headshot of a businesswoman, studio lighting
Photorealistic portrait of an elderly man, detailed wrinkles
Fashion model on runway, high-end photography
Child's portrait with natural lighting, candid expression
Professional athlete portrait, dramatic lighting
```

## Advanced Usage

### Complete Realistic Setup
```bash
docker run -e IMAGE_PRESET_DOWNLOAD=REALISTIC_COMPLETE_WORKFLOW \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Development Setup
```bash
docker run -e IMAGE_PRESET_DOWNLOAD=REALISTIC_VISION_V6 \
  -e ACCESS_PASSWORD=mypassword \
  --gpus all -p 3000:3000 -p 8080:8080 -p 8888:8888 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### With Upscaling
```bash
docker run -e IMAGE_PRESET_DOWNLOAD="REALISTIC_VISION_V6,ESRGAN_MODELS" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Comparison with Other Models

### vs SDXL_BASE_V1
- **This Model**: Superior photorealism, faster, smaller
- **SDXL**: Higher resolution, more versatile

### vs FLUX_DEV_BASIC
- **This Model**: Better for portraits, much cheaper
- **FLUX**: More versatile, higher resolution

### vs JUGGERNAUT_XL_V8
- **This Model**: Photorealism focus, SD 1.5 based
- **Juggernaut**: Artistic focus, SDXL based

## Tips for Best Results

### Prompt Engineering
- Use photography terms (shutter speed, aperture)
- Specify lighting conditions (studio, natural)
- Include camera types and lenses
- Describe subject details (age, features, expression)
- Use professional photography terminology

### Technical Settings
- 20-30 steps optimal
- CFG scale 7-12 recommended
- 512x512 native resolution
- Use upscaling for larger images

### Portrait Photography Tips
- Specify portrait style (headshot, environmental)
- Include lighting setup (Rembrandt, butterfly)
- Mention camera angle and distance
- Describe clothing and background
- Use professional photo terms

## Advanced Features

### Professional Workflow
```bash
# Complete professional photography setup
docker run -e IMAGE_PRESET_DOWNLOAD="REALISTIC_COMPLETE_WORKFLOW,ESRGAN_MODELS" \
  -e ACCESS_PASSWORD=mypassword \
  --gpus all -p 3000:3000 -p 8080:8080 -p 8888:8888 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Multiple Styles
```bash
# Different realistic styles
docker run -e IMAGE_PRESET_DOWNLOAD="REALISTIC_VISION_V6,DELIBERATE_V6,PROTOGEN_XL" \
  -e ACCESS_PASSWORD=mypassword \
  --gpus all -p 3000:3000 -p 8080:8080 -p 8888:8888 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Troubleshooting

### Common Issues
1. **Uncanny faces**: Adjust prompt specificity
2. **Poor lighting**: Specify lighting conditions
3. **Artifacts**: Increase step count or use refiner
4. **Inconsistent quality**: Check VAE loading

### Performance Tips
- Very efficient on RTX 4000 Ada
- Use native 512x512 for best results
- Batch similar portrait prompts
- Monitor memory usage

## Integration Examples

### With Audio Generation
```bash
docker run -e IMAGE_PRESET_DOWNLOAD=REALISTIC_VISION_V6 \
  -e AUDIO_PRESET_DOWNLOAD=BARK_BASIC \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### With Video Generation
```bash
docker run -e IMAGE_PRESET_DOWNLOAD=REALISTIC_VISION_V6 \
  -e PRESET_DOWNLOAD=WAN_22_5B_I2V_GGUF_Q4_K_M \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Production Considerations

### Cost Management
- Very cost-effective for portrait work
- Excellent performance on mid-range GPUs
- Fast generation reduces costs
- Small model size reduces storage costs

### Quality Assurance
- Highly consistent portrait quality
- Well-understood behavior
- Extensive community examples
- Reliable for slim use

## Variations

### Complete Workflow
- **REALISTIC_COMPLETE_WORKFLOW** - With VAE and upscaler (7GB)

### Other Realistic Models
- **DELIBERATE_V6** - Detailed artistic realism (4GB)
- **PROTOGEN_XL** - Versatile realism (5GB)
- **DREAMSHAPER_V8** - Dreamy realistic style (3GB)

## Photography Style Examples

### Studio Portraits
```text
Professional studio portrait, softbox lighting, 85mm lens, f/1.8, sharp focus on eyes, neutral background
```

### Environmental Portraits
```text
Candid environmental portrait, natural window light, 50mm lens, shallow depth of field, authentic expression
```

### Fashion Photography
```text
High fashion portrait, dramatic studio lighting, beauty dish, makeup detailed, couture clothing, professional model
```

## Next Steps

1. **Deploy RunPod** with RTX 4000 Ada (recommended)
2. **Set environment variable** `IMAGE_PRESET_DOWNLOAD=REALISTIC_VISION_V6`
3. **Access ComfyUI** at port 3000
4. **Start with portrait prompts**
5. **Add upscaling** for larger outputs

## Alternatives

- **SDXL_BASE_V1** - Higher resolution (5GB)
- **FLUX_DEV_FP8** - More versatile (6GB)
- **DELIBERATE_V6** - Artistic realism (4GB)
- **REALISTIC_COMPLETE_WORKFLOW** - Complete setup (7GB)