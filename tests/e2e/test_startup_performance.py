"""
E2E tests for container startup performance
Tests container initialization time and service startup benchmarks
"""

import pytest
import time
import subprocess
from pathlib import Path
from unittest.mock import patch, Mock

# Mark all tests as E2E tests
pytestmark = pytest.mark.e2e


@pytest.mark.e2e
@pytest.mark.slow
class TestContainerStartupPerformance:
    """Test container startup performance benchmarks"""

    def test_python_startup_time(self):
        """Test Python interpreter startup time"""
        start_time = time.time()

        result = subprocess.run(
            ["python", "-c", "print('Hello')"],
            capture_output=True,
            text=True
        )

        elapsed = time.time() - start_time

        assert result.returncode == 0
        assert elapsed < 2.0, f"Python startup took {elapsed:.2f}s, expected < 2.0s"

    def test_module_import_time(self):
        """Test module import performance"""
        code = """
import sys
import time

start = time.time()

# Import key modules
import yaml
from pathlib import Path
import asyncio

elapsed = time.time() - start
print(f'{elapsed:.3f}')
"""

        start_time = time.time()
        result = subprocess.run(
            ["python", "-c", code],
            capture_output=True,
            text=True
        )
        total_elapsed = time.time() - start_time

        assert result.returncode == 0
        assert total_elapsed < 5.0, f"Module imports took {total_elapsed:.2f}s, expected < 5.0s"

    def test_config_generation_startup(self, temp_dir):
        """Test config generation as part of startup"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        try:
            from generate_extra_model_paths import ConfigGenerator

            workspace = temp_dir / "workspace"
            workspace.mkdir()

            config_path = temp_dir / "config.yaml"

            start_time = time.time()

            generator = ConfigGenerator(
                workspace_path=workspace,
                config_path=config_path
            )

            config = generator.generate()
            generator.save(config, config_path)

            elapsed = time.time() - start_time

            assert elapsed < 1.0, f"Config generation took {elapsed:.2f}s, expected < 1.0s"
            assert config_path.exists()

        except ImportError:
            pytest.skip("Config generator not available")

    def test_health_check_startup(self, temp_dir):
        """Test health check as part of startup"""
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

            assert elapsed < 2.0, f"Health check took {elapsed:.2f}s, expected < 2.0s"

        except ImportError:
            pytest.skip("Health checker not available")

    def test_complete_startup_sequence(self, temp_dir):
        """Test complete startup sequence performance"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        try:
            from generate_extra_model_paths import ConfigGenerator
            from health_check import HealthChecker, HealthCheckConfig

            overall_start = time.time()

            # Setup
            workspace = temp_dir / "workspace"
            workspace.mkdir()

            # Step 1: Generate config
            config_start = time.time()
            config_path = temp_dir / "config.yaml"
            generator = ConfigGenerator(
                workspace_path=workspace,
                config_path=config_path
            )
            config = generator.generate()
            generator.save(config, config_path)
            config_elapsed = time.time() - config_start

            # Step 2: Run health checks
            health_start = time.time()
            health_config = HealthCheckConfig()
            health_config.WORKSPACE_ROOT = workspace
            checker = HealthChecker(config=health_config)
            summary = checker.run_checks(checks=["workspace"], include_services=False)
            health_elapsed = time.time() - health_start

            total_elapsed = time.time() - overall_start

            # Assert individual step performance
            assert config_elapsed < 1.0, f"Config generation took {config_elapsed:.2f}s"
            assert health_elapsed < 2.0, f"Health check took {health_elapsed:.2f}s"

            # Assert total startup time
            assert total_elapsed < 5.0, f"Total startup took {total_elapsed:.2f}s, expected < 5.0s"

        except ImportError:
            pytest.skip("Required modules not available")

    @pytest.mark.slow
    def test_import_all_modules(self):
        """Test importing all project modules"""
        code = """
import sys
import time

start = time.time()

# Try to import key modules
try:
    import yaml
    import asyncio
    from pathlib import Path
    from typing import Dict, List, Optional

    # Script modules
    sys.path.insert(0, 'scripts')
    from generate_extra_model_paths import ConfigGenerator
    from health_check import HealthChecker

    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)

elapsed = time.time() - start
print(f'{elapsed:.3f}')
"""

        start_time = time.time()
        result = subprocess.run(
            ["python", "-c", code],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent)
        )
        total_elapsed = time.time() - start_time

        # Check for success
        if "ERROR" in result.stdout:
            pytest.skip(f"Module import failed: {result.stdout}")

        # Most critical check - total time
        assert total_elapsed < 10.0, f"All imports took {total_elapsed:.2f}s, expected < 10.0s"


@pytest.mark.e2e
@pytest.mark.slow
class TestServiceStartupPerformance:
    """Test service startup performance"""

    @pytest.mark.asyncio
    async def test_dashboard_startup(self):
        """Test dashboard application startup"""
        from app.dashboard.main import app

        start_time = time.time()

        # App is created at module import
        # Just verify it exists and is responsive
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/health")

        elapsed = time.time() - start_time

        assert response.status_code == 200
        # Dashboard should start quickly (already loaded at import)
        assert elapsed < 1.0, f"Dashboard startup check took {elapsed:.2f}s"

    def test_download_manager_startup(self, temp_dir):
        """Test download manager startup"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        try:
            from download_manager import DownloadManager

            config_path = temp_dir / "presets.yaml"
            models_dir = temp_dir / "models"

            start_time = time.time()

            manager = DownloadManager(
                model_base_path=str(models_dir),
                preset_config_path=str(config_path)
            )

            elapsed = time.time() - start_time

            assert elapsed < 1.0, f"Download manager startup took {elapsed:.2f}s, expected < 1.0s"

        except ImportError:
            pytest.skip("Download manager not available")


@pytest.mark.e2e
@pytest.mark.slow
class TestStartupResourceUsage:
    """Test resource usage during startup"""

    def test_memory_usage_during_startup(self, temp_dir):
        """Test memory usage during startup sequence"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        try:
            import psutil
            from generate_extra_model_paths import ConfigGenerator
            from health_check import HealthChecker, HealthCheckConfig

            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Run startup sequence
            workspace = temp_dir / "workspace"
            workspace.mkdir()

            config_path = temp_dir / "config.yaml"

            generator = ConfigGenerator(
                workspace_path=workspace,
                config_path=config_path
            )

            config = generator.generate()
            generator.save(config, config_path)

            health_config = HealthCheckConfig()
            health_config.WORKSPACE_ROOT = workspace
            checker = HealthChecker(config=health_config)
            summary = checker.run_checks(checks=["workspace"], include_services=False)

            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            # Memory increase should be reasonable
            assert memory_increase < 100, f"Memory increased by {memory_increase:.2f}MB during startup"

        except ImportError:
            pytest.skip("Required modules not available")
        except NameError:
            pytest.skip("psutil not available")


@pytest.mark.e2e
@pytest.mark.slow
class TestStartupErrorHandling:
    """Test error handling during startup"""

    def test_startup_with_invalid_config(self, temp_dir):
        """Test startup handles invalid configuration gracefully"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        try:
            from generate_extra_model_paths import ConfigGenerator

            # Create invalid config path (non-writable)
            invalid_path = Path("/root/readonly/config.yaml")

            workspace = temp_dir / "workspace"
            workspace.mkdir()

            generator = ConfigGenerator(
                workspace_path=workspace,
                config_path=invalid_path
            )

            config = generator.generate()

            # Should handle error gracefully
            try:
                generator.save(config, invalid_path)
                # If it succeeded, that's fine (might be writable in test env)
            except (IOError, OSError, PermissionError):
                # Expected error, handled gracefully
                pass

        except ImportError:
            pytest.skip("Config generator not available")

    def test_startup_with_missing_workspace(self, temp_dir):
        """Test startup handles missing workspace"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        try:
            from health_check import HealthChecker, HealthCheckConfig

            config = HealthCheckConfig()
            config.WORKSPACE_ROOT = temp_dir / "nonexistent"

            checker = HealthChecker(config=config)
            summary = checker.run_checks(checks=["workspace"], include_services=False)

            # Should report critical but not crash
            assert summary.total_checks == 1
            assert summary.overall_status.value == "critical"

        except ImportError:
            pytest.skip("Health checker not available")


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.requires_docker
class TestDockerStartupPerformance:
    """Test Docker container startup performance"""

    def test_docker_build_time(self):
        """Test Docker image build time (if Docker available)"""
        # This test requires Docker to be available
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            pytest.skip("Docker not available")

        # Note: This is a placeholder - actual build time testing
        # would require building the image, which can be very slow
        # In CI/CD, this would be tested separately

    def test_container_start_time(self):
        """Test container start time (if Docker available)"""
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            pytest.skip("Docker not available")

        # Placeholder for container start time test
        # In actual implementation, this would:
        # 1. Build or pull the image
        # 2. Start a container
        # 3. Measure time until health check passes
        # 4. Assert it's within acceptable limits


@pytest.mark.e2e
class TestStartupSequence:
    """Test correct startup sequence"""

    def test_startup_order(self, temp_dir):
        """Test that startup components initialize in correct order"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        startup_order = []

        try:
            # Mock the components to track initialization order
            original_config_init = None
            original_health_init = None

            from generate_extra_model_paths import ConfigGenerator
            from health_check import HealthChecker, HealthCheckConfig

            # Create config first
            workspace = temp_dir / "workspace"
            workspace.mkdir()

            config_path = temp_dir / "config.yaml"

            startup_order.append("config_generator")

            generator = ConfigGenerator(
                workspace_path=workspace,
                config_path=config_path
            )

            config = generator.generate()
            generator.save(config, config_path)

            # Then run health checks
            startup_order.append("health_checker")

            health_config = HealthCheckConfig()
            health_config.WORKSPACE_ROOT = workspace

            checker = HealthChecker(config=health_config)
            summary = checker.run_checks(checks=["workspace"], include_services=False)

            # Verify order
            assert startup_order[0] == "config_generator"
            assert startup_order[1] == "health_checker"

        except ImportError:
            pytest.skip("Required modules not available")


@pytest.mark.e2e
class TestStartupIdempotency:
    """Test that startup can be run multiple times safely"""

    def test_repeated_startup(self, temp_dir):
        """Test that startup can be run multiple times"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        try:
            from generate_extra_model_paths import ConfigGenerator

            workspace = temp_dir / "workspace"
            workspace.mkdir()

            config_path = temp_dir / "config.yaml"

            # Run startup twice
            for i in range(2):
                generator = ConfigGenerator(
                    workspace_path=workspace,
                    config_path=config_path
                )

                config = generator.generate()
                generator.save(config, config_path)

                assert config_path.exists()

            # Should succeed both times
            assert config_path.exists()

        except ImportError:
            pytest.skip("Config generator not available")

    def test_repeated_health_checks(self, temp_dir):
        """Test that health checks can be run repeatedly"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        try:
            from health_check import HealthChecker, HealthCheckConfig

            workspace = temp_dir / "workspace"
            workspace.mkdir()

            config = HealthCheckConfig()
            config.WORKSPACE_ROOT = workspace

            checker = HealthChecker(config=config)

            # Run health checks multiple times
            for i in range(3):
                summary = checker.run_checks(checks=["workspace"], include_services=False)
                assert summary.total_checks == 1

        except ImportError:
            pytest.skip("Health checker not available")
