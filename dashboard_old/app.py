#!/usr/bin/env python3
"""
ComfyUI-Docker Unified Dashboard

FastAPI backend with htmx/Alpine.js frontend for managing ComfyUI containers.
Provides real-time updates via WebSocket and authentication system.
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Request, Response, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.websockets import WebSocketState
import uvicorn

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Configuration
SECRET_KEY = os.environ.get("DASHBOARD_SECRET_KEY", "dev-secret-key-change-in-production")
ACCESS_PASSWORD = os.environ.get("ACCESS_PASSWORD", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")
SESSION_TIMEOUT = int(os.environ.get("SESSION_TIMEOUT_HOURS", "24"))

# Dashboard configuration
DASHBOARD_PORT = int(os.environ.get("DASHBOARD_PORT", "8081"))
DASHBOARD_HOST = os.environ.get("DASHBOARD_HOST", "0.0.0.0")

# Initialize FastAPI
app = FastAPI(
    title="ComfyUI-Docker Dashboard",
    description="Unified dashboard for ComfyUI-Docker container management",
    version="2.0.0"
)

# Session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    max_age=SESSION_TIMEOUT * 3600,
    session_cookie="dashboard_session",
    same_site="lax"
)

# Templates and static files
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

# WebSocket connection manager
class ConnectionManager:
    """Manage WebSocket connections for real-time updates"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.presets_downloads: Dict[str, Dict] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if self.active_connections:
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)

            # Remove disconnected clients
            for conn in disconnected:
                self.active_connections.remove(conn)

    async def send_personal(self, message: Dict[str, Any], websocket: WebSocket):
        """Send message to specific client"""
        try:
            await websocket.send_json(message)
        except Exception:
            pass

manager = ConnectionManager()


# Authentication dependency
def get_current_user(request: Request) -> Optional[str]:
    """Get authenticated user from session"""
    return request.session.get("user")


def require_auth(request: Request) -> str:
    """Require authentication, raise exception if not authenticated"""
    user = request.session.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user


def require_admin(request: Request) -> str:
    """Require admin authentication"""
    user = request.session.get("user")
    if not user or user != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


# Routes

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Dashboard home page"""
    # If not authenticated, show login page
    if not request.session.get("user"):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "title": "Login - ComfyUI Dashboard"}
        )

    # Authenticated users see dashboard
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "title": "ComfyUI-Docker Dashboard",
            "user": request.session.get("user"),
            "is_admin": request.session.get("user") == "admin"
        }
    )


@app.post("/api/auth/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Handle login authentication"""
    # Check credentials
    valid_user = False
    user_role = "user"

    # Admin login
    if username == "admin" and password == ADMIN_PASSWORD:
        valid_user = True
        user_role = "admin"
    # Regular user login with ACCESS_PASSWORD
    elif password == ACCESS_PASSWORD:
        valid_user = True
        user_role = "user"

    if valid_user:
        request.session["user"] = user_role
        request.session["login_time"] = datetime.now().isoformat()

        # Return HTMX redirect to dashboard
        return HTMLResponse(
            '<html><body hx-get="/" hx-trigger="load" hx-swap="outerHTML"></body></html>'
        )

    # Login failed
    return HTMLResponse(
        '<div class="alert alert-error">Invalid credentials</div>',
        status_code=status.HTTP_401_UNAUTHORIZED
    )


@app.post("/api/auth/logout")
async def logout(request: Request):
    """Handle logout"""
    request.session.clear()
    return HTMLResponse(
        '<html><body hx-get="/" hx-trigger="load" hx-swap="outerHTML"></body></html>'
    )


@app.get("/api/status")
async def get_status(user: str = Depends(require_auth)):
    """Get current system status"""
    # Check ComfyUI status
    comfyui_running = False
    try:
        import subprocess
        result = subprocess.run(
            ["pgrep", "-f", "python.*main.py"],
            capture_output=True,
            text=True
        )
        comfyui_running = result.returncode == 0
    except Exception:
        pass

    # Check preset downloads
    progress_file = Path("/tmp/preset_download_progress.json")
    preset_progress = {}
    if progress_file.exists():
        try:
            with open(progress_file) as f:
                preset_progress = json.load(f)
        except Exception:
            pass

    # Calculate summary
    total_presets = len(preset_progress)
    completed = sum(1 for p in preset_progress.values() if p.get("status") == "completed")
    failed = sum(1 for p in preset_progress.values() if p.get("status") == "failed")

    return {
        "comfyui_running": comfyui_running,
        "preset_downloads": {
            "total": total_presets,
            "completed": completed,
            "failed": failed,
            "progress": preset_progress
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/presets")
async def list_presets(user: str = Depends(require_auth)):
    """List available presets"""
    try:
        sys.path.append(str(Path(__file__).parent.parent / "scripts"))
        from generate_download_scripts import DownloadScriptGenerator

        generator = DownloadScriptGenerator()
        presets = generator.load_presets()

        # Group by category
        categories = {}
        for preset_id, preset_data in presets.items():
            category = preset_data.get("category", "Unknown")
            if category not in categories:
                categories[category] = []
            categories[category].append({
                "id": preset_id,
                "name": preset_data.get("name", preset_id),
                "type": preset_data.get("type", "unknown"),
                "size": preset_data.get("download_size", "Unknown"),
                "files": len(preset_data.get("files", [])),
                "description": preset_data.get("description", "")
            })

        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/presets/{preset_id}")
async def get_preset_detail(preset_id: str, user: str = Depends(require_auth)):
    """Get details for a specific preset"""
    try:
        sys.path.append(str(Path(__file__).parent.parent / "scripts"))
        from generate_download_scripts import DownloadScriptGenerator

        generator = DownloadScriptGenerator()
        presets = generator.load_presets()

        if preset_id not in presets:
            raise HTTPException(status_code=404, detail="Preset not found")

        preset_data = presets[preset_id]
        return {
            "id": preset_id,
            **preset_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/presets/{preset_id}/download")
async def download_preset(preset_id: str, user: str = Depends(require_admin)):
    """Trigger download of a specific preset"""
    try:
        import subprocess

        # Run unified preset downloader in background
        cmd = [
            sys.executable,
            str(Path(__file__).parent.parent / "scripts" / "unified_preset_downloader.py"),
            "download",
            "--presets", preset_id,
            "--background"
        ]

        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Notify WebSocket clients
        await manager.broadcast({
            "type": "download_started",
            "preset_id": preset_id,
            "timestamp": datetime.now().isoformat()
        })

        return {"status": "started", "preset_id": preset_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/services")
async def get_services(user: str = Depends(require_auth)):
    """Get status of all services"""
    services = {}

    # Check each service
    service_ports = {
        "ComfyUI": 3000,
        "Preset Manager": 9000,
        "Code Server": 8080,
        "JupyterLab": 8888,
        "Studio": 5000
    }

    for service, port in service_ports.items():
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(("127.0.0.1", port))
            services[service] = {
                "running": result == 0,
                "port": port
            }
            sock.close()
        except Exception:
            services[service] = {
                "running": False,
                "port": port
            }

    return services


@app.get("/api/logs/{service}")
async def get_logs(service: str, user: str = Depends(require_admin), lines: int = 100):
    """Get logs for a specific service"""
    log_files = {
        "comfyui": "/workspace/logs/comfyui.log",
        "preset_manager": "/workspace/logs/preset_manager.log",
        "preset_downloads": "/workspace/logs/preset_downloads.log",
        "studio": "/workspace/logs/comfyui_studio.log",
        "jupyter": "/workspace/logs/jupyterlab.log",
        "code_server": "/workspace/logs/code-server.log"
    }

    log_file = log_files.get(service)
    if not log_file:
        raise HTTPException(status_code=404, detail="Unknown service")

    try:
        result = subprocess.run(
            ["tail", "-n", str(lines), log_file],
            capture_output=True,
            text=True
        )

        return {
            "service": service,
            "logs": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)

    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to ComfyUI-Docker Dashboard",
            "timestamp": datetime.now().isoformat()
        })

        # Handle incoming messages
        while True:
            data = await websocket.receive_json()

            # Handle different message types
            if data.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })

            elif data.get("type") == "subscribe":
                # Subscribe to specific updates
                await websocket.send_json({
                    "type": "subscribed",
                    "channel": data.get("channel", "all"),
                    "timestamp": datetime.now().isoformat()
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# Background task to broadcast updates
async def broadcast_preset_progress():
    """Broadcast preset download progress updates"""
    progress_file = Path("/tmp/preset_download_progress.json")
    last_progress = None

    while True:
        await asyncio.sleep(2)

        try:
            if progress_file.exists():
                with open(progress_file) as f:
                    current_progress = json.load(f)

                # Only broadcast if changed
                if current_progress != last_progress:
                    await manager.broadcast({
                        "type": "preset_progress",
                        "data": current_progress,
                        "timestamp": datetime.now().isoformat()
                    })
                    last_progress = current_progress
        except Exception as e:
            print(f"Error broadcasting progress: {e}")


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize background tasks"""
    # Start preset progress broadcaster
    asyncio.create_task(broadcast_preset_progress())

    print(f"ComfyUI-Docker Dashboard starting on http://{DASHBOARD_HOST}:{DASHBOARD_PORT}")
    print(f"Authentication: {'ENABLED' if ACCESS_PASSWORD else 'DISABLED (insecure!)'}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("ComfyUI-Docker Dashboard shutting down...")


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "connections": len(manager.active_connections)
    }


# Templates for partials
@app.get("/partials/services-panel", response_class=HTMLResponse)
async def services_panel(request: Request, user: str = Depends(require_auth)):
    """Services status panel partial"""
    services = await get_services(user)

    return templates.TemplateResponse(
        "partials/services_panel.html",
        {
            "request": request,
            "services": services,
            "user": user
        }
    )


@app.get("/partials/presets-panel", response_class=HTMLResponse)
async def presets_panel(request: Request, user: str = Depends(require_auth)):
    """Presets panel partial"""
    presets_data = await list_presets(user)

    return templates.TemplateResponse(
        "partials/presets_panel.html",
        {
            "request": request,
            "categories": presets_data["categories"],
            "user": user
        }
    )


@app.get("/partials/downloads-panel", response_class=HTMLResponse)
async def downloads_panel(request: Request, user: str = Depends(require_auth)):
    """Downloads status panel partial"""
    status = await get_status(user)

    return templates.TemplateResponse(
        "partials/downloads_panel.html",
        {
            "request": request,
            "status": status,
            "user": user
        }
    )


def main():
    """Run the dashboard server"""
    uvicorn.run(
        "app:app",
        host=DASHBOARD_HOST,
        port=DASHBOARD_PORT,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
