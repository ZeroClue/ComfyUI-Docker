#!/bin/bash
# RunPod API Test Script
# Usage: source .runpod/.env && ./scripts/test_runpod.sh

set -e

# Check if RUNPOD_API_KEY is set
if [ -z "$RUNPOD_API_KEY" ]; then
    echo "Error: RUNPOD_API_KEY not set"
    echo "Please run: source .runpod/.env"
    exit 1
fi

API_BASE="https://rest.runpod.io/v1"
AUTH_HEADER="Authorization: Bearer $RUNPOD_API_KEY"

echo "=== RunPod API Access Test ==="
echo ""

# Step 1: List existing pods
echo "1. Listing existing pods..."
PODS=$(curl -s -H "$AUTH_HEADER" "$API_BASE/pods")
echo "$PODS" | jq '.'
echo ""

# Step 2: Check user info (verify API key works)
echo "2. Verifying API access..."
if [ "$PODS" = "[]" ]; then
    echo "   API access verified - no pods exist (expected for new account)"
elif echo "$PODS" | jq -e '.id' > /dev/null 2>&1 || echo "$PODS" | jq -e '.[0].id' > /dev/null 2>&1; then
    echo "   API access verified - pods listed successfully"
else
    echo "   Warning: Unexpected response format"
fi
echo ""

# Step 3: Display available options
echo "3. Available CPU flavors for CPU-only pods:"
echo "   - cpu3c, cpu3g, cpu3m (3 vCPU variants)"
echo "   - cpu5c, cpu5g, cpu5m (5 vCPU variants)"
echo ""

echo "4. Available data centers:"
echo "   EU: EU-RO-1, EU-SE-1, EU-CZ-1, EU-NL-1, EU-FR-1, EUR-IS-1, EUR-IS-2, EUR-IS-3, EUR-NO-1"
echo "   US: US-IL-1, US-TX-1, US-TX-3, US-TX-4, US-KS-2, US-KS-3, US-GA-1, US-GA-2, US-WA-1, US-CA-2, US-NC-1, US-DE-1"
echo "   CA: CA-MTL-1, CA-MTL-2, CA-MTL-3"
echo "   OC: OC-AU-1"
echo "   AP: AP-JP-1"
echo ""

echo "5. GPU types available (for reference):"
echo "   Consumer: RTX 3070, RTX 3080, RTX 3080 Ti, RTX 3090, RTX 3090 Ti, RTX 4070 Ti, RTX 4080, RTX 4080 SUPER, RTX 4090, RTX 5080, RTX 5090"
echo "   Pro: RTX A2000, RTX A4000, RTX A4500, RTX A5000, RTX A6000, RTX 2000 Ada, RTX 4000 Ada, RTX 5000 Ada, RTX 6000 Ada"
echo "   Data Center: A30, A40, A100, L4, L40, L40S, H100, H200, B200, MI300X"
echo ""

echo "=== API Access Test Complete ==="
echo ""
echo "To create a CPU pod, use:"
echo '  curl -X POST -H "Authorization: Bearer $RUNPOD_API_KEY" -H "Content-Type: application/json" \'
echo '    "$API_BASE/pods" -d '"'"'{"name": "test-pod", "computeType": "CPU", "cpuFlavorIds": ["cpu3c"], "imageName": "zeroclue/comfyui:slim-torch2.8.0-cu126", "volumeInGb": 20}'"'"''
