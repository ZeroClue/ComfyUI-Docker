# Home Page Design - Real Data Integration

**Date:** 2026-02-19
**Status:** Approved
**Goal:** Replace all mockup data on home page with real API data

## Overview

The home page currently has several sections with hardcoded mockup data. This design replaces all mock data with real API connections, adds a missing download queue section, and creates a combined activity feed.

## Design Principles

- **Balanced Mix**: Status, actions, and recent content all visible
- **Real Data Only**: No hardcoded fallbacks that mask empty states
- **Progressive Enhancement**: Graceful degradation when APIs unavailable
- **Real-time Updates**: WebSocket integration for live progress

## Section Layout

```
┌─────────────────────────────────────────────────────────┐
│ Header: Welcome back + Quick Actions                    │
├─────────────────────────────────────────────────────────┤
│ Stats Grid (4 cards) - Already connected                │
├─────────────────────────────────────────────────────────┤
│ Download Queue (NEW) - Show when active                 │
├─────────────────────────────────────────────────────────┤
│ System Resources (4 bars) - Connect to real data        │
├─────────────────────────────────────────────────────────┤
│ Recent Models (3 cards) - Replace featured mock         │
├─────────────────────────────────────────────────────────┤
│ Activity Feed (list) - Combined generations + downloads │
└─────────────────────────────────────────────────────────┘
```

---

## Section 1: Page Header & Quick Actions

**Status:** No changes needed

Static navigation elements are already correct:
- Welcome header text
- 4 quick action buttons linking to other pages

---

## Section 2: Stats Grid

**Status:** Minimal fix needed

Already connected to `/api/dashboard/stats` via JavaScript. Only change:

**Fix:** Remove hardcoded default values

```javascript
// Before
stats: {
  totalGenerations: 1284,
  modelsInstalled: 12,
  storageUsed: '24.5 GB',
  activeWorkflows: 8
}

// After
stats: {
  totalGenerations: 0,
  modelsInstalled: 0,
  storageUsed: '0 GB',
  activeWorkflows: 0
}
```

**Data Source:** `GET /api/dashboard/stats`

---

## Section 3: Download Queue (NEW)

**Status:** New section to add

Show active and queued downloads prominently near the top.

### UI Layout

```
┌─────────────────────────────────────────────────────────┐
│ Download Queue (2 active)                      [View All]│
├─────────────────────────────────────────────────────────┤
│ WAN 2.1 14B                              67%    [Pause] │
│ ████████████████░░░░░░░░ 14.5 GB / 22 GB               │
│ Downloading checkpoint... ETA: 3m 24s                   │
├─────────────────────────────────────────────────────────┤
│ LTX Video                                        [Queued]│
│ Waiting for current download to complete                │
└─────────────────────────────────────────────────────────┘
```

### Data Source

`GET /api/presets/queue/status`

```json
{
  "current": {
    "preset_id": "WAN_2_1_14B",
    "progress": 67,
    "downloaded_bytes": 15500000000,
    "total_bytes": 22000000000,
    "speed": "45.2 MB/s",
    "eta": "3m 24s",
    "status": "downloading"
  },
  "queue": [
    {"preset_id": "LTX_VIDEO", "status": "queued"}
  ]
}
```

### Behavior

- **Hidden** when queue is empty (current=null, queue=[])
- **Visible** when downloads are active or queued
- WebSocket listener on `/ws/downloads` for real-time progress
- "Pause" button calls `POST /api/presets/{id}/pause`
- "View All" links to `/models` with queue filter

---

## Section 4: System Resources

**Status:** Connect to real data

Currently hardcoded mock values. Connect to existing API.

### Data Source

`GET /api/system/resources`

```json
{
  "cpu_percent": 45.2,
  "memory": {
    "total": 34359738368,
    "used": 19327352832,
    "available": 15032385536,
    "percent": 56.2
  },
  "disk": {
    "total": 107374182400,
    "used": 48318382080,
    "free": 59055800320,
    "percent": 45.0
  },
  "gpu": {
    "devices": [{
      "name": "NVIDIA RTX 2000 Ada",
      "memory_used": 8192,
      "memory_total": 16384,
      "utilization": 72
    }]
  }
}
```

### UI Layout

4 resource bars in a grid:

| Card | Metric | Status Thresholds |
|------|--------|-------------------|
| GPU Memory | used/total | <70% green, 70-90% yellow, >90% red |
| System RAM | used/total | <70% green, 70-90% yellow, >90% red |
| Disk Space | used/total | <80% green, 80-95% yellow, >95% red |
| GPU Util | utilization% | <60% green, 60-85% yellow, >85% red |

### Behavior

- Load on page init via Alpine.js
- Refresh button triggers htmx `hx-get="/api/system/resources"`
- Poll every 10 seconds via setInterval
- Hide GPU cards if `gpu.devices` is empty/null

---

## Section 5: Recent Models

**Status:** Replace Featured Models mock

### Data Source

`GET /api/presets/?limit=6`

Filter logic in frontend:
1. Filter to `installed: true` presets
2. Sort by most recently modified (file timestamp)
3. Take top 3
4. If <3 installed, fill with available presets

### UI Layout

```
┌─────────────────────────────────────────────────────────┐
│ Recent Models                                    [View All]│
├─────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │
│ │ ✓ Installed │ │ ✓ Installed │ │ ○ Available │        │
│ │ WAN 2.1 14B │ │ SDXL Base   │ │ FLUX.1      │        │
│ │ 14.5 GB • V │ │ 6.9 GB • I  │ │ 23 GB • I   │        │
│ │ [Generate]  │ │ [Generate]  │ │ [Install]   │        │
│ └─────────────┘ └─────────────┘ └─────────────┘        │
└─────────────────────────────────────────────────────────┘
```

### Card Actions

| Status | Primary Action | Secondary Action |
|--------|----------------|------------------|
| Installed | Generate → `/generate?model={id}` | Details → modal |
| Available | Install → `POST /api/presets/{id}/install` | Details → modal |

### Empty State

"No models installed yet" with button "Browse Models" → `/models`

---

## Section 6: Activity Feed (Combined)

**Status:** Replace Recent Activity mock with combined feed

### New API Endpoint

`GET /api/activity/recent?limit=5`

Combines generation history and download events.

```json
{
  "activities": [
    {
      "id": "gen_abc123",
      "type": "generation",
      "status": "completed",
      "title": "Image generation completed",
      "subtitle": "Txt2Img SDXL",
      "timestamp": "2026-02-19T15:30:00Z",
      "link": "/gallery?item=abc123"
    },
    {
      "id": "dl_wan14b",
      "type": "download",
      "status": "completed",
      "title": "Model download completed",
      "subtitle": "WAN 2.1 14B",
      "timestamp": "2026-02-19T15:25:00Z",
      "link": "/models?preset=WAN_2_1_14B"
    }
  ]
}
```

### Activity Types

| Type | Icon | Statuses |
|------|------|----------|
| generation | ✓ | completed, failed |
| download | ↓ | completed, failed, started |

### UI Layout

```
┌─────────────────────────────────────────────────────────┐
│ Recent Activity                              [Clear All]│
├─────────────────────────────────────────────────────────┤
│ ✓ Image generation completed                   [Complete]│
│   Txt2Img SDXL • 2 minutes ago                          │
├─────────────────────────────────────────────────────────┤
│ ↓ Model download completed                     [Success] │
│   WAN 2.1 14B • 5 minutes ago                           │
├─────────────────────────────────────────────────────────┤
│ ✕ Generation failed                              [Failed]│
│   Video WAN • Out of memory • 10 min ago                │
└─────────────────────────────────────────────────────────┘
```

### Behavior

- Load on page init
- WebSocket listener for new events
- "Clear All" calls `DELETE /api/activity/clear`
- Click row navigates to link
- Empty state: "No recent activity"

---

## Implementation Tasks

1. **Stats Grid** - Remove hardcoded defaults in JavaScript
2. **Download Queue** - Add new section with queue status display
3. **System Resources** - Connect Alpine.js to `/api/system/resources`
4. **Recent Models** - Replace featured section with API-driven cards
5. **Activity Feed** - Create `/api/activity/recent` endpoint
6. **Activity Endpoint** - Combine generation history + download events
7. **WebSocket Updates** - Wire up real-time updates for all sections

## File Changes

| File | Change |
|------|--------|
| `dashboard/templates/index.html` | Major rewrite - all sections |
| `dashboard/api/system.py` | No changes (API exists) |
| `dashboard/api/presets.py` | No changes (API exists) |
| `dashboard/api/activity.py` | New file - activity feed endpoint |
| `dashboard/api/__init__.py` | Add activity router |

## Out of Scope

- Recommendations engine for "suggested models"
- Activity persistence (DB) - in-memory only
- Notification system beyond current toast
