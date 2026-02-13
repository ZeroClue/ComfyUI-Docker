#!/bin/bash
set -e  # Exit the script if any statement returns a non-true return value

# Ensure venv Python is first in PATH (UV may have added /root/.local/bin first)
export PATH="/workspace/venv/bin:$PATH"

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
    if ! /workspace/venv/bin/python3 -c "from preset_manager.core import ModelManager; print('[DEBUG] Import successful')" 2>&1; then
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

    nohup /workspace/venv/bin/python3 preset_manager.py &> /workspace/logs/preset_manager.log &
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

# ---------------------------------------------------------------------------- #
#                               Main Program                                   #
# ---------------------------------------------------------------------------- #

start_nginx

# Start sync monitor in background for real-time progress tracking
if [ -f "/scripts/sync_monitor.sh" ]; then
    echo "Starting sync progress monitor..."
    nohup /scripts/sync_monitor.sh > /dev/null 2>&1 &
    echo "Sync monitor started - check /workspace/logs/sync_monitor.log for detailed progress"
fi

execute_script "/pre_start.sh" "Running pre-start script..."

echo "Pod Started - Optimizations applied"

setup_ssh
start_jupyter
start_code_server

# Start preset manager in background (don't block container startup)
(
    if ! start_preset_manager; then
        echo "[DEBUG] Preset Manager failed - dumping logs..."
        echo "[DEBUG] === preset_manager.log ==="
        cat /workspace/logs/preset_manager.log 2>/dev/null || echo "[DEBUG] Log file not found"
        echo "[DEBUG] === end of log ==="
    fi
) &

# Run health check if preset manager was started
if [[ "${ENABLE_PRESET_MANAGER,,}" != "false" ]]; then
    # Wait for preset manager to fully initialize with retries
    local max_retries=5
    local retry_delay=3
    local retry_count=0

    while [[ $retry_count -lt $max_retries ]]; do
        if check_preset_manager_health; then
            break
        fi
        ((retry_count++))
        if [[ $retry_count -lt $max_retries ]]; then
            echo "Retrying health check in ${retry_delay}s... ($retry_count/$max_retries)"
            sleep $retry_delay
        fi
    done

    if [[ $retry_count -ge $max_retries ]]; then
        echo "NOTE: Preset Manager health check failed after $max_retries attempts, but continuing startup."
        echo "Preset Manager may not be fully functional. Check logs at /workspace/logs/preset_manager.log"
    fi
fi

export_env_vars

execute_script "/post_start.sh" "Running post-start script..."

echo "Start script(s) finished, pod is ready to use."

sleep infinity
