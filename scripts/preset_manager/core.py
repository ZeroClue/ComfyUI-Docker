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
        """Parse all preset categories and their file mappings"""
        try:
            self.presets = {
                # Video Generation Presets
                'LTXV_2B_FP8_SCALED': {
                    'name': 'LTXV 2B FP8 Scaled',
                    'category': 'Video Generation',
                    'type': 'video',
                    'description': 'LTXV 2B parameter video generation model in FP8 scaled format',
                    'download_size': '4.8GB',
                    'files': [
                        'diffusion_models/LTXV_2B_FP8_SCALED.safetensors'
                    ],
                    'use_case': 'High-quality video generation with optimized memory usage'
                },
                'WAN_22_5B_TIV2': {
                    'name': 'Wan 2.2 5B T2V',
                    'category': 'Video Generation',
                    'type': 'video',
                    'description': 'Wan 2.2 5B parameter text-to-video generation model',
                    'download_size': '9.2GB',
                    'files': [
                        'diffusion_models/Wan2.2_T2V_5B.safetensors',
                        'text_encoders/t5xxl_fp16.safetensors'
                    ],
                    'use_case': 'Text-to-video generation with superior quality'
                },
                'HUNYUAN_T2V_720P': {
                    'name': 'Hunyuan T2V 720P',
                    'category': 'Video Generation',
                    'type': 'video',
                    'description': 'Hunyuan text-to-video model optimized for 720p output',
                    'download_size': '5.1GB',
                    'files': [
                        'diffusion_models/hunyuan_t2v_720p.safetensors'
                    ],
                    'use_case': 'High-resolution 720p video generation'
                },
                'MOCHI_1_PREVIEW_FP8': {
                    'name': 'Mochi 1 Preview FP8',
                    'category': 'Video Generation',
                    'type': 'video',
                    'description': 'Mochi 1 preview video generation model in FP8 format',
                    'download_size': '9.8GB',
                    'files': [
                        'diffusion_models/mochi_1_preview_fp8.safetensors'
                    ],
                    'use_case': 'Preview of next-generation video generation'
                },
                'WAN22_I2V_A14B_GGUF_Q8_0': {
                    'name': 'Wan 2.2 I2V 14B GGUF',
                    'category': 'Video Generation',
                    'type': 'video',
                    'description': 'Wan 2.2 image-to-video 14B model in GGUF Q8 format',
                    'download_size': '7.8GB',
                    'files': [
                        'diffusion_models/Wan2.2_I2V_14B_Q8_0.gguf'
                    ],
                    'use_case': 'Image-to-video conversion with high quality'
                },
                'WAN_22_5B_I2V_GGUF_Q8_0': {
                    'name': 'Wan 2.2 I2V 5B GGUF',
                    'category': 'Video Generation',
                    'type': 'video',
                    'description': 'Wan 2.2 5B image-to-video model in GGUF Q8 format',
                    'download_size': '4.9GB',
                    'files': [
                        'diffusion_models/Wan2.2_I2V_5B_Q8_0.gguf'
                    ],
                    'use_case': 'Efficient image-to-video conversion'
                },
                'WAN22_LIGHTNING_LORA': {
                    'name': 'Wan 2.2 Lightning LoRA',
                    'category': 'Video Generation',
                    'type': 'video',
                    'description': 'Wan 2.2 Lightning LoRA for faster inference',
                    'download_size': '1.4GB',
                    'files': [
                        'loras/wan22_lightning.safetensors'
                    ],
                    'use_case': 'Speed up video generation by 2-3x'
                },
                'WAN22_NSFW_LORA': {
                    'name': 'Wan 2.2 NSFW LoRA',
                    'category': 'Video Generation',
                    'type': 'video',
                    'description': 'Wan 2.2 NSFW filter LoRA',
                    'download_size': '1.2GB',
                    'files': [
                        'loras/wan22_nsfw_filter.safetensors'
                    ],
                    'use_case': 'Content filtering for video generation'
                },
                'WAINSFW_V140': {
                    'name': 'Wan NSFW Filter v1.40',
                    'category': 'Video Generation',
                    'type': 'video',
                    'description': 'Wan NSFW filter model v1.40',
                    'download_size': '538MB',
                    'files': [
                        'diffusion_models/wan_nsfw_filter_v140.safetensors'
                    ],
                    'use_case': 'Content safety filtering'
                },
                'NTRMIX_V40': {
                    'name': 'Neural Texture Refinement Mix v4.0',
                    'category': 'Video Generation',
                    'type': 'video',
                    'description': 'Neural Texture Refinement Mix v4.0',
                    'download_size': '1.8GB',
                    'files': [
                        'diffusion_models/ntrmix_v40.safetensors'
                    ],
                    'use_case': 'Texture refinement and enhancement'
                },
                'UPSCALE_MODELS': {
                    'name': 'Video Upscale Models',
                    'category': 'Video Generation',
                    'type': 'video',
                    'description': 'Video upscaling models collection',
                    'download_size': '2.1GB',
                    'files': [
                        'upscale_models/4x_NMKD-Siax_xl.pth',
                        'upscale_models/4x_NMKD-Superscale_150k.pth',
                        'upscale_models/8x_NMKD-Superscale_150k.pth'
                    ],
                    'use_case': 'Video quality enhancement and upscaling'
                },
                'WAN22_S2V_FP8_SCALED': {
                    'name': 'Wan 2.2 S2V FP8',
                    'category': 'Video Generation',
                    'type': 'video',
                    'description': 'Wan 2.2 sound-to-video model in FP8 format',
                    'download_size': '6.3GB',
                    'files': [
                        'diffusion_models/Wan2.2_S2V_FP8.safetensors',
                        'audio_encoders/audio_encoder.pth'
                    ],
                    'use_case': 'Audio-to-video generation'
                },
                'VIDEO_COMPLETE': {
                    'name': 'Complete Video Workflow',
                    'category': 'Video Generation',
                    'type': 'video',
                    'description': 'Complete video generation workflow with all models',
                    'download_size': '25GB',
                    'files': [
                        'diffusion_models/LTXV_2B_FP8_SCALED.safetensors',
                        'diffusion_models/Wan2.2_T2V_5B.safetensors',
                        'diffusion_models/hunyuan_t2v_720p.safetensors',
                        'diffusion_models/mochi_1_preview_fp8.safetensors',
                        'text_encoders/t5xxl_fp16.safetensors',
                        'loras/wan22_lightning.safetensors',
                        'upscale_models/4x_NMKD-Siax_xl.pth'
                    ],
                    'use_case': 'Full video generation capabilities'
                },

                # Image Generation Presets
                'FLUX_SCHNELL_BASIC': {
                    'name': 'FLUX Schnell',
                    'category': 'Image Generation',
                    'type': 'image',
                    'description': 'FLUX Schnell 12B parameter fast image generation model',
                    'download_size': '24GB',
                    'files': [
                        'diffusion_models/flux1-schnell.safetensors',
                        'text_encoders/t5xxl_fp16.safetensors',
                        'vae/ae.safetensors'
                    ],
                    'use_case': 'Fast, high-quality image generation'
                },
                'FLUX_DEV_BASIC': {
                    'name': 'FLUX Dev',
                    'category': 'Image Generation',
                    'type': 'image',
                    'description': 'FLUX Dev 12B parameter high-quality image generation model',
                    'download_size': '24GB',
                    'files': [
                        'diffusion_models/flux1-dev.safetensors',
                        'text_encoders/t5xxl_fp16.safetensors',
                        'vae/ae.safetensors'
                    ],
                    'use_case': 'Highest quality image generation'
                },
                'SDXL_BASE_V1': {
                    'name': 'SDXL Base 1.0',
                    'category': 'Image Generation',
                    'type': 'image',
                    'description': 'Stable Diffusion XL 1.0 base model',
                    'download_size': '6.9GB',
                    'files': [
                        'checkpoints/sd_xl_base_1.0.safetensors',
                        'vae/sdxl_vae.safetensors'
                    ],
                    'use_case': 'Standard high-resolution image generation'
                },
                'JUGGERNAUT_XL_V8': {
                    'name': 'Juggernaut XL v8',
                    'category': 'Image Generation',
                    'type': 'image',
                    'description': 'Juggernaut XL v8 for photorealistic images',
                    'download_size': '6.9GB',
                    'files': [
                        'checkpoints/juggernautXL_v8Rundiffusion.safetensors',
                        'vae/sdxl_vae.safetensors'
                    ],
                    'use_case': 'Photorealistic image generation'
                },
                'REALISTIC_VISION_V6': {
                    'name': 'Realistic Vision v6.0',
                    'category': 'Image Generation',
                    'type': 'image',
                    'description': 'Realistic Vision v6.0 for SD 1.5',
                    'download_size': '5.1GB',
                    'files': [
                        'checkpoints/realisticVisionV60B1_v51VAE.safetensors'
                    ],
                    'use_case': 'Photorealistic SD 1.5 generation'
                },
                'REALVIS_XL_V4': {
                    'name': 'RealVis XL v4',
                    'category': 'Image Generation',
                    'type': 'image',
                    'description': 'RealVis XL v4 for realistic images',
                    'download_size': '6.9GB',
                    'files': [
                        'checkpoints/realvisxlV40.safetensors',
                        'vae/sdxl_vae.safetensors'
                    ],
                    'use_case': 'Realistic image generation'
                },
                'QWEN_IMAGE_BASIC': {
                    'name': 'Qwen 20B Image',
                    'category': 'Image Generation',
                    'type': 'image',
                    'description': 'Qwen 20B parameter image generation model',
                    'download_size': '38GB',
                    'files': [
                        'diffusion_models/qwen2vl_7b_instruct.pth',
                        'text_encoders/qwen_text_encoder.pth'
                    ],
                    'use_case': 'Advanced image generation with superior text rendering'
                },
                'QWEN_IMAGE_CHINESE': {
                    'name': 'Qwen 20B Chinese',
                    'category': 'Image Generation',
                    'type': 'image',
                    'description': 'Qwen 20B model optimized for Chinese text rendering',
                    'download_size': '38GB',
                    'files': [
                        'diffusion_models/qwen2vl_7b_chinese.pth',
                        'text_encoders/qwen_chinese_encoder.pth'
                    ],
                    'use_case': 'Chinese text in images'
                },
                'IMAGE_COMPLETE_WORKFLOW': {
                    'name': 'Complete Image Workflow',
                    'category': 'Image Generation',
                    'type': 'image',
                    'description': 'Complete image generation workflow with all models',
                    'download_size': '100GB',
                    'files': [
                        'diffusion_models/flux1-schnell.safetensors',
                        'diffusion_models/flux1-dev.safetensors',
                        'checkpoints/sd_xl_base_1.0.safetensors',
                        'checkpoints/juggernautXL_v8Rundiffusion.safetensors',
                        'checkpoints/realisticVisionV60B1_v51VAE.safetensors',
                        'text_encoders/t5xxl_fp16.safetensors',
                        'vae/sdxl_vae.safetensors',
                        'vae/ae.safetensors'
                    ],
                    'use_case': 'Full image generation capabilities'
                },

                # Audio Generation Presets
                'MUSICGEN_MEDIUM': {
                    'name': 'MusicGen Medium',
                    'category': 'Audio Generation',
                    'type': 'audio',
                    'description': 'MusicGen medium model for text-to-music generation',
                    'download_size': '2.8GB',
                    'files': [
                        'audio/musicgen_medium.safetensors'
                    ],
                    'use_case': 'High-quality music generation'
                },
                'BARK_BASIC': {
                    'name': 'Bark TTS',
                    'category': 'Audio Generation',
                    'type': 'audio',
                    'description': 'Bark text-to-speech model',
                    'download_size': '2.1GB',
                    'files': [
                        'TTS/bark_model.pth',
                        'audio_encoders/bark_encoder.pth'
                    ],
                    'use_case': 'High-quality voice synthesis'
                },
                'PARLER_TTS': {
                    'name': 'Parler TTS',
                    'category': 'Audio Generation',
                    'type': 'audio',
                    'description': 'Parler TTS advanced text-to-speech',
                    'download_size': '3.2GB',
                    'files': [
                        'TTS/parler_tts_model.safetensors'
                    ],
                    'use_case': 'Advanced voice synthesis'
                },
                'STABLE_AUDIO_OPEN': {
                    'name': 'Stable Audio Open',
                    'category': 'Audio Generation',
                    'type': 'audio',
                    'description': 'Stable Audio open model for audio generation',
                    'download_size': '2.4GB',
                    'files': [
                        'audio/stable_audio_open.safetensors'
                    ],
                    'use_case': 'High-quality audio generation'
                },
                'MUSICGEN_SMALL': {
                    'name': 'MusicGen Small',
                    'category': 'Audio Generation',
                    'type': 'audio',
                    'description': 'MusicGen small model',
                    'download_size': '1.3GB',
                    'files': [
                        'audio/musicgen_small.safetensors'
                    ],
                    'use_case': 'Fast music generation'
                },
                'AUDIO_ALL': {
                    'name': 'Complete Audio Suite',
                    'category': 'Audio Generation',
                    'type': 'audio',
                    'description': 'Complete audio generation suite with all models',
                    'download_size': '15GB',
                    'files': [
                        'audio/musicgen_medium.safetensors',
                        'audio/musicgen_small.safetensors',
                        'audio/stable_audio_open.safetensors',
                        'TTS/bark_model.pth',
                        'TTS/parler_tts_model.safetensors',
                        'audio_encoders/bark_encoder.pth'
                    ],
                    'use_case': 'Full audio generation capabilities'
                }
            }

            # Organize by category
            self.categories = {
                'Video Generation': [p for p in self.presets.values() if p['category'] == 'Video Generation'],
                'Image Generation': [p for p in self.presets.values() if p['category'] == 'Image Generation'],
                'Audio Generation': [p for p in self.presets.values() if p['category'] == 'Audio Generation']
            }

        except Exception as e:
            print(f"Error parsing presets: {e}")

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