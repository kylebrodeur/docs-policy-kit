# How-to: the tasks you repeat

Checked against `docpol` 0.1.0 on 2026-10-22. One question per section.
The one-time setup lives in [quickstart.md](quickstart.md); every
frequent task lives here. The full command surface and recovery
procedures live in [RUNBOOK.md](RUNBOOK.md).

## How do I check the docs gates right now?

```bash
docpol check .
```

Read each line; every gate prints `ok`, `FAIL` with findings, or a
count. Exit 0 means "publication-safe", exit 1 means "do not publish",
exit 2 means the manifest itself is broken.

## How do I update a private guide and ship the new copy?

Edit the SOURCE doc (the `source_dir` side of the pair), then:

```bash
docpol sync .
docpol check .
```

The sync rewrites every drifted derived copy from its source and
reports each file it touched:

```
sync: wrote: public/quickstart.md from private/quickstart.md
sync: every derived copy now matches its source
```

Never edit the derived copy; the gate treats that as drift.

## How do I add a file to the public docs surface?

Edit the allowlist file (the `publish.allowlist` key), then:

```bash
docpol publish .
```

An entry that fails the class check or the secret scan refuses BY NAME
and nothing is copied. Fix the entry (it does not belong in the
allowlist) or the content, then rerun.

## How do I add a ruling as a guard?

One ruling is one `[[guard]]` row in the manifest:

```toml
[[guard]]
name = "no retired route in the docs"
source = "decisions.md (the ruling this enforces)"
why = "A retired route reappearing in a guide walks an agent back into a closed decision."
kind = "forbid"
targets = ["docs"]
pattern = "(?i)\\bretired-route\\b"
```

Kinds: `absent` (the paths must not exist), `require` (the paths must
exist), `forbid` (the regex must not appear in matching files). The
`why` is printed with every hit; write it for the agent that meets the
finding six months from now.

## How do I fix a prose finding?

```
prose: FAIL (1 findings)
  - quickstart.md:12: <banned filler word (see prose.banned_words)>
```

Fix the prose at `file:line`. The banned defaults are the two dash
characters and the four filler words; the exact lists live in the
manifest's `prose.banned_words` and `prose.banned_chars` keys, not in
this sentence, and the engine defaults live in `docpol/config.py`
(`PROSE_WORD_BANNED`, `PROSE_CHARS_BANNED`).

A line that must NAME a banned term (a doc that defines the rule) is a
citations, not an instance: add a `prose.skip_patterns` entry matching
that line, scoped as narrowly as the definition needs. NEVER widen the
skip list to cover ordinary prose.

## How do I run the audit?

```bash
docpol audit .
```

Expected output (this kit's own tree):

```
markdown files:        N
with a status line:    N
with dead references:  N
```

The audit reports; it never writes. A dead reference names the path
that no longer resolves; fix the doc that cites it.

## How do I keep the kit's own docs out of the gates' hair?

You do not: the kit gates ITSELF with its own manifest (the
`require` guard row for `doc-policy.toml` is the demo). `docpol check`
at this repo's root runs every gate, including the prose gate over the
kit's own markdown. A doc that must show a secret-shaped example uses a
synthetic, self-labeled value (see
[examples/private-source/demo-secret-file.md](../examples/private-source/demo-secret-file.md)),
and the pattern it trips is tested against, never shipped live.

## How do the gates run in CI?

The workflow in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)
installs the kit with `uv` and runs, in order: `ruff check`, the test
suite, and `docpol check .` (the kit gates itself). Copy the same three
steps to gate a repo that vendors the kit.