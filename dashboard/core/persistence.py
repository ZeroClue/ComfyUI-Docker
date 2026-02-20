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
