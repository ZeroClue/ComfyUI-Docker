#!/usr/bin/env python3
"""
Dynamic Download Script Generator
Generates download functionality from YAML preset configuration
"""

import os
import sys
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add script directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from preset_manager.core import ModelManager
    from preset_updater import PresetUpdater
except ImportError:
    # Fallback for testing outside container
    print("[WARNING] Running outside container environment", file=sys.stderr)


class DownloadScriptGenerator:
    """Generates download functionality from YAML preset configuration"""

    def __init__(self, config_dir: str = "/workspace/config"):
        self.config_dir = Path(config_dir)
        self.presets_path = self.config_dir / "presets.yaml"
        self.schema_path = self.config_dir / "presets-schema.json"

    def load_presets(self) -> Dict[str, Any]:
        """Load presets from YAML configuration"""
        try:
            if not self.presets_path.exists():
                print(f"[ERROR] Presets file not found: {self.presets_path}")
                return {}

            with open(self.presets_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            if 'presets' not in config:
                print("[ERROR] Invalid presets configuration: missing 'presets' section")
                return {}

            return config.get('presets', {})

        except Exception as e:
            print(f"[ERROR] Failed to load presets: {e}")
            return {}

    def get_preset_urls(self, preset_id: str, presets: Dict) -> List[Dict[str, str]]:
        """Get download URLs for a specific preset"""
        if preset_id not in presets:
            print(f"[ERROR] Preset not found: {preset_id}")
            return []

        preset = presets[preset_id]
        files = preset.get('files', [])

        if not files:
            print(f"[WARNING] No files defined for preset: {preset_id}")
            return []

        # Convert files to list of {path, url, size} dicts
        result = []
        for file_info in files:
            if isinstance(file_info, dict):
                if 'path' in file_info and 'url' in file_info:
                    result.append({
                        'path': file_info['path'],
                        'url': file_info['url'],
                        'size': file_info.get('size', 'Unknown')
                    })
                else:
                    print(f"[WARNING] Invalid file definition in {preset_id}: missing path or url")
            elif isinstance(file_info, str):
                print(f"[WARNING] Legacy file format in {preset_id}: {file_info} (missing URL)")

        return result

    def generate_bash_function(self, preset_id: str, files: List[Dict[str, str]]) -> str:
        """Generate bash function for downloading preset files"""
        if not files:
            return f"        {preset_id})\n            echo \"No files available for preset {preset_id}\"\n            ;;\n"

        lines = [f"        {preset_id})"]
        lines.append(f'            echo "Preset: {preset_id}"')

        for file_info in files:
            path = file_info['path']
            url = file_info['url']
            # Extract directory from path
            directory = f"/workspace/ComfyUI/models/{os.path.dirname(path)}"
            lines.append(f'            download_if_missing "{url}" "{directory}"')

        lines.append("            ;;")
        lines.append("")

        return "\n".join(lines)

    def generate_download_script(self, preset_ids: List[str]) -> str:
        """Generate complete download script for specified presets"""
        presets = self.load_presets()
        if not presets:
            return "# Error: Could not load presets\n"

        script_lines = [
            "#!/bin/bash",
            "",
            "# Generated download script from YAML preset configuration",
            f"# Generated on: {os.popen('date -u +%Y-%m-%dT%H:%M:%SZ').read().strip()}",
            "",
            "WGET_OPTS=\"--show-progress\"",
            "",
            "if [[ \"$1\" == \"--quiet\" ]]; then",
            "    WGET_OPTS=\"-q\"",
            "    shift",
            "fi",
            "",
            "# download_if_missing <URL> <TARGET_DIR>",
            "download_if_missing() {",
            "    local url=\"$1\"",
            "    local dest_dir=\"$2\"",
            "",
            "    local filename",
            "    filename=$(basename \"$url\")",
            "    local filepath=\"$dest_dir/$filename\"",
            "",
            "    mkdir -p \"$dest_dir\"",
            "",
            "    if [ -f \"$filepath\" ]; then",
            "        echo \"File already exists: $filepath (skipping)\"",
            "        return",
            "    fi",
            "",
            "    echo \"Downloading: $filename → $dest_dir\"",
            "    ",
            "    local tmpdir=\"/workspace/tmp\"",
            "    mkdir -p \"$tmpdir\"",
            "    local tmpfile=\"$tmpdir/${filename}.part\"",
            "",
            "    if wget $WGET_OPTS -O \"$tmpfile\" \"$url\"; then",
            "        mv -f \"$tmpfile\" \"$filepath\"",
            "        echo \"Download completed: $filepath\"",
            "    else",
            "        echo \"Download failed: $url\"",
            "        rm -f \"$tmpfile\"",
            "        return 1",
            "    fi",
            "}",
            "",
            "IFS=',' read -ra PRESETS <<< \"$1\"",
            "",
            "echo \"**** Downloading presets from YAML configuration ****\"",
            "echo \"**** Presets: ${PRESETS[*]} ****\"",
            "",
            "for preset in \"${PRESETS[@]}\"; do",
            "    case \"${preset}\" in"
        ]

        # Generate case statements for each preset
        for preset_id in preset_ids:
            files = self.get_preset_urls(preset_id, presets)
            script_lines.append(self.generate_bash_function(preset_id, files))

        # Add default case
        script_lines.extend([
            "        *)",
            "            echo \"No matching preset for '${preset}', skipping.\"",
            "            ;;",
            "    esac",
            "done",
            "",
            "echo \"**** Preset download completed ****\""
        ])

        return "\n".join(script_lines)

    def list_available_presets(self) -> None:
        """List all available presets with their categories"""
        presets = self.load_presets()
        if not presets:
            print("No presets available")
            return

        print("Available presets:")
        print("=" * 60)

        # Group by category
        categories = {}
        for preset_id, preset_data in presets.items():
            category = preset_data.get('category', 'Unknown')
            if category not in categories:
                categories[category] = []
            categories[category].append((preset_id, preset_data))

        for category, category_presets in sorted(categories.items()):
            print(f"\n{category}:")
            print("-" * 40)
            for preset_id, preset_data in sorted(category_presets):
                name = preset_data.get('name', preset_id)
                size = preset_data.get('download_size', 'Unknown')
                file_count = len(preset_data.get('files', []))
                print(f"  {preset_id:<25} {name:<30} {size:<10} ({file_count} files)")

    def validate_preset(self, preset_id: str) -> bool:
        """Validate a specific preset"""
        presets = self.load_presets()
        if preset_id not in presets:
            print(f"[ERROR] Preset not found: {preset_id}")
            return False

        preset = presets[preset_id]
        files = preset.get('files', [])

        if not files:
            print(f"[ERROR] No files defined for preset: {preset_id}")
            return False

        valid_files = 0
        for i, file_info in enumerate(files):
            if isinstance(file_info, dict):
                if 'path' not in file_info:
                    print(f"[ERROR] File {i+1} missing 'path': {file_info}")
                    continue
                if 'url' not in file_info:
                    print(f"[ERROR] File {i+1} missing 'url': {file_info}")
                    continue
                valid_files += 1
            else:
                print(f"[WARNING] File {i+1} using legacy format: {file_info}")

        if valid_files == 0:
            print(f"[ERROR] No valid files found for preset: {preset_id}")
            return False

        print(f"[OK] Preset {preset_id} has {valid_files} valid files")
        return True

    def update_existing_scripts(self) -> None:
        """Update existing download scripts to use YAML configuration"""
        presets = self.load_presets()
        if not presets:
            print("[ERROR] Cannot update scripts: no presets loaded")
            return

        # Group presets by category
        video_presets = []
        image_presets = []
        audio_presets = []

        for preset_id, preset_data in presets.items():
            category = preset_data.get('category', '')
            preset_type = preset_data.get('type', '')

            if 'Video' in category or preset_type == 'video':
                video_presets.append(preset_id)
            elif 'Audio' in category or preset_type == 'audio':
                audio_presets.append(preset_id)
            elif 'Image' in category or preset_type == 'image':
                image_presets.append(preset_id)

        # Generate updated scripts
        scripts_dir = Path("/workspace/scripts")

        if video_presets:
            video_script = self.generate_download_script(video_presets)
            video_path = scripts_dir / "download_presets.yaml.sh"
            with open(video_path, 'w') as f:
                f.write(video_script)
            os.chmod(video_path, 0o755)
            print(f"[OK] Generated video script: {video_path} ({len(video_presets)} presets)")

        if image_presets:
            image_script = self.generate_download_script(image_presets)
            image_path = scripts_dir / "download_image_presets.yaml.sh"
            with open(image_path, 'w') as f:
                f.write(image_script)
            os.chmod(image_path, 0o755)
            print(f"[OK] Generated image script: {image_path} ({len(image_presets)} presets)")

        if audio_presets:
            audio_script = self.generate_download_script(audio_presets)
            audio_path = scripts_dir / "download_audio_presets.yaml.sh"
            with open(audio_path, 'w') as f:
                f.write(audio_script)
            os.chmod(audio_path, 0o755)
            print(f"[OK] Generated audio script: {audio_path} ({len(audio_presets)} presets)")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Dynamic download script generator")
    parser.add_argument("command", choices=["generate", "list", "validate", "update-scripts"],
                       help="Command to execute")
    parser.add_argument("--presets", help="Comma-separated list of preset IDs")
    parser.add_argument("--preset", help="Single preset ID to validate")
    parser.add_argument("--output", help="Output file path (for generate command)")

    args = parser.parse_args()

    generator = DownloadScriptGenerator()

    if args.command == "list":
        generator.list_available_presets()

    elif args.command == "validate":
        if not args.preset:
            print("[ERROR] --preset required for validate command")
            sys.exit(1)
        success = generator.validate_preset(args.preset)
        sys.exit(0 if success else 1)

    elif args.command == "generate":
        if not args.presets:
            print("[ERROR] --presets required for generate command")
            sys.exit(1)

        preset_ids = [p.strip() for p in args.presets.split(",")]
        script_content = generator.generate_download_script(preset_ids)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(script_content)
            os.chmod(args.output, 0o755)
            print(f"[OK] Generated script: {args.output}")
        else:
            print(script_content)

    elif args.command == "update-scripts":
        generator.update_existing_scripts()


if __name__ == "__main__":
    main()