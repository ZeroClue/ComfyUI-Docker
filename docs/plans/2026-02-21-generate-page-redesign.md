# Generate Page Redesign - Design Document

**Date:** 2026-02-21
**Status:** Approved
**Author:** Design session with Claude

## Overview

Redesign the Generate page as an **All-in-One Integration** that combines workflow-centric generation, AI-powered prompt enhancement, and real-time progress tracking.

## Core Philosophy

The Generate page is the **consumer interface** for workflows. ComfyUI (port 3000) remains the **creator interface** for building/editing workflows.

## Design Decisions

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| Selection Approach | Workflow-First + Intent-Based | Power users get control, beginners get shortcuts |
| Real-time Updates | Hybrid (WebSocket + REST polling) | Responsive for active gen, efficient for background |
| Prompt Enhancement | Local LLM opt-in via Settings | Keeps image slim, user choice, persistent storage |
| Workflow Preview | Card with metadata | Lightweight, informative, no duplication of ComfyUI |
| Intent Matching | Pattern matching | Fast, predictable, no AI needed |

## User Flow

```
Intent Bar (optional) -> Workflow Browser -> Configure -> Generate -> View Results
         |                    |
    Pattern Match      Cards with metadata
    to suggest         showing compatibility
```

## UI Layout

### Three-Column Layout (Responsive)

```
+-----------------------------------------------------------------+
|  Quick Intent Bar (collapsible)                                  |
|  "I want to..." [video from text] [image to video] [upscale]    |
+----------------------------+------------------------------------+
|                            |                                     |
|   WORKFLOW BROWSER         |    GENERATION PANEL                 |
|   (Left, ~40%)             |    (Right, ~60%)                    |
|                            |                                     |
|   [Filter] [Search]        |    [Selected Workflow Card]         |
|                            |    [Prompt Input]                   |
|   [Workflow Cards Grid]    |    [Advanced Settings]              |
|                            |    [Generate Button]                |
|                            |                                     |
+----------------------------+------------------------------------+
|  OUTPUT & QUEUE (Bottom Panel, collapsible)                      |
|  [Current Generation] [Queue] [Recent Generations]               |
+-----------------------------------------------------------------+
```

## Workflow Card Design

```
+-------------------------------------+
|  [Icon] WAN 2.2 T2V Basic           |  <- Name
|  ---------------------------------  |
|  Text-to-video generation with      |  <- Description
|  motion and camera controls         |
|                                     |
|  Input: [Text]  Output: [Video]     |  <- I/O Types
|                                     |
|  [15.5GB] [~2min] [Ready]           |  <- Size, Time, Status
|                                     |
|  [Details]  [Generate ->]           |  <- Actions
+-------------------------------------+
```

### Card Metadata

| Field | Source | Display |
|-------|--------|---------|
| Name | Workflow `_meta.name` or filename | Title |
| Description | Workflow `_meta.description` | Subtitle |
| Category | Folder structure or `_meta.category` | Filter |
| Input Type | Scan workflow nodes | Icon |
| Output Type | Scan workflow nodes | Icon |
| Required Models | Template scanner | Size + status |
| Estimated Time | Preset `requirements.vram_gb` | "~2min" |
| Status | Check model availability | Ready/Missing/Update |

### Status Indicators

- **Ready** - All models installed
- **Missing** - Some models not installed (shows count)
- **Update** - Newer model version available

## Dashboard & Sidebar Integration

### Sidebar Updates

- Generate nav item shows queue count badge when > 0
- System status mini shows active generation

### Cross-Page Navigation

- Models page: [Generate] button on installed presets -> auto-select workflow
- Workflows page: [Generate] button -> select workflow on Generate page
- Settings page: Link to "Open ComfyUI" for workflow editing

### Shared State

- Queue status synced via WebSocket across all pages
- Generation progress shows in sidebar when active
- Toast notifications for generation events

## Real-Time Architecture (Hybrid)

### WebSocket Events (`/ws/generate`)

| Event | Direction | Payload |
|-------|-----------|---------|
| `generation_started` | Server -> Client | `{ prompt_id, workflow_name }` |
| `generation_progress` | Server -> Client | `{ prompt_id, progress, node_name, eta }` |
| `generation_complete` | Server -> Client | `{ prompt_id, outputs: [...] }` |
| `generation_error` | Server -> Client | `{ prompt_id, error }` |
| `queue_updated` | Server -> Client | `{ running: [], pending: [] }` |

### REST Polling (Fallback)

- `GET /api/workflows/queue/status` - Every 10s when no active generation
- `GET /api/workflows/history` - On page load, then every 30s

### Progress Display

```
+-------------------------------------+
|  Generating...                      |
|  ---------------------------------  |
|  [============        ] 67%         |
|                                     |
|  Current: KSampler (step 15/30)    |
|  ETA: ~45 seconds                   |
|                                     |
|  [Pause]  [Cancel]                  |
+-------------------------------------+
```

## Local LLM Prompt Enhancement

### Model Options

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| **Phi-3 Mini** | ~2GB | Fast | Good | Quick enhancements, low VRAM |
| **Qwen 2.5 1.5B** | ~1.5GB | Fastest | Good | Fastest, smallest footprint |
| **Llama 3.2 3B** | ~3GB | Medium | Better | Detailed prompts, nuanced styles |

### Storage

- Location: `/workspace/models/llm/{model-name}/`
- Format: Quantized GGUF
- Survives container updates (network volume)

### Enhancement Styles

| Style | Adds |
|-------|------|
| **Detailed** | Quality tags, lighting, composition |
| **Cinematic** | Film terms, camera angles, mood |
| **Artistic** | Art styles, techniques, references |
| **Minimal** | Light cleanup, grammar fix only |

### Backend

- Lazy load on first request
- Unload after 5min idle
- ~500ms inference time
- Uses llama-cpp-python

## API Endpoints

### New Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `GET /api/workflows/synced` | GET | List workflows with metadata |
| `GET /api/workflows/{id}/compatibility` | GET | Check model requirements |
| `POST /api/generate/intent` | POST | Pattern-match intent to workflows |
| `POST /api/generate/start` | POST | Start generation |
| `POST /api/generate/{id}/pause` | POST | Pause generation |
| `POST /api/generate/{id}/cancel` | POST | Cancel generation |
| `GET /api/llm/status` | GET | LLM model status |
| `POST /api/llm/download` | POST | Download LLM model |
| `POST /api/llm/enhance` | POST | Enhance prompt |
| `WS /ws/generate` | WS | Real-time progress |

## Backend Components

| Component | Purpose |
|-----------|---------|
| `workflow_scanner.py` | Scan workflows, extract metadata |
| `intent_matcher.py` | Pattern-match intent to workflows |
| `llm_service.py` | Manage LLM loading/inference |
| `generation_manager.py` | Track generations, broadcast progress |

## Frontend Components

| Component | Purpose |
|-----------|---------|
| `workflow-browser.js` | Workflow grid with Alpine.js |
| `intent-bar.js` | Quick intent input |
| `generation-progress.js` | Real-time progress display |
| `queue-panel.js` | Queue management UI |

## Files to Modify/Create

### Backend
- `dashboard/api/generate.py` (new)
- `dashboard/api/llm.py` (new)
- `dashboard/core/workflow_scanner.py` (new)
- `dashboard/core/intent_matcher.py` (new)
- `dashboard/core/llm_service.py` (new)
- `dashboard/core/generation_manager.py` (new)
- `dashboard/main.py` (modify - add routes, WebSocket)

### Frontend
- `dashboard/templates/generate.html` (rewrite)
- `dashboard/templates/settings.html` (modify - add LLM settings)
- `dashboard/templates/components/intent_bar.html` (new)
- `dashboard/templates/components/workflow_card.html` (new)
- `dashboard/templates/components/generation_progress.html` (new)
- `dashboard/static/js/workflow-browser.js` (new)

### Database
- Add `llm_model` to settings table
- Add `llm_enabled` to settings table

## Success Criteria

1. User can browse workflows with rich metadata
2. User can quick-start via intent bar
3. Real-time progress shows during generation
4. Queue syncs with actual ComfyUI queue
5. Prompt enhancement works when LLM enabled
6. All features integrate with existing dashboard
