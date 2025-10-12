# Quick Start Guide: Optimized ComfyUI Build System

This guide helps you get started with the optimized ComfyUI build system quickly.

## Prerequisites

- Docker and Docker Buildx installed
- Git
- Python 3.11+ (for local analysis)

## 5-Minute Quick Start

### 1. Analyze Your Custom Nodes

```bash
# Clone the repository
git clone https://github.com/zeroclue/ComfyUI-docker.git
cd ComfyUI-docker

# Analyze current custom nodes for conflicts
python scripts/analyze_requirements.py custom_nodes.txt
```

### 2. Build Optimized Image

```bash
# Build with dependency optimization
docker bake -f docker-bake-optimized.hcl base-optimized-12-6
```

### 3. Run and Validate

```bash
# Run the optimized container
docker run --gpus all -p 3000:3000 zeroclue/comfyui:base-optimized-torch2.8.0-cu126

# Validate installation (inside container)
python scripts/validate_custom_nodes.py
```

## Common Use Cases

### Adding a New Custom Node

```bash
# 1. Create backup
python scripts/node_rollback.py create "Before adding new node"

# 2. Add node to custom_nodes.txt
echo "https://github.com/user/new-node.git" >> custom_nodes.txt

# 3. Check for conflicts
python scripts/analyze_requirements.py custom_nodes.txt

# 4. If no conflicts, rebuild
docker bake -f docker-bake-optimized.hcl base-optimized-12-6

# 5. Validate
python scripts/validate_custom_nodes.py
```

### Troubleshooting Installation Issues

```bash
# Check what failed
python scripts/validate_custom_nodes.py --output validation.json

# Review failed nodes
cat validation.json | jq '.failed_nodes'

# Rollback if needed
python scripts/node_rollback.py list
python scripts/node_rollback.py rollback <backup-id>
```

### Production Deployment

```bash
# Build production-optimized image
docker bake -f docker-bake-optimized.hcl production-optimized-12-8

# Deploy with minimal services
docker run --gpus all -p 3000:3000 \
  -e INSTALL_DEV_TOOLS=false \
  -e INSTALL_CODE_SERVER=false \
  zeroclue/comfyui:production-optimized-torch2.8.0-cu128
```

## Available Build Targets

### Optimized Variants

```bash
# Base with all custom nodes (optimized)
docker bake -f docker-bake-optimized.hcl base-optimized-12-6

# Slim without custom nodes
docker bake -f docker-bake-optimized.hcl slim-optimized-12-6

# Production-ready (minimal)
docker bake -f docker-bake-optimized.hcl production-optimized-12-6

# Ultra-optimized (smallest)
docker bake -f docker-bake-optimized.hcl ultra-optimized-12-6
```

### Validation Variants

```bash
# Build with extra validation
docker bake -f docker-bake-optimized.hcl base-validation-12-6
```

## Environment Variables

### Common Options

```bash
# Enable/disable services
docker run -e INSTALL_CODE_SERVER=false \
           -e INSTALL_DEV_TOOLS=false \
           zeroclue/comfyui:base-optimized

# Set timezone
docker run -e TIME_ZONE="America/New_York" \
           zeroclue/comfyui:base-optimized

# Configure ComfyUI
docker run -e COMFYUI_EXTRA_ARGS="--listen 0.0.0.0" \
           zeroclue/comfyui:base-optimized
```

### Preset Downloads

```bash
# Download video generation presets
docker run -e PRESET_DOWNLOAD=WAN_22_5B_TIV2,WAN22_LIGHTNING_LORA \
           zeroclue/comfyui:base-optimized

# Download image generation presets
docker run -e IMAGE_PRESET_DOWNLOAD=SDXL_BASE_V1,REALISTIC_VISION_V6 \
           zeroclue/comfyui:base-optimized

# Download audio generation presets
docker run -e AUDIO_PRESET_DOWNLOAD=MUSICGEN_MEDIUM,BARK_BASIC \
           zeroclue/comfyui:base-optimized
```

## Validation Commands

### Quick Validation

```bash
# Basic validation
python scripts/validate_custom_nodes.py

# Detailed report
python scripts/validate_custom_nodes.py --output detailed_report.json

# Validate specific ComfyUI installation
python scripts/validate_custom_nodes.py --comfyui-path /path/to/ComfyUI
```

### Understanding Results

```
✅ PASS - Node works correctly
⚠️  WARNING - Minor issues (may be normal)
❌ FAIL - Critical problems that need attention
```

## Rollback Commands

### Managing Rollback Points

```bash
# Create rollback point
python scripts/node_rollback.py create "Description of changes"

# List all rollback points
python scripts/node_rollback.py list

# Rollback to specific point
python scripts/node_rollback.py rollback 20241201_143022

# Dry run (see what would happen)
python scripts/node_rollback.py rollback 20241201_143022 --dry-run

# Remove specific node
python scripts/node_rollback.py remove problematic-node

# Clean up old backups
python scripts/node_rollback.py cleanup --keep 5
```

## Performance Tips

### Build Optimization

```bash
# Use BuildKit for better caching
export DOCKER_BUILDKIT=1
docker build ...

# Build specific target
docker bake -f docker-bake-optimized.hcl base-optimized-12-6

# Parallel builds
docker bake -f docker-bake-optimized.hcl optimized-all
```

### Runtime Optimization

```bash
# Use production variant for smaller size
docker run zeroclue/comfyui:production-optimized

# Disable unused services
docker run -e INSTALL_CODE_SERVER=false \
           -e INSTALL_DEV_TOOLS=false \
           zeroclue/comfyui:base-optimized

# Use host networking for better performance
docker run --network host zeroclue/comfyui:base-optimized
```

## Troubleshooting

### Common Issues

**Build Failures:**
```bash
# Check for dependency conflicts
python scripts/analyze_requirements.py custom_nodes.txt

# Review conflict details
cat custom_nodes_analysis.json | jq '.conflicts'

# Use legacy build if needed
docker bake base-12-6  # Uses original Dockerfile
```

**Import Errors:**
```bash
# Validate installation
python scripts/validate_custom_nodes.py

# Check failed imports
cat custom_nodes_validation.json | jq '.nodes | to_entries[] | select(.value.failed > 0)'

# Rollback problematic changes
python scripts/node_rollback.py rollback <last-working-id>
```

**Performance Issues:**
```bash
# Check node sizes
python scripts/validate_custom_nodes.py | grep "performance"

# Remove large nodes if needed
python scripts/node_rollback.py remove large-node

# Use ultra-optimized variant
docker run zeroclue/comfyui:ultra-optimized
```

### Getting Help

```bash
# Check script help
python scripts/analyze_requirements.py --help
python scripts/validate_custom_nodes.py --help
python scripts/node_rollback.py --help

# Review logs
docker logs <container-id>

# Check build artifacts
ls -la /tmp/custom_nodes_*.json
```

## Next Steps

- **Read the full documentation**: `docs/OPTIMIZED_BUILD_SYSTEM.md`
- **Explore custom nodes**: Check `custom_nodes.txt` for available nodes
- **Join the community**: GitHub discussions for tips and tricks
- **Contribute**: Submit pull requests for improvements

## Cheat Sheet

```bash
# Essential commands
python scripts/analyze_requirements.py custom_nodes.txt
python scripts/dependency_resolver.py custom_nodes_analysis.json
docker bake -f docker-bake-optimized.hcl base-optimized-12-6
python scripts/validate_custom_nodes.py

# Backup and rollback
python scripts/node_rollback.py create "Before changes"
python scripts/node_rollback.py list
python scripts/node_rollback.py rollback <id>

# Common builds
docker bake -f docker-bake-optimized.hcl base-optimized-12-6
docker bake -f docker-bake-optimized.hcl production-optimized-12-6
docker bake -f docker-bake-optimized.hcl ultra-optimized-12-6
```

This should get you up and running with the optimized ComfyUI build system in minutes!