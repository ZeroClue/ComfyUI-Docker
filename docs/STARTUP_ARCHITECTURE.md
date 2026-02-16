# Startup Orchestration Architecture

## Overview

The revolutionary startup orchestration system implements a 4-phase startup flow designed for speed and reliability, targeting **<30 seconds total startup time**.

## Architecture Principles

1. **No rsync**: Eliminated for performance - models stay on network volume
2. **Immutable app code**: All application code pre-built at `/app/`
3. **Network volume models**: Models stored at `/workspace/models`
4. **Background services**: All services start asynchronously
5. **Graceful shutdown**: Proper SIGTERM/SIGINT handling

## Phase Breakdown

### Phase 1: Volume & Config Setup (Target: <8 seconds)

**Purpose**: Verify workspace and generate configuration

**Operations**:
- Create log directory (`/workspace/logs`)
- Verify workspace mount accessibility
- Generate `extra_model_paths.yaml` for ComfyUI
- Create workspace directory structure
- Set up symlinks for models and I/O directories

**Key Files**:
- `/app/scripts/generate_extra_paths.py`: Config generator
- `/app/comfyui/extra_model_paths.yaml`: Generated config

### Phase 2: Service Startup (Target: <15 seconds)

**Purpose**: Start core services

**Operations**:
- Start Nginx (reverse proxy)
- Start SSH (if `PUBLIC_KEY` provided)
- Start ComfyUI in background
- Wait for ComfyUI health check

**Health Check**:
- Endpoint: `http://localhost:3000/system_stats`
- Timeout: 30 seconds
- Process monitoring: `python.*main.py`

### Phase 3: Dashboard Startup (Target: <5 seconds)

**Purpose**: Start optional dashboard services

**Operations**:
- Start Preset Manager (if `ENABLE_PRESET_MANAGER=true`)
- Start background preset downloads (if configured)
- Start Code Server (if `ENABLE_CODE_SERVER=true`)
- Start JupyterLab (if `ENABLE_JUPYTERLAB=true`)

**Background Downloads**:
- Triggered by: `PRESET_DOWNLOAD`, `IMAGE_PRESET_DOWNLOAD`, `AUDIO_PRESET_DOWNLOAD`
- Log file: `/workspace/logs/preset_downloads.log`

### Phase 4: Health Verification (Target: <2 seconds)

**Purpose**: Verify system readiness

**Checks**:
- Workspace accessibility
- ComfyUI service health
- Nginx process status
- Preset Manager process status

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_PRESET_MANAGER` | `true` | Enable Preset Manager web UI |
| `ENABLE_CODE_SERVER` | `true` | Enable VS Code server |
| `ENABLE_JUPYTERLAB` | `true` | Enable JupyterLab |
| `ACCESS_PASSWORD` | (none) | Password for web services |
| `PUBLIC_KEY` | (none) | SSH public key for access |
| `PRESET_DOWNLOAD` | (none) | Video presets to install |
| `IMAGE_PRESET_DOWNLOAD` | (none) | Image presets to install |
| `AUDIO_PRESET_DOWNLOAD` | (none) | Audio presets to install |

### Paths

| Path | Purpose |
|------|---------|
| `/app` | Immutable application code |
| `/app/comfyui` | ComfyUI installation |
| `/app/venv` | Python virtual environment |
| `/workspace` | Network volume mount |
| `/workspace/models` | Model storage |
| `/workspace/logs` | Log files |
| `/workspace/config` | Configuration files |

### Service Ports

| Service | Port |
|---------|------|
| ComfyUI | 3000 |
| Code Server | 8080 |
| JupyterLab | 8888 |
| Preset Manager | 9000 (via Nginx) |
| SSH | 22 |

## Service Management

### Process Tracking

All services track PIDs in `/workspace/logs/*.pid`:
- `comfyui.pid`: ComfyUI process
- `preset_manager.pid`: Preset Manager
- `preset_downloads.pid`: Background downloader
- `code-server.pid`: Code Server
- `jupyterlab.pid`: JupyterLab

### Graceful Shutdown

1. Receive SIGTERM/SIGINT
2. Read all PID files
3. Send SIGTERM to each service
4. Wait up to 10 seconds for graceful shutdown
5. Send SIGKILL if still running
6. Clean up PID files
7. Exit

### Log Files

All services log to `/workspace/logs/`:
- `setup.log`: Volume setup and config generation
- `nginx.log`: Nginx startup and operation
- `ssh.log`: SSH service
- `comfyui.log`: ComfyUI main process
- `preset_manager.log`: Preset Manager
- `preset_downloads.log`: Background downloads
- `code-server.log`: Code Server
- `jupyterlab.log`: JupyterLab

## Performance Monitoring

### Timing Targets

- Phase 1: <8 seconds
- Phase 2: <15 seconds
- Phase 3: <5 seconds
- Phase 4: <2 seconds
- **Total: <30 seconds**

### Timing Output

The script reports actual vs target times for each phase:
```
[SUCCESS] Phase 1 completed in 2.345s (target: 8s)
[SUCCESS] Phase 2 completed in 12.123s (target: 15s)
```

## Error Handling

### Phase Failures

- **Phase 1**: Critical - exits with code 1
- **Phase 2**: Critical - exits with code 1
- **Phase 3**: Non-critical - logs warnings, continues
- **Phase 4**: Non-critical - logs warnings, continues

### Service Failures

Individual service failures are logged but don't stop startup:
- Service startup failures are logged to respective log files
- Health check failures are reported as warnings
- Container remains operational even if optional services fail

## Extension Points

### Pre-start Script

If `/pre_start.sh` exists, it runs before Phase 1.

### Post-start Script

If `/post_start.sh` exists, it runs after Phase 4 completes.

### Custom Services

Add new services by:
1. Creating a start function following the pattern
2. Adding the function to the appropriate phase
3. Implementing PID tracking and logging
4. Adding health checks if needed

## Migration from Old Architecture

### Key Changes

1. **No rsync**: Models no longer synced from container to volume
2. **App code at `/app/`**: Instead of `/workspace/venv` and `/workspace/ComfyUI`
3. **Symlinks instead of copies**: For model and I/O directories
4. **Background downloads**: Presets download asynchronously

### Compatibility

The new architecture is **backward compatible** with:
- Existing model locations (`/workspace/models`)
- Environment variables for service configuration
- Preset download variables
- SSH access configuration

## Troubleshooting

### Startup Exceeds Target Time

1. Check phase timing in startup output
2. Review log files for slow operations
3. Verify network volume performance
4. Check for model download delays

### Service Failures

1. Check service-specific log in `/workspace/logs/`
2. Verify PID files exist
3. Check process status: `ps aux | grep <service>`
4. Review health check endpoints

### Workspace Issues

1. Verify mount: `mount | grep workspace`
2. Check permissions: `ls -la /workspace`
3. Test write access: `touch /workspace/test`

## Future Enhancements

Potential improvements for future iterations:

1. **Parallel phase execution**: Run independent operations concurrently
2. **Dynamic timing targets**: Adjust targets based on hardware
3. **Service dependency graph**: Automatic startup ordering
4. **Health check retries**: Configurable retry logic
5. **Metrics export**: Export timing data for monitoring
