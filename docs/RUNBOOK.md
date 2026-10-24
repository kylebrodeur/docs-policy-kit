# RUNBOOK: the operator's reference

Everything in this runbook is verified against `docpol` 0.1.0
(`docpol/`, Python 3.11+, stdlib only) on 2026-10-22. The tutorial path
lives in [quickstart.md](quickstart.md); repeated tasks live in
[how-to.md](how-to.md). This file is the complete surface: every
command, every manifest key, every error string, and the recovery
procedures.

## The full command surface

```
docpol [-h] {check,sync,publish,audit} ...
```

### `docpol check [root] [--manifest MANIFEST]`

Runs every gate against the kit at `root` (default `.`). Prints one
line per gate: `ok` or `FAIL` with findings. Exit 0 when every gate is
green, 1 when any finding exists, 2 for a manifest error.

- `root`: the repo root. The manifest resolves at
  `<root>/doc-policy.toml` unless `--manifest` names another path
  (relative to the current directory, or absolute).
- Gates in output order: `derive` (mode 1 drift), `publish policy`
  (mode 2 allowlist validation), `guards` (the ruling rows),
  `prose` (the writing rules).

### `docpol sync [root] [--manifest MANIFEST]`

Mode 1's writing half: recompute the expected public text for every
pair and write each drifted derived copy. A current copy is named
`current` and left untouched. A missing SOURCE is not written (only
`check` reports it); a sync never creates a copy without a source.

### `docpol publish [root] [--manifest MANIFEST]`

Mode 2: run the allowlist gates, then copy every allowlisted file into
the published tree. The gates run BEFORE any copy; one refusal aborts
the whole run and copies nothing. A successful run first clears the
published tree (so stale files cannot survive), writes the generated
root README, then copies the files.

### `docpol audit [root] [--manifest MANIFEST]`

The read-only docs inventory: per markdown file under
`audit.source_dir`, a STATUS word if one appears in the first 25 lines,
and backticked repo-relative paths that no longer resolve.

## The full manifest surface (`doc-policy.toml`)

| Key | Default | Meaning |
|---|---|---|
| `version` | required | the manifest-shape version |
| `derived.mode` | required, `"derived-copy"` | mode 1's switch |
| `[[derived.pairs]]` | required, at least one | one repo-to-doc mapping |
| `derived.pairs[].source_dir` / `.target_dir` | required | the private tree and the derived tree, relative to the root; both must resolve UNDER the root |
| `derived.pairs[].guides` | required | the files copied between them |
| `derived.pairs[].base_url` | optional | bare `(guide.md)` links in the source become this URL plus the guide name |
| `derived.pairs[].rewrites` | optional | literal `from`/`to` replacements, applied in order |
| `derived.pairs[].strips` | optional | text removed from the public copy entirely (private pointers) |
| `publish.allowlist` | required | the JSON allowlist file, relative to the root |
| `publish.source_dir` / `.published_dir` | required | the copy's two ends |
| `publish.deny_segments` | the engine set (code) | directory segments never publishable |
| `publish.deny_names` | the engine set (code) | basename regexes never publishable |
| `publish.readme_note` | `""` | a line in the generated published README |
| `[[guard]]` | optional, any count | one locked ruling per row |
| `guard[].kind` | required | `absent`, `require`, or `forbid` |
| `guard[].targets` | required | globs (absent/require) or files/dirs (forbid) |
| `guard[].pattern` | needed by `forbid` | the forbidden regex |
| `prose.banned_words` | the engine four (code) | word-boundary matched |
| `prose.banned_chars` | the engine two (code) | substring matched, a character each |
| `prose.skip_patterns` | the engine's citation set (code) | lines matching one are exempt |
| `audit.source_dir` | required | the inventory root |
| `audit.extensions` | `[".md"]` | the files inventoried |
| `audit.lane_key` | required | the path segment after which the lane name is read |

The engine-side default sets live in `docpol/config.py`
(`DENIED_DIR_SEGMENTS`, `DENIED_FILENAME_PATTERNS`,
`SECRET_PATTERNS`, `PROSE_WORD_BANNED`, `PROSE_CHARS_BANNED`). A doc
that must cite them names the KEY, never a literal term; that is
writing rule 7 of the family standard applied to this kit's own subject
matter.

A manifest path that escapes the repo root is refused at load time:

```
docpol: manifest path escapes the repo root: '../outside' under /root
```

## Every error string, with its fix

An agent-facing harness checks these; the table is the exhaustive list
from the source and the live runs above.

| Error string | Emitted by | The fix |
|---|---|---|
| `manifest not found: <path>` (ConfigError) | every command | create `doc-policy.toml` at the root, or pass `--manifest` |
| `<name>: does not parse: <detail>` (ConfigError) | `Config.load` | fix the TOML; the detail names the line |
| `version: must be a non-empty string` | `Config.load` | set `version = "X.Y.Z"` |
| `derived: missing required table` / `mode: must be "derived-copy"` | `Config.load` | add the mode 1 table |
| `pairs: missing required array of tables` / `no rows` | `Config.load` | add at least one `[[derived.pairs]]` |
| `derived.pairs[i]: missing '<key>'` | `Config.load` | add the named key to that pair |
| `publish: missing required key '<key>'` | `Config.load` | add the named key |
| `publish.<key>: must be an array of strings` | `Config.load` | fix the key's type |
| `audit: missing required key '<key>'` | `Config.load` | add the named key |
| `guard[i]: kind 'forbid' needs a 'pattern'` | `Config.load` | add the row's pattern |
| `guard[i].kind: must be one of absent, require, forbid` | `Config.load` | fix the kind |
| `manifest path escapes the repo root: <path>` (ConfigError) | mode 1 resolution | keep `source_dir`/`target_dir` under the root |
| `allowlist file not found: <path>` (ConfigError) | mode 2 | create the allowlist file |
| `allowlist file does not parse: <detail>` (ConfigError) | mode 2 | fix the JSON |
| `allowlist must be an object with a "files" array` (ConfigError) | mode 2 | fix the shape |
| `allowlist entry must be a string: <entry>` (ConfigError) | mode 2 | fix the entry |
| `invalid allowlist entry: not a non-empty string` | mode 2 | remove or fix the entry |
| `allowlist path must be relative: <path>` (PathEscape) | mode 2 | use a root-relative path |
| `allowlist path escapes the source root: <path>` (PathEscape) | mode 2 | use a path that resolves under `publish.source_dir` |
| `internal path segment "<segment>" is never publishable` | publish policy | remove the entry; the segment is internal-by-construction |
| `internal document class (<pattern>) is never publishable` | publish policy | remove the entry; the class of file is internal |
| `allowlisted file missing under the source root` | publish policy | create the file or drop the entry |
| `content matches the secret class <pattern>` | publish policy | remove the entry; reclassify the file, never the pattern |
| `derived copy missing` / `private source missing` | mode 1 | run `docpol sync` (or restore the source) |
| `derived text drifts from the source (expected N chars, got M)` | mode 1 | run `docpol sync`; never hand-edit the copy |
| `audit source_dir does not exist: <dir>` (ConfigError) | audit | fix `audit.source_dir` |
| `<file>: unreadable: <detail>` (ConfigError) | prose | fix the file encoding (UTF 8 required) |

## Recovery procedures

### A publish copied a file it must not have

The gates predate the copy, so this means the gates were bypassed or
the manifest changed mid-run. Restore the published tree:

```bash
git restore <published_dir>   # or delete it and re-publish after fixing
docpol publish .              # only after the allowlist/pattern issue is fixed
docpol check .
```

### A derived copy was hand-edited and the edit is wanted

The edit belongs in the SOURCE. Move the change to the source doc, then
`docpol sync .`; the gate treats any other resolution as drift.

### An allowlisted file trips the secret scan but the string is safe

The scan is conservative BY DESIGN: reclassify the file. If the string
is a synthetic example documented as one
([examples/private-source/demo-secret-file.md](../examples/private-source/demo-secret-file.md)
style), keep it OUT of the allowlist; the gate has no "it is fake"
exception, and adding one would be weakening the gate.

### The manifest's default denied sets are too narrow for a repo

They are CODE (`docpol/config.py`), changed only with review. A
deployment narrows (never widens) them per repo with the
`publish.deny_segments` and `publish.deny_names` keys; widening the
default sets is an upstream change, not a local edit.

### The prose gate flags a line that is itself the rule

A line that names a banned term as its own rule is a definition. Add a
narrow `prose.skip_patterns` entry matching that line shape. The
defaults exempt the two citation forms (`prose_banned`,
`prose_skip_patterns`); a new definition line needs its own entry. A
skip pattern is a scoped carve-out, never a way to hide ordinary prose.

## Library surface (for scripts that need the verdicts)

Every engine surface is importable without the CLI:

```python
from docpol import Config, check_prose, run_all, validate_allowlist
from docpol.derive import check as drift_check, sync as drift_sync
from docpol.publish import publish as gated_publish

config = Config.load(repo / "doc-policy.toml")
findings = drift_check(repo, config)          # ["finding", ...]; [] = clean
refusals = validate_allowlist(repo, config)   # [Refusal, ...]; [] = clean
guard_hits = run_all(repo, config)            # [GuardFinding, ...]
prose_hits = check_prose(repo, config)        # [ProseFinding, ...]
```

## Verification of this repo's own docs

The doc harness (the AI ECP standard) plus this kit's own gates:

```bash
uv run pytest tests -q
uv run ruff check .
uv run pytest tests -q
uv run docpol check .
```

Expected: every `docs-policy-kit:` check PASS, the tests green, and
every gate `ok`.