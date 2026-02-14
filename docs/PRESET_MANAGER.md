# ComfyUI Preset Manager

A comprehensive web-based model management system for ComfyUI containers, providing complete CRUD operations for AI model presets with storage monitoring and management capabilities.

## Features

### 🎯 Core Functionality
- **Preset Management**: Browse, download, and manage AI model presets by category (Video, Image, Audio)
- **Storage Monitoring**: Real-time disk usage tracking and detailed storage analytics
- **File Operations**: Safe download, deletion, and cleanup of model files
- **ACCESS_PASSWORD Authentication**: Secure access control integrated with existing container authentication

### 📊 Dashboard Features
- **Storage Overview**: Total/used/free space with visual charts
- **Installation Statistics**: Track preset installation progress and status
- **Real-time Updates**: Live progress tracking for downloads and operations
- **Category Organization**: Presets organized by Video/Image/Audio generation

### 🔧 Management Tools
- **Selective Downloads**: Download individual presets or complete workflows
- **Safe Deletion**: Remove specific models with confirmation dialogs
- **Cleanup Operations**: Remove unused models and clear cache
- **Validation**: Check model installation integrity

## Access

The Preset Manager is accessible via port **9000** in the container:

```
http://localhost:9000
```

### Theme System
The preset manager features a comprehensive dark/light theme system:
- **Default Theme**: Dark theme for reduced eye strain
- **Theme Toggle**: Sun/moon icon in sidebar for quick switching
- **Persistent Preference**: Theme choice saved in browser local storage
- **System Detection**: Automatically detects OS theme preference
- **Smooth Transitions**: 0.3s CSS transitions for theme changes
- **Chart Integration**: All charts adapt to current theme

### Authentication
- **Password Protected**: Uses `ACCESS_PASSWORD` environment variable (defaults to 'password')
- **Security Warnings**: Alerts when using default password for development
- **Session Management**: Secure sessions with automatic timeout
- **Consistent Integration**: Same authentication as code-server and JupyterLab

#### Security Considerations
- **Default Password**: The system uses 'password' as the default for development convenience
- **Production Security**: Always set `ACCESS_PASSWORD` environment variable in slim
- **Warning System**: Visual alerts indicate when default password is being used
- **Session Security**: Secure session handling with proper timeout mechanisms

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ACCESS_PASSWORD` | `password` | Password for accessing the web interface (fallback: 'password') |
| `ENABLE_PRESET_MANAGER` | true | Enable/disable preset manager startup |
| `TIME_ZONE` | UTC | Set container timezone |

## User Interface

### Dashboard
- **Storage Cards**: Visual overview of disk usage and preset statistics
- **Installation Charts**: Progress tracking for preset installations
- **Quick Actions**: One-click access to common tasks
- **Storage Breakdown**: Detailed usage by model category

### Preset Browser
- **Search & Filter**: Find presets by name, category, or installation status
- **Sort Options**: Organize by name, size, or status
- **Grid/List View**: Toggle between display modes
- **Batch Operations**: Select multiple presets for bulk actions

### Preset Details
- **Installation Status**: Complete file-by-file installation tracking
- **File Management**: Individual file information and size details
- **Documentation**: Integrated README content for each preset
- **Quick Actions**: Download, delete, or validate installations

### Storage Manager
- **Visual Analytics**: Charts and graphs for storage usage
- **Category Breakdown**: Detailed usage by model type
- **Cleanup Tools**: Safe removal of unused models
- **Export Reports**: Generate storage usage reports

## API Endpoints

### Preset Management
- `GET /api/download/<preset_id>` - Start preset download
- `DELETE /api/delete/<preset_id>` - Delete preset files
- `GET /api/operation/status/<operation_id>` - Get operation status

### Storage Management
- `POST /api/cleanup` - Cleanup unused models
- `GET /api/storage/status` - Get current storage information

### Authentication
- `POST /login` - Authenticate with password
- `GET /logout` - End session

## Supported Presets

### Video Generation
- **LTXV 2B FP8**: High-quality video generation (4.8GB)
- **Wan 2.2 T2V**: Text-to-video generation (9.2GB)
- **Hunyuan T2V 720P**: 720p video generation (5.1GB)
- **Mochi 1 Preview**: Next-generation video (9.8GB)
- **Complete Workflow**: Full video generation suite (25GB)

### Image Generation
- **FLUX Schnell**: Fast high-quality generation (24GB)
- **FLUX Dev**: Maximum quality generation (24GB)
- **SDXL Base 1.0**: Standard high-resolution generation (6.9GB)
- **Realistic Vision**: Photorealistic generation (5.1GB)
- **Complete Workflow**: Full image generation suite (100GB)

### Audio Generation
- **MusicGen Medium**: High-quality music generation (2.8GB)
- **Bark TTS**: Voice synthesis (2.1GB)
- **Stable Audio**: Audio generation (2.4GB)
- **Complete Audio Suite**: Full audio generation (15GB)

## File Structure

The preset manager operates on the following directories:

```
/workspace/ComfyUI/models/
├── checkpoints/          # Main AI models
├── diffusion_models/     # Custom diffusion models
├── text_encoders/       # Text encoder models
├── vae/                 # VAE models
├── loras/               # LoRA adaptation models
├── upscale_models/      # Image upscaling models
├── audio_encoders/      # Audio encoder models
├── TTS/                 # Text-to-speech models
└── audio/               # Music and audio generation models
```

## Security Features

### Authentication
- **Password Protection**: ACCESS_PASSWORD environment variable
- **Session Security**: Signed sessions with configurable timeout
- **Secure Headers**: CSRF protection and secure cookies

### File Operations
- **Safe Deletion**: Confirmation dialogs for all destructive operations
- **Path Validation**: Prevents directory traversal attacks
- **Permission Checks**: Validates file access permissions
- **Audit Logging**: All operations logged to `/workspace/logs/`

### Data Integrity
- **File Validation**: Checksum verification for downloads
- **Rollback Support**: Safe rollback points for major changes
- **Dependency Checking**: Warn before deleting models in use
- **Backup Prompts**: Optional backup before deletions

## Troubleshooting

### Common Issues

**Access Denied**
- Check `ACCESS_PASSWORD` environment variable
- Verify session cookies are enabled
- Clear browser cache and cookies

**Slow Downloads**
- Check internet connection speed
- Verify sufficient disk space
- Monitor progress in real-time

**Storage Errors**
- Check available disk space
- Verify file permissions
- Run storage validation tools

**Service Not Starting**
- Check logs: `/workspace/logs/preset_manager.log`
- Verify port 9001 is available
- Check Nginx configuration

### Log Files

- **Preset Manager**: `/workspace/logs/preset_manager.log`
- **Nginx**: `/var/log/nginx/`
- **Container**: Docker container logs

### Performance Optimization

- **Regular Cleanup**: Remove unused models to free space
- **Storage Monitoring**: Keep an eye on disk usage
- **Batch Operations**: Use bulk actions for efficiency
- **Cache Management**: Clear download cache periodically

## Development

### Local Testing
```bash
# Install dependencies
pip install -r scripts/requirements-preset-manager.txt

# Run development server
cd scripts
python3 preset_manager.py
```

### Configuration
The preset manager can be customized by modifying:
- Preset definitions in `ModelManager._parse_all_presets()`
- Template files in `scripts/templates/`
- Nginx routing in `proxy/nginx.conf`

### Extensions
- Add new presets by updating preset definitions
- Customize UI by modifying HTML templates
- Extend API by adding new Flask routes
- Integrate with external services via API hooks

## Integration

### Container Services
The preset manager integrates with existing container services:
- **Nginx**: Reverse proxy on port 9000
- **Code-server**: Shared authentication system
- **JupyterLab**: Consistent access control
- **SSH**: Secure file access

### External Tools
- **ComfyUI**: Direct model directory integration
- **HuggingFace**: Model download integration
- **Docker**: Container orchestration
- **RunPod**: Cloud deployment platform

## Support

For issues and support:
1. Check container logs for error messages
2. Verify environment variables are set correctly
3. Ensure sufficient disk space and permissions
4. Review this documentation for troubleshooting steps

The preset manager is designed to be intuitive and user-friendly, with comprehensive error handling and helpful documentation integrated throughout the interface.

## Theme Customization

### CSS Variables
The theme system uses CSS custom properties for easy customization:

```css
:root {
    --bg-primary: #ffffff;        /* Main background */
    --bg-secondary: #f8f9fa;      /* Secondary background */
    --text-primary: #212529;      /* Main text */
    --card-bg: #ffffff;          /* Card backgrounds */
    --border-color: #dee2e6;     /* Borders */
}

[data-theme="dark"] {
    --bg-primary: #1a1d23;       /* Dark main background */
    --bg-secondary: #2d3139;     /* Dark secondary background */
    --text-primary: #e9ecef;     /* Dark main text */
    --card-bg: #2d3139;         /* Dark card backgrounds */
    --border-color: #495057;     /* Dark borders */
}
```

### Theme Development
- **Colors**: Modify CSS variables in `templates/base.html`
- **Animations**: Adjust transition effects in CSS
- **Icons**: Replace Font Awesome icons for theme toggle
- **Charts**: Update Chart.js color schemes in theme manager