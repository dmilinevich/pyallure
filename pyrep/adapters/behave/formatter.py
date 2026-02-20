from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from pyrep.storage import EventStore


class PyrepFormatter:
    name = "pyrep"
    description = "Emit pyrep events"

    def __init__(self, stream_opener, config):
        self.stream_opener = stream_opener
        self.config = config
        self.store = EventStore(Path(os.getenv("PYREP_RESULTS_DIR", ".pyrep-results")))
        self.feature_name = "unknown"
        self.current_test_id: str | None = None
        self.current_status = "passed"
        self.current_error: str | None = None
        self.step_stack: list[str] = []

    def _finalize_scenario(self) -> None:
        if not self.current_test_id:
            return
        self.store.write_event(
            {
                "event": "test_stop",
                "test_id": self.current_test_id,
                "status": self.current_status,
                "stop": time.time(),
                "error": self.current_error,
                "retries": [],
            }
        )
        self.current_test_id = None
        self.current_status = "passed"
        self.current_error = None
        self.step_stack = []

    def feature(self, feature: Any) -> None:
        self.feature_name = feature.name

    def scenario(self, scenario: Any) -> None:
        self._finalize_scenario()
        self.current_test_id = f"{self.feature_name}::{scenario.name}"
        self.current_status = "passed"
        self.current_error = None
        self.step_stack = []
        self.store.write_event(
            {
                "event": "test_start",
                "test_id": self.current_test_id,
                "name": scenario.name,
                "suite": self.feature_name,
                "start": time.time(),
                "tags": list(getattr(scenario, "tags", [])),
                "parameters": {},
            }
        )

    def step(self, step: Any) -> None:
        if not self.current_test_id:
            return
        step_id = f"{self.current_test_id}:{len(self.step_stack)}:{int(time.time() * 1000000)}"
        self.step_stack.append(step_id)
        self.store.write_event(
            {
                "event": "step_start",
                "test_id": self.current_test_id,
                "id": step_id,
                "name": f"{step.keyword} {step.name}",
                "start": time.time(),
                "parent_id": None,
            }
        )

    def result(self, step: Any) -> None:
        if not self.current_test_id or not self.step_stack:
            return
        step_id = self.step_stack.pop()
        status_name = getattr(step.status, "name", str(step.status))
        status = "passed" if status_name == "passed" else "failed" if status_name == "failed" else "skipped"
        if status == "failed":
            self.current_status = "failed"
            self.current_error = str(getattr(step, "error_message", "Step failed"))
        elif status == "skipped" and self.current_status != "failed":
            self.current_status = "skipped"

        self.store.write_event(
            {
                "event": "step_stop",
                "test_id": self.current_test_id,
                "id": step_id,
                "stop": time.time(),
                "status": status,
            }
        )

    def eof(self) -> None:
        self._finalize_scenario()

    def close(self) -> None:
        self._finalize_scenario()
