#!/usr/bin/env python3
"""
GitHub Integration for Preset Creation
Handles creating pull requests for new presets to main or community-presets repositories
"""

import os
import sys
import subprocess
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class PresetGitHubIntegration:
    """Handle GitHub operations for preset submissions"""

    def __init__(self, preset_config_path: str = "/workspace/config/presets.yaml"):
        self.preset_config_path = Path(preset_config_path)
        self.main_repo = "ComfyUI-docker"  # Update with actual repo
        self.community_repo = "ComfyUI-docker-community-presets"  # Update with actual repo

    def check_git_status(self) -> Tuple[bool, str]:
        """Check if current directory is a git repository"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0, "Git repository found" if result.returncode == 0 else "Not a git repository"
        except Exception as e:
            return False, f"Error checking git status: {str(e)}"

    def check_gh_cli(self) -> Tuple[bool, str]:
        """Check if GitHub CLI (gh) is installed and authenticated"""
        try:
            result = subprocess.run(
                ['gh', 'auth', 'status'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return True, "GitHub CLI installed and authenticated"
            else:
                return False, "GitHub CLI installed but not authenticated. Run: gh auth login"
        except FileNotFoundError:
            return False, "GitHub CLI not installed. Install from: https://cli.github.com/"
        except Exception as e:
            return False, f"Error checking GitHub CLI: {str(e)}"

    def create_preset_branch(self, preset_id: str) -> Tuple[bool, str]:
        """Create a new git branch for the preset"""
        branch_name = f"preset-{preset_id.lower().replace('_', '-')}"

        try:
            # Check if on main branch
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                capture_output=True,
                text=True,
                timeout=10
            )
            current_branch = result.stdout.strip()

            # Stash changes if needed
            subprocess.run(['git', 'stash', 'push', '-m', 'WIP before preset branch'], capture_output=True, timeout=10)

            # Create and checkout new branch
            result = subprocess.run(
                ['git', 'checkout', '-b', branch_name],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return True, f"Created branch: {branch_name}"
            else:
                return False, f"Failed to create branch: {result.stderr}"

        except Exception as e:
            return False, f"Error creating branch: {str(e)}"

    def add_preset_to_config(self, preset_yaml_path: str, target_repo: str = "main") -> Tuple[bool, str]:
        """Add preset to the appropriate configuration file"""

        # Load the preset
        try:
            with open(preset_yaml_path, 'r', encoding='utf-8') as f:
                preset_data = yaml.safe_load(f)
        except Exception as e:
            return False, f"Error loading preset file: {str(e)}"

        # Determine target file
        if target_repo == "community":
            target_file = Path("config/community-presets.yaml")
        else:
            target_file = self.preset_config_path

        # Load existing config or create new
        if target_file.exists():
            with open(target_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {
                'metadata': {
                    'version': '2.0.0',
                    'last_updated': datetime.now().isoformat(),
                    'description': 'ComfyUI preset definitions',
                    'schema_version': '1.0'
                },
                'categories': {
                    'Video Generation': {'description': 'Video generation models', 'type': 'video'},
                    'Image Generation': {'description': 'Image generation models', 'type': 'image'},
                    'Audio Generation': {'description': 'Audio generation models', 'type': 'audio'}
                },
                'presets': {}
            }

        # Add preset to config
        config['presets'].update(preset_data)

        # Update metadata
        config['metadata']['last_updated'] = datetime.now().isoformat()
        config['metadata']['total_presets'] = len(config['presets'])

        # Save updated config
        try:
            target_file.parent.mkdir(parents=True, exist_ok=True)
            with open(target_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

            return True, f"Preset added to {target_file}"
        except Exception as e:
            return False, f"Error saving config: {str(e)}"

    def commit_changes(self, preset_id: str) -> Tuple[bool, str]:
        """Commit the preset changes"""
        try:
            # Add config file
            subprocess.run(['git', 'add', 'config/presets.yaml'], capture_output=True, timeout=10)

            # Commit with message
            commit_message = f"feat(presets): add {preset_id} preset"
            result = subprocess.run(
                ['git', 'commit', '-m', commit_message],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return True, "Changes committed"
            else:
                return False, f"Failed to commit: {result.stderr}"

        except Exception as e:
            return False, f"Error committing changes: {str(e)}"

    def push_to_fork(self, preset_id: str, username: Optional[str] = None) -> Tuple[bool, str]:
        """Push changes to forked repository"""
        branch_name = f"preset-{preset_id.lower().replace('_', '-')}"

        try:
            # Determine remote
            if username:
                remote_url = f"git@github.com:{username}/{self.main_repo}.git"
                remote_name = f"fork-{username}"

                # Check if remote exists
                result = subprocess.run(
                    ['git', 'remote', 'get-url', remote_name],
                    capture_output=True,
                    timeout=10
                )

                if result.returncode != 0:
                    # Add remote
                    subprocess.run(
                        ['git', 'remote', 'add', remote_name, remote_url],
                        capture_output=True,
                        timeout=10
                    )
            else:
                remote_name = "origin"

            # Push to remote
            result = subprocess.run(
                ['git', 'push', '-u', remote_name, branch_name],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                return True, f"Pushed to {remote_name}/{branch_name}"
            else:
                return False, f"Failed to push: {result.stderr}"

        except Exception as e:
            return False, f"Error pushing changes: {str(e)}"

    def create_pull_request(
        self,
        preset_id: str,
        preset_name: str,
        description: str,
        target_repo: str = "main"
    ) -> Tuple[bool, str]:
        """Create pull request using GitHub CLI"""
        branch_name = f"preset-{preset_id.lower().replace('_', '-')}"

        # Determine base branch and title
        base = "main"
        title = f"Add preset: {preset_name} ({preset_id})"

        # Create PR body
        body = f"""## Preset Summary

**Preset ID**: {preset_id}
**Name**: {preset_name}
**Type**: {target_repo}

## Description

{description}

## Checklist

- [x] Preset follows the configuration schema
- [x] All URLs are accessible
- [x] File sizes are accurate
- [x] Category and tags are appropriate
- [x] Use case is clearly defined

## Files Changed

- `config/presets.yaml`: Added new preset configuration

---

This PR was auto-generated by the ComfyUI Preset Builder.
"""

        try:
            # Check if gh is available
            has_gh, msg = self.check_gh_cli()
            if not has_gh:
                return False, f"Cannot create PR: {msg}"

            # Create PR using gh CLI
            result = subprocess.run([
                'gh', 'pr', 'create',
                '--base', base,
                '--head', branch_name,
                '--title', title,
                '--body', body
            ], capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                pr_url = result.stdout.strip()
                return True, f"PR created: {pr_url}"
            else:
                return False, f"Failed to create PR: {result.stderr}"

        except Exception as e:
            return False, f"Error creating PR: {str(e)}"

    def full_submission_workflow(
        self,
        preset_yaml_path: str,
        preset_id: str,
        preset_name: str,
        description: str,
        target_repo: str = "main",
        github_username: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """Execute full submission workflow"""

        messages = []

        # Check prerequisites
        is_git, git_msg = self.check_git_status()
        messages.append(f"Git: {'✅' if is_git else '❌'} {git_msg}")

        has_gh, gh_msg = self.check_gh_cli()
        messages.append(f"GitHub CLI: {'✅' if has_gh else '❌'} {gh_msg}")

        if not is_git:
            return False, messages

        # Create branch
        success, msg = self.create_preset_branch(preset_id)
        messages.append(f"Branch: {'✅' if success else '❌'} {msg}")
        if not success:
            return False, messages

        # Add preset to config
        success, msg = self.add_preset_to_config(preset_yaml_path, target_repo)
        messages.append(f"Config: {'✅' if success else '❌'} {msg}")
        if not success:
            return False, messages

        # Commit changes
        success, msg = self.commit_changes(preset_id)
        messages.append(f"Commit: {'✅' if success else '❌'} {msg}")
        if not success:
            return False, messages

        # Push to fork
        success, msg = self.push_to_fork(preset_id, github_username)
        messages.append(f"Push: {'✅' if success else '❌'} {msg}")
        if not success:
            return False, messages

        # Create PR if gh CLI is available
        if has_gh:
            success, msg = self.create_pull_request(preset_id, preset_name, description, target_repo)
            messages.append(f"PR: {'✅' if success else '❌'} {msg}")
        else:
            messages.append("PR: ⏭️  Skipped (GitHub CLI not available)")

        return True, messages


def interactive_submission():
    """Interactive mode for GitHub submission"""
    print("\n" + "=" * 70)
    print("GITHUB PRESET SUBMISSION")
    print("=" * 70)

    # Get preset file
    preset_file = input("\nEnter path to preset YAML file: ").strip()

    if not preset_file or not os.path.exists(preset_file):
        print("❌ Invalid preset file path")
        return

    # Load preset to get info
    try:
        with open(preset_file, 'r') as f:
            preset_data = yaml.safe_load(f)
            preset_id = list(preset_data.keys())[0]
            preset_info = preset_data[preset_id]
    except Exception as e:
        print(f"❌ Error loading preset: {e}")
        return

    print(f"\nPreset ID: {preset_id}")
    print(f"Name: {preset_info.get('name', 'Unknown')}")

    # Get GitHub username
    github_username = input("\nGitHub username (for fork): ").strip() or None

    # Choose target
    target_choice = input("\nTarget repository (main/community) [main]: ").strip().lower()

    if target_choice == 'community':
        target_repo = "community"
        print("ℹ️  Community presets go to community-presets repository")
    else:
        target_repo = "main"
        print("ℹ️  Core presets go to main repository")

    # Confirm
    confirm = input("\nProceed with submission? (y/n): ").strip().lower()

    if confirm != 'y':
        print("Submission cancelled")
        return

    # Execute workflow
    integration = PresetGitHubIntegration()

    print("\n" + "-" * 70)
    print("SUBMISSION PROGRESS")
    print("-" * 70)

    success, messages = integration.full_submission_workflow(
        preset_file,
        preset_id,
        preset_info.get('name', preset_id),
        preset_info.get('description', ''),
        target_repo,
        github_username
    )

    print("\n".join(messages))

    if success:
        print("\n✅ Submission successful!")
        if not any("PR created" in msg for msg in messages):
            print("\n📋 Manual steps remaining:")
            print("  1. Go to GitHub and create a pull request")
            print(f"  2. Compare branch: preset-{preset_id.lower().replace('_', '-')}")
            print("  3. Target: main")
    else:
        print("\n❌ Submission failed. Please check the errors above.")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="GitHub integration for preset submissions"
    )
    parser.add_argument(
        "preset_file",
        nargs='?',
        help="Path to preset YAML file"
    )
    parser.add_argument(
        "--preset-id",
        help="Preset ID (auto-detected from file if not provided)"
    )
    parser.add_argument(
        "--target",
        choices=['main', 'community'],
        default='main',
        help="Target repository"
    )
    parser.add_argument(
        "--github-username",
        help="GitHub username for fork"
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Interactive mode"
    )

    args = parser.parse_args()

    # Interactive mode
    if args.interactive or not args.preset_file:
        interactive_submission()
        return

    # Non-interactive mode
    if not os.path.exists(args.preset_file):
        print(f"❌ Preset file not found: {args.preset_file}")
        sys.exit(1)

    # Load preset
    try:
        with open(args.preset_file, 'r') as f:
            preset_data = yaml.safe_load(f)
            preset_id = args.preset_id or list(preset_data.keys())[0]
            preset_info = preset_data[preset_id]
    except Exception as e:
        print(f"❌ Error loading preset: {e}")
        sys.exit(1)

    # Execute workflow
    integration = PresetGitHubIntegration()

    success, messages = integration.full_submission_workflow(
        args.preset_file,
        preset_id,
        preset_info.get('name', preset_id),
        preset_info.get('description', ''),
        args.target,
        args.github_username
    )

    for msg in messages:
        print(msg)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
