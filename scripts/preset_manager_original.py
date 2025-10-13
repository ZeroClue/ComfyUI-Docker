#!/usr/bin/env python3
"""
ComfyUI Preset Manager - Complete Model Management System
A Flask-based web interface for managing ComfyUI presets and models
"""

import os
import sys
import json
import subprocess
import threading
import time
import shutil
import glob
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory

# Try to import optional dependencies
try:
    from flask_session import Session
    HAS_SESSION = True
except ImportError:
    HAS_SESSION = False
    print("Warning: flask-session not available, using default session handling")

try:
    import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False
    print("Warning: markdown not available, README rendering disabled")

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    print("Warning: yaml not available")

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.urandom(24)

# Get access password from environment
ACCESS_PASSWORD = os.environ.get('ACCESS_PASSWORD', 'password')

# Initialize session if available
if HAS_SESSION:
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
    app.config['SESSION_FILE_DIR'] = '/tmp/flask_sessions'
    os.makedirs('/tmp/flask_sessions', exist_ok=True)
    Session(app)
else:
    print("Using default Flask session handling")

# Global variables
operation_status = {}
operation_progress = {}

class ModelManager:
    """Manages ComfyUI models and presets with full CRUD operations"""

    def __init__(self):
        self.base_dir = "/workspace/ComfyUI/models"
        self.readme_base_path = "/workspace/docs/presets"
        self.presets = {}
        self.categories = {}
        self._initialize_directories()
        self._parse_all_presets()
        self._scan_installed_models()

    def _initialize_directories(self):
        """Ensure required directories exist"""
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(f"{self.base_dir}/checkpoints", exist_ok=True)
        os.makedirs(f"{self.base_dir}/diffusion_models", exist_ok=True)
        os.makedirs(f"{self.base_dir}/text_encoders", exist_ok=True)
        os.makedirs(f"{self.base_dir}/vae", exist_ok=True)
        os.makedirs(f"{self.base_dir}/loras", exist_ok=True)
        os.makedirs(f"{self.base_dir}/upscale_models", exist_ok=True)
        os.makedirs(f"{self.base_dir}/audio_encoders", exist_ok=True)
        os.makedirs(f"{self.base_dir}/TTS", exist_ok=True)
        os.makedirs(f"{self.base_dir}/audio", exist_ok=True)

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
        readme_path = os.path.join(self.readme_base_path, 'presets', f'{preset_id}.md')
        if os.path.exists(readme_path):
            with open(readme_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def render_readme(self, readme_content: str) -> str:
        """Render README markdown to HTML"""
        if not HAS_MARKDOWN:
            return f"<pre>{readme_content}</pre>"
        try:
            return markdown.markdown(readme_content)
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

    def get_storage_info(self) -> Dict:
        """Get comprehensive storage information"""
        try:
            # Get disk usage
            statvfs = os.statvfs(self.base_dir)
            total_space = statvfs.f_frsize * statvfs.f_blocks
            free_space = statvfs.f_frsize * statvfs.f_bavail
            used_space = total_space - free_space

            # Get model directory sizes
            model_dirs = {}
            total_model_size = 0

            for category in ['checkpoints', 'diffusion_models', 'text_encoders', 'vae',
                           'loras', 'upscale_models', 'audio_encoders', 'TTS', 'audio']:
                category_path = os.path.join(self.base_dir, category)
                if os.path.exists(category_path):
                    size = self._get_directory_size(category_path)
                    model_dirs[category] = {
                        'size_bytes': size,
                        'size_mb': round(size / (1024 * 1024), 2),
                        'size_gb': round(size / (1024 * 1024 * 1024), 2),
                        'file_count': self._count_files(category_path)
                    }
                    total_model_size += size

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
                'usage_percentage': round((used_space / total_space) * 100, 2),
                'model_directories': model_dirs,
                'total_model_size': {
                    'bytes': total_model_size,
                    'gb': round(total_model_size / (1024**3), 2)
                }
            }

        except Exception as e:
            return {'error': str(e)}

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
            for category in ['checkpoints', 'diffusion_models', 'text_encoders', 'vae',
                           'loras', 'upscale_models', 'audio_encoders', 'TTS', 'audio']:
                category_path = os.path.join(self.base_dir, category)
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

# Initialize model manager
model_manager = ModelManager()

def check_auth():
    """Check if user is authenticated"""
    if 'authenticated' not in session:
        return False
    return session.get('authenticated') == True

@app.before_request
def require_auth():
    """Require authentication for all routes except login and static"""
    if request.endpoint in ['login', 'static'] or request.path.startswith('/static/'):
        return

    if not check_auth():
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ACCESS_PASSWORD:
            session['authenticated'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html',
                                 error='Invalid password',
                                 using_default_password=(ACCESS_PASSWORD == 'password'))

    # Check if using default password
    using_default_password = (ACCESS_PASSWORD == 'password')

    return render_template('login.html',
                         password_required=True,
                         using_default_password=using_default_password)

@app.route('/logout')
def logout():
    """Logout"""
    session.pop('authenticated', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    """Main dashboard with storage overview"""
    storage_info = model_manager.get_storage_info()

    # Calculate installation statistics
    total_presets = len(model_manager.presets)
    installed_presets = len([p for p in model_manager.presets.values() if p['is_installed']])
    partial_presets = len([p for p in model_manager.presets.values() if p['is_partial']])

    stats = {
        'total_presets': total_presets,
        'installed_presets': installed_presets,
        'partial_presets': partial_presets,
        'installation_rate': round((installed_presets / total_presets) * 100, 1) if total_presets > 0 else 0
    }

    return render_template('index.html',
                         storage_info=storage_info,
                         categories=model_manager.categories,
                         stats=stats)

@app.route('/presets')
def presets():
    """Browse all presets"""
    return render_template('presets.html', categories=model_manager.categories)

@app.route('/preset/<preset_id>')
def preset_detail(preset_id):
    """Preset detail page"""
    preset = model_manager.get_preset(preset_id)
    if not preset:
        return "Preset not found", 404

    readme_content = model_manager.get_preset_readme(preset_id)
    readme_html = model_manager.render_readme(readme_content) if readme_content else None

    return render_template('preset_detail.html',
                         preset=preset,
                         preset_id=preset_id,
                         readme_html=readme_html)

@app.route('/storage')
def storage():
    """Storage management page"""
    storage_info = model_manager.get_storage_info()
    return render_template('storage.html', storage_info=storage_info)

@app.route('/api/download/<preset_id>', methods=['POST'])
def start_download(preset_id):
    """Start downloading a preset"""
    preset = model_manager.get_preset(preset_id)
    if not preset:
        return jsonify({'error': 'Preset not found'}), 404

    # Initialize operation status
    operation_id = f"download_{preset_id}_{int(time.time())}"
    operation_status[operation_id] = {
        'type': 'download',
        'preset_id': preset_id,
        'status': 'starting',
        'progress': 0,
        'message': 'Initializing download...',
        'start_time': datetime.now().isoformat()
    }

    # Start download in background thread
    thread = threading.Thread(target=download_preset, args=(operation_id, preset))
    thread.daemon = True
    thread.start()

    return jsonify({'operation_id': operation_id})

@app.route('/api/delete/<preset_id>', methods=['DELETE'])
def delete_preset(preset_id):
    """Delete preset files"""
    try:
        success, message = model_manager.delete_preset_files(preset_id)
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/cleanup', methods=['POST'])
def cleanup_models():
    """Cleanup unused models"""
    try:
        cleanup_type = request.json.get('type', 'unused')

        if cleanup_type == 'unused':
            success, message = model_manager.cleanup_unused_models()
        else:
            return jsonify({'success': False, 'message': 'Unknown cleanup type'}), 400

        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/operation/status/<operation_id>')
def get_operation_status(operation_id):
    """Get operation status"""
    if operation_id not in operation_status:
        return jsonify({'error': 'Operation not found'}), 404

    return jsonify(operation_status[operation_id])

@app.route('/api/storage/status')
def get_storage_status():
    """Get current storage information"""
    storage_info = model_manager.get_storage_info()
    return jsonify(storage_info)

def download_preset(operation_id: str, preset: Dict):
    """Download preset in background thread"""
    try:
        # Determine script path based on preset type
        if preset['type'] == 'video':
            script_path = "/scripts/download_presets.sh"
        elif preset['type'] == 'image':
            script_path = "/scripts/download_image_presets.sh"
        elif preset['type'] == 'audio':
            script_path = "/scripts/download_audio_presets.sh"
        else:
            raise ValueError(f"Unknown preset type: {preset['type']}")

        # Update status
        operation_status[operation_id]['status'] = 'downloading'
        operation_status[operation_id]['message'] = f'Downloading {preset["name"]}...'

        # Run download command
        cmd = [script_path, preset['name'].split()[0]]  # Use first part of name
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # Monitor progress
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                # Parse progress from output
                if 'Downloading' in output or 'downloading' in output.lower():
                    operation_status[operation_id]['progress'] = min(
                        operation_status[operation_id]['progress'] + 5, 90
                    )
                    operation_status[operation_id]['message'] = output.strip()

        # Check result
        return_code = process.poll()
        if return_code == 0:
            operation_status[operation_id]['status'] = 'completed'
            operation_status[operation_id]['progress'] = 100
            operation_status[operation_id]['message'] = 'Download completed successfully!'

            # Rescan models to update status
            model_manager._scan_installed_models()
        else:
            stderr_output = process.stderr.read()
            operation_status[operation_id]['status'] = 'error'
            operation_status[operation_id]['message'] = f'Download failed: {stderr_output}'

    except Exception as e:
        operation_status[operation_id]['status'] = 'error'
        operation_status[operation_id]['message'] = f'Download error: {str(e)}'

if __name__ == '__main__':
    # Create required directories
    os.makedirs('/app/templates', exist_ok=True)
    os.makedirs('/app/static', exist_ok=True)

    # Run Flask app
    app.run(host='0.0.0.0', port=9001, debug=False)