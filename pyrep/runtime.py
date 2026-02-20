from __future__ import annotations

import contextvars
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from pyrep.storage import EventStore

_current_test: contextvars.ContextVar[str | None] = contextvars.ContextVar("current_test", default=None)
_step_stack: contextvars.ContextVar[tuple[dict[str, Any], ...]] = contextvars.ContextVar("step_stack", default=())
_results_dir: contextvars.ContextVar[Path | None] = contextvars.ContextVar("results_dir", default=None)


def bind_test(test_id: str, results_dir: str | Path) -> None:
    _current_test.set(test_id)
    _results_dir.set(Path(results_dir))
    _step_stack.set(())


def unbind_test() -> None:
    _current_test.set(None)
    _step_stack.set(())


def _emit(event: dict[str, Any]) -> None:
    test_id = _current_test.get()
    results_dir = _results_dir.get()
    if not test_id or not results_dir:
        return
    event["test_id"] = test_id
    EventStore(results_dir).write_event(event)


@contextmanager
def step(name: str) -> Iterator[None]:
    start = time.time()
    step_id = str(uuid.uuid4())
    stack = list(_step_stack.get())
    parent_id = stack[-1]["id"] if stack else None
    stack.append({"id": step_id, "name": name, "start": start})
    _step_stack.set(tuple(stack))
    _emit({"event": "step_start", "id": step_id, "name": name, "start": start, "parent_id": parent_id})
    status = "passed"
    try:
        yield
    except Exception:
        status = "failed"
        raise
    finally:
        stop = time.time()
        stack = list(_step_stack.get())
        if stack:
            stack.pop()
        _step_stack.set(tuple(stack))
        _emit({"event": "step_stop", "id": step_id, "stop": stop, "status": status})


def attach(name: str, content: bytes | str, mime: str = "text/plain") -> None:
    test_id = _current_test.get()
    results_dir = _results_dir.get()
    if not test_id or not results_dir:
        return

    payload = content.encode("utf-8") if isinstance(content, str) else content
    attachment_id = str(uuid.uuid4())
    ext = {
        "application/json": "json",
        "image/png": "png",
        "text/plain": "txt",
        "text/html": "html",
    }.get(mime, "bin")
    path = EventStore(results_dir).attachments_dir / f"{attachment_id}.{ext}"
    path.write_bytes(payload)

    stack = _step_stack.get()
    _emit(
        {
            "event": "attachment",
            "id": attachment_id,
            "name": name,
            "mime": mime,
            "path": path.name,
            "size": len(payload),
            "step_id": stack[-1]["id"] if stack else None,
        }
    )


def set_env(key: str, value: str) -> None:
    _emit({"event": "env", "key": key, "value": value})


def set_label(key: str, value: str) -> None:
    _emit({"event": "label", "key": key, "value": value})
