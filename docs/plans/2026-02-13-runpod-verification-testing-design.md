# RunPod Verification Testing Design

**Date:** 2026-02-13
**Goal:** Verify GitHub Issue #5 fix by testing preset manager functionality on actual RunPod deployment

## Overview

Create one CPU pod, test both verified images (slim-12-6 and modern-12-6) sequentially, then terminate.

**Estimated Cost:** ~$0.30-0.50 total (20-30 min runtime)

## Images to Test

1. `zeroclue/comfyui:slim-torch2.8.0-cu126`
2. `zeroclue/comfyui:modern-torch2.8.0-cu126`

## Test Sequence

### Phase 1: Production Image Test

1. Create CPU pod with slim image
2. Wait for container startup (~2-3 min)
3. Run verification tests:
   - Check preset_manager imports
   - Check web UI on port 9000
   - Check ComfyUI on port 3000
   - List presets via API
   - Verify config files exist
4. Record results

### Phase 2: Modern Image Test

1. Terminate slim pod
2. Create CPU pod with modern image
3. Run same verification tests
4. Record results

### Phase 3: Cleanup

1. Terminate pod
2. Report findings to GitHub issue #5

## Verification Tests

| Test | Command | Expected Result |
|------|---------|-----------------|
| Import validation | `python3 -c "from preset_manager.core import ModelManager"` | No errors |
| Web UI | `curl -s localhost:9000 \| head -20` | HTML response |
| ComfyUI | `curl -s localhost:3000` | Response (may be redirect) |
| Preset API | `curl -s localhost:9000/api/presets` | JSON with preset list |
| Config files | `ls /workspace/config/` | presets.yaml present |

## Success Criteria

- [ ] Both containers start without errors
- [ ] Preset manager imports work
- [ ] Web UI accessible on port 9000
- [ ] ComfyUI accessible on port 3000
- [ ] Preset list API returns data
- [ ] Config files present in /workspace/config/

## Cost Breakdown

- CPU pod: ~$0.10-0.20/hr
- Total runtime: ~20-30 min
- **Estimated total: $0.30-0.50**

## Next Steps

1. Get RunPod API key from user
2. Create pod programmatically
3. Execute tests
4. Document results
5. Update GitHub issue #5
