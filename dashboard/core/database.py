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

    def execute_commit(self, query: str, params: tuple = ()) -> bool:
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
