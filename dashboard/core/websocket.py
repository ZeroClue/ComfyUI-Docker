"""
WebSocket handlers for real-time updates
Handles live download progress, queue status, and system metrics
"""

import json
import asyncio
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

from .config import settings
from .comfyui_client import ComfyUIClient


class ConnectionManager:
    """Manages WebSocket connections and broadcasts"""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "general": set(),
            "downloads": set(),
            "queue": set(),
            "system": set()
        }

    async def connect(self, websocket: WebSocket, channel: str = "general"):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)

    def disconnect(self, websocket: WebSocket, channel: str = "general"):
        """Remove a WebSocket connection"""
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)

    async def broadcast(self, message: str, channel: str = "general"):
        """Broadcast a message to all connections in a channel"""
        if channel in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[channel]:
                try:
                    await connection.send_text(message)
                except Exception:
                    disconnected.add(connection)

            # Clean up disconnected connections
            for connection in disconnected:
                self.active_connections[channel].discard(connection)

    async def send_personal(self, message: str, websocket: WebSocket):
        """Send a message to a specific connection"""
        try:
            await websocket.send_text(message)
        except Exception:
            pass


# Global connection manager instance
manager = ConnectionManager()
comfyui_client = ComfyUIClient(base_url=f"http://localhost:{settings.COMFYUI_PORT}")


async def broadcast_download_progress(preset_id: str, progress_data: Dict):
    """Broadcast download progress updates"""
    message = json.dumps({
        "type": "download_progress",
        "preset_id": preset_id,
        "timestamp": datetime.utcnow().isoformat(),
        "data": progress_data
    })
    await manager.broadcast(message, channel="downloads")


async def broadcast_queue_status():
    """Broadcast queue status updates"""
    try:
        status = await comfyui_client.get_queue_status()
        message = json.dumps({
            "type": "queue_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "queue_running": status.get("queue_running", []),
                "queue_pending": status.get("queue_pending", []),
                "queue_remaining": len(status.get("queue_pending", []))
            }
        })
        await manager.broadcast(message, channel="queue")
    except Exception as e:
        print(f"Error broadcasting queue status: {e}")


async def broadcast_system_metrics():
    """Broadcast system metrics updates"""
    try:
        import psutil

        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        message = json.dumps({
            "type": "system_metrics",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "memory_used": memory.used,
                "memory_total": memory.total,
                "disk_used": disk.used,
                "disk_total": disk.total
            }
        })
        await manager.broadcast(message, channel="system")
    except Exception as e:
        print(f"Error broadcasting system metrics: {e}")


async def start_background_broadcasters():
    """Start background tasks for broadcasting updates"""
    # Queue status broadcaster (every 2 seconds)
    async def queue_broadcaster():
        while True:
            await broadcast_queue_status()
            await asyncio.sleep(2)

    # System metrics broadcaster (every 5 seconds)
    async def metrics_broadcaster():
        while True:
            await broadcast_system_metrics()
            await asyncio.sleep(5)

    # Start background tasks
    asyncio.create_task(queue_broadcaster())
    asyncio.create_task(metrics_broadcaster())
