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
    dockerfile = "Dockerfile.modern"
    context = "."
    args = {
        PYTHON_VERSION      = PYTHON_VERSION
        TORCH_VERSION       = TORCH_VERSION
        INSTALL_CODE_SERVER = "true"
        INSTALL_DEV_TOOLS   = "true"
        INSTALL_SCIENCE_PACKAGES = "true"
    }
}

target "_cu128" {
    inherits = ["_common"]
    args = {
        BASE_IMAGE         = "nvidia/cuda:12.8.1-devel-ubuntu24.04"
        RUNTIME_BASE_IMAGE = "nvidia/cuda:12.8.0-runtime-ubuntu22.04"
        CUDA_VERSION       = "cu128"
    }
}

target "_cu126" {
    inherits = ["_common"]
    args = {
        BASE_IMAGE         = "nvidia/cuda:12.6.3-devel-ubuntu24.04"
        RUNTIME_BASE_IMAGE = "nvidia/cuda:12.6.3-runtime-ubuntu24.04"
        CUDA_VERSION       = "cu126"
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

target "modern-12-8" {
    inherits = ["_cu128"]
    tags = tag("modern", "cu128")
}

target "modern-12-6" {
    inherits = ["_cu126"]
    tags = tag("modern", "cu126")
}