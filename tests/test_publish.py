"""Mode 2: allowlist validation, secret refusal, path escape, publish."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from docpol.config import Config, ConfigError
from docpol.publish import (
    PathEscape,
    publish,
    resolve_under_root,
    validate,
)


def _load(kit: Path) -> Config:
    return Config.load(kit / "doc-policy.toml")


def _allow(kit: Path, files: list[str]) -> None:
    (kit / "allowlist.json").write_text(
        json.dumps({"files": files}), encoding="utf-8"
    )


# ── the allowlist file ───────────────────────────────────────────────


def test_missing_allowlist_is_a_named_error(kit: Path) -> None:
    with pytest.raises(ConfigError, match="allowlist file not found"):
        validate(kit, _load(kit))


def test_malformed_allowlist_is_a_named_error(kit: Path) -> None:
    (kit / "allowlist.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(ConfigError, match="does not parse"):
        validate(kit, _load(kit))


def test_allowlist_without_files_array_is_refused(kit: Path) -> None:
    (kit / "allowlist.json").write_text('{"paths": []}', encoding="utf-8")
    with pytest.raises(ConfigError, match='"files" array'):
        validate(kit, _load(kit))


# ── path escape ──────────────────────────────────────────────────────


def test_parent_escape_is_rejected(kit: Path) -> None:
    with pytest.raises(PathEscape, match="escapes"):
        resolve_under_root(kit / "private", "../../etc/passwd")


def test_absolute_path_is_rejected(kit: Path) -> None:
    with pytest.raises(PathEscape, match="relative"):
        resolve_under_root(kit / "private", "/etc/passwd")


def test_null_byte_is_rejected(kit: Path) -> None:
    with pytest.raises(PathEscape):
        resolve_under_root(kit / "private", "quick\0.md")


def test_escape_inside_a_dotted_prefix_is_rejected(kit: Path) -> None:
    # a path that looks nested but climbs out via a .. segment
    with pytest.raises(PathEscape):
        resolve_under_root(kit / "private", "sub/../../quickstart.md")


def test_dot_prefix_and_empty_segments_are_cleaned(kit: Path) -> None:
    abs_path, rel = resolve_under_root(kit / "private", "./quickstart.md")
    assert rel == "quickstart.md"
    assert abs_path == (kit / "private" / "quickstart.md").resolve()


# ── allowlist validation (class + missing) ───────────────────────────


def test_denied_segment_refuses_the_entry(kit: Path) -> None:
    (kit / "private" / "scratchpad-note.md").write_text("x", encoding="utf-8")
    _allow(kit, ["quickstart.md", "scratchpad-note.md"])
    refusals = validate(kit, _load(kit))
    assert [r.path for r in refusals] == ["scratchpad-note.md"]
    assert "document class" in refusals[0].reason


def test_denied_directory_segment_refuses_the_entry(kit: Path) -> None:
    (kit / "private" / "session").mkdir()
    (kit / "private" / "session" / "note.md").write_text("x", encoding="utf-8")
    _allow(kit, ["session/note.md"])
    refusals = validate(kit, _load(kit))
    assert len(refusals) == 1
    assert 'internal path segment "session"' in refusals[0].reason


def test_allowlisted_but_missing_file_is_refused(kit: Path) -> None:
    _allow(kit, ["quickstart.md", "no-such-file.md"])
    refusals = validate(kit, _load(kit))
    assert refusals[-1].path == "no-such-file.md"
    assert "missing" in refusals[-1].reason


def test_clean_allowlist_passes(kit: Path) -> None:
    _allow(kit, ["quickstart.md"])
    assert validate(kit, _load(kit)) == []


# ── the secret scan ──────────────────────────────────────────────────


def test_provider_key_prefix_refuses_the_file(kit: Path) -> None:
    (kit / "private" / "keys.md").write_text(
        "token: sk-dEmoTeStRuNNEr-0123456789abcdef\n", encoding="utf-8"
    )
    _allow(kit, ["keys.md"])
    refusals = validate(kit, _load(kit))
    assert len(refusals) == 1
    assert "secret class" in refusals[0].reason


def test_secret_shaped_assignment_refuses_the_file(kit: Path) -> None:
    (kit / "private" / "config.md").write_text(
        'apiKey = "EXAMPLE-DEMO-NOT-SECRET-12345"\n', encoding="utf-8"
    )
    _allow(kit, ["config.md"])
    refusals = validate(kit, _load(kit))
    assert len(refusals) == 1


def test_pem_block_refuses_the_file(kit: Path) -> None:
    (kit / "private" / "pem.md").write_text("-----BEGIN PRIVATE KEY-----\n")
    _allow(kit, ["pem.md"])
    assert len(validate(kit, _load(kit))) == 1


def test_clean_content_publishes(kit: Path) -> None:
    (kit / "private" / "clean.md").write_text("# clean\nplain prose\n")
    _allow(kit, ["clean.md"])
    assert validate(kit, _load(kit)) == []


# ── publish (the gates run BEFORE any copy) ──────────────────────────


def test_publish_copies_clean_allowlist(published_kit: Path) -> None:
    report = publish(published_kit, _load(published_kit))
    assert report.ok
    assert set(report.wrote) == {"quickstart.md"}
    assert (published_kit / "published" / "quickstart.md").is_file()
    assert (published_kit / "published" / "README.md").is_file()


def test_publish_refusal_copies_nothing(kit: Path) -> None:
    (kit / "private" / "keys.md").write_text("k: sk-dEmoTeStRuNNEr-0123456789abcdef\n")
    _allow(kit, ["quickstart.md", "keys.md"])
    report = publish(kit, _load(kit))
    assert not report.ok
    assert report.wrote == ()
    assert not (kit / "published").exists()


def test_publish_rejects_escape_entry_before_any_copy(kit: Path) -> None:
    _allow(kit, ["../outside.md"])
    (kit.parent / "outside.md").write_text("secret adjacent")
    report = publish(kit, _load(kit))
    assert not report.ok
    assert not (kit / "published").exists()


def test_publish_is_fresh_each_run(published_kit: Path) -> None:
    publish(published_kit, _load(published_kit))
    stale = published_kit / "published" / "stale.md"
    stale.write_text("stale")
    publish(published_kit, _load(published_kit))
    assert not stale.exists()
