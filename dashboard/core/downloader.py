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
from ..api.activity import add_activity


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file

    Args:
        file_path: Path to the file to hash

    Returns:
        Hexadecimal SHA256 hash string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def parse_checksum(checksum: str) -> tuple[str, str]:
    """Parse checksum string into algorithm and hash

    Args:
        checksum: Checksum string in format "algorithm:hash" (e.g., "sha256:abc123...")

    Returns:
        Tuple of (algorithm, hash)

    Raises:
        ValueError: If checksum format is invalid or algorithm is unsupported
    """
    if ':' not in checksum:
        raise ValueError(f"Invalid checksum format: expected 'algorithm:hash', got '{checksum}'")

    algorithm, hash_value = checksum.split(':', 1)
    algorithm = algorithm.lower()

    if algorithm != 'sha256':
        raise ValueError(f"Unsupported checksum algorithm: {algorithm}. Only sha256 is supported.")

    return algorithm, hash_value


class DownloadTask:
    """Represents a single download task"""

    def __init__(
        self,
        preset_id: str,
        file_url: str,
        file_path: str,
        file_size: Optional[str] = None,
        checksum: Optional[str] = None
    ):
        self.preset_id = preset_id
        self.file_url = file_url
        self.file_path = file_path
        self.file_size = file_size
        self.checksum = checksum  # Expected checksum in format "sha256:abc123..."
        self.status = "pending"
        self.progress = 0.0
        self.downloaded_bytes = 0
        self.total_bytes = 0
        self.error = None
        self.started_at = None
        self.completed_at = None
        self.checksum_verified = None  # True if verified, False if failed, None if not checked


class DownloadManager:
    """Manages background downloads with progress tracking"""

    def __init__(self):
        self.active_downloads: Dict[str, List[DownloadTask]] = {}
        self._download_queue: Optional[asyncio.Queue] = None  # Lazy init
        self._processor_task: Optional[asyncio.Task] = None  # Keep reference
        self.current_download: Optional[str] = None
        self.queue_processor_running: bool = False
        self.base_path = Path(settings.MODEL_BASE_PATH)
        self.retry_config = {
            "max_retries": 3,
            "base_delay": 5,  # seconds
            "max_delay": 60
        }

    @property
    def download_queue(self) -> asyncio.Queue:
        """Lazily initialize queue within async context"""
        if self._download_queue is None:
            self._download_queue = asyncio.Queue()
        return self._download_queue

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

        # Check if already in queue (safely access internal queue)
        try:
            if hasattr(self.download_queue, '_queue'):
                for item in list(self.download_queue._queue):
                    if isinstance(item, tuple) and item[0] == preset_id:
                        return f"Preset {preset_id} is already in download queue"
        except Exception:
            pass  # If we can't check the queue, just proceed

        # Create download tasks
        tasks = []
        for file_info in files:
            file_path = file_info.get('path', '')
            file_url = file_info.get('url', '')
            file_size = file_info.get('size', 'Unknown')
            file_checksum = file_info.get('checksum')  # Optional checksum

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
                file_size=file_size,
                checksum=file_checksum
            )
            tasks.append(task)

        if not tasks:
            return f"No files to download for preset {preset_id}"

        self.active_downloads[preset_id] = tasks

        # Add to queue for sequential processing
        await self.download_queue.put((preset_id, tasks))

        # Start queue processor if not running
        if not self.queue_processor_running:
            loop = asyncio.get_running_loop()
            self._processor_task = loop.create_task(self._process_queue())

            # Add a callback to log any exceptions
            def log_task_exception(task):
                try:
                    exc = task.exception()
                    if exc:
                        print(f"Download processor task failed: {exc}")
                        import traceback
                        traceback.print_exception(type(exc), exc, exc.__traceback__)
                except asyncio.CancelledError:
                    print("Download processor task was cancelled")
                except Exception as e:
                    print(f"Error getting task exception: {e}")

            self._processor_task.add_done_callback(log_task_exception)

        return download_id

    async def _process_queue(self):
        """Process downloads sequentially from queue"""
        self.queue_processor_running = True
        print("=" * 50)
        print("Download queue processor STARTED")
        print(f"Queue size at start: {self.download_queue.qsize()}")
        print("=" * 50)

        while True:
            try:
                # Get next preset from queue
                preset_id, tasks = await self.download_queue.get()

                if preset_id not in self.active_downloads:
                    # Download was cancelled while in queue
                    continue

                self.current_download = preset_id
                print(f"Starting download for preset: {preset_id}")

                # Log download started
                add_activity(
                    activity_type="download",
                    status="started",
                    title="Model download started",
                    subtitle=preset_id
                )

                # Broadcast queue update
                await self._broadcast_queue_update()

                # Download files sequentially within preset
                for task in tasks:
                    if task.status in ("cancelled", "paused"):
                        continue

                    retry_count = 0
                    while retry_count < self.retry_config["max_retries"]:
                        await self._download_file(task)

                        if task.status == "completed":
                            break
                        elif task.status == "paused":
                            # Stop processing this preset when paused
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

                    # If paused, stop processing this preset entirely
                    if task.status == "paused":
                        break

                    if task.status == "failed":
                        # Max retries exhausted - log failure
                        add_activity(
                            activity_type="download",
                            status="failed",
                            title="Model download failed",
                            subtitle=f"{preset_id}: {task.error}"
                        )
                        await broadcast_download_progress(preset_id, {
                            "type": "download_failed",
                            "preset_id": preset_id,
                            "file": task.file_path,
                            "error": task.error,
                            "retry_count": self.retry_config["max_retries"]
                        })

                # Mark preset complete only if not paused
                if preset_id in self.active_downloads:
                    # Check if any task is paused - if so, keep in active_downloads
                    any_paused = any(t.status == "paused" for t in tasks)
                    any_failed = any(t.status == "failed" for t in tasks)
                    if not any_paused and not any_failed:
                        # All files completed successfully
                        add_activity(
                            activity_type="download",
                            status="completed",
                            title="Preset installed",
                            subtitle=preset_id
                        )
                        del self.active_downloads[preset_id]
                    elif not any_paused:
                        del self.active_downloads[preset_id]

                self.current_download = None
                await self._broadcast_queue_update()

            except asyncio.CancelledError:
                print("Download queue processor cancelled")
                break
            except Exception as e:
                print(f"Queue processor error: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(1)

        self.queue_processor_running = False
        print("Download queue processor stopped")

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

        # Prepare headers with HF token if available
        headers = {}
        from . import persistence
        if persistence.settings_manager and persistence.settings_manager.has_hf_token():
            token = persistence.settings_manager.get("hf_token")
            headers["Authorization"] = f"Bearer {token}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    task.file_url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=settings.DOWNLOAD_TIMEOUT)
                ) as response:
                    if response.status != 200:
                        # Provide helpful error messages for common HTTP errors
                        error_msg = f"HTTP {response.status}"
                        if response.status == 401:
                            error_msg = "HTTP 401 - Authentication required. Check your HuggingFace token."
                        elif response.status == 403:
                            error_msg = "HTTP 403 - Access denied. You may need to accept the license agreement on HuggingFace."
                        elif response.status == 404:
                            error_msg = "HTTP 404 - File not found. The URL may be incorrect."
                        raise Exception(error_msg)

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
                                task.progress = min((task.downloaded_bytes / task.total_bytes) * 100, 100.0)
                            else:
                                # Unknown total - show downloaded bytes instead of percentage
                                task.progress = -1  # Signal unknown progress

                            # Broadcast progress
                            await broadcast_download_progress(task.preset_id, {
                                "file": task.file_path,
                                "progress": task.progress,
                                "downloaded": task.downloaded_bytes,
                                "total": task.total_bytes,
                                "status": task.status
                            })

            # Check if we exited due to pause/cancel
            if task.status in ("paused", "cancelled"):
                await broadcast_download_progress(task.preset_id, {
                    "file": task.file_path,
                    "progress": task.progress,
                    "downloaded": task.downloaded_bytes,
                    "total": task.total_bytes,
                    "status": task.status
                })
                return  # Exit without marking as completed

            # Verify checksum if provided
            if task.checksum:
                try:
                    algorithm, expected_hash = parse_checksum(task.checksum)

                    # Broadcast verifying status
                    await broadcast_download_progress(task.preset_id, {
                        "file": task.file_path,
                        "progress": 100.0,
                        "status": "verifying",
                        "message": "Verifying file integrity..."
                    })

                    # Calculate hash of downloaded file
                    actual_hash = calculate_sha256(full_path)

                    if actual_hash != expected_hash:
                        # Checksum mismatch - delete file and raise error
                        error_msg = f"Checksum verification failed: expected {expected_hash[:16}..., got {actual_hash[:16]}..."
                        print(f"Checksum mismatch for {task.file_path}: {error_msg}")

                        # Delete corrupted file
                        if full_path.exists():
                            full_path.unlink()

                        task.checksum_verified = False
                        raise Exception(error_msg)

                    # Checksum verified successfully
                    task.checksum_verified = True
                    print(f"Checksum verified for {task.file_path}: {algorithm}:{actual_hash[:16]}...")

                except ValueError as e:
                    # Invalid checksum format - log warning but don't fail download
                    print(f"Warning: Invalid checksum format for {task.file_path}: {e}")
                    task.checksum_verified = None
            else:
                # No checksum provided - skip verification
                task.checksum_verified = None

            task.status = "completed"
            task.completed_at = datetime.utcnow()
            task.progress = 100.0

            # Invalidate preset cache since files changed
            from ..api.presets import preset_cache
            preset_cache.invalidate_installed()

            # Record activity for completed download
            add_activity(
                activity_type="download",
                status="completed",
                title="Model download completed",
                subtitle=task.preset_id
            )

            # Broadcast completion
            await broadcast_download_progress(task.preset_id, {
                "file": task.file_path,
                "progress": 100.0,
                "status": "completed"
            })

        except Exception as e:
            # Log to console for debugging
            print(f"Download failed for {task.file_path}: {e}")

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
                    "downloaded": t.downloaded_bytes,
                    "total": t.total_bytes,
                    "error": t.error,
                    "checksum": t.checksum,
                    "checksum_verified": t.checksum_verified
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
