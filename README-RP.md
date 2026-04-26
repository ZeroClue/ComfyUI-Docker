# ZeroClue ComfyUI-Docker

[![Docker Pulls](https://img.shields.io/docker/pulls/zeroclue/comfyui)](https://hub.docker.com/r/zeroclue/comfyui)

Full-featured ComfyUI platform with a Unified Dashboard for managing models, presets, and system resources. Built on CUDA 13.0.3 + PyTorch 2.11.0 with 25+ custom nodes pre-installed.

**Image**: `zeroclue/comfyui:latest`

## Ports

| Port | Service |
|------|---------|
| `3000/http` | ComfyUI |
| `8082/http` | Unified Dashboard |
| `8080/http` | code-server (VS Code) |
| `8888/http` | JupyterLab |
| `22/tcp` | SSH |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ACCESS_PASSWORD` | Password for dashboard, code-server, JupyterLab | `admin` |
| `HF_TOKEN` | HuggingFace token for gated/faster model downloads | (unset) |
| `ENABLE_UNIFIED_DASHBOARD` | Enable dashboard on port 8082 | `true` |
| `ENABLE_CODE_SERVER` | Enable VS Code server | `true` |
| `ENABLE_JUPYTERLAB` | Enable JupyterLab | `true` |
| `TIME_ZONE` | Container timezone (e.g. `Europe/Berlin`) | `Etc/UTC` |
| `COMFYUI_EXTRA_ARGS` | Extra ComfyUI options (e.g. `--fast`) | (unset) |
| `PRESET_DOWNLOAD` | Video models to download at startup (comma-separated) | (unset) |
| `IMAGE_PRESET_DOWNLOAD` | Image models to download at startup | (unset) |
| `AUDIO_PRESET_DOWNLOAD` | Audio models to download at startup | (unset) |

All variables are optional. The container works out of the box with no configuration.

## Quick Start

1. Deploy with GPU (RTX 3090 or newer recommended)
2. Attach a network volume (100GB+) to `/workspace` for model persistence
3. Open port `8082` for the Dashboard or `3000` for ComfyUI directly
4. Browse and download presets from the Dashboard at your leisure

## Dashboard

The Unified Dashboard (port 8082) provides:

- **Preset Management**: Browse 56+ presets with GPU compatibility indicators
- **One-Click Downloads**: Download models with progress tracking
- **System Monitoring**: Real-time CPU, memory, disk, and GPU metrics
- **Storage Management**: Visual disk usage and cleanup tools
- **Update Tracking**: Badges when new model versions are available

Default login: `admin` / `admin` (set `ACCESS_PASSWORD` to change).

## Preset System

Three independent categories of model presets. Set the corresponding env var for automatic downloads at startup, or install individually via the Dashboard.

**Video** (`PRESET_DOWNLOAD`): WAN 2.1, LTX, HunyuanVideo, Cosmos
**Image** (`IMAGE_PRESET_DOWNLOAD`): SDXL, FLUX, Qwen Image, Realistic Vision
**Audio** (`AUDIO_PRESET_DOWNLOAD`): MusicGen, Bark, TTS (experimental)

## Included

- **OS**: Ubuntu 24.04 | **Python**: 3.13 | **PyTorch**: 2.11.0
- **CUDA**: 13.0.3 (Blackwell-native, backward-compatible)
- **Attention**: SageAttention 2.2.0 (CUDA 12.x) / ComfyUI-Attention-Optimizer (CUDA 13+)
- **Custom Nodes**: KJNodes, WanVideoWrapper, GGUF, Easy-Use, Impact-Pack, IPAdapter+, VideoHelperSuite, and 18 more

## Logs

| Service | Path |
|---------|------|
| ComfyUI | `/workspace/ComfyUI/user/comfyui_3000.log` |
| Dashboard | `/workspace/logs/unified_dashboard.log` |
| code-server | `/workspace/logs/code-server.log` |

## Support

- [GitHub Issues](https://github.com/ZeroClue/ComfyUI-Docker/issues)
- [Docker Hub](https://hub.docker.com/r/zeroclue/comfyui)
- [Wiki](https://github.com/ZeroClue/ComfyUI-Docker/wiki)

If you find this useful, consider [buying me a coffee](https://www.buymeacoffee.com/thezeroclue).
