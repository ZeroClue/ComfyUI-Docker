#!/bin/bash
# SageAttention 2.2.0 installation with source compilation
#
# SageAttention2++ provides significant speedup for diffusion and video models:
# - 2x faster than FlashAttention2 on RTX 4090
# - 2.7x faster on RTX 5090
# - Lossless accuracy for image/video generation
#
# GPU Support: Ampere (RTX 30xx), Ada (RTX 40xx/2000 Ada), Hopper (H100/H800)
# CUDA Requirements: >= 12.0 (12.4+ for FP8 on Ada, 12.8+ for Blackwell/v2++)
#
# For CUDA 13.0+, falls back to ComfyUI-Attention-Optimizer

set -e

echo "=============================================="
echo "SageAttention 2.2.0 Installation"
echo "=============================================="

# Get CUDA version from nvcc or environment
if command -v nvcc &> /dev/null; then
    CUDA_VERSION=$(nvcc --version | grep "release" | sed 's/.*release //' | sed 's/,.*//')
    echo "Detected CUDA version: $CUDA_VERSION (from nvcc)"
else
    # Fallback to environment variable if set during build
    CUDA_VERSION="${CUDA_VERSION:-unknown}"
    echo "Using CUDA version from environment: $CUDA_VERSION"
fi

# Parse CUDA version to numeric for comparison
parse_cuda_version() {
    local version="$1"
    # Handle cuXXX format (e.g., cu128 -> 12.8)
    if [[ "$version" == cu* ]]; then
        version="${version:2:2}.${version:4:1}"
    fi
    echo "$version"
}

CUDA_VER_NUMERIC=$(parse_cuda_version "$CUDA_VERSION")
echo "Parsed CUDA version: $CUDA_VER_NUMERIC"

# Install build dependencies
install_build_deps() {
    echo "Installing build dependencies..."
    pip install --no-cache-dir packaging psutil ninja
}

# Install SageAttention 2.2.0 from source (with compilation)
install_sageattention_from_source() {
    echo ""
    echo "Installing SageAttention 2.2.0 from source (compiling CUDA kernels)..."
    echo "This may take 3-5 minutes..."

    install_build_deps

    # Clone and compile
    cd /tmp
    git clone https://github.com/thu-ml/SageAttention.git
    cd SageAttention

    # Set parallel compilation options for faster build
    export EXT_PARALLEL=4
    export NVCC_APPEND_FLAGS="--threads 8"
    export MAX_JOBS=32

    # Set target GPU architectures (required for builds without GPU)
    # SM 80: A100, SM 86: RTX 3090/A6000, SM 89: RTX 4090/L40/Ada, SM 90: H100
    export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"

    # Compile and install (use --no-build-isolation to access already-installed torch)
    pip install --no-cache-dir --no-build-isolation -e .

    # Cleanup
    cd /
    rm -rf /tmp/SageAttention

    echo "✓ SageAttention 2.2.0 compiled and installed successfully"
}

# Install fallback for CUDA 13.0+
install_attention_optimizer() {
    echo ""
    echo "CUDA ${CUDA_VERSION} detected - SageAttention not yet optimized for CUDA 13+"
    echo "Installing ComfyUI-Attention-Optimizer as alternative..."
    pip install --no-cache-dir comfyui-attention-optimizer
    echo "✓ ComfyUI-Attention-Optimizer installed successfully"
}

# Install legacy pip version (slower Triton backend, no compilation)
install_sageattention_pip() {
    echo ""
    echo "Installing SageAttention from PyPI (Triton backend, slower)..."
    pip install --no-cache-dir sageattention==1.0.6
    echo "✓ SageAttention 1.0.6 installed (Triton backend)"
}

# Determine installation method based on CUDA version
# CUDA 12.0-12.9: Full source compilation (best performance)
# CUDA 13.0+: ComfyUI-Attention-Optimizer
# Unknown: Try pip fallback

case "$CUDA_VERSION" in
    # CUDA 12.x - compile from source for best performance
    12.0|12.1|12.2|12.3|12.4|12.5|12.6|12.7|12.8|12.9)
        install_sageattention_from_source
        ;;
    cu124|cu125|cu126|cu127|cu128|cu129)
        install_sageattention_from_source
        ;;
    # CUDA 13.0+ - use alternative
    13.*|14.*|15.*)
        install_attention_optimizer
        ;;
    cu130|cu131|cu140|cu150)
        install_attention_optimizer
        ;;
    *)
        echo ""
        echo "Warning: Unknown CUDA version '${CUDA_VERSION}'"
        echo "Attempting source compilation..."
        if install_sageattention_from_source 2>/dev/null; then
            echo "✓ SageAttention installed successfully"
        else
            echo "✗ Source compilation failed, falling back to PyPI version"
            install_sageattention_pip
        fi
        ;;
esac

echo ""
echo "=============================================="
echo "Attention optimization installation complete"
echo "=============================================="
