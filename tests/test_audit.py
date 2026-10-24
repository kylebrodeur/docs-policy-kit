"""The audit module."""

from __future__ import annotations

from pathlib import Path

import pytest

from docpol.audit import audit, summary
from docpol.config import Config


@pytest.fixture
def audited(kit: Path) -> Path:
    docs = kit / "docs"
    docs.mkdir()
    (docs / "guide.md").write_text(
        "# guide\n\nSTATUS: CURRENT\n\nSee `docs/other.md` and `docs/gone.md`.\n",
        encoding="utf-8",
    )
    (docs / "other.md").write_text("# other\nplain\n", encoding="utf-8")
    (docs / "gone.md").unlink(missing_ok=True)  # referenced, never created
    return kit


def _load(kit: Path) -> Config:
    return Config.load(kit / "doc-policy.toml")


def test_audit_reports_status_and_dead_refs(audited: Path) -> None:
    rows = audit(audited, _load(audited))
    by_name = {r.path.split("/")[-1]: r for r in rows}
    guide = by_name["guide.md"]
    assert guide.status == "CURRENT"
    assert guide.dead_refs == ("docs/gone.md",)
    assert by_name["other.md"].status is None


def test_audit_summary_counts(audited: Path) -> None:
    text = summary(audit(audited, _load(audited)))
    assert "markdown files:        2" in text
    assert "with dead references:  1" in text


def test_audit_missing_source_dir_is_named_error(kit: Path) -> None:
    with pytest.raises(Exception, match="audit source_dir"):
        audit(kit, _load(kit))
