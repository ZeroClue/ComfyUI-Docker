#!/usr/bin/env python3
"""
ComfyUI Custom Node Requirements Analyzer
Analyzes custom nodes for dependency conflicts and optimization opportunities
"""

import requests
import re
import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse
import tempfile
import os

@dataclass
class NodeInfo:
    """Information about a custom node"""
    name: str
    url: str
    requirements: List[str]
    has_requirements: bool
    potential_conflicts: List[str]
    size_estimate: str

@dataclass
class ConflictInfo:
    """Information about a dependency conflict"""
    dependency: str
    node1: str
    version1: str
    node2: str
    version2: str
    severity: str  # 'high', 'medium', 'low'

class RequirementsAnalyzer:
    """Analyzes custom node requirements for conflicts and optimizations"""

    def __init__(self):
        self.conflicts: List[ConflictInfo] = []
        self.nodes: List[NodeInfo] = []
        self.dependency_matrix: Dict[str, Dict[str, str]] = {}

    def extract_github_info(self, url: str) -> Tuple[str, str]:
        """Extract owner and repo name from GitHub URL"""
        parsed = urlparse(url)
        if 'github.com' not in parsed.netloc:
            raise ValueError(f"Not a GitHub URL: {url}")

        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) < 2:
            raise ValueError(f"Invalid GitHub URL format: {url}")

        return path_parts[0], path_parts[1]

    def fetch_requirements_from_github(self, url: str) -> List[str]:
        """Fetch requirements.txt from a GitHub repository"""
        try:
            owner, repo = self.extract_github_info(url)

            # Try to fetch requirements.txt
            api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/requirements.txt"
            response = requests.get(api_url, timeout=10)

            if response.status_code == 200:
                content = response.json()
                if content.get('encoding') == 'base64':
                    import base64
                    requirements_text = base64.b64decode(content['content']).decode('utf-8')
                else:
                    requirements_text = content['content']

                return self.parse_requirements(requirements_text)
            else:
                print(f"Warning: No requirements.txt found for {url}")
                return []

        except Exception as e:
            print(f"Error fetching requirements for {url}: {e}")
            return []

    def parse_requirements(self, requirements_text: str) -> List[str]:
        """Parse requirements.txt content"""
        requirements = []
        for line in requirements_text.strip().split('\n'):
            line = line.strip()
            # Skip comments and empty lines
            if line and not line.startswith('#'):
                # Handle -r includes and other pip install directives
                if line.startswith('-r '):
                    continue  # Skip includes for now
                # Extract package name and version
                match = re.match(r'^([a-zA-Z0-9\-_\.]+)', line)
                if match:
                    requirements.append(line)
        return requirements

    def analyze_dependency_conflicts(self) -> List[ConflictInfo]:
        """Analyze dependencies for potential conflicts"""
        dependency_versions = {}
        conflicts = []

        for node in self.nodes:
            for req in node.requirements:
                # Extract package name and version
                match = re.match(r'^([a-zA-Z0-9\-_\.]+)([><=!]+.*)?', req)
                if match:
                    package = match.group(1).lower()
                    version_spec = match.group(2) or ""

                    if package not in dependency_versions:
                        dependency_versions[package] = []

                    dependency_versions[package].append({
                        'node': node.name,
                        'version_spec': version_spec,
                        'full_req': req
                    })

        # Check for conflicts
        for package, specs in dependency_versions.items():
            if len(specs) > 1:
                # Check if version specs are compatible
                versions = [s['version_spec'] for s in specs if s['version_spec']]
                if len(set(versions)) > 1:
                    for i in range(len(specs)):
                        for j in range(i + 1, len(specs)):
                            if specs[i]['version_spec'] != specs[j]['version_spec']:
                                severity = self.assess_conflict_severity(package, specs[i]['version_spec'], specs[j]['version_spec'])
                                conflicts.append(ConflictInfo(
                                    dependency=package,
                                    node1=specs[i]['node'],
                                    version1=specs[i]['full_req'],
                                    node2=specs[j]['node'],
                                    version2=specs[j]['full_req'],
                                    severity=severity
                                ))

        return conflicts

    def assess_conflict_severity(self, package: str, spec1: str, spec2: str) -> str:
        """Assess the severity of a version conflict"""
        # Core ML packages are high severity
        critical_packages = ['torch', 'torchvision', 'numpy', 'opencv-python', 'transformers']

        if package in critical_packages:
            return 'high'

        # Exact version mismatches are medium severity
        if '=' in spec1 and '=' in spec2:
            return 'medium'

        # Range conflicts are lower severity
        return 'low'

    def estimate_size_impact(self, requirements: List[str]) -> str:
        """Estimate the size impact of requirements"""
        size_estimates = {
            'torch': '2GB',
            'torchvision': '1GB',
            'opencv-python': '200MB',
            'transformers': '500MB',
            'numpy': '50MB',
            'pillow': '50MB',
            'requests': '10MB',
        }

        total_size = 0
        for req in requirements:
            package = re.match(r'^([a-zA-Z0-9\-_\.]+)', req.lower())
            if package:
                pkg_name = package.group(1)
                for key, size in size_estimates.items():
                    if key in pkg_name:
                        # Convert to MB for calculation
                        size_val = int(size.replace('GB', '000').replace('MB', ''))
                        total_size += size_val
                        break

        if total_size > 2000:
            return f"{total_size//1000}GB+"
        elif total_size > 500:
            return f"{total_size//1000}GB"
        else:
            return f"{total_size}MB"

    def analyze_node(self, url: str) -> NodeInfo:
        """Analyze a single custom node"""
        try:
            owner, repo = self.extract_github_info(url)
            name = repo.replace('ComfyUI-', '').replace('comfyui-', '')

            requirements = self.fetch_requirements_from_github(url)
            size_estimate = self.estimate_size_impact(requirements)

            return NodeInfo(
                name=name,
                url=url,
                requirements=requirements,
                has_requirements=len(requirements) > 0,
                potential_conflicts=[],
                size_estimate=size_estimate
            )

        except Exception as e:
            print(f"Error analyzing node {url}: {e}")
            return NodeInfo(
                name="unknown",
                url=url,
                requirements=[],
                has_requirements=False,
                potential_conflicts=[],
                size_estimate="unknown"
            )

    def analyze_custom_nodes_file(self, file_path: str) -> Dict:
        """Analyze all custom nodes from a custom_nodes.txt file"""
        with open(file_path, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        print(f"Analyzing {len(urls)} custom nodes...")

        # Analyze each node
        for url in urls:
            print(f"Analyzing: {url}")
            node = self.analyze_node(url)
            self.nodes.append(node)

        # Find conflicts
        self.conflicts = self.analyze_dependency_conflicts()

        # Generate dependency matrix
        self.generate_dependency_matrix()

        return self.generate_report()

    def generate_dependency_matrix(self) -> None:
        """Generate a matrix of all dependencies and their versions"""
        all_deps = {}

        for node in self.nodes:
            for req in node.requirements:
                match = re.match(r'^([a-zA-Z0-9\-_\.]+)([><=!]+.*)?', req)
                if match:
                    package = match.group(1).lower()
                    version_spec = match.group(2) or "any"

                    if package not in all_deps:
                        all_deps[package] = {}

                    all_deps[package][node.name] = version_spec

        self.dependency_matrix = all_deps

    def generate_report(self) -> Dict:
        """Generate a comprehensive analysis report"""
        report = {
            'summary': {
                'total_nodes': len(self.nodes),
                'nodes_with_requirements': len([n for n in self.nodes if n.has_requirements]),
                'total_conflicts': len(self.conflicts),
                'high_severity_conflicts': len([c for c in self.conflicts if c.severity == 'high']),
                'estimated_total_size': self.calculate_total_size()
            },
            'nodes': [],
            'conflicts': [],
            'dependency_matrix': self.dependency_matrix,
            'recommendations': self.generate_recommendations()
        }

        # Add node details
        for node in self.nodes:
            report['nodes'].append({
                'name': node.name,
                'url': node.url,
                'requirements_count': len(node.requirements),
                'has_requirements': node.has_requirements,
                'size_estimate': node.size_estimate,
                'requirements': node.requirements
            })

        # Add conflict details
        for conflict in self.conflicts:
            report['conflicts'].append({
                'dependency': conflict.dependency,
                'node1': conflict.node1,
                'version1': conflict.version1,
                'node2': conflict.node2,
                'version2': conflict.version2,
                'severity': conflict.severity
            })

        return report

    def calculate_total_size(self) -> str:
        """Calculate total estimated size of all dependencies"""
        all_requirements = set()
        for node in self.nodes:
            all_requirements.update(node.requirements)

        return self.estimate_size_impact(list(all_requirements))

    def generate_recommendations(self) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []

        if len(self.conflicts) > 0:
            high_conflicts = [c for c in self.conflicts if c.severity == 'high']
            if high_conflicts:
                recommendations.append(f"URGENT: Resolve {len(high_conflicts)} high-severity dependency conflicts")

            med_conflicts = [c for c in self.conflicts if c.severity == 'medium']
            if med_conflicts:
                recommendations.append(f"Address {len(med_conflicts)} medium-severity version conflicts")

        # Check for common dependencies that can be deduplicated
        common_deps = {}
        for node in self.nodes:
            for req in node.requirements:
                package = re.match(r'^([a-zA-Z0-9\-_\.]+)', req.lower())
                if package:
                    pkg_name = package.group(1)
                    if pkg_name not in common_deps:
                        common_deps[pkg_name] = 0
                    common_deps[pkg_name] += 1

        shared_deps = {k: v for k, v in common_deps.items() if v > 1}
        if shared_deps:
            recommendations.append(f"Optimize {len(shared_deps)} shared dependencies for layer efficiency")

        # Size recommendations
        total_size = self.calculate_total_size()
        if 'GB' in total_size:
            recommendations.append("Consider multi-stage builds to reduce final image size")

        return recommendations

def main():
    """Main function to run the analyzer"""
    if len(sys.argv) != 2:
        print("Usage: python analyze_requirements.py <custom_nodes.txt>")
        sys.exit(1)

    custom_nodes_file = sys.argv[1]
    if not os.path.exists(custom_nodes_file):
        print(f"Error: File {custom_nodes_file} not found")
        sys.exit(1)

    analyzer = RequirementsAnalyzer()
    report = analyzer.analyze_custom_nodes_file(custom_nodes_file)

    # Output results
    print("\n" + "="*80)
    print("COMFYUI CUSTOM NODES ANALYSIS REPORT")
    print("="*80)

    print(f"\nSUMMARY:")
    print(f"  Total nodes: {report['summary']['total_nodes']}")
    print(f"  Nodes with requirements: {report['summary']['nodes_with_requirements']}")
    print(f"  Total conflicts: {report['summary']['total_conflicts']}")
    print(f"  High severity conflicts: {report['summary']['high_severity_conflicts']}")
    print(f"  Estimated total size: {report['summary']['estimated_total_size']}")

    if report['summary']['total_conflicts'] > 0:
        print(f"\nCONFLICTS:")
        for conflict in report['conflicts']:
            print(f"  {conflict['severity'].upper()}: {conflict['dependency']}")
            print(f"    {conflict['node1']}: {conflict['version1']}")
            print(f"    {conflict['node2']}: {conflict['version2']}")
            print()

    if report['recommendations']:
        print(f"\nRECOMMENDATIONS:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")

    # Save detailed report to JSON
    report_file = 'custom_nodes_analysis.json'
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\nDetailed report saved to: {report_file}")

    # Exit with error code if high-severity conflicts found
    if report['summary']['high_severity_conflicts'] > 0:
        print("\n⚠️  High-severity conflicts detected! Please resolve before building.")
        sys.exit(1)
    else:
        print("\n✅ Analysis complete. No critical conflicts found.")

if __name__ == "__main__":
    main()