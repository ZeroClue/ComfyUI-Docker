# Unified Dashboard Preset System - Design Document

**Date**: 2026-02-18
**Status**: Approved
**Author**: Claude + User collaboration

## Overview

Design for a fully functional preset management system in the ComfyUI Unified Dashboard. The system enables users to browse, install, and manage AI model presets, then use them with ComfyUI templates for generation.

## Core Architecture

### Single Source of Truth

- **Location**: `config/presets.yaml` in GitHub repository
- **Build time**: Baked into Docker image
- **Runtime refresh**: Fetch latest from GitHub raw URL
  ```
  https://raw.githubusercontent.com/ZeroClue/ComfyUI-Docker/main/config/presets.yaml
  ```

### Data Flow

```
GitHub (presets.yaml)
    ↓ Build time
Docker Image
    ↓ Container start
Local presets.yaml
    ↓ User clicks Refresh
Latest from GitHub (smart refresh)
```

## User Flow

```
Models Page
    ↓ Browse presets (Installed/Available/Downloading badges)
Select preset → Click Install
    ↓ Background download (sequential queue)
Progress displayed in UI
    ↓ Download complete
Toast: "Installed! [Generate Now]"
    ↓ Click Generate Now
Generate Page (filtered templates)
    ↓ Select compatible template
Customize → Generate
```

## Key Features

### 1. Preset Browsing
- Grid view with status badges
- Filter by category (Video/Image/Audio)
- Filter by status (Installed/Available/Downloading)
- Search by name, tag, description
- Sort by name, size, recent, popular

### 2. Smart Refresh
- Updates preset metadata without interrupting active downloads
- Only overwrites preset definitions
- Preserves download queue state
- Future: Handle dangling models (cleanup feature)

### 3. Sequential Download Queue
- One preset downloads at a time
- User can queue multiple presets
- Visual queue display on Models page:
  ```
  📥 Downloading: WAN 2.1 14B
     ████████░░░░░░░░ 45% • 6.5GB/14GB

  📋 Queue (2):
     • FLUX Schnell (24 GB)
     • LTX Video (2.1 GB)
  ```

### 4. Auto-Retry + Manual
- 3 auto-retry attempts with exponential backoff
  - Attempt 1 fails → wait 5s → Attempt 2
  - Attempt 2 fails → wait 15s → Attempt 3
  - Attempt 3 fails → Mark "Failed"
- Manual "Retry" button for failed downloads

### 5. Template Compatibility
- Scan template JSON for model references
- Show all templates (don't hide)
- Visual warning for missing models:
  ```
  ⚠️ Image to Video
     Missing: clip_vision_adapter.safetensors
     [Install Missing]
  ```

### 6. Post-Install Toast
- Notification when preset installed
- "Generate Now" button navigates to Generate page
- Preset pre-selected in template filter

## Technical Implementation

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/presets` | GET | List all presets with install status |
| `/api/presets/refresh` | POST | Fetch latest presets.yaml from GitHub |
| `/api/presets/{id}/install` | POST | Queue preset for download |
| `/api/presets/{id}/pause` | POST | Pause active download |
| `/api/presets/{id}/cancel` | POST | Cancel download, keep partial |
| `/api/presets/{id}/retry` | POST | Retry failed download |
| `/api/presets/queue` | GET | Get current download queue status |
| `/api/templates` | GET | List ComfyUI templates with compatibility |
| `/api/templates/{id}/missing-models` | GET | Get missing models for template |

### WebSocket Events

| Event | Direction | Data |
|-------|-----------|------|
| `download_progress` | Server→Client | `{presetId, progress, speed, eta}` |
| `download_complete` | Server→Client | `{presetId, success}` |
| `download_failed` | Server→Client | `{presetId, error, retryCount}` |
| `queue_updated` | Server→Client | `{queue: [...]}` |

### Background Downloader Service

Single async process that:
- Maintains FIFO download queue
- Downloads one preset at a time
- Reports progress via WebSocket
- Handles retries with exponential backoff
- Persists state for pod restart recovery
- Supports pause/resume per preset

## Schema Considerations

### Current Schema (v1)

```yaml
presets:
  PRESET_ID:
    name: string
    category: string
    type: video|image|audio
    description: string
    download_size: string
    files:
      - path: string
        url: string
        size: string
    use_case: string
    tags: [string, ...]
```

### Future Additions (Not for v1)

```yaml
    checksum: sha256:...        # File verification
    thumbnail: url              # Preview image
    min_vram: 16GB              # Hardware requirements
    compatible_templates: [...] # Template IDs
    deprecated: false           # Soft delete flag
    version: 1.0.0              # For update tracking
```

**Decision**: Keep current schema for v1. Add fields incrementally as needed.

## Error Handling

### Download Errors
- Network timeout → Auto-retry
- 404 Not Found → Mark failed, log error
- Disk full → Mark failed, notify user
- Partial file → Resume if server supports, else restart

### Refresh Errors
- GitHub unreachable → Show warning, keep local copy
- Invalid YAML → Show error, keep local copy
- Schema mismatch → Attempt migration or show warning

## Security Considerations

- Validate URLs are from allowed domains (huggingface.co, civitai.com, etc.)
- Sanitize file paths to prevent directory traversal
- Rate limit refresh calls to prevent abuse

## Future Enhancements

1. **Storage Management**
   - Clean unused models
   - Disk usage visualization
   - Auto-cleanup of old downloads

2. **Advanced Features**
   - Parallel downloads (with limit)
   - Bandwidth throttling
   - Download scheduling

3. **Community Features**
   - Custom preset sharing
   - Preset ratings/reviews
   - Popular presets leaderboard

---

*Next step: Invoke writing-plans skill to create detailed implementation plan*
