"""
SQLite database management for persistent storage
Database lives on network volume at /workspace/data/dashboard.db
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict


class Database:
    """SQLite database manager with WAL mode for concurrency"""

    def __init__(self, db_path: str = "/workspace/data/dashboard.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        """Get or create persistent connection"""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, timeout=30.0)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
        return self._conn

    def _init_db(self):
        """Initialize database schema"""
        conn = self._connect()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                status TEXT NOT NULL,
                title TEXT,
                subtitle TEXT,
                details JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_activity_created ON activity(created_at);
            CREATE INDEX IF NOT EXISTS idx_activity_type ON activity(type);

            CREATE TABLE IF NOT EXISTS download_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                preset_id TEXT NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT,
                files_completed INTEGER DEFAULT 0,
                files_total INTEGER DEFAULT 0,
                started_at TIMESTAMP,
                completed_at TIMESTAMP
            );
        """)

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a query and return cursor on the persistent connection"""
        return self._connect().execute(query, params)

    def execute_commit(self, query: str, params: tuple = ()) -> int:
        """Execute a query, commit, and return lastrowid"""
        conn = self._connect()
        cursor = conn.execute(query, params)
        conn.commit()
        return cursor.lastrowid

    def fetchone(self, query: str, params: tuple = ()) -> Optional[Dict]:
        """Fetch single row as dict"""
        row = self._connect().execute(query, params).fetchone()
        return dict(row) if row else None

    def fetchall(self, query: str, params: tuple = ()) -> List[Dict]:
        """Fetch all rows as list of dicts"""
        rows = self._connect().execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def close(self):
        """Close persistent connection"""
        if self._conn is not None:
            self._conn.close()
            self._conn = None


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
