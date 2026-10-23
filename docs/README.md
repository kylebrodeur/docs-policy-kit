# Docs

**Start here:** [quickstart.md](quickstart.md), the numbered path from
nothing to gated docs.

## The map

| File | What it is for |
|---|---|
| [quickstart.md](quickstart.md) | The one-time path: install, write the manifest, run both modes, read the gates. |
| [how-to.md](how-to.md) | The tasks you repeat: sync after a source edit, publish, add a guard, fix a finding. |
| [RUNBOOK.md](RUNBOOK.md) | The operator's reference: the full command surface, every manifest key, every error string and its fix, and the recovery procedures. |

One question per how-to lives in the how-to; a task that is not listed
there belongs in a new section, not in this README.

## The rule this directory enforces on itself

The kit gates its own docs: `docpol check .` at the repo root runs the
prose gate over every tracked markdown file here. A doc addition is
correct when the gates are green and the harness (the AI ECP standard)
passes.

```bash
docpol check .
uv run pytest tests -q
uv run ruff check .
```