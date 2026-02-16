#!/usr/bin/env python3
"""
WebSocket Progress Tracker for Preset Downloads

Provides real-time download progress updates via WebSocket.
Can be integrated with Flask web interface or standalone.
"""

import os
import json
import time
import asyncio
import websockets
from pathlib import Path
from typing import Dict, Set
from datetime import datetime


class WebSocketProgressServer:
    """WebSocket server for real-time preset download progress"""

    def __init__(self, host: str = "0.0.0.0", port: int = 9001, progress_file: str = "/tmp/preset_download_progress.json"):
        self.host = host
        self.port = port
        self.progress_file = progress_file
        self.clients: Set[websockets.WebSocketServerProtocol] = set()

    async def register_client(self, websocket: websockets.WebSocketServerProtocol):
        """Register a new WebSocket client"""
        self.clients.add(websocket)
        print(f"[WS] Client connected: {websocket.remote_address}")

        # Send current progress immediately
        await self.send_progress(websocket)

    async def unregister_client(self, websocket: websockets.WebSocketServerProtocol):
        """Unregister a WebSocket client"""
        self.clients.discard(websocket)
        print(f"[WS] Client disconnected: {websocket.remote_address}")

    async def send_progress(self, websocket: websockets.WebSocketServerProtocol = None):
        """Send current progress to specific client or all clients"""
        progress = self.load_progress()

        message = {
            "type": "progress_update",
            "data": progress,
            "timestamp": datetime.now().isoformat()
        }

        if websocket:
            try:
                await websocket.send(json.dumps(message))
            except Exception as e:
                print(f"[WS] Error sending to client: {e}")
        else:
            # Broadcast to all clients
            disconnected = set()
            for client in self.clients:
                try:
                    await client.send(json.dumps(message))
                except Exception as e:
                    print(f"[WS] Error broadcasting to client: {e}")
                    disconnected.add(client)

            # Remove disconnected clients
            self.clients -= disconnected

    def load_progress(self) -> Dict:
        """Load current progress from file"""
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[WS] Error loading progress: {e}")

        return {}

    async def broadcast_loop(self):
        """Broadcast progress updates to all clients periodically"""
        while True:
            await asyncio.sleep(2)  # Update every 2 seconds
            await self.send_progress()

    async def handle_client(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """Handle a WebSocket client connection"""
        await self.register_client(websocket)

        try:
            # Keep connection alive and handle incoming messages
            async for message in websocket:
                data = json.loads(message)

                # Handle client requests
                if data.get("type") == "get_progress":
                    await self.send_progress(websocket)
                elif data.get("type") == "ping":
                    await websocket.send(json.dumps({"type": "pong"}))

        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)

    async def start_server(self):
        """Start the WebSocket server"""
        print(f"[WS] Starting WebSocket server on {self.host}:{self.port}")

        # Start broadcast loop in background
        asyncio.create_task(self.broadcast_loop())

        # Start serving WebSocket clients
        async with websockets.serve(self.handle_client, self.host, self.port):
            print(f"[WS] WebSocket server running on ws://{self.host}:{self.port}")
            await asyncio.Future()  # Run forever


def run_websocket_server(host: str = "0.0.0.0", port: int = 9001, progress_file: str = "/tmp/preset_download_progress.json"):
    """Run the WebSocket progress server"""
    server = WebSocketProgressServer(host=host, port=port, progress_file=progress_file)

    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        print("\n[WS] WebSocket server stopped")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="WebSocket progress server for preset downloads")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=9001, help="Port to bind to")
    parser.add_argument("--progress-file", default="/tmp/preset_download_progress.json", help="Progress file path")

    args = parser.parse_args()

    run_websocket_server(host=args.host, port=args.port, progress_file=args.progress_file)
