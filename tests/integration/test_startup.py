"""
Integration tests for startup script functionality
Tests complete startup workflow including config generation, health checks, and service initialization
"""

import pytest
import subprocess
import time
import yaml
from pathlib import Path
from unittest.mock import patch, Mock

# Mark all tests as integration tests
pytestmark = pytest.mark.integration


@pytest.mark.integration
class TestStartupScriptExecution:
    """Test startup script execution and initialization"""

    def test_start_script_exists(self):
        """Test that start script exists"""
        start_script = Path(__file__).parent.parent.parent / "scripts" / "start.sh"

        assert start_script.exists()
        assert start_script.is_file()

    def test_start_script_executable(self):
        """Test that start script is executable"""
        start_script = Path(__file__).parent.parent.parent / "scripts" / "start.sh"

        # Check if file is executable
        assert os.access(start_script, os.X_OK) or start_script.stat().st_mode & 0o111 != 0

    def test_start_script_syntax(self):
        """Test start script has valid bash syntax"""
        start_script = Path(__file__).parent.parent.parent / "scripts" / "start.sh"

        result = subprocess.run(
            ["bash", "-n", str(start_script)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Syntax error: {result.stderr}"

    def test_config_generator_integration(self, temp_dir):
        """Test config generator as part of startup"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        from generate_extra_model_paths import ConfigGenerator

        config_path = temp_dir / "extra_model_paths.yaml"
        workspace_path = temp_dir / "workspace"
        workspace_path.mkdir()

        generator = ConfigGenerator(
            workspace_path=workspace_path,
            config_path=config_path
        )

        config = generator.generate()
        generator.save(config, config_path)

        assert config_path.exists()

        # Verify generated config is valid
        with open(config_path, 'r') as f:
            loaded_config = yaml.safe_load(f)

        assert 'comfyui' in loaded_config
        assert 'models' in loaded_config['comfyui']

    def test_health_check_integration(self, temp_dir):
        """Test health check as part of startup"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        from health_check import HealthChecker, HealthCheckConfig

        # Create minimal directory structure
        workspace = temp_dir / "workspace"
        workspace.mkdir()

        comfyui = workspace / "ComfyUI"
        comfyui.mkdir()

        for file in ["main.py", "server.py", "folder_paths.py"]:
            (comfyui / file).write_text("# test")

        (comfyui / "custom_nodes").mkdir()
        (comfyui / "models").mkdir()

        config = HealthCheckConfig()
        config.WORKSPACE_ROOT = workspace
        config.COMFYUI_ROOT = comfyui
        config.MODELS_ROOT = comfyui / "models"

        checker = HealthChecker(config=config)
        summary = checker.run_checks(include_services=False)

        assert summary.total_checks > 0
        assert summary.overall_status.value in ["healthy", "warning", "critical"]


@pytest.mark.integration
class TestPresetDownloaderIntegration:
    """Test preset downloader integration with startup"""

    def test_downloader_module_exists(self):
        """Test downloader module exists"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        try:
            import download_manager
            assert download_manager is not None
        except ImportError:
            pytest.skip("Download manager not available")

    def test_unified_downloader_exists(self):
        """Test unified downloader script exists"""
        unified_script = Path(__file__).parent.parent.parent / "scripts" / "unified_preset_downloader.py"

        assert unified_script.exists()

    def test_unified_downloader_syntax(self):
        """Test unified downloader has valid syntax"""
        unified_script = Path(__file__).parent.parent.parent / "scripts" / "unified_preset_downloader.py"

        result = subprocess.run(
            ["python", "-m", "py_compile", str(unified_script)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Syntax error: {result.stderr}"

    def test_preset_config_structure(self, temp_dir):
        """Test preset configuration structure for downloader"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        # Create test preset config
        config_path = temp_dir / "presets.yaml"

        test_config = {
            'presets': {
                'TEST_PRESET': {
                    'name': 'Test Preset',
                    'category': 'Test',
                    'type': 'test',
                    'description': 'Test description',
                    'download_size': '1GB',
                    'files': [
                        {
                            'path': 'checkpoints/test.safetensors',
                            'url': 'https://example.com/test.safetensors',
                            'size': '1GB'
                        }
                    ],
                    'use_case': 'Testing',
                    'tags': ['test']
                }
            }
        }

        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)

        # Verify config can be loaded
        with open(config_path, 'r') as f:
            loaded = yaml.safe_load(f)

        assert 'presets' in loaded
        assert 'TEST_PRESET' in loaded['presets']
        assert 'files' in loaded['presets']['TEST_PRESET']


@pytest.mark.integration
class TestModelValidatorIntegration:
    """Test model validator integration"""

    def test_validator_module_exists(self):
        """Test validator module exists"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        try:
            import model_validator
            assert model_validator is not None
        except ImportError:
            pytest.skip("Model validator not available")

    def test_validator_script_syntax(self):
        """Test validator script has valid syntax"""
        validator_script = Path(__file__).parent.parent.parent / "scripts" / "model_validator.py"

        result = subprocess.run(
            ["python", "-m", "py_compile", str(validator_script)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Syntax error: {result.stderr}"

    def test_validator_with_sample_files(self, temp_dir):
        """Test validator with sample model files"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        try:
            from model_validator import ModelValidator

            # Create test models directory
            models_dir = temp_dir / "models"
            models_dir.mkdir()

            checkpoints_dir = models_dir / "checkpoints"
            checkpoints_dir.mkdir()

            # Create test model file
            test_model = checkpoints_dir / "test.safetensors"
            test_model.write_bytes(b"\x00" * 1024 * 1024)  # 1MB file

            validator = ModelValidator(models_dir=str(models_dir))

            # Test file usability check
            is_usable, error = validator._validate_file_usability(test_model)

            assert is_usable is True
            assert error == ""

        except ImportError:
            pytest.skip("Model validator not available")


@pytest.mark.integration
class TestDashboardIntegration:
    """Test dashboard integration with startup"""

    def test_dashboard_module_exists(self):
        """Test dashboard module exists"""
        dashboard_path = Path(__file__).parent.parent.parent / "app" / "dashboard"

        assert dashboard_path.exists()
        assert dashboard_path.is_dir()

    def test_dashboard_main_module(self):
        """Test dashboard main module exists and is importable"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        try:
            from app.dashboard.main import app
            assert app is not None
        except ImportError as e:
            pytest.skip(f"Dashboard main module not importable: {e}")

    def test_dashboard_api_modules(self):
        """Test dashboard API modules exist"""
        api_path = Path(__file__).parent.parent.parent / "app" / "dashboard" / "api"

        assert api_path.exists()

        # Check for expected API modules
        expected_modules = [
            "__init__.py",
            "presets.py",
            "models.py",
            "workflows.py",
            "system.py"
        ]

        for module in expected_modules:
            module_path = api_path / module
            assert module_path.exists(), f"API module {module} not found"

    def test_dashboard_api_import(self):
        """Test dashboard API can be imported"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        try:
            from app.dashboard.api import api_router
            assert api_router is not None
        except ImportError as e:
            pytest.skip(f"Dashboard API not importable: {e}")


@pytest.mark.integration
class TestWebSocketIntegration:
    """Test WebSocket integration for real-time updates"""

    def test_websocket_module_exists(self):
        """Test WebSocket module exists"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        websocket_path = Path(__file__).parent.parent.parent / "app" / "dashboard" / "core" / "websocket.py"

        assert websocket_path.exists()

    def test_websocket_import(self):
        """Test WebSocket can be imported"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        try:
            from app.dashboard.core.websocket import ConnectionManager
            assert ConnectionManager is not None
        except ImportError:
            pytest.skip("WebSocket module not importable")


@pytest.mark.integration
class TestConfigFileGeneration:
    """Test configuration file generation integration"""

    def test_extra_model_paths_generation(self, temp_dir):
        """Test extra_model_paths.yaml generation"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        try:
            from generate_extra_model_paths import ConfigGenerator

            workspace = temp_dir / "workspace"
            workspace.mkdir()

            models_dir = workspace / "ComfyUI" / "models"
            models_dir.mkdir(parents=True)

            config_path = temp_dir / "extra_model_paths.yaml"

            generator = ConfigGenerator(
                workspace_path=workspace,
                config_path=config_path
            )

            config = generator.generate()
            generator.save(config, config_path)

            # Verify file exists and is valid
            assert config_path.exists()

            with open(config_path, 'r') as f:
                loaded = yaml.safe_load(f)

            assert 'comfyui' in loaded
            assert 'models' in loaded['comfyui']

            # Verify standard model paths
            expected_paths = [
                'checkpoints', 'vae', 'loras', 'text_encoders',
                'clip_vision', 'upscale_models'
            ]

            for path in expected_paths:
                assert path in loaded['comfyui']['models']

        except ImportError:
            pytest.skip("Config generator not importable")

    def test_config_file_locations(self, temp_dir):
        """Test config files are created in correct locations"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        try:
            from generate_extra_model_paths import ConfigGenerator

            workspace = temp_dir / "workspace"
            workspace.mkdir()

            models_dir = workspace / "ComfyUI" / "models"
            models_dir.mkdir(parents=True)

            # Test multiple config locations
            config_locations = [
                workspace / "extra_model_paths.yaml",
                Path("/config") / "extra_model_paths.yaml"
            ]

            generator = ConfigGenerator(
                workspace_path=workspace,
                config_path=temp_dir / "config.yaml"
            )

            for config_path in config_locations:
                if not config_path.parent.exists():
                    config_path.parent.mkdir(parents=True, exist_ok=True)

                config = generator.generate()
                generator.save(config, config_path)

                assert config_path.exists()

        except ImportError:
            pytest.skip("Config generator not importable")


@pytest.mark.integration
class TestEnvironmentIntegration:
    """Test environment variable integration"""

    def test_workspace_path_env(self, temp_dir, monkeypatch):
        """Test WORKSPACE_PATH environment variable"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        workspace = temp_dir / "custom_workspace"
        workspace.mkdir()

        monkeypatch.setenv("WORKSPACE_PATH", str(workspace))

        try:
            from generate_extra_model_paths import parse_environment_vars

            env_vars = {
                "WORKSPACE_PATH": str(workspace)
            }

            result = parse_environment_vars(env_vars)

            assert "workspace" in result
            assert result["workspace"] == str(workspace)

        except ImportError:
            pytest.skip("Environment parser not importable")

    def test_model_path_env(self, temp_dir, monkeypatch):
        """Test MODEL_PATH_* environment variables"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        monkeypatch.setenv("MODEL_PATH_CHECKPOINTS", "/custom/checkpoints")
        monkeypatch.setenv("MODEL_PATH_VAE", "/custom/vae")

        try:
            from generate_extra_model_paths import parse_environment_vars

            env_vars = {
                "MODEL_PATH_CHECKPOINTS": "/custom/checkpoints",
                "MODEL_PATH_VAE": "/custom/vae"
            }

            result = parse_environment_vars(env_vars)

            assert "checkpoints" in result
            assert result["checkpoints"] == "/custom/checkpoints"
            assert result["vae"] == "/custom/vae"

        except ImportError:
            pytest.skip("Environment parser not importable")


@pytest.mark.integration
class TestServiceDependencies:
    """Test service dependencies and startup order"""

    def test_python_dependencies(self):
        """Test Python dependencies can be imported"""
        required_modules = [
            "yaml",
            "pathlib",
            "asyncio",
            "typing"
        ]

        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                pytest.fail(f"Required module {module} not available")

    def test_dashboard_dependencies(self):
        """Test dashboard dependencies can be imported"""
        required_modules = [
            "fastapi",
            "uvicorn",
            "pydantic"
        ]

        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                pytest.skip(f"Dashboard dependency {module} not available")

    def test_download_dependencies(self):
        """Test download manager dependencies"""
        required_modules = [
            "aiohttp",
            "asyncio"
        ]

        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                pytest.skip(f"Download dependency {module} not available")


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling in integration scenarios"""

    def test_missing_workspace_handling(self, temp_dir):
        """Test handling of missing workspace directory"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        try:
            from health_check import HealthChecker, HealthCheckConfig

            config = HealthCheckConfig()
            config.WORKSPACE_ROOT = temp_dir / "nonexistent"

            checker = HealthChecker(config=config)
            result = checker.check_workspace_mount()

            # Should return critical status, not raise exception
            assert result.status.value == "critical"
            assert "not found" in result.message.lower()

        except ImportError:
            pytest.skip("Health checker not importable")

    def test_invalid_config_handling(self, temp_dir):
        """Test handling of invalid configuration files"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        # Create invalid YAML file
        invalid_config = temp_dir / "invalid.yaml"
        invalid_config.write_text("invalid: yaml: [unclosed")

        try:
            import yaml
            with open(invalid_config, 'r') as f:
                with pytest.raises(yaml.YAMLError):
                    yaml.safe_load(f)

        except ImportError:
            pytest.skip("YAML module not available")

    def test_permission_error_handling(self, temp_dir):
        """Test handling of permission errors"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        try:
            from model_validator import ModelValidator

            # Create test file
            test_file = temp_dir / "test.safetensors"
            test_file.write_bytes(b"\x00" * 100)

            validator = ModelValidator(models_dir=str(temp_dir))

            # Remove read permissions
            test_file.chmod(0o000)

            is_usable, error = validator._validate_file_usability(test_file)

            assert is_usable is False
            assert "permission" in error.lower() or "readable" in error.lower()

            # Cleanup
            test_file.chmod(0o644)

        except ImportError:
            pytest.skip("Model validator not importable")


@pytest.mark.integration
class TestWorkflowIntegration:
    """Test complete workflow integration"""

    def test_config_and_validation_workflow(self, temp_dir):
        """Test workflow: config generation -> validation"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        try:
            from generate_extra_model_paths import ConfigGenerator
            from health_check import HealthChecker, HealthCheckConfig

            # Setup
            workspace = temp_dir / "workspace"
            workspace.mkdir()

            # Generate config
            config_path = temp_dir / "config.yaml"
            generator = ConfigGenerator(
                workspace_path=workspace,
                config_path=config_path
            )

            config = generator.generate()
            generator.save(config, config_path)

            assert config_path.exists()

            # Run health check
            health_config = HealthCheckConfig()
            health_config.WORKSPACE_ROOT = workspace
            health_config.CONFIG_ROOT = temp_dir

            checker = HealthChecker(config=health_config)
            summary = checker.run_checks(checks=["workspace"], include_services=False)

            assert summary.total_checks == 1

        except ImportError:
            pytest.skip("Required modules not importable")

    def test_preset_and_download_workflow(self, temp_dir):
        """Test workflow: preset config -> download setup"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

        # Create preset config
        config_path = temp_dir / "presets.yaml"

        preset_config = {
            'presets': {
                'TEST_PRESET': {
                    'name': 'Test Preset',
                    'category': 'Test',
                    'type': 'test',
                    'description': 'Test',
                    'download_size': '1GB',
                    'files': [
                        {
                            'path': 'checkpoints/test.safetensors',
                            'url': 'https://example.com/test.safetensors',
                            'size': '1GB'
                        }
                    ],
                    'use_case': 'Test',
                    'tags': ['test']
                }
            }
        }

        with open(config_path, 'w') as f:
            yaml.dump(preset_config, f)

        try:
            from download_manager import DownloadManager

            models_dir = temp_dir / "models"
            models_dir.mkdir()

            manager = DownloadManager(
                model_base_path=str(models_dir),
                preset_config_path=str(config_path)
            )

            presets = manager.get_available_presets()

            assert "TEST_PRESET" in presets

        except ImportError:
            pytest.skip("Download manager not importable")
