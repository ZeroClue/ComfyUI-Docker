# Home Page Real Data Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace all mockup data on home page with real API connections

**Architecture:** Frontend uses Alpine.js for state management, existing backend APIs provide data. New `/api/activity/recent` endpoint combines generation history + download events into unified feed.

**Tech Stack:** FastAPI, Alpine.js, htmx, existing presets/system APIs

---

## Task 1: Create Activity API Endpoint

**Files:**
- Create: `dashboard/api/activity.py`
- Modify: `dashboard/api/__init__.py`

**Step 1: Create activity.py with in-memory store**

```python
"""
Activity feed API endpoints
Combines generation history and download events into unified feed
"""

from typing import List, Dict, Optional
from datetime import datetime
from collections import deque
from pydantic import BaseModel

from fastapi import APIRouter

router = APIRouter()

# In-memory activity store (max 50 items)
activity_store: deque = deque(maxlen=50)


class ActivityItem(BaseModel):
    """Single activity item"""
    id: str
    type: str  # generation, download
    status: str  # completed, failed, started
    title: str
    subtitle: str
    timestamp: str
    link: str


class ActivityResponse(BaseModel):
    """Response for activity list"""
    activities: List[ActivityItem]


def add_activity(
    activity_type: str,
    status: str,
    title: str,
    subtitle: str,
    link: str = "#"
) -> ActivityItem:
    """Add a new activity to the store"""
    import uuid
    activity = ActivityItem(
        id=f"{activity_type}_{uuid.uuid4().hex[:8]}",
        type=activity_type,
        status=status,
        title=title,
        subtitle=subtitle,
        timestamp=datetime.utcnow().isoformat() + "Z",
        link=link
    )
    activity_store.appendleft(activity)
    return activity


def get_activities(limit: int = 10) -> List[ActivityItem]:
    """Get recent activities"""
    return list(activity_store)[:limit]


def clear_activities():
    """Clear all activities"""
    activity_store.clear()


@router.get("/recent", response_model=ActivityResponse)
async def get_recent_activity(limit: int = 10):
    """Get recent activity feed combining generations and downloads"""
    from .presets import download_manager

    activities = list(activity_store)

    # Add current download as activity if active
    queue_status = download_manager.get_queue_status()
    if queue_status.get("current"):
        current = queue_status["current"]
        dl_activity = ActivityItem(
            id=f"dl_{current.get('preset_id', 'unknown')}",
            type="download",
            status="started",
            title=f"Downloading {current.get('preset_id', 'Model')}",
            subtitle=f"{current.get('progress', 0)}% complete",
            timestamp=datetime.utcnow().isoformat() + "Z",
            link=f"/models?preset={current.get('preset_id', '')}"
        )
        # Insert at beginning if not already there
        if not activities or activities[0].id != dl_activity.id:
            activities.insert(0, dl_activity)

    return ActivityResponse(activities=activities[:limit])


@router.delete("/clear")
async def clear_activity_history():
    """Clear all activity history"""
    clear_activities()
    return {"status": "success", "message": "Activity history cleared"}
```

**Step 2: Register router in __init__.py**

Add to `dashboard/api/__init__.py`:

```python
from .activity import router as activity_router
api_router.include_router(activity_router, prefix="/activity", tags=["activity"])
```

**Step 3: Commit**

```bash
git add dashboard/api/activity.py dashboard/api/__init__.py
git commit -m "feat: add activity feed API endpoint

- Combines generation history and download events
- In-memory store with max 50 items
- /api/activity/recent and /api/activity/clear endpoints"
```

---

## Task 2: Add Download Complete Activity Hook

**Files:**
- Modify: `dashboard/core/downloader.py`

**Step 1: Import and call add_activity on download complete**

Find the download completion section in `download_file` method. Add activity recording:

```python
# In dashboard/core/downloader.py
# Add import at top:
from ..api.activity import add_activity

# In download_file method, after successful download:
add_activity(
    activity_type="download",
    status="completed",
    title=f"Model download completed",
    subtitle=preset_id,
    link=f"/models?preset={preset_id}"
)
```

**Step 2: Commit**

```bash
git add dashboard/core/downloader.py
git commit -m "feat: record download completion in activity feed"
```

---

## Task 3: Update Stats Grid - Remove Hardcoded Defaults

**Files:**
- Modify: `dashboard/templates/index.html` (lines 307-314)

**Step 1: Replace hardcoded stats with zeros**

Find the `homeDashboard()` function and change:

```javascript
// Before (line 309-314)
stats: {
    totalGenerations: 1284,
    modelsInstalled: 12,
    storageUsed: '24.5 GB',
    activeWorkflows: 8
},

// After
stats: {
    totalGenerations: 0,
    modelsInstalled: 0,
    storageUsed: '0 GB',
    activeWorkflows: 0
},
```

**Step 2: Commit**

```bash
git add dashboard/templates/index.html
git commit -m "fix: remove hardcoded stats defaults on home page"
```

---

## Task 4: Add Download Queue Section

**Files:**
- Modify: `dashboard/templates/index.html`

**Step 1: Add download queue section after Stats Grid**

Insert after the Stats Grid `</section>` (around line 72):

```html
<!-- Download Queue -->
<section class="mb-8" x-data="downloadQueue()" x-init="initQueue()" x-show="hasActiveDownloads">
    <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-semibold">
            Download Queue
            <span class="text-sm font-normal text-text-secondary ml-2" x-text="queueCountText"></span>
        </h2>
        <a href="/models" class="text-accent-primary text-sm font-medium hover:text-accent-secondary transition-colors">
            View All
        </a>
    </div>

    <div class="bg-bg-secondary border border-border-subtle rounded-lg overflow-hidden">
        <!-- Current Download -->
        <template x-if="currentDownload">
            <div class="p-4 border-b border-border-subtle">
                <div class="flex items-center justify-between mb-2">
                    <span class="font-medium" x-text="currentDownload.preset_id"></span>
                    <div class="flex items-center gap-2">
                        <span class="text-sm text-text-secondary" x-text="currentDownload.progress + '%'"></span>
                        <button @click="pauseDownload(currentDownload.preset_id)"
                                class="btn btn-secondary btn-sm py-1 px-2 text-xs rounded">
                            Pause
                        </button>
                    </div>
                </div>
                <div class="h-2 bg-bg-tertiary rounded-full overflow-hidden mb-2">
                    <div class="h-full bg-gradient-to-r from-accent-primary to-accent-secondary rounded-full transition-all"
                         :style="'width: ' + currentDownload.progress + '%'"></div>
                </div>
                <div class="flex justify-between text-xs text-text-tertiary">
                    <span x-text="formatBytes(currentDownload.downloaded_bytes) + ' / ' + formatBytes(currentDownload.total_bytes)"></span>
                    <span x-text="currentDownload.eta ? 'ETA: ' + currentDownload.eta : 'Downloading...'"></span>
                </div>
            </div>
        </template>

        <!-- Queued Downloads -->
        <template x-for="item in queue" :key="item.preset_id">
            <div class="p-4 flex items-center justify-between hover:bg-bg-hover">
                <div>
                    <span class="font-medium" x-text="item.preset_id"></span>
                    <p class="text-xs text-text-tertiary">Waiting for current download to complete</p>
                </div>
                <span class="text-xs px-2 py-1 rounded-full bg-accent-info/15 text-accent-info">Queued</span>
            </div>
        </template>

        <!-- Empty State -->
        <template x-if="!currentDownload && queue.length === 0">
            <div class="p-4 text-center text-text-secondary">
                No active downloads
            </div>
        </template>
    </div>
</section>
```

**Step 2: Add downloadQueue() JavaScript function**

Add to the `{% block extra_scripts %}` section:

```javascript
function downloadQueue() {
    return {
        currentDownload: null,
        queue: [],
        ws: null,

        initQueue() {
            this.loadQueueStatus();
            this.connectWebSocket();
            // Poll every 5 seconds as backup
            setInterval(() => this.loadQueueStatus(), 5000);
        },

        get hasActiveDownloads() {
            return this.currentDownload !== null || this.queue.length > 0;
        },

        get queueCountText() {
            const count = (this.currentDownload ? 1 : 0) + this.queue.length;
            return count > 0 ? `(${count} active)` : '';
        },

        async loadQueueStatus() {
            try {
                const response = await fetch('/api/presets/queue/status');
                if (response.ok) {
                    const data = await response.json();
                    this.currentDownload = data.current || null;
                    this.queue = data.queue || [];
                }
            } catch (error) {
                console.error('Failed to load queue status:', error);
            }
        },

        connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            this.ws = new WebSocket(`${protocol}//${window.location.host}/ws/downloads`);

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'download_progress') {
                        this.currentDownload = data.current;
                        this.queue = data.queue || [];
                    }
                } catch (e) {}
            };

            this.ws.onclose = () => {
                // Reconnect after 3 seconds
                setTimeout(() => this.connectWebSocket(), 3000);
            };
        },

        async pauseDownload(presetId) {
            try {
                await fetch(`/api/presets/${presetId}/pause`, { method: 'POST' });
                this.loadQueueStatus();
            } catch (error) {
                console.error('Failed to pause download:', error);
            }
        },

        formatBytes(bytes) {
            if (!bytes) return '0 B';
            const units = ['B', 'KB', 'MB', 'GB'];
            let i = 0;
            while (bytes >= 1024 && i < units.length - 1) {
                bytes /= 1024;
                i++;
            }
            return `${bytes.toFixed(1)} ${units[i]}`;
        }
    }
}
```

**Step 3: Commit**

```bash
git add dashboard/templates/index.html
git commit -m "feat: add download queue section to home page

- Shows active download with progress bar
- Lists queued downloads
- WebSocket updates for real-time progress
- Hidden when no active downloads"
```

---

## Task 5: Connect System Resources to Real Data

**Files:**
- Modify: `dashboard/templates/index.html`

**Step 1: Replace hardcoded System Resources section**

Replace the entire System Resources section (around lines 74-138) with:

```html
<!-- System Resources -->
<section class="mb-8" x-data="systemResources()" x-init="initResources()">
    <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-semibold">System Resources</h2>
        <button @click="loadResources()"
                class="btn btn-secondary btn-sm py-1.5 px-3 rounded-md text-sm font-medium border border-border-medium hover:bg-bg-hover hover:border-border-strong transition-all">
            Refresh
        </button>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- GPU Memory -->
        <div class="resource-card bg-bg-secondary border border-border-subtle rounded-lg p-3" x-show="resources.gpu">
            <div class="flex items-center justify-between mb-3">
                <span class="text-sm font-medium text-text-secondary">GPU Memory</span>
                <span class="text-xs" :class="getStatusClass(resources.gpuPercent, 'gpu')">
                    <span x-text="getStatusText(resources.gpuPercent, 'gpu')"></span>
                </span>
            </div>
            <div class="text-lg font-bold mb-2" x-text="formatMemory(resources.gpu?.memory_used, resources.gpu?.memory_total)"></div>
            <div class="h-1.5 bg-bg-tertiary rounded-full overflow-hidden mb-1">
                <div class="h-full rounded-full transition-all duration-200"
                     :class="getBarClass(resources.gpuPercent)"
                     :style="'width: ' + resources.gpuPercent + '%'"></div>
            </div>
            <div class="text-xs text-text-tertiary" x-text="resources.gpuPercent + '% utilized'"></div>
        </div>

        <!-- System Memory -->
        <div class="resource-card bg-bg-secondary border border-border-subtle rounded-lg p-3">
            <div class="flex items-center justify-between mb-3">
                <span class="text-sm font-medium text-text-secondary">System Memory</span>
                <span class="text-xs" :class="getStatusClass(resources.memoryPercent, 'memory')">
                    <span x-text="getStatusText(resources.memoryPercent, 'memory')"></span>
                </span>
            </div>
            <div class="text-lg font-bold mb-2" x-text="formatMemory(resources.memory?.used, resources.memory?.total)"></div>
            <div class="h-1.5 bg-bg-tertiary rounded-full overflow-hidden mb-1">
                <div class="h-full rounded-full transition-all duration-200"
                     :class="getBarClass(resources.memoryPercent)"
                     :style="'width: ' + resources.memoryPercent + '%'"></div>
            </div>
            <div class="text-xs text-text-tertiary" x-text="resources.memoryPercent + '% utilized'"></div>
        </div>

        <!-- Disk Space -->
        <div class="resource-card bg-bg-secondary border border-border-subtle rounded-lg p-3">
            <div class="flex items-center justify-between mb-3">
                <span class="text-sm font-medium text-text-secondary">Disk Space</span>
                <span class="text-xs" :class="getStatusClass(resources.diskPercent, 'disk')">
                    <span x-text="getStatusText(resources.diskPercent, 'disk')"></span>
                </span>
            </div>
            <div class="text-lg font-bold mb-2" x-text="formatDisk(resources.disk?.used, resources.disk?.total)"></div>
            <div class="h-1.5 bg-bg-tertiary rounded-full overflow-hidden mb-1">
                <div class="h-full rounded-full transition-all duration-200"
                     :class="getBarClass(resources.diskPercent, 'disk')"
                     :style="'width: ' + resources.diskPercent + '%'"></div>
            </div>
            <div class="text-xs text-text-tertiary" x-text="resources.diskPercent + '% utilized'"></div>
        </div>

        <!-- GPU Utilization -->
        <div class="resource-card bg-bg-secondary border border-border-subtle rounded-lg p-3" x-show="resources.gpu">
            <div class="flex items-center justify-between mb-3">
                <span class="text-sm font-medium text-text-secondary">GPU Utilization</span>
                <span class="text-xs" :class="getStatusClass(resources.gpuUtil, 'util')">
                    <span x-text="getStatusText(resources.gpuUtil, 'util')"></span>
                </span>
            </div>
            <div class="text-lg font-bold mb-2" x-text="resources.gpuUtil + '%'"></div>
            <div class="h-1.5 bg-bg-tertiary rounded-full overflow-hidden mb-1">
                <div class="h-full rounded-full transition-all duration-200"
                     :class="getBarClass(resources.gpuUtil, 'util')"
                     :style="'width: ' + resources.gpuUtil + '%'"></div>
            </div>
            <div class="text-xs text-text-tertiary">
                <span x-text="resources.gpu?.name || 'GPU'"></span>
            </div>
        </div>
    </div>
</section>
```

**Step 2: Replace systemResources() JavaScript function**

```javascript
function systemResources() {
    return {
        resources: {
            gpu: null,
            memory: null,
            disk: null,
            cpu_percent: 0,
            gpuPercent: 0,
            memoryPercent: 0,
            diskPercent: 0,
            gpuUtil: 0
        },

        initResources() {
            this.loadResources();
            // Refresh every 10 seconds
            setInterval(() => this.loadResources(), 10000);
        },

        async loadResources() {
            try {
                const response = await fetch('/api/system/resources');
                if (response.ok) {
                    const data = await response.json();
                    this.resources.cpu_percent = data.cpu_percent || 0;
                    this.resources.memory = data.memory;
                    this.resources.disk = data.disk;

                    // Calculate percentages
                    this.resources.memoryPercent = Math.round(data.memory?.percent || 0);
                    this.resources.diskPercent = Math.round(data.disk?.percent || 0);

                    // GPU data
                    if (data.gpu && data.gpu.devices && data.gpu.devices.length > 0) {
                        const gpu = data.gpu.devices[0];
                        this.resources.gpu = gpu;
                        this.resources.gpuPercent = Math.round((gpu.memory_used / gpu.memory_total) * 100);
                        this.resources.gpuUtil = gpu.utilization || 0;
                    } else {
                        this.resources.gpu = null;
                        this.resources.gpuPercent = 0;
                        this.resources.gpuUtil = 0;
                    }
                }
            } catch (error) {
                console.error('Failed to load resources:', error);
            }
        },

        formatMemory(used, total) {
            if (!used || !total) return '0 / 0 GB';
            const usedGB = (used / 1024).toFixed(1);
            const totalGB = (total / 1024).toFixed(0);
            return `${usedGB} / ${totalGB} GB`;
        },

        formatDisk(used, total) {
            if (!used || !total) return '0 / 0 GB';
            const usedGB = (used / (1024 ** 3)).toFixed(1);
            const totalGB = (total / (1024 ** 3)).toFixed(0);
            return `${usedGB} / ${totalGB} GB`;
        },

        getStatusClass(percent, type) {
            const thresholds = { gpu: 70, memory: 70, disk: 80, util: 60 };
            const high = { gpu: 90, memory: 90, disk: 95, util: 85 };
            const t = thresholds[type] || 70;
            const h = high[type] || 90;

            if (percent >= h) return 'text-accent-error';
            if (percent >= t) return 'text-accent-warning';
            return 'text-accent-success';
        },

        getStatusText(percent, type) {
            const thresholds = { gpu: 70, memory: 70, disk: 80, util: 60 };
            const t = thresholds[type] || 70;

            if (percent >= 90) return 'Critical';
            if (percent >= t) return 'Moderate';
            return 'Optimal';
        },

        getBarClass(percent, type) {
            const thresholds = { gpu: 70, memory: 70, disk: 80, util: 60 };
            const t = thresholds[type] || 70;

            if (percent >= 90) return 'bg-accent-error';
            if (percent >= t) return 'bg-gradient-to-r from-accent-warning to-accent-error';
            return 'bg-gradient-to-r from-accent-success to-accent-warning';
        }
    }
}
```

**Step 3: Commit**

```bash
git add dashboard/templates/index.html
git commit -m "feat: connect system resources to real API data

- GPU memory, system RAM, disk space, GPU utilization
- Color-coded status based on thresholds
- Auto-refresh every 10 seconds
- Hide GPU cards when no GPU available"
```

---

## Task 6: Replace Featured Models with Recent Models

**Files:**
- Modify: `dashboard/templates/index.html`

**Step 1: Replace Featured Models section**

Replace the Featured Models section (around lines 140-247) with:

```html
<!-- Recent Models -->
<section class="mb-8" x-data="recentModels()" x-init="loadModels()">
    <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-semibold">Recent Models</h2>
        <a href="/models" class="text-accent-primary text-sm font-medium hover:text-accent-secondary transition-colors">
            View All
        </a>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <template x-for="model in models" :key="model.id">
            <div class="preset-card bg-bg-secondary border border-border-subtle rounded-lg p-4 card-hover relative">
                <div class="absolute top-3 right-3 text-xs font-semibold px-2.5 py-1 rounded-full"
                     :class="model.installed ? 'bg-accent-success/15 text-accent-success' : 'bg-accent-info/15 text-accent-info'"
                     x-text="model.installed ? 'Installed' : 'Available'"></div>

                <div class="preset-title text-base font-semibold mb-2 pr-14" x-text="model.name"></div>
                <div class="preset-description text-text-secondary text-sm leading-relaxed mb-3 min-h-10"
                     x-text="model.description"></div>
                <div class="preset-meta flex gap-4 mb-3 text-xs text-text-tertiary">
                    <div class="flex items-center gap-1">
                        <span>Size:</span>
                        <span x-text="model.download_size"></span>
                    </div>
                    <div class="flex items-center gap-1">
                        <span>Type:</span>
                        <span x-text="model.type"></span>
                    </div>
                </div>

                <template x-if="model.status === 'downloading'">
                    <div>
                        <div class="h-2 bg-bg-tertiary rounded-full overflow-hidden mb-2">
                            <div class="h-full bg-gradient-to-r from-accent-primary to-accent-secondary rounded-full"
                                 :style="'width: ' + (model.progress || 0) + '%'"></div>
                        </div>
                        <div class="flex gap-2">
                            <button @click="pauseInstall(model.id)" class="btn btn-secondary flex-1 py-2 px-3 rounded-md text-sm">Pause</button>
                            <button @click="cancelInstall(model.id)" class="btn bg-bg-tertiary flex-1 py-2 px-3 rounded-md text-sm">Cancel</button>
                        </div>
                    </div>
                </template>

                <template x-if="model.status !== 'downloading'">
                    <div class="preset-actions flex gap-2">
                        <button @click="showDetails(model)" class="btn btn-secondary flex-1 py-2 px-3 rounded-md text-sm font-medium border border-border-medium hover:bg-bg-hover">Details</button>
                        <template x-if="model.installed">
                            <a :href="'/generate?model=' + model.id" class="btn btn-primary flex-1 py-2 px-3 rounded-md text-sm font-medium bg-accent-primary text-text-inverse text-center">Generate</a>
                        </template>
                        <template x-if="!model.installed">
                            <button @click="installModel(model)" class="btn btn-primary flex-1 py-2 px-3 rounded-md text-sm font-medium bg-accent-primary text-text-inverse">Install</button>
                        </template>
                    </div>
                </template>
            </div>
        </template>

        <!-- Empty State -->
        <template x-if="models.length === 0 && !loading">
            <div class="col-span-3 text-center py-8 text-text-secondary">
                <p class="mb-4">No models installed yet</p>
                <a href="/models" class="btn btn-primary py-2 px-4 rounded-md bg-accent-primary text-text-inverse">Browse Models</a>
            </div>
        </template>

        <!-- Loading State -->
        <template x-if="loading">
            <div class="col-span-3 text-center py-8 text-text-secondary">
                Loading models...
            </div>
        </template>
    </div>
</section>
```

**Step 2: Add recentModels() JavaScript function**

```javascript
function recentModels() {
    return {
        models: [],
        loading: true,
        ws: null,

        async loadModels() {
            this.loading = true;
            try {
                const response = await fetch('/api/presets/?limit=6');
                if (response.ok) {
                    const data = await response.json();
                    // Sort: installed first, then by name
                    let presets = data.presets || [];

                    // Separate installed and available
                    const installed = presets.filter(p => p.installed);
                    const available = presets.filter(p => !p.installed);

                    // Take up to 3 of each, combine
                    this.models = [
                        ...installed.slice(0, 3),
                        ...available.slice(0, Math.max(0, 3 - installed.length))
                    ].map(p => ({
                        ...p,
                        status: 'idle',
                        progress: 0
                    }));
                }
            } catch (error) {
                console.error('Failed to load models:', error);
            }
            this.loading = false;

            // Connect to WebSocket for download updates
            this.connectWebSocket();
        },

        connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            this.ws = new WebSocket(`${protocol}//${window.location.host}/ws/downloads`);

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'download_progress' && data.preset_id) {
                        const model = this.models.find(m => m.id === data.preset_id);
                        if (model) {
                            model.status = 'downloading';
                            model.progress = data.progress || 0;
                        }
                    } else if (data.type === 'download_complete') {
                        const model = this.models.find(m => m.id === data.preset_id);
                        if (model) {
                            model.status = 'idle';
                            model.installed = true;
                            model.progress = 0;
                        }
                        // Reload to refresh installed status
                        this.loadModels();
                    }
                } catch (e) {}
            };
        },

        async installModel(model) {
            model.status = 'downloading';
            model.progress = 0;

            try {
                const response = await fetch(`/api/presets/${model.id}/install`, { method: 'POST' });
                if (!response.ok) {
                    model.status = 'idle';
                    console.error('Failed to start install');
                }
            } catch (error) {
                model.status = 'idle';
                console.error('Failed to install model:', error);
            }
        },

        async pauseInstall(presetId) {
            await fetch(`/api/presets/${presetId}/pause`, { method: 'POST' });
        },

        async cancelInstall(presetId) {
            await fetch(`/api/presets/${presetId}/cancel`, { method: 'POST' });
            this.loadModels();
        },

        showDetails(model) {
            // Emit event for modal or navigate
            window.dispatchEvent(new CustomEvent('show-model-details', { detail: model }));
        }
    }
}
```

**Step 3: Commit**

```bash
git add dashboard/templates/index.html
git commit -m "feat: replace featured models with real recent models

- Loads from /api/presets endpoint
- Shows installed models first, then available
- Install/Generate buttons with proper actions
- WebSocket updates for download progress"
```

---

## Task 7: Replace Recent Activity with Combined Feed

**Files:**
- Modify: `dashboard/templates/index.html`

**Step 1: Replace Recent Activity section**

Replace the Recent Activity section (around lines 249-301) with:

```html
<!-- Recent Activity -->
<section class="mb-8" x-data="activityFeed()" x-init="loadActivity()">
    <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-semibold">Recent Activity</h2>
        <button @click="clearActivity()"
                x-show="activities.length > 0"
                class="text-accent-primary text-sm font-medium hover:text-accent-secondary transition-colors">
            Clear All
        </button>
    </div>

    <div class="flex flex-col gap-2">
        <template x-for="activity in activities" :key="activity.id">
            <a :href="activity.link"
               class="activity-item flex items-center gap-4 p-3 bg-bg-secondary border border-border-subtle rounded-md hover:bg-bg-hover transition-colors">
                <div class="w-10 h-10 rounded-md flex items-center justify-center flex-shrink-0"
                     :class="getActivityIconBg(activity)">
                    <span x-text="getActivityIcon(activity)"></span>
                </div>
                <div class="flex-1 min-w-0">
                    <div class="text-sm font-medium mb-0.5" x-text="activity.title"></div>
                    <div class="text-xs text-text-tertiary" x-text="activity.subtitle + ' - ' + formatTime(activity.timestamp)"></div>
                </div>
                <div class="px-2.5 py-1 rounded-full text-xs font-semibold flex-shrink-0"
                     :class="getActivityStatusClass(activity.status)">
                    <span x-text="capitalize(activity.status)"></span>
                </div>
            </a>
        </template>

        <!-- Empty State -->
        <template x-if="activities.length === 0 && !loading">
            <div class="text-center py-8 text-text-secondary">
                <p>No recent activity</p>
            </div>
        </template>

        <!-- Loading State -->
        <template x-if="loading">
            <div class="text-center py-8 text-text-secondary">
                Loading activity...
            </div>
        </template>
    </div>
</section>
```

**Step 2: Add activityFeed() JavaScript function**

```javascript
function activityFeed() {
    return {
        activities: [],
        loading: true,
        ws: null,

        async loadActivity() {
            this.loading = true;
            try {
                const response = await fetch('/api/activity/recent?limit=5');
                if (response.ok) {
                    const data = await response.json();
                    this.activities = data.activities || [];
                }
            } catch (error) {
                console.error('Failed to load activity:', error);
            }
            this.loading = false;

            // Connect WebSocket for real-time updates
            this.connectWebSocket();
        },

        connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            this.ws = new WebSocket(`${protocol}//${window.location.host}/ws/dashboard`);

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'new_activity') {
                        this.activities.unshift(data.activity);
                        if (this.activities.length > 5) {
                            this.activities.pop();
                        }
                    }
                } catch (e) {}
            };
        },

        async clearActivity() {
            try {
                await fetch('/api/activity/clear', { method: 'DELETE' });
                this.activities = [];
            } catch (error) {
                console.error('Failed to clear activity:', error);
            }
        },

        getActivityIconBg(activity) {
            if (activity.status === 'failed') return 'bg-accent-error/15';
            if (activity.type === 'download') return 'bg-accent-primary/15';
            return 'bg-accent-success/15';
        },

        getActivityIcon(activity) {
            if (activity.status === 'failed') return 'X';
            if (activity.type === 'download') return 'D';
            return '+';
        },

        getActivityStatusClass(status) {
            if (status === 'completed') return 'bg-accent-success/15 text-accent-success';
            if (status === 'failed') return 'bg-accent-error/15 text-accent-error';
            if (status === 'started') return 'bg-accent-primary/15 text-accent-primary';
            return 'bg-accent-info/15 text-accent-info';
        },

        formatTime(timestamp) {
            const date = new Date(timestamp);
            const now = new Date();
            const diff = (now - date) / 1000;

            if (diff < 60) return 'just now';
            if (diff < 3600) return Math.floor(diff / 60) + ' minutes ago';
            if (diff < 86400) return Math.floor(diff / 3600) + ' hours ago';
            return Math.floor(diff / 86400) + ' days ago';
        },

        capitalize(str) {
            return str.charAt(0).toUpperCase() + str.slice(1);
        }
    }
}
```

**Step 3: Remove old presetCard function**

Delete the old `presetCard()` function (around lines 356-409) as it's no longer used.

**Step 4: Commit**

```bash
git add dashboard/templates/index.html
git commit -m "feat: replace recent activity with real combined feed

- Loads from /api/activity/recent endpoint
- Shows generations and downloads combined
- Real-time updates via WebSocket
- Clear all functionality
- Relative time formatting"
```

---

## Task 8: Clean Up - Remove Unused Code

**Files:**
- Modify: `dashboard/templates/index.html`

**Step 1: Remove old systemResources function**

Delete the old `systemResources()` function that had hardcoded values (around lines 345-354).

**Step 2: Remove old presetCard function**

If not already removed, delete the old `presetCard()` function.

**Step 3: Commit**

```bash
git add dashboard/templates/index.html
git commit -m "refactor: remove unused JavaScript functions from home page"
```

---

## Task 9: Test and Deploy

**Step 1: Verify all endpoints work**

```bash
# Test each endpoint
curl http://localhost:8082/api/dashboard/stats
curl http://localhost:8082/api/system/resources
curl http://localhost:8082/api/presets/queue/status
curl http://localhost:8082/api/presets/?limit=6
curl http://localhost:8082/api/activity/recent
```

**Step 2: Commit and push**

```bash
git add -A
git status  # Verify changes
git push origin main
```

**Step 3: Trigger Docker build**

```bash
gh workflow run build.yml -f targets=base -f cuda_versions=12-8
```

---

## Summary

| Task | Description | Files Changed |
|------|-------------|---------------|
| 1 | Create Activity API | activity.py, __init__.py |
| 2 | Add download activity hook | downloader.py |
| 3 | Remove stats defaults | index.html |
| 4 | Add Download Queue section | index.html |
| 5 | Connect System Resources | index.html |
| 6 | Replace Featured Models | index.html |
| 7 | Replace Recent Activity | index.html |
| 8 | Clean up unused code | index.html |
| 9 | Test and deploy | - |
