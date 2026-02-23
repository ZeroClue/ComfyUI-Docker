"""
Workflow Scanner Service
Scans workflow JSON files and extracts metadata for the Generate page.
Supports both user workflows (filesystem) and library workflows (registry).
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
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
        self._registry_path = Path("/workspace/data/registry.json")
        self._models_path = self.base_path.parent / "models"
        self._comfyui_user_path = Path("/workspace/ComfyUI/user")
        # Model index for preset suggestions
        self._model_index_path = Path("/workspace/data/model_index.json")
        self._model_index: Dict[str, str] = {}
        self._load_model_index()

    def _load_model_index(self) -> None:
        """Load model filename to preset_id mapping from cache."""
        if self._model_index_path.exists():
            try:
                with open(self._model_index_path, 'r') as f:
                    data = json.load(f)
                    self._model_index = data.get("mappings", {})
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Failed to load model index: {e}")
                self._model_index = {}

    def resolve_model_to_preset(self, model_filename: str) -> Optional[Dict[str, Any]]:
        """
        Find which preset provides a given model file.

        Args:
            model_filename: The model filename (e.g., "flux-dev.safetensors")

        Returns:
            Dict with preset_id, preset_name, model_file, installed status, or None if not found.
        """
        # Try exact path match first (checkpoints/filename.safetensors)
        for model_dir in self.MODEL_DIRECTORIES:
            path_key = f"{model_dir}/{model_filename}"
            if path_key in self._model_index:
                preset_id = self._model_index[path_key]
                return self._build_preset_info(preset_id, model_filename)

        # Fallback: filename-only match
        for path_key, preset_id in self._model_index.items():
            if Path(path_key).name == model_filename:
                return self._build_preset_info(preset_id, model_filename)

        return None

    def _build_preset_info(self, preset_id: str, model_file: str) -> Dict[str, Any]:
        """Build preset info dict with installation status."""
        # Get preset details from registry if available
        preset_info = self._get_preset_from_registry(preset_id)

        # Check if the model file is installed
        installed = self._check_model_installed(model_file)

        return {
            "preset_id": preset_id,
            "preset_name": preset_info.get("name", preset_id) if preset_info else preset_id,
            "model_file": model_file,
            "installed": installed,
            "download_size": preset_info.get("download_size") if preset_info else None,
        }

    def _get_preset_from_registry(self, preset_id: str) -> Optional[Dict]:
        """Get preset info from cached registry."""
        if not self._registry_path.exists():
            return None
        try:
            with open(self._registry_path, 'r') as f:
                registry = json.load(f)
                return registry.get("presets", {}).get(preset_id)
        except (json.JSONDecodeError, IOError):
            return None

    def _check_model_installed(self, model_filename: str) -> bool:
        """Check if a model file exists in any model directory."""
        for model_dir in self.MODEL_DIRECTORIES:
            model_path = self._models_path / model_dir / model_filename
            if model_path.exists():
                return True
        return False

    def scan_comfyui_workflows(self) -> List[Dict[str, Any]]:
        """
        Scan workflows from ComfyUI's user directory.
        Handles both single-user (default) and multi-user configurations.
        """
        workflows = []

        if not self._comfyui_user_path.exists():
            return workflows

        # Scan all user directories (handles multi-user mode)
        for user_dir in self._comfyui_user_path.iterdir():
            if not user_dir.is_dir():
                continue

            workflows_dir = user_dir / "workflows"
            if not workflows_dir.exists():
                continue

            for workflow_file in workflows_dir.rglob("*.json"):
                try:
                    metadata = self.scan_workflow(workflow_file)
                    metadata["source"] = "comfyui"
                    workflows.append(metadata)
                except Exception as e:
                    print(f"Warning: Failed to scan ComfyUI workflow {workflow_file}: {e}")
                    continue

        return workflows

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

        # Resolve models to presets
        suggested_presets = []
        unmapped_models = []
        seen_presets = set()

        for model_file in required_models:
            preset_info = self.resolve_model_to_preset(model_file)
            if preset_info:
                preset_id = preset_info["preset_id"]
                if preset_id not in seen_presets:
                    seen_presets.add(preset_id)
                    suggested_presets.append(preset_info)
            else:
                unmapped_models.append(model_file)

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
            "source": "user",  # Mark as user workflow from filesystem
            # Preset suggestion fields
            "suggested_presets": suggested_presets,
            "unmapped_models": unmapped_models,
        }

    def scan_all(self) -> List[Dict[str, Any]]:
        """Scan all workflows - library (registry), comfyui, and user (filesystem)."""
        workflows = []

        # First, scan library workflows from registry
        library_workflows = self.scan_library_workflows()
        workflows.extend(library_workflows)

        # Then, scan ComfyUI user workflows
        comfyui_workflows = self.scan_comfyui_workflows()
        workflows.extend(comfyui_workflows)

        # Finally, scan user workflows from filesystem
        user_workflows = self.scan_user_workflows()
        workflows.extend(user_workflows)

        # De-duplicate by id (prefer comfyui over user for same id)
        seen_ids = {}
        for wf in workflows:
            wf_id = wf.get("id")
            if wf_id not in seen_ids:
                seen_ids[wf_id] = wf
            elif wf.get("source") == "comfyui":
                # Prefer comfyui version over user version
                seen_ids[wf_id] = wf

        return list(seen_ids.values())

    def scan_user_workflows(self) -> List[Dict[str, Any]]:
        """Scan user workflow files from the filesystem."""
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

    def scan_library_workflows(self) -> List[Dict[str, Any]]:
        """
        Scan workflows from the registry.json file.
        Returns workflows with source='library' and preset-based model checking.
        """
        workflows = []

        if not self._registry_path.exists():
            return workflows

        try:
            with open(self._registry_path, 'r') as f:
                registry = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load registry: {e}")
            return workflows

        workflows_data = registry.get("workflows", {})
        presets_data = registry.get("presets", {})
        installed_presets = self._get_installed_presets(presets_data)

        for wf_id, wf_data in workflows_data.items():
            required_presets = wf_data.get("required_presets", [])
            preset_statuses = []

            for preset_id in required_presets:
                preset_info = presets_data.get(preset_id, {})
                preset_statuses.append({
                    "id": preset_id,
                    "name": preset_info.get("name", preset_id),
                    "installed": preset_id in installed_presets,
                    "download_size": preset_info.get("download_size"),
                })

            # Calculate ready status based on preset availability
            ready = all(ps["installed"] for ps in preset_statuses) if preset_statuses else True
            installed_count = sum(1 for ps in preset_statuses if ps["installed"])
            missing_count = len(preset_statuses) - installed_count

            workflows.append({
                "id": wf_id,
                "name": wf_data.get("name", wf_id),
                "description": wf_data.get("description", ""),
                "category": wf_data.get("category", "General"),
                "path": None,  # Library workflows don't have local paths
                "node_count": 0,  # Not available from registry metadata
                "input_types": wf_data.get("input_types", []),
                "output_types": wf_data.get("output_types", []),
                "required_presets": required_presets,  # Preset IDs for library workflows
                "models": preset_statuses,  # For UI compatibility
                "model_status": {
                    "total": len(preset_statuses),
                    "installed": installed_count,
                    "missing": missing_count,
                },
                "ready": ready,
                "source": "library",
                "type": wf_data.get("type", "image"),
                "tags": wf_data.get("tags", []),
                "author": wf_data.get("author", "Unknown"),
                "version": wf_data.get("version", "1.0.0"),
            })

        return workflows

    def _get_installed_presets(self, presets_data: Dict[str, Any]) -> Set[str]:
        """
        Check which presets are installed by verifying all files exist.
        Returns a set of installed preset IDs.
        """
        installed = set()

        for preset_id, preset_data in presets_data.items():
            files = preset_data.get("files", [])

            # If no files defined, skip this preset
            if not files:
                continue

            all_installed = True
            for file_info in files:
                file_path = file_info.get("path", "")
                full_path = self._models_path / file_path
                if not full_path.exists():
                    all_installed = False
                    break

            if all_installed:
                installed.add(preset_id)

        return installed

    def _infer_category(self, workflow_path: Path) -> str:
        """Infer category from path structure."""
        # Handle paths outside base_path (e.g., ComfyUI workflows)
        if not workflow_path.is_relative_to(self.base_path):
            # Try to infer from ComfyUI user directory structure
            if self._comfyui_user_path and workflow_path.is_relative_to(self._comfyui_user_path):
                # Extract user/workflows/category structure
                parts = workflow_path.relative_to(self._comfyui_user_path).parts
                # parts might be: ["default", "workflows", "category", "workflow.json"]
                if len(parts) > 2:
                    return parts[2]  # Return category after user/workflows
            return "comfyui"  # Default for ComfyUI workflows

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

        # Skip MarkdownNote nodes - their content contains model URLs as text
        node_type = node.get("type", "")
        if node_type == "MarkdownNote":
            return models

        if not isinstance(widgets_values, list):
            return models

        for value in widgets_values:
            # Only extract short strings that look like filenames (< 100 chars, no newlines)
            if (isinstance(value, str) and
                len(value) < 100 and
                "\n" not in value and
                any(ext in value.lower() for ext in [".safetensors", ".pt", ".pth", ".bin", ".ckpt"])):
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
