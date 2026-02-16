# ComfyUI-Docker Unified Dashboard

A modern, unified dashboard for managing ComfyUI-Docker containers using FastAPI, htmx, Alpine.js, and Tailwind CSS.

## Features

- **Real-time Updates**: WebSocket support for live preset download progress
- **Authentication**: Session-based auth with ACCESS_PASSWORD or admin credentials
- **Service Management**: Monitor and control all ComfyUI services
- **Preset Management**: Browse and download 56+ AI model presets
- **Responsive Design**: Works on desktop and mobile devices
- **Modern UI**: Beautiful gradient design with Tailwind CSS

## Technology Stack

- **Backend**: FastAPI (Python)
- **Frontend**: htmx + Alpine.js + Tailwind CSS
- **Real-time**: WebSocket for live updates
- **Authentication**: Session-based with secure cookies
- **Templates**: Jinja2 for server-side rendering

## Quick Start

### Development

```bash
cd dashboard

# Install dependencies
pip install fastapi uvicorn jinja2 starlette

# Set environment variables
export ACCESS_PASSWORD="your-secret-password"
export ADMIN_PASSWORD="admin-password"

# Run development server
python app.py

# Or with uvicorn directly
uvicorn app:app --reload --host 0.0.0.0 --port 8081
```

### Production

```bash
# Using gunicorn
pip install gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8081
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ACCESS_PASSWORD` | Regular user password | (empty = no auth) |
| `ADMIN_PASSWORD` | Admin password for full access | `admin` |
| `DASHBOARD_PORT` | Dashboard server port | `8081` |
| `DASHBOARD_HOST` | Dashboard host | `0.0.0.0` |
| `DASHBOARD_SECRET_KEY` | Session encryption key | (auto-generated) |
| `SESSION_TIMEOUT_HOURS` | Session duration | `24` |

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login with credentials
- `POST /api/auth/logout` - Logout and clear session

### System Status
- `GET /api/status` - Get system status and download progress
- `GET /api/services` - Get all service statuses
- `GET /api/logs/{service}` - Get service logs (admin only)

### Presets
- `GET /api/presets` - List all available presets
- `GET /api/presets/{id}` - Get preset details
- `POST /api/presets/{id}/download` - Start preset download (admin only)

### WebSocket
- `WS /ws` - Real-time updates for download progress

## Architecture

```
dashboard/
├── app.py                  # FastAPI application
├── templates/              # Jinja2 templates
│   ├── base.html           # Base template with Tailwind/Alpine
│   ├── login.html          # Login page
│   ├── dashboard.html      # Main dashboard
│   └── partials/           # HTMX partial templates
│       ├── services_panel.html
│       ├── presets_panel.html
│       └── downloads_panel.html
└── static/                 # Static assets (CSS, JS, images)
```

## Features by User Role

### Regular User
- View service status
- Browse available presets
- Monitor download progress
- Access service URLs

### Admin
- All user features, plus:
- Start preset downloads
- View service logs
- Full system access

## Security

- Session-based authentication with secure cookies
- Password protection via ACCESS_PASSWORD
- Admin-only actions protected
- Session timeout after 24 hours (configurable)
- CSRF protection via htmx

## Future Enhancements

- [ ] Multi-container management
- [ ] Container metrics and monitoring
- [ ] Workflow management
- [ ] Model marketplace integration
- [ ] User preferences and customization
- [ ] Dark/light theme toggle
- [ ] Export/import configurations
