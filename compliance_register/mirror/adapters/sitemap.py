"""Sitemap tier: <lastmod> per page is the change signal."""
from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET

from ...sources import Source
from .. import htmlmd, http as _http, store
from . import LISTING_MAX_BYTES, CheckResult, FetchResult, parse_xml

_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def _entries(source: Source, client: _http.Http) -> list[tuple[str, str | None]]:
    """[(url, lastmod)] from the sitemap, recursing one level into an index."""
    out: list[tuple[str, str | None]] = []
    include = source.config.get("include") or []

    def parse(url: str, depth: int) -> None:
        resp = client.get(url, allowed_hosts=source.allowed_hosts, max_bytes=LISTING_MAX_BYTES)
        if resp.status != 200:
            raise _http.HttpUnreachable(f"{url}: HTTP {resp.status}")
        root = parse_xml(resp.body)
        if root.tag == _NS + "sitemapindex" and depth == 0:
            for sm in root.findall(_NS + "sitemap"):
                loc = sm.findtext(_NS + "loc")
                if loc:
                    parse(loc.strip(), 1)
            return
        for u in root.findall(_NS + "url"):
            loc = (u.findtext(_NS + "loc") or "").strip()
            lastmod = (u.findtext(_NS + "lastmod") or "").strip() or None
            if loc and (not include or any(loc.startswith(p) for p in include)):
                out.append((loc, lastmod))

    parse(source.url, 0)
    return out


def _relpath(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()[:16] + ".md"


def check(source: Source, client: _http.Http, *, today: str, cdir) -> CheckResult:
    try:
        entries = _entries(source, client)
    except (_http.HttpUnreachable, _http.HttpRefused, ET.ParseError) as exc:
        return CheckResult("unreachable", None, str(exc))
    manifest = store.load_manifest(cdir, source)
    changed = [u for u, lm in entries if store.needs_refresh(manifest.get(u), lm, None)]
    if changed:
        return CheckResult("moved", None, f"{len(changed)} of {len(entries)} pages have a newer lastmod", changed)
    return CheckResult("fresh", None, f"{len(entries)} pages, no lastmod moved")


def fetch(source: Source, client: _http.Http, cdir, *, today: str, force: bool = False) -> FetchResult:
    result = FetchResult()
    entries = _entries(source, client)
    manifest = store.load_manifest(cdir, source)
    try:
        for url, lastmod in entries:
            if not force and not store.needs_refresh(manifest.get(url), lastmod, None):
                result.skipped += 1
                continue
            try:
                resp = client.get(url, allowed_hosts=source.allowed_hosts)
            except (_http.HttpUnreachable, _http.HttpRefused) as exc:
                result.refused.append(url); continue
            text = resp.body.decode("utf-8", "replace")
            md = htmlmd.html_to_markdown(text, url) if resp.status == 200 and htmlmd.looks_like_html(text) else None
            if md is None:
                result.refused.append(url); continue
            rel = _relpath(url)
            path = store.write_page(cdir, source, rel, {"source_url": url, "lastmod": lastmod}, md, retrieved_at=today)
            manifest[url] = {"fetched": today, "lastmod": lastmod, "hash": store.content_hash(md), "path": rel, "version": None}
            result.written.append(str(path))
    finally:
        store.save_manifest(cdir, source, manifest)
    return result
