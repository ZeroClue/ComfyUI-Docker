# ComfyUI-Docker API Documentation

**Version:** 2.1.0
**Base URL:** `http://localhost:8082/api`
**Last Updated:** 2026-02-21

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [REST API](#rest-api)
  - [Health & Status](#health--status)
  - [Preset Management](#preset-management)
  - [GPU Recommendations](#gpu-recommendations)
  - [Version & Updates](#version--updates)
  - [Registry Sync](#registry-sync)
  - [Model Management](#model-management)
  - [ComfyUI Integration](#comfyui-integration)
  - [Workflow Management](#workflow-management)
  - [Download Management](#download-management)
  - [System Status](#system-status)
- [WebSocket Protocol](#websocket-protocol)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)

---

## Overview

The ComfyUI-Docker API provides a RESTful interface for managing ComfyUI models, workflows, and system resources. All endpoints return JSON unless otherwise specified.

### Base URL

- **Development:** `http://localhost:8082/api`
- **Production:** `https://your-pod-url.proxy.runpod.net/api`

### Response Format

All responses follow this structure:

```json
{
  "status": "success",
  "data": {},
  "message": "Optional message",
  "timestamp": "2026-02-15T10:30:00Z"
}
```

### Pagination

List endpoints support pagination:

```json
{
  "items": [],
  "total": 100,
  "page": 1,
  "per_page": 20,
  "has_next": true,
  "has_prev": false
}
```

---

## Authentication

### API Key Authentication

Include your API key in the request header:

```http
Authorization: Bearer YOUR_API_KEY
```

### Session-Based Authentication

For web UI, session cookies are used automatically.

### Generating API Keys

```bash
# In the container
python -m app.dashboard.core.auth generate-key
```

---

## REST API

### Health & Status

#### GET /health

Check dashboard health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "comfyui-dashboard",
  "version": "2.0.0",
  "timestamp": "2026-02-15T10:30:00Z"
}
```

#### GET /api/system/status

Get comprehensive system status.

**Response:**
```json
{
  "status": "running",
  "uptime": 3600,
  "services": {
    "dashboard": "running",
    "comfyui": "running",
    "preset_manager": "running"
  },
  "resources": {
    "cpu_percent": 45,
    "memory_percent": 78,
    "gpu_percent": 92,
    "disk_used_gb": 125.5,
    "disk_total_gb": 500.0
  }
}
```

#### GET /api/system/storage

Get storage information.

**Query Parameters:**
- `detail` (optional): Set to `true` for detailed breakdown

**Response:**
```json
{
  "workspace": {
    "path": "/workspace",
    "used_gb": 125.5,
    "total_gb": 500.0,
    "available_gb": 374.5,
    "usage_percent": 25.1
  },
  "models": {
    "count": 42,
    "total_size_gb": 98.7,
    "by_type": {
      "checkpoints": 15,
      "text_encoders": 8,
      "vae": 5,
      "loras": 14
    }
  }
}
```

---

## Preset Management

#### GET /api/presets

List all available presets.

**Query Parameters:**
- `category` (optional): Filter by category (`Video Generation`, `Image Generation`, `Audio Generation`)
- `type` (optional): Filter by type (`video`, `image`, `audio`)
- `installed` (optional): Filter by installation status (`true`, `false`)
- `search` (optional): Search in name, description, tags
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20)

**Response:**
```json
{
  "presets": [
    {
      "id": "WAN_22_5B_TIV2",
      "name": "WAN 2.2 5B Text-to-Image V2",
      "category": "Video Generation",
      "type": "video",
      "description": "WAN video generation model with text-to-image V2",
      "download_size": "14.5GB",
      "installed": true,
      "install_date": "2026-02-15T10:00:00Z",
      "use_case": "High-quality video generation from text prompts",
      "tags": ["wan", "t2v", "text-to-video"]
    }
  ],
  "total": 56,
  "page": 1,
  "per_page": 20
}
```

#### GET /api/presets/{preset_id}

Get detailed information about a specific preset.

**Response:**
```json
{
  "id": "WAN_22_5B_TIV2",
  "name": "WAN 2.2 5B Text-to-Image V2",
  "category": "Video Generation",
  "type": "video",
  "description": "WAN video generation model with text-to-image V2",
  "download_size": "14.5GB",
  "installed": true,
  "install_date": "2026-02-15T10:00:00Z",
  "use_case": "High-quality video generation from text prompts",
  "tags": ["wan", "t2v", "text-to-video"],
  "files": [
    {
      "path": "checkpoints/wan21.safetensors",
      "url": "https://huggingface.co/.../wan21.safetensors",
      "size": "4.8GB",
      "installed": true
    }
  ],
  "dependencies": [],
  "workflows": ["wan_t2v_basic.json"]
}
```

#### POST /api/presets/{preset_id}/install

Install a preset (background download).

**Request Body:**
```json
{
  "force": false,
  "priority": "normal"
}
```

**Response:**
```json
{
  "status": "installing",
  "preset_id": "WAN_22_5B_TIV2",
  "download_id": "dl_123456",
  "estimated_time_seconds": 300,
  "total_size_gb": 14.5
}
```

#### DELETE /api/presets/{preset_id}

Uninstall a preset (remove all model files).

**Request Body:**
```json
{
  "confirm": true,
  "remove_dependencies": false
}
```

**Response:**
```json
{
  "status": "uninstalled",
  "preset_id": "WAN_22_5B_TIV2",
  "files_removed": 5,
  "space_freed_gb": 14.5
}
```

#### GET /api/presets/{preset_id}/status

Get installation status for a preset.

**Response:**
```json
{
  "preset_id": "WAN_22_5B_TIV2",
  "status": "installing",
  "progress": 45.2,
  "current_file": "checkpoints/wan21.safetensors",
  "download_speed_mbps": 125.5,
  "eta_seconds": 150,
  "files": {
    "total": 5,
    "completed": 2,
    "failed": 0
  }
}
```

---

## GPU Recommendations

#### GET /api/presets/recommendations

Get preset recommendations based on GPU VRAM.

**Response:**
```json
{
  "gpu": {
    "name": "NVIDIA RTX 4090",
    "vram_mb": 24564,
    "vram_gb": 24.0
  },
  "compatible": [
    {
      "id": "WAN_22_5B_TIV2",
      "name": "WAN 2.2 5B T2V",
      "vram_gb": 16,
      "compatible": true,
      "installed": false
    }
  ],
  "incompatible": [
    {
      "id": "FLUX_DEV_FULL",
      "name": "FLUX Dev Full Precision",
      "vram_gb": 32,
      "compatible": false
    }
  ],
  "unknown": [
    {
      "id": "LEGACY_MODEL",
      "name": "Legacy Model",
      "vram_gb": null,
      "compatible": null
    }
  ]
}
```

---

## Version & Updates

#### GET /api/presets/updates

Check for preset updates by comparing local versions with remote registry.

**Response:**
```json
{
  "total": 2,
  "updates": [
    {
      "id": "WAN_22_5B_TIV2",
      "name": "WAN 2.2 5B T2V",
      "local_version": "1.0.0",
      "remote_version": "1.1.0",
      "category": "Video Generation",
      "type": "video"
    }
  ]
}
```

---

## Registry Sync

#### GET /api/presets/registry/sync

Sync preset registry from remote GitHub repository.

**Response:**
```json
{
  "status": "synced",
  "timestamp": "2026-02-21T10:30:00Z",
  "presets_count": 56,
  "source": "https://raw.githubusercontent.com/zeroclue/comfyui-presets/main/registry.json"
}
```

#### GET /api/presets/registry/status

Get current registry cache status.

**Response:**
```json
{
  "status": "loaded",
  "version": "1.0.0",
  "generated_at": "2026-02-21T08:00:00Z",
  "total_presets": 56,
  "categories": {
    "Video Generation": 26,
    "Image Generation": 25,
    "Audio Generation": 5
  },
  "last_sync": "2026-02-21T10:30:00Z"
}
```

---

## Model Management

#### GET /api/models

List all installed models.

**Query Parameters:**
- `type` (optional): Filter by model type
- `search` (optional): Search in filename
- `page` (optional): Page number
- `per_page` (optional): Items per page

**Response:**
```json
{
  "models": [
    {
      "path": "checkpoints/wan21.safetensors",
      "type": "checkpoints",
      "size_gb": 4.8,
      "modified": "2026-02-15T10:00:00Z",
      "preset": "WAN_22_5B_TIV2"
    }
  ],
  "total": 42,
  "total_size_gb": 98.7
}
```

#### DELETE /api/models

Delete one or more models.

**Request Body:**
```json
{
  "paths": [
    "checkpoints/old_model.safetensors",
    "loras/unused_lora.safetensors"
  ],
  "confirm": true
}
```

**Response:**
```json
{
  "deleted": 2,
  "space_freed_gb": 8.5,
  "errors": []
}
```

#### GET /api/models/types

Get available model types.

**Response:**
```json
{
  "types": [
    {"id": "checkpoints", "name": "Checkpoints", "count": 15},
    {"id": "text_encoders", "name": "Text Encoders", "count": 8},
    {"id": "vae", "name": "VAE", "count": 5},
    {"id": "loras", "name": "LoRAs", "count": 14}
  ]
}
```

#### GET /api/models/validate

Validate model files integrity.

**Query Parameters:**
- `type` (optional): Validate specific model type
- `preset` (optional): Validate models for specific preset

**Response:**
```json
{
  "validated": 42,
  "errors": [
    {
      "path": "checkpoints/corrupt.safetensors",
      "error": "File checksum mismatch"
    }
  ]
}
```

---

## ComfyUI Integration

#### GET /api/comfyui/health

Check ComfyUI service health.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.3.10",
  "queue": {
    "pending": 3,
    "running": 1
  }
}
```

#### POST /api/comfyui/execute

Execute a workflow.

**Request Body:**
```json
{
  "workflow": {
    "1": {
      "class_type": "KSampler",
      "inputs": {
        "seed": 123456,
        "steps": 20,
        "cfg": 8,
        "sampler_name": "euler",
        "scheduler": "normal",
        "denoise": 1
      }
    }
  },
  "priority": 1
}
```

**Response:**
```json
{
  "prompt_id": "abc123",
  "number": 1,
  "status": "queued"
}
```

#### GET /api/comfyui/queue

Get current queue status.

**Response:**
```json
{
  "queue_running": [
    {
      "prompt_id": "abc123",
      "number": 1
    }
  ],
  "queue_pending": [
    {
      "prompt_id": "def456",
      "number": 2
    }
  ]
}
```

#### GET /api/comfyui/history/{prompt_id}

Get execution history for a prompt.

**Response:**
```json
{
  "prompt_id": "abc123",
  "status": "completed",
  "outputs": {
    "images": [
      {
        "filename": "output_00001.png",
        "subfolder": "",
        "type": "output"
      }
    ]
  },
  "started": "2026-02-15T10:30:00Z",
  "completed": "2026-02-15T10:30:15Z"
}
```

#### DELETE /api/comfyui/queue

Clear the queue.

**Query Parameters:**
- `type` (optional): `all`, `pending`, `running` (default: `pending`)

**Response:**
```json
{
  "cleared": 3,
  "status": "success"
}
```

#### POST /api/comfyui/interrupt

Interrupt current execution.

**Response:**
```json
{
  "status": "interrupted"
}
```

---

## Workflow Management

#### GET /api/workflows

List available workflows.

**Query Parameters:**
- `category` (optional): Filter by category
- `search` (optional): Search in name/description
- `page` (optional): Page number
- `per_page` (optional): Items per page

**Response:**
```json
{
  "workflows": [
    {
      "id": "wan_t2v_basic",
      "name": "WAN Text-to-Video Basic",
      "category": "Video Generation",
      "description": "Basic text-to-video workflow using WAN model",
      "preset": "WAN_22_5B_TIV2",
      "path": "workflows/templates/wan_t2v_basic.json"
    }
  ],
  "total": 25
}
```

#### GET /api/workflows/{workflow_id}

Get workflow JSON.

**Response:**
```json
{
  "id": "wan_t2v_basic",
  "workflow": {
    "1": {
      "class_type": "CheckpointLoaderSimple",
      "inputs": {
        "ckpt_name": "wan21.safetensors"
      }
    }
  }
}
```

#### POST /api/workflows

Save a workflow.

**Request Body:**
```json
{
  "name": "My Custom Workflow",
  "category": "Custom",
  "workflow": {
    "1": {
      "class_type": "KSampler",
      "inputs": {}
    }
  }
}
```

**Response:**
```json
{
  "id": "custom_123",
  "status": "saved",
  "path": "workflows/user/custom_123.json"
}
```

#### PUT /api/workflows/{workflow_id}

Update an existing workflow.

**Request Body:**
```json
{
  "name": "Updated Workflow Name",
  "workflow": {}
}
```

#### DELETE /api/workflows/{workflow_id}

Delete a workflow.

**Response:**
```json
{
  "status": "deleted",
  "workflow_id": "custom_123"
}
```

---

## Download Management

#### GET /api/downloads

List active downloads.

**Response:**
```json
{
  "downloads": [
    {
      "id": "dl_123456",
      "preset_id": "WAN_22_5B_TIV2",
      "status": "downloading",
      "progress": 45.2,
      "speed_mbps": 125.5,
      "eta_seconds": 150,
      "current_file": "checkpoints/wan21.safetensors"
    }
  ],
  "active": 1,
  "total": 5
}
```

#### POST /api/downloads/{download_id}/pause

Pause a download.

**Response:**
```json
{
  "status": "paused",
  "download_id": "dl_123456"
}
```

#### POST /api/downloads/{download_id}/resume

Resume a paused download.

**Response:**
```json
{
  "status": "downloading",
  "download_id": "dl_123456"
}
```

#### DELETE /api/downloads/{download_id}

Cancel a download.

**Response:**
```json
{
  "status": "cancelled",
  "download_id": "dl_123456",
  "files_removed": true
}
```

---

## System Status

#### GET /api/system/resources

Get detailed resource usage.

**Response:**
```json
{
  "cpu": {
    "percent": 45.2,
    "count": 16,
    "freq": {
      "current": 3200.0,
      "min": 800.0,
      "max": 3200.0
    }
  },
  "memory": {
    "total_gb": 32.0,
    "available_gb": 7.0,
    "percent": 78.1,
    "used_gb": 25.0
  },
  "gpu": {
    "count": 1,
    "devices": [
      {
        "id": 0,
        "name": "NVIDIA RTX 4090",
        "memory_total_gb": 24.0,
        "memory_used_gb": 22.1,
        "memory_free_gb": 1.9,
        "utilization_percent": 92.0,
        "temperature_c": 75.0
      }
    ]
  },
  "disk": {
    "total_gb": 500.0,
    "used_gb": 125.5,
    "free_gb": 374.5,
    "percent": 25.1
  }
}
```

#### GET /api/system/logs

Get system logs.

**Query Parameters:**
- `service` (optional): Filter by service (dashboard, comfyui, preset_manager)
- `lines` (optional): Number of lines (default: 100)
- `follow` (optional): Enable log streaming (true/false)

**Response:**
```json
{
  "logs": [
    {
      "timestamp": "2026-02-15T10:30:00Z",
      "level": "INFO",
      "service": "dashboard",
      "message": "Starting ComfyUI Unified Dashboard..."
    }
  ]
}
```

---

## WebSocket Protocol

### Connection

**Endpoint:** `ws://localhost:8080/ws`

**Message Format:** All messages are JSON objects with a `type` field.

### Client → Server Messages

#### Subscribe to Updates

```json
{
  "type": "subscribe",
  "channels": ["downloads", "queue", "system"]
}
```

Available channels:
- `downloads`: Download progress updates
- `queue`: ComfyUI queue changes
- `system`: System status updates
- `workflows`: Workflow execution progress

#### Unsubscribe from Updates

```json
{
  "type": "unsubscribe",
  "channels": ["downloads"]
}
```

#### Execute Action

```json
{
  "type": "action",
  "action": "install_preset",
  "data": {
    "preset_id": "WAN_22_5B_TIV2"
  }
}
```

### Server → Client Messages

#### Download Progress

```json
{
  "type": "download_progress",
  "data": {
    "download_id": "dl_123456",
    "preset_id": "WAN_22_5B_TIV2",
    "progress": 45.2,
    "current_file": "checkpoints/wan21.safetensors",
    "speed": "125 MB/s",
    "eta": "2m 30s",
    "files": {
      "total": 5,
      "completed": 2
    }
  }
}
```

#### Download Complete

```json
{
  "type": "download_complete",
  "data": {
    "download_id": "dl_123456",
    "preset_id": "WAN_22_5B_TIV2",
    "status": "success",
    "time_taken_seconds": 300
  }
}
```

#### Queue Update

```json
{
  "type": "queue_update",
  "data": {
    "queue_pending": 3,
    "queue_running": 1,
    "current_task": {
      "prompt_id": "abc123",
      "type": "image_generation"
    }
  }
}
```

#### System Status

```json
{
  "type": "system_status",
  "data": {
    "cpu_usage": 45,
    "memory_usage": 78,
    "gpu_usage": 92,
    "disk_usage": 67
  }
}
```

#### Workflow Progress

```json
{
  "type": "workflow_progress",
  "data": {
    "prompt_id": "abc123",
    "node": "5",
    "value": 0.5,
    "max": 1.0,
    "type": "executing"
  }
}
```

#### Workflow Output

```json
{
  "type": "workflow_output",
  "data": {
    "prompt_id": "abc123",
    "output": {
      "images": [
        {
          "filename": "output_00001.png",
          "subfolder": "",
          "type": "output"
        }
      ]
    }
  }
}
```

#### Error Notification

```json
{
  "type": "error",
  "data": {
    "code": "DOWNLOAD_FAILED",
    "message": "Failed to download model file",
    "details": {
      "file": "checkpoints/wan21.safetensors",
      "error": "Connection timeout"
    }
  }
}
```

---

## Error Codes

| Code | Description | HTTP Status |
|-----|-------------|-------------|
| `PRESET_NOT_FOUND` | Requested preset does not exist | 404 |
| `PRESET_ALREADY_INSTALLED` | Preset is already installed | 409 |
| `DOWNLOAD_FAILED` | Model download failed | 500 |
| `INSUFFICIENT_STORAGE` | Not enough disk space | 507 |
| `COMFYUI_UNAVAILABLE` | ComfyUI service is not responding | 503 |
| `INVALID_WORKFLOW` | Workflow JSON is invalid | 400 |
| `MODEL_NOT_FOUND` | Requested model file does not exist | 404 |
| `QUEUE_FULL` | ComfyUI queue is at capacity | 507 |
| `UNAUTHORIZED` | Authentication required | 401 |
| `FORBIDDEN` | Insufficient permissions | 403 |
| `RATE_LIMIT_EXCEEDED` | Too many requests | 429 |
| `INTERNAL_ERROR` | Unexpected server error | 500 |

### Error Response Format

```json
{
  "error": {
    "code": "PRESET_NOT_FOUND",
    "message": "Preset 'INVALID_ID' not found",
    "details": {},
    "timestamp": "2026-02-15T10:30:00Z"
  }
}
```

---

## Rate Limiting

### Limits

- **Unauthenticated**: 100 requests/minute per IP
- **Authenticated**: 1000 requests/minute per token

### Rate Limit Headers

All responses include rate limit headers:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1641234567
X-RateLimit-Reset-Time: 2026-02-15T10:30:00Z
```

### Handling Rate Limits

When rate limited, the response includes a `Retry-After` header:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

---

## Versioning

The API is versioned using the `X-API-Version` header. Clients can request specific versions:

```http
X-API-Version: 2.0.0
```

Current version: `2.0.0`

---

## CORS

CORS is enabled for all origins by default in development. Configure allowed origins via the `CORS_ORIGINS` environment variable in production.

---

## SDK Examples

### Python

```python
import requests

class ComfyUIDashboard:
    def __init__(self, base_url="http://localhost:8080", api_key=None):
        self.base_url = base_url
        self.headers = {}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    def list_presets(self, category=None, type=None):
        params = {"category": category, "type": type}
        response = requests.get(
            f"{self.base_url}/api/presets",
            params=params,
            headers=self.headers
        )
        return response.json()

    def install_preset(self, preset_id):
        response = requests.post(
            f"{self.base_url}/api/presets/{preset_id}/install",
            headers=self.headers
        )
        return response.json()

# Usage
dashboard = ComfyUIDashboard(api_key="your-api-key")
presets = dashboard.list_presets(type="video")
```

### JavaScript

```javascript
class ComfyUIDashboard {
  constructor(baseUrl = 'http://localhost:8080', apiKey = null) {
    this.baseUrl = baseUrl;
    this.headers = {};
    if (apiKey) {
      this.headers['Authorization'] = `Bearer ${apiKey}`;
    }
  }

  async listPresets(category = null, type = null) {
    const params = new URLSearchParams({
      ...(category && { category }),
      ...(type && { type })
    });

    const response = await fetch(
      `${this.baseUrl}/api/presets?${params}`,
      { headers: this.headers }
    );
    return response.json();
  }

  async installPreset(presetId) {
    const response = await fetch(
      `${this.baseUrl}/api/presets/${presetId}/install`,
      {
        method: 'POST',
        headers: this.headers
      }
    );
    return response.json();
  }
}

// Usage
const dashboard = new ComfyUIDashboard('your-api-key');
const presets = await dashboard.listPresets(null, 'video');
```

---

## WebSocket Client Example

### Python

```python
import asyncio
import websockets
import json

async def subscribe_to_updates():
    uri = "ws://localhost:8080/ws"
    async with websockets.connect(uri) as websocket:
        # Subscribe to channels
        await websocket.send(json.dumps({
            "type": "subscribe",
            "channels": ["downloads", "queue", "system"]
        }))

        # Listen for messages
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Received: {data['type']}", data.get('data'))

# Run
asyncio.run(subscribe_to_updates())
```

### JavaScript

```javascript
const ws = new WebSocket('ws://localhost:8080/ws');

ws.onopen = () => {
  // Subscribe to channels
  ws.send(JSON.stringify({
    type: 'subscribe',
    channels: ['downloads', 'queue', 'system']
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(`Received: ${message.type}`, message.data);

  switch (message.type) {
    case 'download_progress':
      updateProgressBar(message.data);
      break;
    case 'queue_update':
      updateQueueDisplay(message.data);
      break;
    case 'system_status':
      updateSystemStats(message.data);
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket connection closed');
};
```

---

## Support

For API issues or questions:

- **Documentation**: Check [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture
- **Issues**: Report bugs at [GitHub Issues](https://github.com/ZeroClue/ComfyUI-Docker/issues)
- **Examples**: See `examples/` directory for code examples

---

*Document Version: 2.0.0*
*Last Updated: 2026-02-15*
*API Version: 2.0.0*
