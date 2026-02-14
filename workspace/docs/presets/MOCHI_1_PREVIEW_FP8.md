# MOCHI_1_PREVIEW_FP8 - Ultimate Quality Video Generation

Genmo Mochi 1 Preview model with exceptional prompt adherence and quality.

## Quick Start

```bash
docker run -e PRESET_DOWNLOAD=MOCHI_1_PREVIEW_FP8 --gpus all -p 3000:3000 zeroclue/comfyui:base-torch2.8.0-cu126
```

## Model Details

- **Size**: 24GB
- **Parameters**: Large (exact size undisclosed)
- **Type**: Text-to-Video
- **Quality**: State-of-the-art
- **Format**: FP8 optimized
- **Specialty**: Best prompt adherence

## RunPod Requirements

### Recommended GPU
- **RTX 6000 Ada (48GB)** - Minimum recommended
- **A100 (40GB)** - Works well
- **A100 (80GB)** - Best performance

### Storage
- **Minimum**: 40GB
- **Recommended**: 50GB

### Cost Estimate
- **RTX 6000 Ada**: ~$1.20/hour
- **A100 (40GB)**: ~$2.50/hour
- **A100 (80GB)**: ~$4.00/hour

## Performance

### Speed
- **Generation**: 60-120 seconds per clip
- **Inference**: Slowest but highest quality
- **Memory Usage**: ~28GB VRAM

### Quality
- **Visual Quality**: Exceptional
- **Prompt Adherence**: Best in class
- **Motion Quality**: Outstanding
- **Detail Level**: Extremely high

## Use Cases

### Best For
- Professional film slim
- High-end commercial work
- Research and development
- Quality benchmarking
- Premium content creation

### Good For
- Artistic projects requiring quality
- Portfolio pieces
- Demonstrations
- High-end marketing

### Not Ideal For
- Budget-constrained projects
- Real-time applications
- Rapid prototyping
- Casual use

## Example Prompts

```text
A majestic dragon soaring through clouds at sunset
Microscopic view of cells dividing under microscope
Astronaut floating in zero gravity with Earth in background
Vintage camera zooming through Paris streets in 1960s
Abstract patterns of light and color morphing dynamically
```

## Advanced Usage

### Premium Setup
```bash
docker run -e PRESET_DOWNLOAD=MOCHI_1_PREVIEW_FP8 \
  -e ACCESS_PASSWORD=mypassword \
  --gpus all -p 3000:3000 -p 8080:8080 -p 8888:8888 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Research Configuration
```bash
docker run -e PRESET_DOWNLOAD="MOCHI_1_PREVIEW_FP8,HUNYUAN_T2V_720P,LTXV_2B_FP8_SCALED" \
  -e ACCESS_PASSWORD=mypassword \
  --gpus all -p 3000:3000 -p 8080:8080 -p 8888:8888 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Comparison with Other Models

### vs HUNYUAN_T2V_720P
- **This Model**: Superior prompt adherence, much more expensive
- **Hunyuan**: Good quality, more affordable

### vs WAN_22_5B_TIV2
- **This Model**: Dramatically better quality, 5x more expensive
- **WAN 5B**: Good balance of cost and quality

### vs LTXV_13B_FP8_SCALED
- **This Model**: Better prompt following, slower
- **LTXV 13B**: Faster, real-time capable

## Tips for Best Results

### Prompt Engineering
- Mochi understands complex, detailed prompts
- Use specific artistic and technical terms
- Include camera movements and angles
- Describe lighting, mood, and atmosphere
- Be as specific as possible

### Technical Settings
- Higher step counts (50-100) recommended
- CFG scale 7-15 works well
- Longer clips (10-20 seconds) show quality
- 720p to 1080p resolution

### Production Workflow
- Allow ample time for generation
- Test with simpler prompts first
- Use development environment for testing
- Plan for longer rendering times

## Advanced Features

### Research Setup
```bash
# Compare with other top models
docker run -e PRESET_DOWNLOAD="MOCHI_1_PREVIEW_FP8,LTXV_13B_FP8_SCALED,HUNYUAN_COMPLETE_WORKFLOW" \
  -e ACCESS_PASSWORD=mypassword \
  --gpus all -p 3000:3000 -p 8080:8080 -p 8888:8888 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Professional Pipeline
```bash
# Complete professional workflow
docker run -e PRESET_DOWNLOAD=MOCHI_1_PREVIEW_FP8 \
  -e IMAGE_PRESET_DOWNLOAD=FLUX_DEV_BASIC \
  -e AUDIO_PRESET_DOWNLOAD=AUDIO_PRODUCTION \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Troubleshooting

### Common Issues
1. **Memory errors**: Requires RTX 6000 Ada or A100
2. **Very slow generation**: Normal for this quality
3. **Long download times**: Model is very large
4. **Cost concerns**: Use for final renders only

### Performance Tips
- Use A100 for best performance
- Pre-download models during off-peak hours
- Batch similar complex prompts
- Monitor GPU utilization carefully

## Integration Examples

### With Premium Audio
```bash
docker run -e PRESET_DOWNLOAD=MOCHI_1_PREVIEW_FP8 \
  -e AUDIO_PRESET_DOWNLOAD=AUDIO_ALL \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### With State-of-the-Art Images
```bash
docker run -e PRESET_DOWNLOAD=MOCHI_1_PREVIEW_FP8 \
  -e IMAGE_PRESET_DOWNLOAD=FLUX_COMPLETE \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Production Considerations

### Cost Management
- Use only for final renders
- Test concepts with cheaper models first
- Schedule long jobs during off-peak hours
- Monitor usage carefully due to high costs

### Quality Workflow
- Develop concepts with smaller models
- Finalize prompts before using Mochi
- Allow significant time for rendering
- Plan for storage of large outputs

## Variations

### Non-FP8 Version
- **MOCHI_1_PREVIEW** - Original FP16 version (42GB)

## Next Steps

1. **Deploy RunPod** with A100 (recommended)
2. **Set environment variable** `PRESET_DOWNLOAD=MOCHI_1_PREVIEW_FP8`
3. **Access ComfyUI** at port 3000
4. **Develop prompts** using cheaper models first
5. **Render final content** with Mochi

## Alternatives

- **HUNYUAN_T2V_720P** - More affordable (12GB)
- **LTXV_13B_FP8_SCALED** - Faster generation (24GB)
- **WAN_22_5B_TIV2** - Budget-friendly (4.8GB)
- **MOCHI_1_PREVIEW** - Original version (42GB)