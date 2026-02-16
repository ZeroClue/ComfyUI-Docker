#!/usr/bin/env python3
"""
Preset Builder for ComfyUI Workflow Analysis
Generates preset YAML structures from workflow analysis
"""

import sys
import os
import json
import yaml
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field

# Import the workflow parser
try:
    from preset_workflow_parser import ComfyUIWorkflowParser, WorkflowAnalysis, ModelFile
except ImportError:
    print("Error: Could not import preset_workflow_parser", file=sys.stderr)
    sys.exit(1)


@dataclass
class PresetConfig:
    """Configuration for preset generation"""
    preset_id: str = ""
    preset_name: str = ""
    category: str = ""  # Video Generation, Image Generation, Audio Generation
    preset_type: str = ""  # video, image, audio
    description: str = ""
    use_case: str = ""
    tags: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    author: str = ""
    repo_target: str = "main"  # main or community-presets


class PresetBuilder:
    """Builds preset configurations from workflow analysis"""

    def __init__(self, config_dir: str = "/workspace/config"):
        self.config_dir = Path(config_dir)
        self.presets_path = self.config_dir / "presets.yaml"
        self.existing_presets = self._load_existing_presets()

    def _load_existing_presets(self) -> Dict:
        """Load existing presets to avoid duplicates"""
        try:
            if self.presets_path.exists():
                with open(self.presets_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    return config.get('presets', {})
        except Exception as e:
            print(f"Warning: Could not load existing presets: {e}")
        return {}

    def generate_preset_id(self, name: str, category: str = "") -> str:
        """Generate a unique preset ID from name"""
        # Remove special characters, convert to uppercase
        base_id = re.sub(r'[^a-zA-Z0-9\s]', '', name)
        base_id = re.sub(r'\s+', '_', base_id.strip()).upper()

        # Add category prefix if provided
        if category:
            prefix = category.upper()[0]  # V, I, or A
            base_id = f"{prefix}_{base_id}"

        # Ensure uniqueness
        counter = 1
        preset_id = base_id
        while preset_id in self.existing_presets:
            preset_id = f"{base_id}_{counter}"
            counter += 1

        return preset_id

    def build_preset_from_analysis(
        self,
        analysis: WorkflowAnalysis,
        config: PresetConfig
    ) -> Dict[str, Any]:
        """Build a complete preset configuration from workflow analysis"""

        # Auto-generate preset ID if not provided
        if not config.preset_id:
            config.preset_id = self.generate_preset_id(
                config.preset_name or analysis.workflow_name or "Custom",
                analysis.detected_category
            )

        # Map detected category to preset category
        category_mapping = {
            'video': 'Video Generation',
            'image': 'Image Generation',
            'audio': 'Audio Generation'
        }

        preset_category = config.category or category_mapping.get(
            analysis.detected_category,
            'Image Generation'  # Default fallback
        )

        preset_type = config.preset_type or analysis.detected_category or 'image'

        # Build file entries
        files = []
        for model in analysis.models:
            file_entry = {
                'path': model.suggested_path
            }

            if model.detected_url:
                file_entry['url'] = model.detected_url

            if model.estimated_size and model.estimated_size != "Unknown":
                file_entry['size'] = model.estimated_size

            files.append(file_entry)

        # Calculate total download size
        total_size_gb = analysis.total_estimated_size
        if total_size_gb < 1:
            download_size = f"{total_size_gb * 1024:.0f}MB"
        else:
            download_size = f"{total_size_gb:.1f}GB"

        # Generate description if not provided
        description = config.description
        if not description:
            description = f"ComfyUI workflow{' - ' + analysis.workflow_name if analysis.workflow_name else ''} for {preset_category.lower()}"

        # Generate use case if not provided
        use_case = config.use_case
        if not use_case:
            use_case = self._generate_use_case(preset_type, analysis)

        # Generate tags if not provided
        tags = config.tags if config.tags else self._generate_tags(preset_type, analysis)

        # Build the complete preset structure
        preset = {
            config.preset_id: {
                'name': config.preset_name or analysis.workflow_name or config.preset_id.replace('_', ' ').title(),
                'category': preset_category,
                'type': preset_type,
                'description': description,
                'download_size': download_size,
                'files': files,
                'use_case': use_case,
                'tags': tags
            }
        }

        # Add version info as metadata
        preset[config.preset_id]['version'] = config.version
        if config.author:
            preset[config.preset_id]['author'] = config.author

        return preset

    def _generate_use_case(self, preset_type: str, analysis: WorkflowAnalysis) -> str:
        """Generate a use case description based on detected models"""
        model_names = [m.filename for m in analysis.models]

        if preset_type == 'video':
            if any('i2v' in name.lower() for name in model_names):
                return "Convert static images to animated videos"
            elif any('t2v' in name.lower() or 'text' in name.lower() for name in model_names):
                return "Generate videos from text prompts"
            elif any('s2v' in name.lower() or 'audio' in name.lower() for name in model_names):
                return "Generate videos synchronized with audio"
            else:
                return "Advanced video generation workflow"
        elif preset_type == 'image':
            if any('edit' in name.lower() for name in model_names):
                return "Edit and modify existing images"
            elif any('xl' in name.lower() or 'sdxl' in name.lower() for name in model_names):
                return "High-resolution image generation"
            else:
                return "Professional image generation workflow"
        elif preset_type == 'audio':
            if any('music' in name.lower() for name in model_names):
                return "Generate music and audio compositions"
            elif any('tts' in name.lower() or 'speech' in name.lower() for name in model_names):
                return "Text-to-speech synthesis"
            else:
                return "Audio generation and processing"
        else:
            return "ComfyUI workflow for content generation"

    def _generate_tags(self, preset_type: str, analysis: WorkflowAnalysis) -> List[str]:
        """Generate tags based on detected models and workflow type"""
        tags = [preset_type]

        model_names = ' '.join([m.filename.lower() for m in analysis.models])

        # Add model-specific tags
        tag_keywords = {
            'ltx': ['ltx', 'efficient'],
            'wan': ['wan'],
            'flux': ['flux'],
            'sdxl': ['sdxl', 'stable'],
            'sd1.5': ['sd1.5', 'stable'],
            'hunyuan': ['hunyuan'],
            'mochi': ['mochi'],
            'cosmos': ['cosmos', 'nvidia'],
            'qwen': ['qwen', 'text'],
            'juggernaut': ['juggernaut', 'photorealistic'],
            'omnigen': ['omnigen', 'unified'],
            'ace': ['ace-step', 'music', 'commercial'],
            'musicgen': ['musicgen', 'music'],
            'bark': ['bark', 'tts'],
        }

        for keyword, tag_list in tag_keywords.items():
            if keyword in model_names:
                tags.extend(tag_list)

        # Add workflow-specific tags
        node_types = [m.node_type.lower() for m in analysis.models]

        if 'loraloader' in node_types:
            tags.append('lora')

        if any('i2v' in m.filename.lower() for m in analysis.models):
            tags.append('i2v')
            tags.append('image-to-video')

        if any('t2v' in m.filename.lower() for m in analysis.models):
            tags.append('t2v')
            tags.append('text-to-video')

        if any('s2v' in m.filename.lower() for m in analysis.models):
            tags.append('s2v')
            tags.append('sound-to-video')

        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)

        return unique_tags

    def validate_preset(self, preset: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate a preset configuration"""
        errors = []

        preset_data = list(preset.values())[0]

        # Check required fields
        required_fields = ['name', 'category', 'type', 'description', 'download_size', 'files', 'use_case', 'tags']
        for field in required_fields:
            if field not in preset_data:
                errors.append(f"Missing required field: {field}")

        # Validate category
        valid_categories = ['Video Generation', 'Image Generation', 'Audio Generation']
        if preset_data.get('category') not in valid_categories:
            errors.append(f"Invalid category: {preset_data.get('category')}")

        # Validate type
        valid_types = ['video', 'image', 'audio']
        if preset_data.get('type') not in valid_types:
            errors.append(f"Invalid type: {preset_data.get('type')}")

        # Validate files
        files = preset_data.get('files', [])
        if not files:
            errors.append("No files defined in preset")

        for i, file_entry in enumerate(files):
            if not isinstance(file_entry, dict):
                errors.append(f"File entry {i} is not a dictionary")
                continue

            if 'path' not in file_entry:
                errors.append(f"File entry {i} missing 'path' field")

        # Validate tags
        tags = preset_data.get('tags', [])
        if not isinstance(tags, list):
            errors.append("Tags must be a list")

        return len(errors) == 0, errors

    def generate_yaml_output(self, preset: Dict[str, Any], include_metadata: bool = True) -> str:
        """Generate YAML output for the preset"""

        if include_metadata:
            # Wrap in full config structure
            output = {
                'metadata': {
                    'version': '2.0.0',
                    'last_updated': datetime.now().isoformat(),
                    'description': 'Generated preset from ComfyUI workflow',
                    'schema_version': '1.0'
                },
                'categories': {
                    'Video Generation': {
                        'description': 'Video generation models and utilities',
                        'type': 'video'
                    },
                    'Image Generation': {
                        'description': 'Image generation models and utilities',
                        'type': 'image'
                    },
                    'Audio Generation': {
                        'description': 'Audio generation models and utilities',
                        'type': 'audio'
                    }
                },
                'presets': preset
            }
        else:
            output = preset

        return yaml.dump(output, default_flow_style=False, sort_keys=False, allow_unicode=True)


def interactive_builder():
    """Interactive mode for building presets"""
    print("\n" + "=" * 70)
    print("COMFYUI PRESET BUILDER - INTERACTIVE MODE")
    print("=" * 70)

    # Get workflow file
    workflow_file = input("\nEnter path to ComfyUI workflow JSON file: ").strip()

    if not workflow_file or not os.path.exists(workflow_file):
        print("❌ Invalid workflow file path")
        return

    # Parse workflow
    print("\n🔍 Parsing workflow...")
    parser = ComfyUIWorkflowParser()

    try:
        analysis = parser.parse_workflow_file(workflow_file)
        from preset_workflow_parser import print_analysis
        print_analysis(analysis)
    except Exception as e:
        print(f"❌ Error parsing workflow: {e}")
        return

    # Get preset configuration
    print("\n" + "-" * 70)
    print("PRESET CONFIGURATION")
    print("-" * 70)

    config = PresetConfig()

    config.preset_name = input(f"\nPreset name [{analysis.workflow_name or 'My Preset'}]: ").strip()
    if not config.preset_name:
        config.preset_name = analysis.workflow_name or "My Preset"

    config.category = input(f"Category (Video Generation/Image Generation/Audio Generation) [{analysis.detected_category.title()} Generation]: ").strip()
    if not config.category:
        category_map = {
            'video': 'Video Generation',
            'image': 'Image Generation',
            'audio': 'Audio Generation'
        }
        config.category = category_map.get(analysis.detected_category, 'Image Generation')

    config.description = input("\nDescription (optional): ").strip()
    config.use_case = input("Use case (optional): ").strip()
    config.author = input("Author (optional): ").strip()

    # Tags
    tags_input = input("Tags (comma-separated, optional): ").strip()
    if tags_input:
        config.tags = [tag.strip() for tag in tags_input.split(',')]

    # Build preset
    builder = PresetBuilder()
    preset = builder.build_preset_from_analysis(analysis, config)

    # Validate
    is_valid, errors = builder.validate_preset(preset)

    if not is_valid:
        print("\n❌ Validation errors:")
        for error in errors:
            print(f"  - {error}")
        return

    # Display result
    print("\n" + "-" * 70)
    print("GENERATED PRESET")
    print("-" * 70)

    preset_id = list(preset.keys())[0]
    preset_data = preset[preset_id]

    print(f"\nPreset ID: {preset_id}")
    print(f"Name: {preset_data['name']}")
    print(f"Category: {preset_data['category']}")
    print(f"Type: {preset_data['type']}")
    print(f"Description: {preset_data['description']}")
    print(f"Download Size: {preset_data['download_size']}")
    print(f"Use Case: {preset_data['use_case']}")
    print(f"Tags: {', '.join(preset_data['tags'])}")

    print("\nFiles:")
    for i, file_entry in enumerate(preset_data['files'], 1):
        print(f"\n  {i}. {file_entry['path']}")
        if 'url' in file_entry:
            print(f"     URL: {file_entry['url']}")
        else:
            print(f"     URL: [NEEDS MANUAL INPUT]")
        if 'size' in file_entry:
            print(f"     Size: {file_entry['size']}")

    # Save option
    save_choice = input("\n💾 Save preset to file? (y/n): ").strip().lower()

    if save_choice == 'y':
        output_file = input("Output file path (default: preset_output.yaml): ").strip()
        if not output_file:
            output_file = "preset_output.yaml"

        try:
            yaml_content = builder.generate_yaml_output(preset, include_metadata=False)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(yaml_content)

            print(f"\n✅ Preset saved to: {output_file}")

            # Ask about creating PR
            pr_choice = input("\n📋 Create GitHub PR for this preset? (y/n): ").strip().lower()
            if pr_choice == 'y':
                print("\n🔧 To create a PR, you'll need to:")
                print(f"  1. Fork the repository")
                print(f"  2. Add the preset from {output_file} to the appropriate location")
                print(f"  3. Create a pull request")
                print(f"\n  Preset ID: {preset_id}")
                print(f"  Category: {preset_data['category']}")

        except Exception as e:
            print(f"❌ Error saving preset: {e}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Build ComfyUI presets from workflow analysis"
    )
    parser.add_argument(
        "workflow_file",
        nargs='?',
        help="Path to ComfyUI workflow JSON file"
    )
    parser.add_argument(
        "-n", "--name",
        help="Preset name"
    )
    parser.add_argument(
        "-c", "--category",
        choices=['video', 'image', 'audio', 'Video Generation', 'Image Generation', 'Audio Generation'],
        help="Preset category"
    )
    parser.add_argument(
        "-d", "--description",
        help="Preset description"
    )
    parser.add_argument(
        "-u", "--use-case",
        help="Primary use case"
    )
    parser.add_argument(
        "-t", "--tags",
        help="Comma-separated tags"
    )
    parser.add_argument(
        "-a", "--author",
        help="Preset author"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output YAML file path"
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Interactive mode"
    )
    parser.add_argument(
        "--config-dir",
        default="/workspace/config",
        help="Configuration directory path"
    )

    args = parser.parse_args()

    # Interactive mode
    if args.interactive or not args.workflow_file:
        interactive_builder()
        return

    # Non-interactive mode
    if not os.path.exists(args.workflow_file):
        print(f"❌ Workflow file not found: {args.workflow_file}")
        sys.exit(1)

    # Parse workflow
    parser_instance = ComfyUIWorkflowParser()

    try:
        analysis = parser_instance.parse_workflow_file(args.workflow_file)
    except Exception as e:
        print(f"❌ Error parsing workflow: {e}")
        sys.exit(1)

    # Build config
    config = PresetConfig(
        preset_name=args.name or analysis.workflow_name,
        category=args.category,
        description=args.description,
        use_case=args.use_case,
        author=args.author,
        tags=args.tags.split(',') if args.tags else []
    )

    # Build preset
    builder = PresetBuilder(args.config_dir)
    preset = builder.build_preset_from_analysis(analysis, config)

    # Validate
    is_valid, errors = builder.validate_preset(preset)

    if not is_valid:
        print("❌ Validation errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    # Generate output
    output_file = args.output or "preset_output.yaml"

    try:
        yaml_content = builder.generate_yaml_output(preset, include_metadata=False)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(yaml_content)

        preset_id = list(preset.keys())[0]
        print(f"✅ Preset '{preset_id}' saved to: {output_file}")

    except Exception as e:
        print(f"❌ Error saving preset: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
