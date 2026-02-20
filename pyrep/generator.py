from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from pyrep.models import Attachment, Step, TestCase, TestRun
from pyrep.storage import EventStore


SCHEMA_VERSION = "1.0"


def _ci_metadata() -> dict[str, str | None]:
    if os.getenv("GITHUB_ACTIONS"):
        repo = os.getenv("GITHUB_REPOSITORY", "")
        run_id = os.getenv("GITHUB_RUN_ID")
        return {
            "git_sha": os.getenv("GITHUB_SHA"),
            "branch": os.getenv("GITHUB_REF_NAME"),
            "build_url": f"https://github.com/{repo}/actions/runs/{run_id}" if repo and run_id else None,
        }
    if os.getenv("GITLAB_CI"):
        return {
            "git_sha": os.getenv("CI_COMMIT_SHA"),
            "branch": os.getenv("CI_COMMIT_REF_NAME"),
            "build_url": os.getenv("CI_JOB_URL"),
        }
    if os.getenv("TEAMCITY_VERSION"):
        return {
            "git_sha": os.getenv("BUILD_VCS_NUMBER"),
            "branch": os.getenv("TEAMCITY_BUILD_BRANCH"),
            "build_url": os.getenv("BUILD_URL"),
        }
    return {"git_sha": None, "branch": None, "build_url": None}


def _stable_run_id(test_cases: list[TestCase], started: float, finished: float) -> str:
    seed = [f"{started:.6f}", f"{finished:.6f}"]
    for t in test_cases:
        seed.append(f"{t.id}|{t.status}|{t.start:.6f}|{t.stop:.6f}")
    return hashlib.sha256("\n".join(seed).encode("utf-8")).hexdigest()[:16]


def aggregate_results(results_dir: Path) -> tuple[TestRun, list[TestCase]]:
    store = EventStore(results_dir)
    tests: dict[str, dict[str, Any]] = {}
    steps_by_test: dict[str, dict[str, Step]] = defaultdict(dict)
    root_steps: dict[str, list[Step]] = defaultdict(list)
    env_data: dict[str, str] = {}

    for event in store.read_events():
        test_id = event.get("test_id")
        kind = event["event"]
        if kind == "test_start":
            tests[test_id] = {
                "id": test_id,
                "name": event["name"],
                "suite": event["suite"],
                "status": "unknown",
                "start": event["start"],
                "stop": event["start"],
                "duration": 0,
                "labels": {},
                "tags": list(event.get("tags", [])),
                "parameters": event.get("parameters", {}),
                "retries": [],
                "steps": [],
                "attachments": [],
                "error": None,
            }
        elif kind == "test_stop" and test_id in tests:
            tests[test_id]["status"] = event["status"]
            tests[test_id]["stop"] = event["stop"]
            tests[test_id]["duration"] = event["stop"] - tests[test_id]["start"]
            tests[test_id]["error"] = event.get("error")
            tests[test_id]["retries"] = event.get("retries", [])
        elif kind == "label" and test_id in tests:
            tests[test_id]["labels"][event["key"]] = event["value"]
        elif kind == "env":
            env_data[event["key"]] = event["value"]
        elif kind == "step_start" and test_id in tests:
            step = Step(id=event["id"], name=event["name"], start=event["start"])
            steps_by_test[test_id][step.id] = step
            parent_id = event.get("parent_id")
            if parent_id and parent_id in steps_by_test[test_id]:
                steps_by_test[test_id][parent_id].steps.append(step)
            else:
                root_steps[test_id].append(step)
        elif kind == "step_stop" and test_id in tests:
            step = steps_by_test[test_id].get(event["id"])
            if step:
                step.stop = event["stop"]
                step.status = event["status"]
        elif kind == "attachment" and test_id in tests:
            tests[test_id]["attachments"].append(
                Attachment(
                    id=event["id"],
                    name=event["name"],
                    mime=event["mime"],
                    path=event["path"],
                    size=event["size"],
                )
            )

    test_cases: list[TestCase] = []
    for test_id, data in sorted(tests.items(), key=lambda item: (item[1]["suite"], item[1]["name"])):
        data["steps"] = root_steps[test_id]
        test_cases.append(TestCase(**data))

    if test_cases:
        started = min(t.start for t in test_cases)
        finished = max(t.stop for t in test_cases)
    else:
        started = finished = time.time()

    summary = {
        "passed": sum(1 for t in test_cases if t.status == "passed"),
        "failed": sum(1 for t in test_cases if t.status == "failed"),
        "skipped": sum(1 for t in test_cases if t.status == "skipped"),
        "total": len(test_cases),
    }

    run = TestRun(
        schema_version=SCHEMA_VERSION,
        id=_stable_run_id(test_cases, started, finished),
        started_at=started,
        finished_at=finished,
        duration=finished - started,
        env=env_data,
        summary=summary,
        **_ci_metadata(),
    )
    return run, test_cases


def write_report_data(results_dir: Path, out_dir: Path) -> Path:
    run, tests = aggregate_results(results_dir)
    report_data = out_dir / "report-data"
    report_data.mkdir(parents=True, exist_ok=True)
    (report_data / "attachments").mkdir(parents=True, exist_ok=True)

    with (report_data / "run.json").open("w", encoding="utf-8") as f:
        json.dump(run.to_dict(), f, indent=2, sort_keys=True)
    with (report_data / "tests.json").open("w", encoding="utf-8") as f:
        json.dump([t.to_dict() for t in tests], f, indent=2, sort_keys=True)

    source_attachments = results_dir / "attachments"
    if source_attachments.exists():
        for item in sorted(source_attachments.iterdir()):
            if item.is_file():
                shutil.copy2(item, report_data / "attachments" / item.name)
    return report_data
