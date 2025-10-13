# WAN_22_5B_TIV2 - Balanced Video Generation

WAN 2.2 5B Text-to-Video model with balanced quality and performance.

## Quick Start

```bash
docker run -e PRESET_DOWNLOAD=WAN_22_5B_TIV2 --gpus all -p 3000:3000 zeroclue/comfyui:base-torch2.8.0-cu126
```

## Model Details

- **Size**: 4.8GB
- **Parameters**: 5 billion
- **Type**: Text-to-Video (T2V)
- **Format**: FP8 scaled
- **Resolution**: Up to 720p
- **Quality**: Excellent prompt adherence

## RunPod Requirements

### Recommended GPU
- **RTX 4000 Ada (16GB)** - Perfect fit
- **RTX 6000 Ada (48GB)** - For larger workflows
- **A100 (40GB)** - Overkill but works

### Storage
- **Minimum**: 15GB
- **Recommended**: 20GB

### Cost Estimate
- **RTX 4000 Ada**: ~$0.50/hour
- **Spot instance**: ~$0.25/hour

## Performance

### Speed
- **Generation**: 10-30 seconds per clip
- **Inference**: Medium speed
- **Memory Usage**: ~10GB VRAM

### Quality
- **Visual Quality**: Very good
- **Prompt Adherence**: Excellent
- **Motion Quality**: Good
- **Consistency**: Very good

## Use Cases

### Best For
- Prompt-based video creation
- Artistic video generation
- Content creation
- Marketing videos

### Good For
- Social media content
- Educational materials
- Prototyping
- Creative projects

### Not Ideal For
- Real-time applications
- Ultra-fast generation needs
- Very simple prompts

## Example Prompts

```text
A serene lake surrounded by mountains at sunrise
A robot walking through a futuristic city
A child playing with a dog in a park
A chef preparing food in a professional kitchen
A dancer performing ballet on stage
```

## Advanced Usage

### With Lightning LoRA
```bash
docker run -e PRESET_DOWNLOAD="WAN_22_5B_TIV2,WAN_22_LIGHTNING_LORA" --gpus all -p 3000:3000 zeroclue/comfyui:base-torch2.8.0-cu126
```

### Complete Setup
```bash
docker run -e PRESET_DOWNLOAD="WAN_22_5B_TIV2,WAN_22_LIGHTNING_LORA,WAN_22_NSFW_LORA" \
  -e ACCESS_PASSWORD=mypassword \
  --gpus all -p 3000:3000 -p 8080:8080 -p 8888:8888 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Comparison with Other Models

### vs LTXV_2B_FP8_SCALED
- **This Model**: Better prompt adherence, higher quality
- **LTXV 2B**: Faster, real-time, simpler

### vs WAN_22_5B_I2V_GGUF_Q4_K_M
- **This Model**: Text-to-video, higher quality
- **I2V Model**: Image-to-video, lower memory

### vs HUNYUAN_T2V_720P
- **This Model**: Smaller, more efficient
- **Hunyuan**: Higher resolution, more expensive

## Tips for Best Results

### Prompt Engineering
- Be descriptive and specific
- Include motion and action words
- Describe scene composition
- Use artistic style keywords

### Technical Settings
- 720p resolution works best
- 4-8 second clips optimal
- 20-30 inference steps
- CFG scale 7-10 recommended

### Workflow Optimization
- Start with simple prompts
- Gradually increase complexity
- Use Lightning LoRA for speed
- Monitor GPU memory usage

## Advanced Features

### Lightning Optimization
```bash
# 4-step generation with Lightning LoRA
docker run -e PRESET_DOWNLOAD="WAN_22_5B_TIV2,WAN_22_LIGHTNING_LORA" --gpus all -p 3000:3000 zeroclue/comfyui:base-torch2.8.0-cu126
```

### Content Filtering
```bash
# Add NSFW filtering
docker run -e PRESET_DOWNLOAD="WAN_22_5B_TIV2,WAN_22_NSFW_LORA" --gpus all -p 3000:3000 zeroclue/comfyui:base-torch2.8.0-cu126
```

## Troubleshooting

### Common Issues
1. **Slow generation**: Add Lightning LoRA
2. **Poor prompt adherence**: Improve prompt detail
3. **Memory issues**: Reduce batch size
4. **Inconsistent quality**: Check model loading

### Performance Tips
- Use FP8 for memory efficiency
- Batch similar prompts
- Monitor VRAM usage
- Check internet connectivity

## Integration Examples

### With Image Models
```bash
docker run -e PRESET_DOWNLOAD=WAN_22_5B_TIV2 \
  -e IMAGE_PRESET_DOWNLOAD=SDXL_BASE_V1 \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### With Audio Models
```bash
docker run -e PRESET_DOWNLOAD=WAN_22_5B_TIV2 \
  -e AUDIO_PRESET_DOWNLOAD=MUSICGEN_MEDIUM \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Variations

### GGUF Versions (Lower Memory)
- **WAN_22_5B_TIV2_GGUF_Q8_0** - Best quality (5.2GB)
- **WAN_22_5B_TIV2_GGUF_Q6_K** - Balanced (4.3GB)
- **WAN_22_5B_TIV2_GGUF_Q4_K_M** - Smallest (2.9GB)

### FP8 Version
- **WAN_22_5B_TIV2_FP8_E4M3FN** - Alternative FP8 format

## Next Steps

1. **Deploy RunPod** with RTX 4000 Ada
2. **Set environment variable** `PRESET_DOWNLOAD=WAN_22_5B_TIV2`
3. **Access ComfyUI** at port 3000
4. **Start with simple prompts** to test
5. **Optional**: Add Lightning LoRA for speed

## Alternatives

- **LTXV_2B_FP8_SCALED** - Real-time generation (4.8GB)
- **HUNYUAN_T2V_720P** - Higher resolution (12GB)
- **MOCHI_1_PREVIEW_FP8** - Best quality (24GB)
- **WAN_22_5B_I2V_GGUF_Q4_K_M** - Image-to-video (2.9GB)