#!/bin/bash
set -e  # Exit the script if any statement returns a non-true return value

# Revolutionary Architecture: Python venv is in container at /venv
# No rsync needed - instant startup
export PATH="/venv/bin:$PATH"

# ---------------------------------------------------------------------------- #
#                          Function Definitions                                #
# ---------------------------------------------------------------------------- #

# Start nginx service
start_nginx() {
    echo "Starting Nginx service..."
    service nginx start
}

# Execute script if exists
execute_script() {
    local script_path=$1
    local script_msg=$2
    if [[ -f ${script_path} ]]; then
        echo "${script_msg}"
        bash ${script_path}
    fi
}

# Setup ssh
setup_ssh() {
    if [[ $PUBLIC_KEY ]]; then
        echo "Setting up SSH..."
        mkdir -p ~/.ssh
        echo "$PUBLIC_KEY" >> ~/.ssh/authorized_keys
        chmod 700 -R ~/.ssh

        if [ ! -f /etc/ssh/ssh_host_rsa_key ]; then
            ssh-keygen -t rsa -f /etc/ssh/ssh_host_rsa_key -q -N ''
            echo "RSA key fingerprint:"
            ssh-keygen -lf /etc/ssh/ssh_host_rsa_key.pub
        fi

        if [ ! -f /etc/ssh/ssh_host_dsa_key ]; then
            ssh-keygen -t dsa -f /etc/ssh/ssh_host_dsa_key -q -N ''
            echo "DSA key fingerprint:"
            ssh-keygen -lf /etc/ssh/ssh_host_dsa_key.pub
        fi

        if [ ! -f /etc/ssh/ssh_host_ecdsa_key ]; then
            ssh-keygen -t ecdsa -f /etc/ssh/ssh_host_ecdsa_key -q -N ''
            echo "ECDSA key fingerprint:"
            ssh-keygen -lf /etc/ssh/ssh_host_ecdsa_key.pub
        fi

        if [ ! -f /etc/ssh/ssh_host_ed25519_key ]; then
            ssh-keygen -t ed25519 -f /etc/ssh/ssh_host_ed25519_key -q -N ''
            echo "ED25519 key fingerprint:"
            ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
        fi

        service ssh start

        echo "SSH host keys:"
        for key in /etc/ssh/*.pub; do
            echo "Key: $key"
            ssh-keygen -lf $key
        done
    fi
}

# Export env vars
export_env_vars() {
    echo "Exporting environment variables..."
    printenv | grep -E '^RUNPOD_|^PATH=|^_=' | awk -F = '{ print "export " $1 "=\"" $2 "\"" }' >> /etc/rp_environment
    echo 'source /etc/rp_environment' >> ~/.bashrc
}

# Start jupyter
start_jupyter() {
    # Check if JupyterLab is disabled
    if [[ "${ENABLE_JUPYTERLAB,,}" == "false" ]]; then
        echo "JupyterLab is disabled (ENABLE_JUPYTERLAB=false). Skipping startup."
        return
    fi

    # Check if jupyter is installed
    if ! command -v jupyter &> /dev/null; then
        echo "JupyterLab not installed, skipping startup."
        return
    fi

    # Default to not using a password
    JUPYTER_PASSWORD=""

    # Allow a password to be set by providing the ACCESS_PASSWORD environment variable
    if [[ ${ACCESS_PASSWORD} ]]; then
        echo "Starting JupyterLab with the provided password..."
        JUPYTER_PASSWORD=${ACCESS_PASSWORD}
    else
        echo "Starting JupyterLab without a password... (ACCESS_PASSWORD environment variable is not set.)"
    fi
    
    mkdir -p /workspace/logs
    cd / && \
    nohup jupyter lab --allow-root \
        --no-browser \
        --port=8888 \
        --ip=* \
        --FileContentsManager.delete_to_trash=False \
        --ContentsManager.allow_hidden=True \
        --ServerApp.terminado_settings='{"shell_command":["/bin/bash"]}' \
        --ServerApp.token="${JUPYTER_PASSWORD}" \
        --ServerApp.allow_origin=* \
        --ServerApp.preferred_dir=/workspace &> /workspace/logs/jupyterlab.log &
    echo "JupyterLab started"
}

# Start code-server
start_code_server() {
    # Check if code-server should be started (default: true)
    if [[ "${ENABLE_CODE_SERVER,,}" == "false" ]]; then
        echo "code-server is disabled (ENABLE_CODE_SERVER=false). Skipping startup."
        return
    fi

    # Check if code-server is installed
    if ! command -v code-server &> /dev/null; then
        echo "code-server not installed, skipping startup."
        return
    fi

    echo "Starting code-server..."
    mkdir -p /workspace/logs

    # Allow a password to be set by providing the ACCESS_PASSWORD environment variable
    if [[ -n "${ACCESS_PASSWORD}" ]]; then
        echo "Starting code-server with the provided password..."
        export PASSWORD="${ACCESS_PASSWORD}"
        nohup code-server /workspace --bind-addr 0.0.0.0:8080 \
            --auth password \
            --ignore-last-opened \
            --disable-workspace-trust \
            &> /workspace/logs/code-server.log &
    else
        echo "Starting code-server without a password... (ACCESS_PASSWORD environment variable is not set.)"
        nohup code-server /workspace --bind-addr 0.0.0.0:8080 \
            --auth none \
            --ignore-last-opened \
            --disable-workspace-trust \
            &> /workspace/logs/code-server.log &
    fi

    echo "code-server started"
}

# Start preset manager
start_preset_manager() {
    # Check if preset manager should be started (default: true)
    if [[ "${ENABLE_PRESET_MANAGER,,}" == "false" ]]; then
        echo "Preset Manager is disabled (ENABLE_PRESET_MANAGER=false). Skipping startup."
        return
    fi

    echo "Starting Preset Manager..."

    # DEBUG: Set PYTHONPATH first so imports work
    echo "[DEBUG] Setting PYTHONPATH=/app"
    export PYTHONPATH="/app:$PYTHONPATH"
    echo "[DEBUG] PYTHONPATH=$PYTHONPATH"

    # DEBUG: Validate required files exist before starting
    echo "[DEBUG] Checking required files..."
    local missing_components=()

    if [[ ! -f /app/preset_manager.py ]]; then
        missing_components+=("preset_manager.py")
        echo "[DEBUG] MISSING: /app/preset_manager.py"
    else
        echo "[DEBUG] FOUND: /app/preset_manager.py"
    fi

    if [[ ! -d /app/preset_manager ]]; then
        missing_components+=("preset_manager directory")
        echo "[DEBUG] MISSING: /app/preset_manager/"
    else
        echo "[DEBUG] FOUND: /app/preset_manager/"
    fi

    if [[ ! -f /app/preset_manager/core.py ]]; then
        missing_components+=("preset_manager/core.py")
        echo "[DEBUG] MISSING: /app/preset_manager/core.py"
    else
        echo "[DEBUG] FOUND: /app/preset_manager/core.py"
    fi

    if [[ ! -f /app/preset_manager/web_interface.py ]]; then
        missing_components+=("preset_manager/web_interface.py")
        echo "[DEBUG] MISSING: /app/preset_manager/web_interface.py"
    else
        echo "[DEBUG] FOUND: /app/preset_manager/web_interface.py"
    fi

    if [[ ${#missing_components[@]} -gt 0 ]]; then
        echo "WARNING: Preset Manager cannot start - missing components:"
        printf '  - %s\n' "${missing_components[@]}"
        echo "Your Docker image may be outdated. Please rebuild or pull the latest version."
        echo "Visit https://github.com/zeroclue/comfyui-docker for instructions."
        return 1
    fi

    # DEBUG: Validate Python imports before starting
    echo "[DEBUG] Testing Python import..."
    if ! /venv/bin/python3 -c "from preset_manager.core import ModelManager; print('[DEBUG] Import successful')" 2>&1; then
        echo "WARNING: Cannot import ModelManager. Python dependencies may be missing."
        echo "Preset Manager will not start. Please check your Docker image."
        return 1
    fi

    echo "[DEBUG] Creating directories..."
    mkdir -p /workspace/logs
    mkdir -p /workspace/docs/presets

    # Copy templates to the expected location
    echo "[DEBUG] Copying templates..."
    if [[ -d /scripts/templates ]]; then
        mkdir -p /app/templates
        cp -r /scripts/templates/* /app/templates/
        echo "[DEBUG] Templates copied from /scripts/templates"
    else
        echo "[DEBUG] /scripts/templates not found, skipping"
    fi

    # Create static directory
    mkdir -p /app/static

    # Start the preset manager Flask application
    echo "[DEBUG] Starting Flask app..."
    cd /app

    nohup /venv/bin/python3 preset_manager.py &> /workspace/logs/preset_manager.log &
    local pid=$!
    echo "[DEBUG] Flask app started with PID $pid"

    # Verify process started successfully
    echo "[DEBUG] Waiting for process to start..."
    local max_wait=10
    local waited=0
    while [[ $waited -lt $max_wait ]]; do
        if [[ -S /tmp/flask_sessions/* ]] || pgrep -f "python3 preset_manager.py" > /dev/null; then
            echo "[DEBUG] Process found after ${waited}s"
            break
        fi
        sleep 1
        ((waited++))
    done

    # Verify port 8000 is listening (Flask app port)
    echo "[DEBUG] Waiting for port 8000..."
    local max_wait=15
    local waited=0
    while [[ $waited -lt $max_wait ]]; do
        if netstat -tuln 2>/dev/null | grep -q ':8000' || ss -tuln 2>/dev/null | grep -q ':8000'; then
            echo "[DEBUG] Port 8000 is listening"
            break
        fi
        sleep 1
        ((waited++))
    done

    if [[ $waited -ge $max_wait ]]; then
        echo "WARNING: Preset Manager process started but port 8000 is not listening after ${max_wait}s."
        echo "Check logs at /workspace/logs/preset_manager.log for errors."
        echo "[DEBUG] Last 10 lines of preset_manager.log:"
        tail -10 /workspace/logs/preset_manager.log 2>/dev/null || echo "[DEBUG] Log file not found"
        return 1
    fi

    echo "Preset Manager started on port 8000 (accessible via Nginx on port 9000)"
}

# Start preset downloads in background
start_preset_downloads() {
    echo "Checking for preset downloads..."

    # Check if any preset downloads are requested
    local has_presets=false
    if [[ -n "${PRESET_DOWNLOAD}" ]] || [[ -n "${IMAGE_PRESET_DOWNLOAD}" ]] || [[ -n "${AUDIO_PRESET_DOWNLOAD}" ]] || [[ -n "${UNIFIED_PRESET_DOWNLOAD}" ]]; then
        has_presets=true
    fi

    if [[ "$has_presets" == "false" ]]; then
        echo "No preset downloads requested (set PRESET_DOWNLOAD, IMAGE_PRESET_DOWNLOAD, AUDIO_PRESET_DOWNLOAD, or UNIFIED_PRESET_DOWNLOAD)"
        return
    fi

    # Check if unified downloader exists
    if [[ ! -f "/scripts/unified_preset_downloader.py" ]]; then
        echo "WARNING: unified_preset_downloader.py not found, skipping preset downloads"
        return 1
    fi

    echo "Starting preset downloads in background..."
    mkdir -p /workspace/logs

    # Show what will be downloaded
    python3 /scripts/unified_preset_downloader.py status

    # Start preset downloader in background mode with progress tracking
    nohup python3 /scripts/unified_preset_downloader.py download --background --quiet &> /workspace/logs/preset_downloads.log &
    local pid=$!
    echo "Preset downloader started with PID $pid"

    # Save PID for monitoring
    echo $pid > /tmp/preset_downloader.pid

    echo "Preset downloads running in background"
    echo "Check progress:"
    echo "  - Tail logs:    tail -f /workspace/logs/preset_downloads.log"
    echo "  - Watch mode:   python3 /scripts/unified_preset_downloader.py progress --watch"
    echo "  - JSON status:  cat /tmp/preset_download_progress.json"
}

# Check preset manager health
check_preset_manager_health() {
    echo "Checking Preset Manager health..."

    local health_issues=()

    # Check if preset manager process is running
    if ! pgrep -f "python3 preset_manager.py" > /dev/null; then
        health_issues+=("Preset Manager process is not running")
    fi

    # Check if port 8000 is listening (Flask app port)
    if ! netstat -tuln 2>/dev/null | grep -q ':8000' && ! ss -tuln 2>/dev/null | grep -q ':8000'; then
        health_issues+=("Port 8000 is not listening (Preset Manager Flask app)")
    fi

    # Check if Nginx proxy (port 9000) is accessible
    if ! curl -s -f http://localhost:9000 > /dev/null 2>&1; then
        health_issues+=("Nginx proxy on port 9000 is not accessible")
    fi

    if [[ ${#health_issues[@]} -gt 0 ]]; then
        echo "WARNING: Preset Manager health check failed:"
        printf '  - %s\n' "${health_issues[@]}"
        echo "You can still use the container, but the Preset Manager web interface may not work."
        echo "Check logs at /workspace/logs/preset_manager.log for details."
        return 1
    else
        echo "Preset Manager health check passed."
        return 0
    fi
}

# Start ComfyUI Studio
start_comfyui_studio() {
    # Check if studio should be started (default: true)
    if [[ "${ENABLE_STUDIO,,}" == "false" ]]; then
        echo "ComfyUI Studio is disabled (ENABLE_STUDIO=false). Skipping startup."
        return
    fi

    echo "Starting ComfyUI Studio..."

    # Check if studio script exists
    if [[ ! -f /scripts/comfyui_studio.py ]]; then
        echo "WARNING: /scripts/comfyui_studio.py not found, skipping startup"
        return 1
    fi

    mkdir -p /workspace/logs
    mkdir -p /workspace/config/workflows

    # Set environment variables for studio
    export WORKSPACE_ROOT="/workspace"
    export STUDIO_PORT="${STUDIO_PORT:-5000}"

    # Start the studio Flask application
    cd /scripts
    nohup /venv/bin/python3 comfyui_studio.py &> /workspace/logs/comfyui_studio.log &
    local pid=$!
    echo "ComfyUI Studio started with PID $pid on port ${STUDIO_PORT}"

    # Wait briefly and verify
    sleep 2
    if ! pgrep -f "python3 comfyui_studio.py" > /dev/null; then
        echo "WARNING: ComfyUI Studio process not running after startup"
        echo "Check logs at /workspace/logs/comfyui_studio.log"
        return 1
    fi

    echo "ComfyUI Studio started successfully"
}

# Start unified dashboard
start_unified_dashboard() {
    # Check if dashboard should be started (default: true)
    if [[ "${ENABLE_UNIFIED_DASHBOARD,,}" == "false" ]]; then
        echo "Unified Dashboard is disabled (ENABLE_UNIFIED_DASHBOARD=false). Skipping startup."
        return
    fi

    echo "Starting Unified Dashboard..."

    # Check if dashboard app exists
    if [[ ! -f /app/dashboard/main.py ]]; then
        echo "WARNING: /app/dashboard/main.py not found, skipping startup"
        echo "Your Docker image may not include the unified dashboard. Please rebuild."
        return 1
    fi

    mkdir -p /workspace/logs

    # Set environment variables for dashboard
    export DASHBOARD_PORT="${DASHBOARD_PORT:-8000}"
    export DASHBOARD_HOST="0.0.0.0"
    export DASHBOARD_SECRET_KEY="${DASHBOARD_SECRET_KEY:-$(python3 -c 'import secrets; print(secrets.token_hex(32))')}"

    # Use ACCESS_PASSWORD for dashboard if set, otherwise no auth
    if [[ -n "${ACCESS_PASSWORD}" ]]; then
        export ACCESS_PASSWORD="${ACCESS_PASSWORD}"
    fi

    # Start the dashboard FastAPI application
    cd /app/dashboard
    # Add /scripts to PYTHONPATH for generate_download_scripts import
    export PYTHONPATH="/scripts:/app:$PYTHONPATH"
    # Run as module to handle relative imports
    cd /app/dashboard
    nohup /venv/bin/python3 -m main &> /workspace/logs/unified_dashboard.log &
    local pid=$!
    echo "Unified Dashboard started with PID $pid on port ${DASHBOARD_PORT}"

    # Verify process started successfully
    sleep 2
    if ! pgrep -f "python.*-m.*main" > /dev/null; then
        echo "WARNING: Unified Dashboard process not running after startup"
        echo "Check logs at /workspace/logs/unified_dashboard.log"
        return 1
    fi

    echo "Unified Dashboard started successfully"
}

# Install extra custom nodes at runtime if requested
install_extra_nodes() {
    # Check if extra nodes should be installed (default: false)
    if [[ "${INSTALL_EXTRA_NODES,,}" != "true" ]]; then
        return
    fi

    echo "==== Installing Extra Custom Nodes ===="

    if [[ ! -f /custom_nodes_extra.txt ]]; then
        echo "WARNING: /custom_nodes_extra.txt not found, skipping extra nodes installation"
        return 1
    fi

    local custom_nodes_dir="/workspace/ComfyUI/custom_nodes"

    if [[ ! -d "$custom_nodes_dir" ]]; then
        echo "WARNING: Custom nodes directory not found at $custom_nodes_dir"
        return 1
    fi

    cd "$custom_nodes_dir"

    while IFS= read -r url; do
        # Skip empty lines and comments
        [[ -z "$url" || "$url" =~ ^[[:space:]]*# ]] && continue

        local node_name=$(basename "$url" .git)

        if [[ -d "$node_name" ]]; then
            echo "  $node_name already installed, skipping..."
            continue
        fi

        echo "  Cloning $node_name..."
        if git clone --recursive "$url" "$node_name" 2>&1; then
            echo "  ✅ $node_name cloned successfully"
        else
            echo "  ❌ Failed to clone $node_name"
        fi
    done < /custom_nodes_extra.txt

    # Install requirements for extra nodes
    echo "  Installing requirements for extra nodes..."
    find "$custom_nodes_dir" -maxdepth 2 -name "requirements.txt" -exec pip install --no-cache-dir -r {} \; 2>/dev/null || true

    # Run install scripts
    echo "  Running install scripts for extra nodes..."
    find "$custom_nodes_dir" -maxdepth 2 -name "install.py" -exec python {} \; 2>/dev/null || true

    echo "✅ Extra custom nodes installation complete"
}

# ---------------------------------------------------------------------------- #
#                               Main Program                                   #
# ---------------------------------------------------------------------------- #

start_nginx

# Revolutionary Architecture: No sync monitor needed (no rsync!)
# Background preset downloads for instant startup

execute_script "/pre_start.sh" "Running pre-start script..."

# Install extra custom nodes if requested
install_extra_nodes

echo "=================================================="
echo "  ComfyUI-Docker Revolutionary Architecture"
echo "  No rsync - instant startup!"
echo "=================================================="

setup_ssh

# Start preset downloads in background (non-blocking)
start_preset_downloads

start_jupyter
start_code_server

# Start Unified Dashboard (replaces Preset Manager and Studio)
# If Unified Dashboard is enabled, skip Preset Manager and Studio
if [[ "${ENABLE_UNIFIED_DASHBOARD,,}" != "false" ]]; then
    # Start Unified Dashboard (don't exit on failure)
    if ! start_unified_dashboard; then
        echo "[WARN] Unified Dashboard failed to start - check logs"
    fi
else
    # Start preset manager (don't exit on failure)
    if ! start_preset_manager; then
        echo "[WARN] Preset Manager failed to start - check logs"
    fi

    # Start ComfyUI Studio (don't exit on failure)
    if ! start_comfyui_studio; then
        echo "[WARN] ComfyUI Studio failed to start - check logs"
    fi
fi

export_env_vars

execute_script "/post_start.sh" "Running post-start script..."

echo ""
echo "=================================================="
echo "  ComfyUI-Docker is ready!"
echo "=================================================="
echo ""
echo "  Services:"
echo "    - Unified Dashboard: http://localhost:8082 (NEW!)"
echo "    - ComfyUI:          http://localhost:3000"
echo "    - Code Server:      http://localhost:8080"
echo "    - JupyterLab:       http://localhost:8888"
echo "    - Preset Manager:   http://localhost:9000"
echo "    - Studio:           http://localhost:5000"
echo ""
echo "  Architecture:"
echo "    - App code:   /app (container volume)"
echo "    - Models:     /workspace/models (network volume)"
echo "    - No rsync needed!"
echo ""
echo "  Preset downloads running in background."
echo "  Check: tail -f /workspace/logs/preset_downloads.log"
echo "=================================================="

sleep infinity
