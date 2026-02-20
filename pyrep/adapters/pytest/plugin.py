from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import pyrep.runtime as runtime
from pyrep.storage import EventStore


RESULTS_DIR = Path(os.getenv("PYREP_RESULTS_DIR", ".pyrep-results"))
STORE = EventStore(RESULTS_DIR)
_TEST_STATE: dict[str, dict[str, Any]] = {}


def pytest_runtest_setup(item):
    test_id = item.nodeid
    runtime.bind_test(test_id, RESULTS_DIR)
    _TEST_STATE[test_id] = {"start": time.time(), "status": "passed", "error": None, "retries": []}
    STORE.write_event(
        {
            "event": "test_start",
            "test_id": test_id,
            "name": item.name,
            "suite": item.module.__name__,
            "start": _TEST_STATE[test_id]["start"],
            "tags": [m.name for m in item.iter_markers()],
            "parameters": getattr(item, "callspec", None).params if hasattr(item, "callspec") else {},
        }
    )


def pytest_runtest_logreport(report):
    test_id = report.nodeid
    if test_id not in _TEST_STATE:
        return

    state = _TEST_STATE[test_id]
    if report.outcome == "rerun":
        state["retries"].append(f"{report.when}:{getattr(report, 'duration', 0.0):.6f}")
        return

    if report.failed:
        state["status"] = "failed"
        state["error"] = str(report.longrepr)
    elif report.skipped and state["status"] != "failed":
        state["status"] = "skipped"

    if report.when == "teardown":
        STORE.write_event(
            {
                "event": "test_stop",
                "test_id": test_id,
                "status": state["status"],
                "stop": time.time(),
                "error": state["error"],
                "retries": state["retries"],
            }
        )
        runtime.unbind_test()
        _TEST_STATE.pop(test_id, None)
