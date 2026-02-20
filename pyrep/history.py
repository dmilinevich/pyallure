from __future__ import annotations

import json
import shutil
import time
from pathlib import Path


def merge_history(report_dir: Path, keep: int = 20) -> None:
    history_dir = report_dir / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    ts = str(int(time.time()))
    snapshot = history_dir / ts
    snapshot.mkdir(exist_ok=True)
    for name in ("run.json", "tests.json"):
        src = report_dir / "report-data" / name
        if src.exists():
            shutil.copy2(src, snapshot / name)

    entries = sorted([p for p in history_dir.iterdir() if p.is_dir()], key=lambda p: p.name)
    while len(entries) > keep:
        old = entries.pop(0)
        shutil.rmtree(old)

    points = []
    for i, entry in enumerate(entries):
        run_path = entry / "run.json"
        if not run_path.exists():
            continue
        run = json.loads(run_path.read_text(encoding="utf-8"))
        total = max(run.get("summary", {}).get("total", 0), 1)
        passed = run.get("summary", {}).get("passed", 0)
        points.append(
            {
                "i": i,
                "timestamp": entry.name,
                "pass_rate": round((passed / total) * 100, 2),
                "duration": run.get("duration", 0),
            }
        )
    (history_dir / "index.json").write_text(json.dumps(points, indent=2), encoding="utf-8")
