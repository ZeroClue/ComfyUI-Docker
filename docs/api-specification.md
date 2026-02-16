# ComfyUI-Docker Revolutionary API Specification

## Overview

This document defines the REST API and WebSocket protocols for the unified dashboard system. All endpoints return JSON unless otherwise specified.

**Base URL**: `http://localhost:8080/api`

**Authentication**: Optional Bearer token or session-based (configurable via `ENABLE_AUTH` environment variable)

---

## REST API Endpoints

### Health & Status

#### GET /health
Check dashboard health status.

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-02-15T10:30:00Z"
}
```

#### GET /api/system/status
Get comprehensive system status.

**Response**:
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

**Response**:
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

### Preset Management

#### GET /api/presets
List all available presets.

**Query Parameters**:
- `category` (optional): Filter by category (`Video Generation`, `Image Generation`, `Audio Generation`)
- `type` (optional): Filter by type (`video`, `image`, `audio`)
- `installed` (optional): Filter by installation status (`true`, `false`)
- `search` (optional): Search in name, description, tags

**Response**:
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
      "use_case": "High-quality video generation from text prompts",
      "tags": ["wan", "t2v", "text-to-video"]
    }
  ],
  "total": 56,
  "filtered": 10,
  "categories": ["Video Generation", "Image Generation", "Audio Generation"]
}
```

#### GET /api/presets/{preset_id}
Get detailed information about a specific preset.

**Response**:
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

**Request Body**:
```json
{
  "force": false,
  "priority": "normal"
}
```

**Response**:
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

**Response**:
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

**Response**:
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

### Model Management

#### GET /api/models
List all installed models.

**Query Parameters**:
- `type` (optional): Filter by model type
- `search` (optional): Search in filename

**Response**:
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

**Request Body**:
```json
{
  "paths": [
    "checkpoints/old_model.safetensors",
    "loras/unused_lora.safetensors"
  ]
}
```

**Response**:
```json
{
  "deleted": 2,
  "space_freed_gb": 8.5,
  "errors": []
}
```

#### GET /api/models/types
Get available model types.

**Response**:
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

### ComfyUI Integration

#### GET /api/comfyui/health
Check ComfyUI service health.

**Response**:
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

**Request Body**:
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

**Response**:
```json
{
  "prompt_id": "abc123",
  "number": 1,
  "status": "queued"
}
```

#### GET /api/comfyui/queue
Get current queue status.

**Response**:
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

**Response**:
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

**Query Parameters**:
- `type` (optional): `all`, `pending`, `running` (default: `pending`)

**Response**:
```json
{
  "cleared": 3,
  "status": "success"
}
```

#### POST /api/comfyui/interrupt
Interrupt current execution.

**Response**:
```json
{
  "status": "interrupted"
}
```

### Workflow Management

#### GET /api/workflows
List available workflows.

**Query Parameters**:
- `category` (optional): Filter by category
- `search` (optional): Search in name/description

**Response**:
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

**Response**:
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

**Request Body**:
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

**Response**:
```json
{
  "id": "custom_123",
  "status": "saved",
  "path": "workflows/user/custom_123.json"
}
```

### Download Management

#### GET /api/downloads
List active downloads.

**Response**:
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

**Response**:
```json
{
  "status": "paused",
  "download_id": "dl_123456"
}
```

#### POST /api/downloads/{download_id}/resume
Resume a paused download.

**Response**:
```json
{
  "status": "downloading",
  "download_id": "dl_123456"
}
```

#### DELETE /api/downloads/{download_id}
Cancel a download.

**Response**:
```json
{
  "status": "cancelled",
  "download_id": "dl_123456",
  "files_removed": true
}
```

---

## WebSocket Protocol

### Connection

**Endpoint**: `ws://localhost:8080/ws`

**Message Format**: All messages are JSON objects with a `type` field.

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

| Code | Description |
|-----|-------------|
| `PRESET_NOT_FOUND` | Requested preset does not exist |
| `PRESET_ALREADY_INSTALLED` | Preset is already installed |
| `DOWNLOAD_FAILED` | Model download failed |
| `INSUFFICIENT_STORAGE` | Not enough disk space |
| `COMFYUI_UNAVAILABLE` | ComfyUI service is not responding |
| `INVALID_WORKFLOW` | Workflow JSON is invalid |
| `MODEL_NOT_FOUND` | Requested model file does not exist |
| `QUEUE_FULL` | ComfyUI queue is at capacity |

---

## Rate Limiting

- **Unauthenticated**: 100 requests/minute per IP
- **Authenticated**: 1000 requests/minute per token

Rate limit headers are included in all responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1641234567
```

---

## Authentication (Optional)

When `ENABLE_AUTH=true`, clients must authenticate using Bearer tokens or session cookies.

#### POST /api/auth/login
Login with credentials.

**Request Body**:
```json
{
  "username": "admin",
  "password": "password"
}
```

**Response**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600
}
```

#### POST /api/auth/logout
Logout and invalidate session.

**Response**:
```json
{
  "status": "success"
}
```

#### GET /api/auth/verify
Verify authentication token.

**Response**:
```json
{
  "valid": true,
  "user": {
    "username": "admin",
    "role": "administrator"
  }
}
```

---

## WebSocket Authentication

For authenticated connections, include the token in the connection URL:

```
ws://localhost:8080/ws?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Or send an authentication message immediately after connecting:

```json
{
  "type": "auth",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

## Versioning

The API is versioned using the `X-API-Version` header. Clients can request specific versions:

```
X-API-Version: 1.0.0
```

Current version: `1.0.0`

---

## CORS

CORS is enabled for all origins by default in development. Configure allowed origins via the `CORS_ORIGINS` environment variable.

---

*Last Updated: 2026-02-15*
*API Version: 1.0.0*
