#!/usr/bin/env python3
"""
ComfyUI Preset Manager - Complete Model Management System
A Flask-based web interface for managing ComfyUI presets and models

This is the main entry point that imports from the organized preset-manager package.
"""

import sys
import os

# When running from /app/, ensure /app/ is in Python path to access preset_manager package
# This fixes the import issue when script is copied to /app/preset_manager.py
app_dir = '/app/'
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Also add the script directory for development/testing
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from preset_manager.web_interface import PresetManagerWeb

if __name__ == '__main__':
    # Create and run the preset manager web interface
    web_interface = PresetManagerWeb()
    web_interface.run(host='0.0.0.0', port=9001, debug=False)