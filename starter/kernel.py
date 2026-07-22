"""The zero-context kernel (Milestone M1).

A small always-on process that holds no model context. In this scaffold it does
the lifecycle only: acquire a single-instance lock, reconcile on boot, then tick,
writing a heartbeat each tick, until a stop sentinel appears. Later milestones
hang the scheduler, the worker pool, and routing off this same loop.

Run it directly:  python kernel.py
Stop it cleanly:  python osctl.py stop
"""
from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path

import db
import oplog
import proc

TICK_SECONDS = 2.0


def pid_file() -> Path:
    return db.state_dir() / "kernel.pid"


def stop_file() -> Path:
    return db.state_dir() / "daemon.stop"


def acquire_lock() -> bool:
    """Single instance. If a live kernel with a different pid already holds the
    lock, refuse. A stale lock (its pid is not alive) is taken over. Returns
    True if we now own the lock."""
    pf = pid_file()
    if pf.exists():
        try:
            other = int(pf.read_text().strip() or "0")
        except ValueError:
            other = 0
        if other and other != os.getpid() and proc.pid_alive(other):
            return False
    pf.write_text(str(os.getpid()))
    return True


def release_lock() -> None:
    try:
        if pid_file().exists() and pid_file().read_text().strip() == str(os.getpid()):
            pid_file().unlink()
    except OSError:
        pass


def reconcile_on_boot(conn) -> None:
    """Hook for boot reconciliation (orphaned jobs, expired approvals). Nothing
    to reconcile yet; recorded so the seam exists from day one."""
    oplog.emit("boot_reconcile", note="no orphaned work at M1")


async def tick_loop() -> None:
    conn = db.connect()
    try:
        db.kstate_set(conn, "pid", str(os.getpid()))
        db.kstate_set(conn, "boot_at", str(time.time()))
        reconcile_on_boot(conn)
        oplog.emit("kernel_start", pid=os.getpid())
        while not stop_file().exists():
            db.kstate_set(conn, "heartbeat", str(time.time()))
            await asyncio.sleep(TICK_SECONDS)
        oplog.emit("kernel_stop", reason="stop sentinel")
    finally:
        conn.close()
        release_lock()


def main() -> int:
    db.init_db()
    if not acquire_lock():
        print("another kernel instance is already running; exiting", file=sys.stderr)
        return 3
    # A stale stop sentinel from a previous clean shutdown must not kill this run.
    if stop_file().exists():
        stop_file().unlink()
    try:
        asyncio.run(tick_loop())
    except KeyboardInterrupt:
        oplog.emit("kernel_stop", reason="keyboard interrupt")
        release_lock()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
