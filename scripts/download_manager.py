#!/usr/bin/env python3
"""
Background Download Manager for ComfyUI Presets
Handles concurrent downloads with real-time progress tracking, pause/resume, and WebSocket updates
"""

import os
import sys
import yaml
import asyncio
import aiohttp
import logging
import threading
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import hashlib
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DownloadStatus(Enum):
    """Download status enumeration"""
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass
class DownloadProgress:
    """Track download progress for a single file"""
    file_path: str
    url: str
    status: DownloadStatus = DownloadStatus.QUEUED
    progress: float = 0.0
    downloaded_bytes: int = 0
    total_bytes: int = 0
    speed: float = 0.0  # bytes per second
    eta: Optional[float] = None  # seconds remaining
    error: Optional[str] = None
    retry_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_update: Optional[datetime] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for WebSocket broadcast"""
        data = asdict(self)
        data['status'] = self.status.value
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        data['last_update'] = self.last_update.isoformat() if self.last_update else None
        return data


@dataclass
class PresetDownload:
    """Track download progress for an entire preset"""
    preset_id: str
    preset_name: str
    files: List[DownloadProgress] = field(default_factory=list)
    overall_progress: float = 0.0
    total_bytes: int = 0
    downloaded_bytes: int = 0
    status: DownloadStatus = DownloadStatus.QUEUED
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    def calculate_overall_progress(self) -> float:
        """Calculate overall preset download progress"""
        if not self.files:
            return 0.0

        total_files = len(self.files)
        completed_files = sum(1 for f in self.files if f.status == DownloadStatus.COMPLETED)

        # Weight by file size if available
        total_size = sum(f.total_bytes for f in self.files if f.total_bytes > 0)
        if total_size > 0:
            downloaded_size = sum(f.downloaded_bytes for f in self.files)
            return (downloaded_size / total_size) * 100

        # Otherwise use file count
        return (completed_files / total_files) * 100

    def to_dict(self) -> Dict:
        """Convert to dictionary for WebSocket broadcast"""
        return {
            "preset_id": self.preset_id,
            "preset_name": self.preset_name,
            "overall_progress": self.overall_progress,
            "total_bytes": self.total_bytes,
            "downloaded_bytes": self.downloaded_bytes,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "files": {
                "completed": sum(1 for f in self.files if f.status == DownloadStatus.COMPLETED),
                "total": len(self.files),
                "failed": sum(1 for f in self.files if f.status == DownloadStatus.FAILED),
                "downloading": sum(1 for f in self.files if f.status == DownloadStatus.DOWNLOADING)
            }
        }


class WebSocketBroadcaster:
    """WebSocket broadcaster for real-time updates"""

    def __init__(self):
        self._callbacks: List[Callable] = []
        self._enabled = True

    def register_callback(self, callback: Callable):
        """Register a callback for WebSocket broadcasts"""
        self._callbacks.append(callback)

    async def broadcast(self, message: Dict):
        """Broadcast message to all registered callbacks"""
        if not self._enabled:
            return

        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)
            except Exception as e:
                logger.error(f"Error in broadcast callback: {e}")

    def disable(self):
        """Disable broadcasting"""
        self._enabled = False

    def enable(self):
        """Enable broadcasting"""
        self._enabled = True


class DownloadManager:
    """
    Background download manager with queue-based system, progress tracking,
    pause/resume capability, and concurrent download support
    """

    def __init__(
        self,
        model_base_path: str = "/workspace/ComfyUI/models",
        preset_config_path: str = "/workspace/config/presets.yaml",
        max_concurrent_downloads: int = 3,
        max_retries: int = 3,
        chunk_size: int = 8192,
        timeout: int = 3600
    ):
        self.model_base_path = Path(model_base_path)
        self.preset_config_path = Path(preset_config_path)
        self.max_concurrent_downloads = max_concurrent_downloads
        self.max_retries = max_retries
        self.chunk_size = chunk_size
        self.timeout = timeout

        # Download queue and active downloads
        self.download_queue: deque[str] = deque()
        self.active_downloads: Dict[str, PresetDownload] = {}
        self.paused_downloads: Set[str] = set()

        # Threading and async support
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._semaphore: Optional[asyncio.Semaphore] = None

        # Preset configuration cache
        self.presets: Dict[str, Any] = {}
        self._load_presets()

        # WebSocket broadcaster
        self.broadcaster = WebSocketBroadcaster()

        # Status persistence
        self.status_file = Path("/tmp/download_manager_status.json")
        self._load_status()

    def _load_presets(self):
        """Load preset configurations from YAML"""
        try:
            if not self.preset_config_path.exists():
                logger.warning(f"Preset config not found: {self.preset_config_path}")
                return

            with open(self.preset_config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            if 'presets' in config:
                self.presets = config['presets']
                logger.info(f"Loaded {len(self.presets)} preset configurations")

        except Exception as e:
            logger.error(f"Error loading presets: {e}")

    def _load_status(self):
        """Load persisted download status"""
        try:
            if not self.status_file.exists():
                return

            with open(self.status_file, 'r') as f:
                status = json.load(f)

            # Restore paused downloads
            self.paused_downloads = set(status.get('paused_downloads', []))

            logger.info(f"Loaded persisted status: {len(self.paused_downloads)} paused downloads")

        except Exception as e:
            logger.error(f"Error loading status: {e}")

    def _save_status(self):
        """Persist download status to disk"""
        try:
            status = {
                'paused_downloads': list(self.paused_downloads),
                'active_downloads': list(self.active_downloads.keys()),
                'queued_downloads': list(self.download_queue),
                'timestamp': datetime.utcnow().isoformat()
            }

            with open(self.status_file, 'w') as f:
                json.dump(status, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving status: {e}")

    def start(self):
        """Start the download manager in background thread"""
        if self._running:
            logger.warning("Download manager already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._thread.start()
        logger.info("Download manager started")

    def stop(self):
        """Stop the download manager"""
        if not self._running:
            return

        self._running = False

        # Save current status
        self._save_status()

        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

        if self._thread:
            self._thread.join(timeout=5)

        logger.info("Download manager stopped")

    def _run_event_loop(self):
        """Run async event loop in background thread"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._semaphore = asyncio.Semaphore(self.max_concurrent_downloads)

        try:
            self._loop.run_until_complete(self._process_queue())
        except Exception as e:
            logger.error(f"Event loop error: {e}")
        finally:
            self._loop.close()

    async def _process_queue(self):
        """Process download queue continuously"""
        while self._running:
            # Check if we can start new downloads
            while len(self.active_downloads) < self.max_concurrent_downloads and self.download_queue:
                preset_id = self.download_queue.popleft()

                # Skip if paused
                if preset_id in self.paused_downloads:
                    continue

                # Start download
                await self._start_preset_download(preset_id)

            # Wait before checking again
            await asyncio.sleep(1)

    def queue_preset(self, preset_id: str) -> bool:
        """
        Queue a preset for download

        Args:
            preset_id: ID of the preset to download

        Returns:
            True if queued successfully, False otherwise
        """
        if preset_id not in self.presets:
            logger.error(f"Preset not found: {preset_id}")
            return False

        if preset_id in self.active_downloads or preset_id in self.download_queue:
            logger.warning(f"Preset already downloading or queued: {preset_id}")
            return False

        # Add to queue
        self.download_queue.append(preset_id)

        # Create preset download object
        preset_data = self.presets[preset_id]
        preset_name = preset_data.get('name', preset_id)
        files = preset_data.get('files', [])

        preset_download = PresetDownload(
            preset_id=preset_id,
            preset_name=preset_name
        )

        # Create file download tasks
        for file_info in files:
            if isinstance(file_info, dict):
                file_path = file_info.get('path', '')
                url = file_info.get('url', '')
                size_str = file_info.get('size', '0')

                if not url:
                    continue

                # Parse size string to bytes
                size_bytes = self._parse_size(size_str)

                file_progress = DownloadProgress(
                    file_path=file_path,
                    url=url,
                    total_bytes=size_bytes
                )
                preset_download.files.append(file_progress)

        self.active_downloads[preset_id] = preset_download

        # Broadcast queued event
        asyncio.run_coroutine_threadsafe(
            self._broadcast_event({
                "type": "download_queued",
                "preset_id": preset_id,
                "preset_name": preset_name,
                "queue_position": list(self.download_queue).index(preset_id) + 1,
                "timestamp": datetime.utcnow().isoformat()
            }),
            self._loop
        ) if self._loop else None

        logger.info(f"Queued preset: {preset_id}")
        return True

    def _parse_size(self, size_str: str) -> int:
        """Parse size string to bytes (e.g., '4.8GB' -> 5153960755)"""
        try:
            size_str = size_str.upper().strip()

            # Extract number and unit
            import re
            match = re.match(r'([\d.]+)\s*([A-Z]*)', size_str)
            if not match:
                return 0

            number = float(match.group(1))
            unit = match.group(2)

            # Convert to bytes
            multipliers = {
                '': 1,
                'B': 1,
                'KB': 1024,
                'MB': 1024**2,
                'GB': 1024**3,
                'TB': 1024**4
            }

            return int(number * multipliers.get(unit, 1))

        except Exception:
            return 0

    async def _start_preset_download(self, preset_id: str):
        """Start downloading files for a preset"""
        preset_download = self.active_downloads.get(preset_id)
        if not preset_download:
            return

        preset_download.status = DownloadStatus.DOWNLOADING
        preset_download.started_at = datetime.utcnow()

        # Calculate total size
        preset_download.total_bytes = sum(
            f.total_bytes for f in preset_download.files if f.total_bytes > 0
        )

        # Broadcast start event
        await self._broadcast_progress(preset_id)

        # Download files concurrently
        tasks = []
        for file_progress in preset_download.files:
            if file_progress.status not in [DownloadStatus.COMPLETED, DownloadStatus.FAILED]:
                tasks.append(self._download_file(preset_id, file_progress))

        # Wait for all downloads to complete
        await asyncio.gather(*tasks, return_exceptions=True)

        # Update preset status
        completed_files = sum(1 for f in preset_download.files if f.status == DownloadStatus.COMPLETED)
        failed_files = sum(1 for f in preset_download.files if f.status == DownloadStatus.FAILED)

        if completed_files == len(preset_download.files):
            preset_download.status = DownloadStatus.COMPLETED
            preset_download.completed_at = datetime.utcnow()
        elif failed_files == len(preset_download.files):
            preset_download.status = DownloadStatus.FAILED
            preset_download.error = f"All {failed_files} files failed to download"
        else:
            preset_download.status = DownloadStatus.COMPLETED  # Partial completion
            preset_download.completed_at = datetime.utcnow()
            preset_download.error = f"{failed_files} files failed, {completed_files} completed"

        # Broadcast final status
        await self._broadcast_progress(preset_id)

        # Remove from active downloads after delay
        await asyncio.sleep(60)
        if preset_id in self.active_downloads:
            del self.active_downloads[preset_id]

        # Save status
        self._save_status()

    async def _download_file(self, preset_id: str, file_progress: DownloadProgress):
        """Download a single file with progress tracking and retry logic"""
        preset_download = self.active_downloads.get(preset_id)
        if not preset_download:
            return

        # Check if paused
        if preset_id in self.paused_downloads:
            file_progress.status = DownloadStatus.PAUSED
            return

        async with self._semaphore:
            # Check for existing partial download
            full_path = self.model_base_path / file_progress.file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)

            temp_path = full_path.with_suffix(full_path.suffix + '.part')
            resume_position = 0

            if temp_path.exists():
                resume_position = temp_path.stat().st_size
                file_progress.downloaded_bytes = resume_position

            file_progress.status = DownloadStatus.DOWNLOADING
            file_progress.started_at = datetime.utcnow()

            headers = {}
            if resume_position > 0:
                headers['Range'] = f'bytes={resume_position}-'

            retry_count = 0
            last_speed_update = time.time()
            speed_bytes = 0
            speed_start = time.time()

            while retry_count <= self.max_retries:
                try:
                    timeout = aiohttp.ClientTimeout(total=self.timeout)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.get(file_progress.url, headers=headers) as response:
                            if response.status not in [200, 206]:
                                raise Exception(f"HTTP {response.status}")

                            # Get total file size
                            content_length = response.headers.get('Content-Length')
                            if content_length:
                                file_progress.total_bytes = int(content_length) + resume_position

                            # Download with progress tracking
                            mode = 'ab' if resume_position > 0 else 'wb'
                            with open(temp_path, mode) as f:
                                async for chunk in response.content.iter_chunked(self.chunk_size):
                                    # Check if paused
                                    if preset_id in self.paused_downloads:
                                        file_progress.status = DownloadStatus.PAUSED
                                        await self._broadcast_progress(preset_id)
                                        return

                                    f.write(chunk)
                                    chunk_size = len(chunk)

                                    file_progress.downloaded_bytes += chunk_size
                                    if preset_download:
                                        preset_download.downloaded_bytes += chunk_size

                                    speed_bytes += chunk_size
                                    speed_elapsed = time.time() - speed_start

                                    # Update speed every second
                                    if speed_elapsed >= 1.0:
                                        file_progress.speed = speed_bytes / speed_elapsed
                                        speed_bytes = 0
                                        speed_start = time.time()

                                        # Calculate ETA
                                        if file_progress.speed > 0 and file_progress.total_bytes > 0:
                                            remaining = file_progress.total_bytes - file_progress.downloaded_bytes
                                            file_progress.eta = remaining / file_progress.speed

                                    # Update progress
                                    if file_progress.total_bytes > 0:
                                        file_progress.progress = (file_progress.downloaded_bytes / file_progress.total_bytes) * 100

                                    file_progress.last_update = datetime.utcnow()

                                    # Broadcast progress every 2 seconds
                                    if time.time() - last_speed_update >= 2:
                                        await self._broadcast_progress(preset_id)
                                        last_speed_update = time.time()

                    # Move temp file to final location
                    temp_path.rename(full_path)

                    file_progress.status = DownloadStatus.COMPLETED
                    file_progress.progress = 100.0
                    file_progress.completed_at = datetime.utcnow()

                    # Broadcast completion
                    await self._broadcast_progress(preset_id)
                    return

                except Exception as e:
                    retry_count += 1
                    file_progress.retry_count = retry_count

                    if retry_count <= self.max_retries:
                        file_progress.status = DownloadStatus.RETRYING
                        file_progress.error = f"Attempt {retry_count}/{self.max_retries}: {str(e)}"

                        logger.warning(f"Download failed for {file_progress.file_path}, retrying: {e}")
                        await self._broadcast_progress(preset_id)

                        # Wait before retry with exponential backoff
                        await asyncio.sleep(min(2 ** retry_count, 60))

                        # Reset headers for retry
                        headers = {}
                        if file_progress.downloaded_bytes > 0:
                            headers['Range'] = f'bytes={file_progress.downloaded_bytes}-'
                    else:
                        file_progress.status = DownloadStatus.FAILED
                        file_progress.error = str(e)

                        logger.error(f"Download failed after {retry_count} attempts: {file_progress.file_path}")
                        await self._broadcast_progress(preset_id)

    async def _broadcast_progress(self, preset_id: str):
        """Broadcast download progress via WebSocket"""
        preset_download = self.active_downloads.get(preset_id)
        if not preset_download:
            return

        # Update overall progress
        preset_download.overall_progress = preset_download.calculate_overall_progress()

        # Create progress message
        message = {
            "type": "download_progress",
            "preset_id": preset_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": preset_download.to_dict()
        }

        # Broadcast via WebSocket
        await self.broadcaster.broadcast(message)

    async def _broadcast_event(self, event: Dict):
        """Broadcast generic event via WebSocket"""
        await self.broadcaster.broadcast(event)

    def pause_download(self, preset_id: str) -> bool:
        """Pause a download"""
        if preset_id in self.active_downloads:
            self.paused_downloads.add(preset_id)

            # Broadcast pause event
            asyncio.run_coroutine_threadsafe(
                self._broadcast_event({
                    "type": "download_paused",
                    "preset_id": preset_id,
                    "timestamp": datetime.utcnow().isoformat()
                }),
                self._loop
            ) if self._loop else None

            logger.info(f"Paused download: {preset_id}")
            return True
        return False

    def resume_download(self, preset_id: str) -> bool:
        """Resume a paused download"""
        if preset_id in self.paused_downloads:
            self.paused_downloads.remove(preset_id)

            # Re-queue the download
            if preset_id not in self.download_queue:
                self.download_queue.append(preset_id)

            # Broadcast resume event
            asyncio.run_coroutine_threadsafe(
                self._broadcast_event({
                    "type": "download_resumed",
                    "preset_id": preset_id,
                    "timestamp": datetime.utcnow().isoformat()
                }),
                self._loop
            ) if self._loop else None

            logger.info(f"Resumed download: {preset_id}")
            return True
        return False

    def cancel_download(self, preset_id: str) -> bool:
        """Cancel a download"""
        cancelled = False

        # Remove from queue
        if preset_id in self.download_queue:
            self.download_queue.remove(preset_id)
            cancelled = True

        # Remove from active downloads
        if preset_id in self.active_downloads:
            preset_download = self.active_downloads[preset_id]
            preset_download.status = DownloadStatus.CANCELLED

            # Clean up temp files
            for file_progress in preset_download.files:
                temp_path = (self.model_base_path / file_progress.file_path).with_suffix('.part')
                if temp_path.exists():
                    temp_path.unlink()

            del self.active_downloads[preset_id]
            cancelled = True

        # Remove from paused
        if preset_id in self.paused_downloads:
            self.paused_downloads.remove(preset_id)
            cancelled = True

        if cancelled:
            # Broadcast cancel event
            asyncio.run_coroutine_threadsafe(
                self._broadcast_event({
                    "type": "download_cancelled",
                    "preset_id": preset_id,
                    "timestamp": datetime.utcnow().isoformat()
                }),
                self._loop
            ) if self._loop else None

            logger.info(f"Cancelled download: {preset_id}")

        return cancelled

    def get_download_status(self, preset_id: str) -> Optional[Dict]:
        """Get current download status for a preset"""
        preset_download = self.active_downloads.get(preset_id)
        if not preset_download:
            return None

        return preset_download.to_dict()

    def get_all_downloads(self) -> Dict[str, Any]:
        """Get status of all downloads"""
        return {
            "active": {
                preset_id: preset.to_dict()
                for preset_id, preset in self.active_downloads.items()
            },
            "queued": list(self.download_queue),
            "paused": list(self.paused_downloads),
            "active_count": len(self.active_downloads),
            "queued_count": len(self.download_queue),
            "paused_count": len(self.paused_downloads)
        }

    def get_available_presets(self) -> Dict[str, Any]:
        """Get list of available presets from configuration"""
        return {
            preset_id: {
                "name": preset.get('name', preset_id),
                "category": preset.get('category', 'Unknown'),
                "type": preset.get('type', 'unknown'),
                "description": preset.get('description', ''),
                "download_size": preset.get('download_size', 'Unknown'),
                "file_count": len(preset.get('files', []))
            }
            for preset_id, preset in self.presets.items()
        }


# Singleton instance
_download_manager: Optional[DownloadManager] = None


def get_download_manager() -> DownloadManager:
    """Get or create the singleton download manager instance"""
    global _download_manager

    if _download_manager is None:
        _download_manager = DownloadManager()
        _download_manager.start()

    return _download_manager


if __name__ == "__main__":
    # Test the download manager
    manager = get_download_manager()

    # List available presets
    presets = manager.get_available_presets()
    print("Available presets:")
    for preset_id, info in presets.items():
        print(f"  {preset_id}: {info['name']} ({info['file_count']} files)")

    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        manager.stop()
