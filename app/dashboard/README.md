# ComfyUI Unified Dashboard - FastAPI Backend

FastAPI-based backend for the ComfyUI Unified Dashboard, providing REST API endpoints for preset management, model downloads, workflow execution, and system monitoring.

## Features

- **Preset Management**: Browse, install, and manage AI model presets
- **Model Management**: View installed models with disk usage information
- **Workflow Execution**: Execute ComfyUI workflows via REST API
- **System Monitoring**: Real-time system resource monitoring
- **WebSocket Support**: Live updates for downloads and system status
- **Async/Await**: Full async support for high-performance operations

## Installation

```bash
pip install -r requirements.txt
```

## Running the Dashboard

```bash
# Development mode with auto-reload
uvicorn app.dashboard.main:app --reload --host 0.0.0.0 --port 8080

# Production mode
uvicorn app.dashboard.main:app --host 0.0.0.0 --port 8080 --workers 4
```

## API Endpoints

### Presets

- `GET /api/presets/` - List all presets (with optional category/type filtering)
- `GET /api/presets/{preset_id}` - Get specific preset details
- `POST /api/presets/{preset_id}/download` - Start preset download
- `GET /api/presets/{preset_id}/status` - Get preset installation status
- `DELETE /api/presets/{preset_id}` - Delete preset files

### Models

- `GET /api/models/` - List all installed models
- `GET /api/models/validate` - Validate model files
- `GET /api/models/disk-usage` - Get disk usage information
- `GET /api/models/types` - List model types/directories

### Workflows

- `GET /api/workflows/` - List available workflows
- `GET /api/workflows/{workflow_name}` - Get specific workflow
- `POST /api/workflows/execute` - Execute a workflow
- `GET /api/workflows/queue/status` - Get queue status
- `GET /api/workflows/history` - Get execution history

### System

- `GET /api/system/status` - Get overall system status
- `GET /api/system/resources` - Get resource usage
- `GET /api/system/logs` - Get system logs
- `GET /api/system/config` - Get system configuration

## WebSocket Endpoints

- `WS /ws` - Main WebSocket for general updates
- `WS /ws/downloads` - Download progress updates

## Configuration

Environment variables can be set in `/workspace/.env`:

```
DASHBOARD_PORT=8080
COMFYUI_PORT=3000
MODEL_BASE_PATH=/workspace/ComfyUI/models
PRESET_CONFIG_PATH=/workspace/config/presets.yaml
WORKFLOW_BASE_PATH=/workspace/ComfyUI/workflows
```

## Architecture

```
app/dashboard/
├── main.py              # FastAPI application entry point
├── api/
│   ├── __init__.py      # API router initialization
│   ├── presets.py       # Preset management endpoints
│   ├── models.py        # Model management endpoints
│   ├── workflows.py     # Workflow execution endpoints
│   ├── system.py        # System status endpoints
│   └── websocket.py     # WebSocket handlers
├── core/
│   ├── __init__.py      # Core module exports
│   ├── config.py        # Configuration management
│   ├── downloader.py    # Background download manager
│   └── comfyui_client.py # ComfyUI API client
├── templates/           # Jinja2 templates
└── static/             # Static assets
```

## Development

The dashboard uses:
- **FastAPI**: Modern async web framework
- **Pydantic**: Data validation and settings management
- **Jinja2**: Template rendering
- **aiohttp**: Async HTTP client for ComfyUI communication
- **psutil**: System resource monitoring

## Frontend Integration

The backend provides a simple HTML/JS frontend using:
- **Alpine.js**: Reactive frontend framework
- **Tailwind CSS**: Utility-first CSS framework
- **HTMX**: Enhanced HTML interactions
- **WebSocket API**: Real-time updates

## License

MIT License - See LICENSE file for details
