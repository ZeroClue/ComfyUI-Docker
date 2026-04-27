# Changelog

All notable changes to ComfyUI-docker. Format follows [Keep a Changelog](https://keepachangelog.com/).

## [v1.4.1] - 2026-04-27

### Fixed
- Dashboard model scanner now includes `diffusion_models` and `model_patches` directories (Qwen, FLUX, SD3, Z-Image models were invisible in the Models page)

## [v1.4.0] - 2026-04-27

### Fixed
- Critical dashboard security and reliability fixes
- Pin starlette<1.0.0 to prevent Jinja2 template cache breakage
- Quote starlette version pin to prevent shell redirect in Dockerfile

## [v1.3.0] - 2026-04-26

### Added
- CUDA 13.0 build target (`base-13-0`) as primary CI matrix entry with `:latest` Docker tag
- PyTorch 2.11.0 for both CUDA 12.8 and 13.0 builds (cu128 and cu130 wheels)
- Parameterized Dockerfile `FROM` statements via `BASE_IMAGE` and `RUNTIME_BASE_IMAGE` ARGs
- `RUNTIME_BASE_IMAGE` args in `_cu128` and `_cu130` bake targets for correct runtime stage images

### Changed
- `:latest` Docker tag moves from `base-12-8` to `base-13-0` (Blackwell-native, backward-compatible)
- CI matrix builds sequentially (`max-parallel: 1`) — both 12.8 and 13.0 build every run
- `TORCH_VERSION` default: `2.8.0` → `2.11.0`
- `DEFAULT_CUDA` default: `cu128` → `cu130`
- Manual trigger default CUDA version: `12-8` → `13-0`

## [v1.2.0] - 2026-04-26

### Added
- Version-pinned Docker image tags — each build produces both a floating tag (`base-py3.13-cu128`) and a pinned tag (`base-py3.13-cu128-v1.2.0`) for rollback support
- `docker-bake.hcl` tag function now produces dual tags when `EXTRA_TAG` is set
- CI build workflow resolves latest git tag and passes it to bake

## [v1.1.0] - 2026-04-26

### Added
- Generate queue card connected to ComfyUI's real execution queue via 3-second REST polling
- Running items show spinner with real-time progress percentage
- Pending items show queue position number
- `POST /api/workflows/queue/delete/{prompt_id}` endpoint for removing pending items from ComfyUI queue
- `ComfyUIClient.delete_queue_item()` method for targeted queue deletion
- Cancel button distinguishes running (interrupt) vs pending (delete) items
- `workflowNameMap` for resolving prompt IDs to workflow names across the session

### Changed
- CLAUDE.md trimmed from 725 to ~570 lines, historical learnings extracted to `docs/LEARNINGS.md`

### Removed
- Mock `POST /{prompt_id}/pause` endpoint (ComfyUI does not support pause/resume)
- Dead batch queue code (`startQueueItem()`, local queue push logic)

## Pre-release History

### Workflow Preset Suggestions - 2026-02-23
- WorkflowScanner resolves model filenames to preset IDs using `model_index.json`
- User workflow cards show suggested presets with install buttons for missing models
- Sync endpoint downloads `model_index.json` alongside `registry.json`

### LLM Integration - 2026-02-22
- Optional prompt enhancement via local LLM models (Phi-3, Qwen, Llama)
- `POST /api/llm/enhance` endpoint with style presets (detailed, cinematic, artistic, minimal)
- Settings page configuration for LLM model and enable/disable

### Generate Page Redesign - 2026-02-21
- Workflow-first card-based UI with metadata and compatibility badges
- Intent-based entry with pattern-matched shortcuts
- Real-time progress via hybrid WebSocket + REST polling
- Disk space warning modal for low-storage scenarios

### Workflow Registry - 2026-02-20
- Bundle workflow library in container image at `/workspace/workflows/library/`
- WorkflowScanner extracts metadata, widget values, and model references
- Source filter tabs for library vs user workflows

### Preset Registry System - 2026-02-20
- Centralized preset management via separate `comfyui-presets` repository
- Dashboard syncs `registry.json` from GitHub raw URL
- Dual format support (old `presets.yaml` and new registry)

### Unified Dashboard - 2026-02-18
- FastAPI + htmx + Alpine.js dashboard on port 8082
- Home page with real-time stats, download queue, system resources
- Preset management with download queue and progress tracking
- Settings page with HF token validation
- Activity log with 30-day auto-cleanup

### Optimization Baseline - Pre-2026-02
- 4-stage multi-stage Docker build (builder-base → python-deps → comfyui-core → runtime)
- SageAttention 2.2.0 compiled from source with CUDA kernel support
- Matrix builds for CUDA 12.4–13.0 via `docker-bake.hcl`
- Preset Manager web UI on port 9000 (now superseded by Unified Dashboard)
