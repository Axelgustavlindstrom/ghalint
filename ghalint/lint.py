from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable

import yaml

from ghalint.models import Issue, Level, LintReport

# Patterns that indicate a shell run command may need quoting.
_UNQUOTED_RUN_PATTERNS = [
    re.compile(r"run:\s*[^\s'\"]{2,}\s+\{"),
    re.compile(r"run:\s*.+?\$\{"),
]

# Allowlist of safe action references.
_SAFE_ACTIONS = re.compile(r"^actions/[^@]+@[0-9a-f]{40}$|^actions/[^@]+@v\d+$")

_FILE_NAME_PATTERN = re.compile(r"^[a-z0-9._-]+\.ya?ml$")


def _line_at(content: str, offset: int) -> int:
    return content[:offset].count("\n") + 1


def _collect_files(paths: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            for yml in sorted(p.glob("*.yml")):
                files.append(yml)
            for yaml_file in sorted(p.glob("*.yaml")):
                files.append(yaml_file)
        elif p.exists():
            files.append(p)
    return files


def _check_workflow_name(content: str, report: LintReport, path: str) -> None:
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError:
        return
    if not isinstance(data, dict):
        return
    if "name" not in data or not str(data.get("name", "")).strip():
        report.add(Issue(Level.warn, "GH002", "Missing workflow name.", path))


def _check_permissions(content: str, report: LintReport, path: str) -> None:
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError:
        return
    if not isinstance(data, dict):
        return
    if "permissions" not in data:
        report.add(Issue(Level.warn, "GH006", "Missing `permissions` block.", path))


def _check_actions(content: str, report: LintReport, path: str) -> None:
    if "@main" in content or "@master" in content:
        report.add(
            Issue(Level.error, "GH010", "Use a pinned ref instead of mutable branch.", path)
        )


def _check_run_quoting(content: str, report: LintReport, path: str) -> None:
    if "run:" not in content:
        return
    for idx, line in enumerate(content.splitlines(), start=1):
        if "run:" not in line:
            continue
        if "${{" in line:
            report.add(
                Issue(Level.warn, "GH004", "Unquoted run expression with interpolation.", path, idx)
            )
            break


def _check_secret_mask(content: str, report: LintReport, path: str) -> None:
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError:
        return
    if not isinstance(data, dict):
        return
    jobs = data.get("jobs", {})
    if not isinstance(jobs, dict):
        return
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        if job.get("uses"):
            continue
        if "env" not in job or not isinstance(job.get("env"), dict):
            continue
        env = job["env"]
        for key in env:
            if not isinstance(key, str):
                continue
            if re.match(r"^(GITHUB_TOKEN|SECRET_\w+|TOKEN_\w+)$", key, re.IGNORECASE):
                report.add(
                    Issue(
                        Level.warn,
                        "GH005",
                        f"Potential secret exposure in job env: {key}.",
                        path,
                    )
                )


def _check_timeouts(content: str, report: LintReport, path: str) -> None:
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError:
        return
    if not isinstance(data, dict):
        return
    jobs = data.get("jobs", {})
    if not isinstance(jobs, dict):
        return
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        if job.get("uses"):
            continue
        if job.get("timeout-minutes") is None:
            report.add(
                Issue(Level.warn, "GH009", f"Job '{job_name}' has no timeout-minutes.", path)
            )


def _check_always_run(content: str, report: LintReport, path: str) -> None:
    if "${{ always() }}" not in content:
        report.add(
            Issue(Level.info, "GH003", "Consider if `if: ${{ always() }}` is needed for cleanup.", path)
        )


def _check_composite(content: str, report: LintReport, path: str) -> None:
    if "runs.using: composite" in content and "outputs:" not in content:
        report.add(
            Issue(Level.warn, "GH008", "Composite action should define `outputs` when reusable.", path)
        )


_CHECKS = [
    _check_workflow_name,
    _check_permissions,
    _check_actions,
    _check_run_quoting,
    _check_secret_mask,
    _check_timeouts,
    _check_always_run,
    _check_composite,
]


def lint_file(path: Path) -> LintReport:
    content = path.read_text(encoding="utf-8", errors="ignore")
    report = LintReport()
    relative = os.fspath(path)
    if not _FILE_NAME_PATTERN.match(path.name):
        report.add(
            Issue(Level.warn, "GH001", "Use lowercase workflow filename ending in .yml.", relative)
        )
    for check in _CHECKS:
        check(content, report, relative)
    return report


def lint_paths(paths: Iterable[str]) -> LintReport:
    files = _collect_files(paths)
    if not files:
        return LintReport([Issue(Level.warn, "GH000", "No workflow files found.")])
    report = LintReport()
    for file in files:
        report.issues.extend(lint_file(file).issues)
    return report
