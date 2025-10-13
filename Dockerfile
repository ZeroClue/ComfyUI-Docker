# ==========================================
# Multi-stage build for optimized Docker images
# ==========================================

# Set the base images for different stages
ARG BASE_IMAGE=nvidia/cuda:12.6.3-devel-ubuntu24.04
ARG RUNTIME_BASE_IMAGE=nvidia/cuda:12.6.3-runtime-ubuntu24.04

# ==========================================
# Builder Stage - Includes build tools
# ==========================================
FROM ${BASE_IMAGE} AS builder

# Set the shell and enable pipefail for better error handling
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Set build environment variables
ARG PYTHON_VERSION
ARG TORCH_VERSION
ARG CUDA_VERSION

ENV SHELL=/bin/bash
ENV PYTHONUNBUFFERED=True
ENV DEBIAN_FRONTEND=noninteractive

# Update and upgrade
RUN apt-get update --yes && \
    apt-get upgrade --yes

RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen

# Install build dependencies (builder stage only)
RUN apt-get install --yes --no-install-recommends \
        git wget curl bash build-essential cmake ninja-build clang \
        libgl1 libglib2.0-0 libomp-dev ca-certificates && \
    apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Install the UV tool from astral-sh
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

# Install Python and create virtual environment
RUN uv python install ${PYTHON_VERSION} --default --preview && \
    uv venv --seed /venv
ENV PATH="/venv/bin:$PATH"

# Install Python packages that need compilation
RUN pip install --no-cache-dir -U \
    pip setuptools wheel \
    torch==${TORCH_VERSION} torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/${CUDA_VERSION}

# ==========================================
# Runtime Stage - Production optimized
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

# Install essential runtime packages
RUN apt-get install --yes --no-install-recommends \
        git wget curl bash nginx-light rsync sudo binutils ffmpeg lshw nano tzdata file \
        libgl1 libglib2.0-0 \
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

# Copy Python packages from builder stage
COPY --from=builder /venv /venv

# Install essential Python packages
RUN pip install --no-cache-dir -U \
    pip setuptools wheel \
    huggingface_hub hf_transfer \
    numpy requests tqdm pillow pyyaml \
    triton

# Install Flask web framework for preset manager
RUN pip install --no-cache-dir \
    flask>=2.0.0 \
    python-markdown>=3.0.0 \
    pygments>=2.10.0 \
    flask-session>=0.4.0

# Conditionally install development and science packages
RUN if [ "$INSTALL_DEV_TOOLS" = "true" ]; then \
        echo "Installing development tools..." && \
        pip install --no-cache-dir jupyterlab jupyterlab_widgets ipykernel ipywidgets; \
    else \
        echo "Skipping development tools installation."; \
    fi

RUN if [ "$INSTALL_SCIENCE_PACKAGES" = "true" ]; then \
        echo "Installing science packages..." && \
        pip install --no-cache-dir scipy matplotlib pandas scikit-learn seaborn; \
    else \
        echo "Skipping science packages installation."; \
    fi

# Install ComfyUI and ComfyUI Manager
RUN git clone https://github.com/comfyanonymous/ComfyUI.git && \
    cd ComfyUI && \
    pip install --no-cache-dir -r requirements.txt && \
    git clone https://github.com/ltdrdata/ComfyUI-Manager.git custom_nodes/ComfyUI-Manager && \
    cd custom_nodes/ComfyUI-Manager && \
    pip install --no-cache-dir -r requirements.txt

COPY custom_nodes.txt /custom_nodes.txt

RUN if [ -z "$SKIP_CUSTOM_NODES" ]; then \
        cd /ComfyUI/custom_nodes && \
        xargs -n 1 git clone --recursive < /custom_nodes.txt && \
        find /ComfyUI/custom_nodes -name "requirements.txt" -exec pip install --no-cache-dir -r {} \; && \
        find /ComfyUI/custom_nodes -name "install.py" -exec python {} \; ; \
    else \
        echo "Skipping custom nodes installation because SKIP_CUSTOM_NODES is set"; \
    fi

# Install Runpod CLI
#RUN wget -qO- cli.runpod.net | sudo bash

# Install code-server (optional - can be skipped with build argument)
RUN if [ "$INSTALL_CODE_SERVER" = "true" ]; then \
        echo "Installing code-server..." && \
        curl -fsSL https://code-server.dev/install.sh | sh; \
    else \
        echo "Skipping code-server installation."; \
    fi

EXPOSE 22 3000 8080 8888 9000

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

# Create required directories for preset manager
RUN mkdir -p /app/templates /app/static /app/workspace/docs/presets

# Copy preset manager web application to /app/
COPY --chmod=755 scripts/preset_manager_cli.py /app/preset_manager.py
COPY --chmod=644 scripts/preset_manager/ /app/preset_manager/
COPY --chmod=644 scripts/templates/ /app/templates/
COPY --chmod=644 scripts/static/ /app/static/
COPY --chmod=644 workspace/docs/presets/ /app/workspace/docs/presets/

# Welcome Message
#COPY logo/runpod.txt /etc/runpod.txt
#RUN echo 'cat /etc/runpod.txt' >> /root/.bashrc
COPY logo/zeroclue.txt /etc/zeroclue.txt
RUN echo 'cat /etc/zeroclue.txt' >> /root/.bashrc
RUN echo 'echo -e "\nFor detailed documentation and guides, please visit:\n\033[1;34mhttps://docs.runpod.io/\033[0m and \033[1;34mhttps://blog.runpod.io/\033[0m\n\n"' >> /root/.bashrc

# Set entrypoint to the start script
CMD ["/start.sh"]
