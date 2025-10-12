#!/usr/bin/env python3
"""
ComfyUI Custom Nodes Validation Pipeline
Validates custom node installation, integration, and performance
"""

import os
import sys
import json
import time
import traceback
import subprocess
import importlib.util
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
import tempfile
import shutil

@dataclass
class ValidationResult:
    """Result of a validation test"""
    node_name: str
    test_type: str
    status: str  # 'pass', 'fail', 'warning'
    message: str
    details: Optional[Dict] = None
    execution_time: float = 0.0

@dataclass
class NodeInfo:
    """Information about a custom node"""
    name: str
    path: str
    has_init: bool
    has_requirements: bool
    has_install_script: bool
    node_class_count: int = 0
    file_count: int = 0
    size_mb: float = 0.0

class CustomNodesValidator:
    """Validates ComfyUI custom nodes installation"""

    def __init__(self, comfyui_path: str = "/workspace/ComfyUI"):
        self.comfyui_path = Path(comfyui_path)
        self.custom_nodes_path = self.comfyui_path / "custom_nodes"
        self.results: List[ValidationResult] = []
        self.start_time = time.time()

    def discover_nodes(self) -> List[NodeInfo]:
        """Discover all custom nodes in the custom_nodes directory"""
        nodes = []

        if not self.custom_nodes_path.exists():
            self.add_result("system", "discovery", "fail",
                          f"Custom nodes directory not found: {self.custom_nodes_path}")
            return nodes

        for node_path in self.custom_nodes_path.iterdir():
            if not node_path.is_dir():
                continue

            # Skip hidden directories and common non-node directories
            if node_path.name.startswith('.') or node_path.name in ['__pycache__']:
                continue

            node_info = self.analyze_node_structure(node_path)
            nodes.append(node_info)

        return nodes

    def analyze_node_structure(self, node_path: Path) -> NodeInfo:
        """Analyze the structure of a custom node"""
        name = node_path.name
        has_init = (node_path / "__init__.py").exists()
        has_requirements = (node_path / "requirements.txt").exists()
        has_install_script = (node_path / "install.py").exists()

        # Count Python files and estimate size
        py_files = list(node_path.rglob("*.py"))
        file_count = len(list(node_path.rglob("*")))

        size_mb = 0.0
        for file_path in node_path.rglob("*"):
            if file_path.is_file():
                try:
                    size_mb += file_path.stat().st_size / (1024 * 1024)
                except:
                    pass

        # Try to count node classes (basic heuristic)
        node_class_count = 0
        for py_file in py_files:
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                # Look for common ComfyUI node class patterns
                if 'class ' in content and 'NODE_CLASS_MAPPINGS' in content:
                    node_class_count += content.count('class ')
                elif '@classmethod' in content and 'def INPUT_TYPES' in content:
                    node_class_count += content.count('@classmethod')
            except:
                pass

        return NodeInfo(
            name=name,
            path=str(node_path),
            has_init=has_init,
            has_requirements=has_requirements,
            has_install_script=has_install_script,
            node_class_count=node_class_count,
            file_count=file_count,
            size_mb=size_mb
        )

    def validate_imports(self, node_info: NodeInfo) -> ValidationResult:
        """Validate that a node can be imported without errors"""
        start_time = time.time()
        node_name = node_info.name

        try:
            if not node_info.has_init:
                return ValidationResult(
                    node_name=node_name,
                    test_type="import",
                    status="warning",
                    message="No __init__.py file found",
                    execution_time=time.time() - start_time
                )

            init_file = Path(node_info.path) / "__init__.py"

            # Try to import the module
            spec = importlib.util.spec_from_file_location(node_name, init_file)
            if spec is None or spec.loader is None:
                return ValidationResult(
                    node_name=node_name,
                    test_type="import",
                    status="fail",
                    message="Could not create module spec",
                    execution_time=time.time() - start_time
                )

            # Create a temporary module to test import
            temp_module = importlib.util.module_from_spec(spec)

            # Add the node directory to Python path temporarily
            sys.path.insert(0, str(Path(node_info.path).parent))

            try:
                spec.loader.exec_module(temp_module)
                return ValidationResult(
                    node_name=node_name,
                    test_type="import",
                    status="pass",
                    message="Successfully imported",
                    execution_time=time.time() - start_time
                )
            except ImportError as e:
                return ValidationResult(
                    node_name=node_name,
                    test_type="import",
                    status="warning",
                    message=f"Import error (may be normal): {str(e)[:100]}",
                    execution_time=time.time() - start_time
                )
            except Exception as e:
                return ValidationResult(
                    node_name=node_name,
                    test_type="import",
                    status="fail",
                    message=f"Import failed: {str(e)[:100]}",
                    details={"error_type": type(e).__name__},
                    execution_time=time.time() - start_time
                )
            finally:
                # Clean up Python path
                if str(Path(node_info.path).parent) in sys.path:
                    sys.path.remove(str(Path(node_info.path).parent))

        except Exception as e:
            return ValidationResult(
                node_name=node_name,
                test_type="import",
                status="fail",
                message=f"Validation error: {str(e)[:100]}",
                execution_time=time.time() - start_time
            )

    def validate_dependencies(self, node_info: NodeInfo) -> ValidationResult:
        """Validate that node dependencies are properly installed"""
        start_time = time.time()
        node_name = node_info.name

        try:
            if not node_info.has_requirements:
                return ValidationResult(
                    node_name=node_name,
                    test_type="dependencies",
                    status="pass",
                    message="No requirements.txt file (may not need additional dependencies)",
                    execution_time=time.time() - start_time
                )

            req_file = Path(node_info.path) / "requirements.txt"

            # Read requirements
            requirements = []
            try:
                with open(req_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and not line.startswith('-'):
                            requirements.append(line)
            except Exception as e:
                return ValidationResult(
                    node_name=node_name,
                    test_type="dependencies",
                    status="warning",
                    message=f"Could not read requirements.txt: {str(e)}",
                    execution_time=time.time() - start_time
                )

            if not requirements:
                return ValidationResult(
                    node_name=node_name,
                    test_type="dependencies",
                    status="pass",
                    message="Empty requirements.txt",
                    execution_time=time.time() - start_time
                )

            # Check if requirements can be imported (basic check)
            missing_deps = []
            for req in requirements:
                # Extract package name (basic extraction)
                pkg_name = req.split('[')[0].split('>')[0].split('<')[0].split('=')[0].split('!')[0]
                pkg_name = pkg_name.strip().replace('-', '_')

                try:
                    __import__(pkg_name)
                except ImportError:
                    missing_deps.append(pkg_name)

            if missing_deps:
                return ValidationResult(
                    node_name=node_name,
                    test_type="dependencies",
                    status="fail",
                    message=f"Missing dependencies: {', '.join(missing_deps[:5])}",
                    details={"missing_deps": missing_deps, "total_requirements": len(requirements)},
                    execution_time=time.time() - start_time
                )
            else:
                return ValidationResult(
                    node_name=node_name,
                    test_type="dependencies",
                    status="pass",
                    message=f"All {len(requirements)} dependencies available",
                    execution_time=time.time() - start_time
                )

        except Exception as e:
            return ValidationResult(
                node_name=node_name,
                test_type="dependencies",
                status="fail",
                message=f"Dependency validation error: {str(e)[:100]}",
                execution_time=time.time() - start_time
            )

    def validate_integration(self, node_info: NodeInfo) -> ValidationResult:
        """Validate node integration with ComfyUI"""
        start_time = time.time()
        node_name = node_info.name

        try:
            # Check for common ComfyUI integration patterns
            init_file = Path(node_info.path) / "__init__.py"

            if not init_file.exists():
                return ValidationResult(
                    node_name=node_name,
                    test_type="integration",
                    status="warning",
                    message="No __init__.py for integration check",
                    execution_time=time.time() - start_time
                )

            content = init_file.read_text(encoding='utf-8', errors='ignore')

            # Look for integration patterns
            integration_indicators = {
                "NODE_CLASS_MAPPINGS": "Node class mapping found",
                "WEB_DIRECTORY": "Web interface integration found",
                "__all__": "Module exports defined",
                "load": "Load function found",
                "register_node": "Node registration found"
            }

            found_patterns = []
            for pattern, description in integration_indicators.items():
                if pattern in content:
                    found_patterns.append(description)

            if not found_patterns:
                return ValidationResult(
                    node_name=node_name,
                    test_type="integration",
                    status="warning",
                    message="No obvious ComfyUI integration patterns found",
                    details={"checked_patterns": list(integration_indicators.keys())},
                    execution_time=time.time() - start_time
                )

            return ValidationResult(
                node_name=node_name,
                test_type="integration",
                status="pass",
                message=f"Found {len(found_patterns)} integration patterns",
                details={"patterns": found_patterns},
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return ValidationResult(
                node_name=node_name,
                test_type="integration",
                status="fail",
                message=f"Integration validation error: {str(e)[:100]}",
                execution_time=time.time() - start_time
            )

    def validate_performance(self, node_info: NodeInfo) -> ValidationResult:
        """Basic performance validation"""
        start_time = time.time()
        node_name = node_info.name

        try:
            # Performance indicators
            size_score = "good" if node_info.size_mb < 50 else "large" if node_info.size_mb < 200 else "very_large"
            file_score = "good" if node_info.file_count < 100 else "moderate" if node_info.file_count < 500 else "complex"

            warnings = []
            if node_info.size_mb > 500:
                warnings.append(f"Very large node: {node_info.size_mb:.1f}MB")
            if node_info.file_count > 1000:
                warnings.append(f"Many files: {node_info.file_count}")
            if node_info.node_class_count > 50:
                warnings.append(f"Many node classes: {node_info.node_class_count}")

            status = "pass"
            if warnings:
                status = "warning" if len(warnings) == 1 else "fail"

            return ValidationResult(
                node_name=node_name,
                test_type="performance",
                status=status,
                message=f"Size: {size_score}, Files: {file_score}" + (f", Warnings: {len(warnings)}" if warnings else ""),
                details={
                    "size_mb": node_info.size_mb,
                    "file_count": node_info.file_count,
                    "node_class_count": node_info.node_class_count,
                    "warnings": warnings
                },
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return ValidationResult(
                node_name=node_name,
                test_type="performance",
                status="fail",
                message=f"Performance validation error: {str(e)[:100]}",
                execution_time=time.time() - start_time
            )

    def add_result(self, node_name: str, test_type: str, status: str, message: str, details: Optional[Dict] = None):
        """Add a validation result"""
        self.results.append(ValidationResult(
            node_name=node_name,
            test_type=test_type,
            status=status,
            message=message,
            details=details,
            execution_time=0.0
        ))

    def run_all_validations(self) -> Dict:
        """Run all validations on discovered nodes"""
        print("🔍 Starting ComfyUI custom nodes validation...")
        self.start_time = time.time()

        # Discover nodes
        nodes = self.discover_nodes()
        self.add_result("system", "discovery", "pass", f"Found {len(nodes)} custom nodes")

        if not nodes:
            return self.generate_report()

        # Validate each node
        for node_info in nodes:
            print(f"🔍 Validating {node_info.name}...")

            # Run all validation types
            validations = [
                self.validate_imports(node_info),
                self.validate_dependencies(node_info),
                self.validate_integration(node_info),
                self.validate_performance(node_info)
            ]

            for validation in validations:
                self.results.append(validation)

        return self.generate_report()

    def generate_report(self) -> Dict:
        """Generate a comprehensive validation report"""
        total_time = time.time() - self.start_time

        # Group results by node and test type
        results_by_node = {}
        results_by_test = {}

        for result in self.results:
            if result.node_name not in results_by_node:
                results_by_node[result.node_name] = []
            results_by_node[result.node_name].append(result)

            if result.test_type not in results_by_test:
                results_by_test[result.test_type] = []
            results_by_test[result.test_type].append(result)

        # Calculate statistics
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == 'pass'])
        failed_tests = len([r for r in self.results if r.status == 'fail'])
        warning_tests = len([r for r in self.results if r.status == 'warning'])

        # Find problematic nodes
        failed_nodes = set()
        warning_nodes = set()

        for result in self.results:
            if result.status == 'fail' and result.node_name != 'system':
                failed_nodes.add(result.node_name)
            elif result.status == 'warning' and result.node_name != 'system':
                warning_nodes.add(result.node_name)

        report = {
            "summary": {
                "total_nodes": len(results_by_node) - (1 if 'system' in results_by_node else 0),
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "warning_tests": warning_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "validation_time": total_time
            },
            "nodes": {},
            "test_results": {},
            "failed_nodes": list(failed_nodes),
            "warning_nodes": list(warning_nodes),
            "recommendations": self.generate_recommendations(failed_nodes, warning_nodes)
        }

        # Add detailed results for each node
        for node_name, node_results in results_by_node.items():
            if node_name == 'system':
                continue

            report["nodes"][node_name] = {
                "test_count": len(node_results),
                "passed": len([r for r in node_results if r.status == 'pass']),
                "failed": len([r for r in node_results if r.status == 'fail']),
                "warnings": len([r for r in node_results if r.status == 'warning']),
                "tests": []
            }

            for result in node_results:
                report["nodes"][node_name]["tests"].append({
                    "type": result.test_type,
                    "status": result.status,
                    "message": result.message,
                    "execution_time": result.execution_time,
                    "details": result.details
                })

        # Add test type summaries
        for test_type, test_results in results_by_test.items():
            report["test_results"][test_type] = {
                "total": len(test_results),
                "passed": len([r for r in test_results if r.status == 'pass']),
                "failed": len([r for r in test_results if r.status == 'fail']),
                "warnings": len([r for r in test_results if r.status == 'warning'])
            }

        return report

    def generate_recommendations(self, failed_nodes: Set[str], warning_nodes: Set[str]) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        if failed_nodes:
            recommendations.append(f"URGENT: Fix {len(failed_nodes)} failing nodes: {', '.join(list(failed_nodes)[:3])}")

        if warning_nodes:
            recommendations.append(f"Review {len(warning_nodes)} nodes with warnings: {', '.join(list(warning_nodes)[:3])}")

        # Test-specific recommendations
        import_failures = [r for r in self.results if r.test_type == 'import' and r.status == 'fail']
        if import_failures:
            recommendations.append(f"Check import errors in {len(import_failures)} nodes")

        dep_failures = [r for r in self.results if r.test_type == 'dependencies' and r.status == 'fail']
        if dep_failures:
            recommendations.append(f"Install missing dependencies for {len(dep_failures)} nodes")

        perf_issues = [r for r in self.results if r.test_type == 'performance' and r.status != 'pass']
        if perf_issues:
            recommendations.append(f"Optimize performance issues in {len(perf_issues)} nodes")

        if not recommendations:
            recommendations.append("All validations passed successfully!")

        return recommendations

    def print_summary(self, report: Dict):
        """Print a summary of the validation results"""
        print("\n" + "="*80)
        print("COMFYUI CUSTOM NODES VALIDATION REPORT")
        print("="*80)

        summary = report['summary']
        print(f"\nSUMMARY:")
        print(f"  Total Nodes: {summary['total_nodes']}")
        print(f"  Total Tests: {summary['total_tests']}")
        print(f"  Passed: {summary['passed_tests']} ({summary['success_rate']:.1f}%)")
        print(f"  Failed: {summary['failed_tests']}")
        print(f"  Warnings: {summary['warning_tests']}")
        print(f"  Validation Time: {summary['validation_time']:.2f}s")

        if report['failed_nodes']:
            print(f"\n❌ FAILED NODES ({len(report['failed_nodes'])}):")
            for node in report['failed_nodes'][:5]:
                print(f"    - {node}")
            if len(report['failed_nodes']) > 5:
                print(f"    ... and {len(report['failed_nodes']) - 5} more")

        if report['warning_nodes']:
            print(f"\n⚠️  NODES WITH WARNINGS ({len(report['warning_nodes'])}):")
            for node in report['warning_nodes'][:5]:
                print(f"    - {node}")
            if len(report['warning_nodes']) > 5:
                print(f"    ... and {len(report['warning_nodes']) - 5} more")

        print(f"\nRECOMMENDATIONS:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")

        # Test type breakdown
        print(f"\nTEST TYPE BREAKDOWN:")
        for test_type, results in report['test_results'].items():
            total = results['total']
            passed = results['passed']
            success_rate = (passed / total * 100) if total > 0 else 0
            print(f"  {test_type.capitalize()}: {passed}/{total} ({success_rate:.1f}% passed)")

def main():
    """Main function to run the validator"""
    import argparse

    parser = argparse.ArgumentParser(description='Validate ComfyUI custom nodes')
    parser.add_argument('--comfyui-path', default='/workspace/ComfyUI',
                        help='Path to ComfyUI installation')
    parser.add_argument('--output', '-o', default='custom_nodes_validation.json',
                        help='Output JSON file for detailed results')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')

    args = parser.parse_args()

    validator = CustomNodesValidator(args.comfyui_path)
    report = validator.run_all_validations()

    # Save detailed report
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)

    validator.print_summary(report)

    print(f"\n📄 Detailed report saved to: {args.output}")

    # Exit with error code if critical failures
    if report['summary']['failed_tests'] > 0:
        critical_failures = len([r for r in validator.results if r.status == 'fail' and r.test_type in ['import', 'dependencies']])
        if critical_failures > 0:
            print(f"\n❌ Critical validation failures detected!")
            sys.exit(1)

    print(f"\n✅ Validation complete!")

if __name__ == "__main__":
    main()