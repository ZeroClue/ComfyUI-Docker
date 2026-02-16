# ComfyUI-Docker v2.0 Architecture

**Version:** 2.0.0
**Status:** Production Ready
**Last Updated:** 2026-02-15

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Multi-Stage Docker Build](#multi-stage-docker-build)
- [Volume Architecture](#volume-architecture)
- [Dashboard Architecture](#dashboard-architecture)
- [Startup Flow](#startup-flow)
- [API Architecture](#api-architecture)
- [Data Flows](#data-flows)
- [Component Diagram](#component-diagram)
- [Technology Stack](#technology-stack)
- [Performance Optimizations](#performance-optimizations)
- [Security Considerations](#security-considerations)
- [Monitoring & Observability](#monitoring--observability)

---

## Overview

ComfyUI-Docker v2.0 introduces a revolutionary architecture that eliminates the traditional rsync bottleneck and enables instant startup through native ComfyUI integration and persistent network volumes.

### Key Principles

1. **Immutable Application Code**: All application code lives in the container image
2. **Persistent User Data**: All user data lives on network volumes
3. **Zero-Rsync**: Native ComfyUI `extra_model_paths.yaml` for model paths
4. **Unified Dashboard**: Single interface for all operations
5. **Background Processing**: Non-blocking downloads and operations

### Architecture Goals

- **Instant Startup**: <30 seconds from container start to ready
- **Scalability**: Support horizontal and vertical scaling
- **Developer Experience**: Simple setup, clear documentation
- **Operational Simplicity**: Easy deployment and maintenance
- **Cost Efficiency**: Optimize resource usage and storage costs

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Container Layer (Immutable)                  │
├─────────────────────────────────────────────────────────────────┤
│  /app/comfyui/      │  /app/venv/  │  /app/dashboard/          │
│  - ComfyUI Core     │  - Python    │  - FastAPI Backend        │
│  - Custom Nodes     │  - Packages  │  - htmx Frontend          │
│  - Manager          │              │  - Alpine.js Logic        │
│                     │              │  - Tailwind Styles        │
│  /app/tools/        │              │                           │
│  - Preset Manager   │              │                           │
│  - Utilities        │              │                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Network Volume (Persistent - /workspace)            │
├─────────────────────────────────────────────────────────────────┤
│  models/          output/         workflows/      uploads/       │
│  - checkpoints/    - generated/   - user/         - input/      │
│  - text_encoders/  - temp/        - templates/    - assets/     │
│  - vae/                                                          │
│  - clip_vision/                                                  │
│  - audio_encoders/                                               │
│                                                                 │
│  config/                                                          │
│  - extra_model_paths.yaml (generated at startup)                │
│  - user_settings.yaml                                            │
│                                                                 │
│  cache/                                                           │
│  - .cache/huggingface/                                           │
│  - .cache/pip/                                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Technology |
|-----------|----------------|------------|
| **Unified Dashboard** | Central UI for all operations | FastAPI + htmx + Alpine.js + Tailwind |
| **Preset Manager** | Model installation and management | Python + YAML config |
| **ComfyUI Bridge** | Communication with ComfyUI backend | WebSocket + HTTP API |
| **Model Path Manager** | Generate extra_model_paths.yaml | Python + Jinja2 templates |
| **Download Orchestrator** | Background model downloads | Python asyncio + callbacks |
| **WebSocket Server** | Real-time progress updates | FastAPI WebSockets |
| **Startup Orchestrator** | Service initialization and health checks | Bash + Python |
| **Volume Manager** | Network volume health and mounting | Python + RunPod API |

---

## Multi-Stage Docker Build

### Build Stages

```
┌─────────────────────────────────────────────────────────────────┐
│ Stage 1: Builder (nvidia/cuda:XX.X-devel-ubuntu22.04)           │
├─────────────────────────────────────────────────────────────────┤
│ - Install UV package manager                                     │
│ - Create Python virtual environment                              │
│ - Install PyTorch with CUDA support                             │
│ - Build heavy dependencies (numpy, scipy, etc.)                  │
│ - Clone ComfyUI repository                                       │
│ - Install ComfyUI requirements                                   │
│ - Clone ComfyUI-Manager                                          │
│ Output: /venv/, /ComfyUI/                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 2: Python-deps                                            │
├─────────────────────────────────────────────────────────────────┤
│ - Install minimal custom nodes                                  │
│ - Install preset manager dependencies                           │
│ - Install dashboard dependencies (FastAPI, uvicorn, jinja2)     │
│ - Install frontend build tools (node, npm for htmx build)       │
│ Output: Complete Python environment                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 3: Dashboard-builder                                      │
├─────────────────────────────────────────────────────────────────┤
│ - Build htmx + Alpine.js frontend bundle                        │
│ - Compile Tailwind CSS to production stylesheet                  │
│ - Optimize and minify assets                                    │
│ - Copy to /app/dashboard/static/                                │
│ Output: Optimized frontend bundle (~50KB)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 4: Runtime (nvidia/cuda:XX.X-runtime-ubuntu22.04)         │
├─────────────────────────────────────────────────────────────────┤
│ - Copy /venv from Builder stage                                 │
│ - Copy /app/comfyui from ComfyUI-core stage                     │
│ - Copy /app/dashboard from Dashboard-builder stage              │
│ - Copy /app/tools from Tools stage                              │
│ - Copy startup scripts                                          │
│ - Configure nginx reverse proxy                                 │
│ - Set up entrypoint                                             │
│ Output: Production-ready image                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Build Variants

| Variant | Size | Features | Use Case |
|---------|------|----------|----------|
| **minimal** | ~4-5GB | ComfyUI + Manager + Dashboard + Preset Manager | Production serving |
| **standard** | ~6-7GB | Minimal + Popular Custom Nodes | General usage |
| **full** | ~8-10GB | Standard + All Custom Nodes + Dev Tools | Development and testing |
| **dev** | ~10-12GB | Full + Code Server + Jupyter | Full development environment |

---

## Volume Architecture

### Directory Structure

```
/workspace/
├── models/
│   ├── checkpoints/              # Primary diffusion models
│   ├── text_encoders/           # T5, CLIP, etc.
│   ├── vae/                     # Variational autoencoders
│   ├── clip_vision/             # Image encoders
│   ├── loras/                   # LoRA adapters
│   ├── upscale_models/          # Image upscaling
│   ├── audio_encoders/          # Audio processing
│   ├── controlnet/              # ControlNet models
│   └── [other model types]      # Additional model categories
├── output/
│   ├── images/                  # Generated images
│   ├── videos/                  # Generated videos
│   └── temp/                    # Temporary files
├── workflows/
│   ├── user/                    # User-created workflows
│   ├── templates/               # Preset workflows
│   └── presets/                 # Workflow presets
├── uploads/
│   ├── input/                   # User uploads for processing
│   └── assets/                  # Static assets
├── config/
│   ├── extra_model_paths.yaml   # Generated at startup
│   ├── user_settings.yaml       # User configuration
│   └── presets.yaml             # Preset definitions
└── cache/
    ├── .cache/huggingface/      # HuggingFace cache
    ├── .cache/pip/              # pip cache
    └── .cache/uv/               # UV package manager cache
```

### Model Path Configuration

The `extra_model_paths.yaml` file is generated at container startup:

```yaml
# Auto-generated at startup
/workspace:
  checkpoints: /workspace/models/checkpoints
  lora: /workspace/models/lora
  text_encoders: /workspace/models/text_encoders
  vae: /workspace/models/vae
  clip_vision: /workspace/models/clip_vision
  upscale_models: /workspace/models/upscale_models
  embeddings: /workspace/models/embeddings
  controlnet: /workspace/models/controlnet
  ipadapter: /workspace/models/ipadapter
  audio_encoders: /workspace/models/audio_encoders
  output: /workspace/output
  input: /workspace/uploads
```

---

## Dashboard Architecture

### Technology Stack

- **Backend**: FastAPI (async, modern Python web framework)
- **Frontend**: htmx + Alpine.js + Tailwind CSS (~50KB bundle)
- **Real-time**: WebSocket for live updates
- **Templates**: Jinja2 for server-side rendering

### Directory Structure

```
/app/dashboard/
├── main.py                 # FastAPI app initialization
├── api/
│   ├── __init__.py
│   ├── presets.py          # Preset management endpoints
│   ├── comfyui.py          # ComfyUI proxy endpoints
│   ├── models.py           # Model status endpoints
│   ├── workflows.py        # Workflow management
│   └── websocket.py        # WebSocket for real-time updates
├── core/
│   ├── config.py           # Configuration management
│   ├── downloader.py       # Background download manager
│   └── comfyui_client.py   # ComfyUI API client
├── static/
│   ├── css/
│   │   └── styles.css      # Tailwind output
│   └── js/
│       └── app.js          # Alpine.js components
├── templates/
│   ├── base.html           # Base template
│   ├── index.html          # Home section
│   ├── models.html         # Models section
│   ├── workflows.html      # Workflows section
│   └── settings.html       # Settings section
└── requirements.txt
```

### API Endpoints

#### Preset Management
- `GET /api/presets/` - List all presets
- `GET /api/presets/{preset_id}` - Get preset details
- `POST /api/presets/{preset_id}/install` - Install preset
- `DELETE /api/presets/{preset_id}` - Uninstall preset
- `GET /api/presets/{preset_id}/status` - Get installation status

#### Model Management
- `GET /api/models/` - List installed models
- `DELETE /api/models/` - Delete models
- `GET /api/models/types` - List model types

#### ComfyUI Integration
- `GET /api/comfyui/health` - Check ComfyUI health
- `POST /api/comfyui/execute` - Execute workflow
- `GET /api/comfyui/queue` - Get queue status
- `DELETE /api/comfyui/queue` - Clear queue

#### System Status
- `GET /api/system/status` - Get system status
- `GET /api/system/storage` - Get storage information

---

## Startup Flow

### Phases

```
┌─────────────────────────────────────────────────────────────────┐
│ Container Start                                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Phase 1: Volume Health Check (Target: 5 seconds)                │
├─────────────────────────────────────────────────────────────────┤
│ 1. Verify /workspace mount point                               │
│ 2. Test write access                                           │
│ 3. Create directory structure                                  │
│ 4. Check network volume connectivity                           │
└────────────────────────┬────────────────────────────────────────┘
                         │ [PASS]
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Phase 2: Configuration Generation (Target: 3 seconds)           │
├─────────────────────────────────────────────────────────────────┤
│ 1. Generate extra_model_paths.yaml                            │
│ 2. Validate configuration                                      │
│ 3. Create legacy compatibility symlinks (optional)             │
└────────────────────────┬────────────────────────────────────────┘
                         │ [PASS]
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Phase 3: Service Initialization (Target: 15 seconds)            │
├─────────────────────────────────────────────────────────────────┤
│ 1. Start Nginx (2 seconds)                                     │
│ 2. Start ComfyUI (8 seconds)                                   │
│ 3. Start Dashboard FastAPI (3 seconds)                         │
│ 4. Start Preset Manager (2 seconds)                            │
└────────────────────────┬────────────────────────────────────────┘
                         │ [PASS]
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Phase 4: Health Checks (Target: 5 seconds)                      │
├─────────────────────────────────────────────────────────────────┤
│ 1. Dashboard Health Check                                      │
│ 2. ComfyUI Health Check                                        │
│ 3. Volume Health Check                                         │
│ 4. Service Connectivity Check                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │ [ALL PASS]
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ READY STATE (<30 seconds total)                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Startup Performance

| Phase | Target | Measurement |
|-------|--------|-------------|
| Volume Health Check | 5s | ~3-5s |
| Config Generation | 3s | ~2-3s |
| Service Initialization | 15s | ~12-15s |
| Health Checks | 5s | ~3-5s |
| **Total** | **30s** | **~25-30s** |

---

## API Architecture

### REST API

All REST endpoints return JSON unless otherwise specified.

**Base URL**: `http://localhost:8080/api`

**Authentication**: Optional Bearer token or session-based

### WebSocket Protocol

**Endpoint**: `ws://localhost:8080/ws`

**Message Format**: All messages are JSON objects with a `type` field.

#### Client → Server Messages

```json
{
  "type": "subscribe",
  "channels": ["downloads", "queue", "system"]
}
```

#### Server → Client Messages

```json
{
  "type": "download_progress",
  "data": {
    "preset_id": "WAN_22_5B_TIV2",
    "progress": 45.2,
    "speed": "125 MB/s",
    "eta": "2m 30s"
  }
}
```

---

## Data Flows

### Preset Download Flow

```
User clicks "Install" → Dashboard Frontend
       ↓
POST /api/presets/{id}/install → Dashboard Backend
       ↓
Create download task → Download Orchestrator
       ↓
Parse preset configuration → Load from presets.yaml
       ↓
Create download queue → Prioritize files by dependencies
       ↓
Execute downloads (async) → Download from HuggingFace/Direct URLs
       ↓
Real-time progress updates → WebSocket broadcast
       ↓
Completion notification → Update UI
```

### Workflow Execution Flow

```
User submits workflow → Dashboard Frontend
       ↓
Validate workflow → Check required models
       ↓
POST /api/comfyui/execute → ComfyUI Bridge
       ↓
Transform workflow → ComfyUI format
       ↓
Submit to ComfyUI → POST /prompt
       ↓
Stream progress → WebSocket updates
       ↓
Retrieve outputs → GET /history/{prompt_id}
       ↓
Display results → Dashboard UI
```

---

## Component Diagram

### Service Communication

```
┌─────────────────┐          ┌─────────────────┐
│   Dashboard     │          │     ComfyUI     │
│   (FastAPI)     │          │   (Python)      │
└────────┬────────┘          └────────┬────────┘
         │                            │
         │ HTTP API                   │
         ├─ GET /health               │
         ├─ POST /prompt              │
         ├─ GET /queue                │
         │                            │
         │ WebSocket                  │
         ├─ ws://localhost:3000/ws    │
         │  └─ Queue updates          │
         │  └─ Execution progress     │
         │                            │
         │ Shared Resources           │
         └─ /workspace/models/  ◄────┘
            (via extra_model_paths.yaml)
```

---

## Technology Stack

### Backend Technologies

| Component | Technology | Version |
|-----------|------------|---------|
| **Runtime** | Python | 3.13 |
| **Web Framework** | FastAPI | 0.110+ |
| **ASGI Server** | Uvicorn | 0.27+ |
| **WebSocket** | FastAPI WebSockets | Built-in |
| **HTTP Client** | aiohttp | 3.9+ |
| **Template Engine** | Jinja2 | 3.1+ |
| **Configuration** | PyYAML | 6.0+ |
| **Task Queue** | asyncio + BackgroundTasks | Built-in |

### Frontend Technologies

| Component | Technology | Version | Bundle Size |
|-----------|------------|---------|-------------|
| **Base Framework** | htmx | 1.9+ | ~14KB |
| **Reactivity** | Alpine.js | 3.13+ | ~15KB |
| **Styling** | Tailwind CSS | 3.4+ | ~20KB (compiled) |
| **Icons** | Phosphor Icons | 2.0+ | ~5KB |
| **Total** | | | ~50KB |

### Infrastructure Technologies

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Container Runtime** | Docker | Containerization |
| **Base Image** | NVIDIA CUDA | GPU support |
| **Reverse Proxy** | Nginx | Service routing |
| **Package Manager** | UV | Fast Python installs |
| **Cloud Platform** | RunPod | GPU hosting |

---

## Performance Optimizations

### Startup Optimizations

| Optimization | Impact |
|--------------|--------|
| **Eliminate rsync** | Save 60-120s |
| **Pre-built venv** | Instant Python env |
| **Compiled frontend** | No runtime compilation |
| **Parallel service starts** | Reduce initialization time |
| **Health check caching** | Faster ready state |
| **Lazy loading** | Load components on demand |

### Runtime Optimizations

| Optimization | Impact |
|--------------|--------|
| **WebSocket for updates** | Reduce HTTP polling |
| **Background downloads** | Non-blocking UI |
| **Chunked transfers** | Better memory usage |
| **Asset caching** | Reduce bandwidth |
| **GPU memory monitoring** | Prevent OOM |
| **Connection pooling** | Faster API calls |

---

## Security Considerations

### Authentication & Authorization

| Feature | Implementation |
|---------|----------------|
| **Dashboard Auth** | Optional password protection |
| **API Authentication** | Bearer token support |
| **Session Management** | Secure cookie handling |
| **CORS Configuration** | Controlled cross-origin access |

### Network Security

| Feature | Implementation |
|---------|----------------|
| **HTTPS Support** | SSL/TLS termination |
| **WebSocket Security** | WSS protocol |
| **Input Validation** | All API endpoints |
| **File Access Control** | Restricted to /workspace |
| **Secret Management** | Environment variables |

---

## Monitoring & Observability

### Metrics Collection

```python
# System Metrics
- CPU usage (per core)
- Memory usage (used/total)
- GPU usage (utilization, memory)
- Disk usage (workspace, volume)
- Network I/O

# Application Metrics
- Request latency
- WebSocket connections
- Active downloads
- Queue depth
- Error rates

# Business Metrics
- Presets installed
- Workflows executed
- Models downloaded
- Storage consumed
```

### Logging Strategy

```
# Log Levels
- DEBUG: Detailed diagnostic information
- INFO: General informational messages
- WARNING: Warning messages for potential issues
- ERROR: Error messages for failures
- CRITICAL: Critical issues requiring immediate attention

# Log Destinations
- /workspace/logs/dashboard.log
- /workspace/logs/downloads.log
- /workspace/logs/comfyui_bridge.log
- /workspace/logs/startup.log

# Log Rotation
- Daily rotation
- 7-day retention
- Compressed archives
```

---

## Conclusion

The ComfyUI-Docker v2.0 architecture transforms the application into an instant-on, unified dashboard experience with:

1. **Instant Startup** - Eliminate rsync bottleneck with native extra_model_paths.yaml
2. **Unified Dashboard** - Single interface for all operations with htmx + Alpine.js
3. **Background Processing** - Non-blocking preset downloads with real-time progress
4. **Persistent Storage** - Network volume integration for models and workflows
5. **Scalable Design** - Support for multiple pods and vertical scaling

The architecture is designed for production deployment on RunPod with focus on developer experience, operational simplicity, and end-user productivity.

---

*Document Version: 2.0.0*
*Last Updated: 2026-02-15*
*Author: Architecture Team*
