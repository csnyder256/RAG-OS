"""Path normalization and the gate (Milestone M0).

Prompts are advisory; code is enforcement. The gate decides ALLOW or DENY from
the request alone and writes an audit row for every decision. Crown-jewel paths
(the operational store, secrets, the kernel's control plane) are deny-all: no
read, no write, no tier bypasses them. Fail closed, so a path that does not
normalize becomes a sentinel that matches no allowed root and is denied.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import db
from contracts import Decision, GateDecision, GateRequest

_UNRESOLVABLE = "<<unresolvable>>"


def normalize(target: str) -> str:
    """Collapse '..', resolve symlinks, absolutize, and casefold on
    case-insensitive platforms. Returns a sentinel on any error, so callers
    fail closed rather than acting on a half-resolved path."""
    try:
        p = Path(target).expanduser().resolve(strict=False)
        s = str(p)
        return s.casefold() if sys.platform == "win32" else s
    except (OSError, ValueError, RuntimeError):
        return _UNRESOLVABLE


def _sep() -> str:
    return "\\" if sys.platform == "win32" else "/"


def _crown_jewels() -> list[str]:
    """Paths no session may ever touch. The whole operational-state directory is
    deny-all; add real secret locations here as you wire them up."""
    return [normalize(str(db.state_dir())),
            normalize(str(db.state_dir() / "secrets"))]


def _is_under(path: str, root: str) -> bool:
    if path == _UNRESOLVABLE or root == _UNRESOLVABLE:
        return True   # fail closed
    return path == root or path.startswith(root.rstrip("/\\") + _sep())


class Gate:
    """A pure allow/deny oracle. Construct once, call decide() on every access."""

    def decide(self, request: GateRequest) -> GateDecision:
        target = normalize(request.target)
        if target == _UNRESOLVABLE:
            return self._audit(request, Decision.DENY, "path did not normalize")
        for jewel in _crown_jewels():
            if _is_under(target, jewel):
                return self._audit(request, Decision.DENY, "crown-jewel path is deny-all")
        return self._audit(request, Decision.ALLOW, "no fence matched")

    def _audit(self, request: GateRequest, decision: Decision, reason: str) -> GateDecision:
        # At M0 the gate runs kernel-side, so it may write the audit row directly.
        # Once sessions are subprocesses, route audit writes through the kernel to
        # keep the single-writer invariant (guide, Part B).
        conn = db.connect()
        try:
            conn.execute(
                "INSERT INTO audit(ts, actor, action, target, decision, reason) "
                "VALUES(?,?,?,?,?,?)",
                (time.time(), request.actor, request.action, request.target,
                 decision.value, reason))
            conn.commit()
        finally:
            conn.close()
        return GateDecision(decision, reason)
