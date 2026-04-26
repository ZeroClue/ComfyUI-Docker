# Bug Fixes & Learnings

Historical record of issues encountered and solutions. Not loaded into Claude's prompt context — see CLAUDE.md for current gotchas.

## 2026-02-22

- **Workflow format handling**: ComfyUI `/prompt` endpoint only accepts API format workflows. UI format (with `nodes` array) must be exported as API format from ComfyUI. Workflows with subgraphs (composite nodes) cannot be directly executed.
- **Strip `_meta` keys**: ComfyUI rejects workflows with `_meta` keys at root level. Strip them before sending: `{k: v for k, v in workflow.items() if not k.startswith("_")}`
- **Prompt injection**: Only replace positive prompts, preserve negative prompts. Check for "negative" in node title before replacing text in CLIPTextEncode nodes.
- **Alpine.js initialization**: Alpine must load AFTER inline script definitions. Do not use `defer` on Alpine script if it's at end of body - the inline scripts need to define functions before Alpine initializes.

## 2026-02-21

- **Subprocess security**: Always use `shutil.which()` to resolve executable paths before `subprocess.run()` - prevents shell injection
- **Semantic versioning**: Use `packaging.version.parse()` for version comparisons, not string comparison
- **SHA256 chunk size**: Use 1MB chunks (not 8KB) for hashing large model files - significantly faster
- **SHA256 validation**: Validate hash format is 64 hex characters before comparison
- **Constant extraction**: Extract repeated URLs to module-level constants (e.g., `REMOTE_REGISTRY_URL`)
- **GitHub raw content-type**: GitHub raw URLs return `text/plain; charset=utf-8` instead of `application/json`. Use `response.text()` + `json.loads()` instead of `response.json()`.
- **Alpine.js variable initialization**: Variables used in templates (modelCount, gpuUsage, memoryUsage, unreadCount) must be declared in dashboardApp() with initial values and fetched via API in fetchSidebarStats().
- **Favicon 404**: Add favicon.ico to dashboard/static/ to prevent console errors.
- **Lazy initialization for settings-dependent services**: Services like WorkflowScanner that need settings values at init time should use lazy initialization via getter functions. Module-level initialization can happen before settings are loaded, causing path resolution failures.
  ```python
  # WRONG - settings.WORKFLOW_BASE_PATH may not be set yet
  _workflow_scanner = WorkflowScanner(Path(settings.WORKFLOW_BASE_PATH))

  # CORRECT - lazy initialization
  _workflow_scanner = None
  def get_workflow_scanner():
      global _workflow_scanner
      if _workflow_scanner is None:
          _workflow_scanner = WorkflowScanner(Path(settings.WORKFLOW_BASE_PATH))
      return _workflow_scanner
  ```
- **Alpine.js null safety**: Use optional chaining (`?.`) and nullish coalescing (`||`) when accessing potentially null objects in templates:
  ```html
  <!-- WRONG - crashes if intentResult is null -->
  <span x-text="intentResult.matched_keyword"></span>

  <!-- CORRECT - safe null handling -->
  <span x-text="intentResult?.matched_keyword || ''"></span>
  ```

## 2026-02-20

- **Runtime imports for globals**: Persistence globals (`settings_manager`, `activity_logger`) are None at module load time. Import the module (`from ..core import persistence`) and access the attribute at runtime (`persistence.settings_manager`), not the variable directly.
- **FastAPI router prefixes**: Avoid duplicate prefixes. If router has `prefix="/activity"` and `include_router()` also has `prefix="/activity"`, the route becomes `/api/activity/activity/recent`. Only define prefix in one place.
- **Asyncio.Queue lazy init**: Create queues inside async context, not at class instantiation time (no event loop yet). Use property with lazy initialization.
- **Download pause bug**: When pausing download, the loop breaks but code continues to set `status="completed"`. Add explicit check for pause/cancel status before marking complete.
- **Container memory metrics**: `psutil.virtual_memory()` returns host memory in containers. Read from `/sys/fs/cgroup/memory.max` (cgroup v2) or `/sys/fs/cgroup/memory/memory.limit_in_bytes` (cgroup v1) for container limit.
- **Network volume disk metrics**: `psutil.disk_usage('/workspace')` returns host filesystem size on RunPod network volumes. Use `du -sb /workspace` for actual usage and `RUNPOD_VOLUME_GB` env var for total size.
- **add_activity() signature**: Only supports `activity_type`, `status`, `title`, `subtitle`, `details`. Does NOT support `link` parameter - will raise TypeError if passed.

## 2026-02-19

- **FastAPI route ordering**: Literal routes must come BEFORE parameterized routes. `/queue/status` must be defined before `/{preset_id}/status` or FastAPI matches `preset_id="queue"`
- **psutil.version_info**: It's a tuple, not namedtuple. Use `sys.version_info` for Python version
- **activity.py current**: `get_queue_status()` returns `current` as string (preset_id), not dict with properties

## 2026-02-18

- **psutil.uname()**: Use `.sysname` not `.system` (posix.uname_result has no 'system' attribute)
- **WebSocket endpoint**: Dashboard templates expect `/ws/dashboard`, not just `/ws`
- **Dashboard port**: Internal port 8000, external 8082 (via nginx)
- **Pydantic validation**: Preset `files` and `categories` need `Dict[str, Any]` not `Dict[str, str]` (preset YAML has boolean `optional: false` and nested category objects)

## RunPod Pod Management

**CRITICAL**: Always verify pod status after stop command:
```bash
# Stop pod
curl -X POST "https://rest.runpod.io/v1/pods/{pod-id}/stop" -H "Authorization: Bearer $RUNPOD_API_KEY"

# Verify it stopped (check desiredStatus = "EXITED")
curl -s "https://rest.runpod.io/v1/pods/{pod-id}" -H "Authorization: Bearer $RUNPOD_API_KEY"
```

### CPU Pod Debugging

CPU pods require `--cpu` flag for ComfyUI to disable GPU check:
```bash
# ComfyUI won't start on CPU pods without this flag
python main.py --cpu --listen 0.0.0.0
```

### Communication Pattern

Use ntfy for user notifications during long-running tasks:
```bash
# Send notification via MCP tool
mcp__ntfy-me-mcp-extended__ntfy_me(taskTitle="Build Complete", taskSummary="...")

# Ask question with action buttons
mcp__ntfy-me-mcp-extended__ntfy_me_ask(question="Continue?", options=["Yes", "No"])
```
