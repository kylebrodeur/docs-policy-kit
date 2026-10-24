"""The config loader: fail-closed manifest errors."""

from __future__ import annotations

from pathlib import Path

import pytest

from docpol.config import Config, ConfigError

MINIMAL = """\
version = "0.1.0"

[derived]
mode = "derived-copy"

[[derived.pairs]]
name = "p"
source_dir = "private"
target_dir = "public"
guides = ["quickstart.md"]

[publish]
allowlist = "allowlist.json"
source_dir = "private"
published_dir = "published"

[audit]
source_dir = "docs"
extensions = [".md"]
lane_key = "docs"
"""


def _write(kit: Path, text: str) -> Path:
    path = kit / "doc-policy.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_minimal_manifest_loads(tmp_path: Path) -> None:
    cfg = Config.load(_write(tmp_path, MINIMAL))
    assert cfg.version == "0.1.0"
    assert cfg.derived[0].name == "p"
    assert cfg.publish.deny_segments  # engine defaults apply


def test_missing_manifest_names_the_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="manifest not found"):
        Config.load(tmp_path / "doc-policy.toml")


def test_unparsable_manifest_is_a_named_error(tmp_path: Path) -> None:
    path = _write(tmp_path, "version = [unclosed\n")
    with pytest.raises(ConfigError, match="does not parse"):
        Config.load(path)


@pytest.mark.parametrize(
    "mutation",
    [
        'version = ""',
        '[derived]\nmode = "wrong"',
        "no-derived = true",
    ],
)
def test_shape_errors_name_the_key(tmp_path: Path, mutation: str) -> None:
    text = mutation if mutation.startswith(("version", "no-derived")) else None
    if text is None:
        with pytest.raises(ConfigError):
            Config.load(_write(tmp_path, MINIMAL + "\n" + mutation))
        return
    stripped = "\n".join(
        line for line in MINIMAL.splitlines() if not line.startswith("version =")
    )
    with pytest.raises(ConfigError):
        Config.load(_write(tmp_path, stripped + ("\n" if mutation.startswith("version") else "\n" + mutation)))


def test_derived_pair_missing_key_names_it(tmp_path: Path) -> None:
    bad = MINIMAL.replace('guides = ["quickstart.md"]\n', "")
    with pytest.raises(ConfigError, match=r"pairs\[0\]: missing 'guides'"):
        Config.load(_write(tmp_path, bad))


def test_publish_missing_key_names_it(tmp_path: Path) -> None:
    bad = MINIMAL.replace('published_dir = "published"\n', "")
    with pytest.raises(ConfigError, match=r"publish: missing required key"):
        Config.load(_write(tmp_path, bad))


def test_guard_forbidden_without_pattern_names_it(tmp_path: Path) -> None:
    text = (
        MINIMAL
        + '\n[[guard]]\nname = "g"\nsource = "s"\nwhy = "w"\nkind = "forbid"\ntargets = ["x"]\n'
    )
    with pytest.raises(ConfigError, match="forbid.*pattern"):
        Config.load(_write(tmp_path, text))


def test_empty_pairs_table_refused(tmp_path: Path) -> None:
    bad = MINIMAL.replace(
        '[[derived.pairs]]\nname = "p"\nsource_dir = "private"\ntarget_dir = "public"\nguides = ["quickstart.md"]\n\n',
        "",
    )
    with pytest.raises(ConfigError, match="pairs: missing required array"):
        Config.load(_write(tmp_path, bad))
