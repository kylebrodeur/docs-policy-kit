"""Ruling guards: a locked ruling becomes a deterministic check.

One manifest row (`[[guard]]`) is one check, in three kinds:

- `absent`:   these paths must NOT exist (fnmatch over the tree)
- `require`:  these paths MUST exist
- `forbid`:   this regex must not appear in any matching file's lines

Each row cites its ruling (`source`) and carries the `why`. The guard
reports; the CLI decides strictness. Findings are evidence: fix the
tree, never the check.
"""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from pathlib import Path

from .config import Config, Guard


@dataclass(frozen=True)
class GuardFinding:
    """One guard hit, plus the ruling's why."""

    guard: str
    hit: str
    why: str

    def __str__(self) -> str:
        return f"{self.guard}: {self.hit} (why: {self.why})"


def _iter_scope(root: Path, targets: tuple[str, ...]) -> list[Path]:
    """Files/dirs matching the target globs. Absolute-free: all under root."""
    out: list[Path] = []
    seen: set[Path] = set()
    for target in targets:
        for hit in root.glob(target):
            if hit == root or root not in hit.resolve().parents:
                continue
            if hit not in seen:
                seen.add(hit)
                out.append(hit)
    return out


TEXT_SUFFIXES = {".md", ".txt", ".json", ".toml", ".py", ".yml", ".yaml", ".sh"}


def _text_files(hit: Path) -> list[Path]:
    if hit.is_file():
        return [hit]
    return sorted(p for p in hit.rglob("*") if p.is_file() and p.suffix in TEXT_SUFFIXES)


def run_guard(root: Path, guard: Guard) -> list[str]:
    """Evaluate one guard row. Returns hits ([] is a pass)."""
    hits: list[str] = []
    if guard.kind == "absent":
        for hit in _iter_scope(root, guard.targets):
            hits.append(f"{hit.relative_to(root).as_posix()} must not exist")
    elif guard.kind == "require":
        for target in guard.targets:
            if not (root / target).exists():
                hits.append(f"missing: {target}")
    else:  # forbid
        rx = re.compile(guard.pattern)
        for hit in _iter_scope(root, guard.targets):
            for f in _text_files(hit):
                text = f.read_text(encoding="utf-8", errors="replace")
                for lineno, line in enumerate(text.splitlines(), 1):
                    if rx.search(line):
                        hits.append(f"{f.relative_to(root).as_posix()}:{lineno}")
    return hits


def run_all(root: Path, config: Config) -> list[GuardFinding]:
    """Every guard row. Returns the findings ([] is a clean tree)."""
    findings: list[GuardFinding] = []
    for guard in config.guards:
        for hit in run_guard(root, guard):
            findings.append(GuardFinding(guard.name, hit, guard.why))
    return findings


__all__ = ["GuardFinding", "run_guard", "run_all", "fnmatch"]
