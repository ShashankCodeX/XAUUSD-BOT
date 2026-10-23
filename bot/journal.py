"""A tiny trade journal stored in a local SQLite file (journal.db).

SQLite ships with Python, so there is nothing to install.
The file is listed in .gitignore, so your trades are never uploaded.
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


class Journal:
    def __init__(self, path: str | os.PathLike | None = None):
        self.path = Path(path or os.getenv("JOURNAL_DB", "journal.db"))
        with closing(self._connect()) as conn:
            with conn:
                conn.execute(
                    """CREATE TABLE IF NOT EXISTS trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        created_utc TEXT NOT NULL,
                        side TEXT NOT NULL,
                        entry REAL NOT NULL,
                        stop REAL NOT NULL,
                        target REAL NOT NULL,
                        rr REAL NOT NULL,
                        result_r REAL,
                        note TEXT NOT NULL DEFAULT ''
                    )"""
                )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def add(self, side: str, entry: float, stop: float, target: float, rr: float, note: str = "") -> int:
        with closing(self._connect()) as conn:
            with conn:
                cursor = conn.execute(
                    "INSERT INTO trades (created_utc, side, entry, stop, target, rr, note) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (datetime.now(timezone.utc).isoformat(), side, entry, stop, target, rr, note),
                )
                return int(cursor.lastrowid)

    def set_result(self, trade_id: int, result_r: float) -> bool:
        with closing(self._connect()) as conn:
            with conn:
                cursor = conn.execute(
                    "UPDATE trades SET result_r = ? WHERE id = ?", (result_r, trade_id)
                )
                return cursor.rowcount > 0

    def recent(self, limit: int = 10) -> list[sqlite3.Row]:
        with closing(self._connect()) as conn:
            return conn.execute(
                "SELECT * FROM trades ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()

    def stats(self) -> dict:
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT COUNT(result_r) AS closed, COALESCE(SUM(result_r), 0) AS total_r, "
                "COALESCE(SUM(result_r > 0), 0) AS wins FROM trades"
            ).fetchone()
        return {"closed": row["closed"], "total_r": row["total_r"], "wins": row["wins"]}
