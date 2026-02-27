from __future__ import annotations

import os
import time
from pathlib import Path

import pyrep.runtime as runtime
from pyrep.storage import EventStore


RESULTS_DIR = Path(os.getenv("PYREP_RESULTS_DIR", ".pyrep-results"))
STORE = EventStore(RESULTS_DIR)


def pytest_runtest_protocol(item, nextitem):
    test_id = item.nodeid
    runtime.bind_test(test_id, RESULTS_DIR)
    STORE.write_event(
        {
            "event": "test_start",
            "test_id": test_id,
            "name": item.name,
            "suite": item.module.__name__,
            "start": time.time(),
            "tags": [m.name for m in item.iter_markers()],
            "parameters": getattr(item, "callspec", None).params if hasattr(item, "callspec") else {},
        }
    )


def pytest_runtest_logreport(report):
    if report.when != "call":
        return
    status = "passed"
    error = None
    if report.failed:
        status = "failed"
        error = str(report.longrepr)
    elif report.skipped:
        status = "skipped"
    STORE.write_event(
        {
            "event": "test_stop",
            "test_id": report.nodeid,
            "status": status,
            "stop": time.time(),
            "error": error,
            "retries": [],
        }
    )
    runtime.unbind_test()
