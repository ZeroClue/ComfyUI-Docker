// Revolutionary Docker Bake Configuration for ComfyUI-Docker
// Supports multiple CUDA versions and build variants with instant startup

variable "DOCKERHUB_REPO_NAME" {
  default = "zeroclue/comfyui"
}

variable "PYTHON_VERSION" {
  default = "3.13"
}

variable "TORCH_VERSION" {
  default = "2.8.0"
}

variable "REVOLUTIONARY_TAG" {
  default = "rev"
}

// ============================================================================
// Common Configuration
// ============================================================================
target "_common" {
  dockerfile = "Dockerfile.revolutionary"
  context = "."
  args = {
    PYTHON_VERSION = PYTHON_VERSION
    TORCH_VERSION  = TORCH_VERSION
  }
  tags = ["${DOCKERHUB_REPO_NAME}:latest-${REVOLUTIONARY_TAG}"]
}

// ============================================================================
// CUDA Base Images
// ============================================================================
target "_cu124" {
  inherits = ["_common"]
  args = {
    BASE_IMAGE         = "nvidia/cuda:12.4.1-devel-ubuntu22.04"
    RUNTIME_BASE_IMAGE = "nvidia/cuda:12.4.1-runtime-ubuntu22.04"
    CUDA_VERSION       = "cu124"
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

target "_cu128" {
  inherits = ["_common"]
  args = {
    BASE_IMAGE         = "nvidia/cuda:12.8.1-devel-ubuntu24.04"
    RUNTIME_BASE_IMAGE = "nvidia/cuda:12.8.1-runtime-ubuntu24.04"
    CUDA_VERSION       = "cu128"
  }
}

target "_cu130" {
  inherits = ["_common"]
  args = {
    BASE_IMAGE         = "nvidia/cuda:13.0.0-devel-ubuntu24.04"
    RUNTIME_BASE_IMAGE = "nvidia/cuda:13.0.0-runtime-ubuntu24.04"
    CUDA_VERSION       = "cu130"
  }
}

// ============================================================================
// Build Variants
// ============================================================================
target "_minimal" {
  args = {
    VARIANT = "minimal"
  }
}

target "_standard" {
  args = {
    VARIANT = "standard"
  }
}

target "_full" {
  args = {
    VARIANT = "full"
  }
}

target "_dev" {
  args = {
    VARIANT = "dev"
  }
}

// ============================================================================
// Minimal Variant Targets (ComfyUI + Manager + Dashboard)
// ============================================================================
target "minimal-12-4" {
  inherits = ["_cu124", "_minimal"]
  tags = [
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-minimal-cu124",
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-minimal-12-4",
  ]
}

target "minimal-12-6" {
  inherits = ["_cu126", "_minimal"]
  tags = [
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-minimal-cu126",
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-minimal-12-6",
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-minimal",  # Alias for latest CUDA
  ]
}

target "minimal-12-8" {
  inherits = ["_cu128", "_minimal"]
  tags = [
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-minimal-cu128",
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-minimal-12-8",
  ]
}

target "minimal-13-0" {
  inherits = ["_cu130", "_minimal"]
  tags = [
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-minimal-cu130",
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-minimal-13-0",
  ]
}

// ============================================================================
// Standard Variant Targets (Minimal + Popular Custom Nodes)
// ============================================================================
target "standard-12-4" {
  inherits = ["_cu124", "_standard"]
  tags = [
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-standard-cu124",
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-standard-12-4",
  ]
}

target "standard-12-6" {
  inherits = ["_cu126", "_standard"]
  tags = [
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-standard-cu126",
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-standard-12-6",
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-standard",  # Alias for latest CUDA
  ]
}

target "standard-12-8" {
  inherits = ["_cu128", "_standard"]
  tags = [
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-standard-cu128",
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-standard-12-8",
  ]
}

target "standard-13-0" {
  inherits = ["_cu130", "_standard"]
  tags = [
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-standard-cu130",
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-standard-13-0",
  ]
}

// ============================================================================
// Full Variant Targets (Standard + All Custom Nodes + Dev Tools)
// ============================================================================
target "full-12-4" {
  inherits = ["_cu124", "_full"]
  tags = [
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-full-cu124",
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-full-12-4",
  ]
}

target "full-12-6" {
  inherits = ["_cu126", "_full"]
  tags = [
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-full-cu126",
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-full-12-6",
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-full",  # Alias for latest CUDA
  ]
}

target "full-12-8" {
  inherits = ["_cu128", "_full"]
  tags = [
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-full-cu128",
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-full-12-8",
  ]
}

target "full-13-0" {
  inherits = ["_cu130", "_full"]
  tags = [
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-full-cu130",
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-full-13-0",
  ]
}

// ============================================================================
// Dev Variant Targets (Full + Code Server + Jupyter)
// ============================================================================
target "dev-12-4" {
  inherits = ["_cu124", "_dev"]
  tags = [
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-dev-cu124",
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-dev-12-4",
  ]
}

target "dev-12-6" {
  inherits = ["_cu126", "_dev"]
  tags = [
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-dev-cu126",
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-dev-12-6",
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-dev",  // Alias for latest CUDA
  ]
}

target "dev-12-8" {
  inherits = ["_cu128", "_dev"]
  tags = [
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-dev-cu128",
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-dev-12-8",
  ]
}

target "dev-13-0" {
  inherits = ["_cu130", "_dev"]
  tags = [
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONARY_TAG}-dev-cu130",
    "${DOCKERHUB_REPO_NAME}:${REVOLUTIONABLE_TAG}-dev-13-0",
  ]
}

// ============================================================================
// Build Groups
// ============================================================================
group "default" {
  targets = [
    "minimal-12-6",
    "standard-12-6",
    "full-12-6",
  ]
}

group "minimal" {
  targets = [
    "minimal-12-4",
    "minimal-12-6",
    "minimal-12-8",
    "minimal-13-0",
  ]
}

group "standard" {
  targets = [
    "standard-12-4",
    "standard-12-6",
    "standard-12-8",
    "standard-13-0",
  ]
}

group "full" {
  targets = [
    "full-12-4",
    "full-12-6",
    "full-12-8",
    "full-13-0",
  ]
}

group "dev" {
  targets = [
    "dev-12-4",
    "dev-12-6",
    "dev-12-8",
    "dev-13-0",
  ]
}

group "cu126" {
  targets = [
    "minimal-12-6",
    "standard-12-6",
    "full-12-6",
    "dev-12-6",
  ]
}

group "cu128" {
  targets = [
    "minimal-12-8",
    "standard-12-8",
    "full-12-8",
    "dev-12-8",
  ]
}

group "all" {
  targets = [
    "minimal-12-4",
    "minimal-12-6",
    "minimal-12-8",
    "minimal-13-0",
    "standard-12-4",
    "standard-12-6",
    "standard-12-8",
    "standard-13-0",
    "full-12-4",
    "full-12-6",
    "full-12-8",
    "full-13-0",
    "dev-12-4",
    "dev-12-6",
    "dev-12-8",
    "dev-13-0",
  ]
}
