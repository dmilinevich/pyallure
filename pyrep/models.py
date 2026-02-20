from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Attachment:
    id: str
    name: str
    mime: str
    path: str
    size: int


@dataclass
class Step:
    id: str
    name: str
    start: float
    stop: float | None = None
    status: str = "passed"
    steps: list["Step"] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "start": self.start,
            "stop": self.stop,
            "status": self.status,
            "steps": [s.to_dict() for s in self.steps],
        }


@dataclass
class TestCase:
    id: str
    name: str
    suite: str
    status: str
    start: float
    stop: float
    duration: float
    labels: dict[str, str] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)
    retries: list[str] = field(default_factory=list)
    steps: list[Step] = field(default_factory=list)
    attachments: list[Attachment] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["steps"] = [s.to_dict() for s in self.steps]
        return data


@dataclass
class TestRun:
    schema_version: str
    id: str
    started_at: float
    finished_at: float
    duration: float
    git_sha: str | None = None
    branch: str | None = None
    build_url: str | None = None
    env: dict[str, str] = field(default_factory=dict)
    summary: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
