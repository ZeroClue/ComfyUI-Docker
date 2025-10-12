# ==========================================
# Optimized Docker Bake Configuration with Dependency Conflict Resolution
# ==========================================

variable "DOCKERHUB_REPO_NAME" {
    default = "zeroclue/comfyui"
}

variable "PYTHON_VERSION" {
    default = "3.11"  # Downgraded for better compatibility
}

variable "TORCH_VERSION" {
    default = "2.8.0"
}

variable "EXTRA_TAG" {
    default = ""
}

function "tag" {
    params = [tag, cuda]
    result = ["${DOCKERHUB_REPO_NAME}:${tag}-torch${TORCH_VERSION}-${cuda}${EXTRA_TAG}"]
}

# Common optimized base configuration with caching optimization
target "_common_optimized" {
    dockerfile = "Dockerfile.optimized"
    context = "."
    args = {
        PYTHON_VERSION           = PYTHON_VERSION
        TORCH_VERSION            = TORCH_VERSION
        BUILD_MODE               = "optimized"
        INSTALL_CODE_SERVER      = "true"
        INSTALL_DEV_TOOLS        = "true"
        INSTALL_SCIENCE_PACKAGES = "true"
    }
    # Enhanced cache management for better layer reuse
    cache-from = [
        "type=gha,mode=max"
    ]
    cache-to = [
        "type=gha,mode=max,scope=optimized"
    ]
    # Reduce parallelism for space-constrained environments
    platforms = ["linux/amd64"]
}

# Runtime CUDA targets for optimized variants
target "_cu124_optimized" {
    inherits = ["_common_optimized"]
    args = {
        BASE_IMAGE         = "nvidia/cuda:12.4.1-devel-ubuntu22.04"
        RUNTIME_BASE_IMAGE = "nvidia/cuda:12.4.1-runtime-ubuntu22.04"
        CUDA_VERSION       = "cu124"
    }
}

target "_cu126_optimized" {
    inherits = ["_common_optimized"]
    args = {
        BASE_IMAGE         = "nvidia/cuda:12.6.3-devel-ubuntu24.04"
        RUNTIME_BASE_IMAGE = "nvidia/cuda:12.6.3-runtime-ubuntu24.04"
        CUDA_VERSION       = "cu126"
    }
}

target "_cu128_optimized" {
    inherits = ["_common_optimized"]
    args = {
        BASE_IMAGE         = "nvidia/cuda:12.8.1-devel-ubuntu24.04"
        RUNTIME_BASE_IMAGE = "nvidia/cuda:12.8.1-runtime-ubuntu24.04"
        CUDA_VERSION       = "cu128"
    }
    # Override cache scope for CUDA 12.8 to use more aggressive caching
    cache-to = [
        "type=gha,mode=max,scope=cu128-optimized"
    ]
    # Add build labels for monitoring
    labels = {
        "com.zeroclue.build.cuda" = "12.8"
        "com.zeroclue.build.optimized" = "true"
        "com.zeroclue.build.space-aware" = "true"
    }
}

target "_cu129_optimized" {
    inherits = ["_common_optimized"]
    args = {
        BASE_IMAGE         = "nvidia/cuda:12.9.1-devel-ubuntu24.04"
        RUNTIME_BASE_IMAGE = "nvidia/cuda:12.9.1-runtime-ubuntu24.04"
        CUDA_VERSION       = "cu129"
    }
}

target "_cu130_optimized" {
    inherits = ["_common_optimized"]
    args = {
        BASE_IMAGE         = "nvidia/cuda:13.0.0-devel-ubuntu24.04"
        RUNTIME_BASE_IMAGE = "nvidia/cuda:13.0.0-runtime-ubuntu24.04"
        CUDA_VERSION       = "cu130"
    }
}

# Optimized variant configurations
target "_no_custom_nodes_optimized" {
    args = {
        SKIP_CUSTOM_NODES = "true"
    }
}

target "_no_code_server_optimized" {
    args = {
        INSTALL_CODE_SERVER = "false"
    }
}

target "_no_dev_tools_optimized" {
    args = {
        INSTALL_DEV_TOOLS = "false"
    }
}

target "_no_science_packages_optimized" {
    args = {
        INSTALL_SCIENCE_PACKAGES = "false"
    }
}

target "_production_optimized" {
    args = {
        INSTALL_DEV_TOOLS        = "false"
        INSTALL_SCIENCE_PACKAGES = "false"
        INSTALL_CODE_SERVER      = "false"
        BUILD_MODE               = "optimized"
    }
}

target "_validation_mode" {
    args = {
        BUILD_MODE = "validation"
    }
}

# ==========================================
# Optimized Base Variants (with conflict resolution)
# ==========================================

target "base-optimized-12-6" {
    inherits = ["_cu126_optimized"]
    tags = tag("base-optimized", "cu126")
}

target "base-optimized-12-8" {
    inherits = ["_cu128_optimized"]
    tags = tag("base-optimized", "cu128")
    # Additional space optimization for problematic CUDA 12.8 builds
    target = "runtime"
    # Use build-arg to signal space-aware build
    args = {
        BUILD_SPACE_AWARE = "true"
    }
}

target "base-optimized-12-9" {
    inherits = ["_cu129_optimized"]
    tags = tag("base-optimized", "cu129")
}

target "base-optimized-13-0" {
    inherits = ["_cu130_optimized"]
    tags = tag("base-optimized", "cu130")
}

# ==========================================
# Optimized Slim Variants (without custom nodes)
# ==========================================

target "slim-optimized-12-6" {
    inherits = ["_cu126_optimized", "_no_custom_nodes_optimized"]
    tags = tag("slim-optimized", "cu126")
}

target "slim-optimized-12-8" {
    inherits = ["_cu128_optimized", "_no_custom_nodes_optimized"]
    tags = tag("slim-optimized", "cu128")
    # Additional space optimization for problematic CUDA 12.8 builds
    target = "runtime"
    args = {
        BUILD_SPACE_AWARE = "true"
    }
}

target "slim-optimized-12-9" {
    inherits = ["_cu129_optimized", "_no_custom_nodes_optimized"]
    tags = tag("slim-optimized", "cu129")
}

target "slim-optimized-13-0" {
    inherits = ["_cu130_optimized", "_no_custom_nodes_optimized"]
    tags = tag("slim-optimized", "cu130")
}

# ==========================================
# Optimized Production Variants (runtime images)
# ==========================================

target "production-optimized-12-6" {
    inherits = ["_cu126_optimized", "_production_optimized"]
    tags = tag("production-optimized", "cu126")
}

target "production-optimized-12-8" {
    inherits = ["_cu128_optimized", "_production_optimized"]
    tags = tag("production-optimized", "cu128")
    # Additional space optimization for problematic CUDA 12.8 builds
    target = "runtime"
    args = {
        BUILD_SPACE_AWARE = "true"
    }
}

target "production-optimized-12-9" {
    inherits = ["_cu129_optimized", "_production_optimized"]
    tags = tag("production-optimized", "cu129")
}

target "production-optimized-13-0" {
    inherits = ["_cu130_optimized", "_production_optimized"]
    tags = tag("production-optimized", "cu130")
}

# ==========================================
# Validation Variants (with dependency validation)
# ==========================================

target "base-validation-12-6" {
    inherits = ["_cu126_optimized", "_validation_mode"]
    tags = tag("base-validation", "cu126")
}

target "base-validation-12-8" {
    inherits = ["_cu128_optimized", "_validation_mode"]
    tags = tag("base-validation", "cu128")
}

# ==========================================
# Ultra-Optimized Variants (minimal size)
# ==========================================

target "ultra-optimized-12-6" {
    inherits = ["_cu126_optimized", "_no_custom_nodes_optimized", "_no_code_server_optimized", "_no_dev_tools_optimized", "_no_science_packages_optimized"]
    tags = tag("ultra-optimized", "cu126")
}

target "ultra-optimized-12-8" {
    inherits = ["_cu128_optimized", "_no_custom_nodes_optimized", "_no_code_server_optimized", "_no_dev_tools_optimized", "_no_science_packages_optimized"]
    tags = tag("ultra-optimized", "cu128")
}

# ==========================================
# Legacy Compatibility Targets (use original Dockerfile)
# ==========================================

target "_common_legacy" {
    dockerfile = "Dockerfile"
    context = "."
    args = {
        PYTHON_VERSION           = PYTHON_VERSION
        TORCH_VERSION            = TORCH_VERSION
        INSTALL_CODE_SERVER      = "true"
        INSTALL_DEV_TOOLS        = "true"
        INSTALL_SCIENCE_PACKAGES = "true"
    }
}

target "_cu126_legacy" {
    inherits = ["_common_legacy"]
    args = {
        BASE_IMAGE         = "nvidia/cuda:12.6.3-devel-ubuntu24.04"
        RUNTIME_BASE_IMAGE = "nvidia/cuda:12.6.3-runtime-ubuntu24.04"
        CUDA_VERSION       = "cu126"
    }
}

target "_cu128_legacy" {
    inherits = ["_common_legacy"]
    args = {
        BASE_IMAGE         = "nvidia/cuda:12.8.1-devel-ubuntu24.04"
        RUNTIME_BASE_IMAGE = "nvidia/cuda:12.8.1-runtime-ubuntu24.04"
        CUDA_VERSION       = "cu128"
    }
}

# Legacy variants for fallback
target "base-legacy-12-6" {
    inherits = ["_cu126_legacy"]
    tags = tag("base", "cu126")
}

target "base-legacy-12-8" {
    inherits = ["_cu128_legacy"]
    tags = tag("base", "cu128")
}

target "slim-legacy-12-6" {
    inherits = ["_cu126_legacy", "_no_custom_nodes_optimized"]
    tags = tag("slim", "cu126")
}

target "slim-legacy-12-8" {
    inherits = ["_cu128_legacy", "_no_custom_nodes_optimized"]
    tags = tag("slim", "cu128")
}

# ==========================================
# Build Groups for Different Use Cases
# ==========================================

group "optimized-all" {
    targets = [
        "base-optimized-12-6",
        "base-optimized-12-8",
        "slim-optimized-12-6",
        "slim-optimized-12-8",
        "production-optimized-12-6",
        "production-optimized-12-8"
    ]
}

group "production-optimized" {
    targets = [
        "production-optimized-12-6",
        "production-optimized-12-8",
        "production-optimized-12-9",
        "production-optimized-13-0"
    ]
}

group "validation-all" {
    targets = [
        "base-validation-12-6",
        "base-validation-12-8"
    ]
}

group "ultra-optimized" {
    targets = [
        "ultra-optimized-12-6",
        "ultra-optimized-12-8"
    ]
}

group "legacy-fallback" {
    targets = [
        "base-legacy-12-6",
        "base-legacy-12-8",
        "slim-legacy-12-6",
        "slim-legacy-12-8"
    ]
}