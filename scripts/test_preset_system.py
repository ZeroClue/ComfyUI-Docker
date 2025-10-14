#!/usr/bin/env python3
"""
Automated Testing Framework for Preset System
Tests end-to-end functionality and integration
"""

import os
import sys
import tempfile
import subprocess
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add script directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from generate_download_scripts import DownloadScriptGenerator
    from unified_preset_downloader import UnifiedPresetDownloader
    from preset_validator import PresetSystemValidator
except ImportError as e:
    print(f"[ERROR] Failed to import required modules: {e}", file=sys.stderr)
    sys.exit(1)


class PresetSystemTester:
    """Automated testing framework for preset system"""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0}
        }

    def log_test(self, test_name: str, status: str, message: str = "", details: Dict = None):
        """Log test result"""
        self.test_results['tests'][test_name] = {
            'status': status,
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }

        self.test_results['summary']['total'] += 1
        if status == 'passed':
            self.test_results['summary']['passed'] += 1
            print(f"✅ {test_name}: {message}")
        elif status == 'failed':
            self.test_results['summary']['failed'] += 1
            print(f"❌ {test_name}: {message}")
        else:
            self.test_results['summary']['skipped'] += 1
            print(f"⏭️  {test_name}: {message}")

    def test_yaml_loading(self) -> bool:
        """Test YAML configuration loading"""
        try:
            generator = DownloadScriptGenerator(str(self.config_dir))
            presets = generator.load_presets()

            if not presets:
                self.log_test('yaml_loading', 'failed', 'No presets loaded')
                return False

            # Test structure
            sample_preset = list(presets.values())[0]
            required_fields = ['name', 'category', 'type', 'files']
            missing_fields = [f for f in required_fields if f not in sample_preset]

            if missing_fields:
                self.log_test('yaml_loading', 'failed', f'Missing fields: {missing_fields}')
                return False

            self.log_test('yaml_loading', 'passed', f'Loaded {len(presets)} presets')
            return True

        except Exception as e:
            self.log_test('yaml_loading', 'failed', f'Exception: {e}')
            return False

    def test_preset_validation(self) -> bool:
        """Test preset validation functionality"""
        try:
            downloader = UnifiedPresetDownloader()
            downloader.script_generator = DownloadScriptGenerator(str(self.config_dir))
            presets = downloader.script_generator.load_presets()

            if not presets:
                self.log_test('preset_validation', 'skipped', 'No presets to validate')
                return True

            # Test valid preset
            valid_preset_id = list(presets.keys())[0]
            validation = downloader.validate_presets([valid_preset_id])

            if not validation or 'valid' not in validation:
                self.log_test('preset_validation', 'failed', 'Validation returned invalid result')
                return False

            if valid_preset_id not in validation['valid']:
                self.log_test('preset_validation', 'failed', f'Valid preset marked as invalid: {valid_preset_id}')
                return False

            # Test invalid preset
            validation = downloader.validate_presets(['INVALID_PRESET_TEST'])

            if not validation or 'invalid' not in validation:
                self.log_test('preset_validation', 'failed', 'Invalid preset validation failed')
                return False

            if 'INVALID_PRESET_TEST' not in validation['invalid']:
                self.log_test('preset_validation', 'failed', 'Invalid preset not detected')
                return False

            self.log_test('preset_validation', 'passed', 'Preset validation working correctly')
            return True

        except Exception as e:
            self.log_test('preset_validation', 'failed', f'Exception: {e}')
            return False

    def test_script_generation(self) -> bool:
        """Test download script generation"""
        try:
            generator = DownloadScriptGenerator(str(self.config_dir))
            presets = generator.load_presets()

            if not presets:
                self.log_test('script_generation', 'skipped', 'No presets for script generation')
                return True

            # Test generating script for single preset
            sample_preset_id = list(presets.keys())[0]
            script_content = generator.generate_download_script([sample_preset_id])

            # Basic script validation
            required_elements = ['#!/bin/bash', 'download_if_missing', sample_preset_id]
            missing_elements = [elem for elem in required_elements if elem not in script_content]

            if missing_elements:
                self.log_test('script_generation', 'failed', f'Script missing elements: {missing_elements}')
                return False

            # Test script syntax
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(script_content)
                temp_script = f.name

            try:
                # Test bash syntax
                result = subprocess.run(['bash', '-n', temp_script], capture_output=True, text=True)
                if result.returncode != 0:
                    self.log_test('script_generation', 'failed', f'Bash syntax error: {result.stderr}')
                    return False
            finally:
                os.unlink(temp_script)

            self.log_test('script_generation', 'passed', 'Script generation valid')
            return True

        except Exception as e:
            self.log_test('script_generation', 'failed', f'Exception: {e}')
            return False

    def test_env_parsing(self) -> bool:
        """Test environment variable parsing"""
        try:
            downloader = UnifiedPresetDownloader()

            test_cases = [
                ("PRESET1,PRESET2,PRESET3", ["PRESET1", "PRESET2", "PRESET3"]),
                ("  PRESET1  ,  PRESET2  ,  ", ["PRESET1", "PRESET2"]),
                ("", []),
                ("SINGLE_PRESET", ["SINGLE_PRESET"]),
                ("PRESET1, PRESET2,PRESET3 , PRESET4", ["PRESET1", "PRESET2", "PRESET3", "PRESET4"])
            ]

            for input_val, expected in test_cases:
                result = downloader.parse_env_preset_list(input_val)
                if result != expected:
                    self.log_test('env_parsing', 'failed', f'Parse error: "{input_val}" -> {result}, expected {expected}')
                    return False

            self.log_test('env_parsing', 'passed', 'Environment parsing working correctly')
            return True

        except Exception as e:
            self.log_test('env_parsing', 'failed', f'Exception: {e}')
            return False

    def test_preset_urls(self) -> bool:
        """Test preset URL extraction"""
        try:
            generator = DownloadScriptGenerator(str(self.config_dir))
            presets = generator.load_presets()

            if not presets:
                self.log_test('preset_urls', 'skipped', 'No presets for URL testing')
                return True

            # Test a preset with files
            for preset_id, preset_data in presets.items():
                files = preset_data.get('files', [])
                if files:
                    urls = generator.get_preset_urls(preset_id, presets)

                    if not urls:
                        self.log_test('preset_urls', 'failed', f'No URLs extracted for preset {preset_id}')
                        return False

                    # Validate URL structure
                    for url_info in urls:
                        if not isinstance(url_info, dict):
                            self.log_test('preset_urls', 'failed', f'URL info not dict for {preset_id}')
                            return False

                        required_fields = ['path', 'url']
                        missing_fields = [f for f in required_fields if f not in url_info]
                        if missing_fields:
                            self.log_test('preset_urls', 'failed', f'URL missing fields: {missing_fields}')
                            return False

                        if not url_info['url'].startswith('http'):
                            self.log_test('preset_urls', 'failed', f'Invalid URL format: {url_info["url"]}')
                            return False

                    self.log_test('preset_urls', 'passed', f'URL extraction valid (tested {preset_id})')
                    return True

            self.log_test('preset_urls', 'skipped', 'No presets with files found')
            return True

        except Exception as e:
            self.log_test('preset_urls', 'failed', f'Exception: {e}')
            return False

    def test_integration_workflow(self) -> bool:
        """Test complete integration workflow"""
        try:
            # Test 1: Load configuration
            generator = DownloadScriptGenerator(str(self.config_dir))
            presets = generator.load_presets()
            if not presets:
                self.log_test('integration_workflow', 'skipped', 'No presets for integration test')
                return True

            # Test 2: Select a sample preset
            sample_preset_id = list(presets.keys())[0]
            sample_preset = presets[sample_preset_id]

            # Test 3: Generate download script
            script_content = generator.generate_download_script([sample_preset_id])
            if not script_content:
                self.log_test('integration_workflow', 'failed', 'Failed to generate script')
                return False

            # Test 4: Validate script syntax
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(script_content)
                temp_script = f.name

            try:
                result = subprocess.run(['bash', '-n', temp_script], capture_output=True, text=True)
                if result.returncode != 0:
                    self.log_test('integration_workflow', 'failed', f'Script syntax error: {result.stderr}')
                    return False
            finally:
                os.unlink(temp_script)

            # Test 5: Test unified downloader with preset
            downloader = UnifiedPresetDownloader()
            downloader.script_generator = DownloadScriptGenerator(str(self.config_dir))
            validation = downloader.validate_presets([sample_preset_id])

            if not validation or sample_preset_id not in validation.get('valid', []):
                self.log_test('integration_workflow', 'failed', f'Preset validation failed in integration')
                return False

            self.log_test('integration_workflow', 'passed', f'Integration workflow successful (tested {sample_preset_id})')
            return True

        except Exception as e:
            self.log_test('integration_workflow', 'failed', f'Exception: {e}')
            return False

    def test_error_handling(self) -> bool:
        """Test error handling and robustness"""
        try:
            # Test 1: Invalid config directory
            try:
                generator = DownloadScriptGenerator("/nonexistent/directory")
                presets = generator.load_presets()
                if presets:  # Should be empty
                    self.log_test('error_handling', 'failed', 'Should return empty presets for invalid directory')
                    return False
            except Exception:
                pass  # Expected

            # Test 2: Invalid preset list
            downloader = UnifiedPresetDownloader()
            validation = downloader.validate_presets(["", "   ", "INVALID_PRESET"])

            if not validation or "INVALID_PRESET" not in validation.get('invalid', []):
                self.log_test('error_handling', 'failed', 'Invalid preset handling failed')
                return False

            # Test 3: Empty YAML (create temporary)
            temp_dir = tempfile.mkdtemp()
            temp_yaml = Path(temp_dir) / "presets.yaml"

            try:
                with open(temp_yaml, 'w') as f:
                    f.write("metadata:\n  version: test\n\ncategories: {}\n\npresets: {}\n")

                generator = DownloadScriptGenerator(temp_dir)
                presets = generator.load_presets()

                if not isinstance(presets, dict):
                    self.log_test('error_handling', 'failed', 'Empty YAML handling failed')
                    return False

            finally:
                temp_yaml.unlink()
                os.rmdir(temp_dir)

            self.log_test('error_handling', 'passed', 'Error handling robust')
            return True

        except Exception as e:
            self.log_test('error_handling', 'failed', f'Exception: {e}')
            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests"""
        print("🧪 Starting Preset System Test Suite")
        print("=" * 50)

        tests = [
            self.test_yaml_loading,
            self.test_preset_validation,
            self.test_script_generation,
            self.test_env_parsing,
            self.test_preset_urls,
            self.test_integration_workflow,
            self.test_error_handling
        ]

        for test_func in tests:
            try:
                test_func()
            except Exception as e:
                self.log_test(test_func.__name__, 'failed', f'Test crashed: {e}')

        # Summary
        summary = self.test_results['summary']
        total = summary['total']
        passed = summary['passed']
        failed = summary['failed']
        skipped = summary['skipped']

        print("=" * 50)
        print(f"🏁 Test Suite Completed")
        print(f"📊 Total: {total}, Passed: {passed}, Failed: {failed}, Skipped: {skipped}")

        if failed == 0:
            print("🎉 All tests passed!")
            success_rate = 100
        else:
            success_rate = (passed / total) * 100 if total > 0 else 0
            print(f"⚠️  {failed} test(s) failed ({success_rate:.1f}% success rate)")

        # Add summary to results
        self.test_results['summary']['success_rate'] = success_rate
        self.test_results['summary']['success'] = failed == 0

        return self.test_results

    def save_report(self, filename: str, format: str = "json") -> None:
        """Save test report to file"""
        if format == "json":
            with open(filename, 'w') as f:
                json.dump(self.test_results, f, indent=2)
        else:
            with open(filename, 'w') as f:
                f.write("# Preset System Test Report\n\n")
                f.write(f"Generated: {self.test_results['timestamp']}\n\n")

                summary = self.test_results['summary']
                f.write(f"## Summary\n")
                f.write(f"- Total: {summary['total']}\n")
                f.write(f"- Passed: {summary['passed']}\n")
                f.write(f"- Failed: {summary['failed']}\n")
                f.write(f"- Skipped: {summary['skipped']}\n")
                f.write(f"- Success Rate: {summary.get('success_rate', 0):.1f}%\n\n")

                f.write("## Test Results\n\n")
                for test_name, result in self.test_results['tests'].items():
                    if test_name == 'timestamp':
                        continue

                    status_icon = {"passed": "✅", "failed": "❌", "skipped": "⏭️"}.get(result['status'], "❓")
                    f.write(f"### {test_name.replace('_', ' ').title()}\n")
                    f.write(f"Status: {status_icon} {result['status'].upper()}\n")
                    if result['message']:
                        f.write(f"Message: {result['message']}\n")
                    f.write("\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Automated preset system testing")
    parser.add_argument("--config-dir", default="config", help="Configuration directory path")
    parser.add_argument("--output", help="Output report file path")
    parser.add_argument("--format", choices=["json", "text"], default="text", help="Output format")

    args = parser.parse_args()

    tester = PresetSystemTester(args.config_dir)
    results = tester.run_all_tests()

    if args.output:
        tester.save_report(args.output, args.format)
        print(f"\n📄 Test report saved to: {args.output}")

    # Exit with appropriate code
    success = results['summary']['success']
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()