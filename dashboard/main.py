"""
FastAPI application for ComfyUI Unified Dashboard
Main entry point with router initialization and middleware setup
"""

import os
import json
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

from .api import api_router
from .core.config import settings
from .core.websocket import ConnectionManager
from .core.generation_manager import generation_manager


# WebSocket connection manager for real-time updates
manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events"""
    # Startup
    print("Starting ComfyUI Unified Dashboard...")

    # Initialize database and persistence
    from .core.persistence import init_persistence
    init_persistence()
    print("Database initialized")

    print(f"Dashboard URL: http://localhost:{settings.DASHBOARD_PORT}")
    print(f"ComfyUI API: http://localhost:{settings.COMFYUI_PORT}")

    # Create necessary directories
    from pathlib import Path
    Path(settings.WORKFLOW_BASE_PATH).mkdir(parents=True, exist_ok=True)
    Path(settings.BASE_DIR).mkdir(parents=True, exist_ok=True)
    print(f"Workflow directory: {settings.WORKFLOW_BASE_PATH}")

    yield
    # Shutdown
    print("Shutting down ComfyUI Unified Dashboard...")


# Initialize FastAPI application
app = FastAPI(
    title="ComfyUI Unified Dashboard",
    description="Unified management interface for ComfyUI with preset management, model downloads, and workflow execution",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
BASE_DIR = Path(__file__).resolve().parent.parent
static_dir = BASE_DIR / "dashboard" / "static"
templates_dir = BASE_DIR / "dashboard" / "templates"

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))

# Include API routers
app.include_router(api_router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Render main dashboard interface"""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "ComfyUI Unified Dashboard",
            "comfyui_url": f"http://localhost:{settings.COMFYUI_PORT}",
            "api_base": "/api"
        }
    )


@app.get("/generate", response_class=HTMLResponse)
async def generate_page(request: Request):
    """Render generation interface"""
    return templates.TemplateResponse(
        "generate.html",
        {
            "request": request,
            "title": "Generate - ComfyUI Dashboard",
            "comfyui_url": f"http://localhost:{settings.COMFYUI_PORT}",
            "api_base": "/api"
        }
    )


@app.get("/models", response_class=HTMLResponse)
async def models_page(request: Request):
    """Render models management interface"""
    return templates.TemplateResponse(
        "models.html",
        {
            "request": request,
            "title": "Models - ComfyUI Dashboard",
            "comfyui_url": f"http://localhost:{settings.COMFYUI_PORT}",
            "api_base": "/api"
        }
    )


@app.get("/workflows", response_class=HTMLResponse)
async def workflows_page(request: Request):
    """Render workflows management interface"""
    return templates.TemplateResponse(
        "workflows.html",
        {
            "request": request,
            "title": "Workflows - ComfyUI Dashboard",
            "comfyui_url": f"http://localhost:{settings.COMFYUI_PORT}",
            "api_base": "/api"
        }
    )


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Render settings interface"""
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "title": "Settings - ComfyUI Dashboard",
            "comfyui_url": f"http://localhost:{settings.COMFYUI_PORT}",
            "api_base": "/api"
        }
    )


@app.get("/gallery", response_class=HTMLResponse)
async def gallery_page(request: Request):
    """Render gallery interface"""
    return templates.TemplateResponse(
        "gallery.html",
        {
            "request": request,
            "title": "Gallery - ComfyUI Dashboard",
            "comfyui_url": f"http://localhost:{settings.COMFYUI_PORT}",
            "api_base": "/api"
        }
    )


@app.get("/storage", response_class=HTMLResponse)
async def storage_page(request: Request):
    """Render storage management interface"""
    return templates.TemplateResponse(
        "storage.html",
        {
            "request": request,
            "title": "Storage Management - ComfyUI Dashboard",
            "comfyui_url": f"http://localhost:{settings.COMFYUI_PORT}",
            "api_base": "/api"
        }
    )


@app.get("/pro", response_class=HTMLResponse)
async def pro_page(request: Request):
    """Render pro/features interface"""
    return templates.TemplateResponse(
        "pro.html",
        {
            "request": request,
            "title": "Pro Features - ComfyUI Dashboard",
            "comfyui_url": f"http://localhost:{settings.COMFYUI_PORT}",
            "api_base": "/api"
        }
    )


@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration"""
    return {
        "status": "healthy",
        "service": "comfyui-dashboard",
        "version": "1.0.0"
    }


@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics for the home page"""
    from pathlib import Path
    import shutil

    stats = {
        "totalGenerations": 0,
        "modelsInstalled": 0,
        "storageUsed": "0 GB",
        "activeWorkflows": 0
    }

    try:
        # Count models
        model_path = Path(settings.MODEL_BASE_PATH)
        if model_path.exists():
            model_count = 0
            total_size = 0
            for model_file in model_path.rglob("*"):
                if model_file.is_file() and model_file.suffix in ['.safetensors', '.ckpt', '.pt', '.pth', '.bin']:
                    model_count += 1
                    total_size += model_file.stat().st_size

            stats["modelsInstalled"] = model_count

            # Convert to GB
            size_gb = total_size / (1024 ** 3)
            if size_gb < 1:
                stats["storageUsed"] = f"{total_size / (1024 ** 2):.1f} MB"
            else:
                stats["storageUsed"] = f"{size_gb:.1f} GB"

        # Count workflows
        workflow_path = Path(settings.WORKFLOW_BASE_PATH)
        if workflow_path.exists():
            workflow_count = len(list(workflow_path.rglob("*.json")))
            stats["activeWorkflows"] = workflow_count

        # Get generation count from ComfyUI history
        try:
            from .core.comfyui_client import ComfyUIClient
            client = ComfyUIClient(base_url=f"http://localhost:{settings.COMFYUI_PORT}")
            history = await client.get_history()
            stats["totalGenerations"] = len(history)
        except Exception:
            pass

    except Exception as e:
        print(f"Error getting dashboard stats: {e}")

    return stats


@app.post("/api/generate")
async def generate_content(request: Request):
    """Handle generation requests from the UI"""
    from pydantic import BaseModel
    from typing import Optional, Dict, Any

    class GenerateRequest(BaseModel):
        model: str
        mode: str
        prompt: str
        negative_prompt: Optional[str] = ""
        settings: Optional[Dict[str, Any]] = {}
        input_image: Optional[str] = None

    try:
        data = await request.json()
        generate_req = GenerateRequest(**data)

        # Queue the generation with ComfyUI
        from .core.comfyui_client import ComfyUIClient
        client = ComfyUIClient(base_url=f"http://localhost:{settings.COMFYUI_PORT}")

        # Create a simple workflow based on mode
        # This is a placeholder - real implementation would load appropriate workflow
        workflow = {
            "prompt": generate_req.prompt,
            "negative_prompt": generate_req.negative_prompt,
            "model": generate_req.model,
            "mode": generate_req.mode,
            "settings": generate_req.settings
        }

        # For now, return success with a fake prompt_id
        # Real implementation would call ComfyUI API
        return {
            "status": "queued",
            "prompt_id": f"gen_{int(__import__('time').time())}",
            "message": "Generation queued successfully"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@app.get("/api/gallery/recent")
async def get_recent_generations(limit: int = 20):
    """Get recent generations for the gallery"""
    from pathlib import Path

    output_path = Path(settings.BASE_DIR) / "output"
    generations = []

    if output_path.exists():
        # Get recent output files
        for i, file in enumerate(sorted(output_path.rglob("*"), key=lambda x: x.stat().st_mtime, reverse=True)):
            if file.is_file() and file.suffix in ['.png', '.jpg', '.jpeg', '.webp', '.mp4']:
                generations.append({
                    "id": f"gen_{i}",
                    "thumbnail": f"/output/{file.relative_to(output_path)}",
                    "output": f"/output/{file.relative_to(output_path)}",
                    "timestamp": file.stat().st_mtime
                })
                if len(generations) >= limit:
                    break

    return {"generations": generations}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back or handle incoming messages
            await manager.broadcast(f"Received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    """WebSocket endpoint for dashboard real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle dashboard-specific messages
            message = json.loads(data) if data.startswith('{') else {"type": "message", "data": data}
            await manager.broadcast(json.dumps({
                "type": message.get("type", "update"),
                "data": message.get("data", data)
            }))
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.websocket("/ws/downloads")
async def downloads_websocket(websocket: WebSocket):
    """WebSocket endpoint for download progress updates"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle download-specific messages
            await manager.broadcast(json.dumps({
                "type": "download_update",
                "data": data
            }))
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.websocket("/ws/generate")
async def websocket_generate(websocket: WebSocket):
    """WebSocket for real-time generation updates."""
    await websocket.accept()
    generation_manager.register_connection(websocket)

    try:
        # Send initial state
        await websocket.send_text(json.dumps({
            "type": "connected",
            "active_generations": generation_manager.get_active()
        }))

        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            # Handle any client messages if needed
            try:
                message = json.loads(data)
                # Echo back for keepalive
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        pass


# Expose connection manager for use in other modules
@app.get("/ws/connections")
async def get_active_connections():
    """Get count of active WebSocket connections"""
    return {
        "active_connections": len(manager.active_connections)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "dashboard.main:app",
        host="0.0.0.0",
        port=settings.DASHBOARD_PORT,
        reload=True
    )
