#!/usr/bin/env python3
"""
Unified Preset Downloader
Handles all preset downloads from YAML configuration with unified environment variable support
"""

import os
import sys
import yaml
import argparse
from pathlib import Path
from typing import List, Dict, Set

# Add script directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from generate_download_scripts import DownloadScriptGenerator
except ImportError:
    print("[ERROR] Failed to import DownloadScriptGenerator", file=sys.stderr)
    sys.exit(1)


class UnifiedPresetDownloader:
    """Handles unified preset downloads from environment variables"""

    def __init__(self):
        self.script_generator = DownloadScriptGenerator()
        self.presets = self.script_generator.load_presets()

    def parse_env_preset_list(self, env_value: str) -> List[str]:
        """Parse comma-separated preset list from environment variable"""
        if not env_value or env_value.strip() == "":
            return []

        # Split by comma and strip whitespace
        presets = [p.strip() for p in env_value.split(",")]
        # Remove empty entries
        return [p for p in presets if p]

    def get_all_presets_from_env(self) -> List[str]:
        """Get all presets from all environment variables"""
        all_presets = []

        # Parse each environment variable
        env_vars = [
            "PRESET_DOWNLOAD",           # Legacy video presets
            "IMAGE_PRESET_DOWNLOAD",     # Image presets
            "AUDIO_PRESET_DOWNLOAD",     # Audio presets
            "UNIFIED_PRESET_DOWNLOAD"    # New unified variable
        ]

        for env_var in env_vars:
            env_value = os.environ.get(env_var, "")
            if env_value:
                presets = self.parse_env_preset_list(env_value)
                if presets:
                    print(f"[INFO] Found {len(presets)} presets in {env_var}: {', '.join(presets)}")
                    all_presets.extend(presets)

        # Remove duplicates while preserving order
        seen = set()
        unique_presets = []
        for preset in all_presets:
            if preset not in seen:
                seen.add(preset)
                unique_presets.append(preset)

        return unique_presets

    def validate_presets(self, preset_ids: List[str]) -> Dict[str, List[str]]:
        """Validate preset IDs and categorize them"""
        valid_presets = []
        invalid_presets = []

        for preset_id in preset_ids:
            if preset_id in self.presets:
                valid_presets.append(preset_id)
            else:
                invalid_presets.append(preset_id)

        return {
            'valid': valid_presets,
            'invalid': invalid_presets
        }

    def download_presets(self, preset_ids: List[str], quiet: bool = False) -> bool:
        """Download specified presets using the script generator"""
        if not preset_ids:
            print("[INFO] No presets to download")
            return True

        # Validate presets
        validation = self.validate_presets(preset_ids)

        if validation['invalid']:
            print(f"[ERROR] Invalid presets found: {', '.join(validation['invalid'])}")
            if validation['valid']:
                print(f"[INFO] Proceeding with valid presets: {', '.join(validation['valid'])}")
            else:
                print("[ERROR] No valid presets to download")
                return False

        if not validation['valid']:
            print("[INFO] No valid presets to download")
            return True

        # Generate and execute download script
        try:
            script_content = self.script_generator.generate_download_script(validation['valid'])

            # Write script to temporary file
            temp_script = "/tmp/download_presets_temp.sh"
            with open(temp_script, 'w') as f:
                f.write(script_content)

            os.chmod(temp_script, 0o755)

            # Execute script
            import subprocess
            cmd = [temp_script]
            if quiet:
                cmd.append("--quiet")
            cmd.append(",".join(validation['valid']))

            print(f"[INFO] Downloading {len(validation['valid'])} presets...")

            result = subprocess.run(cmd, capture_output=not quiet, text=True)

            # Clean up
            os.remove(temp_script)

            if result.returncode == 0:
                print("[INFO] All presets downloaded successfully")
                return True
            else:
                print(f"[ERROR] Download failed with return code {result.returncode}")
                if result.stderr:
                    print(f"[ERROR] {result.stderr}")
                return False

        except Exception as e:
            print(f"[ERROR] Failed to download presets: {e}")
            return False

    def list_available_presets(self) -> None:
        """List all available presets grouped by category"""
        if not self.presets:
            print("No presets available")
            return

        print("Available presets:")
        print("=" * 80)

        # Group by category
        categories = {}
        for preset_id, preset_data in self.presets.items():
            category = preset_data.get('category', 'Unknown')
            if category not in categories:
                categories[category] = []
            categories[category].append((preset_id, preset_data))

        for category, category_presets in sorted(categories.items()):
            print(f"\n{category}:")
            print("-" * 60)
            for preset_id, preset_data in sorted(category_presets):
                name = preset_data.get('name', preset_id)
                size = preset_data.get('download_size', 'Unknown')
                file_count = len(preset_data.get('files', []))
                preset_type = preset_data.get('type', 'unknown')

                print(f"  {preset_id:<25} {name:<30} {size:<8} ({file_count} files, {preset_type})")

    def show_env_status(self) -> None:
        """Show current environment variable status"""
        print("Environment Variable Status:")
        print("=" * 50)

        env_vars = {
            "PRESET_DOWNLOAD": "Legacy video presets",
            "IMAGE_PRESET_DOWNLOAD": "Image presets",
            "AUDIO_PRESET_DOWNLOAD": "Audio presets",
            "UNIFIED_PRESET_DOWNLOAD": "Unified presets (new)"
        }

        for var, description in env_vars.items():
            value = os.environ.get(var, "")
            if value:
                presets = self.parse_env_preset_list(value)
                print(f"{var:<20} = {description:<25} ({len(presets)} presets)")
                for preset in presets:
                    print(f"{'':>20}   - {preset}")
            else:
                print(f"{var:<20} = {description:<25} (not set)")

        # Show combined result
        all_presets = self.get_all_presets_from_env()
        print(f"\n{'TOTAL':<20} = Combined presets ({len(all_presets)} unique)")
        if all_presets:
            print("Will download:", ", ".join(all_presets))


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Unified preset downloader")
    parser.add_argument("command", choices=["download", "list", "status", "validate"],
                       help="Command to execute")
    parser.add_argument("--presets", help="Comma-separated list of preset IDs (overrides env vars)")
    parser.add_argument("--quiet", action="store_true", help="Suppress download output")
    parser.add_argument("--env-only", action="store_true", help="Only use environment variables (ignore --presets)")

    args = parser.parse_args()

    downloader = UnifiedPresetDownloader()

    if args.command == "list":
        downloader.list_available_presets()

    elif args.command == "status":
        downloader.show_env_status()

    elif args.command == "validate":
        preset_ids = []
        if not args.env_only and args.presets:
            preset_ids = downloader.parse_env_preset_list(args.presets)
        else:
            preset_ids = downloader.get_all_presets_from_env()

        if not preset_ids:
            print("No presets to validate")
            return

        validation = downloader.validate_presets(preset_ids)

        if validation['valid']:
            print(f"Valid presets: {', '.join(validation['valid'])}")

        if validation['invalid']:
            print(f"Invalid presets: {', '.join(validation['invalid'])}")

        total = len(validation['valid']) + len(validation['invalid'])
        print(f"Validation complete: {len(validation['valid'])}/{total} valid")

    elif args.command == "download":
        preset_ids = []

        if not args.env_only and args.presets:
            # Use provided preset list
            preset_ids = downloader.parse_env_preset_list(args.presets)
            print(f"[INFO] Using provided presets: {', '.join(preset_ids)}")
        else:
            # Use environment variables
            preset_ids = downloader.get_all_presets_from_env()
            if preset_ids:
                print(f"[INFO] Using environment variable presets: {', '.join(preset_ids)}")

        success = downloader.download_presets(preset_ids, quiet=args.quiet)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()