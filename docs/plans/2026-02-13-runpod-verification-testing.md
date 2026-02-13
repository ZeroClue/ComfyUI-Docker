# RunPod Verification Testing Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Verify GitHub Issue #5 fix by testing preset manager functionality on RunPod with both verified Docker images.

**Architecture:** Sequential pod testing - create CPU pod, test production image, terminate, create new pod, test modern image, report results.

**Tech Stack:** RunPod API, curl, Python, bash

---

## Prerequisites

- RunPod API key (user will provide)
- `curl` and `jq` available
- Docker images already pushed to Docker Hub:
  - `zeroclue/comfyui:production-torch2.8.0-cu126`
  - `zeroclue/comfyui:modern-torch2.8.0-cu126`

---

### Task 1: Set Up RunPod API Access

**Files:**
- Create: `scripts/test_runpod.sh`

**Step 1: Store API key securely**

Ask user for RunPod API key and store in environment:
```bash
export RUNPOD_API_KEY="your-api-key-here"
```

**Step 2: Verify API access**

Run:
```bash
curl -s -H "Authorization: Bearer $RUNPOD_API_KEY" \
  "https://api.runpod.io/v2/pods" | jq '.'
```
Expected: JSON response with pod list (may be empty)

**Step 3: Get available GPU/CPU types**

Run:
```bash
curl -s -H "Authorization: Bearer $RUNPOD_API_KEY" \
  "https://api.runpod.io/v2/gpu-types" | jq '.[] | select(.id | contains("CPU")) | {id, name, hourly_cost}'
```
Expected: List of CPU pod types with pricing

---

### Task 2: Create Test Script

**Files:**
- Create: `scripts/test_runpod.sh`

**Step 1: Create verification test script**

```bash
#!/bin/bash
# scripts/test_runpod.sh
# RunPod Verification Testing Script

set -e

IMAGE_NAME="${1:-zeroclue/comfyui:production-torch2.8.0-cu126}"
POD_NAME="${2:-comfyui-test}"

echo "=== RunPod Verification Testing ==="
echo "Image: $IMAGE_NAME"
echo "Pod Name: $POD_NAME"
echo ""

# Test functions
test_imports() {
    echo "Testing preset_manager imports..."
    python3 -c "from preset_manager.core import ModelManager; print('✓ Import OK')"
}

test_web_ui() {
    echo "Testing Web UI on port 9000..."
    if curl -s --max-time 5 "http://localhost:9000" | grep -q "html"; then
        echo "✓ Web UI accessible"
    else
        echo "✗ Web UI not accessible"
    fi
}

test_comfyui() {
    echo "Testing ComfyUI on port 3000..."
    if curl -s --max-time 5 "http://localhost:3000" > /dev/null 2>&1; then
        echo "✓ ComfyUI accessible"
    else
        echo "✗ ComfyUI not accessible"
    fi
}

test_preset_api() {
    echo "Testing Preset API..."
    if curl -s --max-time 5 "http://localhost:9000/api/presets" | jq -e '.presets' > /dev/null 2>&1; then
        echo "✓ Preset API working"
    else
        echo "✗ Preset API not working"
    fi
}

test_config_files() {
    echo "Testing config files..."
    if [ -f "/workspace/config/presets.yaml" ]; then
        echo "✓ presets.yaml found"
    else
        echo "✗ presets.yaml not found"
    fi
}

# Run all tests
echo "Running verification tests..."
test_imports
test_web_ui
test_comfyui
test_preset_api
test_config_files

echo ""
echo "=== Tests Complete ==="
```

**Step 2: Make script executable**

Run:
```bash
chmod +x scripts/test_runpod.sh
```

**Step 3: Commit**

```bash
git add scripts/test_runpod.sh
git commit -m "Add RunPod verification test script"
```

---

### Task 3: Create Production Pod and Test

**Files:**
- None (API calls only)

**Step 1: Create CPU pod with production image**

Run:
```bash
curl -s -X POST \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  "https://api.runpod.io/v2/pods" \
  -d '{
    "name": "comfyui-production-test",
    "imageName": "zeroclue/comfyui:production-torch2.8.0-cu126",
    "gpuTypeId": "NVIDIA A100",
    "cloudType": "SECURE",
    "networkVolumeId": null
  }' | jq '.'
```
Expected: JSON with pod ID and status

**Step 2: Wait for pod to be running**

Run:
```bash
# Replace POD_ID with actual pod ID from Step 1
POD_ID="<pod-id-from-step-1>"
curl -s -H "Authorization: Bearer $RUNPOD_API_KEY" \
  "https://api.runpod.io/v2/pods/$POD_ID" | jq '.status'
```
Repeat until status is "RUNNING" (may take 2-5 minutes)

**Step 3: Get pod SSH connection**

Run:
```bash
curl -s -H "Authorization: Bearer $RUNPOD_API_KEY" \
  "https://api.runpod.io/v2/pods/$POD_ID" | jq '.runtime.connect.ssh'
```
Expected: SSH connection string

**Step 4: Connect and run tests**

Run:
```bash
ssh -o StrictHostKeyChecking=no <ssh-connection-string>
# Inside pod, run verification tests
python3 -c "from preset_manager.core import ModelManager; print('✓ Import OK')"
curl -s localhost:9000 | head -5
curl -s localhost:3000 | head -5
ls /workspace/config/
```

**Step 5: Record results**

Document test results for production image.

---

### Task 4: Terminate Production Pod

**Files:**
- None (API calls only)

**Step 1: Terminate pod**

Run:
```bash
curl -s -X DELETE \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  "https://api.runpod.io/v2/pods/$POD_ID" | jq '.'
```
Expected: JSON confirming termination

---

### Task 5: Create Modern Pod and Test

**Files:**
- None (API calls only)

**Step 1: Create CPU pod with modern image**

Run:
```bash
curl -s -X POST \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  "https://api.runpod.io/v2/pods" \
  -d '{
    "name": "comfyui-modern-test",
    "imageName": "zeroclue/comfyui:modern-torch2.8.0-cu126",
    "gpuTypeId": "NVIDIA A100",
    "cloudType": "SECURE",
    "networkVolumeId": null
  }' | jq '.'
```

**Step 2: Wait for pod to be running**

Same as Task 3, Step 2.

**Step 3: Connect and run tests**

Same as Task 3, Step 4.

**Step 4: Record results**

Document test results for modern image.

---

### Task 6: Cleanup and Report

**Files:**
- None (API calls only)

**Step 1: Terminate pod**

Run:
```bash
curl -s -X DELETE \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  "https://api.runpod.io/v2/pods/$POD_ID" | jq '.'
```

**Step 2: Update GitHub issue #5**

Run:
```bash
gh issue comment 5 --repo ZeroClue/ComfyUI-Docker --body "## Verification Test Results

### Production Image (zeroclue/comfyui:production-torch2.8.0-cu126)
- [ ] Preset manager imports: [RESULT]
- [ ] Web UI (port 9000): [RESULT]
- [ ] ComfyUI (port 3000): [RESULT]
- [ ] Preset API: [RESULT]
- [ ] Config files: [RESULT]

### Modern Image (zeroclue/comfyui:modern-torch2.8.0-cu126)
- [ ] Preset manager imports: [RESULT]
- [ ] Web UI (port 9000): [RESULT]
- [ ] ComfyUI (port 3000): [RESULT]
- [ ] Preset API: [RESULT]
- [ ] Config files: [RESULT]

### Conclusion
[SUMMARY OF RESULTS]"
```

---

## Success Criteria

- [ ] Both images start without errors
- [ ] Preset manager imports work
- [ ] Web UI accessible on port 9000
- [ ] ComfyUI accessible on port 3000
- [ ] Preset list API returns data
- [ ] Config files present
- [ ] GitHub issue updated with results

---

## Cost Estimate

- CPU pod: ~$0.10-0.20/hr
- Total runtime: ~20-30 min
- **Estimated total: $0.30-0.50**
