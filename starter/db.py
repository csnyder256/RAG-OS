"""Operational store access (Milestone M0).

SQLite, single writer. The kernel is the only process that writes; the control
CLI and the watchdog open read-only. Paths resolve at CALL time from a
module-level root, so a test can redirect the whole tree to a temp dir. A writer
that binds its path at import time cannot be isolated, and a test then quietly
mutates the real store (a real bug this pattern avoids; guide, Part C).
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

_ROOT = Path(os.environ.get("AIOS_ROOT", Path.cwd())).resolve()
_SCHEMA = Path(__file__).with_name("schema.sql")


def set_root(path) -> None:
    """Point the whole system at a different root (used by tests)."""
    global _ROOT
    _ROOT = Path(path).resolve()


def root() -> Path:
    return _ROOT


def state_dir() -> Path:
    d = _ROOT / "state"
    d.mkdir(parents=True, exist_ok=True)
    return d


def db_path() -> Path:
    return state_dir() / "os.db"


def connect(readonly: bool = False) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path(), timeout=5)
    conn.row_factory = sqlite3.Row
    if readonly:
        # query_only enforces read-only for this connection portably. A hardened
        # build might instead open with an OS-level read-only handle.
        conn.execute("PRAGMA query_only=ON")
    else:
        conn.execute("PRAGMA journal_mode=WAL")   # concurrent readers, one writer
        conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_db() -> None:
    """Idempotent: create the schema if missing. Safe on every boot."""
    conn = connect()
    try:
        conn.executescript(_SCHEMA.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()


def kstate_set(conn, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO kernel_state(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value))
    conn.commit()


def kstate_get(conn, key: str, default=None):
    row = conn.execute("SELECT value FROM kernel_state WHERE key=?", (key,)).fetchone()
    return row[0] if row else default
