#!/usr/bin/env python3

"""
Disk Space Estimation for Docker Builds
Calculates estimated disk space requirements for different ComfyUI variants
"""

import json
from typing import Dict, List

class DiskSpaceEstimator:
    def __init__(self):
        # Base image sizes (approximate, after download and extraction)
        self.base_images = {
            'cuda:12.6.3-devel-ubuntu24.04': 8.5,  # GB
            'cuda:12.6.3-runtime-ubuntu24.04': 6.2,  # GB
            'cuda:12.8.1-devel-ubuntu24.04': 9.2,   # GB (larger than 12.6)
            'cuda:12.8.1-runtime-ubuntu24.04': 6.8,  # GB (larger than 12.6)
        }

        # Package sizes (approximate installed sizes)
        self.package_sizes = {
            'python_system': 0.5,        # GB - Python system packages
            'python_packages': 2.0,      # GB - PyTorch, CUDA, etc.
            'dev_tools': 1.5,            # GB - build-essential, cmake, etc.
            'runtime_tools': 0.8,        # GB - nginx, ssh, etc.
            'comfyui_base': 0.3,         # GB - ComfyUI core
            'comfyui_manager': 0.2,      # GB - ComfyUI Manager
            'custom_node_avg': 0.15,     # GB - average per custom node
            'code_server': 0.5,          # GB - VS Code server
            'jupyter_lab': 0.8,         # GB - Jupyter and science packages
            'build_cache': 2.0,          # GB - Docker build cache during build
            'pip_cache': 1.5,            # GB - pip downloads during build
            'apt_cache': 0.8,            # GB - apt downloads during build
            'temp_files': 1.0,           # GB - temporary files during build
            'docker_layers': 1.2,        # GB - Docker layer overhead
        }

        # GitHub Actions runner constraints
        self.runner_disk = {
            'total_available': 30,       # GB - typical GitHub Actions runner
            'system_reserved': 8,        # GB - OS, tools, etc.
            'safe_available': 22,        # GB - realistically available
            'critical_threshold': 5,     # GB - minimum needed to avoid crashes
        }

    def estimate_variant_size(self, variant: str, cuda: str) -> Dict:
        """Estimate disk space needed for a specific variant"""

        # Map CUDA versions to actual base images
        cuda_mapping = {
            '12-6': '12.6.3',
            '12-8': '12.8.1'
        }
        cuda_formatted = cuda_mapping.get(cuda, cuda.replace('-', '.') + '.1')

        # Determine base images
        if variant == 'production':
            base_devel = self.base_images[f'cuda:{cuda_formatted}-devel-ubuntu24.04']
            base_runtime = self.base_images[f'cuda:{cuda_formatted}-runtime-ubuntu24.04']
        else:
            # All other variants use devel for both stages
            base_devel = self.base_images[f'cuda:{cuda_formatted}-devel-ubuntu24.04']
            base_runtime = base_devel

        # Calculate component sizes
        components = {
            'base_images': base_devel + base_runtime,
            'python_system': self.package_sizes['python_system'],
            'python_packages': self.package_sizes['python_packages'],
        }

        # Add variant-specific components
        if variant in ['base']:
            # Full installation with everything
            components.update({
                'dev_tools': self.package_sizes['dev_tools'],
                'runtime_tools': self.package_sizes['runtime_tools'],
                'comfyui_base': self.package_sizes['comfyui_base'],
                'comfyui_manager': self.package_sizes['comfyui_manager'],
                'custom_nodes': 24 * self.package_sizes['custom_node_avg'],  # 23 nodes + manager
                'code_server': self.package_sizes['code_server'],
                'jupyter_lab': self.package_sizes['jupyter_lab'],
            })
        elif variant == 'slim':
            # No custom nodes
            components.update({
                'dev_tools': self.package_sizes['dev_tools'],
                'runtime_tools': self.package_sizes['runtime_tools'],
                'comfyui_base': self.package_sizes['comfyui_base'],
                'comfyui_manager': self.package_sizes['comfyui_manager'],
                'custom_nodes': 0,
                'code_server': self.package_sizes['code_server'],
                'jupyter_lab': self.package_sizes['jupyter_lab'],
            })
        elif variant == 'minimal':
            # No custom nodes, no code server
            components.update({
                'dev_tools': self.package_sizes['dev_tools'],
                'runtime_tools': self.package_sizes['runtime_tools'],
                'comfyui_base': self.package_sizes['comfyui_base'],
                'comfyui_manager': self.package_sizes['comfyui_manager'],
                'custom_nodes': 0,
                'code_server': 0,
                'jupyter_lab': 0,
            })
        elif variant == 'production':
            # Optimized for serving, runtime base image
            components.update({
                'dev_tools': 0,  # No dev tools in production
                'runtime_tools': self.package_sizes['runtime_tools'],
                'comfyui_base': self.package_sizes['comfyui_base'],
                'comfyui_manager': self.package_sizes['comfyui_manager'],
                'custom_nodes': 0,  # No custom nodes in production
                'code_server': 0,
                'jupyter_lab': 0,
            })
        elif variant == 'ultra-slim':
            # Minimal serving
            components.update({
                'dev_tools': 0,
                'runtime_tools': self.package_sizes['runtime_tools'],
                'comfyui_base': self.package_sizes['comfyui_base'],
                'comfyui_manager': self.package_sizes['comfyui_manager'],
                'custom_nodes': 0,
                'code_server': 0,
                'jupyter_lab': 0,
            })

        # Calculate build-time requirements
        build_requirements = {
            'build_cache': self.package_sizes['build_cache'],
            'pip_cache': self.package_sizes['pip_cache'],
            'apt_cache': self.package_sizes['apt_cache'],
            'temp_files': self.package_sizes['temp_files'],
            'docker_layers': self.package_sizes['docker_layers'],
        }

        # Sum up requirements
        final_image_size = sum(components.values())
        peak_build_size = final_image_size + sum(build_requirements.values())

        return {
            'variant': variant,
            'cuda': cuda,
            'components': components,
            'build_requirements': build_requirements,
            'final_image_gb': round(final_image_size, 1),
            'peak_build_gb': round(peak_build_size, 1),
            'final_image_mb': round(final_image_size * 1024, 0),
            'peak_build_mb': round(peak_build_size * 1024, 0),
        }

    def analyze_all_variants(self) -> Dict:
        """Analyze all current workflow variants"""
        variants = ['base', 'slim', 'minimal', 'production', 'ultra-slim']
        cuda_versions = ['12-6', '12-8']

        results = {}

        for variant in variants:
            for cuda in cuda_versions:
                key = f"{variant}-{cuda}"
                results[key] = self.estimate_variant_size(variant, cuda)

        return results

    def print_analysis(self, results: Dict):
        """Print detailed analysis"""
        print(f"\n{'='*80}")
        print(f"DISK SPACE ANALYSIS FOR COMFYUI DOCKER BUILDS")
        print(f"{'='*80}")

        print(f"\nGitHub Actions Runner Constraints:")
        print(f"  Total Available: {self.runner_disk['total_available']} GB")
        print(f"  System Reserved: {self.runner_disk['system_reserved']} GB")
        print(f"  Safe Available: {self.runner_disk['safe_available']} GB")
        print(f"  Critical Threshold: {self.runner_disk['critical_threshold']} GB")

        print(f"\nDetailed Variant Analysis:")
        print(f"{'Variant':<15} {'Final Size':<12} {'Peak Build':<12} {'Status':<15} {'Notes'}")
        print(f"{'-'*80}")

        for key, result in sorted(results.items()):
            peak = result['peak_build_gb']
            final = result['final_image_gb']

            if peak <= self.runner_disk['safe_available']:
                status = "✅ Should Build"
                note = ""
            elif peak <= self.runner_disk['total_available']:
                status = "⚠️  Tight Fit"
                note = "(may fail)"
            else:
                status = "❌ Will Fail"
                note = "(too large)"

            print(f"{key:<15} {final:>6} GB    {peak:>6} GB     {status:<15} {note}")

        # Find the largest variant
        largest = max(results.items(), key=lambda x: x[1]['peak_build_gb'])
        print(f"\nLargest Variant: {largest[0]} ({largest[1]['peak_build_gb']} GB peak)")

        # Identify problem variants
        problem_variants = [k for k, v in results.items()
                          if v['peak_build_gb'] > self.runner_disk['safe_available']]

        if problem_variants:
            print(f"\n⚠️  VARIANTS WITH DISK SPACE ISSUES:")
            for variant in problem_variants:
                result = results[variant]
                shortage = result['peak_build_gb'] - self.runner_disk['safe_available']
                print(f"  {variant}: Short by {shortage:.1f} GB")

        # Recommendations
        print(f"\n📋 RECOMMENDATIONS:")

        if len(problem_variants) == 0:
            print("  ✅ All variants should build successfully")
        else:
            print(f"  ❌ {len(problem_variants)} variants need disk space optimization")

            # Suggest specific fixes
            base_128_problems = [v for v in problem_variants if 'base-12-8' in v]
            if base_128_problems:
                print("  🔧 For base-12-8 variants:")
                print("     - Consider removing from default workflow matrix")
                print("     - Build manually when needed")
                print("     - Use more aggressive cleanup")

        print(f"\n💡 OPTIMIZATION OPTIONS:")
        print(f"  1. Sequential builds (already implemented)")
        print(f"  2. Aggressive cleanup (already implemented)")
        print(f"  3. Remove problematic variants from matrix")
        print(f"  4. Use larger runners (if available)")

        # Calculate what we'd need for the problematic variant
        if 'base-12-8' in results:
            base_128 = results['base-12-8']
            needed = base_128['peak_build_gb'] + 5  # 5GB safety margin
            print(f"\n🎯 DISK SPACE NEEDED FOR BASE-12-8:")
            print(f"  Peak Build Requirement: {base_128['peak_build_gb']} GB")
            print(f"  Recommended Available: {needed:.1f} GB")
            print(f"  Current Available: {self.runner_disk['safe_available']} GB")
            print(f"  Additional Needed: {needed - self.runner_disk['safe_available']:.1f} GB")

def main():
    """Main execution"""
    estimator = DiskSpaceEstimator()
    results = estimator.analyze_all_variants()
    estimator.print_analysis(results)

    # Save results
    with open('disk_space_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n📁 Detailed analysis saved to: disk_space_analysis.json")

if __name__ == "__main__":
    main()