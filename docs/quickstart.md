# Quickstart: from nothing to gated docs

Checked against `docpol` 0.1.0 on 2026-10-22. Every command is real;
every output shown is real output from the commands above it.

You need: Python 3.11 or newer, and `uv`. No network needed.

## 1. Get the kit

The kit is not published to a package registry yet. From a checkout or
a vendored copy:

```bash
uv tool install --from /path/to/docs-policy-kit docs-policy-kit
```

Or run it straight from a checkout without installing:

```bash
uv run --project /path/to/docs-policy-kit docpol --help
```

Expected output (the same for both forms):

```
usage: docpol [-h] {check,sync,publish,audit} ...

the docs-policy-kit engine

positional arguments:
  {check,sync,publish,audit}
    check               every gate, read-only
    sync                mode 1: rewrite drifted derived copies
    publish             mode 2: the gated allowlist copy
    audit               the docs inventory (read-only)

options:
  -h, --help            show this help message and exit
```

## 2. Write the manifest in YOUR repo

Create `doc-policy.toml` at the repo root. A minimal one that runs both
modes against the layout `private/` (source) and `public/` (derived):

```toml
version = "0.1.0"

[derived]
mode = "derived-copy"

[[derived.pairs]]
name = "my-pair"
source_dir = "private"
target_dir = "public"
guides = ["quickstart.md"]

[publish]
allowlist = "doc-allowlist.json"
source_dir = "private"
published_dir = "site-docs"

[audit]
source_dir = "docs"
extensions = [".md"]
lane_key = "docs"
```

Every policy decision is a manifest key. The engine refuses to run
without one:

```
docpol: manifest not found: /path/to/your-repo/doc-policy.toml
```

And a manifest missing a required key fails named:

```
docpol: publish: missing required key 'allowlist'
```

## 3. Wire mode 1 (derived-copy sync)

A pair copies one private source tree into one public target tree. The
rewrites are literal text replacements applied in order; the strips are
text removed from the public copy entirely:

```toml
[[derived.pairs]]
name = "guides"
source_dir = "docs/release/packages/my-kit"
target_dir = "public-docs"
guides = ["quickstart.md", "RUNBOOK.md"]
base_url = "https://github.com/you/my-kit/tree/main/docs"
rewrites = [
    { from = "(../shared/links.md)", to = "(https://you.example/links.md)" },
]
strips = [
    "Design notes: `docs/release/DESIGN.md` in\nthe system repo.\n",
]
```

Write the source, then sync (which writes the derived copies):

```bash
docpol sync /path/to/your-repo
```

Expected output:

```
sync: wrote: public-docs/quickstart.md from docs/release/packages/my-kit/quickstart.md
sync: wrote: public-docs/RUNBOOK.md from docs/release/packages/my-kit/RUNBOOK.md
sync: every derived copy now matches its source
```

Edit the DERIVED copy by hand and the gate catches it:

```
derive: FAIL (drift: 1)
  - guides/quickstart.md: derived text drifts from the source (expected 812 chars, got 823) (fix: re-copy from docs/release/packages/my-kit via `docpol sync --manifest <manifest>`)
```

Rerun `docpol sync` to clear it; the fix is always the sync, never a
hand edit.

## 4. Wire mode 2 (allowlisted publication)

Declare the allowlist file and the two trees:

```toml
[publish]
allowlist = "doc-allowlist.json"
source_dir = "docs"
published_dir = "site-docs"
```

Create the allowlist (relative paths under `source_dir`):

```json
{ "files": ["guide.md"] }
```

Then publish:

```bash
docpol publish /path/to/your-repo
```

Expected output:

```
publish: wrote guide.md
publish: copied 1 file(s) into site-docs
```

An entry that is internal-by-construction is refused BY NAME before any
copy. Allowlist `scratchpad/guide.md` and the run refuses:

```
publish: REFUSED scratchpad/guide.md: internal path segment "scratchpad" is never publishable
publish: 1 allowlist entries refused; nothing was copied
```

An entry whose content carries a credential-shaped string is refused the
same way, and nothing is copied:

```
publish: REFUSED leaky.md: content matches the secret class '\bsk-[A-Za-z0-9-]{16,}'
publish: 1 allowlist entries refused; nothing was copied
```

The refusal pattern is printed AS A CLASS (the regex source), which is
safe to show; the refused FILE is not published anywhere. The rule for
this kit's own docs: cite the class name or the config key, never a
live-looking value.

## 5. Run every gate

```bash
docpol check /path/to/your-repo
```

A green configured repo looks like:

```
derive: ok (drift: 0)
publish policy: ok (refusals: 0)
guards: ok
prose: ok (0 findings)
```

Exit code 0. Exit code 1 is "do not publish". Exit code 2 is a manifest
problem (not found, does not parse, a missing key), always named:

```
docpol: doc-policy.toml: does not parse: Expected '=' after a key ...
```

## 6. Where to go next

Day-to-day operation (the tasks you repeat):
[docs/how-to.md](how-to.md). The full command surface, every error
string, and the recovery procedures: [docs/RUNBOOK.md](RUNBOOK.md).