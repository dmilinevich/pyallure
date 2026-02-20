from __future__ import annotations

import os
import time
from pathlib import Path

from pyrep.storage import EventStore


class PyrepFormatter:
    name = "pyrep"
    description = "Emit pyrep events"

    def __init__(self, stream_opener, config):
        self.stream_opener = stream_opener
        self.config = config
        self.store = EventStore(Path(os.getenv("PYREP_RESULTS_DIR", ".pyrep-results")))
        self.current_test_id: str | None = None
        self.step_ids: list[str] = []

    def feature(self, feature):
        self.feature_name = feature.name

    def scenario(self, scenario):
        self.current_test_id = f"{self.feature_name}::{scenario.name}"
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

    def step(self, step):
        if not self.current_test_id:
            return
        step_id = f"{self.current_test_id}:{len(self.step_ids)}"
        self.step_ids.append(step_id)
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

    def result(self, step):
        if not self.current_test_id or not self.step_ids:
            return
        step_id = self.step_ids[-1]
        status = "passed" if step.status.name == "passed" else "failed" if step.status.name == "failed" else "skipped"
        self.store.write_event(
            {
                "event": "step_stop",
                "test_id": self.current_test_id,
                "id": step_id,
                "stop": time.time(),
                "status": status,
            }
        )

    def eof(self):
        pass

    def close(self):
        pass

    def scenario_finished(self, scenario):
        if not self.current_test_id:
            return
        status = "passed" if scenario.status.name == "passed" else "failed" if scenario.status.name == "failed" else "skipped"
        self.store.write_event(
            {
                "event": "test_stop",
                "test_id": self.current_test_id,
                "status": status,
                "stop": time.time(),
                "error": None,
                "retries": [],
            }
        )
        self.current_test_id = None
        self.step_ids = []
