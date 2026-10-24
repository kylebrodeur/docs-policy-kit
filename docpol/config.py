"""Load the doc-policy.toml manifest.

One file carries every policy decision the engine enforces:

- ``[[derived.pairs]]``: the repo-to-doc mapping (mode 1, derived copy)
- ``[publish]``: the publication gate (mode 2, allowlisted copy)
- ``[[guard]]``: the ruling guards (locked rulings become checks)
- ``[audit]``: the inventory's source root and extension filter

Policy data lives here and nowhere else. A rule that is not in the
manifest does not exist. The loader is fail-closed: a missing file, a
missing key, or a key of the wrong kind is a ConfigError naming the key,
never a silent default.
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path


class ConfigError(Exception):
    """The manifest is missing, malformed, or contradicts itself."""


# The engine's own policy constants. They are CONSTANTS and live in code,
# not in the manifest: the manifest declares each deployment's data, while
# these declare what a "path escape" or a "secret" IS. Extending them is a
# code change with a review, not a manifest edit.
DENIED_DIR_SEGMENTS = frozenset(
    {"scratchpads", "scratchpad", "session", "sessions", "agents", ".omp", ".grok"}
)

DENIED_FILENAME_PATTERNS = (
    re.compile(r"board", re.IGNORECASE),
    re.compile(r"working", re.IGNORECASE),
    re.compile(r"^control\.", re.IGNORECASE),
    re.compile(r"^decisions\.", re.IGNORECASE),
    re.compile(r"handoff", re.IGNORECASE),
    re.compile(r"scratchpad", re.IGNORECASE),
    re.compile(r"system-map", re.IGNORECASE),
    re.compile(r"^CLAUDE\.", re.IGNORECASE),
    re.compile(r"^AGENTS\.", re.IGNORECASE),
    re.compile(r"internal", re.IGNORECASE),
)

SECRET_PATTERNS = (
    re.compile(r"\b(sk|rk|pk)_(live|test)_[A-Za-z0-9]{8,}"),
    re.compile(r"\bsk-[A-Za-z0-9-]{16,}"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{30,}"),
    re.compile(
        r"\b[A-Za-z0-9_]*"
        r"(?i:SECRET|TOKEN|API_?KEY|PASSWORD|PRIVATE_?KEY)"
        r"[A-Za-z0-9_]*\s*[:=]\s*[\"'`][^\"'`\s]{12,}[\"'`]"
    ),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bBearer\s+[A-Za-z0-9_-]{20,}\."),
)

# The prose gates, from the family conventions (DOC-STANDARD.md writing
# rules). The WORDS and CHARS are banned by the engine, but a doc that
# must name them cites the manifest keys `prose_banned` and
# `prose_skip_patterns` instead of spelling them.
PROSE_WORD_BANNED = frozenset({"robust", "leverage", "seamlessly", "utilize"})
PROSE_CHARS_BANNED = "\u2014\u2013"

# Lines that DEFINE the rule are citations, not instances: a skip pattern
# list in the manifest exempts them (see README "Rule citation lines").
DEFAULT_SKIP_PATTERNS = (
    r"prose_banned",
    r"prose_skip_patterns",
    r"\(the skip patterns exist for lines that DEFINE the rule",
)


@dataclass(frozen=True)
class DerivedPair:
    """One derived-copy mapping: private source docs to one public repo."""

    name: str
    source_dir: str
    target_dir: str
    guides: tuple[str, ...]
    base_url: str = ""
    rewrites: tuple[tuple[str, str], ...] = ()
    strips: tuple[str, ...] = ()


@dataclass(frozen=True)
class Publish:
    """The publication gate: one root, one allowlist, one policy."""

    allowlist: str
    deny_segments: tuple[str, ...]
    deny_names: tuple[str, ...]
    source_dir: str
    published_dir: str
    readme_note: str = ""

    @classmethod
    def from_table(cls, table: dict, defaults: "Publish") -> "Publish":
        if not isinstance(table, dict):
            raise ConfigError("publish: must be a table")
        merged = {
            "deny_segments": defaults.deny_segments,
            "deny_names": defaults.deny_names,
        }
        for key in ("deny_segments", "deny_names"):
            if key in table:
                got = table[key]
                if not isinstance(got, list) or not all(isinstance(v, str) for v in got):
                    raise ConfigError(f"publish.{key}: must be an array of strings")
                merged[key] = tuple(got)
        for key in ("allowlist", "source_dir", "published_dir"):
            if key not in table:
                raise ConfigError(f"publish: missing required key '{key}'")
            if not isinstance(table[key], str):
                raise ConfigError(f"publish.{key}: must be a string")
        for key in ("readme_note",):
            if key in table and not isinstance(table[key], str):
                raise ConfigError(f"publish.{key}: must be a string")
        return cls(
            allowlist=table["allowlist"].strip("/"),
            deny_segments=tuple(merged["deny_segments"]),
            deny_names=tuple(merged["deny_names"]),
            source_dir=table["source_dir"].strip("/"),
            published_dir=table["published_dir"].strip("/"),
            readme_note=table.get("readme_note", defaults.readme_note),
        )


@dataclass(frozen=True)
class Guard:
    """One ruling, stated as a check: a path shape or a forbidden regex."""

    name: str
    source: str
    why: str
    kind: str
    targets: tuple[str, ...]
    pattern: str = ""


@dataclass(frozen=True)
class Audit:
    """The inventory's data: which root, which extensions, which lane key."""

    source_dir: str
    extensions: tuple[str, ...]
    lane_key: str


@dataclass(frozen=True)
class Config:
    """The whole manifest, parsed."""

    version: str
    derived: tuple[DerivedPair, ...]
    publish: Publish
    guards: tuple[Guard, ...]
    audit: Audit
    prose_banned: tuple[str, ...]
    prose_chars_banned: str
    prose_skip_patterns: tuple[str, ...]
    path: Path | None = None

    @classmethod
    def load(cls, path: Path) -> "Config":
        if not path.is_file():
            raise ConfigError(f"manifest not found: {path}")
        try:
            raw = tomllib.loads(path.read_text(encoding="utf-8"))
        except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
            raise ConfigError(f"{path.name}: does not parse: {exc}") from exc

        version = raw.get("version")
        if not isinstance(version, str) or not version.strip():
            raise ConfigError("version: must be a non-empty string")

        derived_table = raw.get("derived")
        if not isinstance(derived_table, dict):
            raise ConfigError("derived: missing required table")
        if derived_table.get("mode") != "derived-copy":
            raise ConfigError('derived: mode: must be "derived-copy"')
        pairs: list[DerivedPair] = []
        for i, row in enumerate(_rows("pairs", derived_table)):
            pairs.append(_derived_pair(i, row))

        base = {"deny_segments": tuple(sorted(DENIED_DIR_SEGMENTS))}
        base["deny_names"] = tuple(p.pattern for p in DENIED_FILENAME_PATTERNS)
        publish_table = raw.get("publish")
        if publish_table is None:
            raise ConfigError("publish: missing required table")
        publish = Publish.from_table(publish_table, Publish(
            allowlist="", deny_segments=base["deny_segments"],
            deny_names=base["deny_names"], source_dir="", published_dir="",
        ))

        guard_rows = raw.get("guard", [])
        if not isinstance(guard_rows, list) or not all(isinstance(r, dict) for r in guard_rows):
            raise ConfigError("guard: must be an array of tables")
        guards = tuple(_guard_row(i, row) for i, row in enumerate(guard_rows))

        audit_table = raw.get("audit")
        if not isinstance(audit_table, dict):
            raise ConfigError("audit: missing required table")
        for key in ("source_dir", "lane_key"):
            if key not in audit_table:
                raise ConfigError(f"audit: missing required key '{key}'")
            if not isinstance(audit_table[key], str):
                raise ConfigError(f"audit.{key}: must be a string")
        exts = audit_table.get("extensions", [".md"])
        if not isinstance(exts, list) or not all(isinstance(e, str) for e in exts):
            raise ConfigError("audit.extensions: must be an array of strings")

        prose = raw.get("prose", {})
        if not isinstance(prose, dict):
            raise ConfigError("prose: must be a table")
        words = prose.get("banned_words", sorted(PROSE_WORD_BANNED))
        chars = prose.get("banned_chars", PROSE_CHARS_BANNED)
        skips = prose.get("skip_patterns", list(DEFAULT_SKIP_PATTERNS))
        if not isinstance(words, list) or not all(isinstance(w, str) for w in words):
            raise ConfigError("prose.banned_words: must be an array of strings")
        if not isinstance(chars, str) or not chars:
            raise ConfigError("prose.banned_chars: must be a non-empty string")
        if not isinstance(skips, list) or not all(isinstance(s, str) for s in skips):
            raise ConfigError("prose.skip_patterns: must be an array of strings")

        return cls(
            version=version,
            derived=tuple(pairs),
            publish=publish,
            guards=guards,
            audit=Audit(
                source_dir=audit_table["source_dir"].strip("/"),
                extensions=tuple(exts),
                lane_key=audit_table["lane_key"],
            ),
            prose_banned=tuple(words),
            prose_chars_banned=chars,
            prose_skip_patterns=tuple(skips),
            path=path,
        )




def _derived_pair(i: int, row: dict) -> DerivedPair:
        for key in ("name", "source_dir", "target_dir", "guides"):
            if key not in row:
                raise ConfigError(f"derived.pairs[{i}]: missing '{key}'")
        rewrites: list[tuple[str, str]] = []
        for j, rw in enumerate(row.get("rewrites", ())):
            if not isinstance(rw, dict):
                raise ConfigError(f"derived.pairs[{i}].rewrites[{j}]: must be a table")
            if "from" not in rw or "to" not in rw:
                raise ConfigError(
                    f"derived.pairs[{i}].rewrites[{j}]: needs 'from' and 'to'"
                )
            rewrites.append((str(rw["from"]), str(rw["to"])))
        strips = tuple(str(s) for s in row.get("strips", ()))
        return DerivedPair(
            name=str(row["name"]),
            source_dir=str(row["source_dir"]).strip("/"),
            target_dir=str(row["target_dir"]).strip("/"),
            guides=tuple(str(g) for g in row["guides"]),
            base_url=str(row.get("base_url", "")),
            rewrites=tuple(rewrites),
            strips=strips,
        )




def _guard_row(i: int, row: dict) -> Guard:
        if not isinstance(row, dict):
            raise ConfigError(f"guard[{i}]: must be a table")
        for key in ("name", "source", "why", "kind", "targets"):
            if key not in row:
                raise ConfigError(f"guard[{i}]: missing '{key}'")
        kind = row["kind"]
        if kind not in ("absent", "require", "forbid"):
            raise ConfigError(
                f"guard[{i}].kind: must be one of absent, require, forbid (got {kind!r})"
            )
        if kind == "forbid" and not row.get("pattern"):
            raise ConfigError(f"guard[{i}]: kind 'forbid' needs a 'pattern'")
        return Guard(
            name=str(row["name"]),
            source=str(row["source"]),
            why=str(row["why"]),
            kind=kind,
            targets=tuple(str(t) for t in row["targets"]),
            pattern=str(row.get("pattern", "")),
        )


def _rows(key: str, table: dict) -> list[dict]:
    got = table.get(key)
    if got is None:
        raise ConfigError(f"{key}: missing required array of tables")
    if not isinstance(got, list) or not all(isinstance(r, dict) for r in got):
        raise ConfigError(f"{key}: must be an array of tables")
    if not got:
        raise ConfigError(f"{key}: no rows; the kit enforces nothing without them")
    return got
