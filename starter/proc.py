"""Query-only process liveness (Milestone M1).

A wedged event loop can keep a process looking alive while doing nothing, so
liveness is checked out of band by the watchdog. This probe NEVER signals the
target:
  - pid <= 0 is rejected, because kill(0, ...) signals the caller's OWN process
    group and kill(-1, ...) fans out even wider. Passing an unchecked pid to a
    "signal 0" liveness check is a classic way to take down the very thing you
    meant to inspect (guide, Part C).
  - POSIX uses signal 0, which delivers nothing and only checks existence.
  - Windows uses OpenProcess with a query-only access right.
"""
from __future__ import annotations

import os
import sys


def pid_alive(pid: int) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    if sys.platform == "win32":
        import ctypes
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259
        k = ctypes.windll.kernel32
        handle = k.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return False
        try:
            code = ctypes.c_ulong()
            if k.GetExitCodeProcess(handle, ctypes.byref(code)):
                return code.value == STILL_ACTIVE
            return True
        finally:
            k.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True   # exists, owned by another user
    return True
