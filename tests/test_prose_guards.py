"""The prose gate and the ruling guards."""

from __future__ import annotations

from pathlib import Path

from docpol.config import Config
from docpol.guards import run_all, run_guard
from docpol.prose import check as prose_check


def _load(kit: Path) -> Config:
    return Config.load(kit / "doc-policy.toml")


# ── prose ────────────────────────────────────────────────────────────


def test_banned_word_is_reported(kit_with_copy: Path) -> None:
    (kit_with_copy / "public" / "quickstart.md").write_text(
        "This works seamlessly with everything.\n", encoding="utf-8"
    )
    findings = prose_check(kit_with_copy, _load(kit_with_copy), files=[kit_with_copy / "public" / "quickstart.md"])
    assert [(f.file, f.rule) for f in findings] == [("quickstart.md", "seamlessly")]


def test_banned_char_is_reported_by_rule_name_only(kit_with_copy: Path) -> None:
    (kit_with_copy / "public" / "quickstart.md").write_text(
        "an em dash \u2014 here\n", encoding="utf-8"
    )
    findings = prose_check(kit_with_copy, _load(kit_with_copy), files=[kit_with_copy / "public" / "quickstart.md"])
    assert findings[0].rule == "banned-chars"


def test_skip_patterns_exempt_rule_citation_lines(kit_with_copy: Path) -> None:
    line = "The skip patterns live in prose_skip_patterns in the manifest."
    (kit_with_copy / "public" / "quickstart.md").write_text(line + "\n", encoding="utf-8")
    assert prose_check(kit_with_copy, _load(kit_with_copy), files=[kit_with_copy / "public" / "quickstart.md"]) == []


def test_word_boundary_match_only(kit_with_copy: Path) -> None:
    # "utilize" inside "utilized" still trips; "utilitarian" does not.
    (kit_with_copy / "public" / "quickstart.md").write_text(
        "utilitarian tools only\n", encoding="utf-8"
    )
    assert prose_check(kit_with_copy, _load(kit_with_copy), files=[kit_with_copy / "public" / "quickstart.md"]) == []


# ── guards ───────────────────────────────────────────────────────────


def test_require_guard_passes_when_present(kit_with_copy: Path) -> None:
    assert run_all(kit_with_copy, _load(kit_with_copy)) == []


def test_require_guard_missing_target_names_it(kit_with_copy: Path) -> None:
    from docpol.config import Guard

    guard = Guard(name="g", source="s", why="w", kind="require", targets=("no-such-file.md",))
    hits = run_guard(kit_with_copy, guard)
    assert hits == ["missing: no-such-file.md"]


def test_absent_guard_reports_present_target(kit_with_copy: Path) -> None:
    from docpol.config import Guard

    (kit_with_copy / "hand-edit.md").write_text("x", encoding="utf-8")
    guard = Guard(name="g", source="s", why="w", kind="absent", targets=("hand-edit.md",))
    hits = run_guard(kit_with_copy, guard)
    assert hits == ["hand-edit.md must not exist"]


def test_forbid_guard_reports_the_line(kit_with_copy: Path) -> None:
    from docpol.config import Guard

    (kit_with_copy / "public" / "quickstart.md").write_text(
        "see docs/release/DESIGN.md for the internals\n", encoding="utf-8"
    )
    guard = Guard(
        name="g", source="s", why="w", kind="forbid",
        targets=("public",), pattern=r"docs/release/[A-Z]+\.md",
    )
    hits = run_guard(kit_with_copy, guard)
    assert hits == ["public/quickstart.md:1"]


def test_forbid_guard_scans_all_text_files_under_a_dir(kit_with_copy: Path) -> None:
    from docpol.config import Guard

    (kit_with_copy / "public" / "nested").mkdir()
    (kit_with_copy / "public" / "nested" / "deep.md").write_text(
        "a $$LEAKYVALUE here\n", encoding="utf-8"
    )
    guard = Guard(
        name="g", source="s", why="w", kind="forbid",
        targets=("public",), pattern=r"\$\$LEAKYVALUE",
    )
    hits = run_guard(kit_with_copy, guard)
    assert hits == ["public/nested/deep.md:1"]
