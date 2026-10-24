"""The CLI verbs end to end (check, sync, publish)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from docpol import cli


@pytest.fixture
def wired(kit_with_copy: Path) -> Path:
    (kit_with_copy / "allowlist.json").write_text('{"files": ["quickstart.md"]}')
    return kit_with_copy


def test_check_clean_wired_kit_exits_zero(wired: Path, capsys) -> None:
    assert cli.main(["check", str(wired)]) == 0
    out = capsys.readouterr().out
    assert "derive: ok" in out
    assert "publish policy: ok" in out
    assert "guards: ok" in out
    assert "prose: ok" in out


def test_check_reports_each_failing_gate(wired: Path, capsys) -> None:
    target = wired / "public" / "quickstart.md"
    target.write_text(target.read_text() + "\ndrift\n")
    (wired / "private" / "scratchpad-note.md").write_text("x")
    (wired / "allowlist.json").write_text(
        json.dumps({"files": ["quickstart.md", "scratchpad-note.md"]})
    )
    assert cli.main(["check", str(wired)]) == 1
    out = capsys.readouterr().out + capsys.readouterr().err
    assert "derive: FAIL" in out
    assert "publish policy: FAIL" in out


def test_sync_clears_drift_then_check_is_green(wired: Path, capsys) -> None:
    target = wired / "public" / "quickstart.md"
    target.write_text("drifted entirely\n")
    assert cli.main(["sync", str(wired)]) == 0
    assert cli.main(["check", str(wired)]) == 0


def test_publish_refusal_exits_nonzero_and_copies_nothing(
    wired: Path, capsys
) -> None:
    (wired / "private" / "leaky.md").write_text(
        "k: sk-dEmoTeStRuNNEr-0123456789abcdef\n"
    )
    (wired / "allowlist.json").write_text(
        json.dumps({"files": ["quickstart.md", "leaky.md"]})
    )
    assert cli.main(["publish", str(wired)]) == 1
    captured = capsys.readouterr()
    assert "REFUSED" in (captured.err + captured.out)
    assert not (wired / "published").exists()


def test_missing_manifest_is_exit_two(tmp_path: Path, capsys) -> None:
    assert cli.main(["check", str(tmp_path)]) == 2
