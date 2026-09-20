"""One module per tier. Each exposes check() and fetch() with the same shape;
the registry maps a source's adapter name to the module."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

from ..http import HttpRefused

LISTING_MAX_BYTES = 5_000_000  # a sitemap or feed larger than this is not a listing we want


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
    from . import eurlex, feed, pagehash, sitemap  # noqa: F401
    registry = {"eurlex": eurlex, "sitemap": sitemap, "feed": feed, "pagehash": pagehash}
    return registry[name]


def prefetch(chosen, client_factory, *, today: str) -> dict:
    """{adapter name: extra kwargs for its check()/fetch()} — the eurlex basket
    is resolved once per run with one client, so N sources cost one SPARQL
    request. Never raises: a failed resolve surfaces per source."""
    from . import eurlex
    basket = [s for s in chosen if s.adapter == "eurlex" and s.tier != "refuse"]
    if not basket:
        return {}
    return {"eurlex": {"resolved": eurlex.prefetch(basket, client_factory(basket[0]), today=today)}}


def parse_xml(body: bytes) -> ET.Element:
    """ET.fromstring behind one guard: a listing carrying a DTD is refused
    before expat sees it (entity expansion is the only XML risk left on a
    modern expat, and a listing never legitimately needs one)."""
    if b"<!DOCTYPE" in body[:4096] or b"<!ENTITY" in body:
        raise HttpRefused("DTD in XML listing")
    return ET.fromstring(body)
