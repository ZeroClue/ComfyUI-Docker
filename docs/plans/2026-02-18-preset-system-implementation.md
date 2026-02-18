# Unified Dashboard Preset System - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement a fully functional preset management system with online refresh, sequential downloads, auto-retry, and template compatibility.

**Architecture:** Single source of truth in GitHub (`config/presets.yaml`), sequential download queue with WebSocket progress, smart refresh that preserves active downloads, template scanning for model compatibility.

**Tech Stack:** FastAPI, Pydantic, aiohttp, WebSocket, Alpine.js, htmx

---

## Phase 1: Backend - Download Queue System

### Task 1.1: Add Sequential Queue to DownloadManager

**Files:**
- Modify: `dashboard/core/downloader.py:41-100`

**Current State:** Uses semaphore for parallel downloads (up to 3 concurrent)
**Target State:** Sequential FIFO queue, one download at a time

**Step 1: Add queue data structures**

Add to `DownloadManager.__init__`:

```python
def __init__(self):
    self.active_downloads: Dict[str, List[DownloadTask]] = {}
    self.download_queue: asyncio.Queue = asyncio.Queue()
    self.current_download: Optional[str] = None
    self.queue_processor_running: bool = False
    self.base_path = Path(settings.MODEL_BASE_PATH)
    self.retry_config = {
        "max_retries": 3,
        "base_delay": 5,  # seconds
        "max_delay": 60
    }
```

**Step 2: Verify no syntax errors**

Run: `python3 -c "from dashboard.core.downloader import DownloadManager; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add dashboard/core/downloader.py
git commit -m "feat(downloader): add sequential queue data structures"
```

---

### Task 1.2: Implement Queue Processor

**Files:**
- Modify: `dashboard/core/downloader.py`

**Step 1: Add queue processor method**

Add method to `DownloadManager` class:

```python
async def _process_queue(self):
    """Process downloads sequentially from queue"""
    self.queue_processor_running = True

    while True:
        try:
            # Get next preset from queue
            preset_id, tasks = await self.download_queue.get()

            if preset_id not in self.active_downloads:
                # Download was cancelled while in queue
                continue

            self.current_download = preset_id

            # Broadcast queue update
            await self._broadcast_queue_update()

            # Download files sequentially within preset
            for task in tasks:
                if task.status == "cancelled":
                    continue

                retry_count = 0
                while retry_count < self.retry_config["max_retries"]:
                    await self._download_file(task)

                    if task.status == "completed":
                        break
                    elif task.status == "failed":
                        retry_count += 1
                        if retry_count < self.retry_config["max_retries"]:
                            delay = min(
                                self.retry_config["base_delay"] * (2 ** retry_count),
                                self.retry_config["max_delay"]
                            )
                            task.status = "retrying"
                            task.error = f"Retrying ({retry_count}/{self.retry_config['max_retries']})..."
                            await asyncio.sleep(delay)
                            task.status = "downloading"

                if task.status == "failed":
                    # Max retries exhausted
                    await broadcast_download_progress(preset_id, {
                        "type": "download_failed",
                        "preset_id": preset_id,
                        "file": task.file_path,
                        "error": task.error,
                        "retry_count": self.retry_config["max_retries"]
                    })

            # Mark preset complete
            if preset_id in self.active_downloads:
                del self.active_downloads[preset_id]

            self.current_download = None
            await self._broadcast_queue_update()

        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Queue processor error: {e}")
            await asyncio.sleep(1)

    self.queue_processor_running = False
```

**Step 2: Add broadcast helper**

```python
async def _broadcast_queue_update(self):
    """Broadcast current queue state via WebSocket"""
    from .websocket import manager

    queue_list = []
    # Get items in queue without removing them
    for item in list(self.download_queue._queue):
        if isinstance(item, tuple):
            queue_list.append(item[0])

    await manager.broadcast_json({
        "type": "queue_updated",
        "current": self.current_download,
        "queue": queue_list
    })
```

**Step 3: Verify syntax**

Run: `python3 -c "from dashboard.core.downloader import DownloadManager; dm = DownloadManager(); print('OK')"`
Expected: `OK`

**Step 4: Commit**

```bash
git add dashboard/core/downloader.py
git commit -m "feat(downloader): implement sequential queue processor with auto-retry"
```

---

### Task 1.3: Update start_download to Use Queue

**Files:**
- Modify: `dashboard/core/downloader.py:49-102`

**Step 1: Replace parallel with queue-based download**

Replace `start_download` method:

```python
async def start_download(
    self,
    preset_id: str,
    files: List[Dict],
    force: bool = False
) -> str:
    """
    Queue preset for sequential download

    Args:
        preset_id: ID of the preset to download
        files: List of file dictionaries with 'path' and 'url' keys
        force: Force re-download even if file exists

    Returns:
        Download ID for tracking
    """
    import time
    download_id = f"{preset_id}_{int(time.time())}"

    # Check if already in queue or downloading
    if preset_id == self.current_download:
        return f"Already downloading: {preset_id}"

    if preset_id in self.active_downloads:
        return f"Already queued: {preset_id}"

    # Check queue
    for item in list(self.download_queue._queue):
        if isinstance(item, tuple) and item[0] == preset_id:
            return f"Already in queue: {preset_id}"

    # Create download tasks
    tasks = []
    for file_info in files:
        file_path = file_info.get('path', '')
        file_url = file_info.get('url', '')
        file_size = file_info.get('size', 'Unknown')

        if not file_url:
            continue

        # Check if file exists and force flag
        full_path = self.base_path / file_path
        if full_path.exists() and not force:
            continue

        task = DownloadTask(
            preset_id=preset_id,
            file_url=file_url,
            file_path=file_path,
            file_size=file_size
        )
        tasks.append(task)

    if not tasks:
        return f"No files to download for preset {preset_id}"

    self.active_downloads[preset_id] = tasks

    # Add to queue
    await self.download_queue.put((preset_id, tasks))

    # Start queue processor if not running
    if not self.queue_processor_running:
        asyncio.create_task(self._process_queue())

    # Broadcast queue update
    await self._broadcast_queue_update()

    return download_id
```

**Step 2: Verify**

Run: `python3 -c "from dashboard.core.downloader import DownloadManager; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add dashboard/core/downloader.py
git commit -m "feat(downloader): use sequential queue for downloads"
```

---

### Task 1.4: Add Pause/Resume/Cancel Methods

**Files:**
- Modify: `dashboard/core/downloader.py:208-224`

**Step 1: Add pause, resume, retry methods**

```python
async def pause_download(self, preset_id: str) -> bool:
    """Pause active download (keeps partial file)"""
    if preset_id not in self.active_downloads:
        return False

    for task in self.active_downloads[preset_id]:
        if task.status == "downloading":
            task.status = "paused"

    await self._broadcast_queue_update()
    return True

async def resume_download(self, preset_id: str) -> bool:
    """Resume paused download"""
    if preset_id not in self.active_downloads:
        return False

    for task in self.active_downloads[preset_id]:
        if task.status == "paused":
            task.status = "pending"

    # Re-queue if not currently downloading
    if self.current_download != preset_id:
        await self.download_queue.put((preset_id, self.active_downloads[preset_id]))

    await self._broadcast_queue_update()
    return True

async def cancel_download(self, preset_id: str, keep_partial: bool = True) -> bool:
    """Cancel download, optionally keeping partial files"""
    if preset_id in self.active_downloads:
        for task in self.active_downloads[preset_id]:
            task.status = "cancelled"
            if not keep_partial:
                full_path = self.base_path / task.file_path
                if full_path.exists():
                    full_path.unlink()

        del self.active_downloads[preset_id]
        await self._broadcast_queue_update()
        return True

    return False

async def retry_download(self, preset_id: str) -> bool:
    """Retry failed download from beginning"""
    # This will be handled by re-calling start_download
    return False  # API endpoint will handle this

def get_queue_status(self) -> Dict:
    """Get current queue status"""
    queue_list = []
    for item in list(self.download_queue._queue):
        if isinstance(item, tuple):
            queue_list.append(item[0])

    return {
        "current": self.current_download,
        "queue": queue_list,
        "active_downloads": len(self.active_downloads)
    }
```

**Step 2: Verify**

Run: `python3 -c "from dashboard.core.downloader import DownloadManager; dm = DownloadManager(); print(dir(dm))"`
Expected: List containing `pause_download`, `resume_download`, `cancel_download`

**Step 3: Commit**

```bash
git add dashboard/core/downloader.py
git commit -m "feat(downloader): add pause/resume/cancel methods"
```

---

### Task 1.5: Add WebSocket broadcast_json Helper

**Files:**
- Modify: `dashboard/core/websocket.py`

**Step 1: Add broadcast_json method to ConnectionManager**

```python
async def broadcast_json(self, data: dict):
    """Broadcast JSON data to all connected clients"""
    import json
    message = json.dumps(data)
    await self.broadcast(message)
```

**Step 2: Verify**

Run: `python3 -c "from dashboard.core.websocket import manager; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add dashboard/core/websocket.py
git commit -m "feat(websocket): add broadcast_json helper method"
```

---

## Phase 2: Backend - Preset Refresh API

### Task 2.1: Add GitHub Refresh Endpoint

**Files:**
- Modify: `dashboard/api/presets.py`

**Step 1: Add refresh endpoint**

Add import at top:
```python
import aiohttp
```

Add endpoint after `list_categories`:

```python
@router.post("/refresh")
async def refresh_presets():
    """
    Fetch latest presets.yaml from GitHub

    Smart refresh: updates preset definitions without interrupting active downloads
    """
    import yaml
    import shutil

    github_url = "https://raw.githubusercontent.com/ZeroClue/ComfyUI-Docker/main/config/presets.yaml"
    local_path = Path(settings.PRESET_CONFIG_PATH)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(github_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"GitHub returned {response.status}"
                    )

                content = await response.text()

        # Validate YAML before saving
        try:
            new_config = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise HTTPException(status_code=400, detail=f"Invalid YAML: {str(e)}")

        # Backup existing config
        if local_path.exists():
            backup_path = local_path.with_suffix('.yaml.bak')
            shutil.copy(local_path, backup_path)

        # Write new config
        local_path.parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, 'w') as f:
            f.write(content)

        return {
            "status": "success",
            "message": "Presets refreshed successfully",
            "total_presets": len(new_config.get('presets', {})),
            "version": new_config.get('metadata', {}).get('version', 'unknown')
        }

    except aiohttp.ClientError as e:
        raise HTTPException(status_code=503, detail=f"Failed to fetch from GitHub: {str(e)}")
```

**Step 2: Verify**

Run: `python3 -c "from dashboard.api.presets import router; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add dashboard/api/presets.py
git commit -m "feat(presets): add GitHub refresh endpoint with smart refresh"
```

---

### Task 2.2: Add Queue Status Endpoint

**Files:**
- Modify: `dashboard/api/presets.py`

**Step 1: Add queue endpoint**

```python
@router.get("/queue/status")
async def get_queue_status():
    """Get current download queue status"""
    return download_manager.get_queue_status()
```

**Step 2: Verify**

Run: `python3 -c "from dashboard.api.presets import router; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add dashboard/api/presets.py
git commit -m "feat(presets): add queue status endpoint"
```

---

### Task 2.3: Add Install/Pause/Cancel/Retry Endpoints

**Files:**
- Modify: `dashboard/api/presets.py`

**Step 1: Add new endpoints**

```python
@router.post("/{preset_id}/install")
async def install_preset(preset_id: str, force: bool = False):
    """
    Queue preset for installation

    - **preset_id**: The ID of the preset to install
    - **force**: Force re-download even if files exist
    """
    config = await get_presets_from_config()

    if preset_id not in config.get('presets', {}):
        raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")

    preset_data = config['presets'][preset_id]

    download_id = await download_manager.start_download(
        preset_id=preset_id,
        files=preset_data.get('files', []),
        force=force
    )

    return {
        "preset_id": preset_id,
        "status": "queued",
        "download_id": download_id
    }


@router.post("/{preset_id}/pause")
async def pause_preset_download(preset_id: str):
    """Pause active download"""
    success = await download_manager.pause_download(preset_id)
    if not success:
        raise HTTPException(status_code=404, detail="No active download for this preset")
    return {"preset_id": preset_id, "status": "paused"}


@router.post("/{preset_id}/resume")
async def resume_preset_download(preset_id: str):
    """Resume paused download"""
    success = await download_manager.resume_download(preset_id)
    if not success:
        raise HTTPException(status_code=404, detail="No paused download for this preset")
    return {"preset_id": preset_id, "status": "resumed"}


@router.post("/{preset_id}/cancel")
async def cancel_preset_download(preset_id: str, keep_partial: bool = True):
    """Cancel download"""
    success = await download_manager.cancel_download(preset_id, keep_partial)
    if not success:
        raise HTTPException(status_code=404, detail="No download to cancel")
    return {"preset_id": preset_id, "status": "cancelled"}


@router.post("/{preset_id}/retry")
async def retry_preset_download(preset_id: str):
    """Retry failed download"""
    config = await get_presets_from_config()

    if preset_id not in config.get('presets', {}):
        raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")

    preset_data = config['presets'][preset_id]

    # Force re-download
    download_id = await download_manager.start_download(
        preset_id=preset_id,
        files=preset_data.get('files', []),
        force=True
    )

    return {
        "preset_id": preset_id,
        "status": "retrying",
        "download_id": download_id
    }
```

**Step 2: Verify**

Run: `python3 -c "from dashboard.api.presets import router; print([r.path for r in router.routes])"`
Expected: List containing `/refresh`, `/queue/status`, `/{preset_id}/install`, etc.

**Step 3: Commit**

```bash
git add dashboard/api/presets.py
git commit -m "feat(presets): add install/pause/resume/cancel/retry endpoints"
```

---

## Phase 3: Backend - Template Compatibility

### Task 3.1: Add Template Scanner

**Files:**
- Create: `dashboard/core/template_scanner.py`

**Step 1: Create template scanner module**

```python
"""
Template scanner for model compatibility checking
Scans ComfyUI workflow templates for required models
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Optional
from dataclasses import dataclass


@dataclass
class ModelReference:
    """Reference to a model found in a template"""
    path: str
    node_type: str
    input_name: str


class TemplateScanner:
    """Scans ComfyUI templates for model references"""

    # Common model input field patterns
    MODEL_PATTERNS = {
        'checkpoints': ['ckpt_name', 'checkpoint', 'model_path'],
        'text_encoders': ['clip_name', 'text_encoder', 't5_name'],
        'vae': ['vae_name', 'vae'],
        'loras': ['lora_name', 'lora'],
        'controlnet': ['controlnet_name', 'control_net'],
        'clip_vision': ['clip_vision_name', 'clip_vision'],
        'upscale_models': ['upscale_model_name', 'model_name'],
        'ipadapters': ['ipadapter_file', 'adapter_name'],
    }

    def __init__(self, model_base_path: str = "/workspace/models"):
        self.model_base_path = Path(model_base_path)

    def scan_template(self, template_path: Path) -> List[ModelReference]:
        """Scan a single template file for model references"""
        references = []

        try:
            with open(template_path, 'r') as f:
                template = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return references

        # Handle both workflow format and node format
        nodes = template if isinstance(template, dict) and 'nodes' not in template else template.get('nodes', {})

        for node_id, node_data in self._iter_nodes(nodes):
            class_type = node_data.get('class_type', '')
            inputs = node_data.get('inputs', {})

            for input_name, input_value in inputs.items():
                if isinstance(input_value, str):
                    # Check if this input matches a model pattern
                    model_type = self._get_model_type(input_name, class_type)
                    if model_type:
                        references.append(ModelReference(
                            path=f"{model_type}/{input_value}",
                            node_type=class_type,
                            input_name=input_name
                        ))

        return references

    def _iter_nodes(self, nodes):
        """Iterate over nodes in either format"""
        if isinstance(nodes, list):
            for i, node in enumerate(nodes):
                yield str(i), node
        elif isinstance(nodes, dict):
            yield from nodes.items()

    def _get_model_type(self, input_name: str, class_type: str) -> Optional[str]:
        """Determine model type from input name and class type"""
        input_lower = input_name.lower()

        for model_type, patterns in self.MODEL_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in input_lower:
                    return model_type

        return None

    def check_installed(self, references: List[ModelReference]) -> Dict[str, bool]:
        """Check which model references are installed"""
        installed = {}

        for ref in references:
            full_path = self.model_base_path / ref.path
            installed[ref.path] = full_path.exists()

        return installed

    def get_missing_models(self, template_path: Path) -> List[Dict]:
        """Get list of missing models for a template"""
        references = self.scan_template(template_path)
        installed = self.check_installed(references)

        missing = []
        for ref in references:
            if not installed.get(ref.path, False):
                missing.append({
                    "path": ref.path,
                    "node_type": ref.node_type,
                    "input_name": ref.input_name
                })

        return missing
```

**Step 2: Verify**

Run: `python3 -c "from dashboard.core.template_scanner import TemplateScanner; ts = TemplateScanner(); print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add dashboard/core/template_scanner.py
git commit -m "feat: add template scanner for model compatibility"
```

---

### Task 3.2: Add Templates API Endpoint

**Files:**
- Modify: `dashboard/api/workflows.py`

**Step 1: Add template compatibility endpoint**

Add import:
```python
from ..core.template_scanner import TemplateScanner
```

Add endpoint:

```python
@router.get("/templates")
async def list_templates():
    """List ComfyUI templates with model compatibility info"""
    from pathlib import Path

    # ComfyUI templates location
    template_paths = [
        Path("/app/comfyui/web/assets"),
        Path("/workspace/workflows"),
    ]

    scanner = TemplateScanner(settings.MODEL_BASE_PATH)
    templates = []

    for base_path in template_paths:
        if not base_path.exists():
            continue

        for template_file in base_path.glob("**/*.json"):
            try:
                missing = scanner.get_missing_models(template_file)

                templates.append({
                    "id": str(template_file.relative_to(base_path)),
                    "name": template_file.stem,
                    "path": str(template_file),
                    "compatible": len(missing) == 0,
                    "missing_models": missing,
                    "missing_count": len(missing)
                })
            except Exception:
                continue

    return {"templates": templates, "total": len(templates)}


@router.get("/templates/{template_id:path}/missing-models")
async def get_template_missing_models(template_id: str):
    """Get missing models for a specific template"""
    from pathlib import Path

    # Find template
    template_paths = [
        Path("/app/comfyui/web/assets") / template_id,
        Path("/workspace/workflows") / template_id,
    ]

    template_file = None
    for path in template_paths:
        if path.exists():
            template_file = path
            break

    if not template_file:
        raise HTTPException(status_code=404, detail="Template not found")

    scanner = TemplateScanner(settings.MODEL_BASE_PATH)
    missing = scanner.get_missing_models(template_file)

    return {
        "template_id": template_id,
        "missing_models": missing,
        "can_generate": len(missing) == 0
    }
```

**Step 2: Verify**

Run: `python3 -c "from dashboard.api.workflows import router; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add dashboard/api/workflows.py
git commit -m "feat(workflows): add templates endpoint with compatibility check"
```

---

## Phase 4: Frontend - Models Page

### Task 4.1: Update Models Template to Remove Mock Data

**Files:**
- Modify: `dashboard/templates/models.html`

**Step 1: Replace mock data fallback with real API call**

Find the `loadModels` function (around line 195) and update:

```javascript
async loadModels() {
    try {
        const response = await fetch('/api/presets/');
        if (response.ok) {
            const data = await response.json();
            this.models = data.presets.map(preset => ({
                id: preset.id,
                name: preset.name,
                description: preset.description,
                size: preset.download_size,
                category: preset.category,
                type: preset.type,
                status: preset.installed ? 'installed' : 'available',
                progress: preset.installed ? 100 : 0,
                tags: preset.tags || []
            }));
            this.calculateCounts();
        }
    } catch (error) {
        console.error('Failed to load models:', error);
        // Show empty state instead of mock data
        this.models = [];
        this.calculateCounts();
    }
},
```

**Step 2: Commit**

```bash
git add dashboard/templates/models.html
git commit -m "feat(models): use real API data instead of mock"
```

---

### Task 4.2: Add Refresh Button Handler

**Files:**
- Modify: `dashboard/templates/models.html`

**Step 1: Update refresh button to call API**

Find the refresh button (around line 18-25) and update:

```html
<button class="btn btn-secondary py-2 px-4 rounded-md text-sm font-medium border border-border-medium hover:bg-bg-hover hover:border-border-strong transition-all"
        @click="refreshPresets"
        :disabled="isRefreshing">
    <span x-show="isRefreshing" class="spinner inline-block"></span>
    <span x-show="!isRefreshing">↻ Refresh</span>
</button>
```

**Step 2: Add refreshPresets method**

Add to `modelsPage()`:

```javascript
isRefreshing: false,

async refreshPresets() {
    this.isRefreshing = true;
    try {
        const response = await fetch('/api/presets/refresh', { method: 'POST' });
        if (response.ok) {
            const data = await response.json();
            window.showToast('success', 'Presets Refreshed', `Loaded ${data.total_presets} presets (v${data.version})`);
            await this.loadModels();
        } else {
            throw new Error('Refresh failed');
        }
    } catch (error) {
        console.error('Refresh failed:', error);
        window.showToast('error', 'Refresh Failed', 'Could not fetch latest presets');
    } finally {
        this.isRefreshing = false;
    }
},
```

**Step 3: Commit**

```bash
git add dashboard/templates/models.html
git commit -m "feat(models): add preset refresh functionality"
```

---

### Task 4.3: Add Download Queue UI

**Files:**
- Modify: `dashboard/templates/models.html`

**Step 1: Add queue display section**

Add after the search/filter section (around line 86):

```html
<!-- Download Queue -->
<div x-show="downloadQueue.current || downloadQueue.queue.length > 0"
     class="bg-bg-secondary border border-border-subtle rounded-lg p-4 mb-6">

    <!-- Current Download -->
    <div x-show="downloadQueue.current" class="mb-4">
        <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-medium">Downloading: <span x-text="downloadQueue.current"></span></span>
            <button @click="pauseDownload(downloadQueue.current)" class="text-xs text-text-secondary hover:text-text-primary">Pause</button>
        </div>
        <div class="progress h-2 bg-bg-tertiary rounded-full overflow-hidden mb-2">
            <div class="h-full bg-gradient-to-r from-accent-primary to-accent-secondary rounded-full transition-all duration-300"
                 :style="`width: ${currentProgress}%`"></div>
        </div>
        <div class="flex justify-between text-xs text-text-tertiary">
            <span x-text="currentProgressText"></span>
            <span x-text="`${currentProgress}%`"></span>
        </div>
    </div>

    <!-- Queue -->
    <div x-show="downloadQueue.queue.length > 0">
        <div class="text-sm font-medium mb-2">Queue (<span x-text="downloadQueue.queue.length"></span>)</div>
        <div class="space-y-1">
            <template x-for="(presetId, index) in downloadQueue.queue" :key="presetId">
                <div class="flex items-center justify-between text-sm text-text-secondary py-1">
                    <span x-text="presetId"></span>
                    <button @click="cancelDownload(presetId)" class="text-xs text-accent-error hover:text-red-400">Cancel</button>
                </div>
            </template>
        </div>
    </div>
</div>
```

**Step 2: Add queue state and methods**

Add to `modelsPage()`:

```javascript
downloadQueue: {
    current: null,
    queue: []
},
currentProgress: 0,
currentProgressText: 'Preparing...',
ws: null,

initModelsPage() {
    this.loadModels();
    this.calculateCounts();
    this.initWebSocket();
},

initWebSocket() {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/dashboard`;

    this.ws = new WebSocket(wsUrl);

    this.ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        } catch (e) {
            console.error('WebSocket parse error:', e);
        }
    };

    this.ws.onclose = () => {
        // Reconnect after 5 seconds
        setTimeout(() => this.initWebSocket(), 5000);
    };
},

handleWebSocketMessage(data) {
    if (data.type === 'download_progress') {
        if (data.presetId === this.downloadQueue.current) {
            this.currentProgress = data.progress || 0;
            this.currentProgressText = `${data.downloaded || 0} / ${data.total || 0}`;
        }
    } else if (data.type === 'download_complete') {
        window.showToast('success', 'Download Complete', `${data.presetId} installed successfully`);
        this.loadModels();
    } else if (data.type === 'download_failed') {
        window.showToast('error', 'Download Failed', `${data.presetId}: ${data.error}`);
    } else if (data.type === 'queue_updated') {
        this.downloadQueue.current = data.current;
        this.downloadQueue.queue = data.queue || [];
        if (!data.current) {
            this.currentProgress = 0;
            this.currentProgressText = 'Preparing...';
        }
    }
},

async pauseDownload(presetId) {
    await fetch(`/api/presets/${presetId}/pause`, { method: 'POST' });
},

async cancelDownload(presetId) {
    await fetch(`/api/presets/${presetId}/cancel`, { method: 'POST' });
},
```

**Step 3: Commit**

```bash
git add dashboard/templates/models.html
git commit -m "feat(models): add download queue UI with WebSocket updates"
```

---

### Task 4.4: Update Install Button Handler

**Files:**
- Modify: `dashboard/templates/models.html`

**Step 1: Update handleAction in presetCard**

Find `handleAction` method (around line 383) and update:

```javascript
async handleAction() {
    if (this.model.status === 'available') {
        try {
            const response = await fetch(`/api/presets/${this.model.id}/install`, { method: 'POST' });
            if (response.ok) {
                this.model.status = 'queued';
                this.updateText();
                window.showToast('success', 'Queued', `${this.model.name} added to download queue`);
            }
        } catch (error) {
            console.error('Failed to queue preset:', error);
            window.showToast('error', 'Queue Failed', 'Could not queue preset for download');
        }
    } else if (this.model.status === 'installed') {
        window.location.href = `/generate?model=${this.model.id}`;
    } else if (this.model.status === 'failed') {
        try {
            const response = await fetch(`/api/presets/${this.model.id}/retry`, { method: 'POST' });
            if (response.ok) {
                this.model.status = 'queued';
                this.updateText();
            }
        } catch (error) {
            console.error('Failed to retry:', error);
        }
    }
}
```

**Step 2: Update statusText mapping**

```javascript
updateText() {
    const statusMap = {
        'installed': { statusText: 'Installed', actionText: 'Generate', progressText: '' },
        'available': { statusText: 'Available', actionText: 'Install', progressText: '' },
        'queued': { statusText: 'Queued', actionText: 'In Queue', progressText: 'Waiting...' },
        'downloading': { statusText: 'Downloading', actionText: 'Pause', progressText: 'Downloading...' },
        'paused': { statusText: 'Paused', actionText: 'Resume', progressText: 'Paused' },
        'failed': { statusText: 'Failed', actionText: 'Retry', progressText: '' }
    };

    const config = statusMap[this.model.status] || statusMap['available'];
    this.statusText = config.statusText;
    this.actionText = config.actionText;
    this.progressText = config.progressText;
},
```

**Step 3: Commit**

```bash
git add dashboard/templates/models.html
git commit -m "feat(models): update install/retry button handlers"
```

---

## Phase 5: Integration & Testing

### Task 5.1: Add Toast Notification System

**Files:**
- Modify: `dashboard/templates/base.html`

**Step 1: Add toast container (using safe DOM methods)**

Add before closing `</body>` tag:

```html
<!-- Toast Container -->
<div id="toast-container" class="fixed bottom-4 right-4 z-50 space-y-2"></div>

<script>
window.showToast = function(type, title, message) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');

    const colors = {
        success: 'bg-accent-success/20 border-accent-success',
        error: 'bg-accent-error/20 border-accent-error',
        warning: 'bg-accent-warning/20 border-accent-warning',
        info: 'bg-accent-info/20 border-accent-info'
    };

    toast.className = `${colors[type] || colors.info} border rounded-lg p-4 shadow-lg max-w-sm transform transition-all duration-300 translate-x-full`;

    // Use safe DOM methods instead of innerHTML
    const titleEl = document.createElement('div');
    titleEl.className = 'font-semibold text-text-primary';
    titleEl.textContent = title;

    const messageEl = document.createElement('div');
    messageEl.className = 'text-sm text-text-secondary mt-1';
    messageEl.textContent = message;

    toast.appendChild(titleEl);
    toast.appendChild(messageEl);
    container.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
        toast.classList.remove('translate-x-full');
    });

    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.classList.add('translate-x-full');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
};
</script>
```

**Step 2: Commit**

```bash
git add dashboard/templates/base.html
git commit -m "feat(base): add toast notification system"
```

---

### Task 5.2: Update API Router Registration

**Files:**
- Modify: `dashboard/api/__init__.py`

**Step 1: Verify all routers are included**

```python
"""
API router aggregation
"""

from fastapi import APIRouter

from .models import router as models_router
from .presets import router as presets_router
from .workflows import router as workflows_router
from .system import router as system_router
from .websocket import router as websocket_router

api_router = APIRouter()

api_router.include_router(models_router, prefix="/models", tags=["models"])
api_router.include_router(presets_router, prefix="/presets", tags=["presets"])
api_router.include_router(workflows_router, prefix="/workflows", tags=["workflows"])
api_router.include_router(system_router, prefix="/system", tags=["system"])
api_router.include_router(websocket_router, prefix="/ws", tags=["websocket"])
```

**Step 2: Verify**

Run: `python3 -c "from dashboard.api import api_router; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add dashboard/api/__init__.py
git commit -m "chore(api): verify router registration"
```

---

### Task 5.3: Push Changes and Deploy Test

**Step 1: Push all changes**

```bash
git push origin main
```

**Step 2: Trigger build**

```bash
gh workflow run build.yml -f targets=base -f cuda_versions=12-8
```

**Step 3: Monitor build**

```bash
gh run watch --interval 30
```

**Step 4: Deploy test pod and verify**

After build completes, deploy pod and test:
1. Navigate to Models page
2. Click Refresh - verify presets load
3. Click Install on a preset - verify queue appears
4. Verify WebSocket updates show progress
5. Verify toast notifications appear

---

## Summary

**Total Tasks:** 17

**Files Modified:**
- `dashboard/core/downloader.py` - Sequential queue, auto-retry
- `dashboard/core/websocket.py` - broadcast_json helper
- `dashboard/core/template_scanner.py` - New file
- `dashboard/api/presets.py` - Refresh, queue, install endpoints
- `dashboard/api/workflows.py` - Templates endpoint
- `dashboard/templates/models.html` - Real data, queue UI, WebSocket
- `dashboard/templates/base.html` - Toast notifications
- `dashboard/api/__init__.py` - Router verification

**Key Features Implemented:**
1. Sequential download queue (FIFO)
2. Auto-retry with exponential backoff (3 attempts)
3. Smart refresh from GitHub
4. Pause/resume/cancel downloads
5. WebSocket progress updates
6. Template compatibility scanning
7. Toast notifications
8. Real API data (no mock)
