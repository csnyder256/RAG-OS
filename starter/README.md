# Starter scaffold: Milestones M0 and M1

A small, runnable reference for the first two milestones of [`BUILD-GUIDE.md`](../BUILD-GUIDE.md). It is intentionally boring and dependency-free so you can read all of it in one sitting and run it in one minute.

- **M0, Scaffold and frozen contracts.** Frozen value types and protocols, the operational SQLite schema, the gate that denies crown-jewel paths, and a `status` control CLI.
- **M1, Daemon lifecycle.** A kernel with a single-instance lock, a heartbeat, an append-only ops log, and an independent watchdog that revives it out of band.

This is a foundation to build on, not the finished system. There is no LLM here yet. That is the point: the kernel holds zero model context, and the lifecycle and the safety boundary are solid before any intelligence is added.

## Requirements

- Python 3.10 or newer. No third-party packages for the runtime.
- `pip install pytest` only if you want to run the test suite.

## Layout

```
starter/
  contracts.py     frozen value types + protocols            (M0)
  schema.sql       operational database schema                (M0)
  db.py            paths, connection, idempotent init         (M0)
  fences.py        path normalization + the gate              (M0)
  osctl.py         control CLI: status, start, stop, gate     (M0/M1)
  proc.py          query-only process liveness probe          (M1)
  oplog.py         append-only ops event log                  (M1)
  kernel.py        the daemon: lock, heartbeat, tick loop     (M1)
  watchdog.py      independent reviver                        (M1)
  tests/           proofs for both milestones
```

## Run it

From inside `starter/`:

```bash
# 1. start the kernel in the background, then check on it
python osctl.py start
python osctl.py status

# 2. watch the heartbeat advance (run status a few times)
python osctl.py status

# 3. stop it cleanly
python osctl.py stop
python osctl.py status
```

State lives in `starter/state/` (gitignored). Delete that folder to reset.

## Prove M0

**The gate denies a crown-jewel path, at any tier.** The operational store and the whole `state/` directory are deny-all.

```bash
python osctl.py gate-check ./state/os.db      # DENY, crown-jewel path is deny-all
python osctl.py gate-check ./notes.md         # ALLOW, no fence matched
python osctl.py gate-check "./state/../state/os.db"   # DENY, .. collapses back in
```

Every decision is written to the `audit` table. That is the security record the later milestones query.

## Prove M1

**A kill brings it back, out of band.** Open two terminals.

Terminal 1, run the watchdog on a short loop so you can watch it work:

```bash
python watchdog.py --loop --interval=5
```

Terminal 2, start the kernel, confirm it is healthy, then kill it hard:

```bash
python osctl.py start
python osctl.py status                  # kernel pid: NNNN  alive=True

# kill it ungracefully (no clean stop):
#   macOS / Linux:  kill -9 <pid>
#   Windows:        taskkill /F /PID <pid>
```

Within one loop the watchdog prints `revived` and launches a new kernel. Run `python osctl.py status` again and the pid has changed and the heartbeat is fresh. A clean `python osctl.py stop` instead writes a stop sentinel, and the watchdog then prints `stopped (intentional; not reviving)`, so a deliberate shutdown is never fought by the watchdog.

## Make it reboot-safe

The kernel comes back after a reboot because the OS scheduler runs the watchdog, and the watchdog starts the kernel if it is not already healthy. Wire up whichever your machine uses:

- **cron (macOS / Linux):** `* * * * * cd /path/to/starter && /usr/bin/python3 watchdog.py`
- **systemd timer:** a one-shot service running `python watchdog.py`, on a one-minute timer with `Persistent=true`.
- **Windows Task Scheduler:** a task that runs `python watchdog.py` every minute and at logon.

## Run the tests

```bash
pip install pytest
python -m pytest tests -q
```

The suite proves, deterministically and against a temp directory: the contracts are frozen, the schema is idempotent, the gate denies crown-jewel paths (including `..` traversal) and audits every decision, the liveness probe refuses pid 0 (so it can never signal the process group), the single-instance lock refuses a second live kernel and takes over a stale one, and the watchdog treats a stale heartbeat as dead while respecting an intentional stop.

## Next

Continue with Milestone M2 in [`BUILD-GUIDE.md`](../BUILD-GUIDE.md): the frontend adapter and the identity allowlist at the edge, both behind one conformance test. Hand the guide to your coding agent and it will ask you which transport to build first.
