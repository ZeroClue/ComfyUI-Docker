#!/usr/bin/env python3
"""
Test script for ComfyUI Preset Manager
Validates core functionality without running the full Flask app
"""

import os
import sys
import tempfile
import json
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test required imports"""
    print("Testing imports...")

    try:
        from flask import Flask
        print("✓ Flask imported successfully")
    except ImportError as e:
        print(f"✗ Flask import failed: {e}")
        return False

    # Test optional imports
    try:
        import markdown
        print("✓ Markdown available")
    except ImportError:
        print("⚠ Markdown not available (README rendering will be limited)")

    try:
        from flask_session import Session
        print("✓ Flask-Session available")
    except ImportError:
        print("⚠ Flask-Session not available (using default session handling)")

    return True

def test_model_manager():
    """Test ModelManager class"""
    print("\nTesting ModelManager...")

    try:
        # Try to import Flask first
        try:
            from flask import Flask
        except ImportError:
            print("⚠ Flask not available, skipping ModelManager tests")
            return True

        # Import and create ModelManager
        from preset_manager import ModelManager

        # Create temporary directories for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test model directory structure
            model_dir = os.path.join(temp_dir, "models")
            os.makedirs(model_dir, exist_ok=True)

            # Create test subdirectories
            for subdir in ['checkpoints', 'diffusion_models', 'text_encoders', 'vae']:
                os.makedirs(os.path.join(model_dir, subdir), exist_ok=True)

            # Test ModelManager initialization
            manager = ModelManager()
            print("✓ ModelManager initialized successfully")

            # Test preset parsing
            assert len(manager.presets) > 0, "No presets loaded"
            print(f"✓ Loaded {len(manager.presets)} presets")

            # Test category organization
            assert len(manager.categories) == 3, "Expected 3 categories"
            print(f"✓ Organized into {len(manager.categories)} categories")

            # Test preset retrieval
            preset = manager.get_preset('FLUX_SCHNELL_BASIC')
            assert preset is not None, "FLUX_SCHNELL_BASIC preset not found"
            assert preset['category'] == 'Image Generation', "Wrong category"
            print("✓ Preset retrieval working correctly")

            # Test storage info (will return minimal data in test environment)
            storage_info = manager.get_storage_info()
            assert isinstance(storage_info, dict), "Storage info should be dict"
            print("✓ Storage info generation working")

            return True

    except Exception as e:
        print(f"✗ ModelManager test failed: {e}")
        return False

def test_preset_definitions():
    """Test preset definitions for consistency"""
    print("\nTesting preset definitions...")

    try:
        # Try to import Flask first
        try:
            from flask import Flask
        except ImportError:
            print("⚠ Flask not available, skipping preset definitions tests")
            return True

        from preset_manager import ModelManager
        manager = ModelManager()

        # Check all presets have required fields
        required_fields = ['name', 'category', 'type', 'description', 'download_size', 'files', 'use_case']

        for preset_id, preset in manager.presets.items():
            for field in required_fields:
                assert field in preset, f"Preset {preset_id} missing field: {field}"

            # Check files list is not empty
            assert len(preset['files']) > 0, f"Preset {preset_id} has no files"

            # Check download size format
            assert 'GB' in preset['download_size'] or 'MB' in preset['download_size'], \
                f"Preset {preset_id} has invalid size format: {preset['download_size']}"

        print(f"✓ All {len(manager.presets)} presets have valid definitions")

        # Check categories
        expected_categories = ['Video Generation', 'Image Generation', 'Audio Generation']
        for category in expected_categories:
            assert category in manager.categories, f"Missing category: {category}"

        print("✓ All expected categories present")

        return True

    except Exception as e:
        print(f"✗ Preset definition test failed: {e}")
        return False

def test_file_operations():
    """Test file operation functions"""
    print("\nTesting file operations...")

    try:
        # Try to import Flask first
        try:
            from flask import Flask
        except ImportError:
            print("⚠ Flask not available, skipping file operations tests")
            return True

        from preset_manager import ModelManager

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test environment
            model_dir = os.path.join(temp_dir, "models")
            os.makedirs(model_dir, exist_ok=True)

            # Create test file
            test_file = os.path.join(model_dir, "test_model.safetensors")
            with open(test_file, 'w') as f:
                f.write("test content")

            # Initialize manager with test directory
            manager = ModelManager()

            # Test directory size calculation
            size = manager._get_directory_size(model_dir)
            assert size > 0, "Directory size should be > 0"
            print("✓ Directory size calculation working")

            # Test file counting
            count = manager._count_files(model_dir)
            assert count == 1, f"Expected 1 file, found {count}"
            print("✓ File counting working")

            return True

    except Exception as e:
        print(f"✗ File operations test failed: {e}")
        return False

def test_template_files():
    """Test that template files exist and are valid"""
    print("\nTesting template files...")

    template_dir = os.path.join(os.path.dirname(__file__), "templates")

    required_templates = [
        "base.html",
        "login.html",
        "index.html",
        "presets.html",
        "preset_detail.html",
        "storage.html"
    ]

    for template in required_templates:
        template_path = os.path.join(template_dir, template)
        if not os.path.exists(template_path):
            print(f"✗ Missing template: {template}")
            return False

        # Check template contains basic HTML structure
        with open(template_path, 'r') as f:
            content = f.read()
            if template not in ["base.html", "login.html"]:
                # All templates except login should extend base.html
                assert '{% extends "base.html" %}' in content, \
                    f"Template {template} should extend base.html"

        print(f"✓ Template {template} is valid")

    return True

def test_nginx_config():
    """Test Nginx configuration includes preset manager"""
    print("\nTesting Nginx configuration...")

    nginx_conf = os.path.join(os.path.dirname(__file__), "..", "proxy", "nginx.conf")

    if not os.path.exists(nginx_conf):
        print(f"✗ Nginx config not found: {nginx_conf}")
        return False

    with open(nginx_conf, 'r') as f:
        content = f.read()

    # Check for preset manager configuration
    if "Preset Manager" not in content:
        print("✗ Nginx config missing preset manager section")
        return False

    if "listen 9000" not in content:
        print("✗ Nginx config missing preset manager port")
        return False

    if "localhost:9001" not in content:
        print("✗ Nginx config missing preset manager proxy target")
        return False

    print("✓ Nginx configuration includes preset manager")
    return True

def test_startup_script():
    """Test startup script includes preset manager"""
    print("\nTesting startup script...")

    start_script = os.path.join(os.path.dirname(__file__), "start.sh")

    if not os.path.exists(start_script):
        print(f"✗ Startup script not found: {start_script}")
        return False

    with open(start_script, 'r') as f:
        content = f.read()

    # Check for preset manager function
    if "start_preset_manager" not in content:
        print("✗ Startup script missing start_preset_manager function")
        return False

    # Check for function call
    if "start_preset_manager" not in content.split("start_preset_manager()")[-1]:
        print("✗ Startup script missing start_preset_manager call")
        return False

    print("✓ Startup script includes preset manager")
    return True

def main():
    """Run all tests"""
    print("=== ComfyUI Preset Manager Test Suite ===\n")

    tests = [
        test_imports,
        test_model_manager,
        test_preset_definitions,
        test_file_operations,
        test_template_files,
        test_nginx_config,
        test_startup_script
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")

    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")

    if passed == total:
        print("🎉 All tests passed! The preset manager is ready to use.")
        return 0
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())