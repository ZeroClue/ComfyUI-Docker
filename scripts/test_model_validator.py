#!/usr/bin/env python3
"""
Test script for Model Validator
Demonstrates validation capabilities and creates test scenarios
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add script directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from model_validator import ModelValidator, ValidationReporter
except ImportError:
    print("[ERROR] Failed to import model_validator")
    sys.exit(1)


def create_test_environment():
    """Create a temporary test environment with sample files"""
    test_dir = tempfile.mkdtemp(prefix="model_validator_test_")
    models_dir = Path(test_dir) / "ComfyUI" / "models"

    # Create directory structure
    (models_dir / "checkpoints").mkdir(parents=True, exist_ok=True)
    (models_dir / "text_encoders").mkdir(parents=True, exist_ok=True)
    (models_dir / "vae").mkdir(parents=True, exist_ok=True)

    # Create test files with known sizes
    test_files = {
        "checkpoints/test_model.safetensors": 1024 * 1024 * 100,  # 100MB
        "text_encoders/test_encoder.safetensors": 1024 * 1024 * 50,  # 50MB
        "vae/test_vae.safetensors": 1024 * 1024 * 25,  # 25MB
    }

    created_files = []
    for file_path, size in test_files.items():
        full_path = models_dir / file_path
        with open(full_path, 'wb') as f:
            f.write(b'\x00' * size)
        created_files.append(full_path)

    print(f"[INFO] Created test environment in: {test_dir}")
    print(f"[INFO] Created {len(created_files)} test files")

    return test_dir, models_dir, created_files


def test_basic_validation(validator):
    """Test basic preset validation"""
    print("\n" + "="*60)
    print("TEST: Basic Preset Validation")
    print("="*60)

    # Test with a real preset
    report = validator.validate_preset("SD1_5_TEXT_TO_IMAGE_BASIC")

    print(f"\nPreset ID: {report['preset_id']}")
    print(f"Preset Name: {report['preset_name']}")
    print(f"Category: {report['category']}")
    print(f"Valid: {report['valid']}")
    print(f"Total Files: {len(report['files'])}")
    print(f"Missing Files: {len(report['missing'])}")
    print(f"Corrupted Files: {len(report['corrupted'])}")

    return report


def test_json_output(validator, report):
    """Test JSON output generation"""
    print("\n" + "="*60)
    print("TEST: JSON Output Generation")
    print("="*60)

    reporter = ValidationReporter(validator)
    json_output = reporter.generate_json_report(report)

    print("\nJSON Output (first 500 chars):")
    print(json_output[:500] + "...")

    # Verify it's valid JSON
    import json
    try:
        parsed = json.loads(json_output)
        print(f"\n✓ JSON is valid")
        print(f"✓ Contains {len(parsed)} keys")
    except json.JSONDecodeError as e:
        print(f"\n✗ JSON parsing failed: {e}")


def test_console_output(validator, report):
    """Test console output generation"""
    print("\n" + "="*60)
    print("TEST: Console Output Generation")
    print("="*60)

    reporter = ValidationReporter(validator)
    console_output = reporter.generate_console_report(report, verbose=True)

    print("\nConsole Output:")
    print(console_output)


def test_category_validation(validator):
    """Test category-based validation"""
    print("\n" + "="*60)
    print("TEST: Category-Based Validation")
    print("="*60)

    categories = ["Video Generation", "Image Generation", "Audio Generation"]

    for category in categories:
        results = validator.validate_all_presets(category=category)
        summary = validator.get_summary()

        print(f"\n{category}:")
        print(f"  Total Presets: {summary['total_presets']}")
        print(f"  Valid: {summary['valid_presets']}")
        print(f"  Invalid: {summary['invalid_presets']}")


def test_size_parsing(validator):
    """Test size string parsing"""
    print("\n" + "="*60)
    print("TEST: Size String Parsing")
    print("="*60)

    test_sizes = [
        "4.8GB",
        "300MB",
        "1.5GB (9536MB)",
        "1024KB",
        "512B"
    ]

    print("\nSize Parsing Results:")
    for size_str in test_sizes:
        parsed = validator._parse_size_string(size_str)
        if parsed:
            gb = parsed / (1024**3)
            mb = parsed / (1024**2)
            print(f"  {size_str:20s} -> {parsed:>15} bytes ({gb:.2f} GB, {mb:.2f} MB)")
        else:
            print(f"  {size_str:20s} -> PARSE FAILED")


def test_summary_generation(validator):
    """Test validation summary generation"""
    print("\n" + "="*60)
    print("TEST: Summary Generation")
    print("="*60)

    # Validate a few presets
    test_presets = ["SD1_5_TEXT_TO_IMAGE_BASIC", "WAN_2_2_T2V_BASIC"]
    for preset_id in test_presets:
        validator.validate_preset(preset_id)

    summary = validator.get_summary()

    print("\nValidation Summary:")
    print(f"  Validated At: {summary['validated_at']}")
    print(f"  Total Presets: {summary['total_presets']}")
    print(f"  Total Files: {summary['total_files']}")
    print(f"  Valid Presets: {summary['valid_presets']}")
    print(f"  Invalid Presets: {summary['invalid_presets']}")
    print(f"  Overall Status: {summary['overall_status']}")


def main():
    """Run all tests"""
    print("="*60)
    print("Model Validator Test Suite")
    print("="*60)

    # Initialize validator
    print("\n[INFO] Initializing validator...")
    try:
        validator = ModelValidator()
        print("[INFO] ✓ Validator initialized successfully")
    except Exception as e:
        print(f"[ERROR] Failed to initialize validator: {e}")
        return 1

    # Run tests
    try:
        # Test 1: Basic validation
        report = test_basic_validation(validator)

        # Test 2: JSON output
        test_json_output(validator, report)

        # Test 3: Console output
        test_console_output(validator, report)

        # Test 4: Size parsing
        test_size_parsing(validator)

        # Test 5: Category validation (limited)
        print("\n" + "="*60)
        print("TEST: Category-Based Validation (limited)")
        print("="*60)

        # Just test one category to keep output manageable
        results = validator.validate_all_presets(category="Audio Generation")
        summary = validator.get_summary()

        print(f"\nAudio Generation:")
        print(f"  Total Presets: {summary['total_presets']}")
        print(f"  Valid: {summary['valid_presets']}")
        print(f"  Invalid: {summary['invalid_presets']}")

        # Test 6: Summary generation
        print("\n" + "="*60)
        print("TEST: Summary Generation")
        print("="*60)

        print("\nValidation Summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")

        print("\n" + "="*60)
        print("All tests completed successfully!")
        print("="*60)

        return 0

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
