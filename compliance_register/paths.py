"""Where things live. The only module allowed to decide a path.

A project is any directory that contains `knowledge-base/`. The skill writes
only under `<root>/knowledge-base/compliance/` and checks every write against
that base — a file name coming from a source, a regime id or a command-line
argument must never be able to escape it."""
from __future__ import annotations

import re
from pathlib import Path

KB = "knowledge-base"
SUB = "compliance"

_SAFE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class NotAProject(Exception):
    """No knowledge-base/ found from the start directory upward."""


class UnsafePath(Exception):
    """A path or name that could write outside the compliance directory."""


def find_root(start: Path | None = None) -> Path:
    p = (start or Path.cwd()).resolve()
    for candidate in (p, *p.parents):
        if (candidate / KB).is_dir():
            return candidate
    raise NotAProject(f"no {KB}/ directory found from {p} upward")


def compliance_dir(root: Path) -> Path:
    return root / KB / SUB


def contained(base: Path, target: Path) -> Path:
    """Resolve `target` (relative to `base` unless absolute) and refuse it if it
    lands outside `base`."""
    b = base.resolve()
    t = (target if target.is_absolute() else b / target).resolve()
    if t != b and b not in t.parents:
        raise UnsafePath(f"{target} resolves outside {base}")
    return t


def safe_component(name: str) -> str:
    """One path segment: ASCII letters, digits, dot, dash, underscore; no
    leading dot; no separators; no whitespace."""
    if not _SAFE.match(name) or name in {".", ".."}:
        raise UnsafePath(f"unsafe name: {name!r}")
    return name
