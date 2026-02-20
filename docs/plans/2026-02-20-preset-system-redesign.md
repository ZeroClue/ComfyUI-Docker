# Preset System Redesign - Design Document

**Date**: 2026-02-20
**Status**: Approved
**Scope**: Reusable System + Community Hub

## Overview

This document describes the redesigned preset system that addresses:
1. **User Experience** - Discovery, installation, management, contextual help
2. **Accuracy** - Version drift, model changes, template updates
3. **Community** - Contribution workflow, sharing, collaboration

## Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────────┐
│                 PRESET MANAGEMENT BOT                            │
│         (Runs once - GitHub Actions scheduled workflow)          │
├─────────────────────────────────────────────────────────────────┤
│  Scheduled Jobs (Daily):                                        │
│  ├── HF Version Scanner: Check all tracked models for updates   │
│  ├── URL Health Check: Verify all URLs are accessible           │
│  ├── Checksum Generator: Download and compute SHA256            │
│  └── Auto-Updater: Create PRs for detected updates              │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GITHUB REGISTRY                               │
│              (zeroclue/comfyui-presets)                          │
│                    (Single Source of Truth)                      │
├─────────────────────────────────────────────────────────────────┤
│  presets/                                                        │
│  ├── wan-2.2.5-t2v/preset.yaml                                  │
│  ├── flux-dev/preset.yaml                                       │
│  └── ...                                                         │
│  registry.json          # Pre-computed metadata                 │
└─────────────────────────────────────────────────────────────────┘
          │
          │ HTTP GET (read-only, cached)
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    COMFYUI PODS (Many)                           │
├─────────────────────────────────────────────────────────────────┤
│  Dashboard API:                                                  │
│  ├── GET /api/registry/sync     # Pull latest registry.json     │
│  ├── GET /api/presets/          # List presets from cache       │
│  └── POST /api/presets/install  # Install with checksum verify  │
│                                                                  │
│  Background Jobs:                                                │
│  └── Periodic sync (hourly) - just pulls registry.json          │
│                                                                  │
│  On-Demand Only:                                                 │
│  └── Checksum verification at download time                     │
└─────────────────────────────────────────────────────────────────┘
```

### Key Architectural Decisions

1. **Separate Repository**: `zeroclue/comfyui-presets` for reusability
2. **Centralized Management**: Single bot handles all validation/versioning
3. **Distributed Consumption**: Pods pull read-only registry (no duplicate work)
4. **Version Pinning**: HuggingFace commit SHA for immutable references
5. **Three-Layer Validation**: CI (schema) + Bot (versions) + Pod (checksums)

## Preset Data Model

### File Structure

```
zeroclue/comfyui-presets/
├── presets/
│   ├── video/
│   │   ├── wan-2.2.5-t2v/
│   │   │   ├── preset.yaml
│   │   │   └── preview.jpg (optional)
│   │   └── ltx-video/
│   ├── image/
│   │   └── flux-dev/
│   └── audio/
│       └── musicgen/
├── registry.json
├── schema.yaml
└── scripts/
    ├── scan_versions.py
    ├── verify_urls.py
    └── generate_registry.py
```

### Preset Schema (preset.yaml)

```yaml
# Metadata
id: wan-2.2.5-t2v
version: "1.0.0"                    # Preset schema version
created: 2026-02-20T00:00:00Z
updated: 2026-02-20T00:00:00Z

# Classification
name: "WAN 2.2.5 Text-to-Video"
category: Video Generation
type: video
tags: [t2v, video, wan, text-to-video]
use_case: "High-quality text-to-video generation"

# Requirements
requirements:
  vram_gb: 24                       # Minimum VRAM
  disk_gb: 32.5                     # Total disk space needed
  recommended_gpu: ["RTX 4090", "A100", "H100"]
  dependencies: []                  # Other presets this depends on

# Model Files with Version Pinning
files:
  - path: checkpoints/wan2.5_t2v_14B.safetensors
    url: https://huggingface.co/Wan-AI/Wan2.5-T2V-14B/resolve/main/wan2.5_t2v_14B.safetensors
    size: 29.5GB
    source:
      type: huggingface
      repo: Wan-AI/Wan2.5-T2V-14B
      revision: abc123def456...      # Git commit SHA (immutable)
    checksum:
      algorithm: sha256
      value: "abc123..."
    verified_at: 2026-02-20T00:00:00Z

# Model Version Tracking
model_version:
  upstream_version: "2.2.5"          # Version reported by model author
  tracked_branch: main               # Branch we track for updates
  last_checked: 2026-02-20T00:00:00Z
  update_available: false

# Description
description: |
  WAN 2.2.5 is a 14B parameter text-to-video model...

# Template Compatibility (pre-computed)
compatible_workflows:
  - id: wan-t2v-basic
    name: "Basic T2V"
    missing_requirements: []
```

### Registry Metadata (registry.json)

```json
{
  "version": "1.0.0",
  "last_scan": "2026-02-20T00:00:00Z",
  "presets": {
    "wan-2.2.5-t2v": {
      "name": "WAN 2.2.5 Text-to-Video",
      "category": "Video Generation",
      "download_size": "32.5GB",
      "vram_gb": 24,
      "update_available": false,
      "installed": false
    }
  },
  "alerts": [
    {
      "type": "model_updated",
      "preset_id": "flux-dev",
      "message": "New version available",
      "severity": "info"
    }
  ]
}
```

## Validation Pipeline

### Layer 1: CI Validation (On PR/Commit)

Runs in GitHub Actions on every pull request:

- Schema compliance (JSON Schema)
- Required fields present
- URL format validation
- Size format validation
- No duplicate preset IDs

### Layer 2: Background Validation (Scheduled)

Runs daily via scheduled GitHub Actions:

- HuggingFace version check (compare revision to main)
- URL accessibility test (HEAD request)
- Model deprecation detection
- Generate "update available" flags

### Layer 3: On-Demand Validation (At Download)

Runs in each pod at install time:

- Checksum verification (SHA256)
- File size match
- Re-verify URL before download
- HF token validation for gated models

## User Experience Enhancements

### Discovery

- Search by name, tags, description
- Filter by category, status, VRAM requirements
- Sort by popularity, name, size, recently added
- "Update Available" badge for outdated presets

### Contextual Help

- VRAM requirements display with GPU compatibility check
- Disk space needed before install
- Dependent presets shown ("Requires: clip_vision_encoder")
- Recommendation engine based on hardware

### Management

- Storage visualization by category
- Cleanup suggestions (unused models, orphaned files)
- Version tracking with update notifications
- One-click uninstall

### Installation

- Pre-flight checks (VRAM, disk, HF token)
- Better error messages (specific HTTP codes)
- Automatic retry with backoff
- Progress per file (existing, keep)

## Community Contribution

### Phase 1: GitHub-Based

1. Fork `zeroclue/comfyui-presets`
2. Add `preset.yaml` in `presets/{category}/{preset-id}/`
3. Run local validation: `python scripts/validate.py`
4. Submit PR
5. CI validates schema + URLs
6. Maintainer reviews and merges

### Phase 2: Issue Template

For non-developers:

1. GitHub Issues → New Preset Request
2. Fill in form (name, URLs, description)
3. Maintainer creates preset from template
4. Linked to original issue for attribution

### Phase 3: Web UI (Future)

- Dashboard form to submit presets
- Auto-generates preset.yaml
- Creates PR on submit

## Implementation Roadmap

### Phase 1: Core Infrastructure (Week 1-2)

- [ ] Create `zeroclue/comfyui-presets` repository
- [ ] Migrate existing 56 presets to new structure
- [ ] Add JSON Schema validation
- [ ] Set up CI validation workflow
- [ ] Generate initial registry.json

### Phase 2: Management Bot (Week 3-4)

- [ ] Build HF version scanner script
- [ ] Build URL health checker
- [ ] Implement scheduled GitHub Actions
- [ ] Auto-generate registry.json
- [ ] Add checksum computation

### Phase 3: Dashboard Integration (Week 5-6)

- [ ] Add `/api/registry/sync` endpoint
- [ ] Update preset loader for new format
- [ ] Add VRAM/requirements display
- [ ] Implement recommendation engine
- [ ] Add storage management UI

### Phase 4: Community Features (Week 7-8)

- [ ] Create issue templates for preset requests
- [ ] Add contribution documentation
- [ ] Build preset submission validator
- [ ] Set up moderation workflow

### Phase 5: Polish & Testing (Week 9-10)

- [ ] Migration testing from old format
- [ ] Edge case handling
- [ ] Documentation
- [ ] Community testing

## Migration Strategy

### Backward Compatibility

The system will support both old and new formats during transition:

1. Read old `config/presets.yaml` if exists
2. Convert to new format in memory
3. Prefer new registry when available
4. Log deprecation warning

**Goal**: Zero breaking changes for existing users.

### Migration Script

```bash
# One-time migration tool
python scripts/migrate_presets.py --source config/presets.yaml --output presets/
```

## Success Criteria

1. **Accuracy**: 100% of presets have valid URLs and correct checksums
2. **Freshness**: Model updates detected within 24 hours
3. **UX**: Users can find and install presets in < 30 seconds
4. **Community**: External contributors can submit presets via PR
5. **Reliability**: Zero breaking changes during migration

## Open Questions

1. Should we support Civitai URLs in addition to HuggingFace?
2. How to handle models that require license acceptance?
3. Should presets include workflow templates?
4. How to handle model deprecation (model removed by author)?

## References

- Existing preset system: `config/presets.yaml`
- Current dashboard API: `dashboard/api/presets.py`
- Download manager: `dashboard/core/downloader.py`
