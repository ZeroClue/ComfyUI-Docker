#!/bin/bash
# ==============================================================================
# ComfyUI-Docker Startup Script v2.0
# ==============================================================================
# Revolutionary Architecture - NO RSYNC!
# - App code is in /app (container volume)
# - Models are in /workspace/models (network volume)
# - ComfyUI uses extra_model_paths.yaml
# - Near-instant startup
# ==============================================================================

set -e

echo "=================================================="
echo "  ComfyUI-Docker v2.0 - Revolutionary Architecture"
echo "=================================================="

# Ensure venv Python is first in PATH
export PATH="/app/venv/bin:$PATH"

# Set PYTHONPATH for app modules
export PYTHONPATH="/app:$PYTHONPATH"

# ---------------------------------------------------------------------------- #
#                          Environment Validation                               #
# ---------------------------------------------------------------------------- #

echo "[STARTUP] Validating environment..."

# Verify critical paths exist
if [ ! -d "/app/comfyui" ]; then
    echo "[ERROR] ComfyUI not found at /app/comfyui"
    exit 1
fi

if [ ! -d "/app/venv" ]; then
    echo "[ERROR] Virtual environment not found at /app/venv"
    exit 1
fi

if [ ! -f "/app/comfyui/extra_model_paths.yaml" ]; then
    echo "[WARN] extra_model_paths.yaml not found, generating..."
    python3 /scripts/generate_extra_paths.py
fi

echo "[STARTUP] Environment validated successfully"

# ---------------------------------------------------------------------------- #
#                          Directory Setup                                      #
# ---------------------------------------------------------------------------- #

echo "[STARTUP] Setting up directories..."

# Create model directories if they don't exist (network volume)
mkdir -p /workspace/models/{checkpoints,diffusion_models,text_encoders,vae,clip_vision,loras,audio_encoders,upscale_models,controlnet,embeddings,TTS}
mkdir -p /workspace/output
mkdir -p /workspace/logs
mkdir -p /workspace/config
mkdir -p /workspace/uploads
mkdir -p /tmp/studio_sessions

# Create app directories (container volume)
mkdir -p /app/templates
mkdir -p /app/static

echo "[STARTUP] Directories ready"

# ---------------------------------------------------------------------------- #
#                          Timezone Setup                                       #
# ---------------------------------------------------------------------------- #

export TZ=${TIME_ZONE:-"Etc/UTC"}
echo "[STARTUP] Timezone set to $TZ"

if [ -f /usr/bin/timedatectl ]; then
    timedatectl set-timezone "$TZ" 2>/dev/null || true
fi

# ---------------------------------------------------------------------------- #
#                          Service Functions                                    #
# ---------------------------------------------------------------------------- #

start_nginx() {
    echo "[STARTUP] Starting Nginx..."
    service nginx start
}

setup_ssh() {
    if [ -n "$PUBLIC_KEY" ]; then
        echo "[STARTUP] Setting up SSH..."
        mkdir -p ~/.ssh
        echo "$PUBLIC_KEY" >> ~/.ssh/authorized_keys
        chmod 700 -R ~/.ssh

        # Generate SSH host keys if missing
        for keytype in rsa ecdsa ed25519; do
            if [ ! -f "/etc/ssh/ssh_host_${keytype}_key" ]; then
                ssh-keygen -t $keytype -f "/etc/ssh/ssh_host_${keytype}_key" -q -N ''
            fi
        done

        service ssh start
        echo "[STARTUP] SSH started"
    fi
}

start_jupyter() {
    if [ "${ENABLE_JUPYTERLAB,,}" = "false" ]; then
        return
    fi

    if ! command -v jupyter &> /dev/null; then
        echo "[STARTUP] JupyterLab not installed, skipping"
        return
    fi

    echo "[STARTUP] Starting JupyterLab..."
    local jupyter_token=""
    if [ -n "$ACCESS_PASSWORD" ]; then
        jupyter_token="$ACCESS_PASSWORD"
    fi

    cd /
    nohup jupyter lab --allow-root \
        --no-browser \
        --port=8888 \
        --ip=0.0.0.0 \
        --FileContentsManager.delete_to_trash=False \
        --ContentsManager.allow_hidden=True \
        --ServerApp.terminado_settings='{"shell_command":["/bin/bash"]}' \
        --ServerApp.token="${jupyter_token}" \
        --ServerApp.allow_origin=* \
        --ServerApp.preferred_dir=/workspace \
        &> /workspace/logs/jupyterlab.log &
    echo "[STARTUP] JupyterLab started on port 8888"
}

start_code_server() {
    if [ "${ENABLE_CODE_SERVER,,}" = "false" ]; then
        return
    fi

    if ! command -v code-server &> /dev/null; then
        echo "[STARTUP] code-server not installed, skipping"
        return
    fi

    echo "[STARTUP] Starting code-server..."
    local auth_flag="none"
    if [ -n "$ACCESS_PASSWORD" ]; then
        export PASSWORD="$ACCESS_PASSWORD"
        auth_flag="password"
    fi

    nohup code-server /workspace --bind-addr 0.0.0.0:8080 \
        --auth $auth_flag \
        --ignore-last-opened \
        --disable-workspace-trust \
        &> /workspace/logs/code-server.log &
    echo "[STARTUP] code-server started on port 8080"
}

start_comfyui() {
    echo "[STARTUP] Starting ComfyUI..."

    cd /app/comfyui

    # Build ComfyUI arguments
    local comfyui_args="--listen --port 3000"

    # Add extra model paths config
    if [ -f "/app/comfyui/extra_model_paths.yaml" ]; then
        comfyui_args="$comfyui_args --extra-model-paths-config /app/comfyui/extra_model_paths.yaml"
    fi

    # Set output directory
    comfyui_args="$comfyui_args --output-directory /workspace/output"

    # Add any extra args from environment
    if [ -n "$COMFYUI_EXTRA_ARGS" ]; then
        comfyui_args="$comfyui_args $COMFYUI_EXTRA_ARGS"
    fi

    nohup python main.py $comfyui_args &> /workspace/logs/comfyui.log &
    local pid=$!
    echo "[STARTUP] ComfyUI started with PID $pid on port 3000"

    # Wait for ComfyUI to be ready
    echo "[STARTUP] Waiting for ComfyUI to be ready..."
    local max_wait=30
    local waited=0
    while [ $waited -lt $max_wait ]; do
        if curl -s http://localhost:3000/system_stats > /dev/null 2>&1; then
            echo "[STARTUP] ComfyUI is ready!"
            break
        fi
        sleep 1
        ((waited++))
    done

    if [ $waited -ge $max_wait ]; then
        echo "[WARN] ComfyUI may not be fully ready, continuing..."
    fi
}

start_preset_manager() {
    if [ "${ENABLE_PRESET_MANAGER,,}" = "false" ]; then
        return
    fi

    echo "[STARTUP] Starting Preset Manager..."

    cd /app
    nohup python preset_manager.py &> /workspace/logs/preset_manager.log &
    local pid=$!
    echo "[STARTUP] Preset Manager started with PID $pid on port 9000 (via Nginx)"
}

start_studio() {
    if [ "${ENABLE_STUDIO,,}" = "false" ]; then
        return
    fi

    echo "[STARTUP] Starting ComfyUI Studio..."

    export WORKSPACE_ROOT="/workspace"
    export STUDIO_PORT="${STUDIO_PORT:-5000}"

    cd /scripts
    nohup python comfyui_studio.py &> /workspace/logs/comfyui_studio.log &
    echo "[STARTUP] ComfyUI Studio started on port ${STUDIO_PORT}"
}

download_presets() {
    # Check if any preset download variables are set
    local has_presets=false

    if [ -n "$PRESET_DOWNLOAD" ] || [ -n "$IMAGE_PRESET_DOWNLOAD" ] || \
       [ -n "$AUDIO_PRESET_DOWNLOAD" ] || [ -n "$UNIFIED_PRESET_DOWNLOAD" ]; then
        has_presets=true
    fi

    if [ "$has_presets" = "true" ]; then
        echo "[STARTUP] Downloading presets..."

        if [ -f "/scripts/unified_preset_downloader.py" ]; then
            python3 /scripts/unified_preset_downloader.py status
            python3 /scripts/unified_preset_downloader.py download --quiet
        else
            echo "[WARN] Unified preset downloader not found"
        fi
    else
        echo "[STARTUP] No presets to download"
    fi
}

export_env_vars() {
    echo "[STARTUP] Exporting environment variables..."
    printenv | grep -E '^RUNPOD_|^PATH=|^_=' | awk -F = '{ print "export " $1 "=\"" $2 "\"" }' >> /etc/rp_environment
    echo 'source /etc/rp_environment' >> ~/.bashrc
}

# ---------------------------------------------------------------------------- #
#                          Main Startup Sequence                                #
# ---------------------------------------------------------------------------- #

echo ""
echo "[STARTUP] Starting services..."
echo ""

# Start Nginx first
start_nginx

# Download presets if configured (runs in background for faster startup)
if [ -n "$PRESET_DOWNLOAD" ] || [ -n "$IMAGE_PRESET_DOWNLOAD" ] || \
   [ -n "$AUDIO_PRESET_DOWNLOAD" ] || [ -n "$UNIFIED_PRESET_DOWNLOAD" ]; then
    download_presets &
fi

# Start core services
setup_ssh
start_comfyui
start_preset_manager
start_studio
start_jupyter
start_code_server

# Export environment variables
export_env_vars

echo ""
echo "=================================================="
echo "  ComfyUI-Docker is ready!"
echo "=================================================="
echo ""
echo "  Services:"
echo "    - ComfyUI:        http://localhost:3000"
echo "    - Preset Manager: http://localhost:9000"
echo "    - Studio:         http://localhost:5000"
echo "    - Code Server:    http://localhost:8080"
echo "    - JupyterLab:     http://localhost:8888"
echo ""
echo "  Model paths configured via /app/comfyui/extra_model_paths.yaml"
echo "  Models directory: /workspace/models"
echo "  Output directory: /workspace/output"
echo ""
echo "=================================================="

# Keep container running
sleep infinity
