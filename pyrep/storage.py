from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Iterable


EVENTS_FILE = "events.jsonl"
ATTACHMENTS_DIR = "attachments"


class EventStore:
    def __init__(self, results_dir: Path) -> None:
        self.results_dir = results_dir
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.attachments_dir = self.results_dir / ATTACHMENTS_DIR
        self.attachments_dir.mkdir(parents=True, exist_ok=True)
        self.events_path = self.results_dir / EVENTS_FILE

    def write_event(self, event: dict[str, Any]) -> None:
        with self.events_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

    def read_events(self) -> Iterable[dict[str, Any]]:
        if not self.events_path.exists():
            return []
        events: list[dict[str, Any]] = []
        with self.events_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
        return events

    def copy_attachment(self, src: Path, attachment_id: str, ext: str) -> Path:
        dst = self.attachments_dir / f"{attachment_id}.{ext.lstrip('.')}"
        shutil.copy2(src, dst)
        return dst
