#!/usr/bin/env python3
"""
Preset Download Status API
Provides status information for preset downloads to the dashboard
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime


def get_download_status() -> dict:
    """Get the current download status from the status file"""
    status_file = "/workspace/logs/preset_download_status.json"

    # Default status
    default_status = {
        "status": "not_started",
        "message": "No downloads configured",
        "progress": 0.0,
        "presets": [],
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    # Check if downloads are configured
    has_presets = any([
        os.environ.get("PRESET_DOWNLOAD", ""),
        os.environ.get("IMAGE_PRESET_DOWNLOAD", ""),
        os.environ.get("AUDIO_PRESET_DOWNLOAD", "")
    ])

    if not has_presets:
        return default_status

    # Check if status file exists
    if not os.path.exists(status_file):
        return {
            **default_status,
            "status": "pending",
            "message": "Downloads configured, waiting to start"
        }

    # Read status file
    try:
        with open(status_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {
            **default_status,
            "status": "error",
            "message": f"Error reading status: {str(e)}"
        }


def get_download_logs(lines: int = 50) -> list:
    """Get recent download log entries"""
    log_file = "/workspace/logs/preset_downloads.log"

    if not os.path.exists(log_file):
        return []

    try:
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            return [line.strip() for line in all_lines[-lines:]]
    except Exception:
        return []


def check_download_process() -> dict:
    """Check if download process is running"""
    pid_file = "/workspace/logs/preset_downloads.pid"

    if not os.path.exists(pid_file):
        return {"running": False, "pid": None}

    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())

        # Check if process is running
        try:
            os.kill(pid, 0)  # Send signal 0 to check if process exists
            return {"running": True, "pid": pid}
        except OSError:
            return {"running": False, "pid": pid}
    except Exception:
        return {"running": False, "pid": None}


def main():
    """Main entry point for CLI usage"""
    import argparse

    parser = argparse.ArgumentParser(description="Get preset download status")
    parser.add_argument("--format", choices=["json", "text"], default="json",
                       help="Output format")
    parser.add_argument("--logs", action="store_true",
                       help="Include recent log entries")
    parser.add_argument("--log-lines", type=int, default=50,
                       help="Number of log lines to include")

    args = parser.parse_args()

    status = get_download_status()
    process_info = check_download_process()

    result = {
        "status": status,
        "process": process_info,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    if args.logs:
        result["logs"] = get_download_logs(args.log_lines)

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print("Preset Download Status")
        print("=" * 40)
        print(f"Status: {status['status']}")
        print(f"Message: {status['message']}")
        print(f"Progress: {status['progress']:.1f}%")
        if status['presets']:
            print(f"Presets: {', '.join(status['presets'])}")
        print(f"Process Running: {process_info['running']}")
        if process_info['pid']:
            print(f"PID: {process_info['pid']}")


if __name__ == "__main__":
    main()
