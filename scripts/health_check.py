#!/usr/bin/env python3
"""
ComfyUI Docker Health Check System

A comprehensive health check system for the ComfyUI Docker container.
Checks workspace mount, model paths, disk space, services, and configuration.

Exit codes:
    0: All checks passed (healthy)
    1: Some warnings (non-critical issues)
    2: Critical failures (system not ready)
"""

import argparse
import json
import os
import shutil
import socket
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class HealthStatus(Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"


class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


@dataclass
class HealthCheckResult:
    """Result of a single health check."""
    name: str
    status: HealthStatus
    message: str
    details: Optional[Dict] = None
    duration_ms: float = 0.0

    def to_dict(self) -> Dict:
        """Convert result to dictionary for JSON output."""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details or {},
            "duration_ms": self.duration_ms,
        }


@dataclass
class HealthCheckSummary:
    """Summary of all health check results."""
    results: List[HealthCheckResult] = field(default_factory=list)
    overall_status: HealthStatus = HealthStatus.HEALTHY
    total_checks: int = 0
    passed: int = 0
    warnings: int = 0
    critical: int = 0

    def add_result(self, result: HealthCheckResult) -> None:
        """Add a result and update summary statistics."""
        self.results.append(result)
        self.total_checks += 1

        if result.status == HealthStatus.HEALTHY:
            self.passed += 1
        elif result.status == HealthStatus.WARNING:
            self.warnings += 1
            if self.overall_status == HealthStatus.HEALTHY:
                self.overall_status = HealthStatus.WARNING
        elif result.status == HealthStatus.CRITICAL:
            self.critical += 1
            self.overall_status = HealthStatus.CRITICAL

    def to_dict(self) -> Dict:
        """Convert summary to dictionary for JSON output."""
        return {
            "overall_status": self.overall_status.value,
            "total_checks": self.total_checks,
            "passed": self.passed,
            "warnings": self.warnings,
            "critical": self.critical,
            "results": [r.to_dict() for r in self.results],
        }


class HealthCheckConfig:
    """Configuration for health check thresholds and paths."""

    # Default paths
    WORKSPACE_ROOT = Path("/workspace")
    COMFYUI_ROOT = WORKSPACE_ROOT / "ComfyUI"
    MODELS_ROOT = COMFYUI_ROOT / "models"
    CONFIG_ROOT = Path("/config")
    VENV_PATH = WORKSPACE_ROOT / "venv"

    # Model subdirectories that should exist
    MODEL_SUBDIRS = [
        "checkpoints",
        "text_encoders",
        "vae",
        "clip_vision",
        "loras",
        "upscale_models",
        "audio_encoders",
        "diffusion_models",
        "controlnet",
        "embeddings",
        "ipadapters",
    ]

    # Service endpoints
    COMFYUI_ENDPOINT = ("localhost", 3000)
    DASHBOARD_ENDPOINT = ("localhost", 8080)

    # Disk space thresholds (bytes)
    DISK_WARNING_THRESHOLD = 10 * 1024 * 1024 * 1024  # 10GB
    DISK_CRITICAL_THRESHOLD = 5 * 1024 * 1024 * 1024   # 5GB

    # Config files to validate
    CONFIG_FILES = [
        CONFIG_ROOT / "extra_model_paths.yaml",
        WORKSPACE_ROOT / "ComfyUI" / "extra_model_paths.yaml",
    ]


class HealthChecker:
    """Main health check system."""

    def __init__(
        self,
        config: Optional[HealthCheckConfig] = None,
        verbose: bool = False,
        json_output: bool = False,
    ):
        self.config = config or HealthCheckConfig()
        self.verbose = verbose
        self.json_output = json_output
        self.summary = HealthCheckSummary()

    def _colorize(self, text: str, color: str) -> str:
        """Add color to text if not outputting JSON."""
        if self.json_output:
            return text
        return f"{color}{text}{Colors.RESET}"

    def _print_result(self, result: HealthCheckResult) -> None:
        """Print a single check result."""
        if self.json_output:
            return

        status_symbol = {
            HealthStatus.HEALTHY: self._colorize("✓", Colors.GREEN),
            HealthStatus.WARNING: self._colorize("⚠", Colors.YELLOW),
            HealthStatus.CRITICAL: self._colorize("✗", Colors.RED),
        }[result.status]

        print(f"  {status_symbol} {result.name}: {result.message}")

        if self.verbose and result.details:
            for key, value in result.details.items():
                print(f"      {key}: {value}")

    def check_workspace_mount(self) -> HealthCheckResult:
        """Check if workspace is mounted and accessible."""
        name = "Workspace Mount"
        start_time = self._get_time_ms()

        try:
            if not self.config.WORKSPACE_ROOT.exists():
                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.CRITICAL,
                    message=f"Workspace root not found: {self.config.WORKSPACE_ROOT}",
                    duration_ms=self._get_time_ms() - start_time,
                )

            if not os.access(self.config.WORKSPACE_ROOT, os.W_OK):
                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.CRITICAL,
                    message=f"Workspace not writable: {self.config.WORKSPACE_ROOT}",
                    duration_ms=self._get_time_ms() - start_time,
                )

            # Get filesystem info
            stat = os.statvfs(self.config.WORKSPACE_ROOT)
            total_space = stat.f_frsize * stat.f_blocks
            free_space = stat.f_frsize * stat.f_bavail

            details = {
                "path": str(self.config.WORKSPACE_ROOT),
                "total_space_gb": f"{total_space / (1024**3):.2f}",
                "free_space_gb": f"{free_space / (1024**3):.2f}",
            }

            return HealthCheckResult(
                name=name,
                status=HealthStatus.HEALTHY,
                message=f"Workspace accessible at {self.config.WORKSPACE_ROOT}",
                details=details,
                duration_ms=self._get_time_ms() - start_time,
            )

        except Exception as e:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.CRITICAL,
                message=f"Failed to access workspace: {e}",
                duration_ms=self._get_time_ms() - start_time,
            )

    def check_model_paths(self) -> HealthCheckResult:
        """Check if all required model subdirectories exist."""
        name = "Model Paths"
        start_time = self._get_time_ms()

        try:
            models_dir = self.config.MODELS_ROOT

            if not models_dir.exists():
                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.CRITICAL,
                    message=f"Models directory not found: {models_dir}",
                    duration_ms=self._get_time_ms() - start_time,
                )

            missing_dirs = []
            existing_dirs = []

            for subdir in self.config.MODEL_SUBDIRS:
                dir_path = models_dir / subdir
                if dir_path.exists():
                    existing_dirs.append(subdir)
                else:
                    missing_dirs.append(subdir)

            details = {
                "models_path": str(models_dir),
                "existing_dirs": existing_dirs,
                "missing_dirs": missing_dirs,
                "total_expected": len(self.config.MODEL_SUBDIRS),
                "total_existing": len(existing_dirs),
            }

            if len(missing_dirs) == 0:
                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.HEALTHY,
                    message=f"All {len(existing_dirs)} model directories present",
                    details=details,
                    duration_ms=self._get_time_ms() - start_time,
                )
            elif len(existing_dirs) >= len(self.config.MODEL_SUBDIRS) // 2:
                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.WARNING,
                    message=f"{len(missing_dirs)} model directories missing (have {len(existing_dirs)}/{len(self.config.MODEL_SUBDIRS)})",
                    details=details,
                    duration_ms=self._get_time_ms() - start_time,
                )
            else:
                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.CRITICAL,
                    message=f"Critical: {len(missing_dirs)} model directories missing",
                    details=details,
                    duration_ms=self._get_time_ms() - start_time,
                )

        except Exception as e:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.CRITICAL,
                message=f"Failed to check model paths: {e}",
                duration_ms=self._get_time_ms() - start_time,
            )

    def check_disk_space(self) -> HealthCheckResult:
        """Check if sufficient disk space is available."""
        name = "Disk Space"
        start_time = self._get_time_ms()

        try:
            stat = os.statvfs(self.config.WORKSPACE_ROOT)
            free_space = stat.f_frsize * stat.f_bavail

            free_gb = free_space / (1024**3)

            details = {
                "free_space_gb": f"{free_gb:.2f}",
                "free_space_bytes": free_space,
                "warning_threshold_gb": (
                    self.config.DISK_WARNING_THRESHOLD / (1024**3)
                ),
                "critical_threshold_gb": (
                    self.config.DISK_CRITICAL_THRESHOLD / (1024**3)
                ),
            }

            if free_space < self.config.DISK_CRITICAL_THRESHOLD:
                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.CRITICAL,
                    message=f"Critical: Only {free_gb:.2f}GB free (threshold: {self.config.DISK_CRITICAL_THRESHOLD / (1024**3):.0f}GB)",
                    details=details,
                    duration_ms=self._get_time_ms() - start_time,
                )
            elif free_space < self.config.DISK_WARNING_THRESHOLD:
                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.WARNING,
                    message=f"Warning: Only {free_gb:.2f}GB free (threshold: {self.config.DISK_WARNING_THRESHOLD / (1024**3):.0f}GB)",
                    details=details,
                    duration_ms=self._get_time_ms() - start_time,
                )
            else:
                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.HEALTHY,
                    message=f"Sufficient disk space: {free_gb:.2f}GB free",
                    details=details,
                    duration_ms=self._get_time_ms() - start_time,
                )

        except Exception as e:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.CRITICAL,
                message=f"Failed to check disk space: {e}",
                duration_ms=self._get_time_ms() - start_time,
            )

    def check_service(self, name: str, host: str, port: int) -> HealthCheckResult:
        """Check if a service is responding on the given port."""
        start_time = self._get_time_ms()

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.HEALTHY,
                    message=f"Service responding on {host}:{port}",
                    details={"host": host, "port": port},
                    duration_ms=self._get_time_ms() - start_time,
                )
            else:
                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.WARNING,
                    message=f"Service not responding on {host}:{port}",
                    details={"host": host, "port": port},
                    duration_ms=self._get_time_ms() - start_time,
                )

        except socket.timeout:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.WARNING,
                message=f"Service timeout on {host}:{port}",
                details={"host": host, "port": port},
                duration_ms=self._get_time_ms() - start_time,
            )
        except Exception as e:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.WARNING,
                message=f"Failed to check service: {e}",
                details={"host": host, "port": port},
                duration_ms=self._get_time_ms() - start_time,
            )

    def check_configuration(self) -> HealthCheckResult:
        """Check if configuration files are valid."""
        name = "Configuration"
        start_time = self._get_time_ms()

        try:
            config_files_found = []
            config_files_missing = []
            config_files_valid = []
            config_files_invalid = []

            for config_path in self.config.CONFIG_FILES:
                if config_path.exists():
                    config_files_found.append(str(config_path))

                    # Try to parse YAML
                    try:
                        import yaml

                        with open(config_path, "r") as f:
                            yaml.safe_load(f)
                        config_files_valid.append(str(config_path))
                    except ImportError:
                        # If yaml not available, just check file exists and is readable
                        if os.access(config_path, os.R_OK):
                            config_files_valid.append(str(config_path))
                        else:
                            config_files_invalid.append(f"{config_path} (not readable)")
                    except Exception as e:
                        config_files_invalid.append(f"{config_path} ({e})")
                else:
                    config_files_missing.append(str(config_path))

            details = {
                "config_files_found": config_files_found,
                "config_files_missing": config_files_missing,
                "config_files_valid": config_files_valid,
                "config_files_invalid": config_files_invalid,
            }

            if len(config_files_invalid) > 0:
                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.CRITICAL,
                    message=f"Configuration errors: {len(config_files_invalid)} invalid files",
                    details=details,
                    duration_ms=self._get_time_ms() - start_time,
                )
            elif len(config_files_found) == 0:
                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.WARNING,
                    message="No configuration files found",
                    details=details,
                    duration_ms=self._get_time_ms() - start_time,
                )
            else:
                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.HEALTHY,
                    message=f"{len(config_files_valid)} configuration files valid",
                    details=details,
                    duration_ms=self._get_time_ms() - start_time,
                )

        except Exception as e:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.WARNING,
                message=f"Failed to validate configuration: {e}",
                duration_ms=self._get_time_ms() - start_time,
            )

    def check_comfyui_installation(self) -> HealthCheckResult:
        """Check if ComfyUI is properly installed."""
        name = "ComfyUI Installation"
        start_time = self._get_time_ms()

        try:
            comfy_dir = self.config.COMFYUI_ROOT

            if not comfy_dir.exists():
                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.CRITICAL,
                    message=f"ComfyUI directory not found: {comfy_dir}",
                    duration_ms=self._get_time_ms() - start_time,
                )

            # Check for key ComfyUI files
            key_files = [
                "main.py",
                "server.py",
                "folder_paths.py",
            ]

            missing_files = []
            for file in key_files:
                if not (comfy_dir / file).exists():
                    missing_files.append(file)

            # Check for custom_nodes directory
            custom_nodes_dir = comfy_dir / "custom_nodes"
            if not custom_nodes_dir.exists():
                missing_files.append("custom_nodes/")

            details = {
                "comfyui_path": str(comfy_dir),
                "key_files_checked": key_files,
                "missing_files": missing_files,
            }

            if len(missing_files) > 0:
                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.CRITICAL,
                    message=f"ComfyUI incomplete: {len(missing_files)} files missing",
                    details=details,
                    duration_ms=self._get_time_ms() - start_time,
                )

            return HealthCheckResult(
                name=name,
                status=HealthStatus.HEALTHY,
                message="ComfyUI installation complete",
                details=details,
                duration_ms=self._get_time_ms() - start_time,
            )

        except Exception as e:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.CRITICAL,
                message=f"Failed to check ComfyUI: {e}",
                duration_ms=self._get_time_ms() - start_time,
            )

    def check_venv(self) -> HealthCheckResult:
        """Check if virtual environment is properly set up."""
        name = "Virtual Environment"
        start_time = self._get_time_ms()

        try:
            venv_path = self.config.VENV_PATH

            if not venv_path.exists():
                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.CRITICAL,
                    message=f"Virtual environment not found: {venv_path}",
                    duration_ms=self._get_time_ms() - start_time,
                )

            # Check for key venv components
            python_bin = venv_path / "bin" / "python3"
            pip_bin = venv_path / "bin" / "pip"

            missing_components = []
            if not python_bin.exists():
                missing_components.append("python3")
            if not pip_bin.exists():
                missing_components.append("pip")

            details = {
                "venv_path": str(venv_path),
                "python_path": str(python_bin),
                "pip_path": str(pip_bin),
            }

            if len(missing_components) > 0:
                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.CRITICAL,
                    message=f"Virtual environment incomplete: {', '.join(missing_components)} missing",
                    details=details,
                    duration_ms=self._get_time_ms() - start_time,
                )

            return HealthCheckResult(
                name=name,
                status=HealthStatus.HEALTHY,
                message="Virtual environment properly set up",
                details=details,
                duration_ms=self._get_time_ms() - start_time,
            )

        except Exception as e:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.WARNING,
                message=f"Failed to check venv: {e}",
                duration_ms=self._get_time_ms() - start_time,
            )

    def run_checks(
        self,
        checks: Optional[List[str]] = None,
        include_services: bool = True,
    ) -> HealthCheckSummary:
        """Run health checks.

        Args:
            checks: List of specific checks to run. If None, runs all checks.
            include_services: Whether to include service connectivity checks.

        Returns:
            HealthCheckSummary with all results.
        """
        # Define all available checks
        all_checks = {
            "workspace": self.check_workspace_mount,
            "models": self.check_model_paths,
            "disk": self.check_disk_space,
            "config": self.check_configuration,
            "comfyui": self.check_comfyui_installation,
            "venv": self.check_venv,
        }

        # Add service checks if requested
        if include_services:
            all_checks.update({
                "comfyui_service": lambda: self.check_service(
                    "ComfyUI Service",
                    *self.config.COMFYUI_ENDPOINT
                ),
                "dashboard_service": lambda: self.check_service(
                    "Dashboard Service",
                    *self.config.DASHBOARD_ENDPOINT
                ),
            })

        # Filter checks if specific ones requested
        if checks:
            for check_name in checks:
                if check_name not in all_checks:
                    print(
                        f"Warning: Unknown check '{check_name}'. Available: {', '.join(all_checks.keys())}",
                        file=sys.stderr,
                    )
            checks_to_run = {
                name: func for name, func in all_checks.items() if name in checks
            }
        else:
            checks_to_run = all_checks

        # Run checks
        for check_name, check_func in checks_to_run.items():
            result = check_func()
            self.summary.add_result(result)

        return self.summary

    @staticmethod
    def _get_time_ms() -> float:
        """Get current time in milliseconds."""
        import time
        return time.time() * 1000


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="ComfyUI Docker Health Check System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit codes:
    0: All checks passed (healthy)
    1: Some warnings (non-critical issues)
    2: Critical failures (system not ready)

Available checks:
    workspace     - Check workspace mount and accessibility
    models        - Check model directory structure
    disk          - Check available disk space
    config        - Check configuration files
    comfyui       - Check ComfyUI installation
    venv          - Check virtual environment
    comfyui_service   - Check ComfyUI service (port 3000)
    dashboard_service - Check dashboard service (port 8080)

Examples:
    # Run all checks
    python health_check.py

    # Run specific checks
    python health_check.py --check workspace disk

    # JSON output for monitoring
    python health_check.py --json

    # Verbose output
    python health_check.py --verbose

    # Custom disk space thresholds
    python health_check.py --disk-warning 20 --disk-critical 10
        """,
    )

    parser.add_argument(
        "--check",
        "-c",
        action="append",
        dest="checks",
        help="Specific check(s) to run. Can be specified multiple times.",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable detailed output",
    )

    parser.add_argument(
        "--no-services",
        action="store_true",
        help="Skip service connectivity checks",
    )

    parser.add_argument(
        "--disk-warning",
        type=int,
        default=10,
        help="Disk space warning threshold in GB (default: 10)",
    )

    parser.add_argument(
        "--disk-critical",
        type=int,
        default=5,
        help="Disk space critical threshold in GB (default: 5)",
    )

    parser.add_argument(
        "--workspace",
        type=str,
        default="/workspace",
        help="Workspace root path (default: /workspace)",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_arguments()

    # Create custom config with user overrides
    config = HealthCheckConfig()
    config.WORKSPACE_ROOT = Path(args.workspace)
    config.COMFYUI_ROOT = config.WORKSPACE_ROOT / "ComfyUI"
    config.MODELS_ROOT = config.COMFYUI_ROOT / "models"
    config.VENV_PATH = config.WORKSPACE_ROOT / "venv"
    config.DISK_WARNING_THRESHOLD = args.disk_warning * 1024 * 1024 * 1024
    config.DISK_CRITICAL_THRESHOLD = args.disk_critical * 1024 * 1024 * 1024

    # Create checker and run checks
    checker = HealthChecker(
        config=config,
        verbose=args.verbose,
        json_output=args.json,
    )

    summary = checker.run_checks(
        checks=args.checks,
        include_services=not args.no_services,
    )

    # Output results
    if args.json:
        print(json.dumps(summary.to_dict(), indent=2))
    else:
        # Print header
        status_color = {
            HealthStatus.HEALTHY: Colors.GREEN,
            HealthStatus.WARNING: Colors.YELLOW,
            HealthStatus.CRITICAL: Colors.RED,
        }[summary.overall_status]

        status_text = summary.overall_status.value.upper()
        print(
            f"\n{Colors.BOLD}Health Check Results: {checker._colorize(status_text, status_color)}{Colors.RESET}"
        )
        print(f"Total: {summary.total_checks} | Passed: {summary.passed} | Warnings: {summary.warnings} | Critical: {summary.critical}\n")

        # Print individual results
        for result in summary.results:
            checker._print_result(result)

        # Print footer
        print()

    # Return appropriate exit code
    if summary.overall_status == HealthStatus.CRITICAL:
        return 2
    elif summary.overall_status == HealthStatus.WARNING:
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
