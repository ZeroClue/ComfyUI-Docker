# ComfyUI-Docker Deployment Guide

**Version:** 2.0.0
**Last Updated:** 2026-02-15

## Table of Contents

- [Overview](#overview)
- [RunPod Deployment](#runpod-deployment)
- [Volume Setup](#volume-setup)
- [First-Run Configuration](#first-run-configuration)
- [Production Deployment](#production-deployment)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

---

## Overview

This guide covers deploying ComfyUI-Docker v2.0 to production, with a focus on RunPod cloud deployment. The revolutionary architecture enables instant startup (<30s) and persistent storage through network volumes.

### Deployment Options

1. **RunPod Cloud** (Recommended) - GPU cloud platform with native network volumes
2. **Local Docker** - For development and testing
3. **Other Cloud Platforms** - AWS, GCP, Azure with Docker

### Prerequisites

- Docker and Docker Compose (for local deployment)
- RunPod account (for cloud deployment)
- Basic understanding of ComfyUI and AI models
- SSH access (for remote deployment)

---

## RunPod Deployment

### Step 1: Create Network Volume

Network volumes provide persistent storage that survives container restarts.

1. **Access RunPod Console**
   - Go to https://www.runpod.io/console
   - Navigate to **Network Volumes**

2. **Create New Volume**
   ```
   Name: comfyui-workspace
   Size: 200GB (adjust based on needs)
   Region: Same region as your planned GPU pods
   ```

3. **Note Volume ID**
   ```
   Volume ID: Your-Volume-ID-Here
   Save this for pod configuration
   ```

### Step 2: Create Pod Template

Create a reusable pod template for easy deployment.

1. **Navigate to Templates**
   - Go to **Templates** → **Create Template**

2. **Basic Configuration**
   ```
   Name: ComfyUI-Docker v2.0
   Container Image: zeroclue/comfyui:base-torch2.8.0-cu126
   Container Disk Size: 50GB (minimum)
   ```

3. **Volume Mapping**
   ```
   Mount Path: /workspace
   Network Volume: comfyui-workspace (select from dropdown)
   ```

4. **Environment Variables**
   ```
   ACCESS_PASSWORD: your_secure_password_here
   PRESET_DOWNLOAD: WAN_22_5B_TIV2,SDXL_BASE_V1
   TIME_ZONE: Etc/UTC
   ```

5. **Exposed Ports**
   ```
   3000 (HTTP) - ComfyUI
   8082 (HTTP) - Unified Dashboard (Primary Interface)
   8080 (HTTP) - code-server
   8888 (HTTP) - JupyterLab
   ```

6. **Save Template**

### Step 3: Deploy Pod

1. **Deploy from Template**
   - Go to **Templates**
   - Select **ComfyUI-Docker v2.0**
   - Click **Deploy**

2. **Select GPU Type**
   ```
   Recommended: NVIDIA RTX 4090
   Alternative: A100 80GB (for large models)
   Budget: RTX 4000 Ada or A40
   ```

3. **Configure Pod Settings**
   ```
   Pod Name: comfyui-prod-1
   Min Pods: 1 (for auto-scaling)
   Max Pods: 3 (for auto-scaling)
   ```

4. **Launch Pod**
   - Click **Deploy**
   - Wait for pod to initialize (~30 seconds)
   - Note the pod URL

### Step 4: Access Services

Once deployed, access the services through RunPod's proxy:

```
ComfyUI:        https://your-pod-id-3000.proxy.runpod.net
Dashboard:      https://your-pod-id-8080.proxy.runpod.net
Preset Manager:  https://your-pod-id-9000.proxy.runpod.net
Studio:         https://your-pod-id-5001.proxy.runpod.net
```

### Step 5: Initial Configuration

1. **Login with Password**
   - Use the `ACCESS_PASSWORD` you set in the template
   - All services use the same password

2. **Verify Setup**
   - Check dashboard shows correct storage usage
   - Verify preset manager lists available presets
   - Test ComfyUI interface loads

---

## Volume Setup

### Volume Structure

Network volumes are organized as follows:

```
/workspace/
├── models/              # All AI models
│   ├── checkpoints/     # Main diffusion models
│   ├── text_encoders/   # T5, CLIP, etc.
│   ├── vae/             # VAE models
│   ├── clip_vision/     # Image encoders
│   ├── loras/           # LoRA adapters
│   └── upscale_models/  # Upscaling models
├── output/              # Generated content
│   ├── images/          # Generated images
│   └── videos/          # Generated videos
├── workflows/           # User workflows
├── config/              # Configuration files
└── cache/               # Download cache
```

### Initial Volume Setup

The container automatically creates the directory structure on first run. No manual setup required.

### Volume Management

#### Check Volume Usage

```bash
# SSH into pod
ssh root@<pod-url>

# Check volume usage
df -h /workspace

# Check model sizes
du -sh /workspace/models/*
```

#### Expand Volume

If you need more storage:

1. **In RunPod Console**
   - Go to **Network Volumes**
   - Select your volume
   - Click **Expand**
   - Enter new size (e.g., 500GB)

2. **Verify in Pod**
   ```bash
   # Check new size
   df -h /workspace
   ```

#### Backup Volume

```bash
# Create snapshot (in RunPod Console)
Network Volumes → comfyui-workspace → Create Snapshot

# Or manually backup important data
rsync -av /workspace/models/ /backup/models/
```

---

## First-Run Configuration

### Initial Setup Wizard

On first run, the container performs automatic setup:

1. **Volume Health Check** (5s)
   - Verify network volume mount
   - Test write access
   - Create directory structure

2. **Configuration Generation** (3s)
   - Generate extra_model_paths.yaml
   - Set up model paths
   - Initialize preset system

3. **Service Startup** (15s)
   - Start ComfyUI
   - Start Dashboard
   - Start Preset Manager

4. **Health Verification** (5s)
   - Verify all services responding
   - Check connectivity
   - Report ready state

### Initial Preset Installation

1. **Via Environment Variable**
   ```
   PRESET_DOWNLOAD=WAN_22_5B_TIV2,SDXL_BASE_V1
   ```

2. **Via Dashboard UI**
   - Go to Dashboard → Models
   - Browse available presets
   - Click Install on desired presets

3. **Via Preset Manager**
   - Go to Preset Manager
   - Select presets to install
   - Monitor progress in real-time

### Verify Installation

```bash
# Check models installed
ls -la /workspace/models/checkpoints/

# Verify ComfyUI sees models
curl http://localhost:3000/system_stats

# Check dashboard model list
curl http://localhost:8080/api/models
```

---

## Production Deployment

### Production Checklist

Before deploying to production:

- [ ] Network volume created and mounted
- [ ] Secure ACCESS_PASSWORD configured
- [ ] Required presets installed
- [ ] Services tested and verified
- [ ] Monitoring configured
- [ ] Backup strategy in place
- [ ] Auto-scaling configured (if needed)
- [ ] Custom domain configured (optional)

### Security Hardening

1. **Strong Passwords**
   ```
   # Use strong, unique passwords
   ACCESS_PASSWORD: your-secure-random-password
   ```

2. **SSH Keys**
   ```bash
   # Add SSH public key to pod
   # In pod template: Add SSH Key
   ```

3. **Network Access**
   ```
   # Use RunPod's proxy for secure access
   # Or configure custom domain with SSL
   ```

4. **Firewall Rules**
   ```
   # Only expose necessary ports
   # Use VPN for admin access
   ```

### Performance Tuning

1. **GPU Selection**
   ```
   High Performance: RTX 4090 or A100 80GB
   Balanced: A40 or RTX 6000 Ada
   Budget: RTX 4000 Ada
   ```

2. **Container Resources**
   ```
   CPU: 8+ cores for optimal performance
   Memory: 32GB+ for large models
   Disk: 50GB minimum for container
   ```

3. **Concurrency**
   ```
   Multiple ComfyUI instances: Use multiple pods
   Background processing: Enable parallel downloads
   ```

### Auto-Scaling Configuration

Configure auto-scaling for variable workload:

```yaml
# In RunPod template
Min Pods: 1
Max Pods: 5
Scale Up Trigger: CPU > 80% for 5 minutes
Scale Down Trigger: CPU < 20% for 10 minutes
```

### Custom Domain Setup

1. **Configure DNS**
   ```
   A Record: comfyui.yourdomain.com → RunPod proxy URL
   ```

2. **SSL Certificate**
   ```
   Use Cloudflare or Let's Encrypt for SSL
   ```

3. **Update Environment**
   ```
   DOMAIN: comfyui.yourdomain.com
   SSL_ENABLED: true
   ```

---

## Monitoring and Maintenance

### Health Monitoring

Monitor these endpoints:

```bash
# Dashboard health
curl https://your-pod-url-8080.proxy.runpod.net/health

# ComfyUI health
curl https://your-pod-url-3000.proxy.runpod.net/system_stats

# Preset Manager health
curl https://your-pod-url-9000.proxy.runpod.net/health
```

### Log Monitoring

```bash
# View container logs
docker logs -f comfyui-container

# View service logs
tail -f /workspace/logs/dashboard.log
tail -f /workspace/logs/comfyui.log
tail -f /workspace/logs/preset_manager.log
```

### Resource Monitoring

Monitor key resources:

- **GPU Usage**: Keep below 95% to avoid OOM
- **Disk Usage**: Keep below 80% to avoid issues
- **Memory Usage**: Monitor for leaks
- **Network I/O**: Check download speeds

### Regular Maintenance

#### Weekly Tasks

- [ ] Check for image updates
- [ ] Review disk usage
- [ ] Clean up temporary files
- [ ] Backup important workflows

#### Monthly Tasks

- [ ] Review and update presets
- [ ] Clean unused models
- [ ] Update container image
- [ ] Test backup restoration

### Updates and Upgrades

#### Update Container Image

```bash
# Pull latest image
docker pull zeroclue/comfyui:base-torch2.8.0-cu126

# Stop current container
docker stop comfyui-prod

# Remove old container
docker rm comfyui-prod

# Start new container with same configuration
docker run -d \
  --name comfyui-prod \
  --gpus all \
  -v comfyui-workspace:/workspace \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

#### Update Presets

Presets are automatically updated at container startup from the latest GitHub configuration.

---

## Troubleshooting

### Common Issues

#### Container Won't Start

**Symptoms**: Pod fails to initialize

**Solutions**:
1. Check volume is properly mounted
2. Verify volume is in same region as pod
3. Check container logs in RunPod console
4. Ensure sufficient GPU availability

#### Services Not Responding

**Symptoms**: 504 Gateway Timeout

**Solutions**:
1. Wait for full startup (max 30s)
2. Check service health endpoints
3. Review service logs for errors
4. Verify network connectivity

#### Models Not Found

**Symptoms**: ComfyUI shows missing models

**Solutions**:
1. Check extra_model_paths.yaml generated
2. Verify models in /workspace/models/
3. Check preset installation completed
4. Review ComfyUI logs for path issues

#### Slow Performance

**Symptoms**: Downloads or generation slow

**Solutions**:
1. Check GPU utilization
2. Verify network bandwidth
3. Check for disk I/O bottlenecks
4. Monitor temperature throttling

### Debug Commands

```bash
# Check volume mount
mount | grep workspace

# Check disk space
df -h /workspace

# Check service status
systemctl status comfyui
systemctl status dashboard

# Test model loading
python -c "import folder_paths; print(folder_paths.get_folder_paths())"

# Check connectivity
curl -v http://localhost:8080/health
curl -v http://localhost:3000/system_stats
```

### Emergency Procedures

#### Container Unresponsive

1. **Force Restart**
   - In RunPod console: Stop Pod
   - Wait 30 seconds
   - Start Pod

2. **Check Volume Corruption**
   ```bash
   # If volume won't mount
   # Create new volume and restore from backup
   ```

#### Data Recovery

1. **Access Volume Directly**
   ```bash
   # Mount volume to recovery pod
   # Copy important data
   rsync -av /workspace/ /recovery/
   ```

2. **Restore from Snapshot**
   - In RunPod console: Restore Volume Snapshot
   - Select snapshot to restore
   - Confirm restore

---

## Best Practices

### Development vs Production

**Development**:
- Use `base` variant for full tooling
- Enable debug logging
- Use lower GPU tiers
- Test changes locally first

**Production**:
- Use `slim` variant for faster startup
- Use strong passwords
- Monitor resource usage
- Set up auto-scaling
- Configure backups

### Cost Optimization

1. **Use Appropriate GPU**
   - Don't over-provision GPU
   - Use spot instances when possible
   - Scale down when not in use

2. **Storage Optimization**
   - Clean unused models regularly
   - Compress old outputs
   - Use appropriate volume size

3. **Network Transfer**
   - Minimize data transfer costs
   - Use CDN for static assets
   - Cache models locally when possible

### High Availability

1. **Multi-Pod Setup**
   ```
   Deploy multiple pods with shared network volume
   Use load balancer for distribution
   Configure health checks
   ```

2. **Auto-Scaling**
   ```
   Set min/max pod limits
   Configure scale triggers
   Test scaling behavior
   ```

3. **Disaster Recovery**
   ```
   Regular volume snapshots
   Backup critical workflows
   Document recovery procedures
   Test restoration process
   ```

### Security Best Practices

1. **Access Control**
   - Use strong passwords
   - Enable SSH key authentication
   - Limit network exposure
   - Use VPN for admin access

2. **Data Protection**
   - Regular backups
   - Encrypt sensitive data
   - Secure API keys
   - Monitor access logs

3. **Update Management**
   - Keep images updated
   - Test updates before production
   - Monitor security advisories
   - Plan update windows

---

## Support

For deployment issues:

- **Documentation**: Check [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- **Troubleshooting**: Review [README.md](../README.md) troubleshooting section
- **Issues**: Report at [GitHub Issues](https://github.com/ZeroClue/ComfyUI-Docker/issues)
- **RunPod Support**: https://docs.runpod.io/

---

*Document Version: 2.0.0*
*Last Updated: 2026-02-15*
