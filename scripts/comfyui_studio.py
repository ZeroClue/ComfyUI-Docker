#!/usr/bin/env python3
"""
ComfyUI Studio Entry Point
"""
import os
import sys
import logging

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from comfyui_studio.web_interface import StudioWeb
from comfyui_studio.config import config

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == '__main__':
    studio = StudioWeb()
    studio.run()
