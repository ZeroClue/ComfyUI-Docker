# Persistent State & User Settings Design

**Date:** 2026-02-20
**Status:** Approved
**Scope:** Dashboard state persistence, user settings, HuggingFace authentication

## Problem Statement

The Unified Dashboard currently stores all state in memory:
- Download queue status is lost on page navigation
- Activity history resets on pod restart
- User settings (e.g., HuggingFace token) cannot be persisted
- Gated HuggingFace models fail with 401 Unauthorized

## Solution Overview

Add SQLite-based persistence on the network volume (`/workspace/data/dashboard.db`) to store:
1. User settings (HuggingFace token, theme preference)
2. Full activity log with 30-day retention
3. Download history

## Storage Architecture

### Database Location

```
/workspace/
├── data/
│   └── dashboard.db      # SQLite database (new)
├── config/
│   └── presets.yaml      # Existing preset definitions
├── models/               # Existing model files
└── logs/                 # Existing logs
```

### Database Schema

```sql
-- User settings (key-value store)
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Activity log (30-day retention)
CREATE TABLE activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,           -- 'download', 'generation', 'error'
    status TEXT NOT NULL,         -- 'completed', 'failed', 'started'
    title TEXT,
    subtitle TEXT,
    details JSON,                 -- Flexible metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_activity_created ON activity(created_at);
CREATE INDEX idx_activity_type ON activity(type);

-- Download history (permanent record)
CREATE TABLE download_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    preset_id TEXT NOT NULL,
    status TEXT NOT NULL,         -- 'completed', 'failed', 'cancelled'
    error_message TEXT,
    files_completed INTEGER DEFAULT 0,
    files_total INTEGER DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

### Why SQLite?

| Requirement | SQLite | JSON/YAML |
|-------------|--------|-----------|
| 30-day auto-cleanup | Efficient SQL DELETE | Load, filter, rewrite entire file |
| User clears history | Instant TRUNCATE | Rewrite entire file |
| Query by type/date | Indexed queries | Linear scan |
| Atomic writes | Built-in ACID | Risk of corruption on crash |
| Dependencies | Python built-in | Python built-in |

## User Settings

### Settings Page (`/settings`)

Two sections:

| Section | Fields |
|---------|--------|
| **Appearance** | Theme toggle (dark/light) |
| **Integrations** | HuggingFace token (masked input, test button) |

### HuggingFace Token Prompt

Modal triggered when user installs a gated model without token:

```
┌─────────────────────────────────────────────┐
│  🔐 Authentication Required                 │
│                                             │
│  This model requires a HuggingFace token.   │
│                                             │
│  [hf_xxxxxxxxxxxxxxxxxxxx     ] [Test]      │
│                                             │
│  Don't have a token? [Get one here →]       │
│                                             │
│  [Cancel]              [Save & Download]    │
└─────────────────────────────────────────────┘
```

### Token Usage

Added as `Authorization: Bearer {token}` header to download requests.

### Token Validation

HEAD request to `https://huggingface.co/api/whoami-v2` with Bearer token to validate before saving.

## Activity Log

### Event Types

| Event | type | status | Example |
|-------|------|--------|---------|
| Download started | `download` | `started` | Model FLUX_DEV_BASIC |
| Download completed | `download` | `completed` | Model FLUX_DEV_BASIC |
| Download failed | `download` | `failed` | Model WAN22_NSFW_LORA |
| Generation started | `generation` | `started` | Workflow xyz.json |
| Generation completed | `generation` | `completed` | 4 images generated |
| Error | `error` | `failed` | API timeout |

### Retention Policy

- **30-day retention** - Records older than 30 days are auto-deleted
- **Auto-cleanup** runs on:
  - Dashboard startup
  - Daily background task
- **Manual clear** - User can clear via "Clear History" button

### API Endpoint

```
POST /api/activity/clear
```

Truncates activity table.

## Download Queue Behavior

### Pod Restart

Interrupted downloads are **not resumed**:
- Downloads in progress are marked as "failed"
- User manually retries after restart

This keeps implementation simple without partial file handling complexity.

## Implementation Components

### New Files

| File | Purpose |
|------|---------|
| `dashboard/core/database.py` | SQLite connection, schema init, CRUD helpers |
| `dashboard/core/persistence.py` | Settings manager, activity logger |
| `dashboard/api/settings.py` | Settings CRUD endpoints |
| `dashboard/templates/settings.html` | Updated settings page UI |

### Modified Files

| File | Changes |
|------|---------|
| `dashboard/core/downloader.py` | Add HF token header, log to SQLite |
| `dashboard/api/activity.py` | Read from SQLite instead of in-memory |
| `dashboard/api/presets.py` | Check for HF token before gated downloads |
| `dashboard/main.py` | Init database on startup, run cleanup |
| `dashboard/core/config.py` | Add `HF_TOKEN` env var fallback |

### Startup Sequence

1. Initialize SQLite database (create tables if not exist)
2. Load settings from DB (or env vars as fallback)
3. Run retention cleanup (delete old activity)
4. Start dashboard

## Error Handling

| Scenario | Handling |
|----------|----------|
| **DB locked** | SQLite WAL mode + retry with backoff |
| **Corrupt DB** | Auto-recreate tables, log warning, reset to defaults |
| **Invalid HF token** | Test button validates before saving |
| **Token revoked later** | Download fails with 401, prompt modal reappears |
| **Pod crash mid-write** | SQLite transactions ensure atomicity |
| **First run** | Tables created automatically, defaults applied |

## Scope

- **Single-user** - One set of settings per pod
- **No multi-user support** - Can be added later if needed
- **No download resume** - Interrupted downloads marked as failed
