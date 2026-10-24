# Contributing to docs-policy-kit

## The setup

The kit is Python 3.11+, stdlib only, tooling via `uv`:

```bash
git clone https://github.com/kylebrodeur/docs-policy-kit
cd docs-policy-kit
uv sync --group dev
uv run pytest tests -q
```

Expected output:

```
.......................................................                  [100%]
55 passed in 0.2s (timing varies)
```

No network is needed: the tests build synthetic kit trees in temporary
directories through a fixture (`tests/conftest.py`).

## The gates (this repo polices itself)

```bash
uv run docpol check .
```

Expected: every gate `ok`.

```bash
uv run ruff check .
```

Expected: `All checks passed!`

## Ground rules

- **Stdlib only.** No runtime dependencies. A dependency needs a
  written reason, not convenience.
- **Policy data is CONFIG.** Paths, patterns, mappings, guard rows,
  and banned lists live in the manifest. An engine default is a
  constant with a review trail, and a deployment narrows it per repo;
  a hardcoded fix is a bug.
- **Fail-closed.** A missing manifest, a missing key, an unresolvable
  path, or an unverifiable entry is an error, never a silent pass.
- **Findings carry their fix.** A finding names the command that
  resolves it (`docpol sync`, or the allowlist edit).
- **No em or en dashes, and none of the four banned filler words**, in
  any tracked markdown; the kit's own prose gate enforces this. Because
  this kit is ABOUT banned words and secret patterns, its docs cite the
  config keys (`prose.banned_words`, the `SECRET_PATTERNS` tuple) and
  never spell out a live-looking value. Examples that must show the
  shape use a synthetic, self-labeled value.
- **Tests are contracts.** An engine change lands with a test that
  fails before and passes after; the suite covers drift detection,
  allowlist validation, the secret-pattern refusal, and path-escape
  rejection.

## Workflow

1. Fork, create a feature branch.
2. Set up per the block above.
3. Run the repo's CI commands locally before submitting; they are
   exactly what `.github/workflows/ci.yml` runs (`ruff`, `pytest`,
   `docpol check`).
4. Open a pull request against `main` describing what and why.

## Doc changes

This repo follows the AI ECP documentation standard (README, AGENTS.md,
the skill, quickstart, how-to, runbook, and the health files). Before a
commit that adds or moves a doc:

```bash
uv run pytest tests -q
uv run ruff check .
```

Those commands print pytest and ruff output, not `docs-policy-kit:` lines: the
family harness that prints those lines is in the PRIVATE system repo and is
maintainer-only. A public contributor runs the commands above, and the
family harness runs on the maintainer's side.

## Security

Do not open public issues for security vulnerabilities. See
[SECURITY.md](SECURITY.md) for the private reporting path.

## License

Apache-2.0. By contributing you agree your contributions are licensed
under the project's license.