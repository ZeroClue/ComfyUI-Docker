"""
Template scanner for model compatibility checking
Scans ComfyUI workflow templates for required models
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Optional
from dataclasses import dataclass


@dataclass
class ModelReference:
    """Reference to a model found in a template"""
    path: str
    node_type: str
    input_name: str


class TemplateScanner:
    """Scans ComfyUI templates for model references"""

    # Common model input field patterns
    MODEL_PATTERNS = {
        'checkpoints': ['ckpt_name', 'checkpoint', 'model_path'],
        'text_encoders': ['clip_name', 'text_encoder', 't5_name'],
        'vae': ['vae_name', 'vae'],
        'loras': ['lora_name', 'lora'],
        'controlnet': ['controlnet_name', 'control_net'],
        'clip_vision': ['clip_vision_name', 'clip_vision'],
        'upscale_models': ['upscale_model_name', 'model_name'],
        'ipadapters': ['ipadapter_file', 'adapter_name'],
    }

    def __init__(self, model_base_path: str = "/workspace/models"):
        self.model_base_path = Path(model_base_path)

    def scan_template(self, template_path: Path) -> List[ModelReference]:
        """Scan a single template file for model references"""
        references = []

        try:
            with open(template_path, 'r') as f:
                template = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return references

        # Handle both workflow format and node format
        nodes = template if isinstance(template, dict) and 'nodes' not in template else template.get('nodes', {})

        for node_id, node_data in self._iter_nodes(nodes):
            class_type = node_data.get('class_type', '')
            inputs = node_data.get('inputs', {})

            for input_name, input_value in inputs.items():
                if isinstance(input_value, str):
                    # Check if this input matches a model pattern
                    model_type = self._get_model_type(input_name, class_type)
                    if model_type:
                        references.append(ModelReference(
                            path=f"{model_type}/{input_value}",
                            node_type=class_type,
                            input_name=input_name
                        ))

        return references

    def _iter_nodes(self, nodes):
        """Iterate over nodes in either format"""
        if isinstance(nodes, list):
            for i, node in enumerate(nodes):
                yield str(i), node
        elif isinstance(nodes, dict):
            yield from nodes.items()

    def _get_model_type(self, input_name: str, class_type: str) -> Optional[str]:
        """Determine model type from input name and class type"""
        input_lower = input_name.lower()

        for model_type, patterns in self.MODEL_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in input_lower:
                    return model_type

        return None

    def check_installed(self, references: List[ModelReference]) -> Dict[str, bool]:
        """Check which model references are installed"""
        installed = {}

        for ref in references:
            full_path = self.model_base_path / ref.path
            installed[ref.path] = full_path.exists()

        return installed

    def get_missing_models(self, template_path: Path) -> List[Dict]:
        """Get list of missing models for a template"""
        references = self.scan_template(template_path)
        installed = self.check_installed(references)

        missing = []
        for ref in references:
            if not installed.get(ref.path, False):
                missing.append({
                    "path": ref.path,
                    "node_type": ref.node_type,
                    "input_name": ref.input_name
                })

        return missing
