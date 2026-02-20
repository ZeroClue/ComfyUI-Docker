# Persistent State & User Settings Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add SQLite-based persistence for user settings and activity log, enabling HuggingFace token storage and 30-day activity history.

**Architecture:** SQLite database on network volume stores settings, activity log, and download history. Settings API provides CRUD operations. Downloader uses HF token for authenticated requests. Activity logger persists all events to SQLite instead of in-memory list.

**Tech Stack:** SQLite3 (Python built-in), pydantic for validation, FastAPI endpoints, htmx UI

---

## Task 1: Database Foundation

**Files:**
- Create: `dashboard/core/database.py`

**Step 1: Create database module with connection and schema**

```python
"""
SQLite database management for persistent storage
Database lives on network volume at /workspace/data/dashboard.db
"""

import sqlite3
import asyncio
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
from datetime import datetime
import json


class Database:
    """SQLite database manager with WAL mode for concurrency"""

    def __init__(self, db_path: str = "/workspace/data/dashboard.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")

            # Settings table (key-value store)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Activity log with 30-day retention
            conn.execute("""
                CREATE TABLE IF NOT EXISTS activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    title TEXT,
                    subtitle TEXT,
                    details JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_activity_created
                ON activity(created_at)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_activity_type
                ON activity(type)
            """)

            # Download history (permanent record)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS download_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    preset_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    files_completed INTEGER DEFAULT 0,
                    files_total INTEGER DEFAULT 0,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Get database connection with proper configuration"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a query and return cursor"""
        with self._get_connection() as conn:
            return conn.execute(query, params)

    def execute_commit(self, query: str, params: tuple = (]) -> bool:
        """Execute a query and commit"""
        with self._get_connection() as conn:
            conn.execute(query, params)
            conn.commit()
            return True

    def fetchone(self, query: str, params: tuple = ()) -> Optional[Dict]:
        """Fetch single row as dict"""
        with self._get_connection() as conn:
            row = conn.execute(query, params).fetchone()
            return dict(row) if row else None

    def fetchall(self, query: str, params: tuple = ()) -> List[Dict]:
        """Fetch all rows as list of dicts"""
        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]


# Global database instance
_db: Optional[Database] = None


def get_database() -> Database:
    """Get or create database instance"""
    global _db
    if _db is None:
        _db = Database()
    return _db


def init_database():
    """Initialize database on startup"""
    return get_database()
```

**Step 2: Verify database module syntax**

Run: `python3 -c "from dashboard.core.database import Database; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add dashboard/core/database.py
git commit -m "feat: add SQLite database module with schema"
```

---

## Task 2: Settings Persistence Layer

**Files:**
- Create: `dashboard/core/persistence.py`

**Step 1: Create settings manager**

```python
"""
Persistence layer for user settings and activity logging
"""

from typing import Optional, Any, Dict, List
from datetime import datetime, timedelta
import json
from .database import get_database


class SettingsManager:
    """Manage user settings with database persistence"""

    DEFAULTS = {
        "theme": "dark",
        "hf_token": "",
        "activity_retention_days": "30",
    }

    def __init__(self):
        self.db = get_database()

    def get(self, key: str) -> Optional[str]:
        """Get a setting value"""
        row = self.db.fetchone(
            "SELECT value FROM settings WHERE key = ?",
            (key,)
        )
        if row:
            return row["value"]
        return self.DEFAULTS.get(key)

    def set(self, key: str, value: str) -> bool:
        """Set a setting value"""
        self.db.execute_commit(
            """INSERT OR REPLACE INTO settings (key, value, updated_at)
               VALUES (?, ?, ?)""",
            (key, value, datetime.utcnow().isoformat())
        )
        return True

    def get_all(self) -> Dict[str, str]:
        """Get all settings as dict"""
        rows = self.db.fetchall("SELECT key, value FROM settings")
        result = self.DEFAULTS.copy()
        for row in rows:
            result[row["key"]] = row["value"]
        return result

    def delete(self, key: str) -> bool:
        """Delete a setting"""
        self.db.execute_commit("DELETE FROM settings WHERE key = ?", (key,))
        return True

    def has_hf_token(self) -> bool:
        """Check if HF token is configured"""
        token = self.get("hf_token")
        return bool(token and token.strip())


class ActivityLogger:
    """Log activities to database with retention policy"""

    def __init__(self, retention_days: int = 30):
        self.db = get_database()
        self.retention_days = retention_days

    def log(
        self,
        activity_type: str,
        status: str,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        details: Optional[Dict] = None
    ) -> bool:
        """Log an activity event"""
        self.db.execute_commit(
            """INSERT INTO activity (type, status, title, subtitle, details, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                activity_type,
                status,
                title,
                subtitle,
                json.dumps(details) if details else None,
                datetime.utcnow().isoformat()
            )
        )
        return True

    def get_recent(self, limit: int = 50, activity_type: Optional[str] = None) -> List[Dict]:
        """Get recent activities"""
        if activity_type:
            rows = self.db.fetchall(
                """SELECT * FROM activity
                   WHERE type = ?
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (activity_type, limit)
            )
        else:
            rows = self.db.fetchall(
                "SELECT * FROM activity ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )

        # Parse details JSON
        for row in rows:
            if row.get("details"):
                try:
                    row["details"] = json.loads(row["details"])
                except json.JSONDecodeError:
                    row["details"] = None
        return rows

    def clear(self) -> int:
        """Clear all activities"""
        result = self.db.execute("DELETE FROM activity")
        return result.rowcount

    def cleanup_old(self) -> int:
        """Delete activities older than retention period"""
        cutoff = datetime.utcnow() - timedelta(days=self.retention_days)
        result = self.db.execute(
            "DELETE FROM activity WHERE created_at < ?",
            (cutoff.isoformat(),)
        )
        return result.rowcount


class DownloadHistory:
    """Track download history"""

    def __init__(self):
        self.db = get_database()

    def start(self, preset_id: str, files_total: int) -> int:
        """Record download start, return history ID"""
        self.db.execute_commit(
            """INSERT INTO download_history
               (preset_id, status, files_total, files_completed, started_at)
               VALUES (?, 'started', ?, 0, ?)""",
            (preset_id, files_total, datetime.utcnow().isoformat())
        )
        row = self.db.fetchone(
            "SELECT last_insert_rowid() as id"
        )
        return row["id"] if row else 0

    def complete(self, history_id: int, files_completed: int) -> bool:
        """Mark download as completed"""
        self.db.execute_commit(
            """UPDATE download_history
               SET status = 'completed',
                   files_completed = ?,
                   completed_at = ?
               WHERE id = ?""",
            (files_completed, datetime.utcnow().isoformat(), history_id)
        )
        return True

    def fail(self, history_id: int, error_message: str, files_completed: int = 0) -> bool:
        """Mark download as failed"""
        self.db.execute_commit(
            """UPDATE download_history
               SET status = 'failed',
                   error_message = ?,
                   files_completed = ?,
                   completed_at = ?
               WHERE id = ?""",
            (error_message, files_completed, datetime.utcnow().isoformat(), history_id)
        )
        return True

    def get_for_preset(self, preset_id: str) -> List[Dict]:
        """Get download history for a preset"""
        return self.db.fetchall(
            """SELECT * FROM download_history
               WHERE preset_id = ?
               ORDER BY started_at DESC""",
            (preset_id,)
        )


# Global instances
settings_manager: Optional[SettingsManager] = None
activity_logger: Optional[ActivityLogger] = None
download_history: Optional[DownloadHistory] = None


def init_persistence():
    """Initialize persistence layer"""
    global settings_manager, activity_logger, download_history

    from .database import init_database
    init_database()

    settings_manager = SettingsManager()
    retention_days = int(settings_manager.get("activity_retention_days") or "30")
    activity_logger = ActivityLogger(retention_days=retention_days)
    download_history = DownloadHistory()

    # Run cleanup on startup
    activity_logger.cleanup_old()

    return settings_manager, activity_logger, download_history
```

**Step 2: Verify persistence module syntax**

Run: `python3 -c "from dashboard.core.persistence import SettingsManager; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add dashboard/core/persistence.py
git commit -m "feat: add persistence layer for settings and activity"
```

---

## Task 3: Settings API Endpoints

**Files:**
- Create: `dashboard/api/settings.py`
- Modify: `dashboard/main.py`

**Step 1: Create settings API**

```python
"""
Settings API endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx

from ..core.persistence import settings_manager

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    key: str
    value: str


class HFTokenUpdate(BaseModel):
    token: str


class SettingsResponse(BaseModel):
    theme: str
    hf_token_set: bool
    activity_retention_days: int


@router.get("", response_model=SettingsResponse)
async def get_settings():
    """Get current settings (token masked)"""
    return SettingsResponse(
        theme=settings_manager.get("theme") or "dark",
        hf_token_set=settings_manager.has_hf_token(),
        activity_retention_days=int(settings_manager.get("activity_retention_days") or "30")
    )


@router.patch("")
async def update_setting(update: SettingsUpdate):
    """Update a single setting"""
    valid_keys = ["theme", "hf_token", "activity_retention_days"]
    if update.key not in valid_keys:
        raise HTTPException(400, f"Invalid setting key: {update.key}")

    settings_manager.set(update.key, update.value)
    return {"status": "ok", "key": update.key}


@router.post("/hf-token")
async def set_hf_token(data: HFTokenUpdate):
    """Set HuggingFace token"""
    token = data.token.strip()
    if not token:
        raise HTTPException(400, "Token cannot be empty")

    # Validate token format (starts with hf_)
    if not token.startswith("hf_"):
        raise HTTPException(400, "Invalid token format. Token should start with 'hf_'")

    settings_manager.set("hf_token", token)
    return {"status": "ok", "message": "Token saved"}


@router.post("/hf-token/validate")
async def validate_hf_token():
    """Validate the current HF token"""
    token = settings_manager.get("hf_token")
    if not token:
        return {"valid": False, "error": "No token configured"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://huggingface.co/api/whoami-v2",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                return {"valid": True, "username": data.get("name", "unknown")}
            else:
                return {"valid": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"valid": False, "error": str(e)}


@router.delete("/hf-token")
async def delete_hf_token():
    """Delete the HF token"""
    settings_manager.delete("hf_token")
    return {"status": "ok", "message": "Token deleted"}
```

**Step 2: Register router in main.py**

Add to `dashboard/main.py` imports:
```python
from .api.settings import router as settings_router
```

Add to `dashboard/main.py` after other router includes:
```python
app.include_router(settings_router)
```

**Step 3: Commit**

```bash
git add dashboard/api/settings.py dashboard/main.py
git commit -m "feat: add settings API endpoints with HF token validation"
```

---

## Task 4: Update Activity API

**Files:**
- Modify: `dashboard/api/activity.py`

**Step 1: Replace in-memory activity with database**

Replace the existing activity module with:

```python
"""
Activity API endpoints - persisted to database
"""

from fastapi import APIRouter
from typing import Optional, List
from pydantic import BaseModel

from ..core.persistence import activity_logger

router = APIRouter(prefix="/api/activity", tags=["activity"])


class ActivityItem(BaseModel):
    id: int
    type: str
    status: str
    title: Optional[str] = None
    subtitle: Optional[str] = None
    details: Optional[dict] = None
    created_at: str


class ActivityResponse(BaseModel):
    activities: List[ActivityItem]
    total: int


def add_activity(
    activity_type: str,
    status: str,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    details: Optional[dict] = None
):
    """Add an activity to the log (used by other modules)"""
    if activity_logger:
        activity_logger.log(
            activity_type=activity_type,
            status=status,
            title=title,
            subtitle=subtitle,
            details=details
        )


@router.get("/recent", response_model=ActivityResponse)
async def get_recent_activity(limit: int = 20, activity_type: Optional[str] = None):
    """Get recent activity from database"""
    activities = activity_logger.get_recent(limit=limit, activity_type=activity_type)
    return ActivityResponse(
        activities=[ActivityItem(**a) for a in activities],
        total=len(activities)
    )


@router.post("/clear")
async def clear_activity():
    """Clear all activity history"""
    count = activity_logger.clear()
    return {"status": "ok", "deleted": count}
```

**Step 2: Commit**

```bash
git add dashboard/api/activity.py
git commit -m "feat: replace in-memory activity with database persistence"
```

---

## Task 5: Update Downloader with HF Token

**Files:**
- Modify: `dashboard/core/downloader.py`

**Step 1: Add HF token to download requests**

In `_download_file` method, add token header. Find the `session.get()` call and replace:

```python
# Before
async with session.get(
    task.file_url,
    timeout=aiohttp.ClientTimeout(total=settings.DOWNLOAD_TIMEOUT)
) as response:

# After
headers = {}
from ..core.persistence import settings_manager
if settings_manager and settings_manager.has_hf_token():
    token = settings_manager.get("hf_token")
    headers["Authorization"] = f"Bearer {token}"

async with session.get(
    task.file_url,
    headers=headers,
    timeout=aiohttp.ClientTimeout(total=settings.DOWNLOAD_TIMEOUT)
) as response:
```

**Step 2: Add better error logging**

In the exception handler, add print statement:

```python
except Exception as e:
    task.status = "failed"
    task.error = str(e)

    # Log to console for debugging
    print(f"Download failed for {task.file_path}: {e}")

    # Broadcast error
    await broadcast_download_progress(task.preset_id, {
        "file": task.file_path,
        "status": "failed",
        "error": str(e)
    })
```

**Step 3: Commit**

```bash
git add dashboard/core/downloader.py
git commit -m "feat: add HF token auth to downloads with error logging"
```

---

## Task 6: Update Presets API for Token Check

**Files:**
- Modify: `dashboard/api/presets.py`

**Step 1: Add token check before gated download**

In the install endpoint, add check after validating preset:

```python
@router.post("/{preset_id}/install")
async def install_preset(preset_id: str, force: bool = False):
    """Install a preset by downloading its files"""

    preset = preset_cache.get_preset(preset_id)
    if not preset:
        raise HTTPException(404, f"Preset {preset_id} not found")

    # Check for HF token if preset has huggingface URLs
    from ..core.persistence import settings_manager
    has_hf_urls = any(
        "huggingface.co" in f.get("url", "")
        for f in preset.get("files", [])
    )
    if has_hf_urls and not settings_manager.has_hf_token():
        return {
            "preset_id": preset_id,
            "status": "token_required",
            "message": "This model requires a HuggingFace token"
        }

    # Continue with existing download logic...
```

**Step 2: Commit**

```bash
git add dashboard/api/presets.py
git commit -m "feat: check HF token before gated model downloads"
```

---

## Task 7: Initialize Persistence on Startup

**Files:**
- Modify: `dashboard/main.py`

**Step 1: Add initialization in lifespan**

Find the lifespan context manager and add persistence init:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting ComfyUI Unified Dashboard...")

    # Initialize database and persistence
    from .core.persistence import init_persistence
    init_persistence()
    print("Database initialized")

    # ... rest of startup

    yield

    # Shutdown
    print("Shutting down...")
```

**Step 2: Commit**

```bash
git add dashboard/main.py
git commit -m "feat: initialize database and persistence on startup"
```

---

## Task 8: Update Settings Page UI

**Files:**
- Modify: `dashboard/templates/settings.html`

**Step 1: Add settings sections to settings page**

Add after the page header:

```html
<!-- Appearance Section -->
<div class="bg-bg-secondary rounded-lg p-6 mb-6">
    <h2 class="text-xl font-semibold mb-4">Appearance</h2>

    <div class="flex items-center justify-between">
        <div>
            <label class="text-text-primary font-medium">Theme</label>
            <p class="text-text-secondary text-sm">Choose your preferred color scheme</p>
        </div>
        <div class="flex items-center gap-2"
             x-data="{ theme: localStorage.getItem('theme') || 'dark' }"
             x-init="$watch('theme', val => { localStorage.setItem('theme', val); document.documentElement.setAttribute('data-theme', val); fetch('/api/settings', { method: 'PATCH', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({key: 'theme', value: val}) }); })">
            <button @click="theme = 'dark'"
                    :class="theme === 'dark' ? 'bg-accent-primary text-white' : 'bg-bg-tertiary text-text-secondary'"
                    class="px-4 py-2 rounded-l-lg transition-colors">
                Dark
            </button>
            <button @click="theme = 'light'"
                    :class="theme === 'light' ? 'bg-accent-primary text-white' : 'bg-bg-tertiary text-text-secondary'"
                    class="px-4 py-2 rounded-r-lg transition-colors">
                Light
            </button>
        </div>
    </div>
</div>

<!-- Integrations Section -->
<div class="bg-bg-secondary rounded-lg p-6 mb-6"
     x-data="hfTokenManager()"
     x-init="init()">
    <h2 class="text-xl font-semibold mb-4">Integrations</h2>

    <div class="border-b border-border-subtle pb-6 mb-6">
        <div class="flex items-start justify-between">
            <div>
                <label class="text-text-primary font-medium">HuggingFace Token</label>
                <p class="text-text-secondary text-sm">Required for downloading gated models</p>
            </div>
            <div class="flex items-center gap-2">
                <template x-if="tokenSet && !editing">
                    <span class="text-accent-success text-sm">✓ Token configured</span>
                </template>
                <button x-show="tokenSet && !editing"
                        @click="editing = true"
                        class="text-text-secondary hover:text-text-primary text-sm">
                    Change
                </button>
            </div>
        </div>

        <div x-show="!tokenSet || editing" class="mt-4">
            <div class="flex gap-2">
                <input type="password"
                       x-model="token"
                       placeholder="hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                       class="flex-1 bg-bg-tertiary border border-border-medium rounded-lg px-4 py-2 text-text-primary placeholder-text-tertiary focus:outline-none focus:border-accent-primary">
                <button @click="validateToken()"
                        :disabled="!token || validating"
                        class="px-4 py-2 bg-bg-tertiary text-text-primary rounded-lg hover:bg-bg-hover disabled:opacity-50">
                    <span x-show="!validating">Test</span>
                    <span x-show="validating">Testing...</span>
                </button>
            </div>

            <div x-show="validationResult" class="mt-2">
                <p x-show="validationResult?.valid" class="text-accent-success text-sm">
                    ✓ Valid token for user: <span x-text="validationResult?.username"></span>
                </p>
                <p x-show="validationResult && !validationResult?.valid" class="text-accent-error text-sm">
                    ✗ Invalid token: <span x-text="validationResult?.error"></span>
                </p>
            </div>

            <div class="flex justify-between mt-4">
                <a href="https://huggingface.co/settings/tokens" target="_blank"
                   class="text-accent-primary hover:text-accent-primary/80 text-sm">
                    Get a token →
                </a>
                <div class="flex gap-2">
                    <button x-show="editing"
                            @click="cancelEdit()"
                            class="px-4 py-2 bg-bg-tertiary text-text-secondary rounded-lg hover:bg-bg-hover">
                        Cancel
                    </button>
                    <button @click="saveToken()"
                            :disabled="!token"
                            class="px-4 py-2 bg-accent-primary text-white rounded-lg hover:bg-accent-primary/80 disabled:opacity-50">
                        Save Token
                    </button>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
function hfTokenManager() {
    return {
        token: '',
        tokenSet: false,
        editing: false,
        validating: false,
        validationResult: null,

        async init() {
            const resp = await fetch('/api/settings');
            const data = await resp.json();
            this.tokenSet = data.hf_token_set;
        },

        async validateToken() {
            if (!this.token) return;

            // First save the token temporarily
            await fetch('/api/settings/hf-token', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({token: this.token})
            });

            // Then validate
            this.validating = true;
            try {
                const resp = await fetch('/api/settings/hf-token/validate');
                this.validationResult = await resp.json();
            } finally {
                this.validating = false;
            }
        },

        async saveToken() {
            if (!this.token) return;

            await fetch('/api/settings/hf-token', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({token: this.token})
            });

            this.tokenSet = true;
            this.editing = false;
            this.token = '';
        },

        cancelEdit() {
            this.editing = false;
            this.token = '';
            this.validationResult = null;
        }
    }
}
</script>
```

**Step 2: Commit**

```bash
git add dashboard/templates/settings.html
git commit -m "feat: add HF token and theme settings to settings page"
```

---

## Task 9: Add Token Required Modal

**Files:**
- Modify: `dashboard/templates/models.html`

**Step 1: Add modal component**

Add to the models page template:

```html
<!-- Token Required Modal -->
<div x-show="showTokenModal"
     x-data="{ showTokenModal: false, token: '', validating: false, error: null }"
     x-init="$root.$on('token-required', () => showTokenModal = true)"
     class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
     @click.self="showTokenModal = false">

    <div class="bg-bg-secondary rounded-xl p-6 max-w-md w-full mx-4">
        <h3 class="text-xl font-semibold mb-2">🔐 Authentication Required</h3>
        <p class="text-text-secondary mb-4">This model requires a HuggingFace token.</p>

        <div class="mb-4">
            <input type="password"
                   x-model="token"
                   placeholder="hf_xxxxxxxxxxxxxxxxxxxx"
                   class="w-full bg-bg-tertiary border border-border-medium rounded-lg px-4 py-2 text-text-primary">
            <p x-show="error" x-text="error" class="text-accent-error text-sm mt-1"></p>
        </div>

        <div class="flex justify-between items-center">
            <a href="https://huggingface.co/settings/tokens" target="_blank"
               class="text-accent-primary text-sm hover:text-accent-primary/80">
                Get a token →
            </a>
            <div class="flex gap-2">
                <button @click="showTokenModal = false"
                        class="px-4 py-2 bg-bg-tertiary text-text-secondary rounded-lg hover:bg-bg-hover">
                    Cancel
                </button>
                <button @click="saveAndRetry()"
                        :disabled="!token || validating"
                        class="px-4 py-2 bg-accent-primary text-white rounded-lg hover:bg-accent-primary/80 disabled:opacity-50">
                    <span x-show="!validating">Save & Download</span>
                    <span x-show="validating">Saving...</span>
                </button>
            </div>
        </div>
    </div>
</div>

<script>
async function saveAndRetry() {
    this.validating = true;
    this.error = null;

    try {
        // Save token
        const resp = await fetch('/api/settings/hf-token', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({token: this.token})
        });

        if (!resp.ok) {
            const data = await resp.json();
            this.error = data.detail || 'Failed to save token';
            return;
        }

        // Close modal and trigger retry
        this.showTokenModal = false;
        this.$dispatch('token-saved');
    } finally {
        this.validating = false;
    }
}
</script>
```

**Step 2: Handle token_required response in install handler**

Update the install button click handler to check for `token_required` status:

```javascript
async function installPreset(presetId) {
    const resp = await fetch(`/api/presets/${presetId}/install`, { method: 'POST' });
    const data = await resp.json();

    if (data.status === 'token_required') {
        // Show token modal
        this.$dispatch('token-required');
        return;
    }

    // Continue with normal flow...
}
```

**Step 3: Commit**

```bash
git add dashboard/templates/models.html
git commit -m "feat: add HF token required modal for gated models"
```

---

## Task 10: Integration Testing

**Files:**
- None (testing only)

**Step 1: Build and push test image**

```bash
docker buildx bake base-12-8 --push
```

**Step 2: Deploy test pod**

```bash
source .runpod/.env && curl -s -X POST "https://rest.runpod.io/v1/pods" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "comfyui-test-persistence",
    "imageName": "zeroclue/comfyui:base-py3.13-cu128",
    "computeType": "GPU",
    "gpuTypeIds": ["NVIDIA RTX 2000 Ada Generation"],
    "dataCenterIds": ["EU-RO-1"],
    "volumeInGb": 100,
    "networkVolumeId": "36dwuaj8dv",
    "ports": ["3000/http", "8082/http", "22/tcp"],
    "supportPublicIp": true
  }'
```

**Step 3: Test checklist**

- [ ] Settings page loads at `/settings`
- [ ] Theme toggle works and persists on refresh
- [ ] HF token can be saved and validated
- [ ] Activity log persists across page navigation
- [ ] Download fails gracefully without token for gated models
- [ ] Download succeeds with valid token
- [ ] Activity log survives pod restart

**Step 4: Final commit**

```bash
git add -A
git commit -m "feat: complete persistent state and user settings implementation"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Database foundation | `dashboard/core/database.py` |
| 2 | Persistence layer | `dashboard/core/persistence.py` |
| 3 | Settings API | `dashboard/api/settings.py`, `dashboard/main.py` |
| 4 | Activity API update | `dashboard/api/activity.py` |
| 5 | Downloader HF token | `dashboard/core/downloader.py` |
| 6 | Presets token check | `dashboard/api/presets.py` |
| 7 | Startup init | `dashboard/main.py` |
| 8 | Settings page UI | `dashboard/templates/settings.html` |
| 9 | Token modal | `dashboard/templates/models.html` |
| 10 | Integration testing | Deploy & verify |
