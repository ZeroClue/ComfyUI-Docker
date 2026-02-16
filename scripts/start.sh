#!/bin/bash
set -e

# =============================================================================
# Revolutionary ComfyUI-Docker Startup Orchestration
# =============================================================================
#
# This script implements a 4-phase startup flow designed for speed and reliability:
#
# Phase 1: Volume & Config Setup (<8 seconds)
#   - Generate extra_model_paths.yaml
#   - Create /workspace directory structure
#   - Verify workspace mount accessibility
#
# Phase 2: Service Startup (<15 seconds)
#   - Start Nginx (if configured)
#   - Start SSH (if PUBLIC_KEY provided)
#   - Start ComfyUI in background with proper logging
#   - Wait for ComfyUI to be ready (health check)
#
# Phase 3: Dashboard Startup (<5 seconds)
#   - Start Dashboard (FastAPI) in background
#   - Start preset downloads in background if PRESET_DOWNLOAD set
#
# Phase 4: Health Verification (<2 seconds)
#   - Run health checks
#   - Report ready state
#
# Target: <30 seconds total startup time
#
# Architecture:
#   - App code at /app/ (pre-built in image, immutable)
#   - Models on /workspace (network volume)
#   - No rsync - eliminated for performance
#
# =============================================================================

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# Phase timing targets (seconds)
PHASE_1_TARGET=8
PHASE_2_TARGET=15
PHASE_3_TARGET=5
PHASE_4_TARGET=2
TOTAL_TARGET=30

# Paths
APP_DIR="/app"
COMFYUI_DIR="${APP_DIR}/comfyui"
VENV_DIR="${APP_DIR}/venv"
WORKSPACE_ROOT="/workspace"
COMFYUI_WORKSPACE="${WORKSPACE_ROOT}/ComfyUI"
MODELS_BASE="${WORKSPACE_ROOT}/models"
LOGS_DIR="${WORKSPACE_ROOT}/logs"
CONFIG_DIR="${WORKSPACE_ROOT}/config"

# Service ports
COMFYUI_PORT=3000
DASHBOARD_PORT=8080
PRESET_MANAGER_PORT=9000
JUPYTER_PORT=8888
CODE_SERVER_PORT=8080

# Health check endpoints
COMFYUI_HEALTH_URL="http://localhost:${COMFYUI_PORT}/system_stats"

# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------

# Get current timestamp in milliseconds
get_time_ms() {
    date +%s%3N
}

# Format duration in seconds
format_duration() {
    local ms=$1
    local seconds=$((ms / 1000))
    local milliseconds=$((ms % 1000))
    printf "${seconds}.${milliseconds}s"
}

# Color output
color_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

color_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

color_warning() {
    echo -e "\033[0;33m[WARNING]\033[0m $1"
}

color_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

color_phase() {
    echo -e "\033[1;36m[PHASE]\033[0m $1"
}

# Logging with timestamps
log_info() {
    color_info "$1"
}

log_success() {
    color_success "$1"
}

log_warning() {
    color_warning "$1"
}

log_error() {
    color_error "$1"
}

# -----------------------------------------------------------------------------
# Phase 1: Volume & Config Setup (Target: <8 seconds)
# -----------------------------------------------------------------------------

phase1_volume_setup() {
    local start_time=$(get_time_ms)

    color_phase "Phase 1: Volume & Config Setup"
    log_info "Starting volume and configuration setup..."

    # Create log directory
    mkdir -p "${LOGS_DIR}"

    # Verify workspace mount is accessible
    if [[ ! -d "${WORKSPACE_ROOT}" ]]; then
        log_error "Workspace root not found: ${WORKSPACE_ROOT}"
        return 1
    fi

    if [[ ! -w "${WORKSPACE_ROOT}" ]]; then
        log_error "Workspace not writable: ${WORKSPACE_ROOT}"
        return 1
    fi

    log_success "Workspace mount verified: ${WORKSPACE_ROOT}"

    # Generate extra_model_paths.yaml
    log_info "Generating extra_model_paths.yaml..."

    if [[ -f "${APP_DIR}/scripts/generate_extra_paths.py" ]]; then
        python3 "${APP_DIR}/scripts/generate_extra_paths.py" \
            --output "${COMFYUI_DIR}/extra_model_paths.yaml" \
            --base-path "${MODELS_BASE}" \
            --create-dirs \
            >> "${LOGS_DIR}/setup.log" 2>&1

        if [[ $? -eq 0 ]]; then
            log_success "extra_model_paths.yaml generated successfully"
        else
            log_error "Failed to generate extra_model_paths.yaml"
            return 1
        fi
    else
        log_warning "generate_extra_paths.py not found, skipping config generation"
    fi

    # Create directory structure
    log_info "Creating workspace directory structure..."

    mkdir -p "${COMFYUI_WORKSPACE}"
    mkdir -p "${MODELS_BASE}/checkpoints"
    mkdir -p "${MODELS_BASE}/text_encoders"
    mkdir -p "${MODELS_BASE}/vae"
    mkdir -p "${MODELS_BASE}/clip_vision"
    mkdir -p "${MODELS_BASE}/loras"
    mkdir -p "${MODELS_BASE}/audio_encoders"
    mkdir -p "${MODELS_BASE}/upscale_models"
    mkdir -p "${MODELS_BASE}/controlnet"
    mkdir -p "${MODELS_BASE}/embeddings"
    mkdir -p "${COMFYUI_WORKSPACE}/output"
    mkdir -p "${COMFYUI_WORKSPACE}/input"
    mkdir -p "${COMFYUI_WORKSPACE}/temp"
    mkdir -p "${CONFIG_DIR}"

    log_success "Directory structure created"

    # Create symlinks for ComfyUI models to workspace
    if [[ -d "${COMFYUI_DIR}/models" && ! -L "${COMFYUI_DIR}/models" ]]; then
        log_info "Setting up model symlinks..."
        rm -rf "${COMFYUI_DIR}/models"
        ln -sf "${MODELS_BASE}" "${COMFYUI_DIR}/models"
        log_success "Model symlink created"
    fi

    # Link output directories
    mkdir -p "${COMFYUI_WORKSPACE}/output"
    if [[ ! -L "${COMFYUI_DIR}/output" ]]; then
        ln -sf "${COMFYUI_WORKSPACE}/output" "${COMFYUI_DIR}/output"
    fi

    if [[ ! -L "${COMFYUI_DIR}/input" ]]; then
        ln -sf "${COMFYUI_WORKSPACE}/input" "${COMFYUI_DIR}/input"
    fi

    local end_time=$(get_time_ms)
    local duration=$((end_time - start_time))

    if [[ $duration -le $((PHASE_1_TARGET * 1000)) ]]; then
        log_success "Phase 1 completed in $(format_duration ${duration}) (target: ${PHASE_1_TARGET}s)"
    else
        log_warning "Phase 1 completed in $(format_duration ${duration}) (exceeded target of ${PHASE_1_TARGET}s)"
    fi

    return 0
}

# -----------------------------------------------------------------------------
# Phase 2: Service Startup (Target: <15 seconds)
# -----------------------------------------------------------------------------

start_nginx() {
    log_info "Starting Nginx service..."

    if command -v nginx &> /dev/null; then
        nginx -t >> "${LOGS_DIR}/nginx.log" 2>&1
        if [[ $? -eq 0 ]]; then
            service nginx start >> "${LOGS_DIR}/nginx.log" 2>&1
            log_success "Nginx started"
        else
            log_warning "Nginx configuration test failed, skipping startup"
        fi
    else
        log_warning "Nginx not found, skipping startup"
    fi
}

start_ssh() {
    if [[ -n "${PUBLIC_KEY}" ]]; then
        log_info "Setting up SSH..."

        mkdir -p ~/.ssh
        echo "${PUBLIC_KEY}" >> ~/.ssh/authorized_keys
        chmod 700 -R ~/.ssh

        # Generate host keys if they don't exist
        if [[ ! -f /etc/ssh/ssh_host_rsa_key ]]; then
            ssh-keygen -t rsa -f /etc/ssh/ssh_host_rsa_key -q -N '' 2>/dev/null
        fi
        if [[ ! -f /etc/ssh/ssh_host_ed25519_key ]]; then
            ssh-keygen -t ed25519 -f /etc/ssh/ssh_host_ed25519_key -q -N '' 2>/dev/null
        fi

        service ssh start >> "${LOGS_DIR}/ssh.log" 2>&1
        log_success "SSH started"
    fi
}

wait_for_comfyui() {
    local max_wait=30
    local waited=0
    local check_interval=1

    log_info "Waiting for ComfyUI to be ready..."

    while [[ $waited -lt $max_wait ]]; do
        if curl -s -f "${COMFYUI_HEALTH_URL}" > /dev/null 2>&1; then
            log_success "ComfyUI is ready after ${waited}s"
            return 0
        fi

        # Check if process is running
        if pgrep -f "python.*main.py" > /dev/null; then
            # Process is running, wait a bit more
            sleep $check_interval
            ((waited += check_interval))
        else
            log_error "ComfyUI process not running"
            return 1
        fi
    done

    log_warning "ComfyUI health check timeout after ${waited}s"
    return 1
}

start_comfyui() {
    log_info "Starting ComfyUI..."

    cd "${COMFYUI_DIR}"

    # Set Python path
    export PYTHONPATH="${APP_DIR}:${PYTHONPATH}"

    # Start ComfyUI in background
    nohup python3 main.py \
        --listen 0.0.0.0 \
        --port ${COMFYUI_PORT} \
        --output-directory "${COMFYUI_WORKSPACE}/output" \
        --input-directory "${COMFYUI_WORKSPACE}/input" \
        --temp-directory "${COMFYUI_WORKSPACE}/temp" \
        --verbose \
        >> "${LOGS_DIR}/comfyui.log" 2>&1 &

    local pid=$!
    echo $pid > "${LOGS_DIR}/comfyui.pid"

    log_success "ComfyUI started with PID ${pid}"

    # Wait for ComfyUI to be ready
    wait_for_comfyui
    return $?
}

phase2_service_startup() {
    local start_time=$(get_time_ms)

    color_phase "Phase 2: Service Startup"
    log_info "Starting core services..."

    # Start Nginx
    start_nginx

    # Start SSH
    start_ssh

    # Start ComfyUI
    start_comfyui
    if [[ $? -ne 0 ]]; then
        log_error "Failed to start ComfyUI"
        return 1
    fi

    local end_time=$(get_time_ms)
    local duration=$((end_time - start_time))

    if [[ $duration -le $((PHASE_2_TARGET * 1000)) ]]; then
        log_success "Phase 2 completed in $(format_duration ${duration}) (target: ${PHASE_2_TARGET}s)"
    else
        log_warning "Phase 2 completed in $(format_duration ${duration}) (exceeded target of ${PHASE_2_TARGET}s)"
    fi

    return 0
}

# -----------------------------------------------------------------------------
# Phase 3: Dashboard Startup (Target: <5 seconds)
# -----------------------------------------------------------------------------

start_preset_manager() {
    if [[ "${ENABLE_PRESET_MANAGER,,}" == "false" ]]; then
        log_info "Preset Manager disabled (ENABLE_PRESET_MANAGER=false)"
        return 0
    fi

    log_info "Starting Preset Manager..."

    # Set Python path
    export PYTHONPATH="${APP_DIR}:${PYTHONPATH}"

    cd "${APP_DIR}"

    # Start preset manager in background
    nohup python3 preset_manager.py \
        >> "${LOGS_DIR}/preset_manager.log" 2>&1 &

    local pid=$!
    echo $pid > "${LOGS_DIR}/preset_manager.pid"

    log_success "Preset Manager started with PID ${pid}"

    return 0
}

start_background_preset_downloads() {
    if [[ -z "${PRESET_DOWNLOAD}" && -z "${IMAGE_PRESET_DOWNLOAD}" && -z "${AUDIO_PRESET_DOWNLOAD}" ]]; then
        log_info "No preset downloads configured"
        return 0
    fi

    log_info "Starting background preset downloads..."

    # Set Python path
    export PYTHONPATH="${APP_DIR}:${PYTHONPATH}"

    cd "${APP_DIR}/scripts"

    # Create status file directory
    mkdir -p "$(dirname "${LOGS_DIR}/preset_download_status.json")"

    # Start unified preset downloader in background with status tracking
    nohup python3 unified_preset_downloader.py download \
        --background \
        --status-file "${LOGS_DIR}/preset_download_status.json" \
        --env-only \
        >> "${LOGS_DIR}/preset_downloads.log" 2>&1 &

    local pid=$!
    echo $pid > "${LOGS_DIR}/preset_downloads.pid"

    log_success "Background preset downloads started with PID ${pid}"
    log_info "Download logs: ${LOGS_DIR}/preset_downloads.log"
    log_info "Status file: ${LOGS_DIR}/preset_download_status.json"

    # Display which presets will be downloaded
    log_info "Configured presets:"
    if [[ -n "${PRESET_DOWNLOAD}" ]]; then
        log_info "  Video (PRESET_DOWNLOAD): ${PRESET_DOWNLOAD}"
    fi
    if [[ -n "${IMAGE_PRESET_DOWNLOAD}" ]]; then
        log_info "  Image (IMAGE_PRESET_DOWNLOAD): ${IMAGE_PRESET_DOWNLOAD}"
    fi
    if [[ -n "${AUDIO_PRESET_DOWNLOAD}" ]]; then
        log_info "  Audio (AUDIO_PRESET_DOWNLOAD): ${AUDIO_PRESET_DOWNLOAD}"
    fi

    return 0
}

start_code_server() {
    if [[ "${ENABLE_CODE_SERVER,,}" == "false" ]]; then
        log_info "Code-server disabled (ENABLE_CODE_SERVER=false)"
        return 0
    fi

    if ! command -v code-server &> /dev/null; then
        log_info "Code-server not installed, skipping"
        return 0
    fi

    log_info "Starting code-server..."

    mkdir -p "${LOGS_DIR}"

    cd "${WORKSPACE_ROOT}"

    if [[ -n "${ACCESS_PASSWORD}" ]]; then
        export PASSWORD="${ACCESS_PASSWORD}"
        nohup code-server "${WORKSPACE_ROOT}" \
            --bind-addr 0.0.0.0:${CODE_SERVER_PORT} \
            --auth password \
            --ignore-last-opened \
            --disable-workspace-trust \
            >> "${LOGS_DIR}/code-server.log" 2>&1 &
    else
        nohup code-server "${WORKSPACE_ROOT}" \
            --bind-addr 0.0.0.0:${CODE_SERVER_PORT} \
            --auth none \
            --ignore-last-opened \
            --disable-workspace-trust \
            >> "${LOGS_DIR}/code-server.log" 2>&1 &
    fi

    local pid=$!
    echo $pid > "${LOGS_DIR}/code-server.pid"

    log_success "Code-server started with PID ${pid}"

    return 0
}

start_jupyter() {
    if [[ "${ENABLE_JUPYTERLAB,,}" == "false" ]]; then
        log_info "JupyterLab disabled (ENABLE_JUPYTERLAB=false)"
        return 0
    fi

    if ! command -v jupyter &> /dev/null; then
        log_info "JupyterLab not installed, skipping"
        return 0
    fi

    log_info "Starting JupyterLab..."

    mkdir -p "${LOGS_DIR}"

    cd /

    local jupyter_password=""
    if [[ -n "${ACCESS_PASSWORD}" ]]; then
        jupyter_password="${ACCESS_PASSWORD}"
    fi

    nohup jupyter lab --allow-root \
        --no-browser \
        --port=${JUPYTER_PORT} \
        --ip=* \
        --FileContentsManager.delete_to_trash=False \
        --ContentsManager.allow_hidden=True \
        --ServerApp.terminado_settings='{"shell_command":["/bin/bash"]}' \
        --ServerApp.token="${jupyter_password}" \
        --ServerApp.allow_origin=* \
        --ServerApp.preferred_dir="${WORKSPACE_ROOT}" \
        >> "${LOGS_DIR}/jupyterlab.log" 2>&1 &

    local pid=$!
    echo $pid > "${LOGS_DIR}/jupyterlab.pid"

    log_success "JupyterLab started with PID ${pid}"

    return 0
}

# Start unified dashboard
start_unified_dashboard() {
    if [[ "${ENABLE_UNIFIED_DASHBOARD,,}" == "false" ]]; then
        log_info "Unified Dashboard disabled (ENABLE_UNIFIED_DASHBOARD=false)"
        return 0
    fi

    if ! command -v python3 &> /dev/null; then
        log_warning "Python3 not found, skipping dashboard startup"
        return 1
    fi

    log_info "Starting Unified Dashboard..."

    # Check if dashboard app exists
    if [[ ! -f /app/dashboard/app.py ]]; then
        log_warning "/app/dashboard/app.py not found, skipping startup"
        log_info "Your Docker image may not include the unified dashboard. Please rebuild."
        return 1
    fi

    mkdir -p "${LOGS_DIR}"

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
    nohup /venv/bin/python3 app.py &> "${LOGS_DIR}/unified_dashboard.log" &
    local pid=$!
    echo $pid > "${LOGS_DIR}/unified_dashboard.pid"

    log_success "Unified Dashboard started with PID ${pid} on port ${DASHBOARD_PORT}"

    # Verify process started successfully
    sleep 2
    if ! pgrep -f "python3 app.py" > /dev/null; then
        log_warning "Unified Dashboard process not running after startup"
        log_info "Check logs at ${LOGS_DIR}/unified_dashboard.log"
        return 1
    fi

    return 0
}

phase3_dashboard_startup() {
    local start_time=$(get_time_ms)

    color_phase "Phase 3: Dashboard Startup"
    log_info "Starting dashboard services..."

    # Start preset manager
    start_preset_manager

    # Start background preset downloads
    start_background_preset_downloads

    # Start code-server
    start_code_server

    # Start Jupyter
    start_jupyter

    # Start unified dashboard
    start_unified_dashboard

    local end_time=$(get_time_ms)
    local duration=$((end_time - start_time))

    if [[ $duration -le $((PHASE_3_TARGET * 1000)) ]]; then
        log_success "Phase 3 completed in $(format_duration ${duration}) (target: ${PHASE_3_TARGET}s)"
    else
        log_warning "Phase 3 completed in $(format_duration ${duration}) (exceeded target of ${PHASE_3_TARGET}s)"
    fi

    return 0
}

# -----------------------------------------------------------------------------
# Phase 4: Health Verification (Target: <2 seconds)
# -----------------------------------------------------------------------------

run_health_checks() {
    log_info "Running health checks..."

    local health_passed=true

    # Check workspace
    if [[ ! -d "${WORKSPACE_ROOT}" ]]; then
        log_error "Workspace health check failed: directory not found"
        health_passed=false
    fi

    # Check ComfyUI
    if ! curl -s -f "${COMFYUI_HEALTH_URL}" > /dev/null 2>&1; then
        log_warning "ComfyUI health check: not responding"
        health_passed=false
    else
        log_success "ComfyUI health check: passed"
    fi

    # Check Nginx
    if pgrep nginx > /dev/null; then
        log_success "Nginx health check: passed"
    else
        log_warning "Nginx health check: not running"
    fi

    # Check preset manager
    if [[ "${ENABLE_PRESET_MANAGER,,}" != "false" ]]; then
        if pgrep -f "preset_manager.py" > /dev/null; then
            log_success "Preset Manager health check: passed"
        else
            log_warning "Preset Manager health check: not running"
        fi
    fi

    return $([[ "$health_passed" == "true" ]] && echo 0 || echo 1)
}

phase4_health_verification() {
    local start_time=$(get_time_ms)

    color_phase "Phase 4: Health Verification"

    run_health_checks

    local end_time=$(get_time_ms)
    local duration=$((end_time - start_time))

    if [[ $duration -le $((PHASE_4_TARGET * 1000)) ]]; then
        log_success "Phase 4 completed in $(format_duration ${duration}) (target: ${PHASE_4_TARGET}s)"
    else
        log_warning "Phase 4 completed in $(format_duration ${duration}) (exceeded target of ${PHASE_4_TARGET}s)"
    fi

    return 0
}

# -----------------------------------------------------------------------------
# Graceful Shutdown
# -----------------------------------------------------------------------------

cleanup() {
    log_info "Received shutdown signal, cleaning up..."

    # Stop all tracked services
    for pid_file in "${LOGS_DIR}"/*.pid; do
        if [[ -f "$pid_file" ]]; then
            local pid=$(cat "$pid_file")
            if kill -0 "$pid" 2>/dev/null; then
                log_info "Stopping service with PID ${pid}..."
                kill -TERM "$pid" 2>/dev/null || true
                # Wait up to 10 seconds for graceful shutdown
                local count=0
                while kill -0 "$pid" 2>/dev/null && [[ $count -lt 10 ]]; do
                    sleep 1
                    ((count++))
                done
                # Force kill if still running
                if kill -0 "$pid" 2>/dev/null; then
                    kill -KILL "$pid" 2>/dev/null || true
                fi
            fi
            rm -f "$pid_file"
        fi
    done

    log_info "Shutdown complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# -----------------------------------------------------------------------------
# Main Execution
# -----------------------------------------------------------------------------

main() {
    local total_start_time=$(get_time_ms)

    echo "=========================================="
    echo "ComfyUI-Docker Startup Orchestration"
    echo "=========================================="
    echo "Target: ${TOTAL_TARGET}s total startup time"
    echo ""

    # Run startup phases
    phase1_volume_setup || exit 1
    phase2_service_startup || exit 1
    phase3_dashboard_startup || exit 1
    phase4_health_verification

    local total_end_time=$(get_time_ms)
    local total_duration=$((total_end_time - total_start_time))

    echo ""
    echo "=========================================="
    color_success "Startup Complete!"
    echo "=========================================="
    echo "Total time: $(format_duration ${total_duration})"
    echo "Target: ${TOTAL_TARGET}s"

    if [[ $total_duration -le $((TOTAL_TARGET * 1000)) ]]; then
        log_success "Startup within target time!"
    else
        log_warning "Startup exceeded target time"
    fi

    echo ""
    echo "Services:"
    echo "  ComfyUI:        http://localhost:${COMFYUI_PORT}"
    echo "  Nginx Proxy:    http://localhost:${PRESET_MANAGER_PORT}"

    if [[ "${ENABLE_CODE_SERVER,,}" != "false" ]] && command -v code-server &> /dev/null; then
        echo "  Code Server:    http://localhost:${CODE_SERVER_PORT}"
    fi

    if [[ "${ENABLE_JUPYTERLAB,,}" != "false" ]] && command -v jupyter &> /dev/null; then
        echo "  JupyterLab:     http://localhost:${JUPYTER_PORT}"
    fi

    if [[ "${ENABLE_PRESET_MANAGER,,}" != "false" ]]; then
        echo "  Preset Manager: http://localhost:${PRESET_MANAGER_PORT}"
    fi

    echo ""
    echo "Logs: ${LOGS_DIR}"
    echo "=========================================="

    # Run custom scripts if they exist
    if [[ -f "/post_start.sh" ]]; then
        log_info "Running post-start script..."
        bash /post_start.sh || log_warning "Post-start script failed"
    fi

    # Keep container running
    log_info "Container ready. Waiting for signals..."
    sleep infinity &
    wait $!
}

# Run main function
main "$@"
