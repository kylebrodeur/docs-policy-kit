#!/usr/bin/env bash
# Runnable example: the whole docpol surface against this kit's own tree.
# Every output below is captured from a real run of these commands
# (2026-10-22, docpol 0.1.0).
set -euo pipefail
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "== 1. check (gates, read-only)"
uv run --project "$KIT" docpol check "$KIT"

echo
echo "== 2. publish (allowlisted copy with the secret gate)"
uv run --project "$KIT" docpol publish "$KIT"

echo
echo "== 3. what the published tree carries"
ls "$KIT/examples/public-published"

echo
echo "== 4. the secret gate refusing an allowlisted file"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
python3 - "$KIT" "$TMP" <<'PY'
import json, shutil, subprocess, sys
from pathlib import Path

kit, tmp = Path(sys.argv[1]), Path(sys.argv[2])
work = tmp / "kit"
shutil.copytree(
    kit, work,
    ignore=shutil.ignore_patterns(
        ".venv", "uv.lock", "__pycache__", ".git", "public-published", "public"
    ),
)
# an allowlisted file whose content carries a credential-shaped string:
(work / "examples" / "private-source" / "leaky.md").write_text(
    "token: sk-dEmoTeStRuNNEr-0123456789abcdef\n", encoding="utf-8"
)
allow = work / "examples" / "allowlist.json"
allow.write_text(json.dumps({"files": ["quickstart.md", "leaky.md"]}), encoding="utf-8")
result = subprocess.run(
    ["uv", "run", "--project", str(kit), "docpol", "publish", str(work)],
    capture_output=True, text=True,
)
print(result.stderr.strip())
print(f"exit code: {result.returncode}")
published = work / "examples" / "public-published"
print(f"published tree exists: {published.exists()}")
PY