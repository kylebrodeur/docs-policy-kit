"""Mode 1: derived-copy sync and drift detection.

A private source doc is copied to a derived public location through a
declared rewrite. The engine computes the expected public text from the
source and the manifest; the copy is drift when it differs, and sync
writes the expected text in place. `check()` is read-only; `sync()` is
its writing half.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import Config, ConfigError, DerivedPair


@dataclass(frozen=True)
class Finding:
    """One drift finding, with the fix inline."""

    pair: str
    guide: str
    problem: str
    fix: str

    def __str__(self) -> str:
        return f"{self.pair}/{self.guide}: {self.problem} (fix: {self.fix})"


def expected_text(source_text: str, pair: DerivedPair) -> str:
    """The public text the copy produces from the private source.

    The declared rewrites apply in order, then the strips, then the
    base_url rule: a bare relative link to a guide of the SAME pair
    becomes the pair's public URL.
    """
    text = source_text
    for old, new in pair.rewrites:
        text = text.replace(old, new)
    for needle in pair.strips:
        text = text.replace(needle, "")
    if pair.base_url:
        for guide in pair.guides:
            text = text.replace(f"({guide})", f"({pair.base_url}/{guide})")
    return text


def _resolve(root: Path, declared: str) -> Path:
    candidate = (root / declared).resolve()
    if candidate == root or root not in candidate.parents:
        raise ConfigError(
            f"manifest path escapes the repo root: {declared!r} under {root}"
        )
    return candidate


def check(root: Path, config: Config) -> list[Finding]:
    """Read-only drift check. Return every finding; [] is clean."""
    findings: list[Finding] = []
    for pair in config.derived:
        source_root = _resolve(root, pair.source_dir)
        target_root = _resolve(root, pair.target_dir)
        for guide in pair.guides:
            src = source_root / guide
            dst = target_root / guide
            fix = (
                f"re-copy from {pair.source_dir} via "
                f"`docpol sync --manifest <manifest>`"
            )
            if not src.is_file():
                findings.append(Finding(pair.name, guide, "private source missing", fix))
                continue
            if not dst.is_file():
                findings.append(Finding(pair.name, guide, "derived copy missing", fix))
                continue
            want = expected_text(src.read_text(encoding="utf-8"), pair)
            got = dst.read_text(encoding="utf-8")
            if got != want:
                findings.append(
                    Finding(
                        pair.name,
                        guide,
                        f"derived text drifts from the source (expected {len(want)} chars, got {len(got)})",
                        fix,
                    )
                )
    return findings


def sync(root: Path, config: Config) -> list[str]:
    """Write the expected text for every pair. Returns what it wrote.

    A sync is an overwrite FROM the source, never a merge: the source
    is the truth. Files already current are left untouched and named
    as current.
    """
    actions: list[str] = []
    for pair in config.derived:
        source_root = _resolve(root, pair.source_dir)
        target_root = _resolve(root, pair.target_dir)
        for guide in pair.guides:
            src = source_root / guide
            if not src.is_file():
                # A missing source is reported by check(); sync touches
                # only what exists.
                continue
            dst = target_root / guide
            want = expected_text(src.read_text(encoding="utf-8"), pair)
            if dst.is_file() and dst.read_text(encoding="utf-8") == want:
                actions.append(f"current: {pair.target_dir}/{guide}")
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(want, encoding="utf-8")
            actions.append(f"wrote: {pair.target_dir}/{guide} from {pair.source_dir}/{guide}")
    return actions
