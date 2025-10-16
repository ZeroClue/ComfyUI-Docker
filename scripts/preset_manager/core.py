"""
Core functionality for the ComfyUI Preset Manager
Contains the ModelManager class and related business logic
"""

import os
import subprocess
import threading
import time
import glob
import re
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .config import README_BASE_PATH, MODEL_PATHS, DEFAULT_CATEGORIES


class ModelManager:
    """Manages ComfyUI models and presets with full CRUD operations"""

    def __init__(self):
        self.base_dir = "/workspace/ComfyUI/models"
        self.readme_base_path = README_BASE_PATH
        self.presets = {}
        self.categories = {}
        self._initialize_directories()
        self._parse_all_presets()
        self._scan_installed_models()

    def _initialize_directories(self):
        """Ensure required directories exist"""
        os.makedirs(self.base_dir, exist_ok=True)
        for directory in MODEL_PATHS.values():
            os.makedirs(directory, exist_ok=True)

    def _parse_all_presets(self):
        """Parse all preset categories and their file mappings from YAML configuration"""
        try:
            # Path to local presets configuration
            presets_path = Path("/workspace/config/presets.yaml")

            # Fallback to hardcoded presets if YAML not available
            if not presets_path.exists():
                print(f"[WARNING] Presets YAML not found at {presets_path}, using fallback configuration")
                self._load_fallback_presets()
                return

            # Load YAML configuration
            try:
                with open(presets_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
            except yaml.YAMLError as e:
                print(f"[ERROR] Error parsing presets YAML: {e}")
                self._load_fallback_presets()
                return
            except Exception as e:
                print(f"[ERROR] Error reading presets file: {e}")
                self._load_fallback_presets()
                return

            # Validate configuration structure
            if not all(key in config for key in ['metadata', 'categories', 'presets']):
                print(f"[ERROR] Invalid presets configuration structure")
                self._load_fallback_presets()
                return

            # Extract presets from YAML
            self.presets = {}
            for preset_id, preset_data in config['presets'].items():
                # Convert file objects from YAML to simple file paths
                files = []
                for file_info in preset_data.get('files', []):
                    if isinstance(file_info, dict) and 'path' in file_info:
                        files.append(file_info['path'])
                    elif isinstance(file_info, str):
                        files.append(file_info)

                # Create preset entry in expected format
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

            # Organize by category
            self.categories = {}
            for category_name, category_data in config['categories'].items():
                # Get presets for this category
                category_presets = [p for p in self.presets.values() if p['category'] == category_name]
                self.categories[category_name] = category_presets

            print(f"[INFO] Loaded {len(self.presets)} presets from YAML configuration")

            # Log metadata
            metadata = config.get('metadata', {})
            print(f"[INFO] Presets version: {metadata.get('version', 'unknown')}")
            print(f"[INFO] Last updated: {metadata.get('last_updated', 'unknown')}")

        except Exception as e:
            print(f"[ERROR] Critical error loading presets: {e}")
            self._load_fallback_presets()

    def _load_fallback_presets(self):
        """Load minimal fallback presets for emergency use"""
        print(f"[WARNING] Loading minimal fallback preset configuration")

        self.presets = {
            'FALLBACK_EMPTY': {
                'name': 'Fallback Empty Preset',
                'category': 'Unknown',
                'type': 'unknown',
                'description': 'Fallback preset for emergency use',
                'download_size': 'Unknown',
                'files': [],
                'use_case': 'Emergency fallback',
                'tags': ['fallback']
            }
        }

        self.categories = {
            'Unknown': list(self.presets.values())
        }

    def _scan_installed_models(self):
        """Scan installed models and update preset status"""
        try:
            for preset_id, preset in self.presets.items():
                preset['installed_files'] = []
                preset['missing_files'] = []
                preset['total_size'] = 0
                preset['is_installed'] = True

                for file_path in preset['files']:
                    full_path = os.path.join(self.base_dir, file_path)
                    if os.path.exists(full_path):
                        size = os.path.getsize(full_path)
                        preset['installed_files'].append({
                            'path': file_path,
                            'size': size,
                            'size_mb': round(size / (1024 * 1024), 2)
                        })
                        preset['total_size'] += size
                    else:
                        preset['missing_files'].append(file_path)
                        preset['is_installed'] = False

                preset['is_partial'] = len(preset['installed_files']) > 0 and len(preset['missing_files']) > 0
                preset['total_size_mb'] = round(preset['total_size'] / (1024 * 1024), 2)
                preset['total_size_gb'] = round(preset['total_size'] / (1024 * 1024 * 1024), 2)

        except Exception as e:
            print(f"Error scanning installed models: {e}")

    def get_preset(self, preset_id: str) -> Optional[Dict]:
        """Get preset by ID"""
        return self.presets.get(preset_id)

    def get_preset_id_by_name(self, preset_name: str) -> Optional[str]:
        """Get preset ID by display name"""
        for preset_id, preset_data in self.presets.items():
            if preset_data.get('name') == preset_name:
                return preset_id
        return None

    def get_preset_readme(self, preset_id: str) -> Optional[str]:
        """Get preset README content"""
        readme_path = os.path.join(self.readme_base_path, f'{preset_id}.md')
        if os.path.exists(readme_path):
            with open(readme_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def render_readme(self, readme_content: str) -> str:
        """Render README markdown to HTML"""
        try:
            import markdown
            return markdown.markdown(readme_content)
        except ImportError:
            return f"<pre>{readme_content}</pre>"
        except Exception as e:
            print(f"Error rendering markdown: {e}")
            return f"<pre>{readme_content}</pre>"

    def delete_preset_files(self, preset_id: str) -> Tuple[bool, str]:
        """Delete all files for a preset"""
        try:
            preset = self.get_preset(preset_id)
            if not preset:
                return False, "Preset not found"

            deleted_files = []
            errors = []

            for file_path in preset['installed_files']:
                full_path = os.path.join(self.base_dir, file_path['path'])
                try:
                    if os.path.exists(full_path):
                        os.remove(full_path)
                        deleted_files.append(file_path['path'])
                except Exception as e:
                    errors.append(f"Failed to delete {file_path['path']}: {str(e)}")

            # Update scan after deletion
            self._scan_installed_models()

            if errors:
                return False, f"Some files could not be deleted: {'; '.join(errors)}"
            else:
                return True, f"Successfully deleted {len(deleted_files)} files"

        except Exception as e:
            return False, f"Error deleting preset files: {str(e)}"

    def _is_runpod_environment(self) -> bool:
        """Check if running in RunPod environment"""
        print(f"[DEBUG] Checking for RunPod environment...")

        # Check for RunPod environment variables
        runpod_vars = [key for key in os.environ.keys() if key.startswith('RUNPOD_')]
        print(f"[DEBUG] Found RUNPOD environment variables: {runpod_vars}")
        if runpod_vars:
            print(f"[DEBUG] Detected RunPod environment via environment variables")
            return True

        # Check for RunPod network volume mount
        try:
            # Check if /workspace is a network mount (NFS, etc.)
            result = subprocess.run(['df', '-T', '/workspace'],
                                  capture_output=True, text=True, timeout=10)
            print(f"[DEBUG] df -T /workspace return code: {result.returncode}")
            print(f"[DEBUG] df -T /workspace stdout: {result.stdout}")
            print(f"[DEBUG] df -T /workspace stderr: {result.stderr}")

            if result.returncode == 0:
                output = result.stdout
                # Look for network filesystem types or RunPod-specific mounts
                if any(fs in output for fs in ['nfs', 'cifs', 'fuse', 'runpod']):
                    print(f"[DEBUG] Detected RunPod environment via filesystem type")
                    return True
        except Exception as e:
            print(f"[DEBUG] Exception checking df -T: {e}")

        print(f"[DEBUG] Not detected as RunPod environment")
        return False

    def _get_runpod_storage_info(self) -> Dict:
        """Get storage information focusing on model storage only for RunPod"""
        print(f"[DEBUG] Getting RunPod storage info (models only)...")
        try:
            # Focus on model storage only - get actual size of models directory
            model_size_info = self._get_total_model_size()
            model_directories = self._get_model_directories_info()

            print(f"[DEBUG] Model storage size: {model_size_info}")
            print(f"[DEBUG] Model directories: {model_directories}")

            return {
                'models_used': model_size_info,
                'models_directory': self.base_dir,
                'model_directories': model_directories,
                'total_model_size': model_size_info,
                'runpod_environment': True,
                'display_mode': 'models_only',
                'source': 'models_directory'
            }

        except Exception as e:
            print(f"[DEBUG] Error getting RunPod model storage info: {e}")
            # Fallback to basic model size calculation
            try:
                model_size = self._get_total_model_size()
                return {
                    'models_used': model_size,
                    'models_directory': self.base_dir,
                    'model_directories': self._get_model_directories_info(),
                    'total_model_size': model_size,
                    'runpod_environment': True,
                    'display_mode': 'models_only',
                    'source': 'fallback'
                }
            except Exception as fallback_e:
                print(f"[DEBUG] Fallback also failed: {fallback_e}")
                return {
                    'models_used': {'bytes': 0, 'gb': 0.0},
                    'models_directory': self.base_dir,
                    'model_directories': {},
                    'total_model_size': {'bytes': 0, 'gb': 0.0},
                    'runpod_environment': True,
                    'display_mode': 'models_only',
                    'source': 'error_fallback',
                    'error': str(e)
                }

    def _get_filesystem_storage_info(self) -> Dict:
        """Get storage information focusing on model storage only"""
        print(f"[DEBUG] Getting filesystem storage info (models only) for: {self.base_dir}")
        try:
            # Focus on model storage only - same approach as RunPod
            model_size_info = self._get_total_model_size()
            model_directories = self._get_model_directories_info()

            print(f"[DEBUG] Model storage size: {model_size_info}")
            print(f"[DEBUG] Model directories: {model_directories}")

            return {
                'models_used': model_size_info,
                'models_directory': self.base_dir,
                'model_directories': model_directories,
                'total_model_size': model_size_info,
                'runpod_environment': False,
                'display_mode': 'models_only',
                'source': 'models_directory'
            }
        except Exception as e:
            print(f"[DEBUG] Error getting filesystem model storage info: {e}")
            return {
                'models_used': {'bytes': 0, 'gb': 0.0},
                'models_directory': self.base_dir,
                'model_directories': {},
                'total_model_size': {'bytes': 0, 'gb': 0.0},
                'runpod_environment': False,
                'display_mode': 'models_only',
                'source': 'error_fallback',
                'error': str(e)
            }

    def _get_model_directories_info(self) -> Dict:
        """Get information about model directories"""
        model_dirs = {}
        total_model_size = 0

        for category in MODEL_PATHS.keys():
            category_path = MODEL_PATHS[category]
            if os.path.exists(category_path):
                size = self._get_directory_size(category_path)
                model_dirs[category] = {
                    'size_bytes': size,
                    'size_mb': round(size / (1024 * 1024), 2),
                    'size_gb': round(size / (1024 * 1024 * 1024), 2),
                    'file_count': self._count_files(category_path)
                }
                total_model_size += size

        return model_dirs

    def _get_total_model_size(self) -> Dict:
        """Get total size of all models"""
        model_dirs = self._get_model_directories_info()
        total_model_size = sum(info['size_bytes'] for info in model_dirs.values())

        return {
            'bytes': total_model_size,
            'gb': round(total_model_size / (1024**3), 2)
        }

    def get_storage_info(self) -> Dict:
        """Get comprehensive storage information with RunPod support"""
        print(f"[DEBUG] === GET STORAGE INFO START ===")
        try:
            # Detect if running in RunPod environment
            is_runpod = self._is_runpod_environment()
            print(f"[DEBUG] Is RunPod environment: {is_runpod}")

            if is_runpod:
                result = self._get_runpod_storage_info()
            else:
                result = self._get_filesystem_storage_info()

            print(f"[DEBUG] Final storage result: {result}")
            print(f"[DEBUG] === GET STORAGE INFO END ===")
            return result

        except Exception as e:
            print(f"[DEBUG] Exception in get_storage_info: {e}")
            print(f"Error getting storage info: {e}")
            # Fallback to basic filesystem method
            return self._get_filesystem_storage_info()

    def _get_directory_size(self, path: str) -> int:
        """Get total size of directory"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total_size += os.path.getsize(fp)
        except Exception:
            pass
        return total_size

    def _count_files(self, path: str) -> int:
        """Count files in directory"""
        count = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                count += len(filenames)
        except Exception:
            pass
        return count

    def cleanup_unused_models(self) -> Tuple[bool, str]:
        """Remove models not part of any preset"""
        try:
            # Get all files that are part of presets
            preset_files = set()
            for preset in self.presets.values():
                for file_path in preset['files']:
                    preset_files.add(os.path.join(self.base_dir, file_path))

            # Find and remove files not in any preset
            removed_files = []
            for category in MODEL_PATHS.keys():
                category_path = MODEL_PATHS[category]
                if os.path.exists(category_path):
                    for dirpath, dirnames, filenames in os.walk(category_path):
                        for filename in filenames:
                            file_path = os.path.join(dirpath, filename)
                            if file_path not in preset_files:
                                try:
                                    os.remove(file_path)
                                    removed_files.append(file_path)
                                except Exception as e:
                                    print(f"Failed to remove {file_path}: {e}")

            self._scan_installed_models()
            return True, f"Removed {len(removed_files)} unused files"

        except Exception as e:
            return False, f"Error during cleanup: {str(e)}"

    def _get_unknown_models(self) -> List[Dict]:
        """Get models that are not part of any preset"""
        unknown_models = []

        try:
            # Get all files that are part of presets
            preset_files = set()
            for preset in self.presets.values():
                for file_path in preset['files']:
                    preset_files.add(file_path)

            # Find all model files in the directories
            model_extensions = ('.safetensors', '.pth', '.pt', '.bin', '.ckpt', '.gguf')

            for category in MODEL_PATHS.keys():
                category_path = MODEL_PATHS[category]
                if os.path.exists(category_path):
                    for dirpath, dirnames, filenames in os.walk(category_path):
                        for filename in filenames:
                            if filename.lower().endswith(model_extensions):
                                # Get relative path from base_dir
                                full_path = os.path.join(dirpath, filename)
                                relative_path = os.path.relpath(full_path, self.base_dir)

                                # Skip if this file is part of a preset
                                if relative_path not in preset_files:
                                    try:
                                        size = os.path.getsize(full_path)
                                        unknown_models.append({
                                            'filename': filename,
                                            'relative_path': relative_path,
                                            'full_path': full_path,
                                            'category': category,
                                            'size_bytes': size,
                                            'size_mb': round(size / (1024 * 1024), 2),
                                            'size_gb': round(size / (1024 * 1024 * 1024), 2)
                                        })
                                    except Exception as e:
                                        print(f"Error getting size for {filename}: {e}")

            # Sort by size (largest first)
            unknown_models.sort(key=lambda x: x['size_bytes'], reverse=True)

        except Exception as e:
            print(f"Error getting unknown models: {e}")

        return unknown_models

    def create_github_issue_data(self, model_info: Dict) -> Dict:
        """Create formatted data for GitHub issue creation"""
        try:
            # Determine model type from category and filename
            model_type = self._guess_model_type(model_info)

            # Create issue title
            title = f"Add preset for {model_info['filename']}"

            # Create issue body with template
            body = f"""## Model Information
- **Filename**: `{model_info['filename']}`
- **Category**: {model_info['category']}
- **Size**: {model_info['size_gb']}GB ({model_info['size_mb']:.0f}MB)
- **Type**: {model_type}
- **Path**: `{model_info['relative_path']}`

## Suggested Preset Details
Please add preset information for this model:

- **Preset Name**: [Suggest a descriptive name]
- **Description**: [Describe what this model does]
- **Use Case**: [Primary use case for this model]
- **Download Size**: {model_info['size_gb']}GB
- **Required Files**:
  - `{model_info['relative_path']}`

## Additional Context
- This model was detected in the user's ComfyUI installation
- The model appears to be {model_type.lower()}
- File size suggests it's a substantial model worth tracking

## System Information
- Environment: RunPod
- Model Directory: /workspace/ComfyUI/models/
- Detection Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""

            return {
                'title': title,
                'body': body,
                'labels': ['preset-request', 'enhancement'],
                'model_info': model_info
            }

        except Exception as e:
            print(f"Error creating GitHub issue data: {e}")
            return {
                'title': f"Add preset for {model_info['filename']}",
                'body': f"Please add preset support for model: {model_info['filename']} ({model_info['size_gb']}GB)",
                'labels': ['preset-request', 'enhancement'],
                'model_info': model_info
            }

    def _guess_model_type(self, model_info: Dict) -> str:
        """Guess model type from filename and category"""
        filename_lower = model_info['filename'].lower()
        category = model_info['category']

        # Video generation indicators
        if any(indicator in filename_lower for indicator in ['wan', 'ltxv', 'mochi', 'hunyuan', 's2v', 'ti2v', 'i2v']):
            return 'Video Generation Model'

        # Image generation indicators
        if any(indicator in filename_lower for indicator in ['flux', 'sdxl', 'juggernaut', 'realistic', 'qwen', 'sd_', 'stable']):
            return 'Image Generation Model'

        # Audio generation indicators
        if any(indicator in filename_lower for indicator in ['musicgen', 'bark', 'tts', 'audio', 'ace']):
            return 'Audio Generation Model'

        # Category-based fallback
        if category == 'diffusion_models':
            return 'Diffusion Model'
        elif category == 'checkpoints':
            return 'Checkpoint Model'
        elif category == 'loras':
            return 'LoRA Model'
        elif category == 'vae':
            return 'VAE Model'
        elif category == 'text_encoders':
            return 'Text Encoder Model'
        elif category == 'audio':
            return 'Audio Model'
        elif category == 'TTS':
            return 'Text-to-Speech Model'
        elif category == 'audio_encoders':
            return 'Audio Encoder Model'
        else:
            return 'Unknown Model Type'