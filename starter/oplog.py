"""Append-only ops event log (Milestone M1), the flight recorder.

JSONL, one line per event, never rewritten. Deliberately separate from the
security audit table (which is queryable and tamper-evident); this stream is
debug narrative. Size or age rotation is a later concern (guide, Pillar 12).
"""
from __future__ import annotations

import json
import os
import time

import db


def log_path():
    return db.state_dir() / "ops.log.jsonl"


def emit(event: str, **fields) -> None:
    rec = {"ts": round(time.time(), 3), "pid": os.getpid(), "event": event}
    rec.update(fields)
    with open(log_path(), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
