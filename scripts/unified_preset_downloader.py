#!/usr/bin/env python3
"""
Unified Preset Downloader
Handles all preset downloads from YAML configuration with unified environment variable support

Features:
- Background download mode
- WebSocket progress tracking
- Environment variable integration
- Multi-category preset support (video, image, audio)
"""

import os
import sys
import yaml
import argparse
import json
import time
import threading
from pathlib import Path
from typing import List, Dict, Set, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# Add script directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from generate_download_scripts import DownloadScriptGenerator
except ImportError:
    print("[ERROR] Failed to import DownloadScriptGenerator", file=sys.stderr)
    sys.exit(1)


@dataclass
class DownloadProgress:
    """Track download progress for WebSocket updates"""
    preset_id: str
    preset_name: str
    total_files: int
    completed_files: int
    total_size: str
    downloaded_size: str
    status: str  # pending, downloading, completed, failed
    error_message: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None

    def to_dict(self):
        return asdict(self)


class ProgressTracker:
    """Track and report download progress with WebSocket support"""

    def __init__(self, progress_file: str = "/tmp/preset_download_progress.json"):
        self.progress_file = progress_file
        self.progress: Dict[str, DownloadProgress] = {}
        self.lock = threading.Lock()

    def start_preset(self, preset_id: str, preset_name: str, total_files: int, total_size: str):
        """Start tracking a preset download"""
        with self.lock:
            self.progress[preset_id] = DownloadProgress(
                preset_id=preset_id,
                preset_name=preset_name,
                total_files=total_files,
                completed_files=0,
                total_size=total_size,
                downloaded_size="0B",
                status="downloading",
                start_time=datetime.now().isoformat()
            )
            self._save_progress()

    def update_file(self, preset_id: str, completed_files: int, downloaded_size: str):
        """Update download progress for a preset"""
        with self.lock:
            if preset_id in self.progress:
                self.progress[preset_id].completed_files = completed_files
                self.progress[preset_id].downloaded_size = downloaded_size
                self._save_progress()

    def complete_preset(self, preset_id: str, success: bool = True, error: str = None):
        """Mark a preset download as complete"""
        with self.lock:
            if preset_id in self.progress:
                self.progress[preset_id].status = "completed" if success else "failed"
                self.progress[preset_id].end_time = datetime.now().isoformat()
                if error:
                    self.progress[preset_id].error_message = error
                self._save_progress()

    def get_progress(self, preset_id: str = None) -> Dict:
        """Get progress for specific preset or all presets"""
        with self.lock:
            if preset_id:
                return self.progress.get(preset_id, {}).to_dict() if preset_id in self.progress else {}
            return {pid: prog.to_dict() for pid, prog in self.progress.items()}

    def _save_progress(self):
        """Save progress to file for WebSocket reading"""
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(self.get_progress(), f, indent=2)
        except Exception as e:
            print(f"[WARN] Failed to save progress: {e}")

    def get_summary(self) -> Dict:
        """Get overall download summary"""
        with self.lock:
            total = len(self.progress)
            completed = sum(1 for p in self.progress.values() if p.status == "completed")
            failed = sum(1 for p in self.progress.values() if p.status == "failed")
            downloading = total - completed - failed

            return {
                "total_presets": total,
                "completed": completed,
                "failed": failed,
                "downloading": downloading,
                "progress_percentage": int((completed / total * 100) if total > 0 else 0),
                "timestamp": datetime.now().isoformat()
            }


class UnifiedPresetDownloader:
    """Handles unified preset downloads from environment variables"""

    def __init__(self, progress_file: str = "/tmp/preset_download_progress.json"):
        self.script_generator = DownloadScriptGenerator()
        self.presets = self.script_generator.load_presets()
        self.progress_tracker = ProgressTracker(progress_file)
        self.background_mode = False
        self.websocket_enabled = False

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

    def download_presets(self, preset_ids: List[str], quiet: bool = False, background: bool = False) -> bool:
        """Download specified presets using the script generator

        Args:
            preset_ids: List of preset IDs to download
            quiet: Suppress output
            background: Run in background mode (returns immediately, downloads in thread)

        Returns:
            True if download started successfully, False otherwise
        """
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

        # Background mode: start download thread and return immediately
        if background:
            return self._download_in_background(validation['valid'], quiet)

        # Foreground mode: download synchronously
        return self._download_sync(validation['valid'], quiet)

    def _download_in_background(self, preset_ids: List[str], quiet: bool = False) -> bool:
        """Start downloads in background thread"""
        import subprocess

        def background_worker():
            try:
                self._download_sync(preset_ids, quiet)
            except Exception as e:
                print(f"[ERROR] Background download failed: {e}")

        thread = threading.Thread(target=background_worker, daemon=True)
        thread.start()

        print(f"[INFO] Started background download for {len(preset_ids)} presets")
        print("[INFO] Check progress with: python3 /scripts/unified_preset_downloader.py progress")

        return True

    def _download_sync(self, preset_ids: List[str], quiet: bool = False) -> bool:
        """Download presets synchronously with progress tracking"""
        if not preset_ids:
            print("[INFO] No presets to download")
            return True

        # Initialize progress tracking for all presets
        for preset_id in preset_ids:
            preset_data = self.presets.get(preset_id, {})
            self.progress_tracker.start_preset(
                preset_id=preset_id,
                preset_name=preset_data.get('name', preset_id),
                total_files=len(preset_data.get('files', [])),
                total_size=preset_data.get('download_size', 'Unknown')
            )

        # Generate and execute download script
        try:
            script_content = self.script_generator.generate_download_script(preset_ids)

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
            cmd.append(",".join(preset_ids))

            if not quiet:
                print(f"[INFO] Downloading {len(preset_ids)} presets...")

            result = subprocess.run(cmd, capture_output=not quiet, text=True)

            # Clean up
            os.remove(temp_script)

            # Update progress based on result
            for preset_id in preset_ids:
                if result.returncode == 0:
                    self.progress_tracker.complete_preset(preset_id, success=True)
                else:
                    self.progress_tracker.complete_preset(preset_id, success=False, error=str(result.stderr))

            if result.returncode == 0:
                if not quiet:
                    print("[INFO] All presets downloaded successfully")
                return True
            else:
                if not quiet:
                    print(f"[ERROR] Download failed with return code {result.returncode}")
                    if result.stderr:
                        print(f"[ERROR] {result.stderr}")
                return False

        except Exception as e:
            if not quiet:
                print(f"[ERROR] Failed to download presets: {e}")
            # Mark all as failed
            for preset_id in preset_ids:
                self.progress_tracker.complete_preset(preset_id, success=False, error=str(e))
            return False

    def get_progress(self, preset_id: str = None) -> Dict:
        """Get download progress for specific preset or all presets

        Args:
            preset_id: Specific preset ID or None for all

        Returns:
            Progress dictionary
        """
        return self.progress_tracker.get_progress(preset_id)

    def get_progress_summary(self) -> Dict:
        """Get overall download summary

        Returns:
            Summary dictionary with total, completed, failed, downloading counts
        """
        return self.progress_tracker.get_summary()

    def watch_progress(self, interval: int = 2):
        """Watch and print download progress in real-time

        Args:
            interval: Update interval in seconds
        """
        import subprocess

        try:
            progress_file = "/tmp/preset_download_progress.json"

            if not os.path.exists(progress_file):
                print("[INFO] No download progress file found")
                return

            print("[INFO] Watching download progress (Ctrl+C to stop)...")
            print("=" * 60)

            while True:
                time.sleep(interval)

                if not os.path.exists(progress_file):
                    break

                with open(progress_file, 'r') as f:
                    progress = json.load(f)

                # Clear screen and print progress
                subprocess.run('clear' if os.name != 'nt' else 'cls', shell=True)

                print("Preset Download Progress:")
                print("=" * 60)

                for preset_id, data in progress.items():
                    status_emoji = {
                        'downloading': '⬇️',
                        'completed': '✅',
                        'failed': '❌'
                    }.get(data.get('status', 'downloading'), '⏳')

                    print(f"{status_emoji} {data.get('preset_name', preset_id)}")
                    print(f"   Files: {data.get('completed_files', 0)}/{data.get('total_files', 0)}")
                    print(f"   Size: {data.get('downloaded_size', '0B')} / {data.get('total_size', 'Unknown')}")
                    print(f"   Status: {data.get('status', 'unknown').capitalize()}")
                    print()

                summary = self.progress_tracker.get_summary()
                print("-" * 60)
                print(f"Total: {summary['total_presets']} | "
                      f"Completed: {summary['completed']} | "
                      f"Failed: {summary['failed']} | "
                      f"Progress: {summary['progress_percentage']}%")

                # Exit if all done
                if summary['downloading'] == 0:
                    print("\n[INFO] All downloads complete!")
                    break

        except KeyboardInterrupt:
            print("\n[INFO] Stopped watching progress")

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
    parser = argparse.ArgumentParser(
        description="Unified preset downloader with background mode and progress tracking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download presets from environment variables (foreground)
  python3 unified_preset_downloader.py download

  # Download in background mode
  python3 unified_preset_downloader.py download --background

  # Watch download progress
  python3 unified_preset_downloader.py progress --watch

  # Get progress summary
  python3 unified_preset_downloader.py progress

  # List available presets
  python3 unified_preset_downloader.py list

  # Show environment variable status
  python3 unified_preset_downloader.py status
        """
    )

    parser.add_argument("command", choices=["download", "list", "status", "validate", "progress", "watch"],
                       help="Command to execute")
    parser.add_argument("--presets", help="Comma-separated list of preset IDs (overrides env vars)")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress download output")
    parser.add_argument("--env-only", action="store_true", help="Only use environment variables (ignore --presets)")
    parser.add_argument("--background", "-b", action="store_true", help="Run downloads in background")
    parser.add_argument("--watch", "-w", action="store_true", help="Watch progress in real-time (for 'progress' command)")
    parser.add_argument("--interval", type=int, default=2, help="Progress update interval in seconds (default: 2)")
    parser.add_argument("--preset-id", help="Get progress for specific preset ID")

    args = parser.parse_args()

    # Initialize downloader
    progress_file = os.environ.get("PRESET_PROGRESS_FILE", "/tmp/preset_download_progress.json")
    downloader = UnifiedPresetDownloader(progress_file=progress_file)

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

        success = downloader.download_presets(preset_ids, quiet=args.quiet, background=args.background)

        if args.background:
            # Don't exit immediately in background mode
            print("[INFO] Background download started")
            print("[INFO] Monitor with: python3 /scripts/unified_preset_downloader.py progress --watch")

        sys.exit(0 if success else 1)

    elif args.command in ["progress", "watch"]:
        if args.watch or args.command == "watch":
            # Watch mode: real-time progress updates
            downloader.watch_progress(interval=args.interval)
        else:
            # Single progress query
            progress = downloader.get_progress(args.preset_id)

            if not progress:
                print("[INFO] No download progress found")
                print("[INFO] Start a download first with: python3 /scripts/unified_preset_downloader.py download")
                return

            if args.preset_id:
                # Single preset progress
                print(f"Preset Progress: {progress.get('preset_name', args.preset_id)}")
                print(f"  Status: {progress.get('status', 'unknown').capitalize()}")
                print(f"  Files: {progress.get('completed_files', 0)}/{progress.get('total_files', 0)}")
                print(f"  Size: {progress.get('downloaded_size', '0B')} / {progress.get('total_size', 'Unknown')}")
                if progress.get('error_message'):
                    print(f"  Error: {progress['error_message']}")
            else:
                # All presets progress
                print("Preset Download Progress:")
                print("=" * 60)

                for preset_id, data in progress.items():
                    status_emoji = {
                        'downloading': '⬇️',
                        'completed': '✅',
                        'failed': '❌'
                    }.get(data.get('status', 'downloading'), '⏳')

                    print(f"{status_emoji} {data.get('preset_name', preset_id)}")
                    print(f"   Files: {data.get('completed_files', 0)}/{data.get('total_files', 0)}")
                    print(f"   Size: {data.get('downloaded_size', '0B')} / {data.get('total_size', 'Unknown')}")
                    print()

                # Summary
                summary = downloader.get_progress_summary()
                print("-" * 60)
                print(f"Total: {summary['total_presets']} | "
                      f"Completed: {summary['completed']} | "
                      f"Failed: {summary['failed']} | "
                      f"Progress: {summary['progress_percentage']}%")


if __name__ == "__main__":
    main()