# docs-policy-kit

A config-driven docs-policy engine: the publication rules for a repo
whose docs are copied from private sources, enforced by exit codes
rather than trust.

Two modes, one engine, one manifest:

| Mode | What it does | Fail closed on |
|---|---|---|
| derived-copy sync | a private source doc is copied to a derived public location through declared rewrites; the engine recomputes the expected public text and rewrites drift | a copy that differs from its source |
| allowlisted publication | only allowlisted paths are copied into the published tree; every entry is checked for content class AND for secret patterns BEFORE anything is copied | an internal file class, a missing file, or one credential-shaped string |

**Start with [docs/quickstart.md](docs/quickstart.md)**: from nothing to
gated docs. Day-to-day operation: [docs/how-to.md](docs/how-to.md). The
full command surface, every error string, and the recovery procedures:
[docs/RUNBOOK.md](docs/RUNBOOK.md).

## Install

The kit is not in a package registry yet. From a checkout or a vendored
copy (facts checked 2026-10-22 against `uv` and `docpol` 0.1.0):

```bash
uv tool install --from "git+https://github.com/kylebrodeur/docs-policy-kit@v0.1.0" docs-policy-kit   # package name, not the script name
# or run without installing:
uv run --project <path-to-kit> docpol --help
```

`<path-to-kit>` is the directory holding this repo's `pyproject.toml`.

    docpol check   <root>    every gate, read-only, red = do not publish
    docpol sync    <root>    mode 1: rewrite drifted derived copies
    docpol publish <root>    mode 2: the gated allowlist copy
    docpol audit   <root>    the docs inventory (read-only)

## The policy data is CONFIG

Every path, pattern, and mapping lives in one manifest,
`doc-policy.toml` at the repo root (a manifest check names the root it
wants). The engine hardcodes two things and only two things: what a
path escape IS (`resolve_under_root`), and the default denied sets
(`docpol/config.py`: the denied internal classes and the secret
classes, applied wherever the manifest does not override them). Extending
the defaults is a code change with review; a deployment narrows them
with the `deny_segments` and `deny_names` keys.

## The gates

| Gate | Refuses when |
|---|---|
| `derive` | a derived copy drifts from its source, or the source itself is missing |
| `publish policy` | an allowlist entry is an internal class, sits in a denied segment, escapes the source root, is missing, or carries a credential-shaped string |
| `guards` | a locked ruling's path shape exists (or is missing), or forbidden text appears |
| `prose` | banned characters or banned words in tracked markdown (rule-citation lines exempt via skip patterns) |

## Tests

55 contract tests (no network; synthetic kit trees via a fixture):

```bash
uv run --project <path-to-kit> pytest tests -q
```

## The skills

[skills/docs-policy-kit/SKILL.md](skills/docs-policy-kit/SKILL.md):
operating the gates and the modes as an agent (this repo ships it).

## Family

This kit is a member of the AI Engineering Control Plane (AI ECP)
family: independent kit repos whose rules are executable. Siblings:
[repo-guards](https://github.com/kylebrodeur/repo-guards) (release and
prose gates), [actions-runner](https://github.com/kylebrodeur/actions-runner)
(the `arun` agent-pipeline runner), [ecp-toolkit](https://github.com/kylebrodeur/ecp-toolkit)
(the `ecp` control-plane CLI),
[agent-workspace-kit](https://github.com/kylebrodeur/agent-workspace-kit)
(the agent-team launcher),
[op-safe](https://github.com/kylebrodeur/op-safe) (the secrets helper), and
[omp-rpc-cli](https://github.com/kylebrodeur/omp-rpc-cli) (persistent
`omp` sessions). The family's standard:
the family documentation standard (in the private control-plane repo).

## Origin

Consolidated on 2026-10-22 from six scattered implementations: a
derived-copy drift gate and its sync runner, an allowlist policy module
and its sync script, and a rulings guard plus a docs audit. The
consolidation moved every policy decision into one manifest; the
reference copies are cited in [docs/RUNBOOK.md](docs/RUNBOOK.md).