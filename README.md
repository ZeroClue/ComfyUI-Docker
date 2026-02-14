[![Build and Push ZeroClue Docker Images (Optimized)](https://github.com/ZeroClue/ComfyUI-Docker/actions/workflows/build.yml/badge.svg)](https://github.com/ZeroClue/ComfyUI-Docker/actions/workflows/build.yml)

# ZeroClue ComfyUI-Docker

> 💬 Feedback & Issues → [GitHub Issues](https://github.com/ZeroClue/ComfyUI-Docker/issues)

> 🚀 This Docker image is maintained by ZeroClue and designed for both cloud deployment and local use.

> 💰 If you're feeling generous and this has value to you, consider donating. 

> 🤍 Sign-up at runpod using my referrer link and you can get between $5 and $500 in your account. [Runpod](https://runpod.io?ref=lnnwdl3q)

> 🌟 **Original Project**: This is a customised fork of the excellent [somb1/ComfyUI-Docker](https://github.com/somb1/ComfyUI-Docker) project. All credit goes to the original maintainers for creating this powerful ComfyUI distribution.

## 🔌 Exposed Ports

| Port | Type | Service               |
| ---- | ---- | --------------------- |
| 22   | TCP  | SSH                   |
| 3000 | HTTP | ComfyUI               |
| 8080 | HTTP | code-server           |
| 8888 | HTTP | JupyterLab            |
| 9000 | HTTP | Preset Manager Web UI |

---

## 🏷️ Tag Format

```text
zeroclue/comfyui:(A)-torch2.8.0-(B)
```

* **(A)**: `base`, `slim`, or `minimal`
  * `base`: ComfyUI + Manager + custom nodes + code-server (**~8-12GB**)
  * `slim`: ComfyUI + Manager, optimized for serving (**~4-5GB**)
  * `minimal`: ComfyUI + Manager + custom nodes, no dev tools (**~6-7GB**)
* **(B)**: CUDA version → `cu126`, `cu128` (new variants), `cu124`, `cu129`, `cu130`

---

## 🧱 Image Variants

### Development & Full-Featured Variants
| Image Name                            | Custom Nodes | Code Server | JupyterLab | Size | CUDA | Build Status |
| ------------------------------------- | ------------ | ----------- | ---------- | ---- | ---- | ------------ |
| `zeroclue/comfyui:base-torch2.8.0-cu126` | ✅ Yes        | ✅ Yes      | ✅ Yes     | ~8-12GB | 12.6 | ✅ Auto-built |
| `zeroclue/comfyui:base-torch2.8.0-cu128` | ✅ Yes        | ✅ Yes      | ✅ Yes     | ~8-12GB | 12.8 | 🔧 Manual only |

> ⚠️ **Important**: `base-torch2.8.0-cu128` requires manual build due to disk space constraints. See [Manual Build Guide](#-manual-build-for-large-variants) below.

### 🆕 Production Optimized Variants
| Image Name                                    | Custom Nodes | Code Server | JupyterLab | Size | CUDA | Use Case |
| --------------------------------------------- | ------------ | ----------- | ---------- | ---- | ---- | -------- |
| `zeroclue/comfyui:slim-torch2.8.0-cu126` | ❌ No         | ❌ No       | ❌ No      | ~4-5GB | 12.6 | Production serving |
| `zeroclue/comfyui:slim-torch2.8.0-cu128` | ❌ No         | ❌ No       | ❌ No      | ~4-5GB | 12.8 | Production serving |

### 🎯 RunPod Optimized Variants (Minimal)
| Image Name                                    | Custom Nodes | Code Server | JupyterLab | Size | CUDA | Use Case |
| --------------------------------------------- | ------------ | ----------- | ---------- | ---- | ---- | -------- |
| `zeroclue/comfyui:minimal-torch2.8.0-cu126` | ✅ Yes        | ❌ No       | ❌ No      | ~6-7GB | 12.6 | RunPod with custom nodes |
| `zeroclue/comfyui:minimal-torch2.8.0-cu128` | ✅ Yes        | ❌ No       | ❌ No      | ~6-7GB | 12.8 | RunPod with custom nodes |

### 🎨 Extended Variants (with Extra Nodes)
| Image Name | Extra Nodes | Size | CUDA | Use Case |
|------------|-------------|------|------|----------|
| `zeroclue/comfyui:base-extra-torch2.8.0-cu126` | ✅ Yes | ~10-14GB | 12.6 | Full-featured with all nodes |
| `zeroclue/comfyui:base-extra-torch2.8.0-cu128` | ✅ Yes | ~10-14GB | 12.8 | Full-featured with all nodes |

> 📦 **Extra Nodes**: LayerStyle (compositing), IC-Light (relighting), SAM3 (segmentation), RMBG (background removal)

> 👉 To switch: **Edit Pod/Template** → set `Container Image`.

### 🚀 Variant Selection Guide

- **For Development**: Use `base` variant with full tooling and 27 custom nodes
- **For Full Features**: Use `base-extra` variants with all 31 nodes (27 core + 4 extra)
- **For Production**: Use `slim` variants (50% smaller, faster startup)
- **For RunPod**: Use `minimal` variants (custom nodes without dev tools, optimal size)
- **All variants** support the same preset systems and environment variables

### 🔄 Migration Guide

Switching between variants is easy and preserves all your data:

#### From Base to Production
```bash
# 1. Stop current container
docker stop my_comfyui

# 2. Start with slim variant (same volume)
docker run --gpus all \
  -v my_workspace:/workspace \
  -e PRESET_DOWNLOAD="WAN_22_5B_TIV2" \
  -e IMAGE_PRESET_DOWNLOAD="SDXL_BASE_V1" \
  zeroclue/comfyui:slim-torch2.8.0-cu126
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
| `ENABLE_JUPYTERLAB`     | Enable/disable JupyterLab notebook interface (`True`/`False`)             | `True`    |
| `ENABLE_CODE_SERVER`    | Enable/disable code-server (VS Code web IDE) (`True`/`False`)             | `True`    |
| `TIME_ZONE`             | [Timezone](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) (e.g., `Asia/Seoul`)   | `Etc/UTC` |
| `COMFYUI_EXTRA_ARGS`    | Extra ComfyUI options (e.g. `--fast`)                        | (unset)   |
| `INSTALL_SAGEATTENTION` | Install [SageAttention2](https://github.com/thu-ml/SageAttention) on start (`True`/`False`) | `False`    |
| `INSTALL_EXTRA_NODES`   | Install optional extra custom nodes at runtime (`True`/`False`). Includes: LayerStyle, IC-Light, SAM3, RMBG | `False` |
| `FORCE_SYNC_ALL`        | Force full resync of venv and ComfyUI on startup (`True`/`False`) | `False`    |
| `ENABLE_PRESET_MANAGER` | Enable/disable preset manager web interface (`True`/`False`) | `True`     |
| `PRESET_DOWNLOAD`       | Download video generation model presets at startup (comma-separated list). **See below**. | (unset)   |
| `IMAGE_PRESET_DOWNLOAD` | Download image generation model presets at startup (comma-separated list). **See below**. | (unset)   |
| `AUDIO_PRESET_DOWNLOAD` | Download audio generation model presets at startup (comma-separated list). ⚠️ **Experimental** - **See below**. | (unset)   |

> 👉 To set: **Edit Pod/Template** → **Add Environment Variable** (Key/Value).

> ⚠️ SageAttention2 requires **Ampere+ GPUs** and ~5 minutes to install.

---

## 🌐 Preset Manager Web Interface

> **Web-based preset management system** - Browse, install, and manage ComfyUI model presets through an intuitive web interface.

### Quick Access

- **URL**: `http://your-pod-url:9000`
- **Authentication**: Use `ACCESS_PASSWORD` environment variable (if set)
- **Features**: Real-time progress tracking, storage analytics, integrated documentation

### Key Capabilities

- **🎛️ Visual Dashboard**: Storage overview and installation statistics
- **📂 Preset Browser**: Browse 52+ presets by category (Video/Image/Audio)
- **📖 Documentation Integration**: View full preset READMEs inline
- **⬇️ One-Click Installation**: Download presets with progress tracking
- **🗂️ Storage Management**: Monitor disk usage and cleanup unused models
- **📱 Responsive Design**: Works on desktop and mobile devices

### Usage Examples

```bash
# Enable preset manager (default - enabled)
docker run -e ACCESS_PASSWORD=mypassword zeroclue/comfyui:base-torch2.8.0-cu126

# Disable preset manager to save resources
docker run -e ENABLE_PRESET_MANAGER=False zeroclue/comfyui:base-torch2.8.0-cu126
```

> 👉 **Complete Guide**: See [PRESET_MANAGER.md](PRESET_MANAGER.md) for detailed documentation, screenshots, and advanced features.

---

## 🔧 Triple Preset System

> This Docker container features a **triple preset system** that supports automatic downloading of models for video, image, and audio generation. Each preset system is independent and can be used alone or combined with others for complete multimedia generation.

> **🔄 Runtime Updates**: Presets are automatically updated at container startup from the latest GitHub configuration, so Docker images always have the most current preset definitions without requiring rebuilds.

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

| App            | Log Path                                      |
| -------------- | --------------------------------------------- |
| ComfyUI        | `/workspace/ComfyUI/user/comfyui_3000.log`    |
| code-server    | `/workspace/logs/code-server.log`             |
| JupyterLab     | `/workspace/logs/jupyterlab.log`              |
| Preset Manager | `/workspace/logs/preset_manager.log`          |

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

---

## 🔧 Manual Build for Large Variants

### Why Manual Build Only?

The `base-torch2.8.0-cu128` variant requires **35GB of disk space** during build, which exceeds GitHub Actions' standard runner limits. To maintain reliable builds (100% success rate), this variant is built manually on demand.

### 🚀 Quick Manual Build (GitHub Actions)

1. **Visit Actions**: https://github.com/ZeroClue/ComfyUI-Docker/actions
2. **Click "Build and Push ZeroClue Docker Images"**
3. **Click "Run workflow"**
4. **Set Parameters**:
   ```
   targets: base
   cuda_versions: 12-8
   ```
5. **Click "Run workflow"** → Build completes in ~30 minutes

### 📦 Alternative: Use Available Variants

For most use cases, these alternatives provide the same functionality:

#### **Need CUDA 12.8?**
```bash
# Use base-12-8 for full development environment
docker run --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu128
# Custom nodes are pre-installed in base variants
```

#### **Need Full Installation?**
```bash
# Use base-12-6 (same features, slightly older CUDA)
docker run --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

#### **Need Production Ready?**
```bash
# Use slim-12-8 (optimized for serving)
docker run --gpus all -p 3000:3000 \
  zeroclue/comfyui:slim-torch2.8.0-cu128
```

### 📋 Auto-Built Variants (100% Success Rate)

✅ **Reliably built automatically:**
- `base-torch2.8.0-cu126/128/129/130` - Full installation with CUDA 12.6-13.0
- `slim-torch2.8.0-cu126/128` - Optimized for serving
- `minimal-torch2.8.0-cu126/128` - RunPod optimized with custom nodes

### 📖 Detailed Instructions

For comprehensive manual build instructions, local building options, and troubleshooting, see: **[Manual Build Guide](MANUAL_BUILD_GUIDE.md)**

---

## 📊 Build Status

| Variant | Status | Success Rate |
|---------|--------|--------------|
| **Auto-built variants (9 total)** | ✅ Working | 100% |
| **Manual variants** | 🔧 Available on demand | N/A |

**Last Updated**: Workflow optimized for reliable builds while maintaining full functionality.
