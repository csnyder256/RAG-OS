"""Independent watchdog (Milestone M1).

Runs out of band, either one-shot from the OS scheduler every minute, or with
--loop for a live demo. If the kernel's heartbeat is stale or its pid is dead,
and no intentional stop sentinel is present, it relaunches the kernel. This is
what makes a wedged or crashed kernel self-heal without a human. A wedged event
loop can hold the process open while the heartbeat goes stale, which is exactly
the case the pid check alone would miss.

One-shot (for cron / Task Scheduler / systemd timer):  python watchdog.py
Live demo:                                             python watchdog.py --loop
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import db
import oplog
import proc

STALE_SECONDS = 20.0                      # heartbeat older than this => presumed dead
KERNEL = Path(__file__).with_name("kernel.py")


def _kstate(key: str):
    if not db.db_path().exists():
        return None
    try:
        conn = db.connect(readonly=True)
    except Exception:
        return None
    try:
        row = conn.execute("SELECT value FROM kernel_state WHERE key=?", (key,)).fetchone()
        return row[0] if row else None
    except Exception:
        return None
    finally:
        conn.close()


def stop_present() -> bool:
    return (db.state_dir() / "daemon.stop").exists()


def kernel_healthy() -> bool:
    pid = _kstate("pid")
    hb = _kstate("heartbeat")
    if not pid or not hb:
        return False
    try:
        age = time.time() - float(hb)
    except (TypeError, ValueError):
        return False
    return proc.pid_alive(int(pid)) and age < STALE_SECONDS


def revive() -> None:
    oplog.emit("watchdog_revive", note="kernel unhealthy, relaunching")
    kwargs = {}
    if sys.platform == "win32":
        # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        kwargs["creationflags"] = 0x00000008 | 0x00000200
    else:
        kwargs["start_new_session"] = True
    subprocess.Popen([sys.executable, str(KERNEL)], **kwargs)


def check_once() -> str:
    if stop_present():
        return "stopped (intentional; not reviving)"
    if kernel_healthy():
        return "healthy"
    revive()
    return "revived"


def main(argv) -> int:
    db.init_db()
    if "--loop" in argv:
        interval = 5.0
        for a in argv:
            if a.startswith("--interval="):
                interval = float(a.split("=", 1)[1])
        print(f"watchdog loop every {interval}s; Ctrl-C to stop")
        try:
            while True:
                print("watchdog:", check_once())
                time.sleep(interval)
        except KeyboardInterrupt:
            return 0
    print("watchdog:", check_once())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
