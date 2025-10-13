# LTXV_2B_FP8_SCALED - Real-time Video Generation

Lightricks LTX-Video 2B model for real-time video generation at 30 FPS.

## Quick Start

```bash
docker run -e PRESET_DOWNLOAD=LTXV_2B_FP8_SCALED --gpus all -p 3000:3000 zeroclue/comfyui:base-torch2.8.0-cu126
```

## Model Details

- **Size**: 4.8GB
- **Resolution**: 768x512
- **Frame Rate**: 30 FPS real-time
- **Quality**: Good quality with fast inference
- **Format**: FP8 scaled for memory efficiency

## RunPod Requirements

### Recommended GPU
- **RTX 4000 Ada (16GB)** - Perfect fit
- **RTX 6000 Ada (48GB)** - Overkill but works
- **A100 (40GB)** - Works, but expensive for this model

### Storage
- **Minimum**: 15GB
- **Recommended**: 20GB

### Cost Estimate
- **RTX 4000 Ada**: ~$0.50/hour
- **Spot instance**: ~$0.25/hour

## Performance

### Speed
- **Generation**: Real-time (30 FPS)
- **Inference**: ~2-3 seconds per 4-second clip
- **Memory Usage**: ~8GB VRAM

### Quality
- **Visual Quality**: Good
- **Motion Smoothness**: Excellent
- **Prompt Adherence**: Good
- **Consistency**: Very good across frames

## Use Cases

### Best For
- Real-time video applications
- Interactive video generation
- Prototyping and testing
- Cost-effective production

### Good For
- Social media content
- Marketing materials
- Educational videos
- Short-form content

### Not Ideal For
- High-end cinema production
- Complex narrative videos
- Ultra-high resolution needs

## Example Prompts

```text
A cat walking through a garden
Sunset over mountain range
Person typing on laptop
Ocean waves at beach
City street at night
```

## Advanced Usage

### With Upscalers
```bash
docker run -e PRESET_DOWNLOAD="LTXV_2B_FP8_SCALED,LTXV_UPSCALERS" --gpus all -p 3000:3000 zeroclue/comfyui:base-torch2.8.0-cu126
```

### Development Setup
```bash
docker run -e PRESET_DOWNLOAD=LTXV_2B_FP8_SCALED \
  -e ACCESS_PASSWORD=mypassword \
  --gpus all -p 3000:3000 -p 8080:8080 -p 8888:8888 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Comparison with Other Models

### vs LTXV_2B_GGUF_Q4_NL
- **This Model**: Better quality, more VRAM
- **GGUF Q4**: Lower quality, less VRAM (660MB)

### vs LTXV_13B_FP8_SCALED
- **This Model**: Faster, smaller, real-time
- **13B Model**: Higher quality, slower, more VRAM (24GB)

### vs WAN_22_5B_TIV2
- **This Model**: Real-time, easier to use
- **WAN 5B**: Better prompt adherence, slower

## Tips for Best Results

### Prompt Engineering
- Be specific and descriptive
- Include motion keywords
- Keep prompts concise
- Use present tense

### Technical Settings
- Use default settings for best results
- 30 FPS is optimal
- 4-8 second clips work best
- Don't exceed 720p resolution

### Cost Optimization
- Use spot instances when possible
- Batch multiple generations
- Keep sessions short for testing
- Scale up for production only

## Troubleshooting

### Common Issues
1. **Slow generation**: Check GPU utilization
2. **Poor quality**: Improve prompt specificity
3. **Memory issues**: Reduce batch size
4. **Stuttering**: Check internet connection

### Performance Tips
- Monitor GPU memory usage
- Use appropriate resolution
- Test with shorter clips first
- Check model download completion

## Integration Examples

### With Audio Generation
```bash
docker run -e PRESET_DOWNLOAD=LTXV_2B_FP8_SCALED \
  -e AUDIO_PRESET_DOWNLOAD=MUSICGEN_MEDIUM \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### With Image Generation
```bash
docker run -e PRESET_DOWNLOAD=LTXV_2B_FP8_SCALED \
  -e IMAGE_PRESET_DOWNLOAD=SDXL_BASE_V1 \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Next Steps

1. **Deploy RunPod** with RTX 4000 Ada
2. **Set environment variable** `PRESET_DOWNLOAD=LTXV_2B_FP8_SCALED`
3. **Access ComfyUI** at port 3000
4. **Start generating** real-time videos
5. **Optional**: Add upscalers or audio models

## Alternatives

- **LTXV_2B_GGUF_Q4_NL** - Lower memory usage (660MB)
- **LTXV_13B_FP8_SCALED** - Higher quality (24GB)
- **WAN_22_5B_TIV2** - Better prompt adherence (4.8GB)
- **MOCHI_1_PREVIEW_FP8** - Best quality (24GB)