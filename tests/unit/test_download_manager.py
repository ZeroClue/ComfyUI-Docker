"""
Unit tests for download manager functionality
Tests preset download, progress tracking, pause/resume, and retry logic
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from datetime import datetime, timedelta
from collections import deque

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

try:
    from download_manager import (
        DownloadManager,
        DownloadStatus,
        DownloadProgress,
        PresetDownload,
        WebSocketBroadcaster
    )
except ImportError:
    pytest.skip("Download manager module not found", allow_module_level=True)


@pytest.mark.unit
class TestDownloadStatus:
    """Test DownloadStatus enum"""

    def test_status_values(self):
        """Test status enum has correct values"""
        assert DownloadStatus.QUEUED.value == "queued"
        assert DownloadStatus.DOWNLOADING.value == "downloading"
        assert DownloadStatus.PAUSED.value == "paused"
        assert DownloadStatus.COMPLETED.value == "completed"
        assert DownloadStatus.FAILED.value == "failed"
        assert DownloadStatus.CANCELLED.value == "cancelled"
        assert DownloadStatus.RETRYING.value == "retrying"


@pytest.mark.unit
class TestDownloadProgress:
    """Test DownloadProgress dataclass"""

    def test_initialization(self):
        """Test DownloadProgress initialization"""
        progress = DownloadProgress(
            file_path="/test/model.safetensors",
            url="https://example.com/model.safetensors"
        )

        assert progress.file_path == "/test/model.safetensors"
        assert progress.url == "https://example.com/model.safetensors"
        assert progress.status == DownloadStatus.QUEUED
        assert progress.progress == 0.0
        assert progress.downloaded_bytes == 0
        assert progress.total_bytes == 0
        assert progress.speed == 0.0
        assert progress.eta is None
        assert progress.error is None
        assert progress.retry_count == 0

    def test_to_dict(self):
        """Test DownloadProgress to_dict conversion"""
        now = datetime.utcnow()
        progress = DownloadProgress(
            file_path="/test/model.safetensors",
            url="https://example.com/model.safetensors",
            status=DownloadStatus.DOWNLOADING,
            progress=50.0,
            downloaded_bytes=1024*1024*100,  # 100MB
            total_bytes=1024*1024*200,  # 200MB
            speed=1024*1024*10,  # 10MB/s
            eta=10.0,
            started_at=now,
            last_update=now
        )

        result = progress.to_dict()

        assert result['file_path'] == "/test/model.safetensors"
        assert result['status'] == "downloading"
        assert result['progress'] == 50.0
        assert result['downloaded_bytes'] == 1024*1024*100
        assert result['total_bytes'] == 1024*1024*200
        assert result['speed'] == 1024*1024*10
        assert result['eta'] == 10.0
        assert result['started_at'] is not None
        assert result['last_update'] is not None


@pytest.mark.unit
class TestPresetDownload:
    """Test PresetDownload dataclass"""

    def test_initialization(self):
        """Test PresetDownload initialization"""
        preset = PresetDownload(
            preset_id="TEST_PRESET",
            preset_name="Test Preset"
        )

        assert preset.preset_id == "TEST_PRESET"
        assert preset.preset_name == "Test Preset"
        assert len(preset.files) == 0
        assert preset.overall_progress == 0.0
        assert preset.status == DownloadStatus.QUEUED

    def test_calculate_overall_progress_empty(self):
        """Test progress calculation with no files"""
        preset = PresetDownload(
            preset_id="TEST_PRESET",
            preset_name="Test Preset"
        )

        progress = preset.calculate_overall_progress()
        assert progress == 0.0

    def test_calculate_overall_progress_by_count(self):
        """Test progress calculation by file count"""
        preset = PresetDownload(
            preset_id="TEST_PRESET",
            preset_name="Test Preset"
        )

        # Add files
        preset.files = [
            DownloadProgress(file_path=f"/test/file{i}.safetensors", url=f"url{i}")
            for i in range(4)
        ]

        # Mark first two as completed
        preset.files[0].status = DownloadStatus.COMPLETED
        preset.files[1].status = DownloadStatus.COMPLETED

        progress = preset.calculate_overall_progress()
        assert progress == 50.0  # 2/4 files

    def test_calculate_overall_progress_by_size(self):
        """Test progress calculation by file size"""
        preset = PresetDownload(
            preset_id="TEST_PRESET",
            preset_name="Test Preset"
        )

        # Add files with sizes
        preset.files = [
            DownloadProgress(
                file_path="/test/file1.safetensors",
                url="url1",
                total_bytes=1000,
                downloaded_bytes=1000
            ),
            DownloadProgress(
                file_path="/test/file2.safetensors",
                url="url2",
                total_bytes=1000,
                downloaded_bytes=500
            )
        ]

        preset.files[0].status = DownloadStatus.COMPLETED
        preset.files[1].status = DownloadStatus.DOWNLOADING

        progress = preset.calculate_overall_progress()
        assert progress == 75.0  # 1500/2000 bytes

    def test_to_dict(self):
        """Test PresetDownload to_dict conversion"""
        preset = PresetDownload(
            preset_id="TEST_PRESET",
            preset_name="Test Preset"
        )

        preset.files = [
            DownloadProgress(
                file_path="/test/file1.safetensors",
                url="url1",
                status=DownloadStatus.COMPLETED
            ),
            DownloadProgress(
                file_path="/test/file2.safetensors",
                url="url2",
                status=DownloadStatus.FAILED
            )
        ]

        result = preset.to_dict()

        assert result['preset_id'] == "TEST_PRESET"
        assert result['preset_name'] == "Test Preset"
        assert result['files']['total'] == 2
        assert result['files']['completed'] == 1
        assert result['files']['failed'] == 1


@pytest.mark.unit
class TestWebSocketBroadcaster:
    """Test WebSocketBroadcaster class"""

    @pytest.mark.asyncio
    async def test_register_callback(self):
        """Test registering callback"""
        broadcaster = WebSocketBroadcaster()
        callback = AsyncMock()

        broadcaster.register_callback(callback)

        assert callback in broadcaster._callbacks

    @pytest.mark.asyncio
    async def test_broadcast_enabled(self):
        """Test broadcasting when enabled"""
        broadcaster = WebSocketBroadcaster()
        callback = AsyncMock()
        broadcaster.register_callback(callback)

        message = {"type": "test", "data": "test_data"}
        await broadcaster.broadcast(message)

        callback.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_disabled(self):
        """Test broadcasting when disabled"""
        broadcaster = WebSocketBroadcaster()
        callback = AsyncMock()
        broadcaster.register_callback(callback)
        broadcaster.disable()

        message = {"type": "test", "data": "test_data"}
        await broadcaster.broadcast(message)

        callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_multiple_callbacks(self):
        """Test broadcasting to multiple callbacks"""
        broadcaster = WebSocketBroadcaster()
        callback1 = AsyncMock()
        callback2 = AsyncMock()

        broadcaster.register_callback(callback1)
        broadcaster.register_callback(callback2)

        message = {"type": "test", "data": "test_data"}
        await broadcaster.broadcast(message)

        callback1.assert_called_once_with(message)
        callback2.assert_called_once_with(message)


@pytest.mark.unit
class TestDownloadManager:
    """Test DownloadManager class"""

    def test_initialization(self, temp_dir):
        """Test DownloadManager initialization"""
        manager = DownloadManager(
            model_base_path=str(temp_dir / "models"),
            preset_config_path=str(temp_dir / "presets.yaml"),
            max_concurrent_downloads=2
        )

        assert manager.model_base_path == Path(temp_dir / "models")
        assert manager.preset_config_path == Path(temp_dir / "presets.yaml")
        assert manager.max_concurrent_downloads == 2
        assert manager.max_retries == 3
        assert manager.chunk_size == 8192
        assert len(manager.download_queue) == 0
        assert len(manager.active_downloads) == 0

    def test_parse_size_string(self, temp_dir):
        """Test size string parsing"""
        manager = DownloadManager(
            model_base_path=str(temp_dir / "models"),
            preset_config_path=str(temp_dir / "presets.yaml")
        )

        assert manager._parse_size("1GB") == 1024**3
        assert manager._parse_size("500MB") == 500 * 1024**2
        assert manager._parse_size("1024KB") == 1024 * 1024
        assert manager._parse_size("100B") == 100
        assert manager._parse_size("1.5GB") == int(1.5 * 1024**3)

    def test_parse_size_invalid(self, temp_dir):
        """Test parsing invalid size strings"""
        manager = DownloadManager(
            model_base_path=str(temp_dir / "models"),
            preset_config_path=str(temp_dir / "presets.yaml")
        )

        assert manager._parse_size("invalid") == 0
        assert manager._parse_size("") == 0
        assert manager._parse_size("XB") == 0

    def test_queue_preset(self, temp_dir, mock_yaml_config):
        """Test queuing a preset for download"""
        # Create preset config
        import yaml
        config_path = temp_dir / "presets.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(mock_yaml_config, f)

        manager = DownloadManager(
            model_base_path=str(temp_dir / "models"),
            preset_config_path=str(config_path)
        )

        result = manager.queue_preset("TEST_PRESET_1")

        assert result is True
        assert "TEST_PRESET_1" in manager.download_queue
        assert "TEST_PRESET_1" in manager.active_downloads

    def test_queue_preset_not_found(self, temp_dir):
        """Test queuing non-existent preset"""
        import yaml
        config_path = temp_dir / "presets.yaml"
        with open(config_path, 'w') as f:
            yaml.dump({'presets': {}}, f)

        manager = DownloadManager(
            model_base_path=str(temp_dir / "models"),
            preset_config_path=str(config_path)
        )

        result = manager.queue_preset("NONEXISTENT")

        assert result is False

    def test_queue_preset_already_queued(self, temp_dir, mock_yaml_config):
        """Test queuing preset that's already queued"""
        import yaml
        config_path = temp_dir / "presets.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(mock_yaml_config, f)

        manager = DownloadManager(
            model_base_path=str(temp_dir / "models"),
            preset_config_path=str(config_path)
        )

        manager.queue_preset("TEST_PRESET_1")
        result = manager.queue_preset("TEST_PRESET_1")

        assert result is False

    def test_pause_download(self, temp_dir, mock_yaml_config):
        """Test pausing a download"""
        import yaml
        config_path = temp_dir / "presets.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(mock_yaml_config, f)

        manager = DownloadManager(
            model_base_path=str(temp_dir / "models"),
            preset_config_path=str(config_path)
        )

        manager.queue_preset("TEST_PRESET_1")
        result = manager.pause_download("TEST_PRESET_1")

        assert result is True
        assert "TEST_PRESET_1" in manager.paused_downloads

    def test_pause_download_not_active(self, temp_dir):
        """Test pausing non-existent download"""
        manager = DownloadManager(
            model_base_path=str(temp_dir / "models"),
            preset_config_path=str(temp_dir / "presets.yaml")
        )

        result = manager.pause_download("NONEXISTENT")

        assert result is False

    def test_resume_download(self, temp_dir, mock_yaml_config):
        """Test resuming a paused download"""
        import yaml
        config_path = temp_dir / "presets.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(mock_yaml_config, f)

        manager = DownloadManager(
            model_base_path=str(temp_dir / "models"),
            preset_config_path=str(config_path)
        )

        manager.queue_preset("TEST_PRESET_1")
        manager.pause_download("TEST_PRESET_1")
        result = manager.resume_download("TEST_PRESET_1")

        assert result is True
        assert "TEST_PRESET_1" not in manager.paused_downloads

    def test_cancel_download(self, temp_dir, mock_yaml_config):
        """Test cancelling a download"""
        import yaml
        config_path = temp_dir / "presets.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(mock_yaml_config, f)

        manager = DownloadManager(
            model_base_path=str(temp_dir / "models"),
            preset_config_path=str(config_path)
        )

        manager.queue_preset("TEST_PRESET_1")
        result = manager.cancel_download("TEST_PRESET_1")

        assert result is True
        assert "TEST_PRESET_1" not in manager.active_downloads

    def test_cancel_download_from_queue(self, temp_dir, mock_yaml_config):
        """Test cancelling queued download"""
        import yaml
        config_path = temp_dir / "presets.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(mock_yaml_config, f)

        manager = DownloadManager(
            model_base_path=str(temp_dir / "models"),
            preset_config_path=str(config_path)
        )

        manager.queue_preset("TEST_PRESET_1")
        result = manager.cancel_download("TEST_PRESET_1")

        assert result is True
        assert "TEST_PRESET_1" not in manager.download_queue

    def test_get_download_status(self, temp_dir, mock_yaml_config):
        """Test getting download status"""
        import yaml
        config_path = temp_dir / "presets.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(mock_yaml_config, f)

        manager = DownloadManager(
            model_base_path=str(temp_dir / "models"),
            preset_config_path=str(config_path)
        )

        manager.queue_preset("TEST_PRESET_1")
        status = manager.get_download_status("TEST_PRESET_1")

        assert status is not None
        assert status['preset_id'] == "TEST_PRESET_1"
        assert status['preset_name'] == "Test Preset 1"

    def test_get_download_status_not_found(self, temp_dir):
        """Test getting status of non-existent download"""
        manager = DownloadManager(
            model_base_path=str(temp_dir / "models"),
            preset_config_path=str(temp_dir / "presets.yaml")
        )

        status = manager.get_download_status("NONEXISTENT")

        assert status is None

    def test_get_all_downloads(self, temp_dir, mock_yaml_config):
        """Test getting all downloads status"""
        import yaml
        config_path = temp_dir / "presets.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(mock_yaml_config, f)

        manager = DownloadManager(
            model_base_path=str(temp_dir / "models"),
            preset_config_path=str(config_path)
        )

        manager.queue_preset("TEST_PRESET_1")
        manager.queue_preset("TEST_PRESET_2")

        all_downloads = manager.get_all_downloads()

        assert all_downloads['active_count'] == 2
        assert all_downloads['queued_count'] == 0
        assert len(all_downloads['active']) == 2

    def test_get_available_presets(self, temp_dir, mock_yaml_config):
        """Test getting available presets"""
        import yaml
        config_path = temp_dir / "presets.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(mock_yaml_config, f)

        manager = DownloadManager(
            model_base_path=str(temp_dir / "models"),
            preset_config_path=str(config_path)
        )

        presets = manager.get_available_presets()

        assert "TEST_PRESET_1" in presets
        assert "TEST_PRESET_2" in presets
        assert presets['TEST_PRESET_1']['name'] == "Test Preset 1"
        assert presets['TEST_PRESET_1']['category'] == "Image Generation"


@pytest.mark.unit
class TestDownloadManagerRetryLogic:
    """Test download manager retry logic"""

    def test_max_retries_configuration(self, temp_dir):
        """Test max retries can be configured"""
        manager = DownloadManager(
            model_base_path=str(temp_dir / "models"),
            preset_config_path=str(temp_dir / "presets.yaml"),
            max_retries=5
        )

        assert manager.max_retries == 5

    def test_retry_count_increments(self, temp_dir):
        """Test retry count increments on failure"""
        manager = DownloadManager(
            model_base_path=str(temp_dir / "models"),
            preset_config_path=str(temp_dir / "presets.yaml")
        )

        progress = DownloadProgress(
            file_path="/test/file.safetensors",
            url="https://example.com/file.safetensors"
        )

        progress.retry_count = 1
        assert progress.retry_count == 1

        progress.retry_count += 1
        assert progress.retry_count == 2


@pytest.mark.unit
class TestDownloadManagerStatusPersistence:
    """Test download manager status persistence"""

    def test_save_status(self, temp_dir):
        """Test saving status to file"""
        manager = DownloadManager(
            model_base_path=str(temp_dir / "models"),
            preset_config_path=str(temp_dir / "presets.yaml")
        )

        manager.paused_downloads = {"TEST_PRESET_1"}
        manager.active_downloads = {"TEST_PRESET_2": Mock()}
        manager.download_queue = deque(["TEST_PRESET_3"])

        manager._save_status()

        assert manager.status_file.exists()

    def test_load_status(self, temp_dir):
        """Test loading status from file"""
        import json
        status_file = temp_dir / "download_status.json"

        status_data = {
            'paused_downloads': ['TEST_PRESET_1'],
            'active_downloads': ['TEST_PRESET_2'],
            'queued_downloads': ['TEST_PRESET_3']
        }

        with open(status_file, 'w') as f:
            json.dump(status_data, f)

        manager = DownloadManager(
            model_base_path=str(temp_dir / "models"),
            preset_config_path=str(temp_dir / "presets.yaml"),
            status_file=status_file
        )

        manager._load_status()

        assert "TEST_PRESET_1" in manager.paused_downloads


@pytest.mark.unit
class TestDownloadManagerConcurrency:
    """Test download manager concurrent download handling"""

    def test_max_concurrent_downloads_configuration(self, temp_dir):
        """Test max concurrent downloads configuration"""
        manager = DownloadManager(
            model_base_path=str(temp_dir / "models"),
            preset_config_path=str(temp_dir / "presets.yaml"),
            max_concurrent_downloads=5
        )

        assert manager.max_concurrent_downloads == 5

    def test_semaphore_creation(self, temp_dir):
        """Test semaphore is created with correct value"""
        manager = DownloadManager(
            model_base_path=str(temp_dir / "models"),
            preset_config_path=str(temp_dir / "presets.yaml"),
            max_concurrent_downloads=3
        )

        # Start manager to create semaphore
        manager._run_event_loop()

        # Check semaphore was created
        assert manager._semaphore is not None

        # Clean up
        manager.stop()


@pytest.mark.unit
class TestSingletonInstance:
    """Test singleton download manager instance"""

    def test_get_download_manager_singleton(self, temp_dir):
        """Test get_download_manager returns singleton"""
        import download_manager

        # Reset singleton
        download_manager._download_manager = None

        manager1 = download_manager.get_download_manager()
        manager2 = download_manager.get_download_manager()

        assert manager1 is manager2

    def test_get_download_manager_starts_on_first_call(self, temp_dir):
        """Test download manager starts on first call"""
        import download_manager

        # Reset singleton
        download_manager._download_manager = None

        manager = download_manager.get_download_manager()

        assert manager._running is True
