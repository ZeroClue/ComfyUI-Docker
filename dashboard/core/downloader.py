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
        self.download_queue: asyncio.Queue = asyncio.Queue()
        self.current_download: Optional[str] = None
        self.queue_processor_running: bool = False
        self.base_path = Path(settings.MODEL_BASE_PATH)
        self.retry_config = {
            "max_retries": 3,
            "base_delay": 5,  # seconds
            "max_delay": 60
        }

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

        # Check if already in queue
        for item in list(self.download_queue._queue):
            if isinstance(item, tuple) and item[0] == preset_id:
                return f"Preset {preset_id} is already in download queue"

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

        # Add to queue for sequential processing
        await self.download_queue.put((preset_id, tasks))

        # Start queue processor if not running
        if not self.queue_processor_running:
            asyncio.create_task(self._process_queue())

        return download_id

    async def _process_queue(self):
        """Process downloads sequentially from queue"""
        self.queue_processor_running = True

        while True:
            try:
                # Get next preset from queue
                preset_id, tasks = await self.download_queue.get()

                if preset_id not in self.active_downloads:
                    # Download was cancelled while in queue
                    continue

                self.current_download = preset_id

                # Broadcast queue update
                await self._broadcast_queue_update()

                # Download files sequentially within preset
                for task in tasks:
                    if task.status == "cancelled":
                        continue

                    retry_count = 0
                    while retry_count < self.retry_config["max_retries"]:
                        await self._download_file(task)

                        if task.status == "completed":
                            break
                        elif task.status == "failed":
                            retry_count += 1
                            if retry_count < self.retry_config["max_retries"]:
                                delay = min(
                                    self.retry_config["base_delay"] * (2 ** retry_count),
                                    self.retry_config["max_delay"]
                                )
                                task.status = "retrying"
                                task.error = f"Retrying ({retry_count}/{self.retry_config['max_retries']})..."
                                await asyncio.sleep(delay)
                                task.status = "downloading"

                    if task.status == "failed":
                        # Max retries exhausted
                        await broadcast_download_progress(preset_id, {
                            "type": "download_failed",
                            "preset_id": preset_id,
                            "file": task.file_path,
                            "error": task.error,
                            "retry_count": self.retry_config["max_retries"]
                        })

                # Mark preset complete
                if preset_id in self.active_downloads:
                    del self.active_downloads[preset_id]

                self.current_download = None
                await self._broadcast_queue_update()

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Queue processor error: {e}")
                await asyncio.sleep(1)

        self.queue_processor_running = False

    async def _broadcast_queue_update(self):
        """Broadcast current queue state via WebSocket"""
        from .websocket import manager

        queue_list = []
        # Get items in queue without removing them
        for item in list(self.download_queue._queue):
            if isinstance(item, tuple):
                queue_list.append(item[0])

        await manager.broadcast_json({
            "type": "queue_updated",
            "current": self.current_download,
            "queue": queue_list
        })

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
                            # Check if paused or cancelled during download
                            if task.status in ("paused", "cancelled"):
                                break

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

    async def pause_download(self, preset_id: str) -> bool:
        """Pause active download (keeps partial file)"""
        if preset_id not in self.active_downloads:
            return False

        for task in self.active_downloads[preset_id]:
            if task.status == "downloading":
                task.status = "paused"

        await self._broadcast_queue_update()
        return True

    async def resume_download(self, preset_id: str) -> bool:
        """Resume paused download"""
        if preset_id not in self.active_downloads:
            return False

        for task in self.active_downloads[preset_id]:
            if task.status == "paused":
                task.status = "pending"

        # Re-queue if not currently downloading
        if self.current_download != preset_id:
            await self.download_queue.put((preset_id, self.active_downloads[preset_id]))

        await self._broadcast_queue_update()
        return True

    async def cancel_download(self, preset_id: str, keep_partial: bool = True) -> bool:
        """Cancel download, optionally keeping partial files"""
        if preset_id in self.active_downloads:
            for task in self.active_downloads[preset_id]:
                task.status = "cancelled"
                if not keep_partial:
                    full_path = self.base_path / task.file_path
                    if full_path.exists():
                        full_path.unlink()

            del self.active_downloads[preset_id]
            await self._broadcast_queue_update()
            return True

        return False

    async def retry_download(self, preset_id: str) -> bool:
        """Retry failed download from beginning"""
        # This will be handled by re-calling start_download
        return False  # API endpoint will handle this

    def get_queue_status(self) -> Dict:
        """Get current queue status"""
        queue_list = []
        for item in list(self.download_queue._queue):
            if isinstance(item, tuple):
                queue_list.append(item[0])

        return {
            "current": self.current_download,
            "queue": queue_list,
            "active_downloads": len(self.active_downloads)
        }

    def get_active_downloads(self) -> List[str]:
        """Get list of preset IDs with active downloads"""
        return list(self.active_downloads.keys())
