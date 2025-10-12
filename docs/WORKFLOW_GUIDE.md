# GitHub Actions Workflow Guide

This guide explains the dual workflow system for ComfyUI Docker builds.

## Overview

You now have two separate GitHub Actions workflows:

### **1. Optimized Workflow** (Automatic)
- **File**: `.github/workflows/build.yml`
- **Trigger**: Push to main branch
- **Features**: Dependency analysis, conflict resolution, optimization
- **Purpose**: Production builds with full optimization

### **2. Legacy Workflow** (Manual)
- **File**: `.github/workflows/build-legacy.yml`
- **Trigger**: Manual dispatch only
- **Features**: Original build process, no analysis
- **Purpose**: Manual builds, testing, fallbacks

## Workflow Comparison

| Feature | Optimized Workflow | Legacy Workflow |
|---------|-------------------|-----------------|
| **Trigger** | Automatic on push | Manual only |
| **Dependency Analysis** | ✅ Yes | ❌ No |
| **Conflict Resolution** | ✅ Yes | ❌ No |
| **Multi-stage Build** | ✅ Yes | ❌ No |
| **Size Optimization** | ✅ 60-80% reduction | ❌ Original size |
| **Build Time** | Slightly longer | Faster |
| **Error Prevention** | ✅ Prevents conflicts | ❌ No prevention |
| **Validation** | ✅ Automated | ❌ Manual |

## Usage Scenarios

### **Normal Development** (Recommended)
```bash
# Make your changes
git add .
git commit -m "Add new custom node"
git push origin main

# Result: Automatic optimized build with conflict analysis
```

### **Manual Legacy Build**
1. Go to **Actions** tab in GitHub
2. Select **"Build and Push ZeroClue Docker Images (Legacy)"**
3. Click **"Run workflow"**
4. Choose your targets and CUDA versions
5. Click **"Run workflow"**

### **When to Use Legacy Workflow**

**Use Legacy when:**
- Testing new custom nodes without analysis overhead
- Emergency builds if optimization has issues
- Quick development builds
- Compatibility verification with existing workflows
- Need faster builds for testing

**Use Optimized when:**
- Production deployments
- Normal development workflow
- Want the benefits of conflict detection
- Need smaller, optimized images

## Build Targets

### **Optimized Workflow Targets**
```yaml
# New optimized variants
base-optimized-12-6    # Full installation with optimization
base-optimized-12-8
slim-optimized-12-6    # No custom nodes, optimized
slim-optimized-12-8
production-optimized-12-6  # Production-ready, minimal
production-optimized-12-8

# Compatibility variants (still optimized)
base-12-6             # Original base variant (now optimized)
base-12-8
slim-12-6             # Original slim variant (now optimized)
slim-12-8
```

### **Legacy Workflow Targets**
```yaml
# Original variants using original Dockerfile
base-12-6             # Full installation
base-12-8
slim-12-6             # No custom nodes
slim-12-8
minimal-12-6          # No custom nodes, no code-server
minimal-12-8
production-12-6       # Production-ready
production-12-8
ultra-slim-12-6       # Minimal size
ultra-slim-12-8
```

## Workflow Examples

### **Example 1: Adding a New Custom Node**

```bash
# 1. Add node to custom_nodes.txt
echo "https://github.com/user/new-node.git" >> custom_nodes.txt

# 2. Push to trigger optimized build
git add custom_nodes.txt
git commit -m "Add new custom node"
git push origin main

# 3. Check GitHub Actions for:
#    - Dependency analysis results
#    - Conflict detection
#    - Build success/failure
#    - Optimized image creation
```

### **Example 2: Quick Testing with Legacy Build**

1. Go to **Actions → "Build and Push ZeroClue Docker Images (Legacy)"**
2. Click **"Run workflow"**
3. Set inputs:
   - `targets`: `base,slim`
   - `cuda_versions`: `12-6`
4. Click **"Run workflow"**
5. Monitor build progress

### **Example 3: Handling Build Failures**

**Optimized Workflow Failure:**
```
❌ Dependency Analysis Failed
   - High-severity conflicts detected
   - Build stopped to prevent issues
```

**Solution Options:**
1. **Fix conflicts** - Resolve dependency issues in custom nodes
2. **Use Legacy** - Run manual legacy build for testing
3. **Remove problematic node** - Temporarily remove conflicting node

**Fallback to Legacy:**
```bash
# If optimized build fails, use legacy
# GitHub Actions → Legacy Workflow → Run
```

## Monitoring and Debugging

### **Build Status**

**Optimized Workflow:**
- Check **Actions** tab for automatic builds
- Look for dependency analysis comments on PRs
- Review build summaries for optimization status

**Legacy Workflow:**
- Check **Actions** tab for manual builds
- Review build logs for issues
- No dependency analysis comments

### **Build Artifacts**

**Optimized Workflow:**
- `custom_nodes_analysis.json` - Detailed analysis results
- `dependency_resolution.json` - Resolution strategies
- Build logs with optimization details

**Legacy Workflow:**
- Standard Docker build logs
- No analysis artifacts

### **Troubleshooting**

**Optimized Build Issues:**
```bash
# Check local analysis first
python scripts/analyze_requirements.py custom_nodes.txt

# Review conflicts
cat custom_nodes_analysis.json | jq '.conflicts'

# If analysis fails, use legacy
```

**Legacy Build Issues:**
```bash
# Standard Docker debugging
docker build -t test .
docker run --rm test bash

# Check custom nodes manually
ls /workspace/ComfyUI/custom_nodes/
```

## Best Practices

### **Development Workflow**
1. **Use optimized workflow** for normal development
2. **Review analysis results** before pushing
3. **Use legacy workflow** only when needed
4. **Monitor both workflows** for issues

### **Before Adding Custom Nodes**
```bash
# Local analysis first
python scripts/analyze_requirements.py custom_nodes.txt

# Check for conflicts
python scripts/dependency_resolver.py custom_nodes_analysis.json

# Push if no critical conflicts
git push origin main
```

### **Emergency Procedures**
1. **Identify issue** in optimized build
2. **Run legacy build** for immediate needs
3. **Fix root cause** in custom nodes
4. **Return to optimized workflow**

### **Maintenance**
- **Monitor optimized build performance**
- **Keep legacy workflow available** for fallbacks
- **Update both workflows** when making changes
- **Document any workflow-specific issues**

## Migration Path

### **From Legacy to Optimized**
1. **Test optimized builds** in development
2. **Review analysis results** for conflicts
3. **Update CI/CD processes** if needed
4. **Monitor production performance**

### **Rollback to Legacy**
1. **Identify optimization issues**
2. **Use legacy workflow** temporarily
3. **Fix optimization problems**
4. **Return to optimized when ready**

## Advanced Configuration

### **Custom Build Targets**

**For optimized builds:**
- Modify `.github/workflows/build.yml` matrix
- Add new `base-optimized-*` targets
- Update `docker-bake-optimized.hcl`

**For legacy builds:**
- Modify `.github/workflows/build-legacy.yml` matrix
- Add new standard targets
- Update `docker-bake.hcl`

### **Build Parameters**

**Optimized Workflow:**
- Automatic based on main branch push
- No manual configuration needed
- Uses latest analysis and optimization

**Legacy Workflow:**
- Manual target selection
- Manual CUDA version selection
- Uses original build parameters

## Support

### **Getting Help**
- **GitHub Issues**: Report workflow-specific problems
- **Actions Tab**: Monitor build status and logs
- **Documentation**: Check `OPTIMIZED_BUILD_SYSTEM.md`
- **Community**: GitHub discussions for tips

### **Common Issues**
- **Build failures**: Check dependency analysis results
- **Permission errors**: Verify GitHub Actions permissions
- **Docker Hub issues**: Check repository access tokens
- **Resource limits**: Monitor GitHub Actions runner usage

This dual workflow system provides maximum flexibility while maintaining production-ready automation for optimized builds.