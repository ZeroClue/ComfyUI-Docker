#!/usr/bin/env python3
"""
ComfyUI Preset Updater
Handles downloading and updating preset configurations from GitHub
"""

import os
import sys
import json
import yaml
import shutil
import hashlib
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple, Any

class PresetUpdater:
    """Manages downloading and updating preset configurations from GitHub"""

    def __init__(self):
        # GitHub repository configuration
        self.github_repo = "zeroclue/ComfyUI-docker"
        self.github_branch = "main"
        self.presets_file = "config/presets.yaml"
        self.schema_file = "config/presets-schema.json"

        # Local paths
        self.workspace_dir = Path("/workspace")
        self.config_dir = self.workspace_dir / "config"
        self.local_presets_path = self.config_dir / "presets.yaml"
        self.local_schema_path = self.config_dir / "presets-schema.json"
        self.backup_dir = self.config_dir / "backups"
        self.version_file = self.config_dir / "presets_version.json"

        # GitHub API URLs
        self.presets_api_url = f"https://api.github.com/repos/{self.github_repo}/contents/{self.presets_file}?ref={self.github_branch}"
        self.schema_api_url = f"https://api.github.com/repos/{self.github_repo}/contents/{self.schema_file}?ref={self.github_branch}"
        self.presets_raw_url = f"https://raw.githubusercontent.com/{self.github_repo}/{self.github_branch}/{self.presets_file}"
        self.schema_raw_url = f"https://raw.githubusercontent.com/{self.github_repo}/{self.github_branch}/{self.schema_file}"

        # Ensure directories exist
        self.config_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def get_current_version(self) -> Dict[str, str]:
        """Get current local version information"""
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.log(f"Error reading version file: {e}", "ERROR")

        return {
            "presets_sha": "",
            "schema_sha": "",
            "last_updated": "",
            "version": "unknown"
        }

    def save_current_version(self, version_info: Dict[str, str]):
        """Save current version information"""
        try:
            with open(self.version_file, 'w') as f:
                json.dump(version_info, f, indent=2)
        except Exception as e:
            self.log(f"Error saving version file: {e}", "ERROR")

    def get_remote_sha(self, api_url: str) -> Optional[str]:
        """Get SHA hash of remote file from GitHub API"""
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('sha')
        except Exception as e:
            self.log(f"Error getting remote SHA from {api_url}: {e}", "ERROR")
            return None

    def download_file(self, url: str, local_path: Path) -> bool:
        """Download file from URL to local path"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Write to temporary file first
            temp_path = local_path.with_suffix('.tmp')
            with open(temp_path, 'wb') as f:
                f.write(response.content)

            # Move to final location
            temp_path.rename(local_path)
            self.log(f"Downloaded {local_path.name} successfully")
            return True

        except Exception as e:
            self.log(f"Error downloading {url}: {e}", "ERROR")
            return False

    def validate_yaml_against_schema(self, yaml_path: Path, schema_path: Path) -> Tuple[bool, str]:
        """Validate YAML file against JSON schema"""
        try:
            # Try to import jsonschema
            import jsonschema

            # Load YAML and schema
            with open(yaml_path, 'r') as f:
                yaml_data = yaml.safe_load(f)

            with open(schema_path, 'r') as f:
                schema_data = json.load(f)

            # Validate
            jsonschema.validate(instance=yaml_data, schema=schema_data)
            return True, "Validation successful"

        except ImportError:
            self.log("jsonschema not available, skipping validation", "WARNING")
            return True, "Validation skipped (jsonschema not available)"
        except Exception as e:
            return False, f"Validation failed: {str(e)}"

    def check_schema_migration_needed(self) -> bool:
        """Check if schema needs migration for backward compatibility"""
        if not self.local_schema_path.exists():
            return False

        try:
            with open(self.local_schema_path, 'r') as f:
                schema = json.load(f)

            # Check if metadata properties need to be added
            metadata_props = schema.get('properties', {}).get('metadata', {}).get('properties', {})

            # Check if new properties are missing
            needs_migration = (
                'total_presets' not in metadata_props or
                'new_presets_from_docs' not in metadata_props
            )

            if needs_migration:
                self.log("Schema missing new metadata properties, migration needed")

            return needs_migration

        except Exception as e:
            self.log(f"Error checking schema migration: {e}", "ERROR")
            return False

    def migrate_schema(self) -> bool:
        """Migrate schema to support new metadata properties"""
        try:
            with open(self.local_schema_path, 'r') as f:
                schema = json.load(f)

            # Get metadata properties section
            metadata_props = schema.get('properties', {}).get('metadata', {}).get('properties', {})

            # Add missing properties
            added_total_presets = False
            added_new_presets = False

            if 'total_presets' not in metadata_props:
                metadata_props['total_presets'] = {
                    'type': 'number',
                    'description': 'Total number of presets in configuration'
                }
                added_total_presets = True

            if 'new_presets_from_docs' not in metadata_props:
                metadata_props['new_presets_from_docs'] = {
                    'type': 'number',
                    'description': 'Number of new presets added from documentation'
                }
                added_new_presets = True

            # Write updated schema back to file
            with open(self.local_schema_path, 'w') as f:
                json.dump(schema, f, indent=2)

            if added_total_presets:
                self.log("✓ Added total_presets property to schema")
            if added_new_presets:
                self.log("✓ Added new_presets_from_docs property to schema")

            return added_total_presets or added_new_presets

        except Exception as e:
            self.log(f"Error migrating schema: {e}", "ERROR")
            return False

    def create_backup(self, file_path: Path) -> Optional[Path]:
        """Create backup of file"""
        if not file_path.exists():
            return None

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = self.backup_dir / backup_name

            shutil.copy2(file_path, backup_path)
            self.log(f"Created backup: {backup_path}")
            return backup_path

        except Exception as e:
            self.log(f"Error creating backup: {e}", "ERROR")
            return None

    def check_for_updates(self) -> Dict[str, Any]:
        """Check if updates are available without downloading"""
        self.log("Checking for preset updates...")

        current_version = self.get_current_version()
        remote_presets_sha = self.get_remote_sha(self.presets_api_url)
        remote_schema_sha = self.get_remote_sha(self.schema_api_url)

        if not remote_presets_sha or not remote_schema_sha:
            return {
                "success": False,
                "message": "Unable to check remote version information"
            }

        presets_update = remote_presets_sha != current_version.get("presets_sha", "")
        schema_update = remote_schema_sha != current_version.get("schema_sha", "")

        return {
            "success": True,
            "presets_update_available": presets_update,
            "schema_update_available": schema_update,
            "current_presets_sha": current_version.get("presets_sha", "unknown"),
            "remote_presets_sha": remote_presets_sha,
            "current_schema_sha": current_version.get("schema_sha", "unknown"),
            "remote_schema_sha": remote_schema_sha,
            "update_available": presets_update or schema_update
        }

    def update_presets(self, force: bool = False) -> Dict[str, Any]:
        """Update presets from GitHub"""
        self.log("Starting preset update process...")

        # Check for updates
        update_check = self.check_for_updates()

        if not update_check["success"]:
            return update_check

        if not update_check["update_available"] and not force:
            return {
                "success": True,
                "message": "No updates available",
                "presets_updated": False,
                "schema_updated": False
            }

        # Get current version
        current_version = self.get_current_version()

        # Create backups
        presets_backup = None
        schema_backup = None

        if self.local_presets_path.exists():
            presets_backup = self.create_backup(self.local_presets_path)

        if self.local_schema_path.exists():
            schema_backup = self.create_backup(self.local_schema_path)

        presets_updated = False
        schema_updated = False
        errors = []

        # Download schema first (needed for validation)
        if update_check["schema_update_available"] or force:
            self.log("Downloading updated schema...")
            if self.download_file(self.schema_raw_url, self.local_schema_path):
                schema_updated = True
            else:
                errors.append("Failed to download schema")

        # Check if schema migration is needed (fix for backward compatibility)
        if self.local_schema_path.exists():
            migration_needed = self.check_schema_migration_needed()
            if migration_needed:
                self.log("Schema migration needed for backward compatibility...")
                if self.migrate_schema():
                    self.log("Schema migration completed successfully")
                    schema_updated = True
                else:
                    errors.append("Schema migration failed")

        # Download presets
        if update_check["presets_update_available"] or force:
            self.log("Downloading updated presets...")
            if self.download_file(self.presets_raw_url, self.local_presets_path):
                # Validate presets against schema
                if self.local_schema_path.exists():
                    validation_result, validation_message = self.validate_yaml_against_schema(
                        self.local_presets_path, self.local_schema_path
                    )

                    if validation_result:
                        presets_updated = True
                        self.log(f"Presets validation: {validation_message}")
                    else:
                        errors.append(f"Presets validation failed: {validation_message}")
                        # Restore backup if validation failed
                        if presets_backup:
                            shutil.copy2(presets_backup, self.local_presets_path)
                            self.log("Restored presets backup due to validation failure")
                else:
                    presets_updated = True
                    self.log("Presets downloaded (schema not available for validation)")
            else:
                errors.append("Failed to download presets")

        # Update version information
        if presets_updated or schema_updated:
            remote_presets_sha = self.get_remote_sha(self.presets_api_url)
            remote_schema_sha = self.get_remote_sha(self.schema_api_url)

            new_version = {
                "presets_sha": remote_presets_sha or "",
                "schema_sha": remote_schema_sha or "",
                "last_updated": datetime.now().isoformat(),
                "version": "updated"
            }

            self.save_current_version(new_version)
            self.log("Version information updated")

        # Prepare result
        success = len(errors) == 0

        if success and (presets_updated or schema_updated):
            message = "Update completed successfully"
            if presets_updated:
                message += " (presets updated)"
            if schema_updated:
                message += " (schema updated)"
        elif not success:
            message = f"Update failed: {'; '.join(errors)}"
        else:
            message = "No updates were needed"

        return {
            "success": success,
            "message": message,
            "presets_updated": presets_updated,
            "schema_updated": schema_updated,
            "errors": errors,
            "backup_created": bool(presets_backup or schema_backup)
        }

    def get_update_history(self) -> Dict[str, Any]:
        """Get history of updates from backup files"""
        try:
            backup_files = list(self.backup_dir.glob("presets_*.yaml"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            history = []
            for backup_file in backup_files[:10]:  # Last 10 updates
                try:
                    stat = backup_file.stat()
                    timestamp = datetime.fromtimestamp(stat.st_mtime)
                    size = stat.st_size

                    history.append({
                        "timestamp": timestamp.isoformat(),
                        "filename": backup_file.name,
                        "size_bytes": size,
                        "size_mb": round(size / (1024 * 1024), 2)
                    })
                except Exception:
                    continue

            return {
                "success": True,
                "history": history,
                "total_backups": len(backup_files)
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error getting update history: {str(e)}",
                "history": []
            }

    def cleanup_old_backups(self, keep_count: int = 5) -> Dict[str, Any]:
        """Clean up old backup files, keeping only the most recent ones"""
        try:
            backup_files = list(self.backup_dir.glob("presets_*.yaml"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            removed_count = 0
            for backup_file in backup_files[keep_count:]:
                try:
                    backup_file.unlink()
                    removed_count += 1
                except Exception:
                    continue

            return {
                "success": True,
                "message": f"Cleaned up {removed_count} old backup files",
                "removed_count": removed_count,
                "kept_count": min(len(backup_files), keep_count)
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error cleaning up backups: {str(e)}",
                "removed_count": 0
            }

def main():
    """Command line interface for preset updater"""
    import argparse

    parser = argparse.ArgumentParser(description="ComfyUI Preset Updater")
    parser.add_argument("command", choices=["check", "update", "history", "cleanup"],
                       help="Command to execute")
    parser.add_argument("--force", action="store_true",
                       help="Force update even if no updates available")
    parser.add_argument("--keep", type=int, default=5,
                       help="Number of backups to keep when cleaning up (default: 5)")

    args = parser.parse_args()

    updater = PresetUpdater()

    if args.command == "check":
        result = updater.check_for_updates()

    elif args.command == "update":
        result = updater.update_presets(force=args.force)

    elif args.command == "history":
        result = updater.get_update_history()

    elif args.command == "cleanup":
        result = updater.cleanup_old_backups(keep_count=args.keep)

    # Output result as JSON for programmatic use
    print(json.dumps(result, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result.get("success", False) else 1)

if __name__ == "__main__":
    main()