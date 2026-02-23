"""
Unit tests for Workflow Scanner Service - Model Index Loading
Tests for Task 2: Add model index loading to WorkflowScanner
"""
import json
import tempfile
from pathlib import Path
import sys
import importlib.util

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load module directly from file to avoid circular import in dashboard.core.__init__.py
_spec = importlib.util.spec_from_file_location(
    "workflow_scanner",
    project_root / "dashboard" / "core" / "workflow_scanner.py"
)
workflow_scanner_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(workflow_scanner_module)
WorkflowScanner = workflow_scanner_module.WorkflowScanner


def test_load_model_index():
    """Test that WorkflowScanner loads model_index.json mapping."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create mock model_index.json
        index_path = Path(tmpdir) / "data" / "model_index.json"
        index_path.parent.mkdir(parents=True)

        index_data = {
            "version": "1.0.0",
            "mappings": {
                "checkpoints/flux-dev.safetensors": "FLUX_DEV",
                "text_encoders/t5xxl_fp16.safetensors": "T5_XXL"
            }
        }
        with open(index_path, 'w') as f:
            json.dump(index_data, f)

        # Create scanner with custom index path
        workflow_path = Path(tmpdir) / "workflows"
        workflow_path.mkdir()

        scanner = WorkflowScanner(workflow_path)
        scanner._model_index_path = index_path
        scanner._load_model_index()

        assert "checkpoints/flux-dev.safetensors" in scanner._model_index
        assert scanner._model_index["checkpoints/flux-dev.safetensors"] == "FLUX_DEV"


def test_load_model_index_missing_file():
    """Test that missing model_index.json is handled gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workflow_path = Path(tmpdir) / "workflows"
        workflow_path.mkdir()

        scanner = WorkflowScanner(workflow_path)
        # Set a non-existent path
        scanner._model_index_path = Path(tmpdir) / "nonexistent" / "model_index.json"
        scanner._load_model_index()

        # Should have empty index, not crash
        assert scanner._model_index == {}


def test_load_model_index_invalid_json():
    """Test that invalid JSON in model_index.json is handled gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        index_path = Path(tmpdir) / "data" / "model_index.json"
        index_path.parent.mkdir(parents=True)

        # Write invalid JSON
        with open(index_path, 'w') as f:
            f.write("not valid json {{{")

        workflow_path = Path(tmpdir) / "workflows"
        workflow_path.mkdir()

        scanner = WorkflowScanner(workflow_path)
        scanner._model_index_path = index_path
        scanner._load_model_index()

        # Should have empty index, not crash
        assert scanner._model_index == {}


def test_load_model_index_missing_mappings_key():
    """Test that model_index.json without 'mappings' key is handled."""
    with tempfile.TemporaryDirectory() as tmpdir:
        index_path = Path(tmpdir) / "data" / "model_index.json"
        index_path.parent.mkdir(parents=True)

        # Valid JSON but missing 'mappings' key
        index_data = {"version": "1.0.0"}
        with open(index_path, 'w') as f:
            json.dump(index_data, f)

        workflow_path = Path(tmpdir) / "workflows"
        workflow_path.mkdir()

        scanner = WorkflowScanner(workflow_path)
        scanner._model_index_path = index_path
        scanner._load_model_index()

        # Should have empty index
        assert scanner._model_index == {}
