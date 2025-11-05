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
    dockerfile = "Dockerfile.single-stage"
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
        CUDA_VERSION       = "cu124"
    }
}

target "_cu125" {
    inherits = ["_common"]
    args = {
        CUDA_VERSION       = "cu125"
    }
}

target "_cu126" {
    inherits = ["_common"]
    args = {
        CUDA_VERSION       = "cu126"
    }
}

target "_cu128" {
    inherits = ["_common"]
    args = {
        CUDA_VERSION       = "cu128"
    }
}

target "_cu129" {
    inherits = ["_common"]
    args = {
        CUDA_VERSION       = "cu129"
    }
}

target "_cu130" {
    inherits = ["_common"]
    args = {
        CUDA_VERSION       = "cu130"
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

# Single-stage variants
target "single-stage-12-4" {
    inherits = ["_cu124"]
    tags = tag("single-stage", "cu124")
}

target "single-stage-12-5" {
    inherits = ["_cu125"]
    tags = tag("single-stage", "cu125")
}

target "single-stage-12-6" {
    inherits = ["_cu126"]
    tags = tag("single-stage", "cu126")
}

target "single-stage-12-8" {
    inherits = ["_cu128"]
    tags = tag("single-stage", "cu128")
}

target "single-stage-12-9" {
    inherits = ["_cu129"]
    tags = tag("single-stage", "cu129")
}

target "single-stage-13-0" {
    inherits = ["_cu130"]
    tags = tag("single-stage", "cu130")
}

# Slim single-stage variants (no custom nodes)
target "single-stage-slim-12-4" {
    inherits = ["_cu124", "_no_custom_nodes"]
    tags = tag("single-stage-slim", "cu124")
}

target "single-stage-slim-12-5" {
    inherits = ["_cu125", "_no_custom_nodes"]
    tags = tag("single-stage-slim", "cu125")
}

target "single-stage-slim-12-6" {
    inherits = ["_cu126", "_no_custom_nodes"]
    tags = tag("single-stage-slim", "cu126")
}

target "single-stage-slim-12-8" {
    inherits = ["_cu128", "_no_custom_nodes"]
    tags = tag("single-stage-slim", "cu128")
}

target "single-stage-slim-12-9" {
    inherits = ["_cu129", "_no_custom_nodes"]
    tags = tag("single-stage-slim", "cu129")
}

target "single-stage-slim-13-0" {
    inherits = ["_cu130", "_no_custom_nodes"]
    tags = tag("single-stage-slim", "cu130")
}

# Production single-stage variants
target "single-stage-production-12-6" {
    inherits = ["_cu126", "_no_custom_nodes", "_production_base"]
    tags = tag("single-stage-production", "cu126")
}

target "single-stage-production-12-8" {
    inherits = ["_cu128", "_no_custom_nodes", "_production_base"]
    tags = tag("single-stage-production", "cu128")
}