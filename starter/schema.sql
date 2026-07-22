-- Operational store schema (Milestone M0).
-- Minimal but representative: the tables later milestones fill in, plus the two
-- this scaffold actually exercises now (kernel_state for the heartbeat, audit
-- for every gate decision). Everything is CREATE ... IF NOT EXISTS so init is
-- idempotent and safe to run on every boot.

CREATE TABLE IF NOT EXISTS kernel_state (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    ts       REAL NOT NULL,
    actor    TEXT NOT NULL,
    action   TEXT NOT NULL,
    target   TEXT NOT NULL,
    decision TEXT NOT NULL,
    reason   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit(ts);

-- Placeholders for later milestones (empty at M0/M1, but the shape is frozen).
CREATE TABLE IF NOT EXISTS jobs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    kind        TEXT NOT NULL,
    state       TEXT NOT NULL,
    created_at  REAL NOT NULL,
    finished_at REAL
);

CREATE TABLE IF NOT EXISTS schedule (
    name   TEXT NOT NULL,
    window TEXT NOT NULL,
    kind   TEXT NOT NULL,
    UNIQUE(name, window)     -- reboot-safe idempotency key (guide, Pillar 11)
);

CREATE TABLE IF NOT EXISTS usage_ledger (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    ts     REAL NOT NULL,
    tokens INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS approvals (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    code    TEXT NOT NULL,
    expires REAL NOT NULL,
    used    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS messages (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ts        REAL NOT NULL,
    direction TEXT NOT NULL,
    body      TEXT NOT NULL
);
