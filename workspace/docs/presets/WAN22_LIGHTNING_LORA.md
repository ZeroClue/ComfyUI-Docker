# WAN22_LIGHTNING_LORA - Video Generation Speed Enhancement

Wan 2.2 Lightning LoRA for dramatically faster video generation inference speed.

## Overview

Lightning LoRA adapter for Wan 2.2 video generation models that reduces inference time by 2-3x while maintaining good quality.

## Model Details

- **Type**: LoRA Adapter
- **Purpose**: Speed enhancement
- **Inference Speed**: 2-3x faster
- **Memory Overhead**: +1.4GB
- **Compatibility**: Wan 2.2 T2V and I2V models

## Installation

The preset manager will automatically download:
- Main LoRA file: `loras/wan22_lightning.safetensors`

## Usage

### Prerequisites
Must be used with a base Wan 2.2 model:
- `WAN_22_5B_TIV2`
- `WAN_22_5B_I2V_GGUF_Q8_0`
- `WAN22_I2V_A14B_GGUF_Q8_0`

### Workflow Integration
1. Load base Wan 2.2 model in ComfyUI
2. Apply Lightning LoRA to the model
3. Use standard text-to-video workflow
4. Enjoy 2-3x faster generation

## Performance Impact

### Speed Improvements
- **Base Model**: ~30 seconds per clip
- **With Lightning**: ~10-15 seconds per clip
- **Quality Retention**: ~85-90% of base quality

### Memory Requirements
- **Additional VRAM**: +1.4GB
- **Total with WAN_22_5B_TIV2**: ~10.6GB VRAM

## Use Cases

### Best For
- Rapid prototyping
- Batch video generation
- Real-time applications
- Cost-effective slim
- Testing workflows

### Good For
- Social media content
- Quick iterations
- Concept development
- Educational content

### Not Ideal For
- Maximum quality requirements
- Fine artistic control
- Production final renders

## Installation Examples

### With Base WAN Model
```bash
docker run -e PRESET_DOWNLOAD="WAN_22_5B_TIV2,WAN22_LIGHTNING_LORA" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Complete Lightning Setup
```bash
docker run -e PRESET_DOWNLOAD="WAN_22_5B_TIV2,WAN22_LIGHTNING_LORA,WAN22_NSFW_LORA" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Technical Details

### Model Architecture
- LoRA (Low-Rank Adaptation) architecture
- Trained specifically for speed optimization
- Compatible with Wan 2.2 T2V and I2V models
- Preserves temporal consistency

### File Format
- **Format**: SafeTensors
- **Size**: 1.4GB
- **Location**: `/workspace/ComfyUI/models/loras/`

## Troubleshooting

### Common Issues
1. **LoRA not loading**: Ensure base model is loaded first
2. **Quality reduction**: Adjust prompt strength or CFG scale
3. **Memory issues**: Reduce batch size or use smaller base models
4. **Speed not improved**: Check LoRA is properly applied

### Performance Tips
- Use with appropriate base models
- Monitor VRAM usage
- Test different strength settings
- Batch similar prompts

## Integration Examples

### With Multiple Enhancements
```bash
docker run -e PRESET_DOWNLOAD="WAN_22_5B_TIV2,WAN22_LIGHTNING_LORA,UPSCALE_MODELS" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### With Complete Workflow
```bash
docker run -e PRESET_DOWNLOAD="VIDEO_COMPLETE,WAN22_LIGHTNING_LORA" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Production Considerations

### Cost Efficiency
- Significantly reduces GPU time
- Ideal for batch processing
- Cost-effective for high-volume generation
- Maintains acceptable quality for most use cases

### Quality vs Speed Trade-off
- **Speed**: 2-3x faster generation
- **Quality**: ~85-90% of base model quality
- **Memory**: +1.4GB additional VRAM
- **Recommendation**: Use for prototyping, switch to base for final renders

## Alternatives

### Other Speed Enhancements
- **WAN22_S2V_FP8_SCALED** - Audio-to-video with efficiency
- **LTXV_2B_FP8_SCALED** - Real-time generation alternative

### Quality-focused Options
- **WAN_22_5B_TIV2** (without LoRA) - Maximum quality
- **MOCHI_1_PREVIEW_FP8** - Next-generation quality

## Next Steps

1. **Deploy with base Wan 2.2 model**
2. **Add Lightning LoRA** for speed boost
3. **Test workflow** with sample prompts
4. **Fine-tune settings** for optimal results
5. **Scale up** for slim use

## Summary

WAN22_LIGHTNING_LORA is an essential enhancement for anyone needing faster video generation with Wan 2.2 models. It provides a 2-3x speed improvement while maintaining good quality, making it ideal for rapid prototyping and cost-effective video slim.