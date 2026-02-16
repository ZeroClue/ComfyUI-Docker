# ComfyUI-Docker Revolutionary Rebuild: Implementation Roadmap

**Version**: 1.0.0
**Last Updated**: 2025-02-15
**Status**: DRAFT

## Executive Summary

This roadmap details the complete system rebuild of ComfyUI-Docker with a focus on eliminating startup bottlenecks (rsync), creating a unified dashboard interface, fixing preset download functionality, and implementing 4 build variants with native ComfyUI model path integration.

**Primary Goals**:
- **Startup Performance**: Reduce 5-10 minute startup to <30 seconds
- **Unified Dashboard**: Single interface (htmx + Alpine + Tailwind) for all management
- **Functional Preset System**: Reliable download with progress tracking
- **Modular Architecture**: 4 build variants (minimal, standard, full, dev)
- **Native Integration**: Seamless extra_model_paths.yaml support

**Estimated Timeline**: 6-8 weeks with parallel execution

---

## Phase 1: Research & Analysis (Week 1)

### Objective
Thoroughly document current architecture, identify bottlenecks, and research solutions.

### Tasks

#### 1.1 Current Architecture Documentation
**Agent Type**: Explore
**Complexity**: Low
**Dependencies**: None
**Parallel**: Yes

**Description**: Create comprehensive documentation of existing system architecture including all services, dependencies, data flows, and integration points.

**Deliverables**:
- `/docs/ARCHITECTURE_CURRENT.md` - Complete system diagram
- `/docs/SERVICE_DEPENDENCIES.md` - Service dependency graph
- `/docs/DATA_FLOWS.md` - Data flow diagrams

**Acceptance Criteria**:
- All services documented (ComfyUI, Preset Manager, Code Server, Jupyter, Nginx)
- All environment variables catalogued
- All volume mounts documented
- All inter-service communications mapped

**Verification**:
```bash
# Run architecture validation
python scripts/validate_architecture_docs.py
```

---

#### 1.2 Bottleneck Analysis
**Agent Type**: Explore
**Complexity**: Medium
**Dependencies**: 1.1
**Parallel**: Yes

**Description**: Analyze rsync bottleneck in `/scripts/post_start.sh` lines 34-229 to identify exact performance constraints and optimization opportunities.

**Key Files**:
- `/scripts/post_start.sh` - rsync operations (lines 34-229)
- `/Dockerfile` - Build structure
- `/scripts/start.sh` - Service orchestration

**Deliverables**:
- `/docs/BOTTLENECK_ANALYSIS.md` - Detailed performance analysis
- `/scripts/profile_sync.py` - Sync profiling tool

**Acceptance Criteria**:
- Exact time spent in each rsync operation documented
- Alternative sync strategies evaluated (bind mounts, volume configurations, symbolic links)
- Implementation recommendation with performance projections

**Risk Areas**:
- Network volume performance characteristics may vary
- Existing user workflows may depend on current sync behavior

**Verification**:
```bash
# Run profiling
python scripts/profile_sync.py
```

---

#### 1.3 Technology Stack Research
**Agent Type**: Explore
**Complexity**: Low
**Dependencies**: None
**Parallel**: Yes

**Description**: Research and document technology choices for unified dashboard.

**Research Areas**:
- **htmx**: Documentation, patterns, limitations
- **Alpine.js**: Reactivity patterns, component architecture
- **Tailwind CSS**: Design system, theming strategy
- **FastAPI**: WebSocket patterns, async operations
- **Build Tools**: Docker multi-stage patterns, caching strategies

**Deliverables**:
- `/docs/TECH_STACK_RESEARCH.md` - Technology comparison
- `/docs/HTMX_PATTERNS.md` - htmx implementation patterns
- `/docs/DESIGN_SYSTEM.md` - Design system specification

**Acceptance Criteria**:
- All technologies evaluated against requirements
- Implementation patterns documented
- Risk areas identified
- Alternative options documented

---

## Phase 2: Infrastructure Rebuild (Week 2-3)

### Objective
Eliminate rsync bottleneck and restructure Docker build system for 4 variants.

### Tasks

#### 2.1 Volume Strategy Redesign
**Agent Type**: Code
**Complexity**: High
**Dependencies**: 1.1, 1.2
**Parallel**: No

**Description**: Implement workspace-first architecture eliminating rsync operations entirely.

**Key Changes**:
- **File**: `/Dockerfile`
  - Change `WORKDIR /` to `WORKDIR /workspace` (line 46)
  - Install ComfyUI directly to `/workspace/ComfyUI` (line 84)
  - Create venv directly at `/workspace/venv` (line 68)
  - Remove all rsync-related code

- **File**: `/scripts/post_start.sh`
  - Remove optimized_venv_sync() function (lines 34-72)
  - Remove ComfyUI sync logic (lines 166-229)
  - Keep only timezone and optional package installation

**New Architecture**:
```
/workspace/
├── ComfyUI/           # Installed directly, no sync
├── venv/              # Created directly, no sync
├── config/            # Configuration
├── models/            # Symlink to /workspace/ComfyUI/models
└── logs/              # Runtime logs
```

**Deliverables**:
- Modified `/Dockerfile`
- Modified `/scripts/post_start.sh`
- `/docs/VOLUME_ARCHITECTURE.md` - New volume design
- `/tests/test_volume_setup.py` - Verification tests

**Acceptance Criteria**:
- Container starts in <30 seconds on fresh volume
- No rsync operations in any startup script
- All paths reference `/workspace` directly
- Backward compatibility maintained for existing volumes

**Risk Areas**:
- Breaking existing user workflows
- Volume mount configuration changes
- Container size increase

**Rollback Strategy**:
- Git branch `feature/volume-redesign`
- Feature flag `USE_NEW_VOLUME_STRATEGY` for gradual rollout
- Maintain old rsync code behind feature flag

**Verification**:
```bash
# Test container startup time
time docker run --rm zeroclue/comfyui:test-volume-strategy

# Verify all paths
docker exec <container> ls -la /workspace/
docker exec <container> test -f /workspace/venv/.sync_complete && echo "FAIL: marker should not exist" || echo "PASS"
```

---

#### 2.2 Multi-Stage Dockerfile Refactor
**Agent Type**: Code
**Complexity**: High
**Dependencies**: 2.1
**Parallel**: No

**Description**: Refactor Dockerfile into explicit stages for each build variant.

**New Dockerfile Structure**:
```dockerfile
# Base stage - common to all variants
FROM nvidia/cuda:${CUDA_VERSION}-devel-ubuntu24.04 AS base
# [Common setup]

# Builder stage - for compilation
FROM base AS builder
# [Heavy compilation - PyTorch, custom nodes]

# Variant stages
FROM base AS minimal-runtime
# [ComfyUI + Manager only]

FROM builder AS standard-runtime
# [minimal + common custom nodes]

FROM standard-runtime AS full-runtime
# [standard + extra nodes + dev tools]

FROM full-runtime AS dev-runtime
# [full + code-server + jupyter + debugging tools]
```

**Key Files**:
- `/Dockerfile` - Complete rewrite
- `/docker-bake.hcl` - Updated build targets
- `/.github/workflows/build.yml` - CI updates

**Deliverables**:
- New multi-stage `/Dockerfile`
- Updated `/docker-bake.hcl` with 4 variant targets
- `/docs/BUILD_VARIANTS.md` - Variant specification
- Build time benchmarks

**Acceptance Criteria**:
- 4 distinct build variants: minimal, standard, full, dev
- Each variant builds successfully
- Image sizes: minimal (~4GB), standard (~6GB), full (~10GB), dev (~12GB)
- All CUDA versions (12.4-13.0) build for each variant

**Risk Areas**:
- Build cache invalidation
- Stage dependency errors
- Increased build complexity

**Verification**:
```bash
# Build all variants
docker buildx bake minimal-12-6 standard-12-6 full-12-6 dev-12-6

# Check image sizes
docker images | grep zeroclue/comfyui
```

---

#### 2.3 Native extra_model_paths.yaml Integration
**Agent Type**: Code
**Complexity**: Medium
**Dependencies**: 2.1
**Parallel**: Yes (with 2.2)

**Description**: Implement automatic extra_model_paths.yaml generation and management.

**Key Files**:
- `/scripts/generate_extra_paths.py` - Already exists, enhance it
- `/scripts/post_start.sh` - Call path generation
- `/workspace/ComfyUI/models/` - Symlink strategy

**Implementation**:
```python
# /scripts/generate_extra_paths.py (enhanced)
def generate_model_paths():
    """Generate ComfyUI extra_model_paths.yaml"""
    config = {
        'workspace': '/workspace/ComfyUI/models',
        'checkpoints': '/workspace/ComfyUI/models/checkpoints',
        'loras': '/workspace/ComfyUI/models/loras',
        # ... all model categories
    }
    # Write to /workspace/ComfyUI/extra_model_paths.yaml
```

**Deliverables**:
- Enhanced `/scripts/generate_extra_paths.py`
- Auto-generation on container start
- Runtime path updates for custom mounts
- `/docs/MODEL_PATHS.md` - Path configuration guide

**Acceptance Criteria**:
- extra_model_paths.yaml auto-generated on startup
- Custom model mounts detected and added
- Paths validated before ComfyUI start
- Preset downloads use configured paths

**Verification**:
```bash
# Check generated file
docker exec <container> cat /workspace/ComfyUI/extra_model_paths.yaml

# Test custom mount
docker run -v /custom/models:/models zeroclue/comfyui:latest
docker exec <container> grep "/models" /workspace/ComfyUI/extra_model_paths.yaml
```

---

## Phase 3: Backend Services (Week 3-4)

### Objective
Build FastAPI backend with WebSocket support for unified dashboard.

### Tasks

#### 3.1 FastAPI Application Skeleton
**Agent Type**: Code
**Complexity**: Medium
**Dependencies**: 2.1, 2.2
**Parallel**: Yes

**Description**: Create FastAPI application with proper structure, authentication, and error handling.

**New Structure**:
```
/backend/
├── __init__.py
├── main.py              # FastAPI app initialization
├── api/
│   ├── __init__.py
│   ├── presets.py       # Preset CRUD endpoints
│   ├── storage.py       # Storage management
│   ├── downloads.py     # Download orchestration
│   ├── system.py        # System info, health
│   └── auth.py          # Authentication
├── models/
│   ├── __init__.py
│   ├── preset.py        # Preset data models
│   ├── download.py      # Download progress models
│   └── system.py        # System info models
├── services/
│   ├── __init__.py
│   ├── preset_manager.py    # Preset business logic
│   ├── downloader.py        # Download orchestration
│   ├── path_manager.py      # Path configuration
│   └── websocket_manager.py # WebSocket handling
├── web/
│   ├── __init__.py
│   └── socket.py        # WebSocket routes
└── config/
    ├── __init__.py
    └── settings.py      # Configuration management
```

**Key Files**:
- `/backend/main.py` - FastAPI app
- `/backend/config/settings.py` - Settings with Pydantic
- `/backend/api/auth.py` - JWT authentication
- `/backend/web/socket.py` - WebSocket manager

**Deliverables**:
- Complete FastAPI application structure
- JWT authentication with ACCESS_PASSWORD
- CORS configuration
- Request/response logging
- `/docs/API_ARCHITECTURE.md` - API documentation
- `/tests/test_api.py` - API tests

**Acceptance Criteria**:
- FastAPI app runs on port 8000
- All endpoints return proper JSON responses
- Authentication middleware functional
- WebSocket connections accepted
- OpenAPI documentation accessible at `/docs`

**Risk Areas**:
- Async/await complexity with existing sync code
- WebSocket connection management
- Authentication token handling

**Verification**:
```bash
# Start backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Test health endpoint
curl http://localhost:8000/api/health

# Test authentication
curl -X POST http://localhost:8000/api/auth/login -d '{"password":"test"}'
```

---

#### 3.2 Preset Management API
**Agent Type**: Code
**Complexity**: High
**Dependencies**: 3.1
**Parallel**: No

**Description**: Implement RESTful API for preset CRUD operations using existing ModelManager from `/scripts/preset_manager/core.py`.

**Endpoints**:
```
GET    /api/presets              - List all presets
GET    /api/presets/:id          - Get preset details
POST   /api/presets/:id/download - Start download
DELETE /api/presets/:id          - Delete preset files
GET    /api/presets/:id/status   - Get installation status
POST   /api/presets/update       - Update preset definitions
GET    /api/presets/categories   - List categories
```

**Key Files**:
- `/backend/api/presets.py` - Preset endpoints
- `/backend/services/preset_manager.py` - Business logic
- Migrate `/scripts/preset_manager/core.py` logic to services layer

**Deliverables**:
- Complete preset API
- Request/response models
- Error handling
- Input validation
- `/tests/test_presets_api.py`

**Acceptance Criteria**:
- All endpoints functional
- Existing ModelManager logic integrated
- Progress tracking via WebSocket
- File validation after download
- Error recovery with retry logic

**Risk Areas**:
- Thread safety in download operations
- Progress tracking accuracy
- File system race conditions

**Verification**:
```bash
# Test preset list
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/presets

# Test download start
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/presets/LTX_VIDEO_T2V/download

# Monitor via WebSocket
wscat -c ws://localhost:8000/ws/downloads
```

---

#### 3.3 Download Service Rewrite
**Agent Type**: Code
**Complexity**: High
**Dependencies**: 3.2
**Parallel**: No

**Description**: Complete rewrite of download functionality with proper progress tracking, error handling, and cancellation support.

**Current Issues**:
- `/scripts/unified_preset_downloader.py` - Generates temp scripts, hard to track
- `/scripts/preset_manager/web_interface.py:495-632` - Complex thread management
- No cancellation support
- Limited progress reporting

**New Implementation**:
```python
# /backend/services/downloader.py
class DownloadService:
    async def download_preset(self, preset_id: str) -> DownloadTask:
        """Start preset download with progress tracking"""

    async def cancel_download(self, task_id: str) -> bool:
        """Cancel active download"""

    async def get_progress(self, task_id: str) -> DownloadProgress:
        """Get real-time progress"""

    async def retry_failed(self, task_id: str) -> bool:
        """Retry failed download"""
```

**Key Files**:
- `/backend/services/downloader.py` - New download service
- `/backend/api/downloads.py` - Download endpoints
- Remove `/scripts/unified_preset_downloader.py`
- Update `/scripts/preset_manager/web_interface.py`

**Deliverables**:
- Async download service
- Per-file progress tracking
- Cancellation support
- Automatic retry with exponential backoff
- Download queue management
- `/tests/test_downloader.py`

**Acceptance Criteria**:
- Downloads report byte-level progress
- Cancellation stops downloads cleanly
- Failed downloads auto-retry 3 times
- Multiple downloads run in parallel (max 4)
- Progress broadcasts via WebSocket

**Risk Areas**:
- Async/sync mixing with subprocess calls
- Memory usage with large parallel downloads
- Network interruption handling

**Verification**:
```bash
# Test download
curl -X POST http://localhost:8000/api/downloads/start \
  -H "Content-Type: application/json" \
  -d '{"preset_id": "LTX_VIDEO_T2V"}'

# Monitor progress
wscat -c ws://localhost:8000/ws/progress/{task_id}

# Test cancellation
curl -X POST http://localhost:8000/api/downloads/{task_id}/cancel
```

---

#### 3.4 WebSocket Progress Broadcasting
**Agent Type**: Code
**Complexity**: Medium
**Dependencies**: 3.3
**Parallel**: Yes (with 3.3)

**Description**: Implement WebSocket manager for real-time progress broadcasting.

**WebSocket Channels**:
```
/ws/downloads          - All download progress
/ws/downloads/{id}     - Specific download progress
/ws/storage            - Storage usage updates
/ws/system             - System status updates
```

**Key Files**:
- `/backend/web/socket.py` - WebSocket routes
- `/backend/services/websocket_manager.py` - Connection manager

**Deliverables**:
- WebSocket connection manager
- Broadcast to channels
- Authentication for WebSocket
- Automatic reconnection handling
- `/tests/test_websockets.py`

**Acceptance Criteria**:
- Multiple clients connect to same channel
- Progress updates <100ms latency
- Authentication required for all connections
- Graceful disconnect handling
- Reconnection support

**Verification**:
```bash
# Connect with wscat
wscat -c "ws://localhost:8000/ws/downloads?token=$TOKEN"

# Should receive progress updates
```

---

## Phase 4: Frontend Dashboard (Week 4-5)

### Objective
Build unified dashboard with htmx, Alpine.js, and Tailwind CSS.

### Tasks

#### 4.1 Design System Implementation
**Agent Type**: Code
**Complexity**: Medium
**Dependencies**: 1.3
**Parallel**: Yes

**Description**: Implement Tailwind CSS design system with theming support.

**Key Files**:
- `/frontend/static/css/styles.css` - Custom styles
- `/frontend/static/css/themes/` - Theme definitions
- `/frontend/static/js/alpine-init.js` - Alpine initialization

**Design Tokens**:
```css
:root {
  --primary: #6366f1;
  --secondary: #8b5cf6;
  --success: #10b981;
  --warning: #f59e0b;
  --danger: #ef4444;
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
}
```

**Deliverables**:
- Tailwind configuration
- Custom CSS variables
- Theme system (light, dark, high contrast)
- Component library
- `/docs/DESIGN_SYSTEM.md`

**Acceptance Criteria**:
- 3 themes available
- Consistent spacing and typography
- Accessible color contrast (WCAG AA)
- Responsive breakpoints
- Dark theme default

**Verification**:
```bash
# Build CSS
npm run build:css

# Check theme switching
curl http://localhost:8000/ | grep "data-theme"
```

---

#### 4.2 Layout Components
**Agent Type**: Code
**Complexity**: Medium
**Dependencies**: 4.1
**Parallel**: No

**Description**: Build core layout components using htmx and Alpine.js.

**Components**:
- Sidebar navigation
- Top bar with search
- Main content area
- Modal system
- Toast notifications
- Loading states

**Key Files**:
- `/frontend/templates/components/sidebar.html`
- `/frontend/templates/components/navbar.html`
- `/frontend/templates/components/modal.html`
- `/frontend/templates/components/toast.html`
- `/frontend/static/js/components.js` - Alpine components

**htmx Patterns**:
```html
<!-- Navigation -->
<nav hx-get="/api/presets" hx-target="#main-content">
  <button hx-get="/api/presets?category=video" hx-push-url="true">
    Video Models
  </button>
</nav>

<!-- Modal -->
<div id="modal" class="modal"
     hx-trigger="click from:#close-modal"
     hx-swap="outerHTML"
     hx-get="/api/modal/close">
</div>
```

**Alpine.js Components**:
```javascript
// Theme switcher
Alpine.data('themeSwitcher', () => ({
  theme: 'dark',
  toggle() {
    this.theme = this.theme === 'dark' ? 'light' : 'dark'
    document.documentElement.setAttribute('data-theme', this.theme)
  }
}))
```

**Deliverables**:
- All layout components
- Component documentation
- Storybook-style examples
- `/tests/test_components.js`

**Acceptance Criteria**:
- All components responsive
- htmx attributes properly configured
- Alpine reactivity working
- Keyboard navigation supported
- ARIA labels present

**Verification**:
```bash
# Test component rendering
curl http://localhost:8000/components/sidebar

# Test htmx interactions
# (manual browser testing)
```

---

#### 4.3 Dashboard Pages
**Agent Type**: Code
**Complexity**: High
**Dependencies**: 4.2
**Parallel**: No

**Description**: Implement main dashboard pages with data binding.

**Pages**:
1. **Overview Dashboard**
   - System stats
   - Storage overview
   - Recent activity
   - Quick actions

2. **Preset Browser**
   - Filterable list
   - Category navigation
   - Search functionality
   - Bulk operations

3. **Preset Detail**
   - Model information
   - Download progress
   - File list
   - Related presets

4. **Storage Manager**
   - Usage breakdown
   - Unknown models
   - Cleanup tools
   - Export/Import

5. **Settings**
   - Configuration
   - Theme selection
   - Download preferences
   - System info

**Key Files**:
- `/frontend/templates/pages/dashboard.html`
- `/frontend/templates/pages/presets.html`
- `/frontend/templates/pages/preset-detail.html`
- `/frontend/templates/pages/storage.html`
- `/frontend/templates/pages/settings.html`

**Deliverables**:
- All 5 pages implemented
- Page transitions with htmx
- Data loading states
- Error handling
- `/tests/test_pages.js`

**Acceptance Criteria**:
- All pages accessible via navigation
- Data loads from API
- Loading states shown
- Errors displayed gracefully
- Back button works

**Risk Areas**:
- Large preset list performance
- WebSocket reconnection during navigation
- Browser back button behavior with htmx

**Verification**:
```bash
# Test each page
curl http://localhost:8000/
curl http://localhost:8000/presets
curl http://localhost:8000/storage
```

---

#### 4.4 Real-time Progress Components
**Agent Type**: Code
**Complexity**: Medium
**Dependencies**: 4.3, 3.4
**Parallel**: Yes

**Description**: Build components for real-time download progress and status updates.

**Components**:
- Download queue display
- Per-file progress bars
- Speed/ETA calculations
- Cancellation buttons
- Retry controls

**Key Files**:
- `/frontend/templates/components/download-queue.html`
- `/frontend/templates/components/progress-bar.html`
- `/frontend/static/js/download-monitor.js`

**WebSocket Integration**:
```javascript
// Connect to download progress
const ws = new WebSocket(`ws://${host}/ws/downloads?token=${token}`)

ws.onmessage = (event) => {
  const data = JSON.parse(event.data)
  Alpine.store('downloads').update(data)
}
```

**Deliverables**:
- Real-time progress components
- Automatic reconnection
- Queue management UI
- Download history
- `/tests/test_progress.js`

**Acceptance Criteria**:
- Progress updates <500ms
- Multiple downloads shown simultaneously
- Cancellation works instantly
- Reconnection automatic
- Download speed calculated

**Verification**:
```bash
# Start test download
# Monitor WebSocket in browser DevTools
# Verify progress updates
```

---

## Phase 5: Integration & Testing (Week 5-6)

### Objective
Integrate all components and ensure system reliability.

### Tasks

#### 5.1 Nginx Configuration Update
**Agent Type**: Code
**Complexity**: Medium
**Dependencies**: 3.1, 4.1
**Parallel**: Yes

**Description**: Update Nginx configuration for unified dashboard routing.

**Key Files**:
- `/proxy/nginx.conf` - Update routing
- `/proxy/snippets/` - Reusable snippets

**New Routing**:
```
Port 3001 -> ComfyUI (existing)
Port 8081 -> Code Server (existing)
Port 8889 -> JupyterLab (existing)
Port 8001 -> Unified Dashboard (NEW)
```

**Deliverables**:
- Updated Nginx config
- WebSocket proxy configuration
- Static file serving
- Compression settings
- `/docs/NGINX_CONFIG.md`

**Acceptance Criteria**:
- Dashboard accessible on default port
- WebSocket connections proxy correctly
- Static assets cached appropriately
- Gzip compression enabled

**Verification**:
```bash
# Test routing
curl http://localhost:8001/
curl http://localhost:8001/api/health

# Test WebSocket
wscat -c ws://localhost:8001/ws/downloads
```

---

#### 5.2 Startup Script Integration
**Agent Type**: Code
**Complexity**: Medium
**Dependencies**: 3.1, 5.1
**Parallel**: No

**Description**: Update startup scripts to launch unified dashboard service.

**Key Files**:
- `/scripts/start.sh` - Add dashboard service
- `/scripts/pre_start.sh` - Pre-flight checks
- `/scripts/post_start.sh` - Post-initialization

**Changes**:
```bash
# Add to start.sh
start_dashboard() {
    echo "Starting Unified Dashboard..."
    cd /backend
    nohup uvicorn main:app --host 0.0.0.0 --port 8000 \
        --log-level info > /workspace/logs/dashboard.log 2>&1 &
}
```

**Deliverables**:
- Updated start.sh
- Health check function
- Graceful shutdown
- Log management

**Acceptance Criteria**:
- Dashboard starts on container boot
- Health check passes
- Logs properly rotated
- Graceful shutdown works

**Verification**:
```bash
# Start container
docker run zeroclue/comfyui:latest

# Check dashboard
curl http://localhost:8001/api/health
```

---

#### 5.3 End-to-End Testing
**Agent Type**: Code
**Complexity**: High
**Dependencies**: All previous tasks
**Parallel**: No

**Description**: Comprehensive E2E testing of all functionality.

**Test Areas**:
1. **Container Startup**
   - Fresh volume start time <30s
   - Existing volume start time <10s
   - All services healthy

2. **Preset Management**
   - List all presets
   - Download preset
   - Cancel download
   - Delete preset
   - Update definitions

3. **Storage Management**
   - View storage usage
   - Identify unknown models
   - Cleanup unused models
   - Export configuration

4. **Dashboard UI**
   - Navigate all pages
   - Theme switching
   - Search/filter
   - Responsive design

**Key Files**:
- `/tests/e2e/test_startup.py`
- `/tests/e2e/test_presets.py`
- `/tests/e2e/test_storage.py`
- `/tests/e2e/test_ui.py`
- `/tests/e2e/fixtures.py`

**Tools**:
- pytest for backend tests
- Playwright for UI tests
- docker-compose for integration tests

**Deliverables**:
- Complete E2E test suite
- Test coverage report
- Performance benchmarks
- CI/CD integration

**Acceptance Criteria**:
- >80% code coverage
- All E2E tests passing
- Performance benchmarks met
- CI/CD pipeline green

**Risk Areas**:
- Test environment setup complexity
- Flaky tests due to timing
- Resource requirements for E2E tests

**Verification**:
```bash
# Run all tests
pytest tests/ -v --cov=/backend --cov-report=html

# Run E2E tests
pytest tests/e2e/ --docker-compose
```

---

#### 5.4 Performance Benchmarking
**Agent Type**: Code
**Complexity**: Medium
**Dependencies**: 5.3
**Parallel**: Yes

**Description**: Benchmark all performance aspects and establish baselines.

**Metrics**:
- Container startup time
- Time to first byte
- API response times
- WebSocket latency
- Download speeds
- Memory usage
- CPU usage

**Key Files**:
- `/tests/benchmarks/startup.py`
- `/tests/benchmarks/api.py`
- `/tests/benchmarks/websocket.py`
- `/tests/benchmarks/memory.py`

**Deliverables**:
- Performance baseline report
- Regression tests
- Monitoring dashboard
- `/docs/PERFORMANCE_BASELINES.md`

**Acceptance Criteria**:
- Startup <30s (target)
- API p95 <100ms
- WebSocket latency <50ms
- Memory <4GB idle

**Verification**:
```bash
# Run benchmarks
pytest tests/benchmarks/ --benchmark-only
```

---

## Phase 6: Documentation & Deployment (Week 6-7)

### Objective
Complete documentation and prepare for deployment.

### Tasks

#### 6.1 User Documentation
**Agent Type**: Write
**Complexity**: Medium
**Dependencies**: 5.3
**Parallel**: Yes

**Description**: Write comprehensive user documentation.

**Documents**:
- Quick Start Guide
- Dashboard User Guide
- Preset Management Guide
- Troubleshooting Guide
- Migration Guide (from old system)

**Key Files**:
- `/docs/USER_GUIDE.md`
- `/docs/QUICKSTART.md`
- `/docs/TROUBLESHOOTING.md`
- `/docs/MIGRATION.md`

**Deliverables**:
- All user-facing documentation
- Screenshots/ diagrams
- Video tutorials (optional)
- FAQ

**Acceptance Criteria**:
- All features documented
- Step-by-step instructions
- Troubleshooting sections
- Migration paths clear

---

#### 6.2 API Documentation
**Agent Type**: Write
**Complexity**: Low
**Dependencies**: 3.1
**Parallel**: Yes

**Description**: Complete API documentation with examples.

**Key Files**:
- `/docs/API_REFERENCE.md`
- OpenAPI spec enhancements
- Postman collection

**Deliverables**:
- Complete API reference
- Request/response examples
- Error code documentation
- Authentication guide

**Acceptance Criteria**:
- All endpoints documented
- Examples for each endpoint
- Error scenarios covered

---

#### 6.3 Deployment Preparation
**Agent Type**: Code
**Complexity**: High
**Dependencies**: All previous tasks
**Parallel**: No

**Description**: Prepare for production deployment.

**Tasks**:
1. Tag and version images
2. Update Docker Hub metadata
3. Create release notes
4. Prepare rollback plan
5. Coordinate with users

**Key Files**:
- `/docs/RELEASE_NOTES.md`
- `/docs/ROLLBACK_PLAN.md`
- `/.github/workflows/release.yml`

**Deliverables**:
- Release notes
- Deployment checklist
- Monitoring setup
- Incident response plan

**Acceptance Criteria**:
- All artifacts ready
- Release notes published
- Monitoring configured
- Team prepared

---

## Phase 7: Launch & Monitoring (Week 7-8)

### Objective
Deploy and monitor the new system.

### Tasks

#### 7.1 Canary Deployment
**Agent Type**: Deploy
**Complexity**: High
**Dependencies**: 6.3
**Parallel**: No

**Description**: Deploy to canary users and monitor.

**Process**:
1. Deploy to 10% of users
2. Monitor for 48 hours
3. Gather feedback
4. Fix critical issues
5. Expand to 50%
6. Monitor for 48 hours
7. Full rollout

**Monitoring**:
- Error rates
- Performance metrics
- User feedback
- Support tickets

**Rollback Triggers**:
- Error rate >5%
- Startup time >60s
- Critical bugs reported

---

#### 7.2 Post-Launch Support
**Agent Type**: Support
**Complexity**: Medium
**Dependencies**: 7.1
**Parallel**: No

**Description**: Provide support during launch period.

**Activities**:
- Monitor issues
- Fix bugs
- Answer questions
- Gather feedback
- Plan improvements

---

## Risk Management

### High Risk Areas

1. **Volume Strategy Change**
   - **Risk**: Breaking existing user workflows
   - **Mitigation**: Feature flags, extensive testing, clear migration guide
   - **Rollback**: Maintain old code behind flag

2. **Download Service Rewrite**
   - **Risk**: New bugs in critical functionality
   - **Mitigation**: Comprehensive testing, gradual rollout
   - **Rollback**: Keep old scripts as fallback

3. **Frontend Framework Change**
   - **Risk**: User unfamiliarity, browser compatibility
   - **Mitigation**: Browser testing, documentation
   - **Rollback**: Maintain Flask UI temporarily

### Medium Risk Areas

1. **WebSocket Reliability**
   - **Risk**: Connection drops, reconnection issues
   - **Mitigation**: Automatic reconnection, fallback to polling

2. **Build Variant Complexity**
   - **Risk**: Increased build times, cache issues
   - **Mitigation**: Parallel builds, cache optimization

3. **Performance Regression**
   - **Risk**: New system slower than old
   - **Mitigation**: Benchmarking, performance testing

---

## Verification Checkpoints

### Phase 1
- [ ] Architecture documented
- [ ] Bottlenecks identified
- [ ] Tech stack selected

### Phase 2
- [ ] Container starts <30s
- [ ] No rsync operations
- [ ] All 4 variants build

### Phase 3
- [ ] All API endpoints functional
- [ ] WebSocket connections work
- [ ] Downloads track progress

### Phase 4
- [ ] All pages render
- [ ] Real-time updates work
- [ ] Theme switching functional

### Phase 5
- [ ] All E2E tests pass
- [ ] Performance benchmarks met
- [ ] Integration complete

### Phase 6
- [ ] Documentation complete
- [ ] Release prepared
- [ ] Team ready

### Phase 7
- [ ] Canary successful
- [ ] Full rollout complete
- [ ] Monitoring stable

---

## Rollback Strategy

### Immediate Rollback (<1 hour)
1. Revert Docker tags to previous version
2. Restore old container configuration
3. Notify users of rollback

### Short-term Rollback (<24 hours)
1. Fix critical issues
2. Release patched version
3. Coordinate re-deployment

### Long-term Rollback (>1 week)
1. Keep maintenance branch for old version
2. Support migration from new to old
3. Plan new attempt with fixes

---

## Timeline Summary

| Phase | Duration | Dependencies | Parallel Tasks |
|-------|----------|--------------|----------------|
| 1. Research | 1 week | None | High |
| 2. Infrastructure | 2 weeks | Phase 1 | Medium |
| 3. Backend | 2 weeks | Phase 2 | High |
| 4. Frontend | 2 weeks | Phase 3 | Medium |
| 5. Integration | 2 weeks | Phase 3-4 | Low |
| 6. Documentation | 1 week | Phase 5 | High |
| 7. Launch | 2 weeks | Phase 6 | None |

**Total**: 12-14 weeks with aggressive parallelization
**Optimized**: 6-8 weeks with optimal parallel execution

---

## Success Criteria

### Must Have
- [ ] Container startup <30 seconds
- [ ] Unified dashboard functional
- [ ] Preset downloads working with progress
- [ ] 4 build variants available
- [ ] Native model path integration

### Should Have
- [ ] Theme system (light/dark)
- [ ] WebSocket reconnection
- [ ] Download cancellation
- [ ] Storage management UI

### Nice to Have
- [ ] Download queue management
- [ ] Bulk operations
- [ ] Export/import configuration
- [ ] Performance monitoring dashboard

---

## Appendix

### File Structure Reference

```
ComfyUI-docker/
├── backend/                    # NEW: FastAPI backend
│   ├── main.py
│   ├── api/
│   ├── models/
│   ├── services/
│   ├── web/
│   └── config/
├── frontend/                   # NEW: Frontend dashboard
│   ├── templates/
│   │   ├── components/
│   │   └── pages/
│   └── static/
│       ├── css/
│       ├── js/
│       └── assets/
├── scripts/                    # MODIFIED: Existing scripts
│   ├── start.sh
│   ├── pre_start.sh           # SIMPLIFIED
│   ├── post_start.sh          # SIMPLIFIED (no rsync)
│   ├── preset_manager/        # MIGRATED to backend
│   └── ...
├── Dockerfile                  # REWRITTEN: Multi-stage
├── docker-bake.hcl            # UPDATED: 4 variants
├── proxy/                      # UPDATED: New routes
└── docs/                       # NEW: Comprehensive docs
```

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `ACCESS_PASSWORD` | Dashboard auth | `password` |
| `ENABLE_PRESET_MANAGER` | Enable manager | `true` |
| `ENABLE_DASHBOARD` | Enable new dashboard | `true` |
| `DASHBOARD_THEME` | Default theme | `dark` |
| `PRESET_DOWNLOAD` | Video presets | empty |
| `IMAGE_PRESET_DOWNLOAD` | Image presets | empty |
| `AUDIO_PRESET_DOWNLOAD` | Audio presets | empty |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/health | Health check |
| POST | /api/auth/login | Authenticate |
| GET | /api/presets | List presets |
| GET | /api/presets/:id | Get preset |
| POST | /api/presets/:id/download | Start download |
| DELETE | /api/presets/:id | Delete preset |
| GET | /api/storage | Storage info |
| WS | /ws/downloads | Download progress |
| WS | /ws/system | System updates |

---

**Document Status**: Ready for review
**Next Steps**: Assign tasks to agents, begin Phase 1
