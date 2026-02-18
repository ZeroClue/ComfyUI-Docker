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


# WebSocket connection manager for real-time updates
manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events"""
    # Startup
    print("Starting ComfyUI Unified Dashboard...")
    print(f"Dashboard URL: http://localhost:{settings.DASHBOARD_PORT}")
    print(f"ComfyUI API: http://localhost:{settings.COMFYUI_PORT}")
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
