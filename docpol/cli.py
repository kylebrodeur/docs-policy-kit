"""docpol: the docs-policy-kit engine CLI.

One config file (the manifest), one CLI, three verbs:

    docpol check <root> [--manifest <toml>]   every gate, read-only
    docpol sync  <root> [--manifest <toml>]   mode 1: rewrite derived copies
    docpol publish <root> [--manifest <toml>] mode 2: gated allowlist copy

Exit 0 when every gate passes, 1 otherwise. A gate finding names its
fix; findings are evidence, never noise.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import audit as audit_mod
from . import derive, guards, prose
from .config import Config, ConfigError
from .publish import PathEscape, validate
from .publish import publish as publish_mod


def _config(root: Path, manifest: str | None) -> Config:
    path = Path(manifest) if manifest else (root / "doc-policy.toml")
    return Config.load(path if path.is_absolute() else (Path.cwd() / path))


def cmd_check(root: Path, config: Config) -> int:
    ok = True

    drift = derive.check(root, config)
    print(f"derive: {'ok' if not drift else 'FAIL'} (drift: {len(drift)})")
    for f in drift:
        print(f"  - {f}")
        ok = False

    refusals = validate(root, config)
    print(f"publish policy: {'ok' if not refusals else 'FAIL'} (refusals: {len(refusals)})")
    for r in refusals:
        print(f"  - REFUSED {r.path}: {r.reason}")
        ok = False

    guard_findings = guards.run_all(root, config)
    if guard_findings:
        for g in config.guards:
            rows = guards.run_guard(root, g)
            if rows:
                ok = False
                print(f"guard {g.name}: FAIL ({len(rows)})")
                for h in rows:
                    print(f"    - {h}")
                print(f"    why: {g.why}")
    else:
        print("guards: ok")

    tracked = prose.tracked_files(root)
    pf = prose.check(root, config, files=tracked)
    print(f"prose: {'ok' if not pf else 'FAIL'} ({len(pf)} findings)")
    for f in pf[:20]:
        print(f"  - {f}")
    if pf:
        ok = False

    return 0 if ok else 1


def cmd_sync(root: Path, config: Config) -> int:
    drift = derive.check(root, config)
    if not drift:
        print("sync: nothing to do (no drift)")
        return 0
    for action in derive.sync(root, config):
        print(f"sync: {action}")
    remaining = derive.check(root, config)
    if remaining:
        for f in remaining:
            print(f"  - {f}")
        return 1
    print("sync: every derived copy now matches its source")
    return 0


def cmd_publish(root: Path, config: Config) -> int:
    report = publish_mod(root, config)
    for r in report.refused:
        print(f"publish: REFUSED {r.path}: {r.reason}", file=sys.stderr)
    if not report.ok:
        print(f"publish: {len(report.refused)} allowlist entries refused; nothing was copied", file=sys.stderr)
        return 1
    if not report.wrote:
        print("publish: allowlist empty; published tree ready (nothing written)")
        return 0
    for rel in report.wrote:
        print(f"publish: wrote {rel}")
    print(f"publish: copied {len(report.wrote)} file(s) into {config.publish.published_dir}")
    return 0


def cmd_audit(root: Path, config: Config) -> int:
    rows = audit_mod.audit(root, config)
    print(audit_mod.summary(rows))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="docpol", description="the docs-policy-kit engine"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "sync", "publish", "audit"):
        p = sub.add_parser(name)
        p.add_argument("root", nargs="?", default=".", help="the repo root to operate on")
        p.add_argument("--manifest", default=None, help="path to doc-policy.toml (default: <root>/doc-policy.toml)")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    try:
        config = _config(root, args.manifest)
    except (ConfigError, PathEscape) as exc:
        print(f"docpol: {exc}", file=sys.stderr)
        return 2

    if args.command == "check":
        return cmd_check(root, config)
    if args.command == "sync":
        return cmd_sync(root, config)
    if args.command == "publish":
        return cmd_publish(root, config)
    return cmd_audit(root, config)


if __name__ == "__main__":
    raise SystemExit(main())
