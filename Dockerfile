# =============================================================================
# Revolutionary Multi-Stage Dockerfile for ComfyUI-Docker
# =============================================================================
# Architecture Overview:
# ---------------------
# This Dockerfile implements a 5-stage multi-stage build for maximum efficiency:
#
# Stage 1: builder-base
#   - Ubuntu 24.04 + CUDA 12.6 + UV package manager
#   - Foundation for all builds
#
# Stage 2: python-deps
#   - Python 3.13 virtual environment at /app/venv
#   - PyTorch with CUDA support and all Python dependencies
#   - Cached and reused across builds
#
# Stage 3: comfyui-core
#   - ComfyUI from GitHub
#   - ComfyUI Manager integrated
#   - Custom nodes (conditional via SKIP_CUSTOM_NODES)
#   - Installed at /app/comfyui
#
# Stage 4: dashboard-builder (conditional via BUILD_DASHBOARD)
#   - Builds static dashboard assets
#   - Only runs for non-minimal variants
#
# Stage 5: runtime
#   - Minimal runtime image
#   - Copies artifacts from previous stages
#   - Immutable app code at /app/
#   - Network volume at /workspace/
#
# Build Variants:
# --------------
# - base: Full installation with custom nodes (~8-12GB)
# - slim: Production optimized, no custom nodes (~4-5GB)
# - minimal: Development optimized (~6-7GB)
# - dev: Includes code-server and dev tools
#
# Usage:
# ------
# docker buildx bake base-12-6  # Build base variant with CUDA 12.6
# docker buildx bake slim-12-6  # Build slim variant with CUDA 12.6
# =============================================================================

# =============================================================================
# Stage 1: builder-base
# =============================================================================
# Purpose: Create base builder image with CUDA and UV
# This stage is only rebuilt when CUDA version changes
# =============================================================================
FROM nvidia/cuda:12.6.3-devel-ubuntu24.04 AS builder-base

# Build arguments
ARG PYTHON_VERSION=3.13
ARG CUDA_VERSION=cu126

# Set the shell for better error handling
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install essential system packages
RUN apt-get update --yes && \
    apt-get install --yes --no-install-recommends \
        git wget curl build-essential cmake ninja-build \
        pkg-config libgl1 libglib2.0-0 \
        libgomp1 libomp-dev clang && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Install UV package manager for fast Python operations
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && \
    rm /uv-installer.sh && \
    chmod +x /root/.local/bin/uv && \
    /root/.local/bin/uv --version

ENV PATH="/root/.local/bin:$PATH"

# Install Python 3.13 using UV
RUN uv python install ${PYTHON_VERSION} && \
    python3.13 --version

# =============================================================================
# Stage 2: python-deps
# =============================================================================
# Purpose: Build Python virtual environment with all dependencies
# This stage is cached and reused unless requirements change
# =============================================================================
FROM builder-base AS python-deps

# Build arguments
ARG PYTHON_VERSION=3.13
ARG TORCH_VERSION=2.8.0
ARG CUDA_VERSION=cu126
ARG INSTALL_DEV_TOOLS=true
ARG INSTALL_SCIENCE_PACKAGES=true

# Create virtual environment at /app/venv
RUN uv venv --seed /app/venv
ENV PATH="/app/venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/venv"

# Upgrade pip and install essential packages
RUN pip install --no-cache-dir -U pip setuptools wheel

# Install PyTorch with CUDA support (this is the largest dependency)
RUN pip install --no-cache-dir \
    torch==${TORCH_VERSION} \
    torchvision \
    torchaudio \
    --extra-index-url https://download.pytorch.org/whl/${CUDA_VERSION}

# Install ComfyUI requirements
RUN pip install --no-cache-dir \
    huggingface_hub \
    hf_transfer \
    requests \
    tqdm \
    pillow \
    pyyaml \
    a101 \
    accelerate \
    ampaliang_comfyui_backend \
    anniespcc \
    insightface \
    onnxruntime \
    pycloudflared \
    sentry-sdk \
    lightning-utilities \
    voluptuous

# Install dev tools (conditional)
RUN if [ "$INSTALL_DEV_TOOLS" = "true" ]; then \
        pip install --no-cache-dir \
            jupyterlab \
            jupyterlab_widgets \
            ipykernel \
            ipywidgets; \
    fi

# Install science packages (conditional)
RUN if [ "$INSTALL_SCIENCE_PACKAGES" = "true" ]; then \
        pip install --no-cache-dir \
            numpy \
            scipy \
            matplotlib \
            pandas \
            scikit-learn \
            seaborn; \
    fi

# Install web framework dependencies for preset manager and dashboard
RUN pip install --no-cache-dir \
    flask \
    Flask-Session \
    python-markdown \
    pygments \
    markdown \
    triton \
    fastapi \
    uvicorn[standard] \
    python-multipart \
    starlette \
    jinja2

# Verify Python environment
RUN python --version && \
    pip list | grep torch && \
    echo "Python dependencies installed successfully"

# =============================================================================
# Stage 3: comfyui-core
# =============================================================================
# Purpose: Install ComfyUI, Manager, and custom nodes
# This stage is only rebuilt when ComfyUI or nodes change
# =============================================================================
FROM python-deps AS comfyui-core

# Build arguments
ARG SKIP_CUSTOM_NODES=""
ARG ENABLE_EXTRA_NODES=false

# Clone ComfyUI from GitHub
WORKDIR /tmp/comfyui-build
RUN git clone https://github.com/comfyanonymous/ComfyUI.git comfyui && \
    cd comfyui && \
    pip install --no-cache-dir -r requirements.txt

# Install ComfyUI Manager
RUN cd /tmp/comfyui-build/comfyui/custom_nodes && \
    git clone https://github.com/ltdrdata/ComfyUI-Manager.git && \
    cd ComfyUI-Manager && \
    pip install --no-cache-dir -r requirements.txt

# Copy custom nodes lists
COPY custom_nodes.txt /tmp/custom_nodes.txt
COPY custom_nodes_extra.txt /tmp/custom_nodes_extra.txt

# Install custom nodes (conditional)
RUN if [ -z "$SKIP_CUSTOM_NODES" ]; then \
        cd /tmp/comfyui-build/comfyui/custom_nodes && \
        echo "Installing custom nodes..." && \
        xargs -n 1 git clone --recursive < /tmp/custom_nodes.txt 2>/dev/null || true && \
        find /tmp/comfyui-build/comfyui/custom_nodes -name "requirements.txt" -exec \
            echo "Installing requirements for {}" \; -exec \
            pip install --no-cache-dir -r {} \; && \
        find /tmp/comfyui-build/comfyui/custom_nodes -name "install.py" -exec \
            echo "Running install script {}" \; -exec \
            python {} \; 2>/dev/null || true; \
    else \
        echo "Skipping custom nodes installation"; \
    fi

# Install extra custom nodes (conditional)
RUN if [ "$ENABLE_EXTRA_NODES" = "true" ] && [ -z "$SKIP_CUSTOM_NODES" ]; then \
        cd /tmp/comfyui-build/comfyui/custom_nodes && \
        echo "Installing extra custom nodes..." && \
        xargs -n 1 git clone --recursive < /tmp/custom_nodes_extra.txt 2>/dev/null || true && \
        find /tmp/comfyui-build/comfyui/custom_nodes -maxdepth 2 -name "requirements.txt" -exec \
            pip install --no-cache-dir -r {} \; && \
        find /tmp/comfyui-build/comfyui/custom_nodes -maxdepth 2 -name "install.py" -exec \
            python {} \; 2>/dev/null || true; \
    fi

# Prepare ComfyUI for final location
RUN mkdir -p /app/comfyui && \
    cp -r /tmp/comfyui-build/comfyui/* /app/comfyui/ && \
    rm -rf /tmp/comfyui-build

# Verify ComfyUI installation
RUN test -f /app/comfyui/main.py && \
    test -d /app/comfyui/custom_nodes && \
    test -d /app/comfyui/custom_nodes/ComfyUI-Manager && \
    echo "ComfyUI core installed successfully"

# =============================================================================
# Stage 4: dashboard-builder (conditional)
# =============================================================================
# Purpose: Build dashboard static assets
# Only runs when BUILD_DASHBOARD=true (non-minimal variants)
# =============================================================================
FROM python-deps AS dashboard-builder

ARG BUILD_DASHBOARD=false

# Create minimal dashboard structure
RUN if [ "$BUILD_DASHBOARD" = "true" ]; then \
        echo "Building dashboard assets..." && \
        mkdir -p /app/dashboard/static /app/dashboard/templates; \
    else \
        echo "Skipping dashboard build"; \
        mkdir -p /app/dashboard; \
    fi

# =============================================================================
# Stage 5: runtime
# =============================================================================
# Purpose: Final minimal runtime image
# Copies only necessary artifacts from previous stages
# =============================================================================
FROM nvidia/cuda:12.6.3-runtime-ubuntu24.04 AS runtime

# Build arguments
ARG PYTHON_VERSION=3.13
ARG TORCH_VERSION=2.8.0
ARG CUDA_VERSION=cu126
ARG SKIP_CUSTOM_NODES=""
ARG BUILD_DASHBOARD=false
ARG INSTALL_CODE_SERVER=true

# Set the shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV SHELL=/bin/bash
ENV TZ=Etc/UTC

# Workspace and cache directories (network volume)
ENV RP_WORKSPACE=/workspace
ENV HF_HOME="${RP_WORKSPACE}/.cache/huggingface/"
ENV HF_HUB_ENABLE_HF_TRANSFER=1
ENV HF_XET_HIGH_PERFORMANCE=1
ENV VIRTUALENV_OVERRIDE_APP_DATA="${RP_WORKSPACE}/.cache/virtualenv/"
ENV PIP_CACHE_DIR="${RP_WORKSPACE}/.cache/pip/"
ENV UV_CACHE_DIR="${RP_WORKSPACE}/.cache/uv/"

# Modern pip workarounds
ENV PIP_BREAK_SYSTEM_PACKAGES=1
ENV PIP_ROOT_USER_ACTION=ignore

# Application directories (immutable in container)
ENV APP_DIR=/app
ENV COMFYUI_DIR=${APP_DIR}/comfyui
ENV VENV_DIR=${APP_DIR}/venv

# Update PATH
ENV PATH="${VENV_DIR}/bin:${COMFYUI_DIR}:${APP_DIR}:${PATH}"

# Set working directory
WORKDIR /workspace

# Install runtime dependencies only
RUN apt-get update --yes && \
    apt-get install --yes --no-install-recommends \
        git wget curl bash nginx-light rsync sudo \
        binutils ffmpeg lshw tzdata file \
        libgl1 libglib2.0-0 \
        openssh-server ca-certificates \
        locales && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Set locale
RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

# =============================================================================
# Copy artifacts from builder stages
# =============================================================================

# Copy Python virtual environment (from python-deps stage)
COPY --from=python-deps /app/venv /app/venv

# Copy ComfyUI installation (from comfyui-core stage)
COPY --from=comfyui-core /app/comfyui /app/comfyui

# Copy dashboard assets (from dashboard-builder stage)
COPY --from=dashboard-builder /app/dashboard /app/dashboard

# =============================================================================
# Install code-server (conditional)
# =============================================================================
RUN if [ "$INSTALL_CODE_SERVER" = "true" ]; then \
        curl -fsSL https://code-server.dev/install.sh | sh && \
        echo "Code server installed"; \
    else \
        echo "Skipping code-server installation"; \
    fi

# =============================================================================
# Copy application code and configuration
# =============================================================================

# Create app directory structure
RUN mkdir -p /app/templates /app/static /app/workspace/docs/presets /workspace/config

# Copy NGINX configuration
COPY proxy/nginx.conf /etc/nginx/nginx.conf
COPY proxy/snippets /etc/nginx/snippets
COPY proxy/readme.html /usr/share/nginx/html/readme.html

# Remove existing SSH host keys
RUN rm -f /etc/ssh/ssh_host_*

# Copy README
COPY README.md /usr/share/nginx/html/README.md

# Copy startup scripts
COPY --chmod=755 scripts/start.sh /
COPY --chmod=755 scripts/pre_start.sh /
COPY --chmod=755 scripts/post_start.sh /

# Copy preset management scripts
COPY --chmod=755 scripts/download_presets.sh /
COPY --chmod=755 scripts/download_image_presets.sh /
COPY --chmod=755 scripts/download_audio_presets.sh /
COPY --chmod=755 scripts/install_custom_nodes.sh /

# Validate download scripts
RUN bash -c 'test -f /download_presets.sh && \
    test -f /download_image_presets.sh && \
    test -f /download_audio_presets.sh && \
    test -x /download_presets.sh && \
    test -x /download_image_presets.sh && \
    test -x /download_audio_presets.sh && \
    echo "Download scripts validated successfully"'

# Copy YAML preset management system
COPY --chmod=644 config/presets.yaml /workspace/config/presets.yaml
COPY --chmod=644 config/presets-schema.json /workspace/config/presets-schema.json
COPY --chmod=755 scripts/preset_updater.py /scripts/
COPY --chmod=755 scripts/unified_preset_downloader.py /scripts/
COPY --chmod=755 scripts/generate_download_scripts.py /scripts/
COPY --chmod=755 scripts/preset_validator.py /scripts/
COPY --chmod=755 scripts/test_preset_system.py /scripts/

# Copy preset manager web application
COPY --chmod=755 scripts/preset_manager_cli.py /app/preset_manager.py
COPY --chmod=644 scripts/preset_manager/ /app/preset_manager/
COPY --chmod=644 scripts/templates/ /app/templates/
COPY --chmod=644 scripts/static/ /app/static/
COPY --chmod=644 workspace/docs/presets/ /app/workspace/docs/presets/

# Validate preset manager components
RUN test -f /app/preset_manager.py || exit 1 && \
    test -d /app/preset_manager || exit 1 && \
    test -f /app/preset_manager/core.py || exit 1 && \
    test -f /app/preset_manager/web_interface.py || exit 1 && \
    test -d /app/templates || exit 1 && \
    test -d /app/static || exit 1 && \
    test -f /workspace/config/presets.yaml || exit 1 && \
    echo "Preset manager components validated successfully"

# Test Python imports during build
RUN PYTHONPATH=/app:$PYTHONPATH python3 -c "from preset_manager.core import ModelManager" || exit 1 && \
    echo "Preset manager Python imports validated successfully"

# Copy welcome message
COPY logo/runpod.txt /etc/runpod.txt
RUN echo 'cat /etc/runpod.txt' >> /root/.bashrc && \
    echo 'echo -e "\nFor detailed documentation and guides, please visit:\n\033[1;34mhttps://docs.runpod.io/\033[0m and \033[1;34mhttps://blog.runpod.io/\033[0m\n\n"' >> /root/.bashrc

# Add build information for debugging
RUN echo "Build timestamp: $(date)" > /build-info.txt && \
    echo "Python version: ${PYTHON_VERSION}" >> /build-info.txt && \
    echo "CUDA version: ${CUDA_VERSION}" >> /build-info.txt && \
    echo "PyTorch version: ${TORCH_VERSION}" >> /build-info.txt && \
    echo "Variant flags: CODE_SERVER=${INSTALL_CODE_SERVER}, SKIP_NODES=${SKIP_CUSTOM_NODES}, DASHBOARD=${BUILD_DASHBOARD}" >> /build-info.txt

# Expose ports
EXPOSE 22 3000 8080 8082 8888 9000

# Set entrypoint
CMD ["/start.sh"]
