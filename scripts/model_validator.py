#!/usr/bin/env python3
"""
Model Validator for ComfyUI Preset System
Validates downloaded models against preset specifications

This module provides comprehensive validation of downloaded preset models,
including file existence, size validation, integrity checks, and usability verification.
"""

import os
import sys
import json
import hashlib
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone

# Add script directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from preset_manager.core import ModelManager
    from preset_manager.config import MODEL_PATHS
except ImportError:
    print("[ERROR] Failed to import preset manager modules", file=sys.stderr)
    sys.exit(1)


class ModelValidator:
    """
    Validates downloaded models against preset specifications

    Checks:
    - File existence
    - File size validation (±2% tolerance)
    - File integrity (SHA256 where available)
    - Directory structure
    - File permissions and usability
    """

    def __init__(self, models_dir: str = "/workspace/ComfyUI/models"):
        """
        Initialize the model validator

        Args:
            models_dir: Base directory for model files
        """
        self.models_dir = Path(models_dir)

        # Initialize model manager in read-only mode
        try:
            self.model_manager = ModelManager()
        except (PermissionError, OSError) as e:
            print(f"[WARNING] Could not initialize ModelManager with full access: {e}")
            print("[INFO] Initializing in read-only mode...")
            self.model_manager = self._init_read_only_model_manager()

        # Validation results storage
        self.validation_results = {
            'validated_at': datetime.now(timezone.utc).isoformat(),
            'models_dir': str(self.models_dir),
            'total_presets_checked': 0,
            'total_files_checked': 0,
            'valid_presets': 0,
            'invalid_presets': 0,
            'partial_presets': 0,
            'preset_details': {}
        }

        # Size tolerance percentage (default 2%)
        self.size_tolerance = 0.02

        # Supported model file extensions
        self.model_extensions = {
            '.safetensors', '.pth', '.pt', '.bin', '.ckpt', '.gguf',
            '.onnx', '.pb', '.h5', '.pkl', '.marshal'
        }

    def _init_read_only_model_manager(self):
        """
        Initialize a minimal model manager for read-only validation

        Returns:
            Minimal object with get_preset and presets attributes
        """
        class ReadOnlyModelManager:
            def __init__(self):
                self.presets = {}
                self._load_presets_read_only()

            def _load_presets_read_only(self):
                """Load presets without requiring write access"""
                try:
                    import yaml
                    presets_path = Path("/workspace/config/presets.yaml")
                    if not presets_path.exists():
                        presets_path = Path("config/presets.yaml")

                    if presets_path.exists():
                        with open(presets_path, 'r', encoding='utf-8') as f:
                            config = yaml.safe_load(f)

                        for preset_id, preset_data in config.get('presets', {}).items():
                            files = []
                            for file_info in preset_data.get('files', []):
                                if isinstance(file_info, dict) and 'path' in file_info:
                                    files.append(file_info['path'])
                                elif isinstance(file_info, str):
                                    files.append(file_info)

                            self.presets[preset_id] = {
                                'name': preset_data.get('name', preset_id),
                                'category': preset_data.get('category', 'Unknown'),
                                'type': preset_data.get('type', 'unknown'),
                                'description': preset_data.get('description', ''),
                                'download_size': preset_data.get('download_size', 'Unknown'),
                                'files': files,
                                'use_case': preset_data.get('use_case', ''),
                                'tags': preset_data.get('tags', [])
                            }

                        print(f"[INFO] Loaded {len(self.presets)} presets in read-only mode")
                    else:
                        print("[ERROR] Could not find presets.yaml configuration")

                except Exception as e:
                    print(f"[ERROR] Failed to load presets: {e}")

            def get_preset(self, preset_id: str) -> Optional[Dict]:
                """Get preset by ID"""
                return self.presets.get(preset_id)

        return ReadOnlyModelManager()

    def _parse_size_string(self, size_str: str) -> Optional[int]:
        """
        Parse size string like "4.8GB", "300MB" to bytes

        Args:
            size_str: Size string with unit (GB, MB, KB, B)

        Returns:
            Size in bytes or None if parsing fails
        """
        if not isinstance(size_str, str):
            return None

        size_str = size_str.strip().upper()

        # Extract number and unit
        for unit, multiplier in [('GB', 1024**3), ('MB', 1024**2), ('KB', 1024), ('B', 1)]:
            if unit in size_str:
                try:
                    # Remove the unit and any parentheses
                    number_str = size_str.replace(unit, '').strip()
                    # Handle cases like "4.8GB (9536MB)"
                    number_str = number_str.split('(')[0].strip()
                    return int(float(number_str) * multiplier)
                except (ValueError, IndexError):
                    continue

        return None

    def _calculate_sha256(self, file_path: Path) -> Optional[str]:
        """
        Calculate SHA256 checksum of a file

        Args:
            file_path: Path to the file

        Returns:
            SHA256 hex digest or None if calculation fails
        """
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                # Read in chunks to handle large files
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            print(f"[ERROR] Failed to calculate SHA256 for {file_path}: {e}")
            return None

    def _validate_file_size(self, file_path: Path, expected_size_str: str) -> Tuple[bool, int, int]:
        """
        Validate file size against expected size

        Args:
            file_path: Path to the file
            expected_size_str: Expected size string (e.g., "4.8GB")

        Returns:
            Tuple of (is_valid, actual_size, expected_size_bytes)
        """
        try:
            actual_size = file_path.stat().st_size
            expected_size = self._parse_size_string(expected_size_str)

            if expected_size is None:
                # Can't validate size if we can't parse expected
                return True, actual_size, 0

            # Check if size is within tolerance
            lower_bound = expected_size * (1 - self.size_tolerance)
            upper_bound = expected_size * (1 + self.size_tolerance)

            is_valid = lower_bound <= actual_size <= upper_bound
            return is_valid, actual_size, expected_size

        except Exception as e:
            print(f"[ERROR] Failed to validate size for {file_path}: {e}")
            return False, 0, 0

    def _validate_file_usability(self, file_path: Path) -> Tuple[bool, str]:
        """
        Check if file is usable (readable, not corrupted)

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (is_usable, error_message)
        """
        try:
            # Check if file is readable
            if not os.access(file_path, os.R_OK):
                return False, "File not readable (permission denied)"

            # Check if file is empty
            if file_path.stat().st_size == 0:
                return False, "File is empty"

            # Try to read first few bytes to check for corruption
            with open(file_path, 'rb') as f:
                header = f.read(1024)
                if not header:
                    return False, "File appears corrupted (cannot read header)"

            # Basic file extension validation
            if file_path.suffix.lower() not in self.model_extensions:
                return False, f"Unrecognized file extension: {file_path.suffix}"

            return True, ""

        except Exception as e:
            return False, f"Usability check failed: {str(e)}"

    def _fix_permission_issue(self, file_path: Path) -> bool:
        """
        Attempt to fix file permission issues

        Args:
            file_path: Path to the file

        Returns:
            True if fix was successful
        """
        try:
            # Try to make file readable
            os.chmod(file_path, 0o644)
            return True
        except Exception:
            return False

    def validate_preset(self, preset_id: str) -> Dict[str, Any]:
        """
        Validate all files for a specific preset

        Args:
            preset_id: Preset identifier

        Returns:
            Validation report dictionary
        """
        preset = self.model_manager.get_preset(preset_id)
        if not preset:
            return {
                'preset_id': preset_id,
                'valid': False,
                'error': f'Preset not found: {preset_id}',
                'validated_at': datetime.now(timezone.utc).isoformat()
            }

        report = {
            'preset_id': preset_id,
            'preset_name': preset.get('name', preset_id),
            'category': preset.get('category', 'Unknown'),
            'valid': True,
            'files': [],
            'missing': [],
            'corrupted': [],
            'size_mismatch': [],
            'validated_at': datetime.now(timezone.utc).isoformat()
        }

        # Get file definitions from presets.yaml for detailed info
        preset_files = self._get_preset_file_details(preset_id)

        for file_info in preset_files:
            file_path = self.models_dir / file_info['path']
            expected_size = file_info.get('size', 'Unknown')
            expected_sha256 = file_info.get('sha256')

            file_report = {
                'path': file_info['path'],
                'expected_size': expected_size,
                'valid': True,
                'issues': []
            }

            # Check file existence
            if not file_path.exists():
                file_report['valid'] = False
                file_report['issues'].append('File not found')
                report['missing'].append(file_info['path'])
                report['valid'] = False
                report['files'].append(file_report)
                continue

            # Get actual file size
            try:
                actual_size = file_path.stat().st_size
                file_report['actual_size'] = actual_size
                file_report['actual_size_mb'] = round(actual_size / (1024 * 1024), 2)
                file_report['actual_size_gb'] = round(actual_size / (1024 * 1024 * 1024), 2)
            except Exception as e:
                file_report['valid'] = False
                file_report['issues'].append(f'Cannot get file size: {e}')
                report['valid'] = False
                report['files'].append(file_report)
                continue

            # Validate file size
            if expected_size != 'Unknown':
                size_valid, actual, expected = self._validate_file_size(file_path, expected_size)
                if not size_valid:
                    file_report['valid'] = False
                    file_report['issues'].append(
                        f'Size mismatch: expected ~{expected_size}, '
                        f'got {file_report["actual_size_gb"]}GB'
                    )
                    report['size_mismatch'].append(file_info['path'])
                    report['valid'] = False

            # Validate SHA256 if available
            if expected_sha256:
                actual_sha256 = self._calculate_sha256(file_path)
                if actual_sha256 != expected_sha256:
                    file_report['valid'] = False
                    file_report['issues'].append(f'SHA256 mismatch: {actual_sha256} != {expected_sha256}')
                    report['corrupted'].append(file_info['path'])
                    report['valid'] = False
                else:
                    file_report['sha256_verified'] = True

            # Check file usability
            usable, usability_error = self._validate_file_usability(file_path)
            if not usable:
                file_report['valid'] = False
                file_report['issues'].append(usability_error)

                # Try to fix permission issues
                if 'permission' in usability_error.lower():
                    if self._fix_permission_issue(file_path):
                        # Re-check usability after fix
                        usable, _ = self._validate_file_usability(file_path)
                        if usable:
                            file_report['issues'].remove(usability_error)
                            file_report['issues'].append('Permission fixed')
                            # Don't mark file as invalid if permission was fixed
                            if len(file_report['issues']) == 1:
                                file_report['valid'] = True

                if not usable:
                    report['corrupted'].append(file_info['path'])
                    report['valid'] = False

            report['files'].append(file_report)

        return report

    def _get_preset_file_details(self, preset_id: str) -> List[Dict]:
        """
        Get detailed file information for a preset from presets.yaml

        Args:
            preset_id: Preset identifier

        Returns:
            List of file information dictionaries
        """
        try:
            # Load presets.yaml to get detailed file info
            presets_path = Path("/workspace/config/presets.yaml")
            if not presets_path.exists():
                # Fall back to basic info from ModelManager
                preset = self.model_manager.get_preset(preset_id)
                return [{'path': f, 'size': 'Unknown'} for f in preset.get('files', [])]

            import yaml
            with open(presets_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            preset_data = config.get('presets', {}).get(preset_id, {})
            files_data = preset_data.get('files', [])

            # Ensure we have proper file dictionaries
            detailed_files = []
            for file_info in files_data:
                if isinstance(file_info, dict):
                    detailed_files.append(file_info)
                elif isinstance(file_info, str):
                    detailed_files.append({'path': file_info, 'size': 'Unknown'})

            return detailed_files

        except Exception as e:
            print(f"[WARNING] Could not load detailed file info: {e}")
            # Fall back to basic info
            preset = self.model_manager.get_preset(preset_id)
            return [{'path': f, 'size': 'Unknown'} for f in preset.get('files', [])]

    def validate_all_presets(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate all presets or presets in a specific category

        Args:
            category: Optional category filter

        Returns:
            Overall validation report
        """
        presets_to_validate = {}

        if category:
            # Filter by category
            for preset_id, preset_data in self.model_manager.presets.items():
                if preset_data.get('category') == category:
                    presets_to_validate[preset_id] = preset_data
        else:
            presets_to_validate = self.model_manager.presets

        self.validation_results['total_presets_checked'] = len(presets_to_validate)

        for preset_id in presets_to_validate.keys():
            report = self.validate_preset(preset_id)
            self.validation_results['preset_details'][preset_id] = report
            self.validation_results['total_files_checked'] += len(report['files'])

            if report['valid']:
                self.validation_results['valid_presets'] += 1
            elif report['missing'] or report['corrupted']:
                self.validation_results['invalid_presets'] += 1
            else:
                self.validation_results['partial_presets'] += 1

        return self.validation_results

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of validation results

        Returns:
            Summary dictionary
        """
        return {
            'validated_at': self.validation_results['validated_at'],
            'total_presets': self.validation_results['total_presets_checked'],
            'total_files': self.validation_results['total_files_checked'],
            'valid_presets': self.validation_results['valid_presets'],
            'invalid_presets': self.validation_results['invalid_presets'],
            'partial_presets': self.validation_results['partial_presets'],
            'overall_status': 'valid' if self.validation_results['invalid_presets'] == 0 else 'invalid'
        }

    def fix_issues(self, preset_id: str) -> Dict[str, Any]:
        """
        Attempt to fix issues found during validation

        Args:
            preset_id: Preset identifier

        Returns:
            Fix report dictionary
        """
        report = {
            'preset_id': preset_id,
            'fixed': [],
            'failed': [],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        preset = self.model_manager.get_preset(preset_id)
        if not preset:
            report['error'] = f'Preset not found: {preset_id}'
            return report

        preset_files = self._get_preset_file_details(preset_id)

        for file_info in preset_files:
            file_path = self.models_dir / file_info['path']

            if not file_path.exists():
                continue  # Can't fix missing files

            # Try to fix permissions
            if not os.access(file_path, os.R_OK):
                try:
                    os.chmod(file_path, 0o644)
                    report['fixed'].append(f"{file_info['path']}: permissions fixed")
                except Exception as e:
                    report['failed'].append(f"{file_info['path']}: {str(e)}")

        return report


class ValidationReporter:
    """Handles reporting of validation results in various formats"""

    def __init__(self, validator: ModelValidator):
        self.validator = validator

    def generate_console_report(self, report: Dict[str, Any], verbose: bool = False) -> str:
        """
        Generate color-coded console report

        Args:
            report: Validation report dictionary
            verbose: Include detailed file information

        Returns:
            Formatted string for console output
        """
        lines = []

        # ANSI color codes
        GREEN = '\033[92m'
        RED = '\033[91m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        RESET = '\033[0m'

        preset_id = report.get('preset_id', 'unknown')
        preset_name = report.get('preset_name', preset_id)
        is_valid = report.get('valid', False)

        # Header
        status_icon = f"{GREEN}✓{RESET}" if is_valid else f"{RED}✗{RESET}"
        lines.append(f"\n{status_icon} {BLUE}{preset_name}{RESET} ({preset_id})")

        # Overall status
        status_text = f"{GREEN}VALID{RESET}" if is_valid else f"{RED}INVALID{RESET}"
        lines.append(f"Status: {status_text}")

        # File counts
        total_files = len(report.get('files', []))
        missing_files = len(report.get('missing', []))
        corrupted_files = len(report.get('corrupted', []))
        size_mismatches = len(report.get('size_mismatch', []))

        lines.append(f"Files: {total_files} total, {missing_files} missing, "
                    f"{corrupted_files} corrupted, {size_mismatches} size mismatches")

        # Detailed file information (verbose mode)
        if verbose:
            lines.append("\nDetailed File Information:")
            for file in report.get('files', []):
                file_path = file.get('path', 'unknown')
                file_valid = file.get('valid', False)

                if file_valid:
                    lines.append(f"  {GREEN}✓{RESET} {file_path}")

                    if 'actual_size_gb' in file:
                        lines.append(f"    Size: {file['actual_size_gb']}GB")

                    if file.get('sha256_verified'):
                        lines.append(f"    {GREEN}SHA256 verified{RESET}")
                else:
                    lines.append(f"  {RED}✗{RESET} {file_path}")

                    for issue in file.get('issues', []):
                        lines.append(f"    {RED}✗{RESET} {issue}")

        # Missing files
        if report.get('missing'):
            lines.append(f"\n{RED}Missing Files:{RESET}")
            for path in report['missing']:
                lines.append(f"  {RED}✗{RESET} {path}")

        # Corrupted files
        if report.get('corrupted'):
            lines.append(f"\n{RED}Corrupted Files:{RESET}")
            for path in report['corrupted']:
                lines.append(f"  {RED}✗{RESET} {path}")

        # Size mismatches
        if report.get('size_mismatch'):
            lines.append(f"\n{YELLOW}Size Mismatches:{RESET}")
            for path in report['size_mismatch']:
                lines.append(f"  {YELLOW}⚠{RESET} {path}")

        return '\n'.join(lines)

    def generate_json_report(self, report: Dict[str, Any]) -> str:
        """
        Generate JSON format report

        Args:
            report: Validation report dictionary

        Returns:
            JSON string
        """
        return json.dumps(report, indent=2)

    def generate_summary_report(self, results: Dict[str, Any]) -> str:
        """
        Generate summary report for multiple preset validations

        Args:
            results: Overall validation results dictionary

        Returns:
            Formatted summary string
        """
        lines = []

        # ANSI color codes
        GREEN = '\033[92m'
        RED = '\033[91m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        RESET = '\033[0m'

        lines.append(f"\n{BLUE}{'='*60}{RESET}")
        lines.append(f"{BLUE}Model Validation Summary{RESET}")
        lines.append(f"{BLUE}{'='*60}{RESET}")

        summary = self.validator.get_summary()

        lines.append(f"\nValidated: {summary['validated_at']}")
        lines.append(f"Total Presets Checked: {summary['total_presets']}")
        lines.append(f"Total Files Checked: {summary['total_files']}")

        lines.append(f"\n{GREEN}Valid Presets: {summary['valid_presets']}{RESET}")

        if summary['invalid_presets'] > 0:
            lines.append(f"{RED}Invalid Presets: {summary['invalid_presets']}{RESET}")
        else:
            lines.append(f"Invalid Presets: {summary['invalid_presets']}")

        if summary['partial_presets'] > 0:
            lines.append(f"{YELLOW}Partial Presets: {summary['partial_presets']}{RESET}")
        else:
            lines.append(f"Partial Presets: {summary['partial_presets']}")

        # Overall status
        overall_status = summary['overall_status']
        status_icon = f"{GREEN}✓{RESET}" if overall_status == 'valid' else f"{RED}✗{RESET}"
        lines.append(f"\n{status_icon} Overall Status: {overall_status.upper()}")

        # List invalid presets
        if summary['invalid_presets'] > 0:
            lines.append(f"\n{RED}Invalid Presets:{RESET}")
            for preset_id, details in results.get('preset_details', {}).items():
                if not details.get('valid', True):
                    preset_name = details.get('preset_name', preset_id)
                    lines.append(f"  {RED}✗{RESET} {preset_name} ({preset_id})")

                    if details.get('missing'):
                        lines.append(f"      Missing: {', '.join(details['missing'][:3])}")
                    if details.get('corrupted'):
                        lines.append(f"      Corrupted: {', '.join(details['corrupted'][:3])}")

        return '\n'.join(lines)


def main():
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(
        description="Validate downloaded ComfyUI models against preset specifications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate a specific preset
  python scripts/model_validator.py --preset SD1_5_TEXT_TO_IMAGE_BASIC

  # Validate all presets
  python scripts/model_validator.py --all

  # Validate all video generation presets
  python scripts/model_validator.py --all --category "Video Generation"

  # Output JSON format
  python scripts/model_validator.py --preset WAN_2_2_T2V_BASIC --json

  # Verbose output with file details
  python scripts/model_validator.py --preset FLUX_SCHNELL_BASIC --verbose

  # Attempt to fix issues
  python scripts/model_validator.py --preset SD1_5_TEXT_TO_IMAGE_BASIC --fix
        """
    )

    parser.add_argument(
        '--preset',
        help='Preset ID to validate'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Validate all presets'
    )

    parser.add_argument(
        '--category',
        help='Filter by category (e.g., "Video Generation", "Image Generation")'
    )

    parser.add_argument(
        '--models-dir',
        default='/workspace/ComfyUI/models',
        help='Models directory path (default: /workspace/ComfyUI/models)'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='Output in JSON format'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output with detailed file information'
    )

    parser.add_argument(
        '--fix',
        action='store_true',
        help='Attempt to fix fixable issues (e.g., permissions)'
    )

    parser.add_argument(
        '--output', '-o',
        help='Save report to file'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.preset and not args.all:
        parser.error("Either --preset or --all must be specified")

    if args.preset and args.all:
        parser.error("Cannot specify both --preset and --all")

    # Initialize validator
    validator = ModelValidator(models_dir=args.models_dir)
    reporter = ValidationReporter(validator)

    try:
        # Run validation
        if args.preset:
            # Validate single preset
            report = validator.validate_preset(args.preset)

            # Try to fix issues if requested
            if args.fix:
                fix_report = validator.fix_issues(args.preset)
                if fix_report.get('fixed'):
                    print(f"\nFixed issues:")
                    for fix in fix_report['fixed']:
                        print(f"  ✓ {fix}")
                    # Re-validate after fixes
                    report = validator.validate_preset(args.preset)

            # Generate output
            if args.json:
                output = reporter.generate_json_report(report)
            else:
                output = reporter.generate_console_report(report, verbose=args.verbose)

        else:
            # Validate all presets (optionally filtered by category)
            results = validator.validate_all_presets(category=args.category)

            # Generate output
            if args.json:
                output = reporter.generate_json_report(results)
            else:
                output = reporter.generate_summary_report(results)

        # Output results
        print(output)

        # Save to file if requested
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(output)
            print(f"\nReport saved to: {args.output}")

        # Set exit code
        if args.preset:
            exit_code = 0 if report.get('valid', False) else 1
        else:
            exit_code = 0 if results.get('overall_status') == 'valid' else 1

        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n[ERROR] Validation failed: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
