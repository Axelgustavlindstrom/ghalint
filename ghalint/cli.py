from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List, Optional, Sequence

from ghalint.lint import lint_file, lint_paths


class _HelpArgs:
    help_requested = True


def _create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ghalint",
        description="Lint GitHub Actions workflow files for common issues.",
    )
    parser.add_argument("--version", action="version", version="ghalint 0.1.0")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument(
        "paths",
        nargs="*",
        default=[os.path.join(".github", "workflows")],
        help="Workflow files or directories to lint.",
    )
    return parser


def parse_args(argv: Optional[List[str]]) -> Optional[argparse.Namespace | _HelpArgs]:
    parser = _create_parser()
    try:
        return parser.parse_args(argv)
    except SystemExit as exc:
        if exc.code == 0:
            return _HelpArgs()
        raise


def _render_text(report) -> str:
    if not report.issues:
        return f"ghalint: {report.summary()}."
    lines = [f"ghalint: {report.summary()}\n"]
    for issue in report.issues:
        lines.append(f"- {issue}")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if args is None or isinstance(args, _HelpArgs):
        return 0
    report = lint_paths(args.paths)
    output = json.dumps(report.to_rows(), indent=2) if getattr(args, "json", False) else _render_text(report)
    if output:
        print(output)
    return 1 if report.failed else 0
