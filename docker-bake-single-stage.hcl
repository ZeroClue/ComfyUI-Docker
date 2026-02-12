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

target "_minimal_base" {
    args = {
        INSTALL_DEV_TOOLS = "false"
        INSTALL_SCIENCE_PACKAGES = "false"
        INSTALL_CODE_SERVER = "false"
    }
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
