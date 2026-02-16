variable "DOCKERHUB_REPO_NAME" {
    default = "zeroclue/comfyui"
}

# Python 3.13 for forward-looking builds
variable "PYTHON_VERSION" {
    default = "3.13"
}

# PyTorch 2.8.0+ for latest features
variable "TORCH_VERSION" {
    default = "2.8.0"
}

# CUDA 12.8 is the default (modern, stable, excellent GPU support)
variable "DEFAULT_CUDA" {
    default = "cu128"
}

variable "EXTRA_TAG" {
    default = ""
}

# Primary tag function: latest-py313-cu128
function "tag" {
    params = [tag, cuda]
    result = ["${DOCKERHUB_REPO_NAME}:${tag}-py${PYTHON_VERSION}-${cuda}${EXTRA_TAG}"]
}

# Legacy tag function for backward compatibility: base-torch2.8.0-cu128
function "legacy_tag" {
    params = [tag, cuda]
    result = ["${DOCKERHUB_REPO_NAME}:${tag}-torch${TORCH_VERSION}-${cuda}${EXTRA_TAG}"]
}

target "_common" {
    dockerfile = "Dockerfile"
    context = "."
    args = {
        PYTHON_VERSION      = PYTHON_VERSION
        TORCH_VERSION       = TORCH_VERSION
        INSTALL_CODE_SERVER = "true"
        INSTALL_DEV_TOOLS   = "true"
        INSTALL_SCIENCE_PACKAGES = "true"
    }
}

target "_cu124" {
    inherits = ["_common"]
    args = {
        BASE_IMAGE         = "nvidia/cuda:12.4.1-devel-ubuntu22.04"
        CUDA_VERSION       = "cu124"
    }
}

target "_cu125" {
    inherits = ["_common"]
    args = {
        BASE_IMAGE         = "nvidia/cuda:12.5.1-devel-ubuntu24.04"
        CUDA_VERSION       = "cu125"
    }
}

target "_cu126" {
    inherits = ["_common"]
    args = {
        BASE_IMAGE         = "nvidia/cuda:12.6.3-devel-ubuntu24.04"
        CUDA_VERSION       = "cu126"
    }
}

target "_cu128" {
    inherits = ["_common"]
    args = {
        BASE_IMAGE         = "nvidia/cuda:12.8.1-devel-ubuntu24.04"
        CUDA_VERSION       = "cu128"
    }
}

target "_cu129" {
    inherits = ["_common"]
    args = {
        BASE_IMAGE         = "nvidia/cuda:12.9.1-devel-ubuntu24.04"
        CUDA_VERSION       = "cu129"
    }
}

target "_cu130" {
    inherits = ["_common"]
    args = {
        BASE_IMAGE         = "nvidia/cuda:13.0.0-devel-ubuntu24.04"
        CUDA_VERSION       = "cu130"
    }
}

# Runtime CUDA targets for slim variants
target "_cu124_runtime" {
    inherits = ["_common"]
    args = {
        BASE_IMAGE         = "nvidia/cuda:12.4.1-devel-ubuntu22.04"
        RUNTIME_BASE_IMAGE = "nvidia/cuda:12.4.1-runtime-ubuntu22.04"
        CUDA_VERSION       = "cu124"
    }
}

target "_cu126_runtime" {
    inherits = ["_common"]
    args = {
        BASE_IMAGE         = "nvidia/cuda:12.6.3-devel-ubuntu24.04"
        RUNTIME_BASE_IMAGE = "nvidia/cuda:12.6.3-runtime-ubuntu24.04"
        CUDA_VERSION       = "cu126"
    }
}

target "_cu128_runtime" {
    inherits = ["_common"]
    args = {
        BASE_IMAGE         = "nvidia/cuda:12.8.1-devel-ubuntu24.04"
        RUNTIME_BASE_IMAGE = "nvidia/cuda:12.8.1-runtime-ubuntu24.04"
        CUDA_VERSION       = "cu128"
    }
}

target "_no_custom_nodes" {
    args = {
        SKIP_CUSTOM_NODES = "1"
    }
}

target "_no_code_server" {
    args = {
        INSTALL_CODE_SERVER = "false"
    }
}

target "_no_dev_tools" {
    args = {
        INSTALL_DEV_TOOLS = "false"
    }
}

target "_no_science_packages" {
    args = {
        INSTALL_SCIENCE_PACKAGES = "false"
    }
}

target "_extra_nodes" {
    args = {
        ENABLE_EXTRA_NODES = "true"
    }
}

target "_slim_base" {
    args = {
        INSTALL_DEV_TOOLS = "false"
        INSTALL_SCIENCE_PACKAGES = "false"
        INSTALL_CODE_SERVER = "false"
    }
}

# ============================================================================
# PRIMARY BUILDS (February 2026 - CUDA 12.8 as default)
# Tag format: <variant>-py<python>-<cuda>
# Example: latest-py313-cu128
# ============================================================================

# Latest builds - forward-looking with Python 3.13
target "latest-py313-cu128" {
    inherits = ["_cu128"]
    tags = tag("latest", "cu128")
    description = "★ DEFAULT - Python 3.13, CUDA 12.8, SageAttention included"
}

target "latest-py313-cu129" {
    inherits = ["_cu129"]
    tags = tag("latest", "cu129")
    description = "Future-proof - Python 3.13, CUDA 12.9, SageAttention included"
}

target "latest-py313-cu130" {
    inherits = ["_cu130"]
    tags = tag("latest", "cu130")
    description = "Future-proof - Python 3.13, CUDA 13.0, ComfyUI-Attention-Optimizer"
}

# Standard builds - full feature set
target "standard-py313-cu128" {
    inherits = ["_cu128"]
    tags = tag("standard", "cu128")
    description = "Full features - Python 3.13, CUDA 12.8, SageAttention included"
}

target "standard-py313-cu129" {
    inherits = ["_cu129"]
    tags = tag("standard", "cu129")
    description = "Full features - Python 3.13, CUDA 12.9, SageAttention included"
}

target "standard-py313-cu130" {
    inherits = ["_cu130"]
    tags = tag("standard", "cu130")
    description = "Full features - Python 3.13, CUDA 13.0, ComfyUI-Attention-Optimizer"
}

# Development builds
target "dev-py313-cu128" {
    inherits = ["_cu128"]
    tags = tag("dev", "cu128")
    description = "Development tools - Python 3.13, CUDA 12.8"
}

# ============================================================================
# LEGACY BUILDS (for backward compatibility)
# ============================================================================

# Legacy Python 3.13 + CUDA 12.6 (Sage Attention compatibility)
target "stable-py313-cu126" {
    inherits = ["_cu126"]
    tags = tag("stable", "cu126")
    description = "Legacy - Python 3.13, CUDA 12.6 for SageAttention compatibility"
}

# Legacy Python 3.11 + CUDA 12.6 (maximum custom node compatibility)
target "stable-py311-cu126" {
    inherits = ["_cu126"]
    args = {
        PYTHON_VERSION = "3.11"
    }
    tags = tag("stable", "cu126")
    description = "Legacy - Python 3.11, CUDA 12.6 for max custom node compatibility"
}

# ============================================================================
# LEGACY TAG FORMATS (backward compatible with existing tags)
# Tag format: <variant>-torch<torch>-<cuda>
# ============================================================================
# Optimized for RunPod with custom nodes but without dev tools
target "_minimal_base" {
    args = {
        INSTALL_DEV_TOOLS = "false"
        INSTALL_SCIENCE_PACKAGES = "true"
        INSTALL_CODE_SERVER = "false"
    }
}

target "base-12-4" {
    inherits = ["_cu124"]
    tags = tag("base", "cu124")
}

target "base-12-5" {
    inherits = ["_cu125"]
    tags = tag("base", "cu125")
}

target "base-12-6" {
    inherits = ["_cu126"]
    tags = tag("base", "cu126")
}

target "base-12-8" {
    inherits = ["_cu128"]
    tags = tag("base", "cu128")
}

target "base-12-9" {
    inherits = ["_cu129"]
    tags = tag("base", "cu129")
}

target "base-13-0" {
    inherits = ["_cu130"]
    tags = tag("base", "cu130")
}

# Extended variants with extra nodes pre-installed
# Build manually: docker buildx bake base-extra-12-6
target "base-extra-12-6" {
    inherits = ["_cu126", "_extra_nodes"]
    tags = tag("base-extra", "cu126")
}

target "base-extra-12-8" {
    inherits = ["_cu128", "_extra_nodes"]
    tags = tag("base-extra", "cu128")
}



# Slim variants - optimized for serving, runtime CUDA images
target "slim-12-6" {
    inherits = ["_cu126_runtime", "_no_custom_nodes", "_slim_base"]
    tags = tag("slim", "cu126")
}

target "slim-12-8" {
    inherits = ["_cu128_runtime", "_no_custom_nodes", "_slim_base"]
    tags = tag("slim", "cu128")
}

# Minimal variants - ComfyUI + Manager without dev tools
# Includes custom nodes but optimized for smaller image size (~6-7GB)
target "minimal-12-6" {
    inherits = ["_cu126", "_minimal_base"]
    tags = tag("minimal", "cu126")
}

target "minimal-12-8" {
    inherits = ["_cu128", "_minimal_base"]
    tags = tag("minimal", "cu128")
}

# Debug variant - for troubleshooting issues
# Build manually: docker buildx bake debug-12-6 --push
target "debug-12-6" {
    inherits = ["_cu126"]
    tags = tag("debug", "cu126")
}
