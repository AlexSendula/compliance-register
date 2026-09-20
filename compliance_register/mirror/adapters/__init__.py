"""One module per tier. Each exposes check() and fetch() with the same shape;
the registry maps a source's adapter name to the module."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CheckResult:
    status: str                      # fresh | unreachable | moved
    version: str | None
    detail: str
    changed: list[str] = field(default_factory=list)
    next_version: str | None = None
    next_date: str | None = None


@dataclass
class FetchResult:
    written: list[str] = field(default_factory=list)
    skipped: int = 0
    refused: list[str] = field(default_factory=list)
    version: str | None = None


def get(name: str):
    from . import bwb, eurlex, feed, pagehash, sitemap  # noqa: F401
    registry = {"eurlex": eurlex, "bwb": bwb, "sitemap": sitemap, "feed": feed, "pagehash": pagehash}
    return registry[name]
