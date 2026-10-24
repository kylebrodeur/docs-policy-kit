"""The prose gate over tracked markdown.

Two rules, from the family's DOC-STANDARD writing rules: no banned
characters and no banned words in any tracked markdown. The banned sets
are CONFIG (`prose.banned_words`, `prose.banned_chars` in the
manifest); a doc that must NAME them cites those keys, never the words.
The `prose.skip_patterns` list exempts rule-citation lines.
"""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from pathlib import Path

from .config import Config, ConfigError


@dataclass(frozen=True)
class ProseFinding:
    """One finding: file, line, and the rule name (never the raw content)."""

    file: str
    line: int
    rule: str

    def __str__(self) -> str:
        return f"{self.file}:{self.line}: <{self.rule}>"


def _skip_match(line: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(p, line) for p in patterns)


def word_hits(line: str, words: tuple[str, ...]) -> list[str]:
    """The banned words the line carries, matched on word boundaries."""
    lower = line.lower()
    return [w for w in words if re.search(rf"\b{re.escape(w)}\b", lower)]


def char_hits(line: str, chars: str) -> list[str]:
    """The banned characters the line carries."""
    return [c for c in chars if c in line]


def tracked_files(root: Path, config: Config | None = None) -> list[Path]:
    """Every tracked markdown file under root's git worktree.

    `git ls-files` is the truth (a generated or untracked file is the
    author's business until it is committed). Without git, every
    `.md` under root counts, so the gate still bites in a bare tree.
    """
    import subprocess

    try:
        out = subprocess.run(
            ["git", "ls-files", "*.md"],
            cwd=root, capture_output=True, text=True, check=True,
        ).stdout.splitlines()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return sorted(root.rglob("*.md"))
    files = [root / line.strip() for line in out if line.strip()]
    return sorted(p for p in files if p.is_file())


def check(root: Path, config: Config, files: list[Path] | None = None) -> list[ProseFinding]:
    """Read-only prose gate over the given (or tracked) markdown files."""
    files = files if files is not None else tracked_files(root)
    findings: list[ProseFinding] = []
    skip = config.prose_skip_patterns
    words = config.prose_banned
    chars = config.prose_chars_banned
    for path in files:
        rel_name = path.name
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise ConfigError(f"{rel_name}: unreadable: {exc}") from exc
        for lineno, line in enumerate(text.splitlines(), 1):
            if _skip_match(line, skip):
                continue
            for word in word_hits(line, words):
                findings.append(ProseFinding(rel_name, lineno, word))
            if char_hits(line, chars):
                findings.append(ProseFinding(rel_name, lineno, "banned-chars"))
    return findings


def glob_scope(root: Path, pattern: str) -> list[Path]:
    """Files matching a guard-style glob under root (no recursion past root)."""
    return [p for p in root.glob(pattern) if p.is_file()]


__all__ = ["ProseFinding", "check", "tracked_files", "word_hits", "char_hits", "fnmatch"]
