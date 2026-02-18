#!/bin/bash
# Post-start script for RunPod compatibility
#
# NOTE: This script is now a no-op because start.sh handles all service startup.
# Previously this script started ComfyUI, but that's now done in start.sh Phase 2.
# Keeping this file for backward compatibility with RunPod templates.

log_info() {
    echo "[INFO] $1"
}

log_info "Post-start script running (no-op - services already started by start.sh)"
