#!/usr/bin/env python3
"""
ComfyUI Workflow Parser for Preset Creation
Parses ComfyUI workflow JSON files and extracts model information for preset generation
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ModelFile:
    """Represents a model file found in the workflow"""
    filename: str
    node_type: str
    node_id: str
    category: str = ""
    suggested_path: str = ""
    detected_url: Optional[str] = None
    estimated_size: str = ""
    confidence: float = 0.0  # 0.0 to 1.0


@dataclass
class WorkflowAnalysis:
    """Complete analysis of a ComfyUI workflow"""
    workflow_name: str = ""
    detected_category: str = "unknown"  # video, image, audio
    models: List[ModelFile] = field(default_factory=list)
    total_estimated_size: float = 0.0
    confidence_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class ComfyUIWorkflowParser:
    """Parser for ComfyUI workflow JSON files"""

    # Node types that load models
    MODEL_LOADER_NODES = {
        'CheckpointLoaderSimple': 'checkpoints',
        'VAELoader': 'vae',
        'LoraLoader': 'loras',
        'CLIPLoader': 'text_encoders',
        'DualCLIPLoader': 'text_encoders',
        'CLIPVisionLoader': 'clip_vision',
        'UNETLoader': 'diffusion_models',
        'DiffusionLoader': 'diffusion_models',
        'AudioLoader': 'audio_encoders',
        'TTSLoader': 'TTS',
        'UpscaleModelLoader': 'upscale_models',
        'ControlNetLoader': 'controlnet',
        'IPAdapterLoader': 'ipadapter',
    }

    # Known model patterns and their HuggingFace URLs
    KNOWN_MODELS = {
        # Video Models
        'ltx-video-2b': {
            'url': 'https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltx-video-2b-v0.9.5.safetensors',
            'category': 'checkpoints',
            'size': '4.8GB'
        },
        'wan2.2_t2v_5b': {
            'url': 'https://huggingface.co/Wailicv/Wan2.2/resolve/main/models/Wan2.2_T2V_5B.safetensors',
            'category': 'diffusion_models',
            'size': '9.2GB'
        },
        'wan2.2_i2v_14b': {
            'url': 'https://huggingface.co/Wailicv/Wan2.2/resolve/main/models/Wan2.2_I2V_14B_Q8_0.gguf',
            'category': 'diffusion_models',
            'size': '7.8GB'
        },
        'hunyuan_video_t2v_720p': {
            'url': 'https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/diffusion_models/hunyuan_video_t2v_720p_bf16.safetensors',
            'category': 'diffusion_models',
            'size': '5.1GB'
        },
        'mochi_1_preview': {
            'url': 'https://huggingface.co/genmo/mochi-1-preview/resolve/main/model.fp8.safetensors',
            'category': 'diffusion_models',
            'size': '9.8GB'
        },
        'cosmos_predict2': {
            'url': 'https://huggingface.co/nvidia/Cosmos-Predict2/resolve/main/cosmos_predict2_video2world.safetensors',
            'category': 'diffusion_models',
            'size': '24.5GB'
        },

        # Image Models
        'flux1-schnell': {
            'url': 'https://huggingface.co/black-forest-labs/FLUX.1-schnell/resolve/main/flux1-schnell.safetensors',
            'category': 'diffusion_models',
            'size': '12GB'
        },
        'flux1-dev': {
            'url': 'https://huggingface.co/black-forest-labs/FLUX.1-dev/resolve/main/flux1-dev.safetensors',
            'category': 'diffusion_models',
            'size': '12GB'
        },
        'sd_xl_base_1.0': {
            'url': 'https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors',
            'category': 'checkpoints',
            'size': '6.9GB'
        },
        'juggernautxl_v8': {
            'url': 'https://huggingface.co/cagliostrolab/animagine-xl-3.0/resolve/main/animagine-xl-3.0.safetensors',
            'category': 'checkpoints',
            'size': '6.9GB'
        },
        'v1-5-pruned': {
            'url': 'https://huggingface.co/Comfy-Org/stable-diffusion-v1-5-archive/resolve/main/v1-5-pruned-emaonly-fp16.safetensors',
            'category': 'checkpoints',
            'size': '4.0GB'
        },
        'qwen_image': {
            'url': 'https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_fp8_e4m3fn.safetensors',
            'category': 'diffusion_models',
            'size': '19GB'
        },
        'sd3_large': {
            'url': 'https://huggingface.co/stabilityai/stable-diffusion-3.5-large/resolve/main/sd3_large.safetensors',
            'category': 'diffusion_models',
            'size': '8.8GB'
        },
        'omnigen2': {
            'url': 'https://huggingface.co/stabilityai/omnigen/resolve/main/omnigen2.safetensors',
            'category': 'diffusion_models',
            'size': '8.5GB'
        },

        # Audio Models
        'musicgen_medium': {
            'url': 'https://huggingface.co/facebook/musicgen-medium/resolve/main/pytorch_model.bin',
            'category': 'audio_encoders',
            'size': '2.8GB'
        },
        'musicgen_small': {
            'url': 'https://huggingface.co/facebook/musicgen-small/resolve/main/pytorch_model.bin',
            'category': 'audio_encoders',
            'size': '1.3GB'
        },
        'stable_audio_open': {
            'url': 'https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/main/model.safetensors',
            'category': 'audio_encoders',
            'size': '2.4GB'
        },
        'bark': {
            'url': 'https://huggingface.co/suno-ai/bark/resolve/main/pytorch_model.bin',
            'category': 'TTS',
            'size': '1.2GB'
        },
        'acestep': {
            'url': 'https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/main/acestep-v15-turbo.safetensors',
            'category': 'checkpoints',
            'size': '7.0GB'
        },

        # Text Encoders
        't5xxl_fp16': {
            'url': 'https://huggingface.co/Comfy-Org/sd3-t5xxlfp16/resolve/main/t5xxl_fp16.safetensors',
            'category': 'text_encoders',
            'size': '4.9GB'
        },
        'clip_l': {
            'url': 'https://huggingface.co/openai/clip-vit-large-patch14/resolve/main/pytorch_model.bin',
            'category': 'text_encoders',
            'size': '1.7GB'
        },
        'clip_g': {
            'url': 'https://huggingface.co/stabilityai/stable-diffusion-3.5-large/resolve/main/text_encoders/clip_g.safetensors',
            'category': 'text_encoders',
            'size': '1.7GB'
        },
        'umt5_xxl_fp8': {
            'url': 'https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors',
            'category': 'text_encoders',
            'size': '6.74GB'
        },
        'qwen_2.5_vl_7b': {
            'url': 'https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors',
            'category': 'text_encoders',
            'size': '14GB'
        },

        # VAE
        'sdxl_vae': {
            'url': 'https://huggingface.co/stabilityai/sdxl-vae-fp16-fix/resolve/main/sdxl_vae_fp16_fix.safetensors',
            'category': 'vae',
            'size': '335MB'
        },
        'wan2.2_vae': {
            'url': 'https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan2.2_vae.safetensors',
            'category': 'vae',
            'size': '1.41GB'
        },
        'ae.safetensors': {
            'url': 'https://huggingface.co/black-forest-labs/FLUX.1-dev/resolve/main/ae.safetensors',
            'category': 'vae',
            'size': '335MB'
        },

        # CLIP Vision
        'sd_image_encoder': {
            'url': 'https://huggingface.co/stabilityai/stable-diffusion-2-1/resolve/main/image_encoder/model.safetensors',
            'category': 'clip_vision',
            'size': '1.6GB'
        },
        'llava_llama3_vision': {
            'url': 'https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/clip_vision/llava_llama3_vision.safetensors',
            'category': 'clip_vision',
            'size': '2.4GB'
        },

        # Upscale Models
        '4x_nmkd-siax_xl': {
            'url': 'https://huggingface.co/Guillaume-M/4x_NMKD-Siax_xl/resolve/main/4x_NMKD-Siax_xl.pth',
            'category': 'upscale_models',
            'size': '690MB'
        },
        '4x_nmkd-superscale_150k': {
            'url': 'https://huggingface.co/ConseilsSuprimes/4x_NMKD-Superscale_150k/resolve/main/4x_NMKD-Superscale_150k.pth',
            'category': 'upscale_models',
            'size': '690MB'
        },

        # Audio Encoders
        'wav2vec2_large': {
            'url': 'https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/audio_encoders/wav2vec2_large_english_fp16.safetensors',
            'category': 'audio_encoders',
            'size': '631MB'
        },
        'audio_encoder': {
            'url': 'https://huggingface.co/Wailicv/Wan2.2/resolve/main/models/audio_encoder.pth',
            'category': 'audio_encoders',
            'size': '1.2GB'
        },
    }

    def __init__(self):
        """Initialize the parser"""
        self.workflow_data = None
        self.analysis = WorkflowAnalysis()

    def parse_workflow_file(self, file_path: str) -> WorkflowAnalysis:
        """Parse a ComfyUI workflow JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Try to parse as JSON
            try:
                self.workflow_data = json.loads(content)
            except json.JSONDecodeError:
                # Some workflows have extra text before/after JSON
                # Try to extract JSON portion
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    self.workflow_data = json.loads(json_match.group(0))
                else:
                    raise ValueError("Could not extract valid JSON from workflow file")

            return self._analyze_workflow()

        except FileNotFoundError:
            raise ValueError(f"Workflow file not found: {file_path}")
        except Exception as e:
            raise ValueError(f"Error parsing workflow: {str(e)}")

    def _analyze_workflow(self) -> WorkflowAnalysis:
        """Analyze the workflow and extract model information"""
        self.analysis = WorkflowAnalysis()

        # Try to get workflow name
        if isinstance(self.workflow_data, dict):
            # Check for API format (newer ComfyUI)
            if 'nodes' in self.workflow_data and isinstance(self.workflow_data['nodes'], list):
                self.analysis.metadata['format'] = 'api'
                nodes_list = self.workflow_data['nodes']
            # Check for legacy format
            elif isinstance(list(self.workflow_data.values())[0], dict) if self.workflow_data else False:
                self.analysis.metadata['format'] = 'legacy'
                nodes_list = list(self.workflow_data.values())
            else:
                self.analysis.metadata['format'] = 'unknown'
                nodes_list = []

            # Extract workflow name if available
            if 'extra' in self.workflow_data and 'ds' in self.workflow_data['extra']:
                ds_data = self.workflow_data['extra']['ds']
                if 'data' in ds_data and 'workflow' in ds_data['data']:
                    workflow_info = ds_data['data']['workflow']
                    if isinstance(workflow_info, dict):
                        self.analysis.workflow_name = workflow_info.get('title', workflow_info.get('name', ''))
        else:
            nodes_list = []

        # Process each node
        for node_data in nodes_list:
            if isinstance(node_data, dict):
                self._process_node(node_data)

        # Determine category
        self._determine_category()

        # Calculate total size
        self._calculate_total_size()

        # Calculate confidence score
        self._calculate_confidence()

        # Generate suggestions
        self._generate_suggestions()

        return self.analysis

    def _process_node(self, node_data: Dict):
        """Process a single node and extract model information"""
        # Get node ID
        node_id = str(node_data.get('id', 'unknown'))

        class_type = node_data.get('type', '') or node_data.get('class_type', '')

        # Get inputs - could be in different places
        inputs = node_data.get('inputs', {})
        widgets_values = node_data.get('widgets_values', [])

        # Handle widgets_values (common in API format)
        if class_type in self.MODEL_LOADER_NODES and widgets_values:
            if isinstance(widgets_values, list) and len(widgets_values) > 0:
                model_filename = widgets_values[0] if isinstance(widgets_values[0], str) else None
                if model_filename:
                    self._create_model_from_filename(model_filename, class_type, node_id)
                    return

        # Handle inputs dict
        if isinstance(inputs, dict):
            for key, value in inputs.items():
                if 'model' in key.lower() or 'ckpt' in key.lower() or 'name' in key.lower():
                    if isinstance(value, str) and value:
                        self._create_model_from_filename(value, class_type, node_id)
                        return
                    elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], str):
                        self._create_model_from_filename(value[0], class_type, node_id)
                        return

    def _create_model_from_filename(self, filename: str, class_type: str, node_id: str):
        """Create a model file entry from filename"""
        if class_type in self.MODEL_LOADER_NODES:
            category = self.MODEL_LOADER_NODES[class_type]

            model_file = ModelFile(
                filename=filename,
                node_type=class_type,
                node_id=node_id,
                category=category
            )

            # Try to match with known models
            self._match_known_model(model_file)

            # Generate suggested path
            model_file.suggested_path = self._suggest_path(category, filename)

            self.analysis.models.append(model_file)

    def _match_known_model(self, model_file: ModelFile):
        """Try to match the model file with known models"""
        filename_lower = model_file.filename.lower()

        for known_pattern, model_info in self.KNOWN_MODELS.items():
            if known_pattern.lower() in filename_lower:
                model_file.detected_url = model_info['url']
                model_file.estimated_size = model_info['size']
                model_file.category = model_info['category']
                model_file.confidence = 0.9
                return

        # Fallback: try to determine size from file extension and common patterns
        model_file.confidence = 0.5
        if model_file.filename.endswith('.safetensors'):
            # Large model
            model_file.estimated_size = "~4GB"
        elif model_file.filename.endswith('.gguf'):
            # Quantized model
            model_file.estimated_size = "~8GB"
        elif model_file.filename.endswith(('.pth', '.pt')):
            # PyTorch model
            model_file.estimated_size = "~1GB"
        else:
            model_file.estimated_size = "Unknown"

    def _suggest_path(self, category: str, filename: str) -> str:
        """Suggest a path for the model file"""
        return f"{category}/{filename}"

    def _determine_category(self):
        """Determine the workflow category based on detected models"""
        video_keywords = ['ltx', 'wan', 'mochi', 'hunyuan', 's2v', 'ti2v', 'i2v', 'cosmos', 'video']
        image_keywords = ['flux', 'sdxl', 'sd1.5', 'juggernaut', 'realistic', 'qwen', 'sd_', 'stable', 'omnigen', 'sd3']
        audio_keywords = ['musicgen', 'bark', 'tts', 'audio', 'ace']

        video_score = 0
        image_score = 0
        audio_score = 0

        for model in self.analysis.models:
            filename_lower = model.filename.lower()

            for keyword in video_keywords:
                if keyword in filename_lower:
                    video_score += 2

            for keyword in image_keywords:
                if keyword in filename_lower:
                    image_score += 2

            for keyword in audio_keywords:
                if keyword in filename_lower:
                    audio_score += 2

            # Category-based scoring
            if model.category in ['diffusion_models', 'checkpoints']:
                if any(kw in filename_lower for kw in video_keywords):
                    video_score += 3
                elif any(kw in filename_lower for kw in image_keywords):
                    image_score += 3

            if model.category in ['audio_encoders', 'TTS']:
                audio_score += 3

        # Determine winner
        max_score = max(video_score, image_score, audio_score)

        if max_score == 0:
            self.analysis.detected_category = 'unknown'
        elif video_score == max_score:
            self.analysis.detected_category = 'video'
        elif image_score == max_score:
            self.analysis.detected_category = 'image'
        else:
            self.analysis.detected_category = 'audio'

    def _calculate_total_size(self):
        """Calculate total estimated download size"""
        total_gb = 0.0

        for model in self.analysis.models:
            if model.estimated_size:
                # Extract numeric value
                size_str = model.estimated_size.lower().replace('~', '').replace('gb', '').replace(' ', '').strip()
                try:
                    if 'mb' in size_str:
                        total_gb += float(size_str.replace('mb', '')) / 1024
                    else:
                        total_gb += float(size_str)
                except ValueError:
                    pass

        self.analysis.total_estimated_size = total_gb

    def _calculate_confidence(self):
        """Calculate overall confidence score"""
        if not self.analysis.models:
            self.analysis.confidence_score = 0.0
            return

        total_confidence = sum(m.confidence for m in self.analysis.models)
        self.analysis.confidence_score = total_confidence / len(self.analysis.models)

    def _generate_suggestions(self):
        """Generate suggestions for improving the preset"""
        if self.analysis.detected_category == 'unknown':
            self.analysis.suggestions.append("Could not auto-detect category. Please specify manually.")

        if self.analysis.confidence_score < 0.5:
            self.analysis.suggestions.append("Some models could not be matched to known repositories. You may need to provide URLs manually.")

        if not self.analysis.models:
            self.analysis.suggestions.append("No model loading nodes detected. This workflow may not require models or use custom loaders.")

        # Check for missing common dependencies
        has_t5xxl = any('t5xxl' in m.filename.lower() for m in self.analysis.models)
        has_flux = any('flux' in m.filename.lower() for m in self.analysis.models)

        if has_flux and not has_t5xxl:
            self.analysis.suggestions.append("FLUX models typically require T5XXL text encoder. It may be missing from this workflow.")


def print_analysis(analysis: WorkflowAnalysis):
    """Print workflow analysis in a formatted way"""
    print("\n" + "=" * 70)
    print("COMFYUI WORKFLOW ANALYSIS")
    print("=" * 70)

    if analysis.workflow_name:
        print(f"\nWorkflow Name: {analysis.workflow_name}")

    print(f"\nDetected Category: {analysis.detected_category.upper()}")
    print(f"Confidence Score: {analysis.confidence_score:.2%}")
    print(f"Models Found: {len(analysis.models)}")
    print(f"Estimated Size: {analysis.total_estimated_size:.2f} GB")

    if analysis.models:
        print("\n" + "-" * 70)
        print("DETECTED MODELS:")
        print("-" * 70)

        for i, model in enumerate(analysis.models, 1):
            print(f"\n{i}. {model.filename}")
            print(f"   Type: {model.node_type}")
            print(f"   Category: {model.category}")
            print(f"   Path: {model.suggested_path}")
            print(f"   Confidence: {model.confidence:.0%}")

            if model.detected_url:
                print(f"   URL: {model.detected_url}")
            else:
                print(f"   URL: [NEEDS MANUAL INPUT]")

            print(f"   Size: {model.estimated_size}")

    if analysis.warnings:
        print("\n" + "-" * 70)
        print("WARNINGS:")
        print("-" * 70)
        for warning in analysis.warnings:
            print(f"  ⚠️  {warning}")

    if analysis.suggestions:
        print("\n" + "-" * 70)
        print("SUGGESTIONS:")
        print("-" * 70)
        for suggestion in analysis.suggestions:
            print(f"  💡 {suggestion}")

    print("\n" + "=" * 70)


def main():
    """Main entry point for command-line usage"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Parse ComfyUI workflow JSON files for preset creation"
    )
    parser.add_argument(
        "workflow_file",
        help="Path to ComfyUI workflow JSON file"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output JSON file for analysis results"
    )
    parser.add_argument(
        "-j", "--json",
        action="store_true",
        help="Output as JSON instead of formatted text"
    )

    args = parser.parse_args()

    # Parse workflow
    parser_instance = ComfyUIWorkflowParser()

    try:
        analysis = parser_instance.parse_workflow_file(args.workflow_file)

        if args.json:
            # Output as JSON
            import dataclasses

            def convert_to_dict(obj):
                if dataclasses.is_dataclass(obj):
                    return dataclasses.asdict(obj)
                elif isinstance(obj, list):
                    return [convert_to_dict(item) for item in obj]
                elif isinstance(obj, dict):
                    return {k: convert_to_dict(v) for k, v in obj.items()}
                else:
                    return obj

            analysis_dict = convert_to_dict(analysis)
            print(json.dumps(analysis_dict, indent=2))
        else:
            # Print formatted analysis
            print_analysis(analysis)

        # Save to file if requested
        if args.output:
            with open(args.output, 'w') as f:
                if args.json:
                    json.dump(analysis_dict, f, indent=2)
                else:
                    # Save as formatted text
                    from io import StringIO
                    import sys

                    old_stdout = sys.stdout
                    sys.stdout = StringIO()
                    print_analysis(analysis)
                    output = sys.stdout.getvalue()
                    sys.stdout = old_stdout

                    f.write(output)

            print(f"\n✅ Analysis saved to: {args.output}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
