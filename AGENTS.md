# docs-policy-kit: the agent boundary (docpol)

`docpol` turns docs-publication claims into exit codes: derived-copy
drift, allowlisted publication, ruling guards, and the prose gate. This
file is the boundary an agent obeys when operating it; the tutorial
prose lives in [docs/quickstart.md](docs/quickstart.md) and
[docs/how-to.md](docs/how-to.md).

## The boundary

1. **The manifest is the only policy surface.** Paths, rewrites,
   strips, allowlists, guard rows, and the banned-word lists live in
   `doc-policy.toml`. NEVER hardcode a path or a pattern in the engine
   to fix a finding; declare it in the manifest. The engine's defaults
   (the denied internal classes and the secret classes in
   `docpol/config.py`) extend only through a reviewed code change.
2. **Findings are evidence, not noise.** A drift finding means the copy
   or the source is wrong; fix the text or rerun `docpol sync`. NEVER
   weaken a gate (dropping a denied class, emptying a deny list,
   widening `prose.skip_patterns`) to turn a report green.
3. **The publication gates run BEFORE any copy.** An allowlist entry
   that fails the class check or the secret scan aborts the whole run
   and copies nothing. NEVER split a refused run into "copy the good
   ones anyway": a half-synced public surface with no signal is the
   exact failure the gate exists to prevent.
4. **The secret scan is deliberately conservative.** A false positive
   costs one blocked doc; a false negative costs a leaked key. NEVER
   trim a secret class to unblock a file; reclassifying the file (it
   does not belong in the allowlist) is the fix.
5. **The source tree is the truth for mode 1.** A sync overwrites the
   derived copy FROM the source; it never merges and never edits the
   source. Hand-editing a derived copy is drift and the gate reports
   it.
6. **The published tree is GENERATED.** `docpol publish` copies from
   the allowlist and rewrites the root README. NEVER treat it as a
   source of truth and NEVER hand-edit it; fix the allowlist and
   re-publish.
7. **Names may be written; values may not.** A doc in this family may
   name a config key, a banned-word key, or a secret-class NAME; it
   must never spell out a live-looking credential or an actual banned
   term where a citation works. See the README's rule-citation note.
8. **Exit 1 means do not publish.** Any lane that copies or publishes
   must either finish after a green run or hand back explicitly as
   refused; a red run hands back nothing.
9. **The audit is read-only.** `docpol audit` inventories and reports;
   it does not fix. Fix the files it names.

## What this kit is NOT

- NOT a formatter or a linter for code. Its prose gate reads only
  tracked (or declared) markdown.
- NOT a secret scanner for a whole repo. The scan covers allowlisted
  files at publish time; repo-wide scanning is a guards row.
- NOT a site generator. It copies files; it does not render them.
- NOT a replacement for the repo's own CI. Its gates run beside CI.

## When an agent is asked to wire a repo's doc policy

Use this repo's skill
([skills/docs-policy-kit/SKILL.md](skills/docs-policy-kit/SKILL.md)):
manifest authoring, the gate inventory, and the failure modes, with the
consolidation traps inline.