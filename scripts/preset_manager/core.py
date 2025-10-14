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
        """Get storage information using df command for RunPod network volumes"""
        print(f"[DEBUG] Getting RunPod storage info...")
        try:
            # Use df to get accurate network volume size
            result = subprocess.run(['df', '-h', '/workspace'],
                                  capture_output=True, text=True, timeout=10)

            print(f"[DEBUG] df -h /workspace return code: {result.returncode}")
            print(f"[DEBUG] df -h /workspace stdout: '{result.stdout}'")
            print(f"[DEBUG] df -h /workspace stderr: '{result.stderr}'")

            if result.returncode != 0:
                print(f"[DEBUG] df command failed, falling back to filesystem method")
                # Fallback to filesystem method
                return self._get_filesystem_storage_info()

            # Parse df output
            # Example output:
            # Filesystem      Size  Used Avail Use% Mounted on
            # /dev/nvme1n1   100G   25G   75G  25% /workspace

            lines = result.stdout.strip().split('\n')
            print(f"[DEBUG] df output lines: {lines}")

            if len(lines) < 2:
                print(f"[DEBUG] df output has less than 2 lines, falling back")
                return self._get_filesystem_storage_info()

            # Skip header, get data line
            data_line = lines[1]
            parts = data_line.split()
            print(f"[DEBUG] df data line parts: {parts}")

            if len(parts) < 4:
                print(f"[DEBUG] df data line has less than 4 parts, falling back")
                return self._get_filesystem_storage_info()

            # Parse sizes (convert from human readable format)
            size_str = parts[1]
            used_str = parts[2]
            avail_str = parts[3]
            print(f"[DEBUG] Parsed sizes - Size: '{size_str}', Used: '{used_str}', Avail: '{avail_str}'")

            def parse_size(size_str: str) -> int:
                """Parse human readable size string to bytes"""
                print(f"[DEBUG] Parsing size: '{size_str}'")
                if not size_str:
                    print(f"[DEBUG] Size string is empty, returning 0")
                    return 0

                # Remove any commas and spaces
                size_str = size_str.replace(',', '').strip()

                # Match pattern like "100G", "25G", "1.5T", "500M", "2.1P"
                match = re.match(r'^(\d+\.?\d*)([KMGTPE]?)(i?B?)?$', size_str.upper())
                print(f"[DEBUG] Regex match result: {match}")
                if not match:
                    print(f"[DEBUG] No regex match, returning 0")
                    return 0

                number, unit = match.groups()[:2]
                print(f"[DEBUG] Parsed number: '{number}', unit: '{unit}'")
                try:
                    number = float(number)
                except ValueError:
                    print(f"[DEBUG] Failed to parse number, returning 0")
                    return 0

                multipliers = {
                    '': 1,
                    'K': 1024,
                    'M': 1024**2,
                    'G': 1024**3,
                    'T': 1024**4,
                    'P': 1024**5,
                    'E': 1024**6
                }

                result = int(number * multipliers.get(unit, 1))
                print(f"[DEBUG] Size parsing result: {result} bytes")
                return result

            total_space = parse_size(size_str)
            used_space = parse_size(used_str)
            free_space = parse_size(avail_str)
            print(f"[DEBUG] Final parsed sizes - Total: {total_space}, Used: {used_space}, Free: {free_space}")

            # Add RunPod-specific metadata
            return {
                'total_space': {
                    'bytes': total_space,
                    'gb': round(total_space / (1024**3), 2)
                },
                'used_space': {
                    'bytes': used_space,
                    'gb': round(used_space / (1024**3), 2)
                },
                'free_space': {
                    'bytes': free_space,
                    'gb': round(free_space / (1024**3), 2)
                },
                'usage_percentage': round((used_space / total_space) * 100, 2) if total_space > 0 else 0,
                'model_directories': self._get_model_directories_info(),
                'total_model_size': self._get_total_model_size(),
                'runpod_environment': True,
                'storage_type': 'network_volume',
                'source': 'df_command'
            }

        except Exception as e:
            print(f"Error getting RunPod storage info: {e}")
            # Fallback to filesystem method
            return self._get_filesystem_storage_info()

    def _get_filesystem_storage_info(self) -> Dict:
        """Get storage information using filesystem stats (original method)"""
        print(f"[DEBUG] Getting filesystem storage info for: {self.base_dir}")
        try:
            statvfs = os.statvfs(self.base_dir)
            print(f"[DEBUG] statvfs results - f_frsize: {statvfs.f_frsize}, f_blocks: {statvfs.f_blocks}, f_bavail: {statvfs.f_bavail}")

            total_space = statvfs.f_frsize * statvfs.f_blocks
            free_space = statvfs.f_frsize * statvfs.f_bavail
            used_space = total_space - free_space

            print(f"[DEBUG] Filesystem sizes - Total: {total_space}, Free: {free_space}, Used: {used_space}")

            return {
                'total_space': {
                    'bytes': total_space,
                    'gb': round(total_space / (1024**3), 2)
                },
                'used_space': {
                    'bytes': used_space,
                    'gb': round(used_space / (1024**3), 2)
                },
                'free_space': {
                    'bytes': free_space,
                    'gb': round(free_space / (1024**3), 2)
                },
                'usage_percentage': round((used_space / total_space) * 100, 2) if total_space > 0 else 0,
                'model_directories': self._get_model_directories_info(),
                'total_model_size': self._get_total_model_size(),
                'runpod_environment': False,
                'storage_type': 'local_filesystem',
                'source': 'filesystem_stats'
            }
        except Exception as e:
            return {'error': str(e)}

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