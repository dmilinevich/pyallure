from __future__ import annotations

import argparse
import http.server
import json
import os
import socketserver
import subprocess
from pathlib import Path

from pyrep.history import merge_history
from pyrep.render import generate_static_report


def cmd_init(args: argparse.Namespace) -> int:
    base = Path(args.path)
    (base / ".pyrep-results").mkdir(parents=True, exist_ok=True)
    cfg = base / "pyrep.json"
    if not cfg.exists():
        cfg.write_text(json.dumps({"results_dir": ".pyrep-results", "report_dir": "report"}, indent=2), encoding="utf-8")
    print(f"Initialized pyrep in {base}")
    return 0


def cmd_collect_pytest(args: argparse.Namespace) -> int:
    env = os.environ.copy()
    env["PYREP_RESULTS_DIR"] = str(Path(args.results_dir).resolve())
    env["PYTHONPATH"] = os.pathsep.join([str(Path.cwd()), env.get("PYTHONPATH", "")]).strip(os.pathsep)
    cmd = ["pytest", "-p", "pyrep.adapters.pytest.plugin", *args.pytest_args]
    try:
        return subprocess.call(cmd, env=env)
    except FileNotFoundError as exc:
        raise SystemExit("pytest executable not found. Install pytest or use `pip install -e .[dev]`.") from exc


def cmd_collect_behave(args: argparse.Namespace) -> int:
    env = os.environ.copy()
    env["PYREP_RESULTS_DIR"] = str(Path(args.results_dir).resolve())
    env["PYTHONPATH"] = os.pathsep.join([str(Path.cwd()), env.get("PYTHONPATH", "")]).strip(os.pathsep)
    cmd = ["behave", "-f", "pyrep.adapters.behave.formatter:PyrepFormatter", *args.behave_args]
    try:
        return subprocess.call(cmd, env=env)
    except FileNotFoundError as exc:
        raise SystemExit("behave executable not found. Install behave or use `pip install -e .[dev]`.") from exc


def cmd_generate(args: argparse.Namespace) -> int:
    results_dir = Path(args.results_dir)
    out = Path(args.out)
    if not (results_dir / "events.jsonl").exists():
        raise SystemExit(f"No events found at {results_dir / 'events.jsonl'}")
    generate_static_report(results_dir, out)
    merge_history(out, keep=args.keep_history)
    print(f"Report generated at {out / 'index.html'}")
    return 0


def cmd_open(args: argparse.Namespace) -> int:
    report_dir = Path(args.report)
    os.chdir(report_dir)
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("127.0.0.1", args.port), handler) as httpd:
        print(f"Serving {report_dir} at http://127.0.0.1:{args.port}")
        httpd.serve_forever()


def cmd_merge_history(args: argparse.Namespace) -> int:
    merge_history(Path(args.history_dir).parent, keep=args.keep)
    print("History merged")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pyrep")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init")
    p_init.add_argument("path", nargs="?", default=".")
    p_init.set_defaults(func=cmd_init)

    p_collect = sub.add_parser("collect")
    collect_sub = p_collect.add_subparsers(dest="target", required=True)

    p_pytest = collect_sub.add_parser("pytest")
    p_pytest.add_argument("--results-dir", default=".pyrep-results")
    p_pytest.add_argument("pytest_args", nargs=argparse.REMAINDER, default=[])
    p_pytest.set_defaults(func=cmd_collect_pytest)

    p_behave = collect_sub.add_parser("behave")
    p_behave.add_argument("--results-dir", default=".pyrep-results")
    p_behave.add_argument("behave_args", nargs=argparse.REMAINDER, default=[])
    p_behave.set_defaults(func=cmd_collect_behave)

    p_gen = sub.add_parser("generate")
    p_gen.add_argument("--results-dir", default=".pyrep-results")
    p_gen.add_argument("--out", default="report")
    p_gen.add_argument("--keep-history", type=int, default=20)
    p_gen.set_defaults(func=cmd_generate)

    p_open = sub.add_parser("open")
    p_open.add_argument("report")
    p_open.add_argument("--port", type=int, default=8765)
    p_open.set_defaults(func=cmd_open)

    p_hist = sub.add_parser("merge-history")
    p_hist.add_argument("--history-dir", required=True)
    p_hist.add_argument("--keep", type=int, default=20)
    p_hist.set_defaults(func=cmd_merge_history)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
