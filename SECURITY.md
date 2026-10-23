# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| latest tag | yes |
| older tags | best effort (backport security fixes as needed) |

## Reporting a Vulnerability

**Do not open a public issue for a security vulnerability.**

Use GitHub's **Private Vulnerability Reporting** to reach the
maintainer:

1. Go to the **Security** tab in this repository.
2. Click **"Report a vulnerability."**
3. Describe the issue, a reproduction path, and the affected version or
   tag.

You receive an acknowledgment within 72 hours. If you do not hear back,
follow up via the contact info on the maintainer's profile.

## Scope notes for docs-policy-kit

The kit is a local CLI (`docpol`) whose job is refusing to publish
internal material and credential-shaped content. Its trust boundaries,
and the reports that are most welcome:

- **Path resolution:** anything that lets an allowlist entry, a
  manifest path, or a rewrite resolve OUTSIDE its declared root is in
  scope, including symlink traversal and Unicode trickery. The
  guarantee is the one `resolve_under_root` makes; breaking it is a
  vulnerability.
- **Denial-by-pass:** any content-class or secret-pattern bypass that
  ships an internal file or a credential-shaped string. The scan is
  conservative by design; a bypass is a real vulnerability, unlike a
  false positive (which is a support request, not one).
- **Config loading:** the manifest determines what is copied and what
  is refused. A path where an attacker-supplied manifest gets loaded is
  in scope.
- **The overwrite shape:** `publish` clears the published tree before
  copying. Any way the clear step can reach a directory outside the
  declared `published_dir` is in scope.

The prose gate's banned-word list is a style gate, not a security
boundary; reports about it are style feedback, not vulnerabilities.

## Disclosure Process

- Reports are triaged, confirmed, and fixed.
- Coordinated disclosure applies (60 to 120 days typical embargo).
- The reporter is credited in the security advisory and release notes
  unless anonymity is preferred.