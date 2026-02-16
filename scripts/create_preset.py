#!/usr/bin/env python3
"""
Unified Preset Creation System
Combines workflow parsing, preset building, and GitHub integration
"""

import sys
import os
import argparse
from pathlib import Path

# Add script directory to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from preset_workflow_parser import ComfyUIWorkflowParser, print_analysis
    from preset_builder import PresetBuilder, PresetConfig
    from preset_github_integration import PresetGitHubIntegration
except ImportError as e:
    print(f"Error importing modules: {e}", file=sys.stderr)
    sys.exit(1)


class PresetCreationSystem:
    """Unified preset creation system"""

    def __init__(self, config_dir: str = "/workspace/config"):
        self.config_dir = config_dir
        self.parser = ComfyUIWorkflowParser()
        self.builder = PresetBuilder(config_dir)
        self.github = PresetGitHubIntegration(config_dir + "/presets.yaml")

    def create_preset_from_workflow(
        self,
        workflow_file: str,
        name: str = None,
        category: str = None,
        description: str = None,
        use_case: str = None,
        tags: list = None,
        author: str = None,
        output_file: str = None,
        skip_github: bool = False,
        interactive: bool = False
    ) -> dict:
        """Complete preset creation workflow"""

        result = {
            'success': False,
            'stage': '',
            'errors': [],
            'warnings': [],
            'preset_id': None,
            'preset_file': None,
            'pr_url': None
        }

        # Stage 1: Parse workflow
        result['stage'] = 'parsing'
        try:
            analysis = self.parser.parse_workflow_file(workflow_file)

            if interactive:
                print("\n" + "=" * 70)
                print("WORKFLOW ANALYSIS")
                print("=" * 70)
                print_analysis(analysis)

                # Get user input
                print("\n" + "-" * 70)
                print("CONFIGURE PRESET")
                print("-" * 70)

                name = name or input(f"Preset name [{analysis.workflow_name or 'My Preset'}]: ").strip()
                if not name:
                    name = analysis.workflow_name or "My Preset"

                category_choice = category or input(f"Category (video/image/audio) [{analysis.detected_category}]: ").strip()
                if not category_choice:
                    category_choice = analysis.detected_category

                if not description:
                    description = input("Description: ").strip() or f"ComfyUI workflow for {category_choice} generation"

                if not use_case:
                    use_case = input("Use case: ").strip() or f"{category_choice.title()} generation workflow"

                tags_input = input("Tags (comma-separated, optional): ").strip()
                tags = tags_input.split(',') if tags_input else []

                if not author:
                    author = input("Author (optional): ").strip()

            else:
                # Auto-generate missing values
                name = name or analysis.workflow_name or "Custom Preset"
                category = category or analysis.detected_category or 'image'
                description = description or f"ComfyUI workflow for {category} generation"
                use_case = use_case or f"{category.title()} generation workflow"
                tags = tags or []
                author = author or ""

            # Map category to full name
            category_map = {
                'video': 'Video Generation',
                'image': 'Image Generation',
                'audio': 'Audio Generation'
            }

            full_category = category_map.get(category.lower(), category)

            # Stage 2: Build preset
            result['stage'] = 'building'

            config = PresetConfig(
                preset_name=name,
                category=full_category,
                preset_type=category.lower(),
                description=description,
                use_case=use_case,
                tags=tags,
                author=author
            )

            preset = self.builder.build_preset_from_analysis(analysis, config)

            # Validate preset
            is_valid, errors = self.builder.validate_preset(preset)
            if not is_valid:
                result['errors'].extend(errors)
                return result

            # Stage 3: Save preset
            result['stage'] = 'saving'

            preset_id = list(preset.keys())[0]
            result['preset_id'] = preset_id

            if not output_file:
                output_file = f"{preset_id.lower()}.yaml"

            yaml_content = self.builder.generate_yaml_output(preset, include_metadata=False)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(yaml_content)

            result['preset_file'] = output_file

            # Stage 4: GitHub submission (optional)
            if not skip_github:
                result['stage'] = 'github'

                has_git, git_msg = self.github.check_git_status()
                has_gh, gh_msg = self.github.check_gh_cli()

                if not has_git:
                    result['warnings'].append("Not in a git repository - skipping GitHub operations")
                elif not has_gh:
                    result['warnings'].append("GitHub CLI not available - skipping PR creation")
                else:
                    if interactive:
                        # Ask about GitHub submission
                        submit = input("\nSubmit to GitHub? (y/n): ").strip().lower()
                        if submit != 'y':
                            result['warnings'].append("GitHub submission skipped by user")
                            skip_github = True

                    if not skip_github:
                        github_username = input("GitHub username (for fork): ").strip() if interactive else None

                        success, messages = self.github.full_submission_workflow(
                            output_file,
                            preset_id,
                            name,
                            description,
                            'main',  # Always target main for now
                            github_username
                        )

                        for msg in messages:
                            if "✅" in msg or "❌" in msg:
                                if "PR created" in msg:
                                    result['pr_url'] = msg.split(": ")[1] if ": " in msg else None

                                if "❌" in msg:
                                    result['errors'].append(msg)
                                else:
                                    result['warnings'].append(msg)

            result['success'] = True
            result['stage'] = 'complete'

        except Exception as e:
            result['errors'].append(f"Error in {result['stage']} stage: {str(e)}")

        return result


def print_result(result: dict):
    """Print preset creation result"""
    print("\n" + "=" * 70)
    print("PRESET CREATION RESULT")
    print("=" * 70)

    if result['success']:
        print(f"\n✅ SUCCESS")
        print(f"\nPreset ID: {result['preset_id']}")

        if result['preset_file']:
            print(f"Preset file: {result['preset_file']}")

        if result['pr_url']:
            print(f"Pull request: {result['pr_url']}")

        if result['warnings']:
            print("\n⚠️  WARNINGS:")
            for warning in result['warnings']:
                print(f"  - {warning}")

        print("\n📋 Next steps:")
        if result['pr_url']:
            print("  1. Monitor your PR for review")
            print("  2. Address any feedback from maintainers")
        else:
            print("  1. Review the generated preset file")
            print("  2. Manually create a PR if needed:")
            print(f"     - Fork the repository")
            print(f"     - Create a branch: preset-{result['preset_id'].lower().replace('_', '-')}")
            print(f"     - Add your preset to config/presets.yaml")
            print(f"     - Create a pull request")

    else:
        print(f"\n❌ FAILED at stage: {result['stage']}")
        print("\nErrors:")
        for error in result['errors']:
            print(f"  - {error}")

    print("=" * 70)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Create ComfyUI presets from workflow files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python create_preset.py workflow.json -i

  # Quick preset creation
  python create_preset.py workflow.json -n "My Cool Preset" -c video

  # Full specification
  python create_preset.py workflow.json \\
    --name "My Preset" \\
    --category video \\
    --description "Amazing video generation" \\
    --use-case "High quality video output" \\
    --tags "fast,efficient" \\
    --author "Your Name" \\
    --output my_preset.yaml

  # Skip GitHub operations
  python create_preset.py workflow.json --skip-github
        """
    )

    parser.add_argument(
        "workflow_file",
        help="Path to ComfyUI workflow JSON file"
    )
    parser.add_argument(
        "-n", "--name",
        help="Preset name"
    )
    parser.add_argument(
        "-c", "--category",
        choices=['video', 'image', 'audio'],
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
        help="Interactive mode with prompts"
    )
    parser.add_argument(
        "--skip-github",
        action="store_true",
        help="Skip GitHub operations"
    )
    parser.add_argument(
        "--config-dir",
        default="/workspace/config",
        help="Configuration directory path"
    )

    args = parser.parse_args()

    # Check if workflow file exists
    if not os.path.exists(args.workflow_file):
        print(f"❌ Error: Workflow file not found: {args.workflow_file}", file=sys.stderr)
        sys.exit(1)

    # Create system
    system = PresetCreationSystem(args.config_dir)

    # Parse tags
    tags = args.tags.split(',') if args.tags else []

    # Create preset
    result = system.create_preset_from_workflow(
        workflow_file=args.workflow_file,
        name=args.name,
        category=args.category,
        description=args.description,
        use_case=args.use_case,
        tags=tags,
        author=args.author,
        output_file=args.output,
        skip_github=args.skip_github,
        interactive=args.interactive
    )

    # Print result
    print_result(result)

    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()
