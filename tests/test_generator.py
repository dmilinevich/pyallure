from __future__ import annotations

import json
from pathlib import Path

from pyrep.generator import aggregate_results, write_report_data
from pyrep.render import generate_static_report


def _write_events(results_dir: Path) -> None:
    events = [
        {"event": "test_start", "test_id": "t1", "name": "test_a", "suite": "suite", "start": 1.0, "tags": ["smoke"], "parameters": {}},
        {"event": "step_start", "test_id": "t1", "id": "s1", "name": "step", "start": 1.1, "parent_id": None},
        {"event": "step_stop", "test_id": "t1", "id": "s1", "stop": 1.2, "status": "passed"},
        {"event": "attachment", "test_id": "t1", "id": "a1", "name": "log", "mime": "text/plain", "path": "a1.txt", "size": 3},
        {"event": "test_stop", "test_id": "t1", "status": "passed", "stop": 1.5, "retries": []},
    ]
    (results_dir / "attachments").mkdir(parents=True)
    (results_dir / "attachments" / "a1.txt").write_text("hey", encoding="utf-8")
    with (results_dir / "events.jsonl").open("w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")


def test_aggregate_results(tmp_path: Path) -> None:
    results = tmp_path / "results"
    results.mkdir()
    _write_events(results)
    run, tests = aggregate_results(results)
    assert run.summary["passed"] == 1
    assert len(tests) == 1
    assert tests[0].steps[0].name == "step"


def test_generate_static_report(tmp_path: Path) -> None:
    results = tmp_path / "results"
    out = tmp_path / "report"
    results.mkdir()
    _write_events(results)
    write_report_data(results, out)
    generate_static_report(results, out)
    assert (out / "index.html").exists()
    data = json.loads((out / "report-data" / "run.json").read_text(encoding="utf-8"))
    assert data["summary"]["total"] == 1
