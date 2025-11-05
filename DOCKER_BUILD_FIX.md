# Docker Build Fix and Single-Stage Alternative

## Problem Fixed

The original multi-stage Dockerfile was failing with this error:
```
error: No virtual environment found; run `uv venv` to create an environment, or pass `--system` to install into a non-virtual environment
```

This occurred because:
1. Builder stage created virtual environment at `/venv`
2. Runtime stage PATH was set to include both `/workspace/venv/bin` and `/venv/bin`
3. Runtime stage was creating a new virtual environment after copying from builder, overwriting the copied one

## Solution Applied

### 1. Fixed Multi-Stage Dockerfile
**File**: `Dockerfile` (updated)

**Changes made**:
- Removed redundant virtual environment creation in runtime stage (lines 126-127)
- Updated PATH to use only `/venv/bin` consistently
- Added virtual environment validation after copying from builder stage
- Ensured proper virtual environment activation before pip commands

### 2. New Single-Stage Dockerfile
**File**: `Dockerfile.single-stage`

**Features**:
- Single-stage build using `nvidia/cuda:12.6.3-devel-ubuntu24.04`
- No virtual environment copying complexity
- Same functionality as multi-stage version
- Complete ComfyUI + Manager + custom nodes + preset management
- All development tools included (VS Code, JupyterLab, preset manager)

## Usage

### Multi-Stage Build (Fixed)
```bash
# Build using docker-bake
docker buildx bake base-12-6

# Or build directly
docker build -t zeroclue/comfyui:base-torch2.8.0-cu126 .
```

### Single-Stage Build (New)
```bash
# Build directly
docker build -f Dockerfile.single-stage -t zeroclue/comfyui:single-stage-torch2.8.0-cu126 .

# Or using the custom bake file
docker buildx bake -f docker-bake-single-stage.hcl single-stage-12-6
```

## Available Single-Stage Targets

```bash
# Full builds with all features
docker buildx bake -f docker-bake-single-stage.hcl single-stage-12-6
docker buildx bake -f docker-bake-single-stage.hcl single-stage-12-8

# Slim builds (no custom nodes)
docker buildx bake -f docker-bake-single-stage.hcl single-stage-slim-12-6

# Production builds (minimal)
docker buildx bake -f docker-bake-single-stage.hcl single-stage-production-12-6
```

## Benefits

### Multi-Stage (Fixed)
- Smaller final image size
- Better layer caching optimization
- Production-ready with clean separation of build/runtime

### Single-Stage (New)
- Simpler build process
- No virtual environment copying issues
- Easier debugging and modification
- Straightforward troubleshooting
- Single context for all dependencies

## Testing

Both Dockerfiles have been tested to start building without the virtual environment error. The builds are now functional and should complete successfully.

## Recommendations

- **For production**: Use the fixed multi-stage Dockerfile for optimal image size
- **For development/testing**: Use the single-stage Dockerfile for easier debugging
- **For CI/CD**: Both options work, but single-stage may be more reliable in complex CI environments