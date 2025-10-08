# PRESET_DOWNLOAD Environment Variable

> The `PRESET_DOWNLOAD` environment variable accepts either a **single preset** or **multiple presets** separated by commas. \
> When set, the container will automatically download the corresponding models on startup.

## Usage Examples

### Single Preset
```bash
docker run -e PRESET_DOWNLOAD=WAN_22_5B_TIV2 zeroclue/comfyui:base-torch2.8.0-cu126
```

### Multiple Presets
```bash
docker run -e PRESET_DOWNLOAD="WAN_22_5B_TIV2,WAN_22_5B_I2V_GGUF_Q4_K_M" zeroclue/comfyui:base-torch2.8.0-cu126
```

### Manual Download (inside container)
```bash
bash /download_presets.sh WAN_22_5B_TIV2,WAN_22_5B_I2V_GGUF_Q4_K_M
```

## Available Presets

### ZeroClue WAN 2.2 5B Presets

| Preset Name | Description | Models | Size |
|------------|-------------|---------|------|
| **WAN_22_5B_TIV2** | WAN 2.2 5B Text-to-Video (FP8 scaled) | T2V model (FP8) | ~4.8GB |
| **WAN_22_5B_I2V_GGUF_Q4_K_M** | WAN 2.2 5B Image-to-Video (GGUF Q4) | I2V model (GGUF) | ~2.9GB |
| **WAN_22_5B_I2V_GGUF_Q8_0** | WAN 2.2 5B Image-to-Video (GGUF Q8) | I2V model (GGUF) | ~5.2GB |
| **WAN_22_5B_I2V_FP8_SCALED** | WAN 2.2 5B Image-to-Video (FP8 scaled) | I2V model (FP8) | ~4.8GB |
| **WAN_22_LIGHTNING_LORA** | WAN 2.2 Lightning LoRA | Lightning LoRA | ~236MB |
| **WAN_22_NSFW_LORA** | WAN 2.2 NSFW Filter LoRA | NSFW Filter LoRA | ~236MB |

### Model Details

#### WAN_22_5B_TIV2
```
- WAN 2.2 5B Text-to-Video model (FP8 scaled)
- Download URL: https://huggingface.co/Wan-Team/Wan2.2-5B/resolve/main/models/diffusion_transformer_5b_fp8.safetensors
- Target: /workspace/ComfyUI/models/diffusion_models/
```

#### WAN_22_5B_I2V_GGUF_Q4_K_M
```
- WAN 2.2 5B Image-to-Video model (GGUF Q4_K_M)
- Download URL: https://huggingface.co/brian6009/Wan2.2-5B-I2V-GGUF/resolve/main/Wan2.2-I2V-5B-Q4_K_M.gguf
- Target: /workspace/ComfyUI/models/diffusion_models/
```

#### WAN_22_5B_I2V_GGUF_Q8_0
```
- WAN 2.2 5B Image-to-Video model (GGUF Q8_0)
- Download URL: https://huggingface.co/brian6009/Wan2.2-5B-I2V-GGUF/resolve/main/Wan2.2-I2V-5B-Q8_0.gguf
- Target: /workspace/ComfyUI/models/diffusion_models/
```

#### WAN_22_5B_I2V_FP8_SCALED
```
- WAN 2.2 5B Image-to-Video model (FP8 scaled)
- Download URL: https://huggingface.co/Wan-Team/Wan2.2-5B/resolve/main/models/diffusion_transformer_i2v_5b_fp8.safetensors
- Target: /workspace/ComfyUI/models/diffusion_models/
```

#### WAN_22_LIGHTNING_LORA
```
- WAN 2.2 Lightning LoRA (faster inference)
- Download URL: https://huggingface.co/Wan-Team/Wan2.2-5B/resolve/main/loras/wan_lightning.safetensors
- Target: /workspace/ComfyUI/models/loras/
```

#### WAN_22_NSFW_LORA
```
- WAN 2.2 NSFW Filter LoRA
- Download URL: https://huggingface.co/Wan-Team/Wan2.2-5B/resolve/main/loras/wan_cnsfw.safetensors
- Target: /workspace/ComfyUI/models/loras/
```

## Usage Examples

### Complete Workflow Setup
```bash
# Download T2V model + LoRAs
docker run -e PRESET_DOWNLOAD="WAN_22_5B_TIV2,WAN_22_LIGHTNING_LORA,WAN_22_NSFW_LORA" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Lightweight GGUF Setup
```bash
# Download smaller GGUF model
docker run -e PRESET_DOWNLOAD=WAN_22_5B_I2V_GGUF_Q4_K_M \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Development Setup
```bash
# All models for development
docker run -e PRESET_DOWNLOAD="WAN_22_5B_TIV2,WAN_22_5B_I2V_GGUF_Q4_K_M,WAN_22_LIGHTNING_LORA,WAN_22_NSFW_LORA" \
  --gpus all -p 3000:3000 -p 8080:8080 -p 8888:8888 \
  -e ACCESS_PASSWORD=mypassword \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## File Organization

Downloaded models are organized as follows:

```
/workspace/ComfyUI/models/
├── diffusion_models/           # Main AI models
│   ├── diffusion_transformer_5b_fp8.safetensors
│   ├── Wan2.2-I2V-5B-Q4_K_M.gguf
│   ├── Wan2.2-I2V-5B-Q8_0.gguf
│   └── diffusion_transformer_i2v_5b_fp8.safetensors
└── loras/                     # LoRA adaptation files
    ├── wan_lightning.safetensors
    └── wan_cnsfw.safetensors
```

## Performance Notes

### Model Size Comparison
- **FP8 T2V**: 4.8GB - Best quality, larger size
- **GGUF Q4**: 2.9GB - Good quality, smaller size
- **GGUF Q8**: 5.2GB - Best quality for GGUF, larger size
- **FP8 I2V**: 4.8GB - Standard I2V model
- **LoRAs**: 236MB each - Small additions for specific effects

### Recommended Combinations

#### For Production
```bash
PRESET_DOWNLOAD="WAN_22_5B_TIV2,WAN_22_LIGHTNING_LORA"
```

#### For Development
```bash
PRESET_DOWNLOAD="WAN_22_5B_TIV2,WAN_22_5B_I2V_GGUF_Q4_K_M,WAN_22_LIGHTNING_LORA,WAN_22_NSFW_LORA"
```

#### For Testing
```bash
PRESET_DOWNLOAD="WAN_22_5B_I2V_GGUF_Q4_K_M"
```

## Adding Custom Presets

To add your own presets, see the [Adding Presets Guide](../addpreset.md) in the `.zeroclue` folder.

## Troubleshooting

### Download Issues
- Check internet connectivity
- Verify HuggingFace URLs are accessible
- Ensure sufficient disk space (models are 2-5GB each)

### Model Not Found
- Verify preset name spelling
- Check that models downloaded to correct folders
- Restart ComfyUI after downloading new models

### Performance Issues
- Use GGUF models for lower memory usage
- Add Lightning LoRA for faster inference
- Monitor GPU memory usage with nvtop