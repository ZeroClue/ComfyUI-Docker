"""
Tests for Workflow Scanner Service
"""
import pytest
from pathlib import Path
import json
import sys
import importlib.util

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load module directly from file to avoid circular import in dashboard.core.__init__.py
_spec = importlib.util.spec_from_file_location(
    "workflow_scanner",
    project_root / "dashboard" / "core" / "workflow_scanner.py"
)
workflow_scanner_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(workflow_scanner_module)
WorkflowScanner = workflow_scanner_module.WorkflowScanner


def test_scan_workflow_extracts_metadata(tmp_path):
    """Test that scanner extracts workflow metadata correctly."""
    # Create a sample workflow file
    workflow = {
        "_meta": {
            "name": "Test Workflow",
            "description": "A test workflow",
            "category": "video"
        },
        "nodes": [
            {"type": "KSampler", "inputs": {"text": ""}},
            {"type": "VAEDecode", "inputs": {}}
        ]
    }

    workflow_file = tmp_path / "test_workflow.json"
    workflow_file.write_text(json.dumps(workflow))

    scanner = WorkflowScanner(tmp_path)
    result = scanner.scan_workflow(workflow_file)

    assert result["name"] == "Test Workflow"
    assert result["description"] == "A test workflow"
    assert result["category"] == "video"
    assert result["node_count"] == 2


def test_scan_workflow_detects_input_types(tmp_path):
    """Test that scanner detects input types from node types."""
    workflow = {
        "_meta": {"name": "Input Test"},
        "nodes": [
            {"type": "CLIPTextEncode", "inputs": {}},
            {"type": "LoadImage", "inputs": {}},
            {"type": "LoadAudio", "inputs": {}},
            {"type": "VHS_LoadVideo", "inputs": {}},
        ]
    }

    workflow_file = tmp_path / "input_test.json"
    workflow_file.write_text(json.dumps(workflow))

    scanner = WorkflowScanner(tmp_path)
    result = scanner.scan_workflow(workflow_file)

    assert "text" in result["input_types"]
    assert "image" in result["input_types"]
    assert "audio" in result["input_types"]
    assert "video" in result["input_types"]


def test_scan_workflow_detects_output_types(tmp_path):
    """Test that scanner detects output types from node types."""
    workflow = {
        "_meta": {"name": "Output Test"},
        "nodes": [
            {"type": "SaveImage", "inputs": {}},
            {"type": "VHS_SaveVideo", "inputs": {}},
            {"type": "SaveAudio", "inputs": {}},
        ]
    }

    workflow_file = tmp_path / "output_test.json"
    workflow_file.write_text(json.dumps(workflow))

    scanner = WorkflowScanner(tmp_path)
    result = scanner.scan_workflow(workflow_file)

    assert "image" in result["output_types"]
    assert "video" in result["output_types"]
    assert "audio" in result["output_types"]


def test_scan_workflow_api_format(tmp_path):
    """Test that scanner handles API format workflows (dict of nodes)."""
    workflow = {
        "_meta": {
            "name": "API Format Workflow",
            "description": "API format test"
        },
        "1": {
            "class_type": "KSampler",
            "inputs": {"text": "test"}
        },
        "2": {
            "class_type": "VAEDecode",
            "inputs": {}
        },
        "3": {
            "class_type": "SaveImage",
            "inputs": {}
        }
    }

    workflow_file = tmp_path / "api_format.json"
    workflow_file.write_text(json.dumps(workflow))

    scanner = WorkflowScanner(tmp_path)
    result = scanner.scan_workflow(workflow_file)

    assert result["name"] == "API Format Workflow"
    assert result["description"] == "API format test"
    assert result["node_count"] == 3  # Excludes _meta
    assert "image" in result["output_types"]


def test_scan_workflow_without_meta(tmp_path):
    """Test that scanner handles workflows without _meta section."""
    workflow = {
        "nodes": [
            {"type": "KSampler", "inputs": {}}
        ]
    }

    workflow_file = tmp_path / "no_meta.json"
    workflow_file.write_text(json.dumps(workflow))

    scanner = WorkflowScanner(tmp_path)
    result = scanner.scan_workflow(workflow_file)

    assert result["name"] == "no_meta"  # Uses filename as fallback
    assert result["description"] == ""
    assert result["category"] == "general"  # Default category


def test_scan_workflow_infers_category_from_path(tmp_path):
    """Test that scanner infers category from subdirectory."""
    workflow = {
        "nodes": [{"type": "KSampler", "inputs": {}}]
    }

    # Create workflow in a subdirectory
    video_dir = tmp_path / "video"
    video_dir.mkdir()
    workflow_file = video_dir / "my_video.json"
    workflow_file.write_text(json.dumps(workflow))

    scanner = WorkflowScanner(tmp_path)
    result = scanner.scan_workflow(workflow_file)

    assert result["category"] == "video"
    assert result["path"] == "video/my_video.json"


def test_scan_workflow_extracts_required_models(tmp_path):
    """Test that scanner extracts model filenames from workflow."""
    workflow = {
        "nodes": [
            {
                "type": "CheckpointLoader",
                "inputs": {
                    "ckpt_name": "model.safetensors"
                }
            },
            {
                "type": "LoraLoader",
                "inputs": {
                    "lora_name": "lora_v2.pt"
                }
            },
            {
                "type": "VAELoader",
                "inputs": {
                    "vae_name": "custom_vae.bin"
                }
            }
        ]
    }

    workflow_file = tmp_path / "models_test.json"
    workflow_file.write_text(json.dumps(workflow))

    scanner = WorkflowScanner(tmp_path)
    result = scanner.scan_workflow(workflow_file)

    assert "model.safetensors" in result["required_models"]
    assert "lora_v2.pt" in result["required_models"]
    assert "custom_vae.bin" in result["required_models"]


def test_scan_all_workflows(tmp_path):
    """Test scanning multiple workflow files."""
    workflow1 = {
        "_meta": {"name": "Workflow 1"},
        "nodes": [{"type": "KSampler", "inputs": {}}]
    }
    workflow2 = {
        "_meta": {"name": "Workflow 2"},
        "nodes": [{"type": "SaveImage", "inputs": {}}]
    }

    (tmp_path / "workflow1.json").write_text(json.dumps(workflow1))
    (tmp_path / "workflow2.json").write_text(json.dumps(workflow2))

    # Create a subdirectory with another workflow
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "workflow3.json").write_text(json.dumps(workflow1))

    scanner = WorkflowScanner(tmp_path)
    results = scanner.scan_all()

    assert len(results) == 3
    names = [r["name"] for r in results]
    assert "Workflow 1" in names
    assert "Workflow 2" in names


def test_scan_all_handles_nonexistent_directory(tmp_path):
    """Test that scan_all handles non-existent directory gracefully."""
    nonexistent = tmp_path / "nonexistent"
    scanner = WorkflowScanner(nonexistent)
    results = scanner.scan_all()

    assert results == []


def test_scan_all_handles_invalid_json(tmp_path):
    """Test that scan_all skips invalid JSON files."""
    valid_workflow = {
        "_meta": {"name": "Valid"},
        "nodes": []
    }

    (tmp_path / "valid.json").write_text(json.dumps(valid_workflow))
    (tmp_path / "invalid.json").write_text("not valid json")

    scanner = WorkflowScanner(tmp_path)
    results = scanner.scan_all()

    # Should only return the valid workflow
    assert len(results) == 1
    assert results[0]["name"] == "Valid"


def test_scan_comfyui_workflows_finds_workflows():
    """Test that scan_comfyui_workflows finds workflows in ComfyUI user directory."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir) / "workflows"
        comfyui_path = Path(tmpdir) / "ComfyUI" / "user" / "default" / "workflows"
        comfyui_path.mkdir(parents=True)

        # Create a test workflow
        workflow = {
            "1": {"class_type": "KSampler", "inputs": {}},
            "_meta": {"name": "Test ComfyUI Workflow", "description": "From ComfyUI"}
        }
        with open(comfyui_path / "test_workflow.json", "w") as f:
            json.dump(workflow, f)

        scanner = WorkflowScanner(base_path)
        scanner._comfyui_user_path = Path(tmpdir) / "ComfyUI" / "user"

        comfyui_workflows = scanner.scan_comfyui_workflows()

        assert len(comfyui_workflows) == 1
        assert comfyui_workflows[0]["id"] == "test_workflow"
        assert comfyui_workflows[0]["name"] == "Test ComfyUI Workflow"
        assert comfyui_workflows[0]["source"] == "comfyui"


def test_scan_all_includes_comfyui_workflows():
    """Test that scan_all includes workflows from all three sources."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir) / "workflows"
        base_path.mkdir(parents=True)

        # Create user workflow
        user_workflow = {"1": {"class_type": "KSampler"}, "_meta": {"name": "User WF"}}
        with open(base_path / "user_wf.json", "w") as f:
            json.dump(user_workflow, f)

        # Create ComfyUI workflow
        comfyui_path = Path(tmpdir) / "ComfyUI" / "user" / "default" / "workflows"
        comfyui_path.mkdir(parents=True)
        comfyui_workflow = {"1": {"class_type": "KSampler"}, "_meta": {"name": "ComfyUI WF"}}
        with open(comfyui_path / "comfyui_wf.json", "w") as f:
            json.dump(comfyui_workflow, f)

        scanner = WorkflowScanner(base_path)
        scanner._comfyui_user_path = Path(tmpdir) / "ComfyUI" / "user"

        all_workflows = scanner.scan_all()

        # Should have 2 workflows (user + comfyui), no library without registry
        assert len(all_workflows) == 2
        sources = {wf["source"] for wf in all_workflows}
        assert "user" in sources
        assert "comfyui" in sources


def test_scan_all_deduplicates_preferring_comfyui():
    """Test that scan_all deduplicates workflows, preferring ComfyUI version."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir) / "workflows"
        base_path.mkdir(parents=True)

        # Create user workflow with same id as ComfyUI workflow
        user_workflow = {"1": {"class_type": "KSampler"}, "_meta": {"name": "User Version"}}
        with open(base_path / "duplicate.json", "w") as f:
            json.dump(user_workflow, f)

        # Create ComfyUI workflow with same id
        comfyui_path = Path(tmpdir) / "ComfyUI" / "user" / "default" / "workflows"
        comfyui_path.mkdir(parents=True)
        comfyui_workflow = {"1": {"class_type": "KSampler"}, "_meta": {"name": "ComfyUI Version"}}
        with open(comfyui_path / "duplicate.json", "w") as f:
            json.dump(comfyui_workflow, f)

        scanner = WorkflowScanner(base_path)
        scanner._comfyui_user_path = Path(tmpdir) / "ComfyUI" / "user"

        all_workflows = scanner.scan_all()

        # Should have 1 workflow (deduplicated)
        assert len(all_workflows) == 1
        # Should prefer ComfyUI version
        assert all_workflows[0]["source"] == "comfyui"
        assert all_workflows[0]["name"] == "ComfyUI Version"
