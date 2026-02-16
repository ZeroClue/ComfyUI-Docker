"""
Background download manager for preset files
Handles concurrent downloads with progress tracking and WebSocket updates
"""

import asyncio
import aiohttp
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from urllib.parse import urlparse

from .config import settings
from .websocket import broadcast_download_progress


class DownloadTask:
    """Represents a single download task"""

    def __init__(
        self,
        preset_id: str,
        file_url: str,
        file_path: str,
        file_size: Optional[str] = None
    ):
        self.preset_id = preset_id
        self.file_url = file_url
        self.file_path = file_path
        self.file_size = file_size
        self.status = "pending"
        self.progress = 0.0
        self.downloaded_bytes = 0
        self.total_bytes = 0
        self.error = None
        self.started_at = None
        self.completed_at = None


class DownloadManager:
    """Manages background downloads with progress tracking"""

    def __init__(self):
        self.active_downloads: Dict[str, List[DownloadTask]] = {}
        self.download_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_DOWNLOADS)
        self.base_path = Path(settings.MODEL_BASE_PATH)

    async def start_download(
        self,
        preset_id: str,
        files: List[Dict],
        force: bool = False
    ) -> str:
        """
        Start downloading files for a preset

        Args:
            preset_id: ID of the preset to download
            files: List of file dictionaries with 'path' and 'url' keys
            force: Force re-download even if file exists

        Returns:
            Download ID for tracking
        """
        download_id = f"{preset_id}_{datetime.utcnow().timestamp()}"

        if preset_id in self.active_downloads:
            return f"Download already active for preset {preset_id}"

        # Create download tasks
        tasks = []
        for file_info in files:
            file_path = file_info.get('path', '')
            file_url = file_info.get('url', '')
            file_size = file_info.get('size', 'Unknown')

            if not file_url:
                continue

            # Check if file exists and force flag
            full_path = self.base_path / file_path
            if full_path.exists() and not force:
                continue

            task = DownloadTask(
                preset_id=preset_id,
                file_url=file_url,
                file_path=file_path,
                file_size=file_size
            )
            tasks.append(task)

        if not tasks:
            return f"No files to download for preset {preset_id}"

        self.active_downloads[preset_id] = tasks

        # Start background download
        asyncio.create_task(self._download_preset(preset_id, tasks))

        return download_id

    async def _download_preset(self, preset_id: str, tasks: List[DownloadTask]):
        """Download all files for a preset concurrently"""

        async def download_with_semaphore(task: DownloadTask):
            async with self.download_semaphore:
                await self._download_file(task)

        # Start all downloads
        download_coroutines = [download_with_semaphore(task) for task in tasks]
        await asyncio.gather(*download_coroutines, return_exceptions=True)

        # Clean up completed downloads
        if preset_id in self.active_downloads:
            del self.active_downloads[preset_id]

    async def _download_file(self, task: DownloadTask):
        """Download a single file with progress tracking"""

        task.status = "downloading"
        task.started_at = datetime.utcnow()

        full_path = self.base_path / task.file_path

        # Create parent directories
        full_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    task.file_url,
                    timeout=aiohttp.ClientTimeout(total=settings.DOWNLOAD_TIMEOUT)
                ) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}")

                    # Get total file size
                    task.total_bytes = int(response.headers.get('Content-Length', 0))

                    # Download with progress tracking
                    with open(full_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(settings.DOWNLOAD_CHUNK_SIZE):
                            f.write(chunk)
                            task.downloaded_bytes += len(chunk)

                            if task.total_bytes > 0:
                                task.progress = (task.downloaded_bytes / task.total_bytes) * 100

                            # Broadcast progress
                            await broadcast_download_progress(task.preset_id, {
                                "file": task.file_path,
                                "progress": task.progress,
                                "downloaded": task.downloaded_bytes,
                                "total": task.total_bytes,
                                "status": task.status
                            })

            task.status = "completed"
            task.completed_at = datetime.utcnow()
            task.progress = 100.0

            # Broadcast completion
            await broadcast_download_progress(task.preset_id, {
                "file": task.file_path,
                "progress": 100.0,
                "status": "completed"
            })

        except Exception as e:
            task.status = "failed"
            task.error = str(e)

            # Broadcast error
            await broadcast_download_progress(task.preset_id, {
                "file": task.file_path,
                "status": "failed",
                "error": str(e)
            })

    async def get_download_status(self, preset_id: str) -> Optional[Dict]:
        """Get current download status for a preset"""

        if preset_id not in self.active_downloads:
            return None

        tasks = self.active_downloads[preset_id]

        return {
            "preset_id": preset_id,
            "total_files": len(tasks),
            "completed": sum(1 for t in tasks if t.status == "completed"),
            "failed": sum(1 for t in tasks if t.status == "failed"),
            "downloading": sum(1 for t in tasks if t.status == "downloading"),
            "pending": sum(1 for t in tasks if t.status == "pending"),
            "files": [
                {
                    "path": t.file_path,
                    "status": t.status,
                    "progress": t.progress,
                    "error": t.error
                }
                for t in tasks
            ]
        }

    async def cancel_download(self, preset_id: str) -> bool:
        """Cancel active download for a preset"""

        if preset_id in self.active_downloads:
            # Mark all tasks as cancelled
            for task in self.active_downloads[preset_id]:
                task.status = "cancelled"

            del self.active_downloads[preset_id]
            return True

        return False

    def get_active_downloads(self) -> List[str]:
        """Get list of preset IDs with active downloads"""
        return list(self.active_downloads.keys())
