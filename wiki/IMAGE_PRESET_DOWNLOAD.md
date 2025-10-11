# IMAGE_PRESET_DOWNLOAD Environment Variable

> The `IMAGE_PRESET_DOWNLOAD` environment variable accepts either a **single preset** or **multiple presets** separated by commas. \
> When set, the container will automatically download the corresponding image generation models on startup.

## Usage Examples

### Single Preset
```bash
docker run -e IMAGE_PRESET_DOWNLOAD=REALISTIC_VISION_V6 zeroclue/comfyui:base-torch2.8.0-cu126
```

### Multiple Presets
```bash
docker run -e IMAGE_PRESET_DOWNLOAD="SDXL_BASE_V1,ESRGAN_MODELS" zeroclue/comfyui:base-torch2.8.0-cu126
```

### Manual Download (inside container)
```bash
bash /download_image_presets.sh REALISTIC_VISION_V6,SDXL_BASE_V1
```

### Combined with Video Presets
```bash
docker run \
  -e IMAGE_PRESET_DOWNLOAD="SDXL_BASE_V1,REALISTIC_VISION_V6" \
  -e PRESET_DOWNLOAD="WAN_22_5B_TIV2" \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Available Presets

### SDXL Models (High Quality)

| Preset Name | Description | Models | Size |
|------------|-------------|---------|------|
| **SDXL_BASE_V1** | Stable Diffusion XL Base 1.0 + VAE | SDXL Base + VAE | ~6.9GB |
| **JUGGERNAUT_XL_V8** | High-quality anime/art generation | Animagine XL 3.0 | ~6.9GB |
| **REALVIS_XL_V4** | Photorealistic image generation | RealVis XL v4.0 | ~6.9GB |
| **DREAMSHAPER_XL_V7** | Balanced artistic style | DreamShaper XL v7 | ~6.9GB |

### SD 1.5 Models (Versatile)

| Preset Name | Description | Models | Size |
|------------|-------------|---------|------|
| **REALISTIC_VISION_V6** | Photorealistic images | Realistic Vision v6 | ~4.2GB |
| **DELIBERATE_V6** | High-quality artistic images | Deliberate v6 | ~4.2GB |
| **DREAMSHAPER_V8** | Balanced general-purpose model | DreamShaper v8 | ~4.2GB |
| **PROTOGEN_XL** | Creative and experimental | ProtoGen X5.8 | ~4.2GB |

### Anime/Art Style Models

| Preset Name | Description | Models | Size |
|------------|-------------|---------|------|
| **ANYTHING_V5** | High-quality anime style | Anything V5 | ~4.2GB |
| **MEINAMIX_V12** | Premium anime quality | MeinaMix v12 | ~4.2GB |
| **COUNTERFEIT_V3** | Artistic anime style | Counterfeit V3.0 | ~4.2GB |

### Utility Models

| Preset Name | Description | Models | Size |
|------------|-------------|---------|------|
| **SDXL_REFINER** | Detail enhancement for SDXL | SDXL Refiner | ~6.2GB |
| **ESRGAN_MODELS** | Image upscaling collection | 3 ESRGAN models | ~1.2GB |
| **INPAINTING_MODELS** | Image editing/repair | SD Inpainting models | ~6.9GB |

### Complete Workflow Bundles

| Preset Name | Description | Models | Size |
|------------|-------------|---------|------|
| **SDXL_COMPLETE_WORKFLOW** | Full SDXL pipeline | Base + Refiner + VAE | ~13.8GB |
| **REALISTIC_COMPLETE_WORKFLOW** | Complete realistic workflow | RV v6 + VAE + Upscale | ~8.5GB |
| **ANIME_COMPLETE_WORKFLOW** | Complete anime workflow | Anything V5 + Anime Upscale | ~8.5GB |

### Qwen Image Models (Advanced 20B Parameter Models)

| Preset Name | Description | Models | Size |
|------------|-------------|---------|------|
| **QWEN_IMAGE_BASIC** | Qwen text-to-image workflow | Diffusion + Text Encoder + VAE | ~17-24GB |
| **QWEN_IMAGE_EDIT** | Qwen image editing workflow | Edit Model + Text Encoder + VAE | ~17-24GB |
| **QWEN_IMAGE_COMPLETE** | Complete Qwen workflow | All Qwen models (generation + editing) | ~37-47GB |
| **QWEN_IMAGE_CHINESE** | Optimized for Chinese text | Same as QWEN_IMAGE_BASIC | ~17-24GB |

### Flux Image Models (State-of-the-Art 12B Parameter Models)

| Preset Name | Description | Models | Size |
|------------|-------------|---------|------|
| **FLUX_SCHNELL_BASIC** | Fast generation (4 steps) | Schnell + Encoders + VAE | ~25-35GB |
| **FLUX_DEV_BASIC** | High quality generation (20-50 steps) | Dev + Encoders + VAE | ~25-35GB |
| **FLUX_SCHNELL_FP8** | Memory efficient fast generation | FP8 Schnell + Encoders + VAE | ~20-30GB |
| **FLUX_DEV_FP8** | Memory efficient high quality | FP8 Dev + Encoders + VAE | ~20-30GB |
| **FLUX_COMPLETE** | Full Flux collection | Both models + Encoders + VAE | ~50-70GB |
| **FLUX_PRODUCTION** | Production optimized (FP8 both) | FP8 Schnell + FP8 Dev + Encoders + VAE | ~25-35GB |

## Model Details

### SDXL_BASE_V1
```
- Stable Diffusion XL Base 1.0 (highest quality SDXL model)
- SDXL VAE (optimized VAE for SDXL)
- Download URLs: SDXL Base + VAE
- Target: /workspace/ComfyUI/models/checkpoints/, /workspace/ComfyUI/models/vae/
```

### REALISTIC_VISION_V6
```
- Realistic Vision V6.0 (best for photorealistic images)
- No VAE included (uses built-in)
- Download URL: Realistic Vision v6.0
- Target: /workspace/ComfyUI/models/checkpoints/
```

### JUGGERNAUT_XL_V8
```
- Animagine XL 3.0 (high-quality anime/art)
- Optimized for artistic and anime styles
- Download URL: Animagine XL 3.0
- Target: /workspace/ComfyUI/models/checkpoints/
```

### ESRGAN_MODELS
```
- Real-ESRGAN x4plus (general upscaling)
- Real-ESRGAN x4plus_anime_6B (anime optimized)
- Real-ESRGAN x2plus (2x upscaling)
- Target: /workspace/ComfyUI/models/upscale_models/
```

### QWEN_IMAGE_BASIC
```
- Qwen-Image 20B parameter MMDiT model (FP8 quantized)
- Qwen 2.5 VL 7B text encoder (FP8 scaled)
- Qwen Image VAE
- Download URLs: All from Comfy-Org/Qwen-Image_ComfyUI split_files
- Targets: diffusion_models/, text_encoders/, vae/
- License: Apache 2.0 (Commercial-friendly)
```

### QWEN_IMAGE_EDIT
```
- Qwen-Image Edit model (FP8 quantized)
- Qwen 2.5 VL 7B text encoder (FP8 scaled)
- Qwen Image VAE
- Specialized for image editing and modification
- Download URLs: All from Comfy-Org/Qwen-Image_ComfyUI split_files
- Targets: diffusion_models/, text_encoders/, vae/
```

### QWEN_IMAGE_COMPLETE
```
- Qwen-Image generation model (FP8)
- Qwen-Image edit model (FP8)
- Qwen 2.5 VL 7B text encoder (FP8 scaled)
- Qwen Image VAE
- Complete workflow with generation and editing
- Download URLs: All from Comfy-Org/Qwen-Image_ComfyUI split_files
- Targets: diffusion_models/, text_encoders/, vae/
```

### QWEN_IMAGE_CHINESE
```
- Same models as QWEN_IMAGE_BASIC
- Optimized workflow for Chinese text generation
- Superior Chinese character rendering
- Download URLs: All from Comfy-Org/Qwen-Image_ComfyUI split_files
- Targets: diffusion_models/, text_encoders/, vae/
```

### FLUX_SCHNELL_BASIC
```
- FLUX.1 Schnell 12B parameter model (rectified flow transformer)
- CLIP-L text encoder (for understanding)
- T5-XXL text encoder (FP8 quantized for efficiency)
- Flux VAE (ae.safetensors)
- 4-step generation for very fast results
- Download URLs: black-forest-labs/FLUX.1-schnell + comfyanonymous/flux_text_encoders
- Targets: unet/, clip/, vae/
- License: Apache 2.0 (Commercial-friendly)
```

### FLUX_DEV_BASIC
```
- FLUX.1 Dev 12B parameter model (rectified flow transformer)
- CLIP-L text encoder (for understanding)
- T5-XXL text encoder (FP8 quantized for efficiency)
- Flux VAE (ae.safetensors)
- 20-50 step generation for highest quality
- Download URLs: black-forest-labs/FLUX.1-dev + comfyanonymous/flux_text_encoders
- Targets: unet/, clip/, vae/
- License: Custom (non-commercial research)
```

### FLUX_SCHNELL_FP8
```
- FLUX.1 Schnell FP8 quantized model (memory efficient)
- Same text encoders and VAE as basic version
- Reduced VRAM requirements while maintaining speed
- Ideal for systems with 12-16GB VRAM
- Download URLs: Comfy-Org/flux1-schnell + others
- Targets: unet/, clip/, vae/
```

### FLUX_DEV_FP8
```
- FLUX.1 Dev FP8 quantized model (memory efficient)
- Same text encoders and VAE as basic version
- Reduced VRAM requirements while maintaining quality
- Ideal for systems with 12-16GB VRAM
- Download URLs: Comfy-Org/flux1-dev + others
- Targets: unet/, clip/, vae/
```

### FLUX_COMPLETE
```
- Both FLUX.1 Schnell and FLUX.1 Dev models
- Shared text encoders and VAE
- Complete flexibility for speed vs quality trade-offs
- Largest download but most versatile
- Download URLs: Both model repositories + shared encoders
- Targets: unet/, clip/, vae/
```

### FLUX_PRODUCTION
```
- FP8 quantized versions of both Schnell and Dev
- Optimized for production workloads
- Balanced memory usage and performance
- Best for continuous operation
- Download URLs: Comfy-Org repositories + shared encoders
- Targets: unet/, clip/, vae/
```

## Usage Examples

### Quick Start with SDXL
```bash
# Get started with high-quality SDXL model
docker run -e IMAGE_PRESET_DOWNLOAD=SDXL_BASE_V1 \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Realistic Photography Setup
```bash
# Complete realistic photography workflow
docker run -e IMAGE_PRESET_DOWNLOAD=REALISTIC_COMPLETE_WORKFLOW \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Anime Art Generation
```bash
# Complete anime workflow with upscaling
docker run -e IMAGE_PRESET_DOWNLOAD=ANIME_COMPLETE_WORKFLOW \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Professional Setup
```bash
# Multiple high-quality models for different styles
docker run -e IMAGE_PRESET_DOWNLOAD="SDXL_COMPLETE_WORKFLOW,REALISTIC_VISION_V6,ANYTHING_V5" \
  --gpus all -p 3000:3000 -p 8080:8080 -p 8888:8888 \
  -e ACCESS_PASSWORD=mypassword \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Qwen Image Generation
```bash
# Basic Qwen workflow for high-quality generation
docker run -e IMAGE_PRESET_DOWNLOAD=QWEN_IMAGE_BASIC \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Qwen with Chinese Text Support
```bash
# Optimized for Chinese text generation
docker run -e IMAGE_PRESET_DOWNLOAD=QWEN_IMAGE_CHINESE \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Qwen Complete Workflow
```bash
# Full Qwen workflow with generation and editing
docker run -e IMAGE_PRESET_DOWNLOAD=QWEN_IMAGE_COMPLETE \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Flux Fast Generation
```bash
# Fast 4-step generation with Flux Schnell
docker run -e IMAGE_PRESET_DOWNLOAD=FLUX_SCHNELL_BASIC \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Flux High Quality Generation
```bash
# High quality 20-50 step generation with Flux Dev
docker run -e IMAGE_PRESET_DOWNLOAD=FLUX_DEV_BASIC \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Flux Memory Efficient
```bash
# Memory efficient FP8 models for systems with limited VRAM
docker run -e IMAGE_PRESET_DOWNLOAD=FLUX_SCHNELL_FP8 \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Flux Production Setup
```bash
# Production-optimized setup with both models
docker run -e IMAGE_PRESET_DOWNLOAD=FLUX_PRODUCTION \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Combined Image + Video Generation
```bash
# Both image and video generation capabilities
docker run \
  -e IMAGE_PRESET_DOWNLOAD="SDXL_BASE_V1,REALISTIC_VISION_V6" \
  -e PRESET_DOWNLOAD="WAN_22_5B_TIV2,WAN22_LIGHTNING_LORA" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## File Organization

Downloaded models are organized as follows:

```
/workspace/ComfyUI/models/
├── checkpoints/           # Main AI models (SDXL, SD 1.5)
│   ├── sd_xl_base_1.0.safetensors
│   ├── realisticVision_v60B1_noVAE.safetensors
│   ├── anything-v5-prerelease.safetensors
│   └── ...
├── vae/                   # VAE models for specific models
│   ├── sdxl_vae_fp16_fix.safetensors
│   └── ...
├── upscale_models/        # Image enhancement models
│   ├── RealESRGAN_x4plus.safetensors
│   ├── RealESRGAN_x4plus_anime_6B.safetensors
│   └── ...
└── [other model directories for different use cases]
```

## Performance Notes

### Model Size Comparison
- **SDXL Models**: 6.9GB each - Highest quality, requires more VRAM
- **SD 1.5 Models**: 4.2GB each - Good quality, lower VRAM usage
- **Qwen Models**: 17-24GB each - 20B parameter models, highest quality and capabilities
- **Flux Models**: 20-35GB each - 12B parameter state-of-the-art models
- **VAE Models**: ~300MB each - Additional quality enhancement
- **Upscale Models**: 200-500MB each - Post-processing enhancement
- **Complete Workflows**: 8-70GB total - Multiple models for complete pipelines (Flux and Qwen workflows are largest)

### Recommended Combinations

#### For Beginners
```bash
IMAGE_PRESET_DOWNLOAD="SDXL_BASE_V1"
```

#### For Photographers
```bash
IMAGE_PRESET_DOWNLOAD="REALISTIC_COMPLETE_WORKFLOW"
```

#### For Anime Artists
```bash
IMAGE_PRESET_DOWNLOAD="ANIME_COMPLETE_WORKFLOW"
```

#### For Professionals
```bash
IMAGE_PRESET_DOWNLOAD="SDXL_COMPLETE_WORKFLOW,REALISTIC_VISION_V6,ANYTHING_V5,ESRGAN_MODELS"
```

#### For Mixed Media
```bash
IMAGE_PRESET_DOWNLOAD="SDXL_BASE_V1,REALISTIC_VISION_V6,JUGGERNAUT_XL_V8"
```

#### For Chinese Text Generation
```bash
IMAGE_PRESET_DOWNLOAD="QWEN_IMAGE_CHINESE"
```

#### For Advanced Users (High VRAM)
```bash
IMAGE_PRESET_DOWNLOAD="QWEN_IMAGE_COMPLETE,SDXL_BASE_V1"
```

#### For State-of-the-Art Quality
```bash
IMAGE_PRESET_DOWNLOAD="FLUX_DEV_BASIC"
```

#### For Speed and Quality Balance
```bash
IMAGE_PRESET_DOWNLOAD="FLUX_PRODUCTION"
```

#### For Maximum Flexibility
```bash
IMAGE_PRESET_DOWNLOAD="FLUX_COMPLETE,SDXL_COMPLETE_WORKFLOW"
```

## Workflow Recommendations

### SDXL Workflow
1. Generate with `SDXL_BASE_V1`
2. Enhance details with `SDXL_REFINER`
3. Upscale with `ESRGAN_MODELS`

### Realistic Photography Workflow
1. Generate with `REALISTIC_VISION_V6`
2. Refine with custom prompts
3. Upscale with `ESRGAN_MODELS`

### Anime Art Workflow
1. Generate with `ANYTHING_V5` or `MEINAMIX_V12`
2. Refine details
3. Upscale with anime-optimized ESRGAN models

### Professional Workflow
1. Start with `SDXL_BASE_V1` for high-quality base
2. Use specific style models (`REALISTIC_VISION_V6`, `ANYTHING_V5`)
3. Apply `SDXL_REFINER` for detail enhancement
4. Upscale with appropriate `ESRGAN_MODELS`

### Qwen Workflow
1. Generate with `QWEN_IMAGE_BASIC` or `QWEN_IMAGE_CHINESE` for highest quality
2. For image editing tasks, use `QWEN_IMAGE_EDIT`
3. Qwen excels at complex text rendering (especially Chinese characters)
4. Supports multiple artistic styles and precise editing
5. For complete workflow, use `QWEN_IMAGE_COMPLETE` with both generation and editing

### Flux Workflow
1. For fast generation, use `FLUX_SCHNELL_BASIC` (4 steps, very fast)
2. For highest quality, use `FLUX_DEV_BASIC` (20-50 steps, exceptional quality)
3. For memory efficiency, use FP8 versions (`FLUX_SCHNELL_FP8`, `FLUX_DEV_FP8`)
4. For production workloads, use `FLUX_PRODUCTION` (balanced FP8 models)
5. For maximum flexibility, use `FLUX_COMPLETE` with both models
6. Flux excels at following complex prompts and achieving photorealistic results
7. Commercial use: prefer FLUX_SCHNELL (Apache 2.0 licensed) over FLUX_DEV (research only)

## Troubleshooting

### Download Issues
- Check internet connectivity
- Verify HuggingFace URLs are accessible
- Ensure sufficient disk space (models are 2-7GB each)

### Model Not Found
- Verify preset name spelling
- Check that models downloaded to correct folders
- Restart ComfyUI after downloading new models

### Performance Issues
- Use SD 1.5 models for lower memory usage
- Monitor GPU memory usage with nvtop
- Consider using smaller models for development/testing

### Out of Memory Errors
- Reduce image resolution
- Use SD 1.5 models instead of SDXL
- Close other GPU applications
- Consider using models with built-in VAE to save memory

## Comparison with Video Presets

| Feature | IMAGE_PRESET_DOWNLOAD | PRESET_DOWNLOAD |
|---------|----------------------|-----------------|
| **Purpose** | Image generation models | Video generation models |
| **Model Types** | SDXL, SD 1.5, VAE, Upscale | WAN 2.2, Text Encoders, VAE |
| **File Sizes** | 2-7GB per model | 3-5GB per model |
| **Use Cases** | Art, photography, design | Video creation, animation |
| **Workflow** | Text-to-Image, Image-to-Image | Text-to-Video, Image-to-Video |
| **Memory Usage** | Moderate to High | High |

Both systems can be used together for comprehensive AI media generation capabilities.