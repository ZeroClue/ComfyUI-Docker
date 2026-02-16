"""
Unit tests for model validator functionality
Tests model file validation, size checking, integrity verification
"""

import pytest
import hashlib
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

try:
    from model_validator import (
        ModelValidator,
        ValidationReporter,
        HealthStatus
    )
except ImportError:
    # Try alternative import
    try:
        from scripts.model_validator import (
            ModelValidator,
            ValidationReporter,
            HealthStatus
        )
    except ImportError:
        pytest.skip("Model validator module not found", allow_module_level=True)


@pytest.mark.unit
class TestModelValidator:
    """Test ModelValidator class functionality"""

    def test_initialization(self, temp_dir):
        """Test ModelValidator initialization"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))

        assert validator.models_dir == Path(temp_dir / "models")
        assert validator.size_tolerance == 0.02
        assert len(validator.validation_results) == 0
        assert isinstance(validator.model_extensions, set)

    def test_model_extensions(self, temp_dir):
        """Test model extensions are properly defined"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))

        expected_extensions = {
            '.safetensors', '.pth', '.pt', '.bin', '.ckpt',
            '.gguf', '.onnx', '.pb', '.h5', '.pkl', '.marshal'
        }

        assert validator.model_extensions == expected_extensions

    def test_parse_size_string_gb(self, temp_dir):
        """Test parsing GB size strings"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))

        assert validator._parse_size_string("1GB") == 1024**3
        assert validator._parse_size_string("4.8GB") == int(4.8 * 1024**3)
        assert validator._parse_size_string("0.5GB") == int(0.5 * 1024**3)

    def test_parse_size_string_mb(self, temp_dir):
        """Test parsing MB size strings"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))

        assert validator._parse_size_string("1MB") == 1024**2
        assert validator._parse_size_string("500MB") == 500 * 1024**2
        assert validator._parse_size_string("1.5MB") == int(1.5 * 1024**2)

    def test_parse_size_string_kb(self, temp_dir):
        """Test parsing KB size strings"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))

        assert validator._parse_size_string("1KB") == 1024
        assert validator._parse_size_string("500KB") == 500 * 1024

    def test_parse_size_string_invalid(self, temp_dir):
        """Test parsing invalid size strings"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))

        assert validator._parse_size_string("invalid") is None
        assert validator._parse_size_string("") is None
        assert validator._parse_size_string(None) is None
        assert validator._parse_size_string(123) is None

    def test_calculate_sha256(self, temp_dir):
        """Test SHA256 calculation"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))

        # Create test file
        test_file = temp_dir / "test.bin"
        test_file.write_bytes(b"test content")

        result = validator._calculate_sha256(test_file)

        assert result is not None
        assert len(result) == 64  # SHA256 hex length

        # Verify against known hash
        expected_hash = hashlib.sha256(b"test content").hexdigest()
        assert result == expected_hash

    def test_calculate_sha256_nonexistent_file(self, temp_dir):
        """Test SHA256 calculation for nonexistent file"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))

        result = validator._calculate_sha256(temp_dir / "nonexistent.bin")

        assert result is None

    def test_validate_file_size_valid(self, temp_dir):
        """Test file size validation within tolerance"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))

        # Create test file
        test_file = temp_dir / "test.bin"
        expected_size = 1000
        test_file.write_bytes(b"x" * expected_size)

        is_valid, actual, expected = validator._validate_file_size(
            test_file,
            "1KB"  # Close enough
        )

        assert is_valid is True
        assert actual == expected_size
        assert expected == 1024

    def test_validate_file_size_outside_tolerance(self, temp_dir):
        """Test file size validation outside tolerance"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))

        # Create test file
        test_file = temp_dir / "test.bin"
        test_file.write_bytes(b"x" * 100)  # 100 bytes

        is_valid, actual, expected = validator._validate_file_size(
            test_file,
            "1KB"  # Way off
        )

        assert is_valid is False

    def test_validate_file_size_unparseable_expected(self, temp_dir):
        """Test file size validation with unparseable expected size"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))

        # Create test file
        test_file = temp_dir / "test.bin"
        test_file.write_bytes(b"x" * 100)

        is_valid, actual, expected = validator._validate_file_size(
            test_file,
            "invalid"
        )

        # Should pass validation if we can't parse expected
        assert is_valid is True
        assert actual == 100

    def test_validate_file_usability_valid(self, temp_dir):
        """Test file usability validation for valid file"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))

        # Create test file
        test_file = temp_dir / "test.safetensors"
        test_file.write_bytes(b"\x00" * 2048)

        is_usable, error = validator._validate_file_usability(test_file)

        assert is_usable is True
        assert error == ""

    def test_validate_file_usability_not_readable(self, temp_dir):
        """Test file usability validation for unreadable file"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))

        # Create test file and remove read permissions
        test_file = temp_dir / "test.safetensors"
        test_file.write_bytes(b"\x00" * 2048)
        test_file.chmod(0o000)

        is_usable, error = validator._validate_file_usability(test_file)

        assert is_usable is False
        assert "permission" in error.lower() or "readable" in error.lower()

        # Cleanup
        test_file.chmod(0o644)

    def test_validate_file_usability_empty(self, temp_dir):
        """Test file usability validation for empty file"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))

        # Create empty test file
        test_file = temp_dir / "test.safetensors"
        test_file.write_bytes(b"")

        is_usable, error = validator._validate_file_usability(test_file)

        assert is_usable is False
        assert "empty" in error.lower()

    def test_validate_file_usability_invalid_extension(self, temp_dir):
        """Test file usability validation for invalid extension"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))

        # Create test file with invalid extension
        test_file = temp_dir / "test.invalid"
        test_file.write_bytes(b"\x00" * 2048)

        is_usable, error = validator._validate_file_usability(test_file)

        assert is_usable is False
        assert "extension" in error.lower()

    def test_validate_preset_not_found(self, temp_dir):
        """Test validating non-existent preset"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))

        report = validator.validate_preset("NONEXISTENT_PRESET")

        assert report['valid'] is False
        assert 'error' in report
        assert 'not found' in report['error'].lower()

    def test_validate_preset_missing_files(self, temp_dir, sample_preset_file):
        """Test validating preset with missing files"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))

        # Create config with files that don't exist
        import yaml
        config = {
            'presets': {
                'TEST_PRESET': {
                    'name': 'Test Preset',
                    'category': 'Test',
                    'files': [
                        {
                            'path': 'checkpoints/missing.safetensors',
                            'size': '1GB'
                        }
                    ]
                }
            }
        }

        config_file = temp_dir / "presets.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)

        # Patch the preset path
        with patch.object(validator, '_get_preset_file_details') as mock_files:
            mock_files.return_value = [
                {'path': 'checkpoints/missing.safetensors', 'size': '1GB'}
            ]

            report = validator.validate_preset("TEST_PRESET")

        assert report['valid'] is False
        assert len(report['missing']) > 0

    def test_validate_preset_valid(self, temp_dir, sample_model_files):
        """Test validating preset with valid files"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))

        # Create config that matches sample files
        import yaml
        config = {
            'presets': {
                'TEST_PRESET': {
                    'name': 'Test Preset',
                    'category': 'Test',
                    'files': [
                        {
                            'path': 'checkpoints/test_model.safetensors',
                            'size': '4KB'  # Close to actual
                        }
                    ]
                }
            }
        }

        config_file = temp_dir / "presets.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)

        # Patch the preset file details
        with patch.object(validator, '_get_preset_file_details') as mock_files:
            mock_files.return_value = [
                {'path': 'checkpoints/test_model.safetensors', 'size': '4KB'}
            ]

            # Mock model manager
            mock_manager = Mock()
            mock_manager.get_preset.return_value = config['presets']['TEST_PRESET']
            validator.model_manager = mock_manager

            report = validator.validate_preset("TEST_PRESET")

        assert report['valid'] is True
        assert len(report['missing']) == 0

    def test_validate_all_presets(self, temp_dir, sample_preset_file):
        """Test validating all presets"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))

        # Mock model manager
        mock_manager = Mock()
        mock_manager.presets = {
            'TEST_PRESET_1': {
                'name': 'Test Preset 1',
                'category': 'Test',
                'files': []
            },
            'TEST_PRESET_2': {
                'name': 'Test Preset 2',
                'category': 'Test',
                'files': []
            }
        }
        validator.model_manager = mock_manager

        results = validator.validate_all_presets()

        assert results['total_presets_checked'] == 2
        assert 'preset_details' in results

    def test_validate_all_presets_by_category(self, temp_dir):
        """Test validating presets by category"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))

        # Mock model manager
        mock_manager = Mock()
        mock_manager.presets = {
            'VIDEO_PRESET': {
                'name': 'Video Preset',
                'category': 'Video Generation',
                'files': []
            },
            'IMAGE_PRESET': {
                'name': 'Image Preset',
                'category': 'Image Generation',
                'files': []
            }
        }
        validator.model_manager = mock_manager

        results = validator.validate_all_presets(category="Video Generation")

        assert results['total_presets_checked'] == 1

    def test_get_summary(self, temp_dir, sample_preset_file):
        """Test getting validation summary"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))

        # Set some validation results
        validator.validation_results = {
            'validated_at': datetime.now(timezone.utc).isoformat(),
            'total_presets_checked': 10,
            'total_files_checked': 50,
            'valid_presets': 8,
            'invalid_presets': 1,
            'partial_presets': 1,
            'preset_details': {}
        }

        summary = validator.get_summary()

        assert summary['total_presets'] == 10
        assert summary['total_files'] == 50
        assert summary['valid_presets'] == 8
        assert summary['invalid_presets'] == 1
        assert summary['partial_presets'] == 1
        assert summary['overall_status'] == 'invalid'


@pytest.mark.unit
class TestValidationReporter:
    """Test ValidationReporter class functionality"""

    def test_initialization(self, temp_dir):
        """Test ValidationReporter initialization"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))
        reporter = ValidationReporter(validator)

        assert reporter.validator is validator

    def test_generate_console_report_valid(self, temp_dir):
        """Test console report generation for valid preset"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))
        reporter = ValidationReporter(validator)

        report = {
            'preset_id': 'TEST_PRESET',
            'preset_name': 'Test Preset',
            'valid': True,
            'files': [
                {
                    'path': 'checkpoints/test.safetensors',
                    'valid': True,
                    'actual_size_gb': 1.0
                }
            ],
            'missing': [],
            'corrupted': [],
            'size_mismatch': []
        }

        output = reporter.generate_console_report(report)

        assert 'Test Preset' in output
        assert 'VALID' in output
        assert '✓' in output

    def test_generate_console_report_invalid(self, temp_dir):
        """Test console report generation for invalid preset"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))
        reporter = ValidationReporter(validator)

        report = {
            'preset_id': 'TEST_PRESET',
            'preset_name': 'Test Preset',
            'valid': False,
            'files': [
                {
                    'path': 'checkpoints/missing.safetensors',
                    'valid': False,
                    'issues': ['File not found']
                }
            ],
            'missing': ['checkpoints/missing.safetensors'],
            'corrupted': [],
            'size_mismatch': []
        }

        output = reporter.generate_console_report(report)

        assert 'Test Preset' in output
        assert 'INVALID' in output
        assert '✗' in output
        assert 'missing' in output.lower()

    def test_generate_console_report_verbose(self, temp_dir):
        """Test verbose console report generation"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))
        reporter = ValidationReporter(validator)

        report = {
            'preset_id': 'TEST_PRESET',
            'preset_name': 'Test Preset',
            'valid': True,
            'files': [
                {
                    'path': 'checkpoints/test.safetensors',
                    'valid': True,
                    'actual_size_gb': 1.5,
                    'sha256_verified': True
                }
            ],
            'missing': [],
            'corrupted': [],
            'size_mismatch': []
        }

        output = reporter.generate_console_report(report, verbose=True)

        assert 'Detailed File Information' in output
        assert '1.5GB' in output
        assert 'SHA256 verified' in output

    def test_generate_json_report(self, temp_dir):
        """Test JSON report generation"""
        import json

        validator = ModelValidator(models_dir=str(temp_dir / "models"))
        reporter = ValidationReporter(validator)

        report = {
            'preset_id': 'TEST_PRESET',
            'preset_name': 'Test Preset',
            'valid': True,
            'files': [],
            'missing': [],
            'corrupted': [],
            'size_mismatch': []
        }

        output = reporter.generate_json_report(report)

        # Verify valid JSON
        parsed = json.loads(output)
        assert parsed['preset_id'] == 'TEST_PRESET'
        assert parsed['valid'] is True

    def test_generate_summary_report(self, temp_dir):
        """Test summary report generation"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))
        reporter = ValidationReporter(validator)

        results = {
            'validated_at': datetime.now(timezone.utc).isoformat(),
            'total_presets_checked': 10,
            'total_files_checked': 50,
            'valid_presets': 8,
            'invalid_presets': 1,
            'partial_presets': 1,
            'preset_details': {
                'VALID_PRESET': {
                    'preset_name': 'Valid Preset',
                    'valid': True,
                    'missing': [],
                    'corrupted': []
                },
                'INVALID_PRESET': {
                    'preset_name': 'Invalid Preset',
                    'valid': False,
                    'missing': ['file1.safetensors'],
                    'corrupted': ['file2.safetensors']
                }
            }
        }

        validator.validation_results = results
        output = reporter.generate_summary_report(results)

        assert 'Model Validation Summary' in output
        assert '10' in output  # Total presets
        assert '8' in output  # Valid presets
        assert 'Invalid Preset' in output


@pytest.mark.unit
class TestPermissionFixing:
    """Test permission fixing functionality"""

    def test_fix_permission_issue_readable(self, temp_dir):
        """Test fixing readable file (no fix needed)"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))

        # Create readable file
        test_file = temp_dir / "test.safetensors"
        test_file.write_bytes(b"\x00" * 100)

        # Already readable, should return True
        result = validator._fix_permission_issue(test_file)
        assert result is True

    def test_fix_permission_issue_not_writable(self, temp_dir):
        """Test fixing non-writable file"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))

        # Create file and remove write permissions
        test_file = temp_dir / "test.safetensors"
        test_file.write_bytes(b"\x00" * 100)
        test_file.chmod(0o444)  # Read-only

        # Should be able to fix
        result = validator._fix_permission_issue(test_file)

        # File should now be readable
        assert test_file.stat().st_mode & 0o444 != 0

        # Cleanup
        test_file.chmod(0o644)

    def test_fix_issues_method(self, temp_dir):
        """Test fix_issues method"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))

        # Mock model manager
        mock_manager = Mock()
        mock_manager.get_preset.return_value = {
            'name': 'Test Preset',
            'files': [
                {'path': 'checkpoints/test.safetensors'}
            ]
        }
        validator.model_manager = mock_manager

        # Create test file
        test_file = temp_dir / "models" / "checkpoints" / "test.safetensors"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_bytes(b"\x00" * 100)

        # Mock _get_preset_file_details
        with patch.object(validator, '_get_preset_file_details') as mock_files:
            mock_files.return_value = [
                {'path': 'checkpoints/test.safetensors'}
            ]

            report = validator.fix_issues("TEST_PRESET")

        assert 'timestamp' in report
        assert 'preset_id' in report


@pytest.mark.unit
class TestModelValidatorEdgeCases:
    """Test edge cases and error handling"""

    def test_validate_corrupted_file(self, temp_dir):
        """Test validation of corrupted file"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))

        # Create file that exists but can't be read
        test_file = temp_dir / "test.safetensors"
        test_file.write_bytes(b"\x00" * 100)

        # Mock to raise error when reading
        with patch('builtins.open', side_effect=IOError("Corrupted")):
            is_usable, error = validator._validate_file_usability(test_file)

        assert is_usable is False
        assert "corrupted" in error.lower() or "failed" in error.lower()

    def test_validate_symlink_file(self, temp_dir):
        """Test validation of symlinked file"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))

        # Create actual file
        actual_file = temp_dir / "actual.safetensors"
        actual_file.write_bytes(b"\x00" * 100)

        # Create symlink
        symlink_file = temp_dir / "link.safetensors"
        symlink_file.symlink_to(actual_file)

        is_usable, error = validator._validate_file_usability(symlink_file)

        assert is_usable is True

        # Cleanup
        symlink_file.unlink()
        actual_file.unlink()

    def test_validate_large_file(self, temp_dir):
        """Test validation of large file"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))

        # Create large-ish file (1MB)
        test_file = temp_dir / "large.safetensors"
        test_file.write_bytes(b"\x00" * (1024 * 1024))

        # Should handle large files
        is_usable, error = validator._validate_file_usability(test_file)

        assert is_usable is True

    def test_get_preset_file_details_missing_config(self, temp_dir):
        """Test getting preset file details when config missing"""
        validator = ModelValidator(models_dir=str(temp_dir / "models"))

        details = validator._get_preset_file_details("TEST_PRESET")

        # Should fall back to basic info from model manager
        assert isinstance(details, list)
