"""Fixture: a synthetic kit tree (manifest + source docs + derived copies)."""

from __future__ import annotations

from pathlib import Path

import pytest

from docpol.config import Config

MANIFEST = """\
version = "0.1.0"

[derived]
mode = "derived-copy"

[[derived.pairs]]
name = "demo"
source_dir = "private"
target_dir = "public"
guides = ["quickstart.md"]
base_url = "https://github.com/example/demo/tree/main/docs"
rewrites = [
    { from = "(../private-source/quickstart.md)", to = "(https://example.demo/docs/quickstart.md)" },
]
strips = [
    "Design notes: `docs/release/DESIGN.md` in\\nthe system repo.\\n",
]

[publish]
allowlist = "allowlist.json"
source_dir = "private"
published_dir = "published"

[[guard]]
name = "guard-demo"
source = "test ruling"
why = "demo why"
kind = "require"
targets = ["doc-policy.toml"]

[prose]
banned_words = ["seamlessly", "utilize", "leverage", "robust"]
banned_chars = "\\u2014\\u2013"
skip_patterns = ["prose_skip_patterns"]

[audit]
source_dir = "docs"
extensions = [".md"]
lane_key = "docs"
"""

SOURCE_TEXT = """# source quickstart

See (../private-source/quickstart.md) for itself.

Design notes: `docs/release/DESIGN.md` in
the system repo.

Next: (RUNBOOK.md).
"""


@pytest.fixture
def kit(tmp_path: Path) -> Path:
    """A synthetic kit root: private source, a derived copy, the manifest."""
    root = tmp_path / "kit"
    (root / "private").mkdir(parents=True)
    (root / "private" / "quickstart.md").write_text(SOURCE_TEXT, encoding="utf-8")
    root_manifest = root / "doc-policy.toml"
    root_manifest.write_text(MANIFEST, encoding="utf-8")
    return root


@pytest.fixture
def kit_with_copy(kit: Path) -> Path:
    """The fixture with a CORRECT derived copy (as sync would write it)."""
    from docpol.derive import expected_text

    config = Config.load(kit / "doc-policy.toml")
    derived = config.derived[0]
    text = expected_text((kit / "private" / "quickstart.md").read_text(), derived)
    (kit / "public").mkdir()
    (kit / "public" / "quickstart.md").write_text(text, encoding="utf-8")
    return kit


@pytest.fixture
def published_kit(kit: Path) -> Path:
    """The fixture with a clean allowlist and a published tree."""
    (kit / "allowlist.json").write_text(
        '{ "files": ["quickstart.md"] }', encoding="utf-8"
    )
    return kit
