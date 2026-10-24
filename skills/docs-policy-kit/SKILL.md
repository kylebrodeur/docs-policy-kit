---
name: docs-policy-kit
description: Use when operating, reading, or fixing the docpol docs-policy engine (derived-copy drift gates, allowlisted publication, ruling guards, prose gate), when a publication or drift finding needs its exact fix, or when wiring a repo's doc policy through a doc-policy.toml manifest.
---

# Operating docpol (the docs-policy-kit engine)

The kit: one config file per repo (`doc-policy.toml`), one CLI
(`docpol`), four gates. Docs-publication claims become exit codes.

## The gates and what each refuses

| Gate | Refuses when | First fix |
|---|---|---|
| `derive` | a derived copy drifts from its source, or the source is missing | `docpol sync` (or restore the source); never hand-edit the copy |
| `publish policy` | an allowlist entry is an internal class, escapes the root, is missing, or carries a credential-shaped string | fix the allowlist or the content; never the pattern |
| `guards` | a ruling's path shape exists (or is missing), or forbidden text appears | fix the tree the finding names |
| `prose` | banned characters or banned words in tracked markdown | fix the prose at `file:line` |

## The commands

```bash
docpol check .              # every gate, read-only; red = do not publish
docpol sync .               # mode 1: rewrite drifted derived copies
docpol publish .            # mode 2: the gated allowlist copy
docpol audit .              # the docs inventory (read-only)
docpol check . --manifest ./other/doc-policy.toml
```

## The rules an agent obeys

1. **The manifest is the only policy surface.** Declare a path, a
   rewrite, or a pattern in `doc-policy.toml`; never hardcode one in
   the engine to fix a finding.
2. **Findings are evidence.** Fix the tree or the allowlist. Never
   weaken a gate: no dropped denied class, no emptied deny list, no
   widened skip patterns.
3. **Publish gates run before ANY copy.** One refusal aborts the run
   and copies nothing; never "copy the good ones anyway".
4. **The secret scan is deliberately conservative.** A false positive
   is one blocked doc; a false negative is a leaked key. Reclassify
   the file; never trim a secret class.
5. **The source is the truth; sync overwrites from it.** A hand edit
   of a derived copy is drift, and the sync erases it.
6. **The published tree is GENERATED.** Fix the allowlist and
   re-publish; do not edit the tree.
7. **Name a class, never a value.** Citing `prose.banned_words` or a
   secret class by NAME is right; spelling out a live-looking
   credential (or an actual banned filler word where a citation works)
   is the thing this kit exists to refuse.
8. **Exit 1 means do not publish.** Hand back explicitly; a red run
   hands back nothing.

## Reading a finding

Every finding names its file (or allowlist entry) and the rule that
fired, with the fix inline. The refusal reason prints a pattern
CLASS (the regex source), which is always safe; the refused file is
never copied anywhere. Apply the named fix; do not improvise a nearby
one.

## The two modes

- **Mode 1 (derived copy):** a private source tree is copied to a
  derived public location through declared rewrites and strips. The
  engine recomputes the expected public text; any difference is drift.
- **Mode 2 (allowlisted publication):** only allowlisted paths are
  copied, each checked for content class AND secret patterns before
  anything is copied.

## Not this kit's job

- NOT a repo-wide secret scanner: the scan covers allowlisted files at
  publish time (and any `forbid` guards row declares its own scope).
- NOT a site generator: it copies files; it does not render them.
- NOT a replacement for the repo's CI: its gates run beside CI.

## Verifying a state claim

"Published" means: the publish gates refused nothing, the published
tree contains exactly the allowlisted files plus the generated README,
and `docpol check` is green. Anything less is "not published",
whatever the chat says.