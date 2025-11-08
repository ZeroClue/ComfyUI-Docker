# ==========================================
# Modern Multi-stage build optimized Docker images (2025 Best Practices)
# ==========================================

# Enable Docker BuildKit for cache mounts and advanced features
# syntax=docker/dockerfile:1.6

# Set the base images - use devel for building, runtime for production
ARG BASE_IMAGE=nvidia/cuda:12.8.0-devel-ubuntu22.04
ARG RUNTIME_BASE_IMAGE=nvidia/cuda:12.8.0-runtime-ubuntu22.04


# ==========================================
# UV Tools Stage - Temporary UV for build operations
# ==========================================
FROM ghcr.io/astral-sh/uv:latest AS uv-tools

# ==========================================
# Builder Stage - Heavy compilation and package building
# ==========================================
FROM ${BASE_IMAGE} AS builder

# Import UV from uv-tools stage
COPY --from=uv-tools /uv /uvx /bin/

# Set the shell and enable pipefail for better error handling
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Set build environment variables
ARG PYTHON_VERSION
ARG TORCH_VERSION
ARG CUDA_VERSION

ENV SHELL=/bin/bash
ENV PYTHONUNBUFFERED=True
ENV DEBIAN_FRONTEND=noninteractive
# Prevent UV from creating symlinks that break across stages
ENV UV_LINK_MODE=copy
# Enable bytecode compilation for faster startup
ENV UV_COMPILE_BYTECODE=1

# Set working directory
WORKDIR /app

# Update and upgrade
RUN apt-get update --yes && \
    apt-get upgrade --yes

RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen

# Install build dependencies (builder stage only)
RUN apt-get install --yes --no-install-recommends \
        git wget curl bash build-essential cmake ninja-build clang \
        libgl1 libglib2.0-0 libomp-dev ca-certificates && \
    apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Install Python and create virtual environment using cache mounts
RUN --mount=type=cache,target=/root/.cache/uv \
    uv python install ${PYTHON_VERSION} --default --preview && \
    uv venv --seed /app/.venv

# Set virtual environment path
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Install PyTorch and core dependencies using UV with cache mounts
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --no-cache-dir -U \
    pip setuptools wheel && \
    uv pip install --no-cache-dir \
    torch==${TORCH_VERSION} torchvision torchaudio \
    --extra-index-url https://download.pytorch.org/whl/${CUDA_VERSION}

# Install triton in builder stage since it requires compilation
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --no-cache-dir triton

# Install SageAttention2
RUN git clone https://github.com/thu-ml/SageAttention.git && \
    cd SageAttention && \
    export EXT_PARALLEL=4 NVCC_APPEND_FLAGS="--threads 8" MAX_JOBS=32 && \
    uv pip install --no-cache-dir . && \
    cd .. && \
    rm -rf SageAttention

# Install additional ML packages for better performance
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --no-cache-dir \
    huggingface_hub hf_transfer \
    numpy requests tqdm pillow pyyaml \
    flask python-markdown pygments Flask Flask-Session markdown

# Export requirements for reproducibility (optional)
RUN uv pip freeze > requirements-built.txt


# ==========================================
# Runtime Stage - Production optimized minimal image
# ==========================================
FROM ${RUNTIME_BASE_IMAGE} AS runtime

# Set the shell and enable pipefail for better error handling
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Set runtime environment variables
ARG PYTHON_VERSION
ARG TORCH_VERSION
ARG CUDA_VERSION
ARG SKIP_CUSTOM_NODES
ARG INSTALL_DEV_TOOLS=true
ARG INSTALL_SCIENCE_PACKAGES=true
ARG INSTALL_CODE_SERVER=true

# Set basic environment variables
ENV SHELL=/bin/bash
ENV PYTHONUNBUFFERED=True
ENV DEBIAN_FRONTEND=noninteractive

# Set the default workspace directory
ENV RP_WORKSPACE=/workspace

# Override the default huggingface cache directory for better performance
ENV HF_HOME="${RP_WORKSPACE}/.cache/huggingface/"

# Faster transfer of models from the hub to the container
ENV HF_HUB_ENABLE_HF_TRANSFER=1
ENV HF_XET_HIGH_PERFORMANCE=1

# Use local cache directories for better performance
ENV VIRTUALENV_OVERRIDE_APP_DATA="/root/.cache/virtualenv/"
ENV PIP_CACHE_DIR="/root/.cache/pip/"
ENV UV_CACHE_DIR="/root/.cache/uv/"

# Set TZ and Locale
ENV TZ=Etc/UTC

# Set working directory
WORKDIR /app

# Update and upgrade
RUN apt-get update --yes && \
    apt-get upgrade --yes

RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen

# Install essential runtime packages only (minimal footprint)
RUN apt-get install --yes --no-install-recommends \
        git curl wget bash nginx-light rsync sudo binutils ffmpeg lshw nano tzdata file \
        libgl1 libglib2.0-0 \
        openssh-server ca-certificates \
        # Python build essentials for any runtime compilation needs
        python3-dev python3-pip && \
    apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy the complete virtual environment from builder stage
# This preserves all UV optimizations and compiled packages
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Set virtual environment paths
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV=/app/.venv

# Copy ComfyUI and set up the application
COPY --from=builder --chown=appuser:appuser /app/ComfyUI /app/ComfyUI

# Change to app user for security
USER appuser
WORKDIR /app

# Install ComfyUI and ComfyUI Manager if not already present
RUN if [ ! -d "ComfyUI" ]; then \
        git clone https://github.com/comfyanonymous/ComfyUI.git && \
        cd ComfyUI && \
        uv pip install --no-cache-dir -r requirements.txt && \
        git clone https://github.com/ltdrdata/ComfyUI-Manager.git custom_nodes/ComfyUI-Manager && \
        cd custom_nodes/ComfyUI-Manager && \
        uv pip install --no-cache-dir -r requirements.txt && \
        cd ../..; \
    fi

# Conditionally install development tools (as appuser)
RUN if [ "$INSTALL_DEV_TOOLS" = "true" ]; then \
        echo "Installing development tools..." && \
        uv pip install --no-cache-dir jupyterlab jupyterlab_widgets ipykernel ipywidgets; \
    fi

# Set jupyter lab dark theme as default (if installed)
COPY --chown=appuser:appuser jupyter/overrides.json /usr/local/share/jupyter/lab/settings/overrides.json

# Conditionally install science packages
RUN if [ "$INSTALL_SCIENCE_PACKAGES" = "true" ]; then \
        echo "Installing science packages..." && \
        uv pip install --no-cache-dir scipy matplotlib pandas scikit-learn seaborn; \
    fi

# Handle custom nodes
COPY --chown=appuser:appuser custom_nodes.txt /app/custom_nodes.txt
RUN if [ -z "$SKIP_CUSTOM_NODES" ]; then \
        echo "Installing essential custom nodes only..." && \
        cd /app/ComfyUI/custom_nodes && \
        for repo in "https://github.com/ComfyUI-Manager/ComfyUI-Manager.git" \
                     "https://github.com/ltdrdata/ComfyUI-Impact-Pack.git"; do \
            if grep -q "$(basename "$repo" .git)" /app/custom_nodes.txt; then \
                echo "Installing $(basename "$repo" .git)"; \
                git clone "$repo"; \
            fi; \
        done && \
        find /app/ComfyUI/custom_nodes -maxdepth 2 -name "requirements.txt" -exec uv pip install --no-cache-dir -r {} \; && \
        find /app/ComfyUI/custom_nodes -maxdepth 2 -name "install.py" -exec python {} \; && \
        find /app/ComfyUI/custom_nodes -maxdepth 2 -name ".git" -type d -exec rm -rf {} + 2>/dev/null || true; \
    fi

# Install code-server if requested (switch back to root for system installation)
USER root
RUN if [ "$INSTALL_CODE_SERVER" = "true" ]; then \
        echo "Installing code-server..." && \
        curl -fsSL https://code-server.dev/install.sh | sh; \
    fi
USER appuser

# Expose ports
EXPOSE 22 3000 8080 8888 9000

# NGINX Proxy configuration (as root)
USER root
COPY --chown=appuser:appuser proxy/nginx.conf /etc/nginx/nginx.conf
COPY --chown=appuser:appuser proxy/snippets /etc/nginx/snippets
COPY --chown=appuser:appuser proxy/readme.html /usr/share/nginx/html/readme.html

# Remove existing SSH host keys
RUN rm -f /etc/ssh/ssh_host_*

# Copy the README.md
COPY --chown=appuser:appuser README.md /usr/share/nginx/html/README.md

# Copy start scripts and set permissions
COPY --chown=appuser:appuser --chmod=755 scripts/start.sh /
COPY --chown=appuser:appuser --chmod=755 scripts/pre_start.sh /
COPY --chown=appuser:appuser --chmod=755 scripts/post_start.sh /

COPY --chown=appuser:appuser --chmod=755 scripts/download_presets.sh /
COPY --chown=appuser:appuser --chmod=755 scripts/download_image_presets.sh /
COPY --chown=appuser:appuser --chmod=755 scripts/download_audio_presets.sh /
COPY --chown=appuser:appuser --chmod=755 scripts/install_custom_nodes.sh /

# Create required directories for preset manager and YAML configuration
RUN mkdir -p /app/templates /app/static /app/workspace/docs/presets /workspace/config && \
    chown -R appuser:appuser /app /workspace

# Copy YAML preset management system
COPY --chown=appuser:appuser --chmod=644 config/presets.yaml /workspace/config/presets.yaml
COPY --chown=appuser:appuser --chmod=644 config/presets-schema.json /workspace/config/presets-schema.json
COPY --chown=appuser:appuser --chmod=755 scripts/preset_updater.py /scripts/
COPY --chown=appuser:appuser --chmod=755 scripts/unified_preset_downloader.py /scripts/
COPY --chown=appuser:appuser --chmod=755 scripts/generate_download_scripts.py /scripts/
COPY --chown=appuser:appuser --chmod=755 scripts/preset_validator.py /scripts/
COPY --chown=appuser:appuser --chmod=755 scripts/test_preset_system.py /scripts/

# Copy preset manager web application to /app/
COPY --chown=appuser:appuser --chmod=755 scripts/preset_manager_cli.py /app/preset_manager.py
COPY --chown=appuser:appuser --chmod=644 scripts/preset_manager/ /app/preset_manager/
COPY --chown=appuser:appuser --chmod=644 scripts/templates/ /app/templates/
COPY --chown=appuser:appuser --chmod=644 scripts/static/ /app/static/
COPY --chown=appuser:appuser --chmod=644 workspace/docs/presets/ /app/workspace/docs/presets/

# Welcome Message
COPY --chown=appuser:appuser logo/zeroclue.txt /etc/zeroclue.txt
RUN echo 'cat /etc/zeroclue.txt' >> /home/appuser/.bashrc && \
    echo 'echo -e "\nFor detailed documentation and guides, please visit:\n\033[1;34mhttps://docs.runpod.io/\033[0m and \033[1;34mhttps://blog.runpod.io/\033[0m\n\n"' >> /home/appuser/.bashrc

# Add build information for debugging
RUN echo "Build timestamp: $(date)" > /build-info.txt && \
    echo "Python version: $(python --version)" >> /build-info.txt && \
    echo "CUDA version: ${CUDA_VERSION}" >> /build-info.txt && \
    echo "PyTorch version: ${TORCH_VERSION}" >> /build-info.txt

# Final cleanup and set back to app user
RUN uv cache clean --all && \
    find /app/.venv -name "*.pyc" -delete && \
    find /app/.venv -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true && \
    chown -R appuser:appuser /build-info.txt

USER appuser

# Set entrypoint to the start script
CMD ["/start.sh"]