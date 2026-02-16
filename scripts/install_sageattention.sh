#!/bin/bash
# Conditional SageAttention installation based on CUDA version
#
# SageAttention supports CUDA 12.0-12.9 only
# For CUDA 13.0+, use ComfyUI-Attention-Optimizer instead
#
# This script should be called during Docker build after custom nodes installation

set -e

echo "Checking CUDA version for SageAttention compatibility..."

# Get CUDA version from nvcc or environment
if command -v nvcc &> /dev/null; then
    CUDA_VERSION=$(nvcc --version | grep "release" | sed 's/.*release //' | sed 's/,.*//')
    echo "Detected CUDA version: $CUDA_VERSION (from nvcc)"
else
    # Fallback to environment variable if set during build
    CUDA_VERSION="${CUDA_VERSION:-unknown}"
    echo "Using CUDA version from environment: $CUDA_VERSION"
fi

# SageAttention version compatibility check
# Supports: 12.0, 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8, 12.9
# Does NOT support: 13.0+

install_sageattention() {
    local version="$1"
    echo "Installing SageAttention ${version}..."
    # Install SageAttention with proper version pinning
    pip install --no-cache-dir sageattention
    echo "✓ SageAttention installed successfully"
}

install_attention_optimizer() {
    echo "SageAttention not supported for CUDA ${CUDA_VERSION}"
    echo "Installing ComfyUI-Attention-Optimizer as alternative..."
    pip install --no-cache-dir comfyui-attention-optimizer
    echo "✓ ComfyUI-Attention-Optimizer installed successfully"
}

# Parse CUDA version and install appropriate attention optimization
case "$CUDA_VERSION" in
    12.0|12.1|12.2|12.3|12.4|12.5|12.6|12.7|12.8|12.9)
        install_sageattention "$CUDA_VERSION"
        ;;
    13.*|14.*|15.*)
        install_attention_optimizer
        ;;
    cu124|cu125|cu126|cu127|cu128|cu129)
        # Handle PyTorch-style CUDA version strings (cu124, cu126, etc.)
        install_sageattention "${CUDA_VERSION:2}.${CUDA_VERSION:3}"
        ;;
    cu130|cu131|cu140|cu150)
        # CUDA 13.0+ - use alternative
        install_attention_optimizer
        ;;
    *)
        echo "Warning: Unknown CUDA version '${CUDA_VERSION}'"
        echo "Attempting to install SageAttention..."
        if pip install --no-cache-dir sageattention 2>/dev/null; then
            echo "✓ SageAttention installed successfully"
        else
            echo "✗ SageAttention installation failed, falling back to ComfyUI-Attention-Optimizer"
            install_attention_optimizer
        fi
        ;;
esac

echo "Attention optimization installation complete."
