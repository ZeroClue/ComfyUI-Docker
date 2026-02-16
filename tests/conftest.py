"""
pytest configuration and shared fixtures for ComfyUI-Docker tests
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Generator, Optional
from unittest.mock import Mock, MagicMock, patch
import pytest
import asyncio
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

# Test configuration
TEST_TIMEOUT = 30
FIXTURES_DIR = Path(__file__).parent / "fixtures"
MOCKS_DIR = Path(__file__).parent / "mocks"


class TestConfig:
    """Test configuration constants"""
    TEST_DATA_DIR = FIXTURES_DIR / "data"
    TEST_MODELS_DIR = FIXTURES_DIR / "models"
    TEST_CONFIG_DIR = FIXTURES_DIR / "config"
    TEMP_DIR = tempfile.mkdtemp(prefix="comfyui_test_")

    # Performance thresholds
    MAX_CONTAINER_STARTUP_TIME = 30.0  # seconds
    MAX_DASHBOARD_RESPONSE_TIME = 2.0  # seconds
    MAX_DOWNLOAD_SPEED_MBPS = 10.0  # minimum MB/s

    # Coverage targets
    MIN_COVERAGE_PERCENTAGE = 80


@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration"""
    return TestConfig


@pytest.fixture(scope="session")
def test_data_dir():
    """Create and provide test data directory"""
    data_dir = TestConfig.TEST_DATA_DIR
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture(scope="session")
def test_models_dir():
    """Create and provide test models directory"""
    models_dir = TestConfig.TEST_MODELS_DIR
    models_dir.mkdir(parents=True, exist_ok=True)

    # Create model subdirectories
    subdirs = [
        "checkpoints", "text_encoders", "vae", "clip_vision",
        "loras", "upscale_models", "audio_encoders", "controlnet"
    ]
    for subdir in subdirs:
        (models_dir / subdir).mkdir(parents=True, exist_ok=True)

    return models_dir


@pytest.fixture(scope="session")
def test_config_dir():
    """Create and provide test config directory"""
    config_dir = TestConfig.TEST_CONFIG_DIR
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    temp_path = Path(tempfile.mkdtemp(prefix="comfyui_test_"))
    yield temp_path
    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def mock_yaml_config():
    """Create mock YAML configuration"""
    return {
        'presets': {
            'TEST_PRESET_1': {
                'name': 'Test Preset 1',
                'category': 'Image Generation',
                'type': 'image',
                'description': 'A test preset',
                'download_size': '1.0GB',
                'files': [
                    {
                        'path': 'checkpoints/test_model.safetensors',
                        'url': 'https://example.com/test.safetensors',
                        'size': '1.0GB'
                    }
                ],
                'use_case': 'Testing',
                'tags': ['test']
            },
            'TEST_PRESET_2': {
                'name': 'Test Preset 2',
                'category': 'Video Generation',
                'type': 'video',
                'description': 'Another test preset',
                'download_size': '2.5GB',
                'files': [
                    {
                        'path': 'checkpoints/test_video.safetensors',
                        'url': 'https://example.com/test_video.safetensors',
                        'size': '2.5GB'
                    },
                    {
                        'path': 'text_encoders/t5.safetensors',
                        'url': 'https://example.com/t5.safetensors',
                        'size': '500MB'
                    }
                ],
                'use_case': 'Testing',
                'tags': ['test', 'video']
            }
        }
    }


@pytest.fixture
def sample_preset_file(test_config_dir, mock_yaml_config):
    """Create sample preset configuration file"""
    import yaml
    preset_file = test_config_dir / "test_presets.yaml"
    with open(preset_file, 'w') as f:
        yaml.dump(mock_yaml_config, f)
    return preset_file


@pytest.fixture
def sample_model_files(test_models_dir):
    """Create sample model files for testing"""
    # Create some test model files
    test_files = {
        'checkpoints/test_model.safetensors': b'\x00\x01\x02\x03' * 1000,  # Small test file
        'vae/test_vae.safetensors': b'\x04\x05\x06\x07' * 500,
        'text_encoders/test_encoder.safetensors': b'\x08\x09\x0A\x0B' * 250,
    }

    created_files = []
    for relative_path, content in test_files.items():
        file_path = test_models_dir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)
        created_files.append(file_path)

    return created_files


@pytest.fixture
def mock_download_manager():
    """Create mock download manager"""
    manager = Mock()
    manager.queue_preset = Mock(return_value=True)
    manager.pause_download = Mock(return_value=True)
    manager.resume_download = Mock(return_value=True)
    manager.cancel_download = Mock(return_value=True)
    manager.get_download_status = Mock(return_value={
        'status': 'completed',
        'progress': 100.0
    })
    manager.get_all_downloads = Mock(return_value={
        'active': {},
        'queued': [],
        'paused': []
    })
    manager.get_available_presets = Mock(return_value={
        'TEST_PRESET': {
            'name': 'Test Preset',
            'category': 'Test',
            'file_count': 1
        }
    })
    return manager


@pytest.fixture
def mock_websocket_broadcaster():
    """Create mock WebSocket broadcaster"""
    broadcaster = Mock()
    broadcaster.broadcast = AsyncMock()
    broadcaster.register_callback = Mock()
    broadcaster.disable = Mock()
    broadcaster.enable = Mock()
    return broadcaster


@pytest.fixture
def mock_comfyui_client():
    """Create mock ComfyUI client"""
    client = Mock()
    client.get_system_info = Mock(return_value={
        'version': '1.0.0',
        'status': 'running'
    })
    client.get_queue_info = Mock(return_value={
        'queue_running': [],
        'queue_pending': []
    })
    client.get_history = Mock(return_value={})
    return client


@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def async_mock():
    """Create async mock for patching async functions"""
    class AsyncMock(MagicMock):
        async def __call__(self, *args, **kwargs):
            return super(AsyncMock, self).__call__(*args, **kwargs)
    return AsyncMock


@pytest.fixture
def mock_http_response():
    """Create mock HTTP response"""
    def _create_response(status_code=200, json_data=None, text_data=None):
        response = Mock()
        response.status_code = status_code
        response.json = Mock(return_value=json_data or {})
        response.text = text_data or ""
        response.raise_for_status = Mock()
        if status_code >= 400:
            response.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
        return response
    return _create_response


@pytest.fixture
def docker_container_mock():
    """Create mock Docker container"""
    container = Mock()
    container.id = "test_container_id"
    container.name = "test_comfyui_container"
    container.status = "running"
    container.logs = Mock(return_value=b"Container logs")
    container.stop = Mock()
    container.start = Mock()
    container.remove = Mock()
    container.exec_run = Mock(return_value=(0, b"output"))
    return container


@pytest.fixture
def docker_client_mock(docker_container_mock):
    """Create mock Docker client"""
    client = Mock()
    client.containers = Mock()
    client.containers.get = Mock(return_value=docker_container_mock)
    client.containers.list = Mock(return_value=[docker_container_mock])
    client.containers.run = Mock(return_value=docker_container_mock)
    client.images = Mock()
    client.images.get = Mock(return_value=Mock())
    client.images.pull = Mock(return_value=Mock())
    return client


@pytest.fixture
def performance_metrics():
    """Fixture to track performance metrics"""
    metrics = {
        'container_startup_time': None,
        'dashboard_response_time': None,
        'download_speed': None,
        'memory_usage': None,
        'cpu_usage': None
    }
    return metrics


@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Automatically clean up temporary files after each test"""
    yield
    # Cleanup any temp files created during test
    temp_pattern = Path("/tmp").glob("comfyui_test_*")
    for temp_path in temp_pattern:
        if temp_path.is_dir():
            shutil.rmtree(temp_path, ignore_errors=True)


# Custom pytest markers
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "requires_docker: Tests requiring Docker")
    config.addinivalue_line("markers", "requires_network: Tests requiring network access")


# Async test support
@pytest.fixture
def async_test_wrapper():
    """Wrapper for running async tests"""
    def run_async(coro):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    return run_async


# Shared helper functions
class TestUtils:
    """Utility functions for tests"""

    @staticmethod
    def create_fake_model_file(path: Path, size_mb: float = 1.0) -> Path:
        """Create a fake model file for testing"""
        path.parent.mkdir(parents=True, exist_ok=True)
        size_bytes = int(size_mb * 1024 * 1024)
        with open(path, 'wb') as f:
            f.write(b'\x00' * size_bytes)
        return path

    @staticmethod
    def wait_for_condition(condition, timeout=5, interval=0.1):
        """Wait for a condition to be true"""
        import time
        start = time.time()
        while time.time() - start < timeout:
            if condition():
                return True
            time.sleep(interval)
        return False

    @staticmethod
    def measure_time(func):
        """Measure execution time of a function"""
        import time
        start = time.time()
        result = func()
        elapsed = time.time() - start
        return result, elapsed


@pytest.fixture
def test_utils():
    """Provide test utilities"""
    return TestUtils
