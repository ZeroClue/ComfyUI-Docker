# HUNYUAN_T2V_720P - High-Quality Video Generation

Tencent HunyuanVideo Text-to-Video model for professional 720p video generation.

## Quick Start

```bash
docker run -e PRESET_DOWNLOAD=HUNYUAN_T2V_720P --gpus all -p 3000:3000 zeroclue/comfyui:base-torch2.8.0-cu126
```

## Model Details

- **Size**: 12GB
- **Resolution**: 1280x720p
- **Type**: Text-to-Video (T2V)
- **Quality**: Professional grade
- **Company**: Tencent

## RunPod Requirements

### Recommended GPU
- **RTX 4000 Ada (16GB)** - Minimum requirement
- **RTX 6000 Ada (48GB)** - Recommended for production
- **A100 (40GB)** - Best performance

### Storage
- **Minimum**: 25GB
- **Recommended**: 30GB

### Cost Estimate
- **RTX 4000 Ada**: ~$0.70/hour
- **RTX 6000 Ada**: ~$1.20/hour
- **A100**: ~$2.50/hour

## Performance

### Speed
- **Generation**: 30-60 seconds per clip
- **Inference**: Slower but high quality
- **Memory Usage**: ~14GB VRAM

### Quality
- **Visual Quality**: Excellent
- **Prompt Adherence**: Very good
- **Motion Quality**: Very good
- **Resolution**: True 720p HD

## Use Cases

### Best For
- Professional video production
- High-quality marketing content
- Commercial applications
- Cinematic video creation

### Good For
- Premium social media content
- High-end educational materials
- Artistic projects
- Portfolio work

### Not Ideal For
- Real-time applications
- Budget-constrained projects
- Rapid prototyping
- Simple testing

## Example Prompts

```text
A cinematic shot of a sunset over ocean waves
Professional interview setup in modern office
Time-lapse of city traffic at night
Nature documentary style: wildlife in forest
Corporate training video scenario
```

## Advanced Usage

### Complete HunyuanVideo Setup
```bash
docker run -e PRESET_DOWNLOAD=HUNYUAN_COMPLETE_WORKFLOW \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### With Image-to-Video
```bash
docker run -e PRESET_DOWNLOAD="HUNYUAN_T2V_720P,HUNYUAN_I2V_720P_V2" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Development Setup
```bash
docker run -e PRESET_DOWNLOAD=HUNYUAN_T2V_720P \
  -e ACCESS_PASSWORD=mypassword \
  --gpus all -p 3000:3000 -p 8080:8080 -p 8888:8888 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Comparison with Other Models

### vs WAN_22_5B_TIV2
- **This Model**: Higher resolution, better quality, more expensive
- **WAN 5B**: Faster, smaller, more efficient

### vs LTXV_13B_FP8_SCALED
- **This Model**: Better prompt adherence, smaller size
- **LTXV 13B**: Faster generation, larger model

### vs MOCHI_1_PREVIEW_FP8
- **This Model**: More affordable, good quality
- **Mochi 1**: Best quality, much more expensive

## Tips for Best Results

### Prompt Engineering
- Use professional, descriptive language
- Include camera angles and movements
- Specify lighting conditions
- Describe scene composition in detail

### Technical Settings
- 720p is optimal resolution
- 20-50 inference steps
- CFG scale 7-12 recommended
- 8-16 second clips work best

### Production Workflow
- Test with shorter clips first
- Use development setup for testing
- Scale to production GPU when ready
- Monitor rendering times

## Advanced Features

### Professional Workflow
```bash
# Complete professional setup
docker run -e PRESET_DOWNLOAD="HUNYUAN_COMPLETE_WORKFLOW" \
  -e ACCESS_PASSWORD=mypassword \
  --gpus all -p 3000:3000 -p 8080:8080 -p 8888:8888 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Combined T2V and I2V
```bash
# Both text-to-video and image-to-video
docker run -e PRESET_DOWNLOAD="HUNYUAN_T2V_720P,HUNYUAN_I2V_720P_V2" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Troubleshooting

### Common Issues
1. **Memory errors**: Use RTX 6000 Ada or A100
2. **Slow generation**: Normal for this quality level
3. **Quality issues**: Improve prompt detail
4. **Connection issues**: Check model download completion

### Performance Tips
- Use RTX 6000 Ada for best experience
- Pre-download models when possible
- Batch similar prompts together
- Monitor GPU temperature and usage

## Integration Examples

### With Audio Production
```bash
docker run -e PRESET_DOWNLOAD=HUNYUAN_T2V_720P \
  -e AUDIO_PRESET_DOWNLOAD=AUDIO_PRODUCTION \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### With Image Generation
```bash
docker run -e PRESET_DOWNLOAD=HUNYUAN_T2V_720P \
  -e IMAGE_PRESET_DOWNLOAD=REALISTIC_VISION_V6 \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Production Considerations

### Cost Management
- Use spot instances for testing
- Reserve production instances in advance
- Batch rendering when possible
- Monitor usage closely

### Quality Assurance
- Test prompts thoroughly
- Review output before scaling
- Use development environment for testing
- Maintain consistent quality settings

## Variations

### Complete Workflow
- **HUNYUAN_COMPLETE_WORKFLOW** - All HunyuanVideo models (18GB)

### I2V Models
- **HUNYUAN_I2V_720P_V1** - Image-to-video v1 (concat method)
- **HUNYUAN_I2V_720P_V2** - Image-to-video v2 (replace method)

## Next Steps

1. **Deploy RunPod** with RTX 6000 Ada (recommended)
2. **Set environment variable** `PRESET_DOWNLOAD=HUNYUAN_T2V_720P`
3. **Access ComfyUI** at port 3000
4. **Test with professional prompts**
5. **Scale to production** when satisfied

## Alternatives

- **WAN_22_5B_TIV2** - More affordable (4.8GB)
- **LTXV_13B_FP8_SCALED** - Faster generation (24GB)
- **MOCHI_1_PREVIEW_FP8** - Best quality (24GB)
- **HUNYUAN_COMPLETE_WORKFLOW** - Complete setup (18GB)