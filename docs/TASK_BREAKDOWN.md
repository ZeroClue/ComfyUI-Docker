# ComfyUI-Docker Revolutionary Rebuild: Task Breakdown

**Companion to**: IMPLEMENTATION_ROADMAP.md
**Purpose**: Agent-executable task list with clear acceptance criteria
**Format**: JSON-ready for task management systems

---

## Task Catalog

### PHASE 1: RESEARCH & ANALYSIS

#### T1.1 - Architecture Documentation
```json
{
  "id": "T1.1",
  "name": "Document Current Architecture",
  "phase": 1,
  "complexity": "low",
  "agent_type": "Explore",
  "estimated_hours": 8,
  "dependencies": [],
  "deliverables": [
    "docs/ARCHITECTURE_CURRENT.md",
    "docs/SERVICE_DEPENDENCIES.md",
    "docs/DATA_FLOWS.md"
  ],
  "acceptance_criteria": [
    "All services documented (ComfyUI, Preset Manager, Code Server, Jupyter, Nginx)",
    "All environment variables catalogued",
    "All volume mounts documented",
    "All inter-service communications mapped"
  ],
  "verification": "python scripts/validate_architecture_docs.py"
}
```

#### T1.2 - Bottleneck Analysis
```json
{
  "id": "T1.2",
  "name": "Analyze rsync Bottleneck",
  "phase": 1,
  "complexity": "medium",
  "agent_type": "Explore",
  "estimated_hours": 12,
  "dependencies": ["T1.1"],
  "key_files": [
    "scripts/post_start.sh",
    "Dockerfile",
    "scripts/start.sh"
  ],
  "deliverables": [
    "docs/BOTTLENECK_ANALYSIS.md",
    "scripts/profile_sync.py"
  ],
  "focus_areas": [
    "scripts/post_start.sh:34-72 (venv_sync)",
    "scripts/post_start.sh:166-229 (comfyui_sync)",
    "Network volume performance characteristics",
    "Alternative sync strategies"
  ],
  "acceptance_criteria": [
    "Exact time per rsync operation documented",
    "Alternative strategies evaluated",
    "Implementation recommendation with projections"
  ]
}
```

#### T1.3 - Technology Research
```json
{
  "id": "T1.3",
  "name": "Research Dashboard Technologies",
  "phase": 1,
  "complexity": "low",
  "agent_type": "Explore",
  "estimated_hours": 8,
  "dependencies": [],
  "research_areas": [
    "htmx patterns and limitations",
    "Alpine.js reactivity patterns",
    "Tailwind CSS theming",
    "FastAPI WebSocket patterns",
    "Docker multi-stage caching"
  ],
  "deliverables": [
    "docs/TECH_STACK_RESEARCH.md",
    "docs/HTMX_PATTERNS.md",
    "docs/DESIGN_SYSTEM.md"
  ]
}
```

---

### PHASE 2: INFRASTRUCTURE

#### T2.1 - Volume Strategy Redesign
```json
{
  "id": "T2.1",
  "name": "Eliminate rsync with Volume Redesign",
  "phase": 2,
  "complexity": "high",
  "agent_type": "Code",
  "estimated_hours": 24,
  "dependencies": ["T1.1", "T1.2"],
  "key_files": [
    "Dockerfile",
    "scripts/post_start.sh"
  ],
  "changes": [
    {
      "file": "Dockerfile",
      "line": 46,
      "from": "WORKDIR /",
      "to": "WORKDIR /workspace"
    },
    {
      "file": "Dockerfile",
      "line": 84,
      "action": "Install ComfyUI directly to /workspace/ComfyUI"
    },
    {
      "file": "Dockerfile",
      "line": 68,
      "action": "Create venv directly at /workspace/venv"
    },
    {
      "file": "scripts/post_start.sh",
      "lines": "34-72, 166-229",
      "action": "Remove all rsync logic"
    }
  ],
  "new_structure": {
    "workspace": {
      "ComfyUI": "Installed directly, no sync",
      "venv": "Created directly, no sync",
      "config": "Configuration",
      "models": "Symlink to ComfyUI/models",
      "logs": "Runtime logs"
    }
  },
  "deliverables": [
    "Modified Dockerfile",
    "Modified scripts/post_start.sh",
    "docs/VOLUME_ARCHITECTURE.md",
    "tests/test_volume_setup.py"
  ],
  "acceptance_criteria": [
    "Container starts in <30 seconds on fresh volume",
    "No rsync operations in any startup script",
    "All paths reference /workspace directly",
    "Backward compatibility maintained"
  ],
  "verification": [
    "time docker run --rm zeroclue/comfyui:test-volume-strategy",
    "docker exec <container> ls -la /workspace/",
    "docker exec <container> test -f /workspace/venv/.sync_complete && echo FAIL || echo PASS"
  ],
  "rollback": {
    "branch": "feature/volume-redesign",
    "feature_flag": "USE_NEW_VOLUME_STRATEGY"
  }
}
```

#### T2.2 - Multi-Stage Dockerfile
```json
{
  "id": "T2.2",
  "name": "Refactor Dockerfile for 4 Variants",
  "phase": 2,
  "complexity": "high",
  "agent_type": "Code",
  "estimated_hours": 32,
  "dependencies": ["T2.1"],
  "key_files": [
    "Dockerfile",
    "docker-bake.hcl",
    ".github/workflows/build.yml"
  ],
  "stages": [
    "base - Common dependencies",
    "builder - Compilation (PyTorch, nodes)",
    "minimal-runtime - ComfyUI + Manager only",
    "standard-runtime - minimal + common nodes",
    "full-runtime - standard + extra nodes",
    "dev-runtime - full + dev tools"
  ],
  "variants": [
    {"name": "minimal", "size_gb": 4, "components": ["ComfyUI", "Manager"]},
    {"name": "standard", "size_gb": 6, "components": ["minimal", "common nodes"]},
    {"name": "full", "size_gb": 10, "components": ["standard", "extra nodes"]},
    {"name": "dev", "size_gb": 12, "components": ["full", "code-server", "jupyter"]}
  ],
  "deliverables": [
    "New multi-stage Dockerfile",
    "Updated docker-bake.hcl",
    "docs/BUILD_VARIANTS.md"
  ],
  "acceptance_criteria": [
    "4 distinct build variants",
    "All variants build successfully",
    "Image sizes within targets",
    "All CUDA versions build"
  ],
  "verification": "docker buildx bake minimal-12-6 standard-12-6 full-12-6 dev-12-6"
}
```

#### T2.3 - Model Paths Integration
```json
{
  "id": "T2.3",
  "name": "Native extra_model_paths.yaml Integration",
  "phase": 2,
  "complexity": "medium",
  "agent_type": "Code",
  "estimated_hours": 12,
  "dependencies": ["T2.1"],
  "key_files": [
    "scripts/generate_extra_paths.py",
    "scripts/post_start.sh"
  ],
  "enhancements": [
    "Auto-generate on container start",
    "Detect custom mounts",
    "Validate paths before ComfyUI start",
    "Runtime path updates"
  ],
  "deliverables": [
    "Enhanced scripts/generate_extra_paths.py",
    "Auto-generation on startup",
    "docs/MODEL_PATHS.md"
  ],
  "verification": [
    "docker exec <container> cat /workspace/ComfyUI/extra_model_paths.yaml",
    "docker run -v /custom/models:/models zeroclue/comfyui:latest && docker exec <container> grep /models /workspace/ComfyUI/extra_model_paths.yaml"
  ]
}
```

---

### PHASE 3: BACKEND SERVICES

#### T3.1 - FastAPI Skeleton
```json
{
  "id": "T3.1",
  "name": "Create FastAPI Application",
  "phase": 3,
  "complexity": "medium",
  "agent_type": "Code",
  "estimated_hours": 16,
  "dependencies": ["T2.1", "T2.2"],
  "structure": {
    "backend": [
      "main.py",
      "api/__init__.py",
      "api/presets.py",
      "api/storage.py",
      "api/downloads.py",
      "api/system.py",
      "api/auth.py",
      "models/preset.py",
      "models/download.py",
      "models/system.py",
      "services/preset_manager.py",
      "services/downloader.py",
      "services/path_manager.py",
      "services/websocket_manager.py",
      "web/socket.py",
      "config/settings.py"
    ]
  },
  "features": [
    "JWT authentication",
    "CORS configuration",
    "Request/response logging",
    "OpenAPI docs at /docs"
  ],
  "deliverables": [
    "Complete FastAPI structure",
    "docs/API_ARCHITECTURE.md",
    "tests/test_api.py"
  ],
  "acceptance_criteria": [
    "FastAPI runs on port 8000",
    "All endpoints return JSON",
    "Authentication functional",
    "WebSocket connections accepted",
    "OpenAPI docs accessible"
  ]
}
```

#### T3.2 - Preset API
```json
{
  "id": "T3.2",
  "name": "Implement Preset Management API",
  "phase": 3,
  "complexity": "high",
  "agent_type": "Code",
  "estimated_hours": 24,
  "dependencies": ["T3.1"],
  "endpoints": [
    "GET /api/presets - List all",
    "GET /api/presets/:id - Get details",
    "POST /api/presets/:id/download - Start download",
    "DELETE /api/presets/:id - Delete files",
    "GET /api/presets/:id/status - Get status",
    "POST /api/presets/update - Update definitions",
    "GET /api/presets/categories - List categories"
  ],
  "migration": {
    "from": "scripts/preset_manager/core.py",
    "to": "backend/services/preset_manager.py",
    "preserve": "All existing ModelManager logic"
  },
  "deliverables": [
    "Complete preset API",
    "Request/response models",
    "Error handling",
    "tests/test_presets_api.py"
  ],
  "acceptance_criteria": [
    "All endpoints functional",
    "Existing logic integrated",
    "Progress via WebSocket",
    "File validation",
    "Error recovery"
  ]
}
```

#### T3.3 - Download Service
```json
{
  "id": "T3.3",
  "name": "Rewrite Download Service",
  "phase": 3,
  "complexity": "high",
  "agent_type": "Code",
  "estimated_hours": 32,
  "dependencies": ["T3.2"],
  "current_issues": [
    "scripts/unified_preset_downloader.py - generates temp scripts",
    "scripts/preset_manager/web_interface.py:495-632 - complex threads",
    "No cancellation support",
    "Limited progress reporting"
  ],
  "new_implementation": {
    "file": "backend/services/downloader.py",
    "methods": [
      "download_preset(preset_id) -> DownloadTask",
      "cancel_download(task_id) -> bool",
      "get_progress(task_id) -> DownloadProgress",
      "retry_failed(task_id) -> bool"
    ]
  },
  "features": [
    "Async download",
    "Per-file progress",
    "Cancellation",
    "Auto-retry (3x with exponential backoff)",
    "Parallel queue (max 4)"
  ],
  "deliverables": [
    "Async download service",
    "tests/test_downloader.py"
  ],
  "acceptance_criteria": [
    "Byte-level progress",
    "Cancellation works",
    "Auto-retry functional",
    "Parallel downloads",
    "WebSocket broadcasts"
  ]
}
```

#### T3.4 - WebSocket Manager
```json
{
  "id": "T3.4",
  "name": "Implement WebSocket Progress Broadcasting",
  "phase": 3,
  "complexity": "medium",
  "agent_type": "Code",
  "estimated_hours": 16,
  "dependencies": ["T3.3"],
  "channels": [
    "/ws/downloads - All download progress",
    "/ws/downloads/{id} - Specific download",
    "/ws/storage - Storage updates",
    "/ws/system - System status"
  ],
  "features": [
    "Multiple clients per channel",
    "<100ms latency",
    "Authentication required",
    "Graceful disconnect",
    "Auto-reconnection"
  ],
  "deliverables": [
    "WebSocket manager",
    "Connection handling",
    "tests/test_websockets.py"
  ]
}
```

---

### PHASE 4: FRONTEND DASHBOARD

#### T4.1 - Design System
```json
{
  "id": "T4.1",
  "name": "Implement Tailwind Design System",
  "phase": 4,
  "complexity": "medium",
  "agent_type": "Code",
  "estimated_hours": 12,
  "dependencies": ["T1.3"],
  "design_tokens": {
    "colors": ["primary", "secondary", "success", "warning", "danger"],
    "backgrounds": ["bg-primary", "bg-secondary"],
    "text": ["text-primary", "text-secondary"]
  },
  "themes": ["dark (default)", "light", "high-contrast"],
  "deliverables": [
    "Tailwind configuration",
    "Custom CSS variables",
    "Theme system",
    "Component library",
    "docs/DESIGN_SYSTEM.md"
  ],
  "acceptance_criteria": [
    "3 themes available",
    "Consistent spacing/typography",
    "WCAG AA compliant",
    "Responsive",
    "Dark default"
  ]
}
```

#### T4.2 - Layout Components
```json
{
  "id": "T4.2",
  "name": "Build Layout Components",
  "phase": 4,
  "complexity": "medium",
  "agent_type": "Code",
  "estimated_hours": 20,
  "dependencies": ["T4.1"],
  "components": [
    "Sidebar navigation",
    "Top bar with search",
    "Main content area",
    "Modal system",
    "Toast notifications",
    "Loading states"
  ],
  "technologies": {
    "htmx": "Dynamic content loading",
    "alpine": "Component reactivity"
  },
  "deliverables": [
    "All layout components",
    "Component docs",
    "Storybook examples",
    "tests/test_components.js"
  ],
  "acceptance_criteria": [
    "All responsive",
    "htmx configured",
    "Alpine reactive",
    "Keyboard navigation",
    "ARIA labels"
  ]
}
```

#### T4.3 - Dashboard Pages
```json
{
  "id": "T4.3",
  "name": "Implement Dashboard Pages",
  "phase": 4,
  "complexity": "high",
  "agent_type": "Code",
  "estimated_hours": 32,
  "dependencies": ["T4.2"],
  "pages": [
    {
      "name": "Overview Dashboard",
      "features": ["System stats", "Storage overview", "Recent activity"]
    },
    {
      "name": "Preset Browser",
      "features": ["Filterable list", "Category nav", "Search", "Bulk ops"]
    },
    {
      "name": "Preset Detail",
      "features": ["Model info", "Download progress", "File list"]
    },
    {
      "name": "Storage Manager",
      "features": ["Usage breakdown", "Unknown models", "Cleanup tools"]
    },
    {
      "name": "Settings",
      "features": ["Config", "Themes", "Preferences", "System info"]
    }
  ],
  "deliverables": [
    "All 5 pages",
    "Page transitions",
    "Loading/error states",
    "tests/test_pages.js"
  ],
  "acceptance_criteria": [
    "All pages accessible",
    "Data loads from API",
    "Loading states shown",
    "Errors graceful",
    "Back button works"
  ]
}
```

#### T4.4 - Progress Components
```json
{
  "id": "T4.4",
  "name": "Build Real-time Progress Components",
  "phase": 4,
  "complexity": "medium",
  "agent_type": "Code",
  "estimated_hours": 16,
  "dependencies": ["T4.3", "T3.4"],
  "components": [
    "Download queue display",
    "Per-file progress bars",
    "Speed/ETA calculations",
    "Cancellation buttons",
    "Retry controls"
  ],
  "deliverables": [
    "Progress components",
    "Auto-reconnection",
    "Queue UI",
    "Download history",
    "tests/test_progress.js"
  ],
  "acceptance_criteria": [
    "Updates <500ms",
    "Multiple downloads shown",
    "Cancellation instant",
    "Reconnection auto",
    "Speed calculated"
  ]
}
```

---

### PHASE 5: INTEGRATION

#### T5.1 - Nginx Config
```json
{
  "id": "T5.1",
  "name": "Update Nginx Configuration",
  "phase": 5,
  "complexity": "medium",
  "agent_type": "Code",
  "estimated_hours": 8,
  "dependencies": ["T3.1", "T4.1"],
  "routes": [
    {"port": 3001, "service": "ComfyUI", "existing": true},
    {"port": 8081, "service": "Code Server", "existing": true},
    {"port": 8889, "service": "Jupyter", "existing": true},
    {"port": 8001, "service": "Dashboard", "existing": false}
  ],
  "deliverables": [
    "Updated nginx.conf",
    "WebSocket proxy",
    "Static file serving",
    "docs/NGINX_CONFIG.md"
  ]
}
```

#### T5.2 - Startup Scripts
```json
{
  "id": "T5.2",
  "name": "Integrate Dashboard Startup",
  "phase": 5,
  "complexity": "medium",
  "agent_type": "Code",
  "estimated_hours": 12,
  "dependencies": ["T3.1", "T5.1"],
  "changes": [
    {
      "file": "scripts/start.sh",
      "add": "start_dashboard() function"
    }
  ],
  "deliverables": [
    "Updated start.sh",
    "Health check",
    "Graceful shutdown",
    "Log management"
  ]
}
```

#### T5.3 - E2E Testing
```json
{
  "id": "T5.3",
  "name": "End-to-End Testing",
  "phase": 5,
  "complexity": "high",
  "agent_type": "Code",
  "estimated_hours": 40,
  "dependencies": ["All previous tasks"],
  "test_areas": [
    "Container startup (<30s)",
    "Preset management (CRUD)",
    "Storage management",
    "Dashboard UI navigation",
    "Theme switching",
    "Download progress"
  ],
  "tools": ["pytest", "playwright", "docker-compose"],
  "deliverables": [
    "Complete E2E suite",
    "Coverage report (>80%)",
    "Performance benchmarks",
    "CI/CD integration"
  ]
}
```

#### T5.4 - Performance Benchmarking
```json
{
  "id": "T5.4",
  "name": "Performance Benchmarking",
  "phase": 5,
  "complexity": "medium",
  "agent_type": "Code",
  "estimated_hours": 16,
  "dependencies": ["T5.3"],
  "metrics": [
    "Startup time",
    "TTFB",
    "API response times",
    "WebSocket latency",
    "Download speeds",
    "Memory usage",
    "CPU usage"
  ],
  "targets": {
    "startup": "<30s",
    "api_p95": "<100ms",
    "websocket": "<50ms",
    "memory_idle": "<4GB"
  },
  "deliverables": [
    "Baseline report",
    "Regression tests",
    "Monitoring dashboard",
    "docs/PERFORMANCE_BASELINES.md"
  ]
}
```

---

### PHASE 6: DOCUMENTATION

#### T6.1 - User Documentation
```json
{
  "id": "T6.1",
  "name": "Write User Documentation",
  "phase": 6,
  "complexity": "medium",
  "agent_type": "Write",
  "estimated_hours": 24,
  "dependencies": ["T5.3"],
  "documents": [
    "Quick Start Guide",
    "Dashboard User Guide",
    "Preset Management Guide",
    "Troubleshooting Guide",
    "Migration Guide"
  ],
  "deliverables": [
    "docs/USER_GUIDE.md",
    "docs/QUICKSTART.md",
    "docs/TROUBLESHOOTING.md",
    "docs/MIGRATION.md",
    "Screenshots/diagrams",
    "FAQ"
  ]
}
```

#### T6.2 - API Documentation
```json
{
  "id": "T6.2",
  "name": "Complete API Documentation",
  "phase": 6,
  "complexity": "low",
  "agent_type": "Write",
  "estimated_hours": 12,
  "dependencies": ["T3.1"],
  "deliverables": [
    "docs/API_REFERENCE.md",
    "OpenAPI spec",
    "Postman collection",
    "Error code docs",
    "Authentication guide"
  ]
}
```

#### T6.3 - Deployment Preparation
```json
{
  "id": "T6.3",
  "name": "Prepare for Deployment",
  "phase": 6,
  "complexity": "high",
  "agent_type": "Code",
  "estimated_hours": 16,
  "dependencies": ["All previous tasks"],
  "tasks": [
    "Tag and version images",
    "Update Docker Hub metadata",
    "Create release notes",
    "Rollback plan",
    "Coordinate with users"
  ],
  "deliverables": [
    "docs/RELEASE_NOTES.md",
    "docs/ROLLBACK_PLAN.md",
    ".github/workflows/release.yml",
    "Deployment checklist"
  ]
}
```

---

### PHASE 7: LAUNCH

#### T7.1 - Canary Deployment
```json
{
  "id": "T7.1",
  "name": "Canary Deployment",
  "phase": 7,
  "complexity": "high",
  "agent_type": "Deploy",
  "estimated_hours": 40,
  "dependencies": ["T6.3"],
  "stages": [
    {"percentage": 10, "duration": "48h", "action": "Monitor and fix"},
    {"percentage": 50, "duration": "48h", "action": "Monitor and fix"},
    {"percentage": 100, "duration": "ongoing", "action": "Full support"}
  ],
  "monitoring": [
    "Error rates",
    "Performance metrics",
    "User feedback",
    "Support tickets"
  ],
  "rollback_triggers": [
    "Error rate >5%",
    "Startup time >60s",
    "Critical bugs"
  ]
}
```

#### T7.2 - Post-Launch Support
```json
{
  "id": "T7.2",
  "name": "Post-Launch Support",
  "phase": 7,
  "complexity": "medium",
  "agent_type": "Support",
  "estimated_hours": "ongoing",
  "dependencies": ["T7.1"],
  "activities": [
    "Monitor issues",
    "Fix bugs",
    "Answer questions",
    "Gather feedback",
    "Plan improvements"
  ]
}
```

---

## Execution Order

### Week 1 (Parallel)
- T1.1, T1.2, T1.3

### Week 2-3 (Sequential within phase)
- T2.1 → T2.2, T2.3 (parallel after T2.1)

### Week 3-4 (Sequential within phase)
- T3.1 → T3.2 → T3.3, T3.4 (parallel)

### Week 4-5 (Sequential within phase)
- T4.1 → T4.2 → T4.3, T4.4 (parallel)

### Week 5-6 (Integration)
- T5.1, T5.2 (parallel) → T5.3 → T5.4

### Week 6-7 (Documentation)
- T6.1, T6.2 (parallel) → T6.3

### Week 7-8 (Launch)
- T7.1 → T7.2

---

## Summary

- **Total Tasks**: 23
- **Total Estimated Hours**: ~432 hours
- **Critical Path**: T2.1 → T2.2 → T3.1 → T3.2 → T3.3 → T4.3 → T5.3 → T6.3 → T7.1
- **Maximum Parallelization**: Weeks 1, 3-4, 4, 6
- **Timeline**: 6-8 weeks with optimal parallel execution
