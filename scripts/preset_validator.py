#!/usr/bin/env python3
"""
Comprehensive Preset System Validator
Validates YAML configuration, URLs, and system integrity
"""

import os
import sys
import yaml
import json
import requests
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

# Add script directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from generate_download_scripts import DownloadScriptGenerator
    from unified_preset_downloader import UnifiedPresetDownloader
except ImportError as e:
    print(f"[ERROR] Failed to import required modules: {e}", file=sys.stderr)
    sys.exit(1)


class PresetSystemValidator:
    """Comprehensive validation for the preset system"""

    def __init__(self, config_dir: str = "/workspace/config"):
        self.config_dir = Path(config_dir)
        self.presets_path = self.config_dir / "presets.yaml"
        self.schema_path = self.config_dir / "presets-schema.json"
        self.script_generator = DownloadScriptGenerator(config_dir)
        self.unified_downloader = UnifiedPresetDownloader()

        # Validation results
        self.results = {
            'yaml_config': {'status': 'unknown', 'errors': [], 'warnings': []},
            'schema_validation': {'status': 'unknown', 'errors': [], 'warnings': []},
            'url_validation': {'status': 'unknown', 'errors': [], 'warnings': [], 'failed_urls': []},
            'script_generation': {'status': 'unknown', 'errors': [], 'warnings': []},
            'unified_downloader': {'status': 'unknown', 'errors': [], 'warnings': []},
            'web_interface': {'status': 'unknown', 'errors': [], 'warnings': []},
            'fallback_systems': {'status': 'unknown', 'errors': [], 'warnings': []}
        }

    def log_result(self, category: str, status: str, message: str, is_error: bool = False):
        """Log validation result"""
        self.results[category]['status'] = status
        if is_error:
            self.results[category]['errors'].append(message)
            print(f"[ERROR] {category}: {message}")
        else:
            self.results[category]['warnings'].append(message)
            print(f"[WARNING] {category}: {message}")

    def validate_yaml_config(self) -> bool:
        """Validate YAML configuration file"""
        print("🔍 Validating YAML configuration...")

        try:
            if not self.presets_path.exists():
                self.log_result('yaml_config', 'error', f"Presets file not found: {self.presets_path}", True)
                return False

            # Try to load YAML
            with open(self.presets_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # Check required sections
            required_sections = ['metadata', 'categories', 'presets']
            for section in required_sections:
                if section not in config:
                    self.log_result('yaml_config', 'error', f"Missing required section: {section}", True)
                    return False

            # Validate metadata
            metadata = config['metadata']
            required_metadata = ['version', 'last_updated', 'description']
            for field in required_metadata:
                if field not in metadata:
                    self.log_result('yaml_config', 'warning', f"Missing metadata field: {field}")

            # Validate presets structure
            presets = config['presets']
            if not isinstance(presets, dict):
                self.log_result('yaml_config', 'error', "Presets section must be a dictionary", True)
                return False

            # Check for empty presets
            if len(presets) == 0:
                self.log_result('yaml_config', 'warning', "No presets defined in configuration")

            print(f"✅ YAML configuration valid ({len(presets)} presets)")
            self.results['yaml_config']['status'] = 'valid'
            return True

        except yaml.YAMLError as e:
            self.log_result('yaml_config', 'error', f"YAML parsing error: {e}", True)
            return False
        except Exception as e:
            self.log_result('yaml_config', 'error', f"Unexpected error: {e}", True)
            return False

    def validate_schema(self) -> bool:
        """Validate YAML against JSON schema"""
        print("🔍 Validating schema...")

        try:
            if not self.schema_path.exists():
                self.log_result('schema_validation', 'warning', "Schema file not found, skipping validation")
                return True

            # Load schema
            with open(self.schema_path, 'r') as f:
                schema = json.load(f)

            # Try to import jsonschema
            try:
                import jsonschema

                # Load and validate YAML
                with open(self.presets_path, 'r') as f:
                    config = yaml.safe_load(f)

                # Validate against schema
                jsonschema.validate(instance=config, schema=schema)
                print("✅ Schema validation passed")
                self.results['schema_validation']['status'] = 'valid'
                return True

            except ImportError:
                self.log_result('schema_validation', 'warning', "jsonschema not available, skipping validation")
                return True
            except jsonschema.ValidationError as e:
                self.log_result('schema_validation', 'error', f"Schema validation failed: {e.message}", True)
                return False

        except Exception as e:
            self.log_result('schema_validation', 'error', f"Schema validation error: {e}", True)
            return False

    def validate_urls(self, sample_size: int = 5) -> bool:
        """Validate a sample of URLs from presets"""
        print("🔍 Validating URLs...")

        try:
            presets = self.script_generator.load_presets()
            if not presets:
                self.log_result('url_validation', 'error', "No presets loaded for URL validation", True)
                return False

            total_files = 0
            valid_urls = 0
            failed_urls = []

            # Sample presets to check (to avoid checking all URLs)
            preset_items = list(presets.items())
            sample_presets = preset_items[:sample_size] if len(preset_items) > sample_size else preset_items

            for preset_id, preset_data in sample_presets:
                files = preset_data.get('files', [])
                for file_info in files:
                    if isinstance(file_info, dict) and 'url' in file_info:
                        total_files += 1
                        url = file_info['url']

                        try:
                            # Just check if the URL is accessible (HEAD request)
                            response = requests.head(url, timeout=10, allow_redirects=True)
                            if response.status_code < 400:
                                valid_urls += 1
                            else:
                                failed_urls.append((url, f"HTTP {response.status_code}"))
                        except requests.RequestException as e:
                            failed_urls.append((url, str(e)))

            success_rate = (valid_urls / total_files) * 100 if total_files > 0 else 0

            if failed_urls:
                self.log_result('url_validation', 'warning', f"{len(failed_urls)} URLs failed validation")
                for url, error in failed_urls[:3]:  # Show first 3 errors
                    self.results['url_validation']['failed_urls'].append((url, error))
                    print(f"  - {url}: {error}")

                if len(failed_urls) > 3:
                    print(f"  ... and {len(failed_urls) - 3} more")

            print(f"✅ URL validation complete: {valid_urls}/{total_files} URLs accessible ({success_rate:.1f}%)")

            if success_rate >= 80:
                self.results['url_validation']['status'] = 'valid'
                return True
            else:
                self.log_result('url_validation', 'error', f"Low URL success rate: {success_rate:.1f}%", True)
                return False

        except Exception as e:
            self.log_result('url_validation', 'error', f"URL validation error: {e}", True)
            return False

    def validate_script_generation(self) -> bool:
        """Validate script generation functionality"""
        print("🔍 Validating script generation...")

        try:
            presets = self.script_generator.load_presets()
            if not presets:
                self.log_result('script_generation', 'error', "No presets for script generation", True)
                return False

            # Test generating script for a sample preset
            sample_presets = list(presets.keys())[:3]  # Test first 3 presets

            for preset_id in sample_presets:
                try:
                    script_content = self.script_generator.generate_download_script([preset_id])

                    # Basic script validation
                    if not script_content.strip():
                        self.log_result('script_generation', 'error', f"Empty script generated for {preset_id}", True)
                        return False

                    if '#!/bin/bash' not in script_content:
                        self.log_result('script_generation', 'error', f"Invalid script format for {preset_id}", True)
                        return False

                except Exception as e:
                    self.log_result('script_generation', 'error', f"Script generation failed for {preset_id}: {e}", True)
                    return False

            print(f"✅ Script generation valid (tested {len(sample_presets)} presets)")
            self.results['script_generation']['status'] = 'valid'
            return True

        except Exception as e:
            self.log_result('script_generation', 'error', f"Script generation error: {e}", True)
            return False

    def validate_unified_downloader(self) -> bool:
        """Validate unified downloader functionality"""
        print("🔍 Validating unified downloader...")

        try:
            # Test environment variable parsing
            test_env_values = [
                "PRESET1,PRESET2,PRESET3",
                "  PRESET1  ,  PRESET2  ,  ",  # With whitespace
                "",  # Empty
                "SINGLE_PRESET"
            ]

            for env_value in test_env_values:
                try:
                    parsed = self.unified_downloader.parse_env_preset_list(env_value)
                    # Just ensure it doesn't crash
                except Exception as e:
                    self.log_result('unified_downloader', 'error', f"Env parsing failed: {e}", True)
                    return False

            # Test preset validation
            presets = self.unified_downloader.script_generator.load_presets()
            if presets:
                test_ids = list(presets.keys())[:2] + ["INVALID_PRESET"]
                validation = self.unified_downloader.validate_presets(test_ids)

                if not validation or 'valid' not in validation or 'invalid' not in validation:
                    self.log_result('unified_downloader', 'error', "Preset validation failed", True)
                    return False

            print("✅ Unified downloader valid")
            self.results['unified_downloader']['status'] = 'valid'
            return True

        except Exception as e:
            self.log_result('unified_downloader', 'error', f"Unified downloader error: {e}", True)
            return False

    def validate_fallback_systems(self) -> bool:
        """Validate fallback systems exist and are accessible"""
        print("🔍 Validating fallback systems...")

        fallback_issues = []

        # Check for legacy download scripts
        legacy_scripts = [
            "/scripts/download_presets.sh",
            "/scripts/download_image_presets.sh",
            "/scripts/download_audio_presets.sh"
        ]

        for script in legacy_scripts:
            if not os.path.exists(script):
                fallback_issues.append(f"Missing legacy script: {script}")

        # Check for preset updater
        if not os.path.exists("/scripts/preset_updater.py"):
            fallback_issues.append("Missing preset updater")

        # Check for preset manager core
        if not os.path.exists("/scripts/preset_manager/core.py"):
            fallback_issues.append("Missing preset manager core")

        if fallback_issues:
            for issue in fallback_issues:
                self.log_result('fallback_systems', 'warning', issue)

            # Don't fail validation for missing fallbacks, just warn
            print(f"⚠️  {len(fallback_issues)} fallback systems missing")
            self.results['fallback_systems']['status'] = 'partial'
            return True
        else:
            print("✅ All fallback systems available")
            self.results['fallback_systems']['status'] = 'valid'
            return True

    def run_full_validation(self, validate_urls: bool = False) -> Dict[str, Any]:
        """Run complete validation suite"""
        print("🚀 Starting comprehensive preset system validation")
        print("=" * 60)

        start_time = datetime.now()

        # Run all validations
        results = {
            'yaml_config': self.validate_yaml_config(),
            'schema_validation': self.validate_schema(),
            'script_generation': self.validate_script_generation(),
            'unified_downloader': self.validate_unified_downloader(),
            'fallback_systems': self.validate_fallback_systems()
        }

        if validate_urls:
            results['url_validation'] = self.validate_urls()

        # Calculate overall status
        all_valid = all(results.values())
        overall_status = 'valid' if all_valid else 'invalid'

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print("=" * 60)
        print(f"🏁 Validation completed in {duration:.1f} seconds")
        print(f"📊 Overall status: {'✅ VALID' if all_valid else '❌ INVALID'}")

        # Summary
        print("\n📋 Validation Summary:")
        for category, result in results.items():
            status_emoji = "✅" if result else "❌"
            print(f"  {status_emoji} {category.replace('_', ' ').title()}: {'PASS' if result else 'FAIL'}")

        # Add overall status to results
        self.results['overall'] = {
            'status': overall_status,
            'duration_seconds': duration,
            'timestamp': end_time.isoformat(),
            'individual_results': results
        }

        return self.results

    def generate_report(self) -> str:
        """Generate detailed validation report"""
        report = []
        report.append("# Preset System Validation Report")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")

        # Overall status
        overall = self.results.get('overall', {})
        report.append(f"## Overall Status: {overall.get('status', 'unknown').upper()}")
        report.append(f"Duration: {overall.get('duration_seconds', 0):.1f} seconds")
        report.append("")

        # Individual results
        for category, result in self.results.items():
            if category == 'overall':
                continue

            status = result.get('status', 'unknown')
            status_icon = {"valid": "✅", "invalid": "❌", "partial": "⚠️", "unknown": "❓"}.get(status, "❓")

            report.append(f"## {category.replace('_', ' ').title()}")
            report.append(f"Status: {status_icon} {status.upper()}")

            if result.get('errors'):
                report.append("### Errors:")
                for error in result['errors']:
                    report.append(f"- {error}")

            if result.get('warnings'):
                report.append("### Warnings:")
                for warning in result['warnings']:
                    report.append(f"- {warning}")

            if category == 'url_validation' and result.get('failed_urls'):
                report.append("### Failed URLs:")
                for url, error in result['failed_urls']:
                    report.append(f"- {url}: {error}")

            report.append("")

        return "\n".join(report)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Comprehensive preset system validator")
    parser.add_argument("--config-dir", default="/workspace/config",
                       help="Configuration directory path")
    parser.add_argument("--validate-urls", action="store_true",
                       help="Validate URLs (can be slow)")
    parser.add_argument("--output", help="Output report file path")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                       help="Output format")

    args = parser.parse_args()

    validator = PresetSystemValidator(args.config_dir)
    results = validator.run_full_validation(validate_urls=args.validate_urls)

    if args.output:
        if args.format == "json":
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
        else:
            with open(args.output, 'w') as f:
                f.write(validator.generate_report())
        print(f"\n📄 Report saved to: {args.output}")

    # Exit with appropriate code
    overall_status = results.get('overall', {}).get('status', 'invalid')
    sys.exit(0 if overall_status == 'valid' else 1)


if __name__ == "__main__":
    main()