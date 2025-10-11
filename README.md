# ZeroClue ComfyUI-Docker

> 🔄 **Auto-updated every 8 hours** to always include the latest version.

> 💬 Feedback & Issues → [GitHub Issues](https://github.com/ZeroClue/ComfyUI-Docker/issues)

> 🚀 This Docker image is maintained by ZeroClue and designed for both cloud deployment and local use.

> 🌟 **Original Project**: This is a customised fork of the excellent [somb1/ComfyUI-Docker](https://github.com/somb1/ComfyUI-Docker) project. All credit goes to the original maintainers for creating this powerful ComfyUI distribution.

## 🔌 Exposed Ports

| Port | Type | Service     |
| ---- | ---- | ----------- |
| 22   | TCP  | SSH         |
| 3000 | HTTP | ComfyUI     |
| 8080 | HTTP | code-server |
| 8888 | HTTP | JupyterLab  |

---

## 🏷️ Tag Format

```text
zeroclue/comfyui:(A)-torch2.8.0-(B)
```

* **(A)**: `base`, `slim`, `minimal`, `production`, or `ultra-slim`
  * `base`: ComfyUI + Manager + custom nodes + code-server (**~8-12GB**)
  * `slim`: ComfyUI + Manager + code-server (no custom nodes) (**~6-8GB**)
  * `minimal`: ComfyUI + Manager only (no custom nodes, no code-server) (**~4-6GB**)
  * `production`: ComfyUI + Manager, optimized for serving (**~4-5GB**) 🆕
  * `ultra-slim`: ComfyUI only, minimal dependencies (**~2-3GB**) 🆕
* **(B)**: CUDA version → `cu126`, `cu128` (new variants), `cu124`, `cu129`, `cu130`

---

## 🧱 Image Variants

### Development & Full-Featured Variants
| Image Name                            | Custom Nodes | Code Server | JupyterLab | Size | CUDA |
| ------------------------------------- | ------------ | ----------- | ---------- | ---- | ---- |
| `zeroclue/comfyui:base-torch2.8.0-cu126` | ✅ Yes        | ✅ Yes      | ✅ Yes     | ~8-12GB | 12.6 |
| `zeroclue/comfyui:base-torch2.8.0-cu128` | ✅ Yes        | ✅ Yes      | ✅ Yes     | ~8-12GB | 12.8 |
| `zeroclue/comfyui:slim-torch2.8.0-cu126` | ❌ No         | ✅ Yes      | ✅ Yes     | ~6-8GB | 12.6 |
| `zeroclue/comfyui:slim-torch2.8.0-cu128` | ❌ No         | ✅ Yes      | ✅ Yes     | ~6-8GB | 12.8 |
| `zeroclue/comfyui:minimal-torch2.8.0-cu126` | ❌ No         | ❌ No       | ✅ Yes     | ~4-6GB | 12.6 |
| `zeroclue/comfyui:minimal-torch2.8.0-cu128` | ❌ No         | ❌ No       | ✅ Yes     | ~4-6GB | 12.8 |

### 🆕 Production Optimized Variants
| Image Name                                    | Custom Nodes | Code Server | JupyterLab | Size | CUDA | Use Case |
| --------------------------------------------- | ------------ | ----------- | ---------- | ---- | ---- | -------- |
| `zeroclue/comfyui:production-torch2.8.0-cu126` | ❌ No         | ❌ No       | ❌ No      | ~4-5GB | 12.6 | Production serving |
| `zeroclue/comfyui:production-torch2.8.0-cu128` | ❌ No         | ❌ No       | ❌ No      | ~4-5GB | 12.8 | Production serving |
| `zeroclue/comfyui:ultra-slim-torch2.8.0-cu126` | ❌ No         | ❌ No       | ❌ No      | ~2-3GB | 12.6 | Minimal footprint |
| `zeroclue/comfyui:ultra-slim-torch2.8.0-cu128` | ❌ No         | ❌ No       | ❌ No      | ~2-3GB | 12.8 | Minimal footprint |

> 👉 To switch: **Edit Pod/Template** → set `Container Image`.

### 🚀 Variant Selection Guide

- **For Development**: Use `base` or `slim` variants with full tooling
- **For Production**: Use `production` variants (30-50% smaller, faster startup)
- **For Resource-Constrained**: Use `ultra-slim` variants (60-70% smaller)
- **All variants** support the same preset systems and environment variables

### 🔄 Migration Guide

Switching between variants is easy and preserves all your data:

#### From Base to Production
```bash
# 1. Stop current container
docker stop my_comfyui

# 2. Start with production variant (same volume)
docker run --gpus all \
  -v my_workspace:/workspace \
  -e PRESET_DOWNLOAD="WAN_22_5B_TIV2" \
  -e IMAGE_PRESET_DOWNLOAD="SDXL_BASE_V1" \
  zeroclue/comfyui:production-torch2.8.0-cu126
```

#### Benefits of Migration
- **Smaller Size**: 30-70% reduction in image size
- **Faster Startup**: No development tools to initialize
- **Lower Memory**: Reduced runtime footprint
- **Same Functionality**: All presets and custom nodes work identically

> 👉 To switch: **Edit Pod/Template** → set `Container Image`.

---

## ⚙️ Environment Variables

| Variable                | Description                                                                | Default   |
| ----------------------- | -------------------------------------------------------------------------- | --------- |
| `ACCESS_PASSWORD`       | Password for JupyterLab & code-server                                      | (unset)   |
| `ENABLE_CODE_SERVER`    | Enable/disable code-server (VS Code web IDE) (`True`/`False`)             | `True`    |
| `TIME_ZONE`             | [Timezone](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) (e.g., `Asia/Seoul`)   | `Etc/UTC` |
| `COMFYUI_EXTRA_ARGS`    | Extra ComfyUI options (e.g. `--fast`)                        | (unset)   |
| `INSTALL_SAGEATTENTION` | Install [SageAttention2](https://github.com/thu-ml/SageAttention) on start (`True`/`False`) | `False`    |
| `FORCE_SYNC_ALL`        | Force full resync of venv and ComfyUI on startup (`True`/`False`) | `False`    |
| `PRESET_DOWNLOAD`       | Download video generation model presets at startup (comma-separated list). **See below**. | (unset)   |
| `IMAGE_PRESET_DOWNLOAD` | Download image generation model presets at startup (comma-separated list). **See below**. | (unset)   |
| `AUDIO_PRESET_DOWNLOAD` | Download audio generation model presets at startup (comma-separated list). ⚠️ **Experimental** - **See below**. | (unset)   |

> 👉 To set: **Edit Pod/Template** → **Add Environment Variable** (Key/Value).

> ⚠️ SageAttention2 requires **Ampere+ GPUs** and ~5 minutes to install.

---

## 🔧 Triple Preset System

> This Docker container features a **triple preset system** that supports automatic downloading of models for video, image, and audio generation. Each preset system is independent and can be used alone or combined with others for complete multimedia generation.

### 🎬 Video Generation (PRESET_DOWNLOAD)

> The `PRESET_DOWNLOAD` environment variable accepts either a **single preset** or **multiple presets** separated by commas.\
> (e.g. `WAINSFW_V140` or `WAN22_I2V_A14B_GGUF_Q8_0,WAN22_LIGHTNING_LORA,WAN22_NSFW_LORA`) \
> When set, the container will automatically download the corresponding video generation models on startup.

#### Manual Execution
```bash
bash /download_presets.sh WAN22_I2V_A14B_GGUF_Q8_0,WAN22_LIGHTNING_LORA
```

#### Available Video Presets Include:
- **WAN Video Models**: WAN_22_5B_TIV2, WAN22_I2V_A14B_GGUF_Q8_0, WAN22_T2V_A14B
- **Image Models**: WAINSFW_V140, NTRMIX_V40
- **Enhancement LoRAs**: WAN22_LIGHTNING_LORA, WAN22_NSFW_LORA
- **Utilities**: UPSCALE_MODELS, WAN22_S2V_FP8_SCALED

### 🖼️ Image Generation (IMAGE_PRESET_DOWNLOAD)

> The `IMAGE_PRESET_DOWNLOAD` environment variable accepts either a **single preset** or **multiple presets** separated by commas.\
> When set, the container will automatically download the corresponding image generation models on startup.

#### Manual Execution
```bash
bash /download_image_presets.sh SDXL_BASE_V1,REALISTIC_VISION_V6
```

#### Available Image Presets Include:
- **SDXL Models**: SDXL_BASE_V1, JUGGERNAUT_XL_V8, REALVIS_XL_V4, DREAMSHAPER_XL_V7
- **SD 1.5 Models**: REALISTIC_VISION_V6, DELIBERATE_V6, DREAMSHAPER_V8, PROTOGEN_XL
- **Anime/Art Models**: ANYTHING_V5, MEINAMIX_V12, COUNTERFEIT_V3
- **Qwen Models**: QWEN_IMAGE_BASIC, QWEN_IMAGE_CHINESE (20B parameter, superior Chinese text)
- **Flux Models**: FLUX_SCHNELL_BASIC, FLUX_DEV_BASIC (12B parameter, state-of-the-art)
- **Utility Models**: ESRGAN_MODELS, SDXL_REFINER, INPAINTING_MODELS
- **Complete Workflows**: SDXL_COMPLETE_WORKFLOW, REALISTIC_COMPLETE_WORKFLOW, ANIME_COMPLETE_WORKFLOW

### 🎵 Audio Generation (AUDIO_PRESET_DOWNLOAD) ⚠️ **EXPERIMENTAL**

> ⚠️ **Warning**: The audio generation presets are **experimental** and may contain bugs, compatibility issues, or instability. The audio custom nodes are actively developed and may not work reliably with all ComfyUI versions. Use with caution and report issues to the respective custom node repositories.

> The `AUDIO_PRESET_DOWNLOAD` environment variable accepts either a **single preset** or **multiple presets** separated by commas.\
> When set, the container will automatically download the corresponding audio generation models and custom nodes on startup.

#### Manual Execution
```bash
bash /download_audio_presets.sh MUSICGEN_MEDIUM,BARK_BASIC
```

#### Available Audio Presets Include:
- **Text-to-Speech**: BARK_BASIC, TTS_AUDIO_SUITE, PARLER_TTS
- **Music Generation**: MUSICGEN_SMALL, MUSICGEN_MEDIUM, ACE_STEP, SONGBLOOM
- **Audio Processing**: STABLE_AUDIO_OPEN
- **Complete Workflows**: AUDIO_SPEECH_COMPLETE, AUDIO_MUSIC_COMPLETE, AUDIO_PRODUCTION, AUDIO_ALL

### 🌟 Combined Usage Examples

#### Complete Multimedia Generation
```bash
docker run \
  -e PRESET_DOWNLOAD="WAN_22_5B_TIV2,WAN22_LIGHTNING_LORA" \
  -e IMAGE_PRESET_DOWNLOAD="SDXL_BASE_V1,REALISTIC_VISION_V6" \
  -e AUDIO_PRESET_DOWNLOAD="MUSICGEN_MEDIUM,BARK_BASIC" \
  zeroclue/comfyui:base-torch2.8.0-cu126
```
> ⚠️ **Note**: Audio presets are experimental - see warnings above

#### Professional Setup
```bash
docker run \
  -e IMAGE_PRESET_DOWNLOAD="FLUX_DEV_BASIC,QWEN_IMAGE_COMPLETE" \
  -e AUDIO_PRESET_DOWNLOAD="AUDIO_PRODUCTION" \
  -e PRESET_DOWNLOAD="WAN_22_5B_TIV2" \
  zeroclue/comfyui:base-torch2.8.0-cu126
```
> ⚠️ **Note**: Audio presets are experimental - see warnings above

#### Quick Start Examples
```bash
# Video generation only
docker run -e PRESET_DOWNLOAD=WAN_22_5B_TIV2 zeroclue/comfyui:base-torch2.8.0-cu126

# High-quality image generation
docker run -e IMAGE_PRESET_DOWNLOAD=SDXL_BASE_V1 zeroclue/comfyui:base-torch2.8.0-cu126

# Music and speech generation (⚠️ Experimental)
docker run -e AUDIO_PRESET_DOWNLOAD="MUSICGEN_MEDIUM,BARK_BASIC" zeroclue/comfyui:base-torch2.8.0-cu126
```

> 👉 To see detailed information about available presets and model specifications for each system, check the [Wiki documentation](https://github.com/ZeroClue/ComfyUI-Docker/wiki):
> - [Video Presets](https://github.com/ZeroClue/ComfyUI-Docker/wiki/PRESET_DOWNLOAD)
> - [Image Presets](https://github.com/ZeroClue/ComfyUI-Docker/wiki/IMAGE_PRESET_DOWNLOAD)
> - [Audio Presets](https://github.com/ZeroClue/ComfyUI-Docker/wiki/AUDIO_PRESET_DOWNLOAD)

---

## 📁 Logs

| App         | Log Path                                   |
| ----------- | ------------------------------------------ |
| ComfyUI     | `/workspace/ComfyUI/user/comfyui_3000.log` |
| code-server | `/workspace/logs/code-server.log`          |
| JupyterLab  | `/workspace/logs/jupyterlab.log`           |

---

## 🧩 Pre-installed Components

### System

* **OS**: Ubuntu 24.04 (22.02 for CUDA 12.4)
* **Python**: 3.13
* **Framework**: [ComfyUI](https://github.com/comfyanonymous/ComfyUI) + [ComfyUI Manager](https://github.com/Comfy-Org/ComfyUI-Manager) + [JupyterLab](https://jupyter.org/) + [code-server](https://github.com/coder/code-server)
* **Libraries**: PyTorch 2.8.0, CUDA (12.4–12.8), Triton, [hf\_hub](https://huggingface.co/docs/huggingface_hub), [nvtop](https://github.com/Syllo/nvtop)

#### Custom Nodes (only in **base** image)

* ComfyUI-KJNodes
* ComfyUI-WanVideoWrapper
* ComfyUI-GGUF
* ComfyUI-Easy-Use
* ComfyUI-Frame-Interpolation
* ComfyUI-mxToolkit
* ComfyUI-MultiGPU
* ComfyUI_TensorRT
* ComfyUI_UltimateSDUpscale
* comfyui-prompt-reader-node
* ComfyUI_essentials
* ComfyUI-Impact-Pack
* ComfyUI-Impact-Subpack
* efficiency-nodes-comfyui
* ComfyUI-Custom-Scripts
* ComfyUI_JPS-Nodes
* cg-use-everywhere
* ComfyUI-Crystools
* rgthree-comfy
* ComfyUI-Image-Saver
* comfy-ex-tagcomplete
* ComfyUI-VideoHelperSuite
* ComfyUI-wanBlockswap

> 👉 More details in the [Wiki](https://github.com/ZeroClue/ComfyUI-Docker/wiki/Custom-Nodes).
