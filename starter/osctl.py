"""Local control CLI (Milestone M0 status; M1 stop/start).

The only surface that may mutate control state. Reads the DB read-only for
status; writes only the stop sentinel and launches the kernel. It never touches
channel content.

  python osctl.py status            show live state
  python osctl.py start             launch the kernel in the background
  python osctl.py stop              write the stop sentinel (clean shutdown)
  python osctl.py gate-check <path> ask the gate whether a path is readable
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import db
import proc
from contracts import GateRequest, Tier
from fences import Gate


def cmd_status() -> int:
    if not db.db_path().exists():
        print("status: not initialized yet (run the kernel or watchdog once)")
        return 0
    conn = db.connect(readonly=True)
    try:
        def g(k):
            r = conn.execute("SELECT value FROM kernel_state WHERE key=?", (k,)).fetchone()
            return r[0] if r else None
        pid, hb, boot = g("pid"), g("heartbeat"), g("boot_at")
        alive = proc.pid_alive(int(pid)) if pid else False
        age = (time.time() - float(hb)) if hb else None
        audits = conn.execute("SELECT COUNT(*) FROM audit").fetchone()[0]
        print("Personal AI OS -- status")
        print(f"  db:         {db.db_path()}")
        print(f"  kernel pid: {pid or '(none)'}  alive={alive}")
        print(f"  heartbeat:  {f'{age:.1f}s ago' if age is not None else '(none)'}")
        print(f"  booted at:  {boot or '(none)'}")
        print(f"  audit rows: {audits}")
        print(f"  stop file:  {'present' if (db.state_dir() / 'daemon.stop').exists() else 'no'}")
        return 0
    finally:
        conn.close()


def cmd_stop() -> int:
    (db.state_dir() / "daemon.stop").write_text(f"stopped by osctl at {time.time()}\n")
    print("ok: stop sentinel written; the kernel exits within a couple of ticks")
    return 0


def _detached_kwargs():
    if sys.platform == "win32":
        return {"creationflags": 0x00000008 | 0x00000200}
    return {"start_new_session": True}


def cmd_start() -> int:
    sf = db.state_dir() / "daemon.stop"
    if sf.exists():
        sf.unlink()
    subprocess.Popen([sys.executable, str(Path(__file__).with_name("kernel.py"))],
                     **_detached_kwargs())
    print("ok: kernel launched in the background")
    return 0


def cmd_gate_check(path: str) -> int:
    db.init_db()
    decision = Gate().decide(GateRequest("osctl", "read", path, Tier.T0_READ_ONLY))
    print(f"gate: {decision.decision.value.upper()} -- {decision.reason}")
    return 0 if decision.decision.value == "allow" else 1


USAGE = "usage: osctl.py [status | start | stop | gate-check <path>]"


def main(argv) -> int:
    if not argv:
        print(USAGE)
        return 2
    cmd = argv[0]
    if cmd == "status":
        return cmd_status()
    if cmd == "start":
        return cmd_start()
    if cmd == "stop":
        return cmd_stop()
    if cmd == "gate-check" and len(argv) >= 2:
        return cmd_gate_check(argv[1])
    print(USAGE)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
