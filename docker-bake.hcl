variable "DOCKERHUB_REPO_NAME" {
    default = "zeroclue/comfyui"
}

variable "PYTHON_VERSION" {
    default = "3.13"
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

# Runtime CUDA targets for production variants
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

target "_production_base" {
    args = {
        INSTALL_DEV_TOOLS = "false"
        INSTALL_SCIENCE_PACKAGES = "false"
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



# Production variants - optimized for serving, runtime CUDA images
target "production-12-6" {
    inherits = ["_cu126_runtime", "_no_custom_nodes", "_production_base"]
    tags = tag("production", "cu126")
}

target "production-12-8" {
    inherits = ["_cu128_runtime", "_no_custom_nodes", "_production_base"]
    tags = tag("production", "cu128")
}

