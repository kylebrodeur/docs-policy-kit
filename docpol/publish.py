"""Mode 2: allowlisted publication.

Only allowlisted paths are copied into the published tree. Each entry
is checked BEFORE any file is copied, on two rules:

1. `path_refusal`: the path must be relative (no escape), must not sit
   in a denied directory segment, and must not match a denied filename
   class.
2. `secret_refusal`: the content must not carry a credential-shaped
   string, whatever the path.

One refusal aborts the whole run. Publishing the good entries while
skipping the bad would leave the surface half-synced with no signal
that something was refused.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .config import (
    DENIED_FILENAME_PATTERNS,
    SECRET_PATTERNS,
    Config,
    ConfigError,
)


class PathEscape(Exception):
    """An allowlist path resolves outside its declared root."""


@dataclass(frozen=True)
class Refusal:
    """One allowlist entry's refusal, with the rule that fired."""

    path: str
    reason: str


def resolve_under_root(root: Path, declared: str) -> tuple[Path, str]:
    """Resolve `declared` under `root`; refuse every escape.

    Returns (absolute_source, relative_posix). Raises PathEscape for a
    relative path that leaves the root, and ConfigError for an empty or
    absolute entry.
    """
    if not isinstance(declared, str) or not declared.strip():
        raise ConfigError("invalid allowlist entry: not a non-empty string")
    cleaned = declared.strip()
    if cleaned.startswith("./"):
        cleaned = cleaned[2:]
    cleaned = cleaned.replace("\\", "/")
    if cleaned.startswith("/") or "\0" in cleaned:
        raise PathEscape(f"allowlist path must be relative: {declared!r}")
    parts = [p for p in cleaned.split("/") if p not in ("", ".")]
    if ".." in parts:
        raise PathEscape(f"allowlist path escapes the source root: {declared!r}")
    root_resolved = root.resolve()
    candidate = (root_resolved / Path(*parts)).resolve() if parts else root_resolved
    if candidate != root_resolved and root_resolved not in candidate.parents:
        raise PathEscape(f"allowlist path escapes the source root: {declared!r}")
    return candidate, "/".join(parts)


def path_refusal(rel_path: str, config: Config) -> str | None:
    """Why `rel_path` may not be published, or None when it may.

    The DENIED sets are the engine defaults narrowed by the manifest's
    `publish.deny_segments` / `publish.deny_names` keys.
    """
    segments = [s for s in rel_path.split("/") if s]
    if not segments:
        return "empty path"
    denied_segments = {s.lower() for s in config.publish.deny_segments}
    for segment in segments:
        if segment.lower() in denied_segments:
            return f'internal path segment "{segment}" is never publishable'
    basename = segments[-1]
    allowed_names = set(config.publish.deny_names)
    for pattern in DENIED_FILENAME_PATTERNS:
        if pattern.pattern not in allowed_names:
            continue
        if pattern.search(basename):
            return f"internal document class ({pattern.pattern}) is never publishable"
    return None


def secret_refusal(content: str) -> str | None:
    """The matched secret CLASS in `content`, or None when clean.

    Deliberately conservative: a false positive costs one blocked doc,
    a false negative costs a leaked key.
    """
    if not isinstance(content, str):
        return None
    for pattern in SECRET_PATTERNS:
        if pattern.search(content):
            return f"content matches the secret class {pattern.pattern!r}"
    return None


def load_allowlist(path: Path) -> tuple[str, ...]:
    """Read the allowlist file: {"files": ["relative/path.md", ...]}."""
    if not path.is_file():
        raise ConfigError(f"allowlist file not found: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ConfigError(f"allowlist file does not parse: {exc}") from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("files"), list):
        raise ConfigError('allowlist must be an object with a "files" array')
    files: list[str] = []
    for entry in raw["files"]:
        if not isinstance(entry, str):
            raise ConfigError(f"allowlist entry must be a string: {entry!r}")
        files.append(entry)
    return tuple(files)


def validate(root: Path, config: Config) -> list[Refusal]:
    """Run the gates over every allowlisted entry. Read-only."""
    allowlist_path = (root / config.publish.allowlist).resolve()
    files = load_allowlist(allowlist_path)
    source_root = (root / config.publish.source_dir).resolve()
    refusals: list[Refusal] = []
    for entry in files:
        try:
            _, rel = resolve_under_root(source_root, entry)
        except PathEscape as exc:
            refusals.append(Refusal(str(entry), str(exc)))
            continue
        except ConfigError as exc:
            refusals.append(Refusal(str(entry), str(exc)))
            continue
        denial = path_refusal(rel, config)
        if denial:
            refusals.append(Refusal(rel, denial))
            continue
        src = source_root / rel
        if not src.is_file():
            refusals.append(Refusal(rel, "allowlisted file missing under the source root"))
            continue
        secret = secret_refusal(src.read_text(encoding="utf-8", errors="replace"))
        if secret:
            refusals.append(Refusal(rel, secret))
    return refusals


PUBLISHED_README = """# {title}

{note}

Generated from `{allowlist}` via `docpol publish`; do not edit as
source of truth.
"""


@dataclass(frozen=True)
class PublishReport:
    """What a publish run did (or refused)."""

    refused: tuple[Refusal, ...]
    wrote: tuple[str, ...] = ()
    readme: str = ""

    @property
    def ok(self) -> bool:
        return not self.refused


def publish(root: Path, config: Config) -> PublishReport:
    """Copy every allowlisted file into the published tree.

    Gates run BEFORE any copy. A refusal returns a report with
    `refused` filled and NOTHING copied.
    """
    refusals = validate(root, config)
    if refusals:
        return PublishReport(refused=tuple(refusals))

    files = load_allowlist((root / config.publish.allowlist).resolve())
    source_root = (root / config.publish.source_dir).resolve()
    published_root = (root / config.publish.published_dir).resolve()
    wrote: list[str] = []
    import shutil

    if published_root.exists():
        for child in published_root.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    readme = PUBLISHED_README.format(
        title="published docs",
        note=config.publish.readme_note,
        allowlist=config.publish.allowlist,
    )
    (published_root / "README.md").parent.mkdir(parents=True, exist_ok=True)
    (published_root / "README.md").write_text(readme, encoding="utf-8")

    for entry in files:
        _, rel = resolve_under_root(source_root, entry)
        src = source_root / rel
        dst = published_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        wrote.append(rel)
    return PublishReport(refused=(), wrote=tuple(wrote), readme=readme)
