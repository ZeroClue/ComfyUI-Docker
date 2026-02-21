"""
Generation Manager
Manages active generations and broadcasts progress via WebSocket.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
import weakref


@dataclass
class ActiveGeneration:
    """Tracks an active generation."""
    prompt_id: str
    workflow_name: str
    workflow_id: str
    prompt: str
    status: str = "running"
    progress: float = 0.0
    current_node: str = ""
    started_at: datetime = field(default_factory=datetime.now)
    eta_seconds: int = 0


class GenerationManager:
    """Manages generations and WebSocket broadcasts."""

    def __init__(self):
        self.active_generations: Dict[str, ActiveGeneration] = {}
        self.connections: Set = weakref.WeakSet()
        self._comfyui_client = None

    @property
    def comfyui_client(self):
        """Lazy load ComfyUI client."""
        if self._comfyui_client is None:
            from .comfyui_client import ComfyUIClient
            from .config import settings
            self._comfyui_client = ComfyUIClient(base_url=f"http://localhost:{settings.COMFYUI_PORT}")
        return self._comfyui_client

    def register_connection(self, websocket):
        """Register a WebSocket connection."""
        self.connections.add(websocket)

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """Broadcast event to all connected clients."""
        message = json.dumps({
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            **data
        })

        dead_connections = set()
        for ws in self.connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead_connections.add(ws)

        # Clean up dead connections
        for ws in dead_connections:
            self.connections.discard(ws)

    async def start_generation(self, prompt_id: str, workflow_id: str, workflow_name: str, prompt: str):
        """Start tracking a generation."""
        generation = ActiveGeneration(
            prompt_id=prompt_id,
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            prompt=prompt,
            status="running"
        )
        self.active_generations[prompt_id] = generation

        await self.broadcast("generation_started", {
            "prompt_id": prompt_id,
            "workflow_id": workflow_id,
            "workflow_name": workflow_name
        })

    async def update_progress(self, prompt_id: str, progress: float, current_node: str = "", eta: int = 0):
        """Update generation progress."""
        if prompt_id in self.active_generations:
            gen = self.active_generations[prompt_id]
            gen.progress = progress
            gen.current_node = current_node
            gen.eta_seconds = eta

            await self.broadcast("generation_progress", {
                "prompt_id": prompt_id,
                "progress": progress,
                "current_node": current_node,
                "eta": eta
            })

    async def complete_generation(self, prompt_id: str, outputs: List[str]):
        """Mark generation as complete."""
        if prompt_id in self.active_generations:
            gen = self.active_generations[prompt_id]
            gen.status = "completed"
            gen.progress = 100.0

            await self.broadcast("generation_complete", {
                "prompt_id": prompt_id,
                "outputs": outputs,
                "duration_seconds": (datetime.now() - gen.started_at).total_seconds()
            })

            # Remove after a delay
            await asyncio.sleep(60)
            self.active_generations.pop(prompt_id, None)

    async def fail_generation(self, prompt_id: str, error: str):
        """Mark generation as failed."""
        if prompt_id in self.active_generations:
            gen = self.active_generations[prompt_id]
            gen.status = "failed"

            await self.broadcast("generation_error", {
                "prompt_id": prompt_id,
                "error": error
            })

            # Remove after a delay
            await asyncio.sleep(60)
            self.active_generations.pop(prompt_id, None)

    def get_active(self) -> List[Dict[str, Any]]:
        """Get all active generations."""
        return [
            {
                "prompt_id": gen.prompt_id,
                "workflow_name": gen.workflow_name,
                "status": gen.status,
                "progress": gen.progress,
                "current_node": gen.current_node,
                "eta": gen.eta_seconds
            }
            for gen in self.active_generations.values()
        ]


# Global instance
generation_manager = GenerationManager()


__all__ = ["GenerationManager", "generation_manager"]
