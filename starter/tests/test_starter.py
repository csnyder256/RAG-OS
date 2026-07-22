"""Proofs for M0 and M1. Pure stdlib plus pytest. Everything runs against a temp
state directory, so the real tree is never touched (guide, Part C: a test that
mutates the real store is a real bug)."""
from __future__ import annotations

import dataclasses
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import db          # noqa: E402
import proc        # noqa: E402
from contracts import Decision, GateRequest, ResultStatus, Tier  # noqa: E402


@pytest.fixture(autouse=True)
def temp_root(tmp_path):
    db.set_root(tmp_path)
    db.init_db()
    yield


# --- M0: contracts, schema, gate ------------------------------------------
def test_contracts_are_frozen():
    r = GateRequest(actor="x", action="read", target="/tmp/a", tier=Tier.T0_READ_ONLY)
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.actor = "y"           # frozen value type: mutation must fail


def test_result_status_values_exist():
    assert {s.value for s in ResultStatus} >= {"done", "failed", "gated", "down", "parked"}


def test_init_db_is_idempotent():
    db.init_db()
    db.init_db()                # second call must not raise
    conn = db.connect(readonly=True)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    assert {"kernel_state", "audit", "jobs", "schedule"} <= tables


def test_gate_denies_crown_jewel_and_audits():
    from fences import Gate
    jewel = str(db.db_path())   # the operational store itself
    d = Gate().decide(GateRequest("sess-1", "read", jewel, Tier.T3_EXTERNAL_EFFECTS))
    assert d.decision is Decision.DENY          # even the top tier cannot read it
    conn = db.connect(readonly=True)
    n = conn.execute("SELECT COUNT(*) FROM audit WHERE decision='deny'").fetchone()[0]
    conn.close()
    assert n >= 1                                # the denial was audited


def test_gate_allows_ordinary_path():
    from fences import Gate
    d = Gate().decide(GateRequest("sess-1", "read", str(db.root() / "notes.md"), Tier.T0_READ_ONLY))
    assert d.decision is Decision.ALLOW


def test_normalize_blocks_traversal_into_jewel():
    from fences import Gate
    sneaky = str(db.state_dir() / ".." / "state" / "os.db")   # '..' collapses back in
    d = Gate().decide(GateRequest("sess-1", "read", sneaky, Tier.T0_READ_ONLY))
    assert d.decision is Decision.DENY


# --- M1: liveness, lock, heartbeat, watchdog ------------------------------
def test_pid_alive_guards_and_truth():
    assert proc.pid_alive(0) is False           # never signal the process group
    assert proc.pid_alive(-1) is False
    assert proc.pid_alive(os.getpid()) is True
    assert proc.pid_alive(2_000_000_000) is False


def test_single_instance_lock():
    import kernel
    assert kernel.acquire_lock() is True        # first acquire wins
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        kernel.pid_file().write_text(str(child.pid))   # a different, LIVE pid holds it
        assert kernel.acquire_lock() is False          # refuse the second instance
    finally:
        child.terminate()
        child.wait(timeout=5)
    assert kernel.acquire_lock() is True        # dead pid => stale lock is taken over


def test_watchdog_health_and_stop():
    import watchdog
    conn = db.connect()
    db.kstate_set(conn, "pid", str(os.getpid()))
    db.kstate_set(conn, "heartbeat", str(time.time()))
    conn.close()
    assert watchdog.kernel_healthy() is True    # fresh heartbeat + live pid

    conn = db.connect()
    db.kstate_set(conn, "heartbeat", str(time.time() - 999))
    conn.close()
    assert watchdog.kernel_healthy() is False   # stale heartbeat => presumed dead

    (db.state_dir() / "daemon.stop").write_text("stop")
    assert watchdog.check_once() == "stopped (intentional; not reviving)"
