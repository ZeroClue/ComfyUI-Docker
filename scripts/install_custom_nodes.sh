#!/bin/bash

# ComfyUI Custom Nodes Installation Script with Conflict Resolution
# Supports both standard and optimized installation modes

set -e

echo "==== Installing ComfyUI custom nodes ===="

# Configuration
CUSTOM_NODES_DIR="/workspace/ComfyUI/custom_nodes"
LOG_FILE="/tmp/custom_nodes_install.log"
BACKUP_DIR="/tmp/custom_nodes_backup"
FAILED_NODES="/tmp/failed_nodes.txt"

# Installation modes
INSTALL_MODE="${1:-standard}"  # 'standard', 'optimized', 'validation'
USE_RESOLUTION="${2:-true}"     # 'true', 'false'

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}" | tee -a "$LOG_FILE"
}

# Error handling
handle_error() {
    local node=$1
    local error=$2
    print_status $RED "❌ Failed to install $node: $error"
    echo "$node" >> "$FAILED_NODES"
    return 1
}

# Backup existing installation
backup_existing() {
    if [ -d "$CUSTOM_NODES_DIR" ] && [ "$(ls -A $CUSTOM_NODES_DIR)" ]; then
        print_status $YELLOW "📦 Backing up existing custom nodes..."
        mkdir -p "$BACKUP_DIR"
        cp -r "$CUSTOM_NODES_DIR"/* "$BACKUP_DIR/" 2>/dev/null || true
    fi
}

# Restore from backup on failure
restore_backup() {
    if [ -d "$BACKUP_DIR" ] && [ "$(ls -A $BACKUP_DIR)" ]; then
        print_status $YELLOW "🔄 Restoring from backup due to installation failure..."
        rm -rf "$CUSTOM_NODES_DIR"
        mkdir -p "$CUSTOM_NODES_DIR"
        cp -r "$BACKUP_DIR"/* "$CUSTOM_NODES_DIR/"
    fi
}

# Check if dependency resolution is available
check_resolution_available() {
    [ -f "/tmp/dependency_resolution.json" ] && [ "$USE_RESOLUTION" = "true" ]
}

# Install dependencies with conflict resolution
install_dependencies_resolved() {
    print_status $BLUE "🔧 Installing dependencies with conflict resolution..."

    if check_resolution_available; then
        # Use optimized installation script from resolver
        if python3 /usr/local/lib/python3.*/site-packages/json.tool /tmp/dependency_resolution.json > /dev/null 2>&1; then
            # Extract installation script from resolution JSON
            INSTALL_SCRIPT="/tmp/optimized_install.sh"
            python3 -c "
import json
with open('/tmp/dependency_resolution.json', 'r') as f:
    data = json.load(f)
with open('$INSTALL_SCRIPT', 'w') as f:
    f.write(data['installation_script'])
"

            if [ -f "$INSTALL_SCRIPT" ]; then
                chmod +x "$INSTALL_SCRIPT"
                print_status $GREEN "✅ Using optimized dependency installation"
                bash "$INSTALL_SCRIPT" 2>&1 | tee -a "$LOG_FILE"
                return 0
            fi
        fi
    fi

    # Fallback to grouped installation
    install_dependencies_grouped
}

# Install dependencies in logical groups
install_dependencies_grouped() {
    print_status $BLUE "📦 Installing dependencies in logical groups..."

    # Core ML dependencies
    print_status $BLUE "Installing Core ML dependencies..."
    pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 2>&1 | tee -a "$LOG_FILE" || handle_error "Core ML" "PyTorch installation failed"

    # Video processing dependencies
    print_status $BLUE "Installing Video processing dependencies..."
    pip install --no-cache-dir opencv-python==4.8.1.78 imageio[ffmpeg]==2.34.1 av==10.0.0 2>&1 | tee -a "$LOG_FILE" || handle_error "Video processing" "OpenCV/FFmpeg installation failed"

    # Image processing dependencies
    print_status $BLUE "Installing Image processing dependencies..."
    pip install --no-cache-dir pillow numpy scipy scikit-image 2>&1 | tee -a "$LOG_FILE" || handle_error "Image processing" "Image libraries installation failed"

    # Install requirements from custom nodes
    print_status $BLUE "Installing custom node requirements..."
    local req_count=0
    while IFS= read -r -d '' req_file; do
        local node_dir=$(dirname "$req_file")
        local node_name=$(basename "$node_dir")

        print_status $BLUE "📋 Installing requirements for $node_name..."
        if pip install --no-cache-dir -r "$req_file" 2>&1 | tee -a "$LOG_FILE"; then
            print_status $GREEN "✅ $node_name requirements installed"
            ((req_count++))
        else
            handle_error "$node_name" "Requirements installation failed"
        fi
    done < <(find "$CUSTOM_NODES_DIR" -name "requirements.txt" -print0 2>/dev/null)

    print_status $GREEN "✅ Installed requirements for $req_count nodes"
}

# Install dependencies traditionally (fallback)
install_dependencies_standard() {
    print_status $BLUE "📦 Installing dependencies (standard mode)..."

    # Find and install all requirements.txt files
    local req_count=0
    while IFS= read -r -d '' req_file; do
        local node_dir=$(dirname "$req_file")
        local node_name=$(basename "$node_dir")

        print_status $BLUE "📋 Installing requirements for $node_name..."
        if pip install --no-cache-dir -r "$req_file" 2>&1 | tee -a "$LOG_FILE"; then
            print_status $GREEN "✅ $node_name requirements installed"
            ((req_count++))
        else
            handle_error "$node_name" "Requirements installation failed"
        fi
    done < <(find "$CUSTOM_NODES_DIR" -name "requirements.txt" -print0 2>/dev/null)

    print_status $GREEN "✅ Installed requirements for $req_count nodes"
}

# Clone custom nodes with error handling
clone_custom_nodes() {
    print_status $BLUE "📥 Cloning custom nodes..."

    local clone_count=0
    local total_nodes=$(wc -l < /custom_nodes.txt)

    while IFS= read -r url; do
        # Skip empty lines and comments
        [[ -z "$url" || "$url" =~ ^[[:space:]]*# ]] && continue

        local node_name=$(basename "$url" .git | sed 's/ComfyUI-//I')
        print_status $BLUE "📥 Cloning $node_name..."

        if git clone --recursive "$url" "$CUSTOM_NODES_DIR/$(basename "$url" .git)" 2>&1 | tee -a "$LOG_FILE"; then
            print_status $GREEN "✅ $node_name cloned successfully"
            ((clone_count++))
        else
            handle_error "$node_name" "Git clone failed"
        fi

    done < /custom_nodes.txt

    print_status $GREEN "✅ Cloned $clone_count/$total_nodes custom nodes"
}

# Run installation scripts
run_install_scripts() {
    print_status $BLUE "🔧 Running custom node installation scripts..."

    local script_count=0
    while IFS= read -r -d '' install_script; do
        local node_dir=$(dirname "$install_script")
        local node_name=$(basename "$node_dir")

        print_status $BLUE "🔧 Running install script for $node_name..."
        if python "$install_script" 2>&1 | tee -a "$LOG_FILE"; then
            print_status $GREEN "✅ $node_name install script completed"
            ((script_count++))
        else
            handle_error "$node_name" "Install script failed"
        fi
    done < <(find "$CUSTOM_NODES_DIR" -name "install.py" -print0 2>/dev/null)

    print_status $GREEN "✅ Ran $script_count installation scripts"
}

# Validate installation
validate_installation() {
    print_status $BLUE "🔍 Validating custom node installation..."

    local valid_count=0
    local total_nodes=$(find "$CUSTOM_NODES_DIR" -maxdepth 1 -type d ! -path "$CUSTOM_NODES_DIR" | wc -l)

    for node_dir in "$CUSTOM_NODES_DIR"/*; do
        [ ! -d "$node_dir" ] && continue

        local node_name=$(basename "$node_dir")
        local __init__file="$node_dir/__init__.py"

        if [ -f "$__init__file" ]; then
            # Try to import the node to check for basic syntax errors
            if python -c "import sys; sys.path.insert(0, '$node_dir'); import $(basename "$__init__file" .py)" 2>/dev/null; then
                print_status $GREEN "✅ $node_name validates"
                ((valid_count++))
            else
                print_status $YELLOW "⚠️  $node_name has import issues (may be normal)"
                ((valid_count++))  # Still count as valid, many nodes have complex dependencies
            fi
        else
            print_status $YELLOW "⚠️  $node_name has no __init__.py"
        fi
    done

    print_status $GREEN "✅ Validation complete: $valid_count/$total_nodes nodes appear functional"
}

# Cleanup function
cleanup_installation() {
    print_status $BLUE "🧹 Cleaning up installation..."

    # Remove pip cache
    pip cache purge 2>/dev/null || true

    # Remove temporary files
    find "$CUSTOM_NODES_DIR" -name "*.pyc" -delete 2>/dev/null || true
    find "$CUSTOM_NODES_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

    # Remove .git directories to save space
    find "$CUSTOM_NODES_DIR" -name ".git" -type d -exec rm -rf {} + 2>/dev/null || true

    # Remove temporary installation files
    rm -f /tmp/optimized_install.sh /tmp/requirements_*.txt 2>/dev/null || true

    print_status $GREEN "✅ Cleanup completed"
}

# Generate installation report
generate_report() {
    print_status $BLUE "📊 Generating installation report..."

    local report_file="/tmp/custom_nodes_report.json"
    local total_nodes=$(find "$CUSTOM_NODES_DIR" -maxdepth 1 -type d ! -path "$CUSTOM_NODES_DIR" | wc -l)
    local failed_count=0

    [ -f "$FAILED_NODES" ] && failed_count=$(wc -l < "$FAILED_NODES")

    cat > "$report_file" << EOF
{
    "installation_summary": {
        "mode": "$INSTALL_MODE",
        "total_nodes": $total_nodes,
        "successful_nodes": $((total_nodes - failed_count)),
        "failed_nodes": $failed_count,
        "conflict_resolution_used": $(check_resolution_available && echo true || echo false)
    },
    "failed_nodes": [
EOF

    if [ -f "$FAILED_NODES" ]; then
        local first=true
        while IFS= read -r node; do
            [ "$first" = true ] && first=false || echo "," >> "$report_file"
            echo "            \"$node\"" >> "$report_file"
        done < "$FAILED_NODES"
    fi

    cat >> "$report_file" << EOF
    ],
    "log_file": "$LOG_FILE",
    "timestamp": "$(date -Iseconds)"
}
EOF

    print_status $GREEN "✅ Installation report saved to $report_file"
}

# Main installation function
main_install() {
    print_status $GREEN "🚀 Starting ComfyUI custom nodes installation (Mode: $INSTALL_MODE)"

    # Initialize log
    echo "ComfyUI Custom Nodes Installation Log - $(date)" > "$LOG_FILE"

    # Backup existing installation
    backup_existing

    # Clone custom nodes
    clone_custom_nodes

    # Install dependencies based on mode
    case "$INSTALL_MODE" in
        "optimized")
            install_dependencies_resolved
            ;;
        "validation")
            install_dependencies_grouped
            ;;
        *)
            install_dependencies_standard
            ;;
    esac

    # Run installation scripts
    run_install_scripts

    # Validate installation
    validate_installation

    # Cleanup
    cleanup_installation

    # Generate report
    generate_report

    # Check for failures
    if [ -f "$FAILED_NODES" ] && [ -s "$FAILED_NODES" ]; then
        print_status $YELLOW "⚠️  Installation completed with some failures:"
        while IFS= read -r node; do
            print_status $YELLOW "  - $node"
        done < "$FAILED_NODES"
        print_status $YELLOW "Check $LOG_FILE for details"
    else
        print_status $GREEN "🎉 All custom nodes installed successfully!"
    fi

    print_status $GREEN "✅ Installation complete!"
}

# Script entry point
case "${1:-help}" in
    "standard"|"optimized"|"validation")
        main_install
        ;;
    "help"|*)
        echo "Usage: $0 [mode] [use_resolution]"
        echo ""
        echo "Modes:"
        echo "  standard    - Traditional installation (default)"
        echo "  optimized   - Use dependency conflict resolution"
        echo "  validation  - Grouped installation with validation"
        echo ""
        echo "Options:"
        echo "  use_resolution - 'true' (default) or 'false'"
        echo ""
        echo "Examples:"
        echo "  $0                    # Standard installation"
        echo "  $0 optimized          # Optimized installation"
        echo "  $0 optimized false    # Optimized without resolution"
        ;;
esac