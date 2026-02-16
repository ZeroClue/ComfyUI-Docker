"""
Unit tests for health check system
Tests workspace mount, model paths, disk space, services, and configuration checks
"""

import pytest
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

try:
    from health_check import (
        HealthChecker,
        HealthCheckConfig,
        HealthCheckResult,
        HealthCheckSummary,
        HealthStatus,
        Colors
    )
except ImportError:
    pytest.skip("Health check module not found", allow_module_level=True)


@pytest.mark.unit
class TestHealthStatus:
    """Test HealthStatus enum"""

    def test_status_values(self):
        """Test status enum has correct values"""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.WARNING.value == "warning"
        assert HealthStatus.CRITICAL.value == "critical"


@pytest.mark.unit
class TestHealthCheckResult:
    """Test HealthCheckResult dataclass"""

    def test_initialization(self):
        """Test HealthCheckResult initialization"""
        result = HealthCheckResult(
            name="Test Check",
            status=HealthStatus.HEALTHY,
            message="Check passed"
        )

        assert result.name == "Test Check"
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "Check passed"
        assert result.details == {}
        assert result.duration_ms == 0.0

    def test_to_dict(self):
        """Test HealthCheckResult to_dict conversion"""
        result = HealthCheckResult(
            name="Test Check",
            status=HealthStatus.WARNING,
            message="Check warning",
            details={"key": "value"},
            duration_ms=123.45
        )

        result_dict = result.to_dict()

        assert result_dict['name'] == "Test Check"
        assert result_dict['status'] == "warning"
        assert result_dict['message'] == "Check warning"
        assert result_dict['details'] == {"key": "value"}
        assert result_dict['duration_ms'] == 123.45


@pytest.mark.unit
class TestHealthCheckSummary:
    """Test HealthCheckSummary dataclass"""

    def test_initialization(self):
        """Test HealthCheckSummary initialization"""
        summary = HealthCheckSummary()

        assert summary.results == []
        assert summary.overall_status == HealthStatus.HEALTHY
        assert summary.total_checks == 0
        assert summary.passed == 0
        assert summary.warnings == 0
        assert summary.critical == 0

    def test_add_result_healthy(self):
        """Test adding healthy result"""
        summary = HealthCheckSummary()
        result = HealthCheckResult(
            name="Test",
            status=HealthStatus.HEALTHY,
            message="OK"
        )

        summary.add_result(result)

        assert summary.total_checks == 1
        assert summary.passed == 1
        assert summary.warnings == 0
        assert summary.critical == 0
        assert summary.overall_status == HealthStatus.HEALTHY

    def test_add_result_warning(self):
        """Test adding warning result"""
        summary = HealthCheckSummary()
        result = HealthCheckResult(
            name="Test",
            status=HealthStatus.WARNING,
            message="Warning"
        )

        summary.add_result(result)

        assert summary.total_checks == 1
        assert summary.passed == 0
        assert summary.warnings == 1
        assert summary.overall_status == HealthStatus.WARNING

    def test_add_result_critical(self):
        """Test adding critical result"""
        summary = HealthCheckSummary()
        result = HealthCheckResult(
            name="Test",
            status=HealthStatus.CRITICAL,
            message="Critical"
        )

        summary.add_result(result)

        assert summary.total_checks == 1
        assert summary.passed == 0
        assert summary.critical == 1
        assert summary.overall_status == HealthStatus.CRITICAL

    def test_overall_status_escalation(self):
        """Test overall status escalation"""
        summary = HealthCheckSummary()

        # Add healthy result
        summary.add_result(HealthCheckResult(
            name="Test1",
            status=HealthStatus.HEALTHY,
            message="OK"
        ))
        assert summary.overall_status == HealthStatus.HEALTHY

        # Add warning result
        summary.add_result(HealthCheckResult(
            name="Test2",
            status=HealthStatus.WARNING,
            message="Warning"
        ))
        assert summary.overall_status == HealthStatus.WARNING

        # Add critical result
        summary.add_result(HealthCheckResult(
            name="Test3",
            status=HealthStatus.CRITICAL,
            message="Critical"
        ))
        assert summary.overall_status == HealthStatus.CRITICAL

    def test_to_dict(self):
        """Test HealthCheckSummary to_dict conversion"""
        summary = HealthCheckSummary()
        result = HealthCheckResult(
            name="Test",
            status=HealthStatus.HEALTHY,
            message="OK"
        )
        summary.add_result(result)

        summary_dict = summary.to_dict()

        assert summary_dict['overall_status'] == "healthy"
        assert summary_dict['total_checks'] == 1
        assert summary_dict['passed'] == 1
        assert len(summary_dict['results']) == 1


@pytest.mark.unit
class TestHealthCheckConfig:
    """Test HealthCheckConfig class"""

    def test_default_paths(self):
        """Test default path configuration"""
        config = HealthCheckConfig()

        assert config.WORKSPACE_ROOT == Path("/workspace")
        assert config.COMFYUI_ROOT == Path("/workspace/ComfyUI")
        assert config.MODELS_ROOT == Path("/workspace/ComfyUI/models")
        assert config.CONFIG_ROOT == Path("/config")
        assert config.VENV_PATH == Path("/workspace/venv")

    def test_model_subdirs(self):
        """Test model subdirectories configuration"""
        config = HealthCheckConfig()

        expected_subdirs = [
            "checkpoints", "text_encoders", "vae", "clip_vision",
            "loras", "upscale_models", "audio_encoders", "diffusion_models",
            "controlnet", "embeddings", "ipadapters"
        ]

        assert config.MODEL_SUBDIRS == expected_subdirs

    def test_service_endpoints(self):
        """Test service endpoints configuration"""
        config = HealthCheckConfig()

        assert config.COMFYUI_ENDPOINT == ("localhost", 3000)
        assert config.DASHBOARD_ENDPOINT == ("localhost", 8080)

    def test_disk_thresholds(self):
        """Test disk space thresholds"""
        config = HealthCheckConfig()

        expected_warning = 10 * 1024 * 1024 * 1024  # 10GB
        expected_critical = 5 * 1024 * 1024 * 1024   # 5GB

        assert config.DISK_WARNING_THRESHOLD == expected_warning
        assert config.DISK_CRITICAL_THRESHOLD == expected_critical


@pytest.mark.unit
class TestHealthChecker:
    """Test HealthChecker class"""

    def test_initialization(self):
        """Test HealthChecker initialization"""
        config = HealthCheckConfig()
        checker = HealthChecker(config=config)

        assert checker.config == config
        assert checker.verbose is False
        assert checker.json_output is False
        assert isinstance(checker.summary, HealthCheckSummary)

    def test_initialization_with_options(self):
        """Test HealthChecker initialization with options"""
        config = HealthCheckConfig()
        checker = HealthChecker(
            config=config,
            verbose=True,
            json_output=True
        )

        assert checker.verbose is True
        assert checker.json_output is True

    def test_colorize_text(self):
        """Test text colorization"""
        checker = HealthChecker()

        # When json_output is False, should colorize
        result = checker._colorize("test", Colors.RED)
        assert Colors.RED in result
        assert "test" in result

        # When json_output is True, should not colorize
        checker.json_output = True
        result = checker._colorize("test", Colors.RED)
        assert result == "test"

    def test_check_workspace_mount_exists(self, temp_dir):
        """Test workspace mount check when exists"""
        config = HealthCheckConfig()
        config.WORKSPACE_ROOT = temp_dir
        checker = HealthChecker(config=config)

        result = checker.check_workspace_mount()

        assert result.name == "Workspace Mount"
        assert result.status == HealthStatus.HEALTHY
        assert "accessible" in result.message.lower()

    def test_check_workspace_mount_not_exists(self, temp_dir):
        """Test workspace mount check when not exists"""
        config = HealthCheckConfig()
        config.WORKSPACE_ROOT = temp_dir / "nonexistent"
        checker = HealthChecker(config=config)

        result = checker.check_workspace_mount()

        assert result.name == "Workspace Mount"
        assert result.status == HealthStatus.CRITICAL
        assert "not found" in result.message.lower()

    def test_check_workspace_mount_not_writable(self, temp_dir):
        """Test workspace mount check when not writable"""
        config = HealthCheckConfig()
        config.WORKSPACE_ROOT = temp_dir
        checker = HealthChecker(config=config)

        # Mock os.access to return False for write
        with patch('os.access', return_value=False):
            result = checker.check_workspace_mount()

        assert result.name == "Workspace Mount"
        assert result.status == HealthStatus.CRITICAL
        assert "not writable" in result.message.lower()

    def test_check_model_paths_all_exist(self, temp_dir):
        """Test model paths check when all exist"""
        # Create model directory structure
        models_dir = temp_dir / "models"
        models_dir.mkdir()

        for subdir in HealthCheckConfig().MODEL_SUBDIRS:
            (models_dir / subdir).mkdir()

        config = HealthCheckConfig()
        config.MODELS_ROOT = models_dir
        checker = HealthChecker(config=config)

        result = checker.check_model_paths()

        assert result.name == "Model Paths"
        assert result.status == HealthStatus.HEALTHY
        assert "all" in result.message.lower()

    def test_check_model_paths_some_missing(self, temp_dir):
        """Test model paths check when some missing"""
        models_dir = temp_dir / "models"
        models_dir.mkdir()

        # Create only half the directories
        subdirs = HealthCheckConfig().MODEL_SUBDIRS
        for subdir in subdirs[:len(subdirs)//2]:
            (models_dir / subdir).mkdir()

        config = HealthCheckConfig()
        config.MODELS_ROOT = models_dir
        checker = HealthChecker(config=config)

        result = checker.check_model_paths()

        assert result.name == "Model Paths"
        # Should be warning if at least half exist
        assert result.status in [HealthStatus.WARNING, HealthStatus.HEALTHY]

    def test_check_model_paths_most_missing(self, temp_dir):
        """Test model paths check when most missing"""
        models_dir = temp_dir / "models"
        models_dir.mkdir()

        # Create only one directory
        (models_dir / "checkpoints").mkdir()

        config = HealthCheckConfig()
        config.MODELS_ROOT = models_dir
        checker = HealthChecker(config=config)

        result = checker.check_model_paths()

        assert result.name == "Model Paths"
        assert result.status == HealthStatus.CRITICAL

    def test_check_model_paths_not_exist(self, temp_dir):
        """Test model paths check when models dir doesn't exist"""
        config = HealthCheckConfig()
        config.MODELS_ROOT = temp_dir / "nonexistent"
        checker = HealthChecker(config=config)

        result = checker.check_model_paths()

        assert result.name == "Model Paths"
        assert result.status == HealthStatus.CRITICAL

    def test_check_disk_space_healthy(self, temp_dir):
        """Test disk space check when healthy"""
        config = HealthCheckConfig()
        config.WORKSPACE_ROOT = temp_dir
        checker = HealthChecker(config=config)

        # Mock statvfs to return lots of free space
        mock_stat = Mock()
        mock_stat.f_frsize = 4096
        mock_stat.f_bavail = 100 * 1024 * 1024  # ~400GB free

        with patch('os.statvfs', return_value=mock_stat):
            result = checker.check_disk_space()

        assert result.name == "Disk Space"
        assert result.status == HealthStatus.HEALTHY
        assert "sufficient" in result.message.lower()

    def test_check_disk_space_warning(self, temp_dir):
        """Test disk space check when warning"""
        config = HealthCheckConfig()
        config.WORKSPACE_ROOT = temp_dir
        config.DISK_WARNING_THRESHOLD = 2 * 1024 * 1024 * 1024  # 2GB
        config.DISK_CRITICAL_THRESHOLD = 1 * 1024 * 1024 * 1024   # 1GB
        checker = HealthChecker(config=config)

        # Mock statvfs to return warning level space
        mock_stat = Mock()
        mock_stat.f_frsize = 4096
        mock_stat.f_bavail = (1.5 * 1024 * 1024 * 1024) // 4096  # ~1.5GB free

        with patch('os.statvfs', return_value=mock_stat):
            result = checker.check_disk_space()

        assert result.name == "Disk Space"
        assert result.status == HealthStatus.WARNING
        assert "warning" in result.message.lower()

    def test_check_disk_space_critical(self, temp_dir):
        """Test disk space check when critical"""
        config = HealthCheckConfig()
        config.WORKSPACE_ROOT = temp_dir
        config.DISK_WARNING_THRESHOLD = 2 * 1024 * 1024 * 1024  # 2GB
        config.DISK_CRITICAL_THRESHOLD = 1 * 1024 * 1024 * 1024   # 1GB
        checker = HealthChecker(config=config)

        # Mock statvfs to return critical level space
        mock_stat = Mock()
        mock_stat.f_frsize = 4096
        mock_stat.f_bavail = (0.5 * 1024 * 1024 * 1024) // 4096  # ~500MB free

        with patch('os.statvfs', return_value=mock_stat):
            result = checker.check_disk_space()

        assert result.name == "Disk Space"
        assert result.status == HealthStatus.CRITICAL
        assert "critical" in result.message.lower()

    def test_check_service_responding(self, temp_dir):
        """Test service check when responding"""
        checker = HealthChecker()

        # Mock successful socket connection
        with patch('socket.socket') as mock_socket:
            mock_sock = MagicMock()
            mock_sock.connect_ex.return_value = 0
            mock_socket.return_value.__enter__ = Mock(return_value=mock_sock)
            mock_socket.return_value.__exit__ = Mock(return_value=False)

            result = checker.check_service("Test Service", "localhost", 3000)

        assert result.name == "Test Service"
        assert result.status == HealthStatus.HEALTHY
        assert "responding" in result.message.lower()

    def test_check_service_not_responding(self, temp_dir):
        """Test service check when not responding"""
        checker = HealthChecker()

        # Mock failed socket connection
        with patch('socket.socket') as mock_socket:
            mock_sock = MagicMock()
            mock_sock.connect_ex.return_value = 1  # Connection failed
            mock_socket.return_value.__enter__ = Mock(return_value=mock_sock)
            mock_socket.return_value.__exit__ = Mock(return_value=False)

            result = checker.check_service("Test Service", "localhost", 3000)

        assert result.name == "Test Service"
        assert result.status == HealthStatus.WARNING
        assert "not responding" in result.message.lower()

    def test_check_configuration_valid(self, temp_dir):
        """Test configuration check with valid config"""
        import yaml

        config = HealthCheckConfig()
        config.CONFIG_ROOT = temp_dir
        config.WORKSPACE_ROOT = temp_dir / "workspace"
        config.WORKSPACE_ROOT.mkdir()

        # Create valid config files
        config_file = temp_dir / "extra_model_paths.yaml"
        with open(config_file, 'w') as f:
            yaml.dump({'test': 'config'}, f)

        comfy_config = config.WORKSPACE_ROOT / "extra_model_paths.yaml"
        with open(comfy_config, 'w') as f:
            yaml.dump({'test': 'config2'}, f)

        config.CONFIG_FILES = [config_file, comfy_config]

        checker = HealthChecker(config=config)
        result = checker.check_configuration()

        assert result.name == "Configuration"
        assert result.status == HealthStatus.HEALTHY

    def test_check_configuration_missing(self, temp_dir):
        """Test configuration check with missing config"""
        config = HealthCheckConfig()
        config.CONFIG_ROOT = temp_dir
        config.WORKSPACE_ROOT = temp_dir / "workspace"
        config.WORKSPACE_ROOT.mkdir()

        config.CONFIG_FILES = [
            temp_dir / "nonexistent.yaml",
            config.WORKSPACE_ROOT / "nonexistent.yaml"
        ]

        checker = HealthChecker(config=config)
        result = checker.check_configuration()

        assert result.name == "Configuration"
        assert result.status == HealthStatus.WARNING

    def test_check_comfyui_installation_complete(self, temp_dir):
        """Test ComfyUI installation check when complete"""
        config = HealthCheckConfig()
        config.COMFYUI_ROOT = temp_dir
        checker = HealthChecker(config=config)

        # Create ComfyUI directory structure
        for file in ["main.py", "server.py", "folder_paths.py"]:
            (temp_dir / file).write_text("# test")

        (temp_dir / "custom_nodes").mkdir()

        result = checker.check_comfyui_installation()

        assert result.name == "ComfyUI Installation"
        assert result.status == HealthStatus.HEALTHY
        assert "complete" in result.message.lower()

    def test_check_comfyui_installation_incomplete(self, temp_dir):
        """Test ComfyUI installation check when incomplete"""
        config = HealthCheckConfig()
        config.COMFYUI_ROOT = temp_dir
        checker = HealthChecker(config=config)

        # Create incomplete ComfyUI (missing files)
        (temp_dir / "main.py").write_text("# test")

        result = checker.check_comfyui_installation()

        assert result.name == "ComfyUI Installation"
        assert result.status == HealthStatus.CRITICAL
        assert "incomplete" in result.message.lower()

    def test_check_venv_complete(self, temp_dir):
        """Test venv check when complete"""
        config = HealthCheckConfig()
        config.VENV_PATH = temp_dir
        checker = HealthChecker(config=config)

        # Create venv structure
        bin_dir = temp_dir / "bin"
        bin_dir.mkdir()

        (bin_dir / "python3").write_text("#!/bin/bash\n")
        (bin_dir / "pip").write_text("#!/bin/bash\n")

        result = checker.check_venv()

        assert result.name == "Virtual Environment"
        assert result.status == HealthStatus.HEALTHY
        assert "properly set up" in result.message.lower()

    def test_check_venv_incomplete(self, temp_dir):
        """Test venv check when incomplete"""
        config = HealthCheckConfig()
        config.VENV_PATH = temp_dir
        checker = HealthChecker(config=config)

        # Create incomplete venv
        bin_dir = temp_dir / "bin"
        bin_dir.mkdir()
        (bin_dir / "python3").write_text("#!/bin/bash\n")
        # Missing pip

        result = checker.check_venv()

        assert result.name == "Virtual Environment"
        assert result.status == HealthStatus.CRITICAL
        assert "incomplete" in result.message.lower()

    def test_run_all_checks(self, temp_dir):
        """Test running all checks"""
        config = HealthCheckConfig()
        config.WORKSPACE_ROOT = temp_dir
        config.COMFYUI_ROOT = temp_dir
        config.MODELS_ROOT = temp_dir
        config.VENV_PATH = temp_dir

        checker = HealthChecker(config=config)

        # Create minimal structure
        for file in ["main.py", "server.py", "folder_paths.py"]:
            (temp_dir / file).write_text("# test")
        (temp_dir / "custom_nodes").mkdir()
        (temp_dir / "bin").mkdir()
        (temp_dir / "bin" / "python3").write_text("#!/bin/bash\n")
        (temp_dir / "bin" / "pip").write_text("#!/bin/bash\n")

        summary = checker.run_checks(include_services=False)

        assert summary.total_checks > 0
        assert summary.overall_status in [
            HealthStatus.HEALTHY,
            HealthStatus.WARNING,
            HealthStatus.CRITICAL
        ]

    def test_run_specific_checks(self, temp_dir):
        """Test running specific checks"""
        config = HealthCheckConfig()
        config.WORKSPACE_ROOT = temp_dir
        checker = HealthChecker(config=config)

        summary = checker.run_checks(checks=["workspace"], include_services=False)

        assert summary.total_checks == 1
        assert len(summary.results) == 1
        assert summary.results[0].name == "Workspace Mount"

    def test_run_checks_with_services(self, temp_dir):
        """Test running checks including services"""
        config = HealthCheckConfig()
        config.WORKSPACE_ROOT = temp_dir
        checker = HealthChecker(config=config)

        # Mock service checks
        with patch.object(checker, 'check_service') as mock_service:
            mock_service.return_value = HealthCheckResult(
                name="Service",
                status=HealthStatus.WARNING,
                message="Not responding"
            )

            summary = checker.run_checks(include_services=True)

        # Should include service checks
        assert any("Service" in r.name for r in summary.results)

    def test_get_time_ms(self):
        """Test time measurement helper"""
        time_ms = HealthChecker._get_time_ms()

        assert isinstance(time_ms, float)
        assert time_ms > 0


@pytest.mark.unit
class TestHealthCheckColors:
    """Test ANSI color codes"""

    def test_color_codes(self):
        """Test color code values"""
        assert Colors.RESET == "\033[0m"
        assert Colors.RED == "\033[91m"
        assert Colors.YELLOW == "\033[93m"
        assert Colors.GREEN == "\033[92m"
        assert Colors.BLUE == "\033[94m"
        assert Colors.BOLD == "\033[1m"
        assert Colors.DIM == "\033[2m"


@pytest.mark.unit
class TestHealthCheckEdgeCases:
    """Test edge cases and error handling"""

    def test_check_workspace_exception(self, temp_dir):
        """Test workspace check handles exceptions"""
        config = HealthCheckConfig()
        config.WORKSPACE_ROOT = temp_dir
        checker = HealthChecker(config=config)

        # Mock to raise exception
        with patch('os.statvfs', side_effect=Exception("Test error")):
            result = checker.check_workspace_mount()

        assert result.status == HealthStatus.CRITICAL
        assert "failed" in result.message.lower()

    def test_check_model_paths_exception(self, temp_dir):
        """Test model paths check handles exceptions"""
        config = HealthCheckConfig()
        config.MODELS_ROOT = temp_dir
        checker = HealthChecker(config=config)

        # Mock to raise exception
        with patch('pathlib.Path.exists', side_effect=Exception("Test error")):
            result = checker.check_model_paths()

        assert result.status == HealthStatus.CRITICAL
        assert "failed" in result.message.lower()

    def test_check_disk_space_exception(self, temp_dir):
        """Test disk space check handles exceptions"""
        config = HealthCheckConfig()
        config.WORKSPACE_ROOT = temp_dir
        checker = HealthChecker(config=config)

        # Mock to raise exception
        with patch('os.statvfs', side_effect=Exception("Test error")):
            result = checker.check_disk_space()

        assert result.status == HealthStatus.CRITICAL
        assert "failed" in result.message.lower()

    def test_check_service_timeout(self, temp_dir):
        """Test service check handles timeout"""
        checker = HealthChecker()

        # Mock socket timeout
        with patch('socket.socket') as mock_socket:
            import socket as socket_module
            mock_sock = MagicMock()
            mock_sock.connect_ex.side_effect = socket_module.timeout()
            mock_socket.return_value.__enter__ = Mock(return_value=mock_sock)
            mock_socket.return_value.__exit__ = Mock(return_value=False)

            result = checker.check_service("Test", "localhost", 3000)

        assert result.status == HealthStatus.WARNING
        assert "timeout" in result.message.lower()

    def test_check_service_exception(self, temp_dir):
        """Test service check handles exceptions"""
        checker = HealthChecker()

        # Mock socket exception
        with patch('socket.socket', side_effect=Exception("Socket error")):
            result = checker.check_service("Test", "localhost", 3000)

        assert result.status == HealthStatus.WARNING
        assert "failed" in result.message.lower()

    def test_run_checks_unknown_check(self, temp_dir):
        """Test running unknown check name"""
        config = HealthCheckConfig()
        config.WORKSPACE_ROOT = temp_dir
        checker = HealthChecker(config=config)

        # Should not raise exception, just warn
        summary = checker.run_checks(checks=["unknown_check"], include_services=False)

        # Unknown checks should be ignored
        assert summary.total_checks == 0

    def test_configuration_check_yaml_import_error(self, temp_dir):
        """Test configuration check handles yaml import error"""
        config = HealthCheckConfig()
        config.CONFIG_ROOT = temp_dir
        config.WORKSPACE_ROOT = temp_dir / "workspace"
        config.WORKSPACE_ROOT.mkdir()

        # Create config files
        config_file = temp_dir / "extra_model_paths.yaml"
        config_file.write_text("test: config")

        config.CONFIG_FILES = [config_file]

        checker = HealthChecker(config=config)

        # Mock yaml import to fail
        with patch.dict('sys.modules', {'yaml': None}):
            result = checker.check_configuration()

        # Should still pass based on file readability
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.WARNING]
