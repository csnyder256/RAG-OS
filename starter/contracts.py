"""Frozen cross-module contracts (Milestone M0).

These value types and protocols are the stable seams every later milestone codes
against. They are frozen on purpose: pinning the interfaces early is what lets a
cheaper or future model resume the build without re-litigating them. Pure stdlib,
and this module imports nothing from the rest of the system.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Protocol, runtime_checkable


class Tier(IntEnum):
    """Permission ladder, lowest privilege first (guide, Pillar 5)."""
    T0_READ_ONLY = 0
    T1_WRITE_SANDBOX = 1
    T2_RUN_ALLOWLISTED = 2
    T3_EXTERNAL_EFFECTS = 3


class Decision(Enum):
    ALLOW = "allow"
    DENY = "deny"


class JobState(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    AWAITING_APPROVAL = "awaiting_approval"


class ResultStatus(Enum):
    """An execution engine returns one of these. It NEVER raises for these
    conditions, because the kernel's fallback logic keys off the returned
    status (guide, Pillar 9). Wired up in a later milestone; frozen here."""
    DONE = "done"
    FAILED = "failed"
    GATED = "gated"     # a resource-contention gate refused (transient)
    DOWN = "down"       # the engine or server is unavailable (transient)
    PARKED = "parked"   # the budget governor parked the work


@dataclass(frozen=True)
class GateRequest:
    actor: str          # who is asking: "operator", a session id, "worker:42"
    action: str         # "read" | "write" | "run" | "external"
    target: str         # the path or resource being acted on
    tier: Tier


@dataclass(frozen=True)
class GateDecision:
    decision: Decision
    reason: str


@runtime_checkable
class Clock(Protocol):
    """Injected so tests can pin time; production passes the real wall clock."""
    def now(self) -> float: ...


@runtime_checkable
class SupportsGate(Protocol):
    def decide(self, request: GateRequest) -> GateDecision: ...
