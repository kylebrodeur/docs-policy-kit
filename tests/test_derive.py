"""Mode 1: drift detection and sync."""

from __future__ import annotations

from pathlib import Path

from docpol.config import Config
from docpol.derive import check, expected_text, sync


def _load(kit: Path) -> Config:
    return Config.load(kit / "doc-policy.toml")


def test_expected_text_applies_rewrite_strip_and_base_url(kit: Path) -> None:
    config = _load(kit)
    text = expected_text((kit / "private" / "quickstart.md").read_text(), config.derived[0])
    assert "(https://example.demo/docs/quickstart.md)" in text
    assert "docs/release/DESIGN.md" not in text
    # an undeclared relative link (RUNBOOK.md is not in guides) stays as-is
    assert "(RUNBOOK.md)" in text


def test_clean_copy_has_no_drift(kit_with_copy: Path) -> None:
    assert check(kit_with_copy, _load(kit_with_copy)) == []


def test_drift_detected_when_copy_is_edited(kit_with_copy: Path) -> None:
    target = kit_with_copy / "public" / "quickstart.md"
    target.write_text(target.read_text() + "\nA hand edit.\n", encoding="utf-8")
    findings = check(kit_with_copy, _load(kit_with_copy))
    assert len(findings) == 1
    assert "drifts" in findings[0].problem


def test_drift_detected_when_copy_missing(kit: Path) -> None:
    findings = check(kit, _load(kit))
    assert [(f.guide, f.problem) for f in findings] == [
        ("quickstart.md", "derived copy missing"),
    ]


def test_drift_detected_when_source_missing(kit_with_copy: Path) -> None:
    (kit_with_copy / "private" / "quickstart.md").unlink()
    findings = check(kit_with_copy, _load(kit_with_copy))
    assert findings[0].problem == "private source missing"


def test_sync_writes_the_expected_text_and_clears_drift(kit_with_copy: Path) -> None:
    target = kit_with_copy / "public" / "quickstart.md"
    target.write_text("drifted\n", encoding="utf-8")
    config = _load(kit_with_copy)
    actions = sync(kit_with_copy, config)
    assert any("wrote" in a for a in actions)
    assert check(kit_with_copy, config) == []


def test_sync_skips_current_copies(kit_with_copy: Path) -> None:
    config = _load(kit_with_copy)
    actions = sync(kit_with_copy, config)
    assert actions == ["current: public/quickstart.md"]


def test_sync_never_creates_a_copy_without_a_source(kit: Path) -> None:
    from docpol.derive import sync as _sync

    (kit / "private" / "quickstart.md").unlink()
    actions = _sync(kit, _load(kit))
    assert actions == []
    assert not (kit / "public" / "quickstart.md").exists()
