from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, List


class Level(str, Enum):
    error = "error"
    warn = "warn"
    info = "info"


@dataclass(frozen=True)
class Issue:
    level: Level
    code: str
    message: str
    path: str | None = None
    line: int | None = None

    def __str__(self) -> str:
        location = ""
        if self.path:
            location = self.path
            if self.line is not None:
                location += f":{self.line}"
            location = f"{location}: "
        return f"{location}[{self.level.value.upper()}] {self.code}: {self.message}"


@dataclass
class LintReport:
    issues: List[Issue] = field(default_factory=list)

    def add(self, issue: Issue) -> None:
        self.issues.append(issue)

    @property
    def failed(self) -> bool:
        return any(i.level == Level.error for i in self.issues)

    def summary(self) -> str:
        counts = {Level.error: 0, Level.warn: 0, Level.info: 0}
        for issue in self.issues:
            counts[issue.level] = counts.get(issue.level, 0) + 1
        return (
            f"{counts[Level.error]} error(s), "
            f"{counts[Level.warn]} warning(s), "
            f"{counts[Level.info]} info"
        )

    def to_rows(self) -> list[dict]:
        return [
            {
                "level": i.level.value,
                "code": i.code,
                "message": i.message,
                "path": i.path,
                "line": i.line,
            }
            for i in self.issues
        ]
