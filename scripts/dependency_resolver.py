#!/usr/bin/env python3
"""
ComfyUI Dependency Resolver
Resolves dependency conflicts and creates optimized installation order
"""

import json
import sys
import re
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict, OrderedDict

@dataclass
class DependencyGroup:
    """Group of dependencies that can be installed together"""
    name: str
    dependencies: List[str]
    nodes: List[str]
    priority: int

@dataclass
class ResolutionStrategy:
    """Strategy for resolving a specific conflict"""
    dependency: str
    conflicts: List[Tuple[str, str]]  # (node, version_spec)
    recommended_version: str
    affected_nodes: List[str]
    risk_level: str  # 'low', 'medium', 'high'

class DependencyResolver:
    """Resolves and optimizes ComfyUI custom node dependencies"""

    def __init__(self, analysis_file: str = 'custom_nodes_analysis.json'):
        """Initialize with analysis results"""
        self.analysis_file = analysis_file
        self.load_analysis()
        self.resolutions: List[ResolutionStrategy] = []
        self.installation_groups: List[DependencyGroup] = []

    def load_analysis(self):
        """Load analysis results from JSON file"""
        try:
            with open(self.analysis_file, 'r') as f:
                self.analysis = json.load(f)
        except FileNotFoundError:
            print(f"Error: Analysis file {self.analysis_file} not found")
            print("Run analyze_requirements.py first")
            sys.exit(1)

    def resolve_conflicts(self) -> List[ResolutionStrategy]:
        """Generate resolution strategies for all conflicts"""
        strategies = []

        # Group conflicts by dependency
        conflict_groups = defaultdict(list)
        for conflict in self.analysis['conflicts']:
            conflict_groups[conflict['dependency']].append(conflict)

        for dependency, conflicts in conflict_groups.items():
            strategy = self.resolve_dependency_conflict(dependency, conflicts)
            strategies.append(strategy)

        self.resolutions = strategies
        return strategies

    def resolve_dependency_conflict(self, dependency: str, conflicts: List[Dict]) -> ResolutionStrategy:
        """Resolve conflicts for a specific dependency"""
        # Collect all version specs
        version_specs = []
        for conflict in conflicts:
            version_specs.append((conflict['node1'], conflict['version1']))
            version_specs.append((conflict['node2'], conflict['version2']))

        # Remove duplicates
        version_specs = list(set(version_specs))

        # Determine resolution strategy based on dependency type
        recommended_version, risk_level = self.get_resolution_for_dependency(dependency, version_specs)

        # Get all affected nodes
        affected_nodes = list(set([node for node, _ in version_specs]))

        return ResolutionStrategy(
            dependency=dependency,
            conflicts=version_specs,
            recommended_version=recommended_version,
            affected_nodes=affected_nodes,
            risk_level=risk_level
        )

    def get_resolution_for_dependency(self, dependency: str, version_specs: List[Tuple[str, str]]) -> Tuple[str, str]:
        """Get recommended version and risk level for a dependency"""

        # Known dependency resolutions
        known_resolutions = {
            'opencv-python': {
                'version': 'opencv-python==4.8.1.78',
                'risk': 'medium',
                'reason': 'VideoHelperSuite requires this version'
            },
            'torch': {
                'version': 'torch>=2.0.0',
                'risk': 'high',
                'reason': 'ComfyUI base requirement'
            },
            'numpy': {
                'version': 'numpy>=1.24.0',
                'risk': 'low',
                'reason': 'Wide compatibility range'
            },
            'transformers': {
                'version': 'transformers>=4.30.0',
                'risk': 'medium',
                'reason': 'AI model compatibility'
            }
        }

        # Check if we have a known resolution
        if dependency.lower() in known_resolutions:
            resolution = known_resolutions[dependency.lower()]
            return resolution['version'], resolution['risk']

        # Check for exact version conflicts
        exact_versions = [spec for _, spec in version_specs if '=' in spec and '>' not in spec and '<' not in spec]
        if len(exact_versions) > 1:
            # Multiple exact versions - high risk
            # Try to find a compatible range
            return f"{dependency}>=1.0.0", 'high'

        # Check for version ranges
        range_specs = [spec for _, spec in version_specs if '>' in spec or '<' in spec]
        if range_specs:
            # Try to find intersection of ranges
            # For now, recommend latest compatible version
            return f"{dependency}>=1.0.0", 'medium'

        # Default: recommend flexible version
        return f"{dependency}>=1.0.0", 'low'

    def create_installation_groups(self) -> List[DependencyGroup]:
        """Create optimized installation groups based on dependency relationships"""

        # Group dependencies by type and usage patterns
        groups = []

        # Core ML dependencies (install first)
        core_deps = self.get_core_dependencies()
        if core_deps:
            groups.append(DependencyGroup(
                name="Core ML Dependencies",
                dependencies=core_deps,
                nodes=self.get_nodes_for_dependencies(core_deps),
                priority=1
            ))

        # Video processing dependencies
        video_deps = self.get_video_dependencies()
        if video_deps:
            groups.append(DependencyGroup(
                name="Video Processing",
                dependencies=video_deps,
                nodes=self.get_nodes_for_dependencies(video_deps),
                priority=2
            ))

        # Image processing dependencies
        image_deps = self.get_image_dependencies()
        if image_deps:
            groups.append(DependencyGroup(
                name="Image Processing",
                dependencies=image_deps,
                nodes=self.get_nodes_for_dependencies(image_deps),
                priority=3
            ))

        # Utility dependencies
        utility_deps = self.get_utility_dependencies()
        if utility_deps:
            groups.append(DependencyGroup(
                name="Utility Dependencies",
                dependencies=utility_deps,
                nodes=self.get_nodes_for_dependencies(utility_deps),
                priority=4
            ))

        # Node-specific dependencies
        specific_deps = self.get_node_specific_dependencies()
        if specific_deps:
            groups.append(DependencyGroup(
                name="Node-Specific Dependencies",
                dependencies=specific_deps,
                nodes=self.get_nodes_for_dependencies(specific_deps),
                priority=5
            ))

        # Sort by priority
        groups.sort(key=lambda x: x.priority)
        self.installation_groups = groups
        return groups

    def get_core_dependencies(self) -> List[str]:
        """Get core ML/AI dependencies"""
        core_patterns = ['torch', 'tensorflow', 'numpy', 'scipy']
        return self.filter_dependencies_by_patterns(core_patterns)

    def get_video_dependencies(self) -> List[str]:
        """Get video processing dependencies"""
        video_patterns = ['opencv', 'ffmpeg', 'av', 'imageio', 'moviepy']
        return self.filter_dependencies_by_patterns(video_patterns)

    def get_image_dependencies(self) -> List[str]:
        """Get image processing dependencies"""
        image_patterns = ['pillow', 'pil', 'skimage', 'cv2', 'image']
        return self.filter_dependencies_by_patterns(image_patterns)

    def get_utility_dependencies(self) -> List[str]:
        """Get utility dependencies"""
        utility_patterns = ['requests', 'yaml', 'tqdm', 'click', 'rich']
        return self.filter_dependencies_by_patterns(utility_patterns)

    def get_node_specific_dependencies(self) -> List[str]:
        """Get dependencies that are used by only one node"""
        dependency_usage = defaultdict(int)

        for node in self.analysis['nodes']:
            for req in node['requirements']:
                package = re.match(r'^([a-zA-Z0-9\-_\.]+)', req.lower())
                if package:
                    dependency_usage[package.group(1)] += 1

        # Return dependencies used by only one node
        return [dep for dep, count in dependency_usage.items() if count == 1]

    def filter_dependencies_by_patterns(self, patterns: List[str]) -> List[str]:
        """Filter dependencies matching given patterns"""
        matching_deps = set()

        for node in self.analysis['nodes']:
            for req in node['requirements']:
                package = re.match(r'^([a-zA-Z0-9\-_\.]+)', req.lower())
                if package:
                    pkg_name = package.group(1)
                    for pattern in patterns:
                        if pattern in pkg_name:
                            matching_deps.add(req)
                            break

        return list(matching_deps)

    def get_nodes_for_dependencies(self, dependencies: List[str]) -> List[str]:
        """Get nodes that use the specified dependencies"""
        nodes = set()

        for node in self.analysis['nodes']:
            for req in node['requirements']:
                if req in dependencies:
                    nodes.add(node['name'])
                    break

        return list(nodes)

    def generate_optimized_requirements(self) -> Dict[str, List[str]]:
        """Generate optimized requirements files for each group"""
        optimized = {}

        for group in self.installation_groups:
            # Apply conflict resolutions
            resolved_deps = []
            for dep in group.dependencies:
                resolved_dep = self.apply_resolution(dep)
                if resolved_dep:
                    resolved_deps.append(resolved_dep)

            # Remove duplicates while preserving order
            seen = set()
            unique_deps = []
            for dep in resolved_deps:
                package = re.match(r'^([a-zA-Z0-9\-_\.]+)', dep.lower())
                if package:
                    pkg_name = package.group(1)
                    if pkg_name not in seen:
                        seen.add(pkg_name)
                        unique_deps.append(dep)

            optimized[group.name] = unique_deps

        return optimized

    def apply_resolution(self, dependency: str) -> Optional[str]:
        """Apply conflict resolution to a dependency"""
        package = re.match(r'^([a-zA-Z0-9\-_\.]+)', dependency.lower())
        if not package:
            return dependency

        pkg_name = package.group(1)

        # Check if we have a resolution for this dependency
        for resolution in self.resolutions:
            if resolution.dependency.lower() == pkg_name.lower():
                return resolution.recommended_version

        # No resolution needed
        return dependency

    def generate_installation_script(self) -> str:
        """Generate optimized installation script"""
        script_lines = [
            "#!/bin/bash",
            "# Optimized ComfyUI Custom Nodes Installation",
            "# Generated by dependency_resolver.py",
            "",
            "set -e",
            "",
            "echo \"Installing ComfyUI custom node dependencies...\"",
            ""
        ]

        # Add pip optimization settings
        script_lines.extend([
            "# Optimize pip for faster installs",
            "pip install --upgrade pip setuptools wheel",
            "export PIP_NO_CACHE_DIR=1",
            "export PIP_DISABLE_PIP_VERSION_CHECK=1",
            ""
        ])

        # Add installation groups
        optimized_reqs = self.generate_optimized_requirements()
        for group_name, dependencies in optimized_reqs.items():
            if dependencies:
                script_lines.extend([
                    f"# Install {group_name}",
                    f"echo \"Installing {group_name}...\""
                ])

                # Create temporary requirements file
                script_lines.extend([
                    f"cat > /tmp/{group_name.lower().replace(' ', '_')}.txt << 'EOF'"
                ])
                script_lines.extend(dependencies)
                script_lines.extend([
                    "EOF",
                    f"pip install -r /tmp/{group_name.lower().replace(' ', '_')}.txt || {{",
                    "  echo \"Warning: Some dependencies in {group_name} failed to install\"",
                    "}",
                    "",
                ])

        # Add cleanup
        script_lines.extend([
            "# Cleanup temporary files",
            "rm -f /tmp/*.txt",
            "",
            "echo \"Dependency installation complete!\"",
            ""
        ])

        return "\n".join(script_lines)

    def save_resolution_report(self, filename: str = 'dependency_resolution.json'):
        """Save resolution report to JSON file"""
        report = {
            'summary': {
                'total_conflicts': len(self.analysis['conflicts']),
                'resolutions_generated': len(self.resolutions),
                'installation_groups': len(self.installation_groups),
                'high_risk_resolutions': len([r for r in self.resolutions if r.risk_level == 'high'])
            },
            'resolutions': [],
            'installation_groups': [],
            'optimized_requirements': self.generate_optimized_requirements(),
            'installation_script': self.generate_installation_script()
        }

        # Add resolution details
        for resolution in self.resolutions:
            report['resolutions'].append({
                'dependency': resolution.dependency,
                'conflicts': resolution.conflicts,
                'recommended_version': resolution.recommended_version,
                'affected_nodes': resolution.affected_nodes,
                'risk_level': resolution.risk_level
            })

        # Add installation group details
        for group in self.installation_groups:
            report['installation_groups'].append({
                'name': group.name,
                'dependencies': group.dependencies,
                'nodes': group.nodes,
                'priority': group.priority
            })

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        return filename

    def print_summary(self):
        """Print resolution summary"""
        print("\n" + "="*80)
        print("DEPENDENCY RESOLUTION SUMMARY")
        print("="*80)

        print(f"\nConflicts Found: {len(self.analysis['conflicts'])}")
        print(f"Resolutions Generated: {len(self.resolutions)}")
        print(f"Installation Groups: {len(self.installation_groups)}")

        high_risk = [r for r in self.resolutions if r.risk_level == 'high']
        if high_risk:
            print(f"\n⚠️  High Risk Resolutions: {len(high_risk)}")
            for resolution in high_risk:
                print(f"    {resolution.dependency}: {resolution.recommended_version}")
                print(f"      Affects: {', '.join(resolution.affected_nodes)}")

        print(f"\nInstallation Groups:")
        for group in self.installation_groups:
            print(f"  {group.priority}. {group.name} ({len(group.dependencies)} deps, {len(group.nodes)} nodes)")

def main():
    """Main function to run the dependency resolver"""
    if len(sys.argv) < 2:
        print("Usage: python dependency_resolver.py <analysis_file> [output_file]")
        sys.exit(1)

    analysis_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'dependency_resolution.json'

    resolver = DependencyResolver(analysis_file)

    print("Resolving dependency conflicts...")
    resolver.resolve_conflicts()

    print("Creating installation groups...")
    resolver.create_installation_groups()

    print("Generating resolution report...")
    resolver.save_resolution_report(output_file)

    resolver.print_summary()

    print(f"\n✅ Resolution complete! Report saved to: {output_file}")

    # Exit with warning if high-risk resolutions
    high_risk = [r for r in resolver.resolutions if r.risk_level == 'high']
    if high_risk:
        print(f"\n⚠️  Warning: {len(high_risk)} high-risk resolutions require manual review")
        sys.exit(1)

if __name__ == "__main__":
    main()