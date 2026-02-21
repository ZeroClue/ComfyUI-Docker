"""
Workflow Scanner Service
Scans workflow JSON files and extracts metadata for the Generate page.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class WorkflowMetadata:
    """Metadata extracted from a workflow file."""
    id: str
    name: str
    description: str
    category: str
    path: str
    node_count: int
    input_types: List[str]
    output_types: List[str]
    required_models: List[str]


class WorkflowScanner:
    """Scans workflow files and extracts metadata."""

    # Model directories to search (in order)
    MODEL_DIRECTORIES = [
        "checkpoints",
        "diffusion_models",
        "text_encoders",
        "vae",
        "loras",
        "clip_vision",
        "controlnet",
        "upscale_models",
    ]

    # Node types that indicate input type
    INPUT_NODES = {
        "CLIPTextEncode": "text",
        "LoadImage": "image",
        "LoadAudio": "audio",
        "VHS_LoadVideo": "video",
    }

    # Node types that indicate output type
    OUTPUT_NODES = {
        "SaveImage": "image",
        "VHS_SaveVideo": "video",
        "SaveAudio": "audio",
    }

    # Model type inference patterns
    MODEL_TYPE_PATTERNS = {
        "diffusion_models": ["flux", "unet", "diffusion", "_turbo", "sdxl", "sd15"],
        "text_encoders": ["clip", "t5", "qwen", "llama", "text_encoder"],
        "vae": ["vae", "ae.safetensors"],
        "loras": ["lora"],
        "checkpoints": ["checkpoint", "inpaint", "dreamshaper"],
    }

    def __init__(self, workflow_base_path: Path):
        self.base_path = Path(workflow_base_path)

    def scan_workflow(self, workflow_path: Path) -> Dict[str, Any]:
        """Scan a single workflow file and extract metadata."""
        with open(workflow_path, 'r') as f:
            data = json.load(f)

        # Handle both API format and UI format
        if "nodes" in data:
            # UI format
            nodes = data.get("nodes", [])
            meta = data.get("_meta", {})
            node_count = len(nodes)

            # Scan for input/output types
            input_types = set()
            output_types = set()

            for node in nodes:
                node_type = node.get("type", "")
                if node_type in self.INPUT_NODES:
                    input_types.add(self.INPUT_NODES[node_type])
                if node_type in self.OUTPUT_NODES:
                    output_types.add(self.OUTPUT_NODES[node_type])
        else:
            # API format (dict of nodes)
            nodes = data
            meta = data.get("_meta", {})
            node_count = len([k for k in nodes.keys() if not k.startswith("_")])
            input_types = set()
            output_types = set()

            for node_id, node_data in nodes.items():
                if node_id.startswith("_"):
                    continue
                class_type = node_data.get("class_type", "")
                if class_type in self.INPUT_NODES:
                    input_types.add(self.INPUT_NODES[class_type])
                if class_type in self.OUTPUT_NODES:
                    output_types.add(self.OUTPUT_NODES[class_type])

        # Extract required models from workflow
        required_models = self._extract_required_models(data)

        # Check model availability
        models = self.check_workflow_models(required_models)

        # Calculate model status
        installed_count = sum(1 for m in models if m["installed"])
        missing_count = len(models) - installed_count

        return {
            "id": workflow_path.stem,
            "name": meta.get("name", workflow_path.stem),
            "description": meta.get("description", ""),
            "category": meta.get("category", self._infer_category(workflow_path)),
            "path": str(workflow_path.relative_to(self.base_path)) if workflow_path.is_relative_to(self.base_path) else str(workflow_path),
            "node_count": node_count,
            "input_types": list(input_types),
            "output_types": list(output_types),
            "required_models": required_models,
            # Model availability fields
            "models": models,
            "model_status": {
                "total": len(models),
                "installed": installed_count,
                "missing": missing_count,
            },
            "ready": missing_count == 0 if models else True,  # Ready if no models or all installed
        }

    def scan_all(self) -> List[Dict[str, Any]]:
        """Scan all workflow files in the base path."""
        workflows = []

        if not self.base_path.exists():
            return workflows

        for workflow_file in self.base_path.rglob("*.json"):
            try:
                metadata = self.scan_workflow(workflow_file)
                workflows.append(metadata)
            except Exception as e:
                print(f"Warning: Failed to scan {workflow_file}: {e}")
                continue

        return workflows

    def _infer_category(self, workflow_path: Path) -> str:
        """Infer category from path structure."""
        parts = workflow_path.relative_to(self.base_path).parts
        if len(parts) > 1:
            return parts[0]
        return "general"

    def _infer_model_type(self, filename: str) -> str:
        """Infer model type from filename patterns."""
        filename_lower = filename.lower()

        for model_type, patterns in self.MODEL_TYPE_PATTERNS.items():
            for pattern in patterns:
                if pattern in filename_lower:
                    return model_type

        # Default to checkpoints for unknown models
        return "checkpoints"

    def _extract_models_from_widgets(self, node: Dict) -> List[str]:
        """Extract model filenames from widgets_values array."""
        models = []
        widgets_values = node.get("widgets_values", [])

        if not isinstance(widgets_values, list):
            return models

        for value in widgets_values:
            if isinstance(value, str) and any(
                ext in value.lower()
                for ext in [".safetensors", ".pt", ".pth", ".bin", ".ckpt"]
            ):
                models.append(value)

        return models

    def _extract_required_models(self, data: Dict) -> List[str]:
        """Extract required model filenames from workflow."""
        models = []

        # Handle both UI and API formats
        nodes = data.get("nodes", data) if "nodes" in data else data

        for node_data in (nodes.values() if isinstance(nodes, dict) else nodes):
            if isinstance(node_data, dict):
                inputs = node_data.get("inputs", {})
                # Handle both dict (API format) and list (UI format) for inputs
                if isinstance(inputs, dict):
                    for key, value in inputs.items():
                        if isinstance(value, str) and any(
                            ext in value.lower()
                            for ext in [".safetensors", ".pt", ".pth", ".bin", ".ckpt"]
                        ):
                            models.append(value)
                elif isinstance(inputs, list):
                    for input_item in inputs:
                        if isinstance(input_item, dict):
                            value = input_item.get("value", "")
                            if isinstance(value, str) and any(
                                ext in value.lower()
                                for ext in [".safetensors", ".pt", ".pth", ".bin", ".ckpt"]
                            ):
                                models.append(value)

                # Also check widgets_values for packed/composite nodes
                models.extend(self._extract_models_from_widgets(node_data))

        return list(set(models))

    def check_model_availability(self, model_filename: str) -> Dict[str, Any]:
        """Check if a model is installed and return its info."""
        for model_type in self.MODEL_DIRECTORIES:
            path = self.base_path.parent / "models" / model_type / model_filename
            if path.exists():
                return {
                    "name": model_filename,
                    "installed": True,
                    "type": model_type,
                    "path": str(path),
                }

        # Not found - infer type from filename
        inferred_type = self._infer_model_type(model_filename)
        return {
            "name": model_filename,
            "installed": False,
            "type": inferred_type,
            "path": None,
        }

    def check_workflow_models(self, required_models: List[str]) -> List[Dict[str, Any]]:
        """Check availability for all required models."""
        return [self.check_model_availability(model) for model in required_models]


__all__ = ["WorkflowScanner", "WorkflowMetadata"]
