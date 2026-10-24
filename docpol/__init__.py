"""docpol: the docs-policy-kit engine.

One config file, one CLI, and three verbs (check, sync, publish). The
kit consolidates two docs-publication modes behind one manifest:

- mode 1, derived-copy sync: a private source doc is copied to a
  derived public location; drift is detected and rewritten.
- mode 2, allowlisted publication: only allowlisted paths are copied,
  and each is checked for content class AND secret patterns before
  anything is copied.

Public surface: `Config`, `derive`, `prose`, `guards`, `audit`, and
`publish.validate` / `publish.publish`. The CLI lives in `docpol.cli`.
"""

from .config import (
    DENIED_DIR_SEGMENTS,
    DENIED_FILENAME_PATTERNS,
    SECRET_PATTERNS,
    Config,
    ConfigError,
)
from .derive import Finding, check, expected_text, sync
from .guards import GuardFinding, run_all, run_guard
from .prose import ProseFinding, tracked_files
from .prose import check as check_prose
from .publish import (
    PathEscape,
    Refusal,
)
from .publish import (
    publish as publish_allowlist,
)
from .publish import (
    validate as validate_allowlist,
)

__all__ = [
    "Config",
    "ConfigError",
    "DENIED_DIR_SEGMENTS",
    "DENIED_FILENAME_PATTERNS",
    "SECRET_PATTERNS",
    "Finding",
    "check",
    "expected_text",
    "sync",
    "GuardFinding",
    "run_all",
    "run_guard",
    "ProseFinding",
    "check_prose",
    "tracked_files",
    "PathEscape",
    "publish_allowlist",
    "Refusal",
    "validate_allowlist",
]
