#!/bin/bash
#
# Revolutionary Architecture Pre-Start Script
#
# This script performs minimal initialization before starting services.
# Key changes from legacy architecture:
# - NO rsync operations (apps in container, models on network volume)
# - Fast startup (seconds vs minutes)
# - Clean separation of app code vs user data
#

set -e

export PYTHONUNBUFFERED=1

echo "**** Revolutionary Architecture Startup ****"
echo "**** Apps in container, models on network volume ****"

# Set timezone based on TIME_ZONE environment variable
echo "**** Setting timezone... ****"
export TZ=${TIME_ZONE:-"Etc/UTC"}
echo "**** Timezone set to $TZ ****"
echo "$TZ" | sudo tee /etc/timezone > /dev/null
sudo ln -sf "/usr/share/zoneinfo/$TZ" /etc/localtime
sudo dpkg-reconfigure -f noninteractive tzdata

# Generate extra_model_paths.yaml for ComfyUI
# This tells ComfyUI to find models on /workspace (network volume)
echo "**** Generating ComfyUI model path configuration... ****"
if [ -f "/generate_extra_paths.py" ]; then
    python3 /generate_extra_paths.py --create-dirs
    echo "✓ Model paths configured"
else
    echo "⚠ generate_extra_paths.py not found, using default paths"
fi

# Create workspace directories
echo "**** Creating workspace directories... ****"
mkdir -p /workspace/output
mkdir -p /workspace/input
mkdir -p /workspace/user
mkdir -p /workspace/temp
mkdir -p /workspace/logs
mkdir -p /workspace/config/workflows
echo "✓ Workspace directories created"

# Verify ComfyUI installation
echo "**** Verifying ComfyUI installation... ****"
COMFYUI_PATH="${COMFYUI_PATH:-/ComfyUI}"
if [ -d "$COMFYUI_PATH" ]; then
    echo "✓ ComfyUI found at $COMFYUI_PATH"
else
    echo "⚠ ComfyUI not found at $COMFYUI_PATH"
fi

# Verify venv in container (not on workspace)
echo "**** Verifying Python venv... ****"
VENV_PATH="${VENV_PATH:-/venv}"
if [ -d "$VENV_PATH" ] && [ -f "$VENV_PATH/bin/python" ]; then
    echo "✓ Python venv found at $VENV_PATH"
    PYTHON_VERSION=$("$VENV_PATH/bin/python" --version 2>&1)
    echo "  Python version: $PYTHON_VERSION"
else
    echo "⚠ Python venv not found at $VENV_PATH"
fi

echo "**** Pre-start initialization complete ****"
echo "**** Ready for service startup ****"
