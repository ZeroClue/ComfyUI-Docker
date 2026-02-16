"""
Performance tests for ComfyUI-Docker
Benchmarks container startup, download speeds, dashboard response times, and resource usage
"""

import pytest
import time
import psutil
import threading
from pathlib import Path
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor

# Mark all tests as performance tests
pytestmark = pytest.mark.performance


@pytest.mark.performance
class TestContainerStartupPerformance:
    """Test container startup performance benchmarks"""

    @pytest.mark.slow
    def test_import_time(self):
        """Test module import time"""
        start_time = time.time()

        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

            # Import key modules
            import yaml
            from pathlib import Path
            import asyncio

            elapsed = time.time() - start_time

            # Imports should complete in reasonable time
            assert elapsed < 5.0, f"Module imports took {elapsed:.2f}s, expected < 5.0s"

        except ImportError as e:
            pytest.skip(f"Module import failed: {e}")

    @pytest.mark.slow
    def test_config_generation_time(self, temp_dir):
        """Test configuration generation performance"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        try:
            from generate_extra_model_paths import ConfigGenerator

            start_time = time.time()

            workspace = temp_dir / "workspace"
            workspace.mkdir()

            config_path = temp_dir / "config.yaml"

            generator = ConfigGenerator(
                workspace_path=workspace,
                config_path=config_path
            )

            config = generator.generate()
            generator.save(config, config_path)

            elapsed = time.time() - start_time

            # Config generation should be fast
            assert elapsed < 1.0, f"Config generation took {elapsed:.2f}s, expected < 1.0s"

        except ImportError:
            pytest.skip("Config generator not available")

    @pytest.mark.slow
    def test_health_check_time(self, temp_dir):
        """Test health check execution time"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        try:
            from health_check import HealthChecker, HealthCheckConfig

            # Setup minimal structure
            workspace = temp_dir / "workspace"
            workspace.mkdir()

            config = HealthCheckConfig()
            config.WORKSPACE_ROOT = workspace

            checker = HealthChecker(config=config)

            start_time = time.time()
            summary = checker.run_checks(checks=["workspace"], include_services=False)
            elapsed = time.time() - start_time

            # Health check should be fast
            assert elapsed < 2.0, f"Health check took {elapsed:.2f}s, expected < 2.0s"

        except ImportError:
            pytest.skip("Health checker not available")


@pytest.mark.performance
class TestDownloadPerformance:
    """Test download performance benchmarks"""

    def test_download_manager_initialization(self, temp_dir):
        """Test download manager initialization time"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        try:
            from download_manager import DownloadManager

            start_time = time.time()

            config_path = temp_dir / "presets.yaml"
            models_dir = temp_dir / "models"

            manager = DownloadManager(
                model_base_path=str(models_dir),
                preset_config_path=str(config_path)
            )

            elapsed = time.time() - start_time

            # Initialization should be fast
            assert elapsed < 1.0, f"Initialization took {elapsed:.2f}s, expected < 1.0s"

        except ImportError:
            pytest.skip("Download manager not available")

    def test_preset_queueing_time(self, temp_dir, mock_yaml_config):
        """Test preset queueing performance"""
        import sys
        import yaml
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        try:
            from download_manager import DownloadManager

            # Create preset config
            config_path = temp_dir / "presets.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(mock_yaml_config, f)

            models_dir = temp_dir / "models"

            manager = DownloadManager(
                model_base_path=str(models_dir),
                preset_config_path=str(config_path)
            )

            # Measure queueing time
            start_time = time.time()

            for preset_id in mock_yaml_config['presets'].keys():
                manager.queue_preset(preset_id)

            elapsed = time.time() - start_time

            # Queueing should be very fast
            assert elapsed < 0.5, f"Queueing took {elapsed:.2f}s, expected < 0.5s"

        except ImportError:
            pytest.skip("Download manager not available")


@pytest.mark.performance
class TestDashboardPerformance:
    """Test dashboard response time performance"""

    @pytest.mark.asyncio
    async def test_health_response_time(self):
        """Test health endpoint response time"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        start_time = time.time()
        response = client.get("/health")
        elapsed = time.time() - start_time

        assert response.status_code == 200
        assert elapsed < 0.5, f"Health check took {elapsed:.2f}s, expected < 0.5s"

    @pytest.mark.asyncio
    async def test_api_response_time(self):
        """Test API response time"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        start_time = time.time()
        response = client.get("/api/models/types")
        elapsed = time.time() - start_time

        # API should respond quickly
        assert elapsed < 2.0, f"API request took {elapsed:.2f}s, expected < 2.0s"

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient
        import concurrent.futures

        client = TestClient(app)

        def make_request():
            start = time.time()
            response = client.get("/health")
            elapsed = time.time() - start
            return elapsed

        # Make 10 concurrent requests
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            elapsed_times = [f.result() for f in futures]

        total_elapsed = time.time() - start_time

        # All requests should complete in reasonable time
        assert total_elapsed < 5.0, f"Concurrent requests took {total_elapsed:.2f}s, expected < 5.0s"

        # Individual request times should be reasonable
        avg_time = sum(elapsed_times) / len(elapsed_times)
        assert avg_time < 1.0, f"Average request time {avg_time:.2f}s, expected < 1.0s"


@pytest.mark.performance
class TestMemoryUsage:
    """Test memory usage benchmarks"""

    def test_config_generation_memory(self, temp_dir):
        """Test memory usage during config generation"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        try:
            from generate_extra_model_paths import ConfigGenerator

            # Get initial memory
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Generate config
            workspace = temp_dir / "workspace"
            workspace.mkdir()

            config_path = temp_dir / "config.yaml"

            generator = ConfigGenerator(
                workspace_path=workspace,
                config_path=config_path
            )

            config = generator.generate()
            generator.save(config, config_path)

            # Get final memory
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            # Memory increase should be reasonable
            assert memory_increase < 50, f"Memory increased by {memory_increase:.2f}MB, expected < 50MB"

        except ImportError:
            pytest.skip("Config generator not available")

    def test_download_manager_memory(self, temp_dir):
        """Test memory usage of download manager"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        try:
            from download_manager import DownloadManager

            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Create manager
            config_path = temp_dir / "presets.yaml"
            models_dir = temp_dir / "models"

            manager = DownloadManager(
                model_base_path=str(models_dir),
                preset_config_path=str(config_path)
            )

            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            # Memory increase should be reasonable
            assert memory_increase < 100, f"Memory increased by {memory_increase:.2f}MB, expected < 100MB"

        except ImportError:
            pytest.skip("Download manager not available")


@pytest.mark.performance
class TestCPUUsage:
    """Test CPU usage benchmarks"""

    def test_config_generation_cpu(self, temp_dir):
        """Test CPU usage during config generation"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        try:
            from generate_extra_model_paths import ConfigGenerator

            # Monitor CPU during config generation
            process = psutil.Process()

            workspace = temp_dir / "workspace"
            workspace.mkdir()

            config_path = temp_dir / "config.yaml"

            generator = ConfigGenerator(
                workspace_path=workspace,
                config_path=config_path
            )

            # Generate config and measure CPU
            config = generator.generate()
            generator.save(config, config_path)

            # Get CPU percent
            cpu_percent = process.cpu_percent(interval=0.1)

            # CPU usage should be reasonable (not 100% for extended period)
            assert cpu_percent < 100, f"CPU usage was {cpu_percent}%, expected < 100%"

        except ImportError:
            pytest.skip("Config generator not available")


@pytest.mark.performance
class TestFileOperations:
    """Test file operation performance"""

    def test_large_yaml_write(self, temp_dir):
        """Test writing large YAML files"""
        import yaml

        # Create large config
        large_config = {
            'presets': {
                f'PRESET_{i}': {
                    'name': f'Preset {i}',
                    'category': 'Test',
                    'type': 'test',
                    'description': f'Test preset {i}',
                    'download_size': '1GB',
                    'files': [
                        {
                            'path': f'models/file{j}.safetensors',
                            'url': f'https://example.com/file{j}.safetensors',
                            'size': '500MB'
                        }
                        for j in range(10)
                    ],
                    'use_case': 'Test',
                    'tags': ['test', f'tag{i}']
                }
                for i in range(100)
            }
        }

        config_path = temp_dir / "large_config.yaml"

        start_time = time.time()
        with open(config_path, 'w') as f:
            yaml.dump(large_config, f)
        elapsed = time.time() - start_time

        # Should write large files quickly
        assert elapsed < 1.0, f"Writing large YAML took {elapsed:.2f}s, expected < 1.0s"

    def test_large_yaml_read(self, temp_dir):
        """Test reading large YAML files"""
        import yaml

        # Create large config
        large_config = {
            'presets': {
                f'PRESET_{i}': {
                    'name': f'Preset {i}',
                    'category': 'Test',
                    'files': []
                }
                for i in range(100)
            }
        }

        config_path = temp_dir / "large_config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(large_config, f)

        # Measure read time
        start_time = time.time()
        with open(config_path, 'r') as f:
            loaded = yaml.safe_load(f)
        elapsed = time.time() - start_time

        # Should read large files quickly
        assert elapsed < 1.0, f"Reading large YAML took {elapsed:.2f}s, expected < 1.0s"


@pytest.mark.performance
class TestScalability:
    """Test system scalability benchmarks"""

    def test_many_presets_handling(self, temp_dir):
        """Test handling of many presets"""
        import sys
        import yaml
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        try:
            from download_manager import DownloadManager

            # Create config with many presets
            config = {
                'presets': {
                    f'PRESET_{i}': {
                        'name': f'Preset {i}',
                        'category': 'Test',
                        'files': [
                            {
                                'path': f'models/model{i}.safetensors',
                                'url': f'https://example.com/model{i}.safetensors',
                                'size': '1GB'
                            }
                        ]
                    }
                    for i in range(50)
                }
            }

            config_path = temp_dir / "presets.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(config, f)

            models_dir = temp_dir / "models"

            # Measure manager creation time
            start_time = time.time()
            manager = DownloadManager(
                model_base_path=str(models_dir),
                preset_config_path=str(config_path)
            )
            elapsed = time.time() - start_time

            # Should handle many presets efficiently
            assert elapsed < 2.0, f"Handling 50 presets took {elapsed:.2f}s, expected < 2.0s"

            # Test getting available presets
            start_time = time.time()
            presets = manager.get_available_presets()
            elapsed = time.time() - start_time

            assert len(presets) == 50
            assert elapsed < 0.5, f"Getting presets took {elapsed:.2f}s, expected < 0.5s"

        except ImportError:
            pytest.skip("Download manager not available")

    def test_concurrent_file_operations(self, temp_dir):
        """Test concurrent file operations"""
        import yaml
        from concurrent.futures import ThreadPoolExecutor

        def create_config(index):
            config = {
                'presets': {
                    f'PRESET_{index}': {
                        'name': f'Preset {index}',
                        'category': 'Test',
                        'files': []
                    }
                }
            }

            config_path = temp_dir / f"config_{index}.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(config, f)

            return config_path

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_config, i) for i in range(20)]
            results = [f.result() for f in futures]

        elapsed = time.time() - start_time

        # Concurrent operations should be efficient
        assert elapsed < 2.0, f"Concurrent file ops took {elapsed:.2f}s, expected < 2.0s"
        assert len(results) == 20


@pytest.mark.performance
class TestPerformanceRegression:
    """Performance regression tests to catch slowdowns"""

    def test_validation_performance(self, temp_dir):
        """Test model validation performance"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        try:
            from model_validator import ModelValidator

            # Create test model files
            models_dir = temp_dir / "models"
            models_dir.mkdir()

            for i in range(10):
                subdir = models_dir / f"checkpoints{i}"
                subdir.mkdir()
                model_file = subdir / f"model{i}.safetensors"
                model_file.write_bytes(b"\x00" * 1024 * 1024)  # 1MB

            validator = ModelValidator(models_dir=str(models_dir))

            start_time = time.time()

            # Validate all files
            for i in range(10):
                file_path = models_dir / f"checkpoints{i}" / f"model{i}.safetensors"
                is_usable, _ = validator._validate_file_usability(file_path)

            elapsed = time.time() - start_time

            # Validation should be fast
            assert elapsed < 1.0, f"Validating 10 files took {elapsed:.2f}s, expected < 1.0s"

        except ImportError:
            pytest.skip("Model validator not available")


@pytest.mark.performance
class TestNetworkPerformance:
    """Test network-related performance"""

    def test_dns_lookup_time(self):
        """Test DNS lookup performance"""
        import socket

        start_time = time.time()
        try:
            socket.gethostbyname("example.com")
            elapsed = time.time() - start_time

            # DNS lookup should be fast
            assert elapsed < 2.0, f"DNS lookup took {elapsed:.2f}s, expected < 2.0s"
        except socket.gaierror:
            pytest.skip("Network not available")


@pytest.mark.performance
class TestBenchmarkBaselines:
    """Establish and verify performance baselines"""

    @pytest.fixture
    def baseline_metrics(self):
        """Define baseline performance metrics"""
        return {
            'config_generation_time': 1.0,  # seconds
            'health_check_time': 2.0,  # seconds
            'api_response_time': 2.0,  # seconds
            'memory_increase_limit': 100,  # MB
            'concurrent_request_limit': 5.0,  # seconds for 10 requests
        }

    def test_verify_baseline_config_generation(self, temp_dir, baseline_metrics):
        """Verify config generation meets baseline"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        try:
            from generate_extra_model_paths import ConfigGenerator

            workspace = temp_dir / "workspace"
            workspace.mkdir()

            config_path = temp_dir / "config.yaml"

            generator = ConfigGenerator(
                workspace_path=workspace,
                config_path=config_path
            )

            start_time = time.time()
            config = generator.generate()
            generator.save(config, config_path)
            elapsed = time.time() - start_time

            baseline = baseline_metrics['config_generation_time']
            assert elapsed <= baseline, f"Config generation {elapsed:.2f}s exceeds baseline {baseline:.2f}s"

        except ImportError:
            pytest.skip("Config generator not available")

    def test_verify_baseline_health_check(self, temp_dir, baseline_metrics):
        """Verify health check meets baseline"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        try:
            from health_check import HealthChecker, HealthCheckConfig

            workspace = temp_dir / "workspace"
            workspace.mkdir()

            config = HealthCheckConfig()
            config.WORKSPACE_ROOT = workspace

            checker = HealthChecker(config=config)

            start_time = time.time()
            summary = checker.run_checks(checks=["workspace"], include_services=False)
            elapsed = time.time() - start_time

            baseline = baseline_metrics['health_check_time']
            assert elapsed <= baseline, f"Health check {elapsed:.2f}s exceeds baseline {baseline:.2f}s"

        except ImportError:
            pytest.skip("Health checker not available")
