"""Read-only inventory of a docs tree.

For every markdown file under the manifest's `audit.source_dir`:
a STATUS word if one appears near the top, and backticked repo-relative
paths that no longer resolve (dead references). The lane folder comes
from the manifest's `audit.lane_key`. Nothing is written.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .config import Config, ConfigError

STATUS_RE = re.compile(
    r"\bstatus\b[^A-Za-z]{0,6}(OPEN|DONE|CLOSED|PARTIAL|SUPERSEDED|CONSUMED|"
    r"PROPOSAL|DRAFT|CURRENT|ACTIVE|ARCHIVED|RESOLVED|SHUTDOWN|LOCKED|COMPLETE)\b",
    re.IGNORECASE,
)

PATH_RE = re.compile(r"`((?:docs|skills|tools|examples|tests)/[^`\s*<>]+)`")


@dataclass(frozen=True)
class AuditRow:
    """One markdown file's inventory row."""

    path: str
    lane: str
    status: str | None
    dead_refs: tuple[str, ...]


def inspect(path: Path, root: Path, lane_key: str) -> AuditRow:
    text = path.read_text(encoding="utf-8", errors="replace")
    head = "\n".join(text.splitlines()[:25])
    status = STATUS_RE.search(head)
    dead: list[str] = []
    rel = path.relative_to(root).as_posix()
    parts = rel.split("/")
    lane = ""
    if lane_key in parts:
        i = parts.index(lane_key) + 1
        lane = parts[i] if i < len(parts) else ""
    for ref in sorted(set(PATH_RE.findall(text))):
        target = ref.rstrip(".,;:)")
        if not (root / target).exists():
            dead.append(target)
    return AuditRow(path=rel, lane=lane, status=status.group(1).upper() if status else None, dead_refs=tuple(dead))


def audit(root: Path, config: Config) -> list[AuditRow]:
    """Inventory the manifest's audit source tree. Read-only."""
    source = root / config.audit.source_dir
    if not source.is_dir():
        raise ConfigError(f"audit source_dir does not exist: {config.audit.source_dir}")
    rows: list[AuditRow] = []
    for ext in config.audit.extensions:
        for p in sorted(source.rglob(f"*{ext}")):
            if p.is_file():
                rows.append(inspect(p, root, config.audit.lane_key))
    return rows


def summary(rows: list[AuditRow]) -> str:
    """The one-line-per-class summary the console command prints."""
    with_dead = [r for r in rows if r.dead_refs]
    no_status = [r for r in rows if r.status is None]
    lines = [
        f"markdown files:        {len(rows)}",
        f"with a status line:    {len(rows) - len(no_status)}",
        f"with dead references:  {len(with_dead)}",
    ]
    if with_dead:
        lines.append("worst dead-reference offenders:")
        for r in sorted(with_dead, key=lambda r: -len(r.dead_refs))[:10]:
            lines.append(f"  {len(r.dead_refs):>3}  {r.path}")
    return "\n".join(lines)


__all__ = ["AuditRow", "audit", "summary", "inspect"]
