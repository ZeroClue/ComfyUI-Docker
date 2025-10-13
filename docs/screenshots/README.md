# Preset Manager Screenshots

This directory contains screenshots for the Preset Manager documentation.

## Required Screenshots

1. **dashboard.png** - Main dashboard showing storage overview and preset categories
2. **preset_browser.png** - Preset browsing interface with video/image/audio tabs
3. **preset_details.png** - Individual preset detail page with README rendering
4. **storage_management.png** - Storage management interface with disk usage analytics
5. **progress_tracking.png** - Download progress and operation status interface

## Screenshot Guidelines

- **Resolution**: 1920x1080 or higher
- **Format**: PNG (for quality) or WebP (for size)
- **Content**: Show complete browser window with URL bar visible
- **Privacy**: Ensure no sensitive information is visible
- **Consistency**: Use consistent theme and browser settings

## How to Generate Screenshots

1. Start a ComfyUI container with preset manager enabled
2. Access `http://localhost:9000` in your browser
3. Navigate to different sections of the interface
4. Capture high-quality screenshots of key features
5. Rename files according to the list above
6. Optimize for web display (reasonable file size)

## Current Status

📸 **Screenshots Needed**: 5
📁 **Directory Created**: ✅
📖 **Documentation Ready**: ✅
🔧 **README Location Fixed**: ✅ (Now reads from container image)
⏳ **To Generate**: Run container and access http://localhost:9000

## Quick Instructions for Generating Screenshots

1. **Start Container**:
   ```bash
   docker run --gpus all -p 9000:9000 -e ACCESS_PASSWORD=mypassword zeroclue/comfyui:base-torch2.8.0-cu126
   ```

2. **Access Interface**: Open `http://localhost:9000` in browser

3. **Login**: Use the password you set (or leave blank if no ACCESS_PASSWORD)

4. **Capture Screenshots**:
   - Navigate to Dashboard (home page)
   - Click "Presets" and capture preset browser
   - Click any preset to capture details page
   - Check "Storage" for storage management
   - Start a download to capture progress tracking

5. **Save Files**: Save as PNG with names from the list above