"""
Core workflow management logic
"""
import os
import json
import shutil
import logging
import random
import copy
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from .config import config

logger = logging.getLogger(__name__)


class WorkflowManager:
    """Manages ComfyUI workflow templates"""

    def __init__(self):
        self.workflows: Dict[str, Dict[str, Any]] = {}
        config.ensure_directories()
        self.load_workflows()

    def load_workflows(self):
        """Load all workflow JSON files from workflows folder"""
        workflows_path = Path(config.WORKFLOWS_FOLDER)
        workflows_path.mkdir(exist_ok=True, parents=True)

        self.workflows = {}

        for json_file in workflows_path.glob('*.json'):
            try:
                workflow_data = self._load_workflow_file(json_file)

                workflow_id = json_file.stem
                workflow_name = workflow_id.replace('_', ' ').replace('-', ' ').title()

                self.workflows[workflow_id] = {
                    'id': workflow_id,
                    'name': workflow_name,
                    'workflow': workflow_data,
                    'description': self._extract_description(workflow_data),
                    'filename': json_file.name,
                    'modified': datetime.fromtimestamp(json_file.stat().st_mtime).isoformat()
                }
                logger.info(f"Loaded workflow: {workflow_name}")

            except Exception as e:
                logger.error(f"Failed to load {json_file}: {e}")

        logger.info(f"Total workflows loaded: {len(self.workflows)}")

    def _load_workflow_file(self, filepath: Path) -> Dict[str, Any]:
        """Load and validate a workflow file"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Validate it's API format (dict with node IDs as keys)
        if not isinstance(data, dict):
            raise ValueError("Workflow must be a JSON object")

        # Check it's not full UI format (has 'nodes' and 'links')
        if 'nodes' in data and 'links' in data:
            raise ValueError(
                "Workflow appears to be in full ComfyUI format, not API format. "
                "Please export using 'Save (API Format)' in ComfyUI."
            )

        return data

    def _extract_description(self, workflow: Dict[str, Any]) -> str:
        """Extract description from workflow metadata"""
        if '_meta' in workflow:
            return workflow['_meta'].get('description', '')

        # Try to find description from class types
        class_types = set()
        for node_id, node in workflow.items():
            if not node_id.startswith('_'):
                class_types.add(node.get('class_type', ''))

        if 'KSampler' in class_types:
            return "Image generation workflow"
        elif 'VAEDecode' in class_types:
            return "Image processing workflow"

        return "ComfyUI workflow"

    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific workflow by ID"""
        return self.workflows.get(workflow_id)

    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all available workflows"""
        return [
            {
                'id': wf['id'],
                'name': wf['name'],
                'description': wf['description'],
                'filename': wf['filename'],
                'modified': wf['modified']
            }
            for wf in self.workflows.values()
        ]

    def analyze_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze workflow and extract user-configurable inputs"""
        inputs = {}

        for node_id, node in workflow.items():
            if node_id.startswith('_'):
                continue

            class_type = node.get('class_type', '')
            node_inputs = node.get('inputs', {})
            meta = node.get('_meta', {})
            title = meta.get('title', class_type)

            # LoadImage nodes
            if class_type == 'LoadImage':
                inputs[f"image_{node_id}"] = {
                    'type': 'image',
                    'node_id': node_id,
                    'title': title,
                    'required': True
                }

            # Text prompt nodes
            elif class_type in ('CLIPTextEncode', 'TextEncode'):
                current_text = node_inputs.get('text', '')
                is_negative = any(
                    word in title.lower()
                    for word in ['negative', 'neg']
                ) or any(
                    word in current_text.lower()
                    for word in ['bad', 'worst', 'low quality']
                )

                inputs[f"text_{node_id}"] = {
                    'type': 'text',
                    'node_id': node_id,
                    'title': title,
                    'value': current_text,
                    'multiline': True,
                    'prompt_type': 'negative' if is_negative else 'positive',
                    'required': True
                }

            # KSampler settings
            elif class_type == 'KSampler':
                inputs[f"seed_{node_id}"] = {
                    'type': 'number',
                    'node_id': node_id,
                    'title': f"{title} - Seed",
                    'value': node_inputs.get('seed', -1),
                    'min': -1,
                    'max': 2147483647,
                    'required': False
                }

                inputs[f"steps_{node_id}"] = {
                    'type': 'number',
                    'node_id': node_id,
                    'title': f"{title} - Steps",
                    'value': node_inputs.get('steps', 20),
                    'min': 1,
                    'max': 150,
                    'required': False
                }

                inputs[f"cfg_{node_id}"] = {
                    'type': 'number',
                    'node_id': node_id,
                    'title': f"{title} - CFG Scale",
                    'value': node_inputs.get('cfg', 7),
                    'min': 1,
                    'max': 30,
                    'step': 0.5,
                    'required': False
                }

            # Empty Latent Image (dimensions)
            elif class_type == 'EmptyLatentImage':
                inputs[f"width_{node_id}"] = {
                    'type': 'number',
                    'node_id': node_id,
                    'title': f"{title} - Width",
                    'value': node_inputs.get('width', 512),
                    'min': 64,
                    'max': 2048,
                    'step': 64,
                    'required': False
                }

                inputs[f"height_{node_id}"] = {
                    'type': 'number',
                    'node_id': node_id,
                    'title': f"{title} - Height",
                    'value': node_inputs.get('height', 512),
                    'min': 64,
                    'max': 2048,
                    'step': 64,
                    'required': False
                }

        return inputs

    def apply_inputs(
        self,
        workflow: Dict[str, Any],
        user_inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply user inputs to workflow"""
        workflow_copy = copy.deepcopy(workflow)
        logger.info(f"Applying {len(user_inputs)} user inputs to workflow")

        for input_id, value in user_inputs.items():
            parts = input_id.split('_', 1)
            if len(parts) != 2:
                continue

            input_type, node_id = parts
            if node_id not in workflow_copy:
                continue

            node = workflow_copy[node_id]

            if input_type == 'image':
                node['inputs']['image'] = value
                logger.info(f"Set image for node {node_id}")

            elif input_type == 'text':
                node['inputs']['text'] = value
                logger.info(f"Set text for node {node_id}")

            elif input_type == 'seed':
                try:
                    seed_value = int(value)
                    if seed_value == -1:
                        seed_value = random.randint(0, 2147483647)
                    elif seed_value < -1 or seed_value > 2147483647:
                        seed_value = max(-1, min(2147483647, seed_value))
                    node['inputs']['seed'] = seed_value
                except (ValueError, TypeError):
                    # Invalid input, use random seed
                    node['inputs']['seed'] = random.randint(0, 2147483647)

            elif input_type == 'steps':
                try:
                    steps_value = int(value)
                    node['inputs']['steps'] = max(1, min(150, steps_value))
                except (ValueError, TypeError):
                    node['inputs']['steps'] = 20  # Default

            elif input_type == 'cfg':
                try:
                    cfg_value = float(value)
                    node['inputs']['cfg'] = max(1.0, min(30.0, cfg_value))
                except (ValueError, TypeError):
                    node['inputs']['cfg'] = 7.0  # Default

            elif input_type == 'width':
                try:
                    width_value = int(value)
                    # Round to nearest 64
                    width_value = (width_value // 64) * 64
                    node['inputs']['width'] = max(64, min(2048, width_value))
                except (ValueError, TypeError):
                    node['inputs']['width'] = 512  # Default

            elif input_type == 'height':
                try:
                    height_value = int(value)
                    # Round to nearest 64
                    height_value = (height_value // 64) * 64
                    node['inputs']['height'] = max(64, min(2048, height_value))
                except (ValueError, TypeError):
                    node['inputs']['height'] = 512  # Default

        return workflow_copy

    def sync_from_comfyui(self) -> Dict[str, Any]:
        """Sync workflows from ComfyUI's saved workflows"""
        comfyui_path = Path(config.COMFYUI_WORKFLOWS_FOLDER)
        studio_path = Path(config.WORKFLOWS_FOLDER)

        if not comfyui_path.exists():
            return {
                'success': False,
                'message': 'ComfyUI workflows folder not found',
                'synced': 0
            }

        synced = 0
        errors = []

        for workflow_file in comfyui_path.glob('*.json'):
            try:
                # Validate workflow format
                workflow_data = self._load_workflow_file(workflow_file)

                target_path = studio_path / workflow_file.name

                # Check if file exists and content differs
                if target_path.exists():
                    with open(target_path, 'r') as f:
                        existing_data = json.load(f)

                    if existing_data == workflow_data:
                        continue  # Same content, skip

                    # Create versioned backup
                    self._create_version(target_path)

                # Copy workflow
                shutil.copy2(workflow_file, target_path)
                synced += 1
                logger.info(f"Synced workflow: {workflow_file.name}")

            except Exception as e:
                errors.append(f"{workflow_file.name}: {str(e)}")
                logger.error(f"Failed to sync {workflow_file}: {e}")

        # Reload workflows
        self.load_workflows()

        return {
            'success': True,
            'synced': synced,
            'errors': errors,
            'message': f"Synced {synced} workflows"
        }

    def _create_version(self, filepath: Path):
        """Create a versioned backup of a workflow"""
        base = filepath.stem
        ext = filepath.suffix
        parent = filepath.parent

        # Find next version number
        version = 1
        while True:
            version_path = parent / f"{base}_{version:03d}{ext}"
            if not version_path.exists():
                break
            version += 1

        # Rename existing file to version
        shutil.move(str(filepath), str(version_path))
        logger.info(f"Created version: {version_path.name}")

    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow file"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return False

        filepath = Path(config.WORKFLOWS_FOLDER) / workflow['filename']
        if filepath.exists():
            filepath.unlink()
            del self.workflows[workflow_id]
            logger.info(f"Deleted workflow: {workflow_id}")
            return True

        return False

    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage information for workflows folder"""
        workflows_path = Path(config.WORKFLOWS_FOLDER)

        total_size = 0
        file_count = 0

        for f in workflows_path.glob('*.json'):
            total_size += f.stat().st_size
            file_count += 1

        return {
            'workflows_folder': str(workflows_path),
            'total_workflows': file_count,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        }
