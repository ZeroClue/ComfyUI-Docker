# Set the base image
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

# Set the shell and enable pipefail for better error handling
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Set basic environment variables
ARG PYTHON_VERSION
ARG TORCH_VERSION
ARG CUDA_VERSION
ARG SKIP_CUSTOM_NODES
ARG ENABLE_EXTRA_NODES=false
ARG INSTALL_CODE_SERVER=true
ARG INSTALL_DEV_TOOLS=true
ARG INSTALL_SCIENCE_PACKAGES=true

# Set basic environment variables
ENV SHELL=/bin/bash 
ENV PYTHONUNBUFFERED=True 
ENV DEBIAN_FRONTEND=noninteractive

# Set the default workspace directory
ENV RP_WORKSPACE=/workspace

# Override the default huggingface cache directory.
ENV HF_HOME="${RP_WORKSPACE}/.cache/huggingface/"

# Faster transfer of models from the hub to the container
ENV HF_HUB_ENABLE_HF_TRANSFER=1
ENV HF_XET_HIGH_PERFORMANCE=1

# Shared python package cache
ENV VIRTUALENV_OVERRIDE_APP_DATA="${RP_WORKSPACE}/.cache/virtualenv/"
ENV PIP_CACHE_DIR="${RP_WORKSPACE}/.cache/pip/"
ENV UV_CACHE_DIR="${RP_WORKSPACE}/.cache/uv/"

# modern pip workarounds
ENV PIP_BREAK_SYSTEM_PACKAGES=1
ENV PIP_ROOT_USER_ACTION=ignore

# Set TZ and Locale
ENV TZ=Etc/UTC

# Set working directory
WORKDIR /

# Update and upgrade
RUN apt-get update --yes && \
    apt-get upgrade --yes

RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen

# Install essential packages
RUN apt-get install --yes --no-install-recommends \
        git wget curl bash nginx-light rsync sudo binutils ffmpeg lshw nano tzdata file build-essential cmake nvtop \
        libgl1 libglib2.0-0 clang libomp-dev ninja-build \
        openssh-server ca-certificates && \
    apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Install the UV tool from astral-sh
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

# Install Python and create virtual environment
RUN uv python install ${PYTHON_VERSION} --default --preview && \
    uv venv --seed /venv
ENV PATH="/workspace/venv/bin:/venv/bin:$PATH"

# Install essential Python packages and dependencies
RUN pip install --no-cache-dir -U pip setuptools wheel && \
    if [ "$INSTALL_DEV_TOOLS" = "true" ]; then \
        pip install --no-cache-dir jupyterlab jupyterlab_widgets ipykernel ipywidgets; \
    fi && \
    pip install --no-cache-dir huggingface_hub hf_transfer && \
    if [ "$INSTALL_SCIENCE_PACKAGES" = "true" ]; then \
        pip install --no-cache-dir numpy scipy matplotlib pandas scikit-learn seaborn; \
    fi && \
    pip install --no-cache-dir requests tqdm pillow pyyaml flask python-markdown pygments Flask Flask-Session markdown triton && \
    pip install --no-cache-dir torch==${TORCH_VERSION} torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/${CUDA_VERSION}

# Install ComfyUI and ComfyUI Manager
RUN git clone https://github.com/comfyanonymous/ComfyUI.git && \
    cd ComfyUI && \
    pip install --no-cache-dir -r requirements.txt && \
    git clone https://github.com/ltdrdata/ComfyUI-Manager.git custom_nodes/ComfyUI-Manager && \
    cd custom_nodes/ComfyUI-Manager && \
    pip install --no-cache-dir -r requirements.txt

COPY custom_nodes.txt /custom_nodes.txt
COPY custom_nodes_extra.txt /custom_nodes_extra.txt

RUN if [ -z "$SKIP_CUSTOM_NODES" ]; then \
        cd /ComfyUI/custom_nodes && \
        xargs -n 1 git clone --recursive < /custom_nodes.txt && \
        find /ComfyUI/custom_nodes -name "requirements.txt" -exec pip install --no-cache-dir -r {} \; && \
        find /ComfyUI/custom_nodes -name "install.py" -exec python {} \; ; \
    else \
        echo "Skipping custom nodes installation because SKIP_CUSTOM_NODES is set"; \
    fi

# Install extra custom nodes (optional)
RUN if [ "$ENABLE_EXTRA_NODES" = "true" ] && [ -z "$SKIP_CUSTOM_NODES" ]; then \
        cd /ComfyUI/custom_nodes && \
        xargs -n 1 git clone --recursive < /custom_nodes_extra.txt && \
        find /ComfyUI/custom_nodes -maxdepth 2 -name "requirements.txt" -exec pip install --no-cache-dir -r {} \; && \
        find /ComfyUI/custom_nodes -maxdepth 2 -name "install.py" -exec python {} \; ; \
    fi

# Install SageAttention or ComfyUI-Attention-Optimizer based on CUDA version
# SageAttention: CUDA 12.0-12.9 (2-4x video generation speedup)
# ComfyUI-Attention-Optimizer: CUDA 13.0+ (1.5-2x speedup, works with all CUDA versions)
COPY --chmod=755 scripts/install_sageattention.sh /tmp/install_sageattention.sh
RUN bash /tmp/install_sageattention.sh && rm /tmp/install_sageattention.sh

# Install Runpod CLI
#RUN wget -qO- cli.runpod.net | sudo bash

# Install code-server
RUN if [ "$INSTALL_CODE_SERVER" = "true" ]; then \
        curl -fsSL https://code-server.dev/install.sh | sh; \
    fi

EXPOSE 22 3000 8080 8888

# NGINX Proxy
COPY proxy/nginx.conf /etc/nginx/nginx.conf
COPY proxy/snippets /etc/nginx/snippets
COPY proxy/readme.html /usr/share/nginx/html/readme.html

# Remove existing SSH host keys
RUN rm -f /etc/ssh/ssh_host_*

# Copy the README.md
COPY README.md /usr/share/nginx/html/README.md

# Start Scripts
COPY --chmod=755 scripts/start.sh /
COPY --chmod=755 scripts/pre_start.sh /
COPY --chmod=755 scripts/post_start.sh /

COPY --chmod=755 scripts/download_presets.sh /
COPY --chmod=755 scripts/download_image_presets.sh /
COPY --chmod=755 scripts/download_audio_presets.sh /
COPY --chmod=755 scripts/install_custom_nodes.sh /

# Validate download scripts were copied and are executable
RUN bash -c 'test -f /download_presets.sh && test -f /download_image_presets.sh && test -f /download_audio_presets.sh && test -x /download_presets.sh && test -x /download_image_presets.sh && test -x /download_audio_presets.sh && echo "Download scripts validated successfully"'
RUN mkdir -p /app/templates /app/static /app/workspace/docs/presets /workspace/config

# Copy YAML preset management system
COPY --chmod=644 config/presets.yaml /workspace/config/presets.yaml
COPY --chmod=644 config/presets-schema.json /workspace/config/presets-schema.json
COPY --chmod=755 scripts/preset_updater.py /scripts/
COPY --chmod=755 scripts/unified_preset_downloader.py /scripts/
COPY --chmod=755 scripts/generate_download_scripts.py /scripts/
COPY --chmod=755 scripts/preset_validator.py /scripts/
COPY --chmod=755 scripts/test_preset_system.py /scripts/

# Copy preset manager web application to /app/
COPY --chmod=755 scripts/preset_manager_cli.py /app/preset_manager.py
COPY --chmod=644 scripts/preset_manager/ /app/preset_manager/
COPY --chmod=644 scripts/templates/ /app/templates/
COPY --chmod=644 scripts/static/ /app/static/
COPY --chmod=644 workspace/docs/presets/ /app/workspace/docs/presets/

# Validate preset manager components were copied successfully
RUN test -f /app/preset_manager.py || exit 1 && \
    test -d /app/preset_manager || exit 1 && \
    test -f /app/preset_manager/core.py || exit 1 && \
    test -f /app/preset_manager/web_interface.py || exit 1 && \
    test -d /app/templates || exit 1 && \
    test -d /app/static || exit 1 && \
    test -f /workspace/config/presets.yaml || exit 1 && \
    echo "Preset manager components validated successfully"

# Test Python imports during build to catch import errors early
RUN PYTHONPATH=/app:$PYTHONPATH python3 -c "from preset_manager.core import ModelManager" || exit 1 && \
    echo "Preset manager Python imports validated successfully"

# Welcome Message
COPY logo/runpod.txt /etc/runpod.txt
RUN echo 'cat /etc/runpod.txt' >> /root/.bashrc
RUN echo 'echo -e "\nFor detailed documentation and guides, please visit:\n\033[1;34mhttps://docs.runpod.io/\033[0m and \033[1;34mhttps://blog.runpod.io/\033[0m\n\n"' >> /root/.bashrc

# Add build information for debugging
RUN echo "Build timestamp: $(date)" > /build-info.txt && \
    echo "Python version: $(python --version)" >> /build-info.txt && \
    echo "CUDA version: ${CUDA_VERSION}" >> /build-info.txt && \
    echo "PyTorch version: ${TORCH_VERSION}" >> /build-info.txt && \
    echo "Variant flags: CODE_SERVER=${INSTALL_CODE_SERVER}, DEV_TOOLS=${INSTALL_DEV_TOOLS}, SCIENCE_PKGS=${INSTALL_SCIENCE_PACKAGES}" >> /build-info.txt

# ============================================================================
# FINAL CLEANUP - Remove unnecessary build tools to reclaim space
# ============================================================================
# Keep CUDA development tools (nvcc) for custom node compatibility
# Remove general build tools that are no longer needed after installation
RUN apt-get remove -y \
        build-essential \
        cmake \
        ninja-build \
        clang \
        libomp-dev \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/* /tmp/* /root/.cache/*

# Clear pip and UV caches
RUN pip cache purge \
    && rm -rf /root/.cache/uv \
    && rm -rf /root/.cache/pip

# Clear Python __pycache__ directories
RUN find /venv -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
RUN find /ComfyUI -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Set entrypoint to the start script
CMD ["/start.sh"]