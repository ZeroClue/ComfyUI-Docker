#!/usr/bin/env python3
"""
ComfyUI Preset Manager - Complete Model Management System
A Flask-based web interface for managing ComfyUI presets and models

This is the main entry point that imports from the organized preset-manager package.
"""

import sys
import os

# Add the current directory to the Python path to access preset-manager package
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from preset_manager.web_interface import PresetManagerWeb

if __name__ == '__main__':
    # Create and run the preset manager web interface
    web_interface = PresetManagerWeb()
    web_interface.run(host='0.0.0.0', port=9001, debug=False)