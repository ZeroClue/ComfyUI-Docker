# ComfyUI-Docker Migration Guide v1.x to v2.0

**Version:** 2.0.0
**Last Updated:** 2026-02-15

## Table of Contents

- [Overview](#overview)
- [What's New in v2.0](#whats-new-in-v20)
- [Breaking Changes](#breaking-changes)
- [Migration Steps](#migration-steps)
- [Data Migration](#data-migration)
- [Configuration Migration](#configuration-migration)
- [Rollback Procedures](#rollback-procedures)
- [Troubleshooting](#troubleshooting)

---

## Overview

ComfyUI-Docker v2.0 introduces a revolutionary architecture that eliminates the rsync bottleneck and enables instant startup. This guide helps you migrate from v1.x to v2.0 with minimal disruption.

### Migration Benefits

- **4x Faster Startup**: <30 seconds vs 2-5 minutes
- **Zero-Rsync**: Native ComfyUI integration
- **Unified Dashboard**: Single interface for all operations
- **Persistent Storage**: Models survive container restarts
- **Background Downloads**: Non-blocking preset installations

### Migration Path

The migration is designed to be:

- **Non-Destructive**: Your data is preserved
- **Reversible**: You can rollback if needed
- **Gradual**: Migrate at your own pace
- **Compatible**: Existing workflows and models continue to work

---

## What's New in v2.0

### Architecture Changes

**v1.x Architecture:**
```
Container Start → rsync Models → Start ComfyUI (60-120s)
```

**v2.0 Architecture:**
```
Container Start → Generate Config → Start Services (<30s)
```

### New Features

1. **Unified Dashboard** (Port 8080)
   - System overview and monitoring
   - Preset browser and installer
   - Model management
   - Workflow execution

2. **Instant Startup**
   - Eliminated rsync bottleneck
   - Parallel service initialization
   - Optimized configuration generation

3. **Persistent Storage**
   - Models on network volume
   - Survives container restarts
   - Shared across multiple pods

4. **Background Downloads**
   - Non-blocking preset installations
   - Real-time progress tracking
   - WebSocket updates

5. **ComfyUI Studio** (Port 5001)
   - Simplified workflow execution
   - Auto-generated input forms
   - Template-based workflows

---

## Breaking Changes

### Port Changes

| Service | v1.x | v2.0 | Notes |
|---------|------|------|-------|
| ComfyUI | 3000 | 3000 | Unchanged |
| Dashboard | N/A | 8080 | New unified dashboard |
| Preset Manager | 9000 | 9000 | Unchanged |
| Studio | N/A | 5001 | New simplified interface |

### Environment Variable Changes

**Removed Variables:**
- `SYNC_MODE` - No longer needed with zero-rsync
- `RSYNC_ON_START` - Replaced by instant startup
- `MODEL_SYNC_SOURCE` - Models always on network volume

**New Variables:**
- `ENABLE_DASHBOARD` - Control unified dashboard (default: true)
- `ENABLE_STUDIO` - Control ComfyUI Studio (default: true)
- `STUDIO_PORT` - Studio internal port (default: 5000)

**Changed Variables:**
- `WORKSPACE_DIR` → `WORKSPACE_ROOT` (more explicit naming)
- `PRESET_MANAGER_PORT` → `PRESET_MANAGER_PORT` (unchanged, but now part of dashboard)

### Volume Structure Changes

**v1.x Structure:**
```
/workspace/
├── ComfyUI/
│   ├── models/           # Models synced here
│   └── ...
└── ...
```

**v2.0 Structure:**
```
/workspace/
├── models/               # Models directly here
├── ComfyUI/
│   └── models/           # Empty (via extra_model_paths.yaml)
├── output/
├── workflows/
└── config/
```

### API Changes

**New Endpoints:**
- `GET /api/system/status` - Comprehensive system status
- `GET /api/system/storage` - Storage information
- `POST /api/workflows` - Save workflows
- `WebSocket /ws` - Real-time updates

**Changed Endpoints:**
- Preset endpoints now return additional metadata
- Model endpoints include type filtering
- System endpoints enhanced with more details

---

## Migration Steps

### Phase 1: Preparation (15 minutes)

1. **Backup Current Setup**
   ```bash
   # Backup important data
   ssh root@<your-pod-url>

   # Backup models
   rsync -av /workspace/ComfyUI/models/ /backup/models/

   # Backup workflows
   rsync -av /workspace/ComfyUI/workflows/ /backup/workflows/

   # Backup config
   cp /workspace/config/presets.yaml /backup/
   ```

2. **Document Current Configuration**
   ```bash
   # Note your current environment variables
   env | grep -E "(PRESET|ACCESS|ENABLE)" > /backup/env_vars.txt

   # Note installed presets
   ls /workspace/ComfyUI/models/ > /backup/installed_models.txt
   ```

3. **Test v2.0 Locally** (Optional)
   ```bash
   # Pull v2.0 image
   docker pull zeroclue/comfyui:base-torch2.8.0-cu126

   # Test with test volume
   docker run -d \
     --name comfyui-v2-test \
     --gpus all \
     -v $(pwd)/test-workspace:/workspace \
     -e PRESET_DOWNLOAD=SDXL_BASE_V1 \
     zeroclue/comfyui:base-torch2.8.0-cu126
   ```

### Phase 2: Volume Migration (30 minutes)

1. **Stop Current Pod**
   - In RunPod console: Stop your v1.x pod
   - Wait for graceful shutdown

2. **Create New Volume Structure**
   ```bash
   # Access your network volume
   # In RunPod console: Launch temporary pod with volume

   # Create new structure
   mkdir -p /workspace/models/{checkpoints,text_encoders,vae,clip_vision,loras,upscale_models}
   mkdir -p /workspace/output/{images,videos}
   mkdir -p /workspace/workflows/{user,templates}
   mkdir -p /workspace/uploads/{input,assets}
   mkdir -p /workspace/config
   mkdir -p /workspace/cache
   mkdir -p /workspace/logs
   ```

3. **Migrate Models**
   ```bash
   # Move models to new location
   rsync -av /workspace/ComfyUI/models/checkpoints/ /workspace/models/checkpoints/
   rsync -av /workspace/ComfyUI/models/loras/ /workspace/models/loras/
   rsync -av /workspace/ComfyUI/models/vae/ /workspace/models/vae/
   rsync -av /workspace/ComfyUI/models/text_encoders/ /workspace/models/text_encoders/
   rsync -av /workspace/ComfyUI/models/clip_vision/ /workspace/models/clip_vision/
   rsync -av /workspace/ComfyUI/models/upscale_models/ /workspace/models/upscale_models/

   # Move other model types as needed
   ```

4. **Migrate Workflows**
   ```bash
   # Move workflows to new location
   rsync -av /workspace/ComfyUI/workflows/ /workspace/workflows/user/

   # Copy config
   cp /workspace/config/presets.yaml /workspace/config/presets.yaml.bak
   ```

### Phase 3: Deployment (15 minutes)

1. **Update Pod Template**
   - In RunPod console: Edit your pod template
   - Update image: `zeroclue/comfyui:base-torch2.8.0-cu126`
   - Add new environment variables:
     ```
     ENABLE_DASHBOARD: true
     ENABLE_STUDIO: true
     ```
   - Update exposed ports (add 8080, 5001)

2. **Deploy New Pod**
   - Deploy pod from updated template
   - Use same network volume
   - Wait for pod to initialize (~30 seconds)

3. **Verify Migration**
   ```bash
   # Access new dashboard
   # https://your-pod-url-8080.proxy.runpod.net

   # Check models are visible
   # Dashboard → Models

   # Test ComfyUI
   # https://your-pod-url-3000.proxy.runpod.net
   ```

### Phase 4: Validation (15 minutes)

1. **Test Model Loading**
   - Open ComfyUI
   - Load a workflow that uses different model types
   - Verify all models load correctly

2. **Test Preset Installation**
   - Go to Dashboard → Models
   - Install a test preset
   - Verify installation completes successfully

3. **Test Workflow Execution**
   - Run a simple workflow
   - Verify execution completes
   - Check outputs appear in correct location

4. **Test New Features**
   - Explore unified dashboard
   - Try ComfyUI Studio
   - Test background downloads

---

## Data Migration

### Automatic Migration Script

For complex setups, use this migration script:

```bash
#!/bin/bash
# migrate_v1_to_v2.sh

set -e

echo "Starting ComfyUI-Docker v1.x to v2.0 migration..."

# Configuration
WORKSPACE="/workspace"
BACKUP_DIR="/workspace/migration_backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup current setup
echo "Creating backup..."
rsync -av "$WORKSPACE/ComfyUI/models/" "$BACKUP_DIR/models/"
rsync -av "$WORKSPACE/ComfyUI/workflows/" "$BACKUP_DIR/workflows/"
cp "$WORKSPACE/config/presets.yaml" "$BACKUP_DIR/presets.yaml"

# Create new structure
echo "Creating new volume structure..."
mkdir -p "$WORKSPACE/models"/{checkpoints,text_encoders,vae,clip_vision,loras,upscale_models}
mkdir -p "$WORKSPACE/output"/{images,videos}
mkdir -p "$WORKSPACE/workflows"/{user,templates}
mkdir -p "$WORKSPACE/uploads"/{input,assets}
mkdir -p "$WORKSPACE/config"
mkdir -p "$WORKSPACE/cache"
mkdir -p "$WORKSPACE/logs"

# Migrate models
echo "Migrating models..."
rsync -av "$BACKUP_DIR/models/checkpoints/" "$WORKSPACE/models/checkpoints/" || true
rsync -av "$BACKUP_DIR/models/loras/" "$WORKSPACE/models/loras/" || true
rsync -av "$BACKUP_DIR/models/vae/" "$WORKSPACE/models/vae/" || true
rsync -av "$BACKUP_DIR/models/text_encoders/" "$WORKSPACE/models/text_encoders/" || true
rsync -av "$BACKUP_DIR/models/clip_vision/" "$WORKSPACE/models/clip_vision/" || true
rsync -av "$BACKUP_DIR/models/upscale_models/" "$WORKSPACE/models/upscale_models/" || true

# Migrate workflows
echo "Migrating workflows..."
rsync -av "$BACKUP_DIR/workflows/" "$WORKSPACE/workflows/user/"

# Restore config
echo "Restoring configuration..."
cp "$BACKUP_DIR/presets.yaml" "$WORKSPACE/config/presets.yaml"

echo "Migration complete!"
echo "Backup stored at: $BACKUP_DIR"
```

### Manual Migration Steps

If you prefer manual migration:

1. **Identify Model Locations**
   ```bash
   # Find all model files
   find /workspace/ComfyUI/models/ -type f -name "*.safetensors" -o -name "*.pt"
   ```

2. **Create Target Directories**
   ```bash
   # Create directories for each model type
   mkdir -p /workspace/models/{checkpoints,text_encoders,vae,clip_vision,loras,upscale_models,controlnet,ipadapter}
   ```

3. **Move Models**
   ```bash
   # Move models based on type
   # Adjust paths based on your setup
   ```

---

## Configuration Migration

### Preset Configuration

Your existing `presets.yaml` should work without modification. However, consider these updates:

**Old Format:**
```yaml
presets:
  WAN_22_5B_TIV2:
    name: "WAN 2.2 5B TIV2"
    files:
      - path: "checkpoints/wan21.safetensors"
        url: "https://..."
```

**New Format (Recommended):**
```yaml
presets:
  WAN_22_5B_TIV2:
    name: "WAN 2.2 5B TIV2"
    category: "Video Generation"
    type: "video"
    files:
      - path: "checkpoints/wan21.safetensors"
        url: "https://..."
    use_case: "High-quality video generation"
    tags: ["wan", "t2v"]
```

### Environment Variables

Update your environment variables:

```bash
# Old variables (remove)
SYNC_MODE=false
RSYNC_ON_START=false
MODEL_SYNC_SOURCE=/workspace

# New variables (add)
ENABLE_DASHBOARD=true
ENABLE_STUDIO=true
STUDIO_PORT=5000

# Keep existing variables
ACCESS_PASSWORD=your_password
PRESET_DOWNLOAD=WAN_22_5B_TIV2
TIME_ZONE=Etc/UTC
```

---

## Rollback Procedures

### If Migration Fails

1. **Stop v2.0 Pod**
   - In RunPod console: Stop the v2.0 pod

2. **Restore from Backup**
   ```bash
   # Launch temporary pod with volume
   rsync -av /workspace/migration_backup/ /workspace/
   ```

3. **Deploy v1.x Pod**
   - Use your original pod template
   - Deploy with same network volume

### If Issues Persist

1. **Identify the Issue**
   - Check logs for specific errors
   - Test with fresh volume
   - Verify model integrity

2. **Partial Rollback**
   - Roll back specific components
   - Keep working parts of v2.0
   - Gradual migration approach

3. **Get Help**
   - Check [GitHub Issues](https://github.com/ZeroClue/ComfyUI-Docker/issues)
   - Review documentation
   - Contact support

---

## Troubleshooting

### Models Not Found After Migration

**Symptoms**: ComfyUI shows missing models after migration

**Solutions**:
1. Verify `extra_model_paths.yaml` generated correctly
2. Check models are in `/workspace/models/`
3. Verify file permissions
4. Check ComfyUI logs for path issues

```bash
# Verify paths
cat /workspace/ComfyUI/models/extra_model_paths.yaml

# Check file locations
find /workspace/models/ -type f -name "*.safetensors"
```

### Preset Installation Fails

**Symptoms**: Presets fail to install after migration

**Solutions**:
1. Verify `presets.yaml` format is correct
2. Check network connectivity
3. Verify sufficient disk space
4. Review preset installation logs

```bash
# Validate preset config
python -m app.dashboard.core.preset_manager validate

# Check disk space
df -h /workspace
```

### Dashboard Not Accessible

**Symptoms**: Can't access dashboard after migration

**Solutions**:
1. Verify `ENABLE_DASHBOARD=true`
2. Check dashboard logs
3. Verify port 8080 is exposed
4. Check firewall rules

```bash
# Check dashboard status
curl http://localhost:8080/health

# Check dashboard logs
tail -f /workspace/logs/dashboard.log
```

### Performance Issues After Migration

**Symptoms**: Slower performance after migration

**Solutions**:
1. Verify network volume mount
2. Check GPU utilization
3. Monitor disk I/O
4. Review resource allocation

```bash
# Check volume performance
dd if=/dev/zero of=/workspace/test.img bs=1G count=1 oflag=direct

# Check GPU usage
nvidia-smi
```

---

## Post-Migration Checklist

After migration, verify:

- [ ] All services start successfully
- [ ] Models are accessible in ComfyUI
- [ ] Workflows execute correctly
- [ ] Preset installation works
- [ ] Dashboard is accessible
- [ ] ComfyUI Studio works
- [ ] Background downloads work
- [ ] Storage usage is as expected
- [ ] Performance is acceptable
- [ ] Backups are working

---

## Support

For migration issues:

- **Documentation**: Check [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- **Issues**: Report at [GitHub Issues](https://github.com/ZeroClue/ComfyUI-Docker/issues)
- **Community**: Join discussions in [GitHub Discussions](https://github.com/ZeroClue/ComfyUI-Docker/discussions)

---

## Migration Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Preparation | 15 minutes | None |
| Volume Migration | 30 minutes | Backup complete |
| Deployment | 15 minutes | Volume migration complete |
| Validation | 15 minutes | Deployment complete |
| **Total** | **~75 minutes** | |

---

*Document Version: 2.0.0*
*Last Updated: 2026-02-15*
