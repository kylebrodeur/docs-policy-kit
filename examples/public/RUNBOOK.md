# private-source RUNBOOK (the SOURCE truth)

The operator reference in the private tree. A derived copy ships
publicly, rewritten by the manifest.

Errors:

```
docpol: manifest not found: doc-policy.toml
```
Fix: point `--manifest` at the kit root's `doc-policy.toml`.

```
publish: REFUSED <path>: internal document class (...) is never publishable
```
Fix: remove the entry from the allowlist; it is internal-by-construction.

Recovery: if a publish copied a file it must not have, `git restore`
the published tree and re-run `docpol check`; the gate report names the
entry that should have been refused.