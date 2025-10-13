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

### LTX-Video (Lightricks) - Real-time Video Generation

| Preset Name | Description | Models | Size |
|------------|-------------|---------|------|
| **LTXV_2B_FP8_SCALED** | LTX-Video 2B Text-to-Video (FP8 scaled) | 2B DiT model (FP8) | ~4.8GB |
| **LTXV_2B_DISTILLED_FP8** | LTX-Video 2B Distilled (FP8, faster) | 2B distilled model (FP8) | ~4.5GB |
| **LTXV_2B_GGUF_Q8_0** | LTX-Video 2B (GGUF Q8, high quality) | 2B model (GGUF Q8) | ~8.2GB |
| **LTXV_2B_GGUF_Q6_K** | LTX-Video 2B (GGUF Q6, balanced) | 2B model (GGUF Q6) | ~5.0GB |
| **LTXV_2B_GGUF_Q4_NL** | LTX-Video 2B (GGUF Q4, lightweight) | 2B model (GGUF Q4) | ~660MB |
| **LTXV_13B_FP8_SCALED** | LTX-Video 13B Text-to-Video (FP8 scaled) | 13B DiT model (FP8) | ~24GB |
| **LTXV_13B_DISTILLED_FP8** | LTX-Video 13B Distilled (FP8, faster) | 13B distilled model (FP8) | ~22GB |
| **LTXV_UPSCALERS** | LTX-Video Temporal & Spatial Upscalers | Upscaler models | ~3.2GB |
| **LTXV_COMPLETE_WORKFLOW** | Complete LTXV setup with all components | 2B model + upscalers | ~8GB |

### HunyuanVideo (Tencent) - High-Quality Video Generation

| Preset Name | Description | Models | Size |
|------------|-------------|---------|------|
| **HUNYUAN_T2V_720P** | HunyuanVideo Text-to-Video (720p) | T2V model + encoders + VAE | ~12GB |
| **HUNYUAN_I2V_720P_V1** | HunyuanVideo Image-to-Video v1 (concat) | I2V model v1 + encoders + VAE | ~14GB |
| **HUNYUAN_I2V_720P_V2** | HunyuanVideo Image-to-Video v2 (replace) | I2V model v2 + encoders + VAE | ~14GB |
| **HUNYUAN_COMPLETE_WORKFLOW** | Complete HunyuanVideo setup | T2V + I2V v1 + I2V v2 + all components | ~18GB |

### Cosmos Predict2 (NVIDIA) - Video2World Generation

| Preset Name | Description | Models | Size |
|------------|-------------|---------|------|
| **COSMOS_PREDICT2_V2W_480P** | Cosmos Predict2 Video2World (480p 16fps) | 2B model + text encoder + VAE | ~8.5GB |
| **COSMOS_PREDICT2_COMPLETE** | Complete Cosmos Predict2 setup | All components + utilities | ~10GB |

### Mochi 1 Preview (Genmo) - Large Open-Source Model

| Preset Name | Description | Models | Size |
|------------|-------------|---------|------|
| **MOCHI_1_PREVIEW** | Mochi 1 Preview Video Generation | Main model + VAE + text encoder | ~42GB |
| **MOCHI_1_PREVIEW_FP8** | Mochi 1 Preview (FP8 optimized) | FP8 model + VAE + text encoder | ~24GB |

### WAN 2.1 Specialized Workflows - Advanced Video Generation

| Preset Name | Description | Models | Size |
|------------|-------------|---------|------|
| **WAN21_BASE_1.3B** | WAN 2.1 Text-to-Video 1.3B | T2V model + VAE + Text Encoder | ~3GB |
| **WAN21_I2V_480P_14B** | WAN 2.1 Image-to-Video 480p 14B | I2V model + CLIP Vision + VAE + Text Encoder | ~12GB |
| **WAN21_I2V_720P_14B** | WAN 2.1 Image-to-Video 720p 14B | I2V model + CLIP Vision + VAE + Text Encoder | ~13GB |
| **WAN21_VACE_1.3B** | WAN 2.1 VACE Camera Control 1.3B | VACE model + VAE + Text Encoder | ~4GB |
| **WAN21_VACE_14B** | WAN 2.1 VACE Camera Control 14B | VACE model + VAE + Text Encoder | ~12GB |
| **WAN21_ATI_14B** | WAN 2.1 Audio-Text-to-Image 14B | ATI model + CLIP Vision + VAE + Text Encoder | ~13GB |
| **WAN21_FLF_14B_FP16** | WAN 2.1 FLF Flow-based 14B (FP16) | FLF model + CLIP Vision + VAE + Text Encoder | ~33GB |
| **WAN21_FLF_14B_FP8** | WAN 2.1 FLF Flow-based 14B (FP8) | FLF model + CLIP Vision + VAE + Text Encoder | ~17GB |
| **WAN21_FUN_CONTROL_1.3B** | WAN 2.1 Fun Control 1.3B | Fun Control model + CLIP Vision + VAE + Text Encoder | ~4GB |
| **WAN21_FUN_CONTROL_14B** | WAN 2.1 Fun Control 14B | Fun Control model + CLIP Vision + VAE + Text Encoder | ~12GB |
| **WAN21_FUN_CAMERA_1.3B** | WAN 2.1 Fun Camera 1.3B | Fun Camera model + CLIP Vision + VAE + Text Encoder | ~4GB |
| **WAN21_FUN_CAMERA_14B** | WAN 2.1 Fun Camera 14B | Fun Camera model + CLIP Vision + VAE + Text Encoder | ~12GB |
| **WAN21_FUN_INP_1.3B** | WAN 2.1 Fun Inpainting 1.3B | Fun Inpaint model + CLIP Vision + VAE + Text Encoder | ~4GB |
| **WAN21_FUN_INP_14B** | WAN 2.1 Fun Inpainting 14B | Fun Inpaint model + CLIP Vision + VAE + Text Encoder | ~12GB |
| **WAN21_COMPLETE_WORKFLOW** | Ultimate WAN 2.1 Setup (All workflows) | All models + dependencies | ~50GB |

### WAN 2.2 Specialized Workflows - Advanced Video Generation

| Preset Name | Description | Models | Size |
|------------|-------------|---------|------|
| **WAN22_ANIMATE_14B** | WAN 2.2 Animate 14B (Character animation) | Animate model + CLIP Vision + VAE + Text Encoder | ~12GB |
| **WAN22_ANIMATE_WITH_LORA** | WAN 2.2 Animate with LightX2V LoRA | Animate model + Lightning LoRA + all components | ~12.5GB |
| **WAN22_S2V_14B_FP8** | WAN 2.2 Sound-to-Video 14B (FP8) | S2V model + Audio encoder + Text encoder + VAE | ~10GB |
| **WAN22_S2V_14B_BF16** | WAN 2.2 Sound-to-Video 14B (BF16) | S2V model + Audio encoder + Text encoder + VAE | ~14GB |
| **WAN22_S2V_COMPLETE** | Complete WAN 2.2 S2V with Lightning LoRA | All S2V models + Lightning LoRA + dependencies | ~15GB |
| **WAN22_FUN_INPAINT_14B** | WAN 2.2 Fun Inpainting (Start/End frames) | Fun Inpaint models (High/Low noise) + dependencies | ~12GB |
| **WAN22_FUN_INPAINT_WITH_LORA** | WAN 2.2 Fun Inpainting with Lightning | Fun Inpaint models + Lightning LoRAs + all components | ~13GB |
| **WAN22_FUN_CONTROL_14B** | WAN 2.2 Fun Control (Canny/Depth/Pose) | Fun Control models (High/Low noise) + dependencies | ~12GB |
| **WAN22_FUN_CONTROL_WITH_LORA** | WAN 2.2 Fun Control with Lightning | Fun Control models + Lightning LoRAs + all components | ~13GB |
| **WAN22_FUN_CAMERA_14B** | WAN 2.2 Fun Camera (Cinematic motion) | Fun Camera model + dependencies | ~12GB |
| **WAN22_T2V_14B_COMPLETE** | Complete WAN 2.2 T2V 14B Setup | T2V models (High/Low noise) + all dependencies | ~15GB |
| **WAN22_I2V_14B_COMPLETE** | Complete WAN 2.2 I2V 14B Setup | I2V models (High/Low noise) + all dependencies | ~16GB |
| **WAN22_COMPLETE_WORKFLOW** | Ultimate WAN 2.2 Setup (All workflows) | All models + LoRAs + dependencies | ~45GB |

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

### LTX-Video Model Details

#### LTXV_2B_FP8_SCALED
```
- LTX-Video 2B DiT model (FP8 scaled)
- Download URL: https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltx-video-2b-v0.9.8-distilled-fp8.safetensors
- Target: /workspace/ComfyUI/models/diffusion_models/
- Resolution: 768x512, 30 FPS real-time generation
```

#### LTXV_2B_DISTILLED_FP8
```
- LTX-Video 2B Distilled model (FP8, faster inference)
- Download URL: https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltx-video-2b-v0.9.8-distilled-fp8.safetensors
- Target: /workspace/ComfyUI/models/diffusion_models/
- Optimized for faster generation with slight quality trade-off
```

#### LTXV_2B_GGUF_Q8_0
```
- LTX-Video 2B model (GGUF Q8_0, high quality)
- Download URL: https://huggingface.co/calcuis/ltxv-gguf/resolve/main/ltxv-2b-0.9.8-distilled-q8_0.gguf
- Target: /workspace/ComfyUI/models/diffusion_models/
- Best quality GGUF variant
```

#### LTXV_2B_GGUF_Q6_K
```
- LTX-Video 2B model (GGUF Q6_K, balanced)
- Download URL: https://huggingface.co/calcuis/ltxv-gguf/resolve/main/ltxv-2b-0.9.8-distilled-q6_k.gguf
- Target: /workspace/ComfyUI/models/diffusion_models/
- Balanced quality and size
```

#### LTXV_2B_GGUF_Q4_NL
```
- LTX-Video 2B model (GGUF Q4_NL, lightweight)
- Download URL: https://huggingface.co/calcuis/ltxv-gguf/resolve/main/ltxv-2b-0.9.8-distilled-iq4_nl.gguf
- Target: /workspace/ComfyUI/models/diffusion_models/
- Minimal memory usage
```

#### LTXV_13B_FP8_SCALED
```
- LTX-Video 13B DiT model (FP8 scaled, highest quality)
- Download URL: https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltx-video-13b-v0.9.8-dev-fp8.safetensors
- Target: /workspace/ComfyUI/models/diffusion_models/
- Best quality, requires significant VRAM
```

#### LTXV_13B_DISTILLED_FP8
```
- LTX-Video 13B Distilled model (FP8, faster)
- Download URL: https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltx-video-13b-v0.9.8-distilled-fp8.safetensors
- Target: /workspace/ComfyUI/models/diffusion_models/
- High quality with optimized inference
```

#### LTXV_UPSCALERS
```
- LTX-Video Temporal Upscaler
- Download URL: https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltx-video-temporal-upscaler-v0.9.8.safetensors
- Target: /workspace/ComfyUI/models/diffusion_models/
- LTX-Video Spatial Upscaler
- Download URL: https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltx-video-spatial-upscaler-v0.9.8.safetensors
- Target: /workspace/ComfyUI/models/diffusion_models/
```

### HunyuanVideo Model Details

#### HUNYUAN_T2V_720P
```
- HunyuanVideo T2V model (720p generation)
- Download URLs:
  - T2V Model: https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/diffusion_models/hunyuan_video_t2v_720p_bf16.safetensors
  - CLIP-L: https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/text_encoders/clip_l.safetensors
  - LLava-LLaMA3: https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/text_encoders/llava_llama3_fp8_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/vae/hunyuan_video_vae_bf16.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, text_encoders, vae)
- Resolution: 1280x720p
```

#### HUNYUAN_I2V_720P_V1
```
- HunyuanVideo I2V model v1 "concat" (720p generation)
- Download URLs:
  - I2V Model: https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/diffusion_models/hunyuan_video_image_to_video_720p_bf16.safetensors
  - CLIP-L: https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/text_encoders/clip_l.safetensors
  - LLava-LLaMA3: https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/text_encoders/llava_llama3_fp8_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/vae/hunyuan_video_vae_bf16.safetensors
  - CLIP-Vision: https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/clip_vision/llava_llama3_vision.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, text_encoders, vae, clip_vision)
- Image concatenation method
```

#### HUNYUAN_I2V_720P_V2
```
- HunyuanVideo I2V model v2 "replace" (720p generation, improved)
- Download URLs:
  - I2V Model: https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/diffusion_models/hunyuan_video_v2_replace_image_to_video_720p_bf16.safetensors
  - CLIP-L: https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/text_encoders/clip_l.safetensors
  - LLava-LLaMA3: https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/text_encoders/llava_llama3_fp8_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/vae/hunyuan_video_vae_bf16.safetensors
  - CLIP-Vision: https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/clip_vision/llava_llama3_vision.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, text_encoders, vae, clip_vision)
- Image replacement method (recommended)
```

### Cosmos Predict2 Model Details

#### COSMOS_PREDICT2_V2W_480P
```
- Cosmos Predict2 Video2World model (480p 16fps)
- Download URLs:
  - Main Model: https://huggingface.co/Comfy-Org/Cosmos_Predict2_repackaged/resolve/main/cosmos_predict2_2b_video2world_480p_16fps.safetensors
  - Text Encoder: https://huggingface.co/comfyanonymous/cosmos_1.0_text_encoder_and_VAE_ComfyUI/resolve/main/text_encoders/oldt5_xxl_fp8_e4m3fn_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, text_encoders, vae)
- Resolution: 854x480 at 16fps
```

### Mochi 1 Preview Model Details

#### MOCHI_1_PREVIEW
```
- Mochi 1 Preview Video Generation model
- Download URLs:
  - Main Model: https://huggingface.co/genmo/mochi-1-preview/resolve/main/mochi_preview_bf16.safetensors
  - VAE: https://huggingface.co/genmo/mochi-1-preview/resolve/main/vae.safetensors
  - Text Encoder: https://huggingface.co/Comfy-Org/stable_diffusion_3_repackaged/resolve/main/text_encoders/t5xxl_fp16.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, vae, text_encoders)
- Large 40GB+ model with excellent prompt adherence
```

#### MOCHI_1_PREVIEW_FP8
```
- Mochi 1 Preview (FP8 optimized version)
- Download URLs:
  - Main Model: https://huggingface.co/genmo/mochi-1-preview/resolve/main/mochi_preview_fp8.safetensors
  - VAE: https://huggingface.co/genmo/mochi-1-preview/resolve/main/vae.safetensors
  - Text Encoder: https://huggingface.co/Comfy-Org/stable_diffusion_3_repackaged/resolve/main/text_encoders/t5xxl_fp8_e4m3fn.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, vae, text_encoders)
- Optimized for lower memory usage
```

### WAN 2.2 Specialized Workflow Model Details

#### WAN22_ANIMATE_14B
```
- WAN 2.2 Animate 14B (Character animation)
- Download URLs:
  - Animate Model: https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Animate/Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors
  - CLIP Vision: https://huggingface.co/Comfy-Org/stable_diffusion_3_repackaged/resolve/main/clip_vision/clip_vision_h.safetensors
  - Text Encoder: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, clip_vision, text_encoders, vae)
- Specialized for character and object animation
```

#### WAN22_ANIMATE_WITH_LORA
```
- WAN 2.2 Animate 14B with LightX2V LoRA
- Download URLs:
  - Animate Model: https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Animate/Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors
  - LightX2V LoRA: https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Animate/lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors
  - CLIP Vision: https://huggingface.co/Comfy-Org/stable_diffusion_3_repackaged/resolve/main/clip_vision/clip_vision_h.safetensors
  - Text Encoder: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, loras, clip_vision, text_encoders, vae)
- Enhanced animation with 4-step LoRA optimization
```

#### WAN22_S2V_14B_FP8
```
- WAN 2.2 Sound-to-Video 14B (FP8 optimized)
- Download URLs:
  - S2V Model: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_s2v_14B_fp8_scaled.safetensors
  - Audio Encoder: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/audio_encoders/wav2vec2_large_english_fp16.safetensors
  - Text Encoder: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, audio_encoders, text_encoders, vae)
- Generates video from audio input
```

#### WAN22_S2V_14B_BF16
```
- WAN 2.2 Sound-to-Video 14B (BF16 high quality)
- Download URLs:
  - S2V Model: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_s2v_14B_bf16.safetensors
  - Audio Encoder: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/audio_encoders/wav2vec2_large_english_fp16.safetensors
  - Text Encoder: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, audio_encoders, text_encoders, vae)
- Higher quality S2V generation
```

#### WAN22_S2V_COMPLETE
```
- Complete WAN 2.2 Sound-to-Video Setup
- Download URLs:
  - S2V Model FP8: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_s2v_14B_fp8_scaled.safetensors
  - S2V Model BF16: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_s2v_14B_bf16.safetensors
  - Audio Encoder: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/audio_encoders/wav2vec2_large_english_fp16.safetensors
  - Lightning LoRA: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/loras/wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors
  - Text Encoder: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, audio_encoders, loras, text_encoders, vae)
- Complete S2V workflow with all optimizations
```

#### WAN22_FUN_INPAINT_14B
```
- WAN 2.2 Fun Inpainting 14B (Start/End frame control)
- Download URLs:
  - Fun Inpaint High Noise: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_fun_inpaint_high_noise_14B_fp8_scaled.safetensors
  - Fun Inpaint Low Noise: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_fun_inpaint_low_noise_14B_fp8_scaled.safetensors
  - Text Encoder: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, text_encoders, vae)
- Generates intermediate video between start and end frames
```

#### WAN22_FUN_INPAINT_WITH_LORA
```
- WAN 2.2 Fun Inpainting 14B with Lightning LoRA
- Download URLs:
  - Fun Inpaint High Noise: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_fun_inpaint_high_noise_14B_fp8_scaled.safetensors
  - Fun Inpaint Low Noise: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_fun_inpaint_low_noise_14B_fp8_scaled.safetensors
  - Lightning LoRA High: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors
  - Lightning LoRA Low: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors
  - Text Encoder: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, loras, text_encoders, vae)
- Optimized inpainting with 4-step generation
```

#### WAN22_FUN_CONTROL_14B
```
- WAN 2.2 Fun Control 14B (Canny/Depth/Pose control)
- Download URLs:
  - Fun Control High Noise: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_fun_control_high_noise_14B_fp8_scaled.safetensors
  - Fun Control Low Noise: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_fun_control_low_noise_14B_fp8_scaled.safetensors
  - Text Encoder: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, text_encoders, vae)
- ControlNet-based video generation (requires ComfyUI-comfyui_controlnet_aux)
```

#### WAN22_FUN_CONTROL_WITH_LORA
```
- WAN 2.2 Fun Control 14B with Lightning LoRA
- Download URLs:
  - Fun Control High Noise: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_fun_control_high_noise_14B_fp8_scaled.safetensors
  - Fun Control Low Noise: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_fun_control_low_noise_14B_fp8_scaled.safetensors
  - Lightning LoRA High: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors
  - Lightning LoRA Low: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors
  - Text Encoder: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, loras, text_encoders, vae)
- Fast ControlNet-based generation with Lightning optimization
```

#### WAN22_FUN_CAMERA_14B
```
- WAN 2.2 Fun Camera 14B (Cinematic camera motion)
- Download URLs:
  - Fun Camera Model: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_fun_camera_14B_fp8_scaled.safetensors
  - Text Encoder: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, text_encoders, vae)
- Generates video with cinematic camera movements (pan, tilt, zoom)
```

#### WAN22_T2V_14B_COMPLETE
```
- Complete WAN 2.2 T2V 14B Setup
- Download URLs:
  - T2V High Noise: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors
  - T2V Low Noise: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors
  - Text Encoder: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, text_encoders, vae)
- Complete text-to-video workflow with high/low noise variants
```

#### WAN22_I2V_14B_COMPLETE
```
- Complete WAN 2.2 I2V 14B Setup
- Download URLs:
  - I2V High Noise: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_i2v_high_noise_14B_fp16.safetensors
  - I2V Low Noise: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_i2v_low_noise_14B_fp16.safetensors
  - Text Encoder: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, text_encoders, vae)
- Complete image-to-video workflow with high/low noise variants
```

#### WAN22_COMPLETE_WORKFLOW
```
- Ultimate WAN 2.2 Complete Setup (All workflows)
- Includes all models from above presets
- Total size: ~45GB for complete WAN 2.2 ecosystem
- Supports: T2V, I2V, Animate, S2V, Fun Inpainting, Fun Control, Fun Camera
- Target: /workspace/ComfyUI/models/ (all subdirectories)
- Complete professional video generation suite
```

### WAN 2.1 Specialized Workflow Model Details

#### WAN21_BASE_1.3B
```
- WAN 2.1 Text-to-Video 1.3B Base Model
- Download URLs:
  - T2V Model: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors
  - Text Encoder: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, text_encoders, vae)
- Lightweight T2V generation
```

#### WAN21_I2V_480P_14B
```
- WAN 2.1 Image-to-Video 480p 14B
- Download URLs:
  - I2V Model: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_i2v_480p_14B_fp16.safetensors
  - CLIP Vision: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors
  - Text Encoder: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, clip_vision, text_encoders, vae)
- 480p resolution output
```

#### WAN21_I2V_720P_14B
```
- WAN 2.1 Image-to-Video 720p 14B
- Download URLs:
  - I2V Model: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_i2v_720p_14B_fp16.safetensors
  - CLIP Vision: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors
  - Text Encoder: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, clip_vision, text_encoders, vae)
- 720p high-resolution output
```

#### WAN21_VACE_1.3B
```
- WAN 2.1 VACE Camera Control 1.3B
- Download URLs:
  - VACE Model: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_vace_1.3B_fp16.safetensors
  - Text Encoder: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, text_encoders, vae)
- Video Aspect Camera Control for camera motion
```

#### WAN21_VACE_14B
```
- WAN 2.1 VACE Camera Control 14B
- Download URLs:
  - VACE Model: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_vace_14B_fp16.safetensors
  - Text Encoder: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, text_encoders, vae)
- High-quality camera control
```

#### WAN21_ATI_14B
```
- WAN 2.1 Audio-Text-to-Image 14B
- Download URLs:
  - ATI Model: https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Wan2_1-I2V-ATI-14B_fp8_e4m3fn.safetensors
  - CLIP Vision: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors
  - Text Encoder: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, clip_vision, text_encoders, vae)
- Audio-text-to-image/video generation
```

#### WAN21_FLF_14B_FP16
```
- WAN 2.1 FLF Flow-based 14B (FP16)
- Download URLs:
  - FLF Model: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_flf2v_720p_14B_fp16.safetensors
  - CLIP Vision: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors
  - Text Encoder: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, clip_vision, text_encoders, vae)
- Flow-based Latent Fusion, 720p*1280 optimal output
```

#### WAN21_FLF_14B_FP8
```
- WAN 2.1 FLF Flow-based 14B (FP8 optimized)
- Download URLs:
  - FLF Model: https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Wan2_1-FLF2V-14B-720P_fp8_e4m3fn.safetensors
  - CLIP Vision: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors
  - Text Encoder: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, clip_vision, text_encoders, vae)
- Memory-optimized FLF generation
```

#### WAN21_FUN_CONTROL_1.3B
```
- WAN 2.1 Fun Control 1.3B
- Download URLs:
  - Fun Control Model: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_fun_control_1.3B_bf16.safetensors
  - CLIP Vision: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors
  - Text Encoder: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, clip_vision, text_encoders, vae)
- Lightweight control-based generation
```

#### WAN21_FUN_CONTROL_14B
```
- WAN 2.1 Fun Control 14B
- Download URLs:
  - Fun Control Model: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/Wan2.1-Fun-14B-Control.safetensors
  - CLIP Vision: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors
  - Text Encoder: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, clip_vision, text_encoders, vae)
- High-quality control-based generation
```

#### WAN21_FUN_CAMERA_1.3B
```
- WAN 2.1 Fun Camera 1.3B
- Download URLs:
  - Fun Camera Model: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_fun_camera_v1.1_1.3B_bf16.safetensors
  - CLIP Vision: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors
  - Text Encoder: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, clip_vision, text_encoders, vae)
- Lightweight camera motion control
```

#### WAN21_FUN_CAMERA_14B
```
- WAN 2.1 Fun Camera 14B
- Download URLs:
  - Fun Camera Model: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_fun_camera_v1.1_14B_bf16.safetensors
  - CLIP Vision: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors
  - Text Encoder: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, clip_vision, text_encoders, vae)
- High-quality camera motion control
```

#### WAN21_FUN_INP_1.3B
```
- WAN 2.1 Fun Inpainting 1.3B
- Download URLs:
  - Fun Inpaint Model: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_fun_inp_1.3B_bf16.safetensors
  - CLIP Vision: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors
  - Text Encoder: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, clip_vision, text_encoders, vae)
- Lightweight inpainting workflow
```

#### WAN21_FUN_INP_14B
```
- WAN 2.1 Fun Inpainting 14B
- Download URLs:
  - Fun Inpaint Model: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/Wan2.1-Fun-14B-InP.safetensors
  - CLIP Vision: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors
  - Text Encoder: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - VAE: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors
- Target: /workspace/ComfyUI/models/ (diffusion_models, clip_vision, text_encoders, vae)
- High-quality inpainting workflow
```

#### WAN21_COMPLETE_WORKFLOW
```
- Ultimate WAN 2.1 Complete Setup (All workflows)
- Includes all models from above presets
- Total size: ~50GB for complete WAN 2.1 ecosystem
- Supports: T2V, I2V (480p/720p), VACE, ATI, FLF, Fun Control, Fun Camera, Fun Inpainting
- Target: /workspace/ComfyUI/models/ (all subdirectories)
- Complete WAN 2.1 professional video generation suite
```

## Usage Examples

### Complete Workflow Setup
```bash
# WAN 2.2 Complete Setup
docker run -e PRESET_DOWNLOAD="WAN_22_5B_TIV2,WAN_22_LIGHTNING_LORA,WAN_22_NSFW_LORA" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126

# LTX-Video Complete Workflow (real-time generation)
docker run -e PRESET_DOWNLOAD="LTXV_2B_FP8_SCALED,LTXV_UPSCALERS" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126

# HunyuanVideo Complete Workflow (high-quality 720p)
docker run -e PRESET_DOWNLOAD="HUNYUAN_COMPLETE_WORKFLOW" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Lightweight GGUF Setup
```bash
# WAN 2.2 Lightweight GGUF
docker run -e PRESET_DOWNLOAD=WAN_22_5B_I2V_GGUF_Q4_K_M \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126

# LTX-Video Ultra Lightweight (660MB)
docker run -e PRESET_DOWNLOAD=LTXV_2B_GGUF_Q4_NL \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### High-Quality Production Setup
```bash
# LTX-Video High Quality (13B model)
docker run -e PRESET_DOWNLOAD="LTXV_13B_FP8_SCALED,LTXV_UPSCALERS" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126

# Mochi 1 Preview (best prompt adherence)
docker run -e PRESET_DOWNLOAD=MOCHI_1_PREVIEW_FP8 \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Development Setup
```bash
# Comprehensive video generation setup
docker run -e PRESET_DOWNLOAD="LTXV_2B_FP8_SCALED,HUNYUAN_T2V_720P,COSMOS_PREDICT2_V2W_480P,WAN_22_5B_TIV2" \
  --gpus all -p 3000:3000 -p 8080:8080 -p 8888:8888 \
  -e ACCESS_PASSWORD=mypassword \
  zeroclue/comfyui:base-torch2.8.0-cu126

# Complete video model research setup
docker run -e PRESET_DOWNLOAD="LTXV_COMPLETE_WORKFLOW,HUNYUAN_COMPLETE_WORKFLOW,COSMOS_PREDICT2_COMPLETE,MOCHI_1_PREVIEW_FP8,WAN_22_5B_TIV2" \
  --gpus all -p 3000:3000 -p 8080:8080 -p 8888:8888 \
  -e ACCESS_PASSWORD=mypassword \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### WAN 2.2 Specialized Workflow Setup

#### Character Animation
```bash
# WAN 2.2 Animate with LoRA optimization
docker run -e PRESET_DOWNLOAD="WAN22_ANIMATE_WITH_LORA" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126

# Basic character animation
docker run -e PRESET_DOWNLOAD="WAN22_ANIMATE_14B" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

#### Sound-to-Video Generation
```bash
# Complete S2V setup with optimization
docker run -e PRESET_DOWNLOAD="WAN22_S2V_COMPLETE" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126

# Lightweight S2V (FP8)
docker run -e PRESET_DOWNLOAD="WAN22_S2V_14B_FP8" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

#### ControlNet Video Generation
```bash
# Fun Control with Lightning optimization
docker run -e PRESET_DOWNLOAD="WAN22_FUN_CONTROL_WITH_LORA" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126

# Cinematic camera motion
docker run -e PRESET_DOWNLOAD="WAN22_FUN_CAMERA_14B" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

#### Advanced Inpainting
```bash
# Start/End frame inpainting with Lightning
docker run -e PRESET_DOWNLOAD="WAN22_FUN_INPAINT_WITH_LORA" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126

# Complete WAN 2.2 ecosystem (45GB)
docker run -e PRESET_DOWNLOAD="WAN22_COMPLETE_WORKFLOW" \
  --gpus all -p 3000:3000 -p 8080:8080 -p 8888:8888 \
  -e ACCESS_PASSWORD=mypassword \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### WAN 2.1 Specialized Workflow Setup

#### Basic WAN 2.1 Generation
```bash
# Lightweight T2V (3GB)
docker run -e PRESET_DOWNLOAD="WAN21_BASE_1.3B" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126

# High-quality I2V 720p (13GB)
docker run -e PRESET_DOWNLOAD="WAN21_I2V_720P_14B" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

#### Advanced WAN 2.1 Workflows
```bash
# Camera motion control (VACE)
docker run -e PRESET_DOWNLOAD="WAN21_VACE_14B" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126

# Audio-text-to-image/video (ATI)
docker run -e PRESET_DOWNLOAD="WAN21_ATI_14B" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126

# Flow-based generation (FLF)
docker run -e PRESET_DOWNLOAD="WAN21_FLF_14B_FP8" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126

# Complete WAN 2.1 ecosystem (50GB)
docker run -e PRESET_DOWNLOAD="WAN21_COMPLETE_WORKFLOW" \
  --gpus all -p 3000:3000 -p 8080:8080 -p 8888:8888 \
  -e ACCESS_PASSWORD=mypassword \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

#### Mixed WAN Ecosystem Setup
```bash
# Complete WAN ecosystem (WAN 2.1 + WAN 2.2 = 95GB)
docker run -e PRESET_DOWNLOAD="WAN21_COMPLETE_WORKFLOW,WAN22_COMPLETE_WORKFLOW" \
  --gpus all -p 3000:3000 -p 8080:8080 -p 8888:8888 \
  -e ACCESS_PASSWORD=mypassword \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## File Organization

Downloaded models are organized as follows:

```
/workspace/ComfyUI/models/
├── diffusion_models/           # Main AI video models
│   # WAN 2.2 Models
│   ├── diffusion_transformer_5b_fp8.safetensors
│   ├── Wan2.2-I2V-5B-Q4_K_M.gguf
│   ├── Wan2.2-I2V-5B-Q8_0.gguf
│   ├── diffusion_transformer_i2v_5b_fp8.safetensors
│   # LTX-Video Models
│   ├── ltx-video-2b-v0.9.8-distilled-fp8.safetensors
│   ├── ltx-video-13b-v0.9.8-dev-fp8.safetensors
│   ├── ltxv-2b-0.9.8-distilled-q8_0.gguf
│   ├── ltxv-2b-0.9.8-distilled-q6_k.gguf
│   ├── ltxv-2b-0.9.8-distilled-iq4_nl.gguf
│   ├── ltx-video-temporal-upscaler-v0.9.8.safetensors
│   ├── ltx-video-spatial-upscaler-v0.9.8.safetensors
│   # HunyuanVideo Models
│   ├── hunyuan_video_t2v_720p_bf16.safetensors
│   ├── hunyuan_video_image_to_video_720p_bf16.safetensors
│   ├── hunyuan_video_v2_replace_image_to_video_720p_bf16.safetensors
│   # Cosmos Predict2 Models
│   ├── cosmos_predict2_2b_video2world_480p_16fps.safetensors
│   # Mochi Models
│   ├── mochi_preview_bf16.safetensors
│   ├── mochi_preview_fp8.safetensors
├── text_encoders/             # Text encoding models
│   # WAN Text Encoders
│   ├── umt5_xxl_fp8_e4m3fn_scaled.safetensors
│   # HunyuanVideo Text Encoders
│   ├── clip_l.safetensors
│   ├── llava_llama3_fp8_scaled.safetensors
│   # Cosmos Text Encoders
│   ├── oldt5_xxl_fp8_e4m3fn_scaled.safetensors
│   # Mochi Text Encoders
│   ├── t5xxl_fp16.safetensors
│   ├── t5xxl_fp8_e4m3fn.safetensors
│   # GGUF Text Encoders
│   ├── umt5-xxl-encoder-Q8_0.gguf
│   ├── umt5-xxl-encoder-Q6_K.gguf
│   └── umt5-xxl-encoder-Q5_K_M.gguf
├── vae/                       # VAE models
│   # WAN VAEs
│   ├── wan2.2_vae.safetensors
│   ├── wan_2.1_vae.safetensors
│   # HunyuanVideo VAE
│   ├── hunyuan_video_vae_bf16.safetensors
│   # Mochi VAE
│   └── vae.safetensors
├── clip_vision/               # CLIP Vision models
│   └── llava_llama3_vision.safetensors
└── loras/                     # LoRA adaptation files
    ├── wan_lightning.safetensors
    ├── wan_cnsfw.safetensors
    └── additional lora files...
```

## Performance Notes

### Model Size Comparison

#### LTX-Video Models
- **LTXV 2B FP8**: 4.8GB - Real-time generation, good quality
- **LTXV 2B Distilled FP8**: 4.5GB - Faster inference, slight quality trade-off
- **LTXV 2B GGUF Q8**: 8.2GB - Best quality GGUF
- **LTXV 2B GGUF Q6**: 5.0GB - Balanced quality and size
- **LTXV 2B GGUF Q4**: 660MB - Minimal memory usage
- **LTXV 13B FP8**: 24GB - Highest quality, requires significant VRAM
- **LTXV 13B Distilled FP8**: 22GB - High quality with optimized inference
- **LTXV Upscalers**: 3.2GB - Enhanced resolution capabilities

#### HunyuanVideo Models
- **T2V 720p**: ~12GB - High-quality text-to-video generation
- **I2V 720p**: ~14GB - High-quality image-to-video generation
- **Complete Workflow**: ~18GB - All HunyuanVideo components

#### Cosmos & Mochi Models
- **Cosmos Predict2**: 8.5GB - Video2World generation (480p 16fps)
- **Mochi 1 Preview**: 42GB - Excellent prompt adherence, very large
- **Mochi 1 Preview FP8**: 24GB - Optimized memory usage

#### WAN 2.2 Models
- **FP8 T2V**: 4.8GB - Best quality, larger size
- **GGUF Q4**: 2.9GB - Good quality, smaller size
- **GGUF Q8**: 5.2GB - Best quality for GGUF, larger size
- **FP8 I2V**: 4.8GB - Standard I2V model
- **LoRAs**: 236MB each - Small additions for specific effects

### VRAM Requirements (Approximate)

#### Minimum Requirements (8GB VRAM)
- LTXV_2B_GGUF_Q4_NL (660MB)
- WAN_22_5B_I2V_GGUF_Q4_K_M (2.9GB)

#### Recommended Requirements (16GB VRAM)
- LTXV_2B_FP8_SCALED (4.8GB)
- WAN_22_5B_TIV2 (4.8GB)
- COSMOS_PREDICT2_V2W_480P (8.5GB)

#### High-End Requirements (24GB+ VRAM)
- HUNYUAN_T2V_720P (12GB)
- LTXV_13B_FP8_SCALED (24GB)
- MOCHI_1_PREVIEW_FP8 (24GB)

#### Professional Requirements (48GB+ VRAM)
- MOCHI_1_PREVIEW (42GB)
- Complete multi-model setups

### Recommended Combinations

#### For Production

**Real-time Video Generation (LTX-Video)**
```bash
PRESET_DOWNLOAD="LTXV_2B_FP8_SCALED,LTXV_UPSCALERS"
```

**High-Quality Video Generation (HunyuanVideo)**
```bash
PRESET_DOWNLOAD="HUNYUAN_T2V_720P,HUNYUAN_I2V_720P_V2"
```

**Balanced Production Setup**
```bash
PRESET_DOWNLOAD="LTXV_2B_FP8_SCALED,WAN_22_5B_TIV2,WAN_22_LIGHTNING_LORA"
```

#### For Development

**Comprehensive Video Development**
```bash
PRESET_DOWNLOAD="LTXV_2B_FP8_SCALED,HUNYUAN_T2V_720P,COSMOS_PREDICT2_V2W_480P,WAN_22_5B_TIV2,WAN_22_5B_I2V_GGUF_Q4_K_M"
```

**Research Setup with All Models**
```bash
PRESET_DOWNLOAD="LTXV_COMPLETE_WORKFLOW,HUNYUAN_COMPLETE_WORKFLOW,COSMOS_PREDICT2_COMPLETE,MOCHI_1_PREVIEW_FP8,WAN_22_5B_TIV2,WAN_22_LIGHTNING_LORA,WAN_22_NSFW_LORA"
```

#### For Testing

**Lightweight Testing (660MB)**
```bash
PRESET_DOWNLOAD="LTXV_2B_GGUF_Q4_NL"
```

**Standard Testing**
```bash
PRESET_DOWNLOAD="LTXV_2B_GGUF_Q6_K,WAN_22_5B_I2V_GGUF_Q4_K_M"
```

**High-Quality Testing**
```bash
PRESET_DOWNLOAD="LTXV_2B_FP8_SCALED,WAN_22_5B_TIV2,WAN_22_LIGHTNING_LORA"
```

#### Specialized Use Cases

**Best Prompt Adherence**
```bash
PRESET_DOWNLOAD="MOCHI_1_PREVIEW_FP8"
```

**Maximum Quality**
```bash
PRESET_DOWNLOAD="LTXV_13B_FP8_SCALED,LTXV_UPSCALERS"
```

**Fast Real-time Generation**
```bash
PRESET_DOWNLOAD="LTXV_2B_DISTILLED_FP8"
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