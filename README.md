# pyallure-like (pyrep)

A Python-only, offline-first test report generator inspired by Allure UX.

## Features

- Static HTML report + JSON (`report-data/`) output.
- Run summary dashboard (pass/fail/skip + duration).
- Suite/test tree + test detail panel.
- Nested steps with timing.
- Attachments (JSON/text/image/binary links).
- Environment labels and metadata.
- History trend generated from `report/history/` snapshots.
- CLI commands for init/collect/generate/open/merge-history.
- Adapters for `pytest` and `behave`.

## Install

```bash
pip install -e .
```

## Quickstart

```bash
pyrep init
pyrep collect pytest --results-dir .pyrep-results examples/pytest_sample/tests
pyrep generate --results-dir .pyrep-results --out report
pyrep open report
```

Behave:

```bash
pyrep collect behave --results-dir .pyrep-results examples/behave_sample/features
pyrep generate --results-dir .pyrep-results --out report
```

## CLI

- `pyrep init [path]`
- `pyrep collect pytest --results-dir .pyrep-results [pytest args...]`
- `pyrep collect behave --results-dir .pyrep-results [behave args...]`
- `pyrep generate --results-dir .pyrep-results --out report --keep-history 20`
- `pyrep open report --port 8765`
- `pyrep merge-history --history-dir report/history --keep 20`

## Runtime API

```python
from pyrep.runtime import step, attach, set_env, set_label

with step("Login"):
    attach("request.json", '{"username": "demo"}', mime="application/json")

set_env("python", "3.12")
set_label("team", "qa-platform")
```

## Output layout

```text
report/
  index.html
  assets/
    app.js
    styles.css
  report-data/
    run.json
    tests.json
    attachments/
  history/
    <timestamp>/run.json
    <timestamp>/tests.json
    index.json
```

## Schema (v1.0)

- `report-data/run.json`: run metadata + summary.
- `report-data/tests.json`: deterministic ordered list of tests including steps, attachments, retries, tags.
- `report-data/attachments/*`: copied payloads.

## Development checks

```bash
pytest
```

## Notes

- No Java, no Allure CLI, no external services.
- UI is vanilla JS + CSS and works offline.
- `pyrep open` serves local files to avoid `file://` fetch constraints.
