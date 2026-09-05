from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.fspath(Path(__file__).resolve().parent.parent))

from ghalint.lint import LintReport, lint_file, lint_paths
from ghalint.cli import main


def _write_tmp(content: str, tmp_path: Path, name: str = "workflow.yml") -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_lint_file_detects_missing_name(tmp_path: Path) -> None:
    workflow = _write_tmp(
        """
on: push

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - run: echo hi
""",
        tmp_path,
    )
    report = lint_file(workflow)
    assert any(i.code == "GH002" for i in report.issues)


def test_lint_file_detects_mutable_branch(tmp_path: Path) -> None:
    workflow = _write_tmp(
        """
name: CI
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@main
      - run: echo hello
""",
        tmp_path,
    )
    report = lint_file(workflow)
    assert any(i.code == "GH010" for i in report.issues)


def test_lint_file_ignores_pinned_action(tmp_path: Path) -> None:
    workflow = _write_tmp(
        """
name: CI
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo hello
""",
        tmp_path,
    )
    report = lint_file(workflow)
    assert not any(i.code == "GH010" for i in report.issues)


def test_lint_directory_collects_yml(tmp_path: Path) -> None:
    (tmp_path / "a.yml").write_text("on: push\n", encoding="utf-8")
    (tmp_path / "b.yaml").write_text("on: push\n", encoding="utf-8")
    report = lint_paths([os.fspath(tmp_path)])
    assert len(report.issues) >= 2
    assert len({i.path for i in report.issues}) == 2


def test_main_returns_zero_on_warnings(tmp_path: Path) -> None:
    workflow = _write_tmp(
        """
on: push
jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - run: echo hi
""",
        tmp_path,
    )
    rc = main([os.fspath(workflow)])
    assert rc == 0


def test_main_returns_one_on_error(tmp_path: Path) -> None:
    workflow = _write_tmp(
        """
name: CI
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@main
      - run: echo hello
""",
        tmp_path,
    )
    rc = main([os.fspath(workflow)])
    assert rc == 1


def test_main_json_output(tmp_path: Path, capsys) -> None:
    workflow = _write_tmp(
        """
on: push
jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - run: echo hi
""",
        tmp_path,
    )
    rc = main(["--json", os.fspath(workflow)])
    captured = capsys.readouterr()
    assert rc == 0
    parsed = json.loads(captured.out)
    assert isinstance(parsed, list)
    assert any(item["code"] == "GH002" for item in parsed)
