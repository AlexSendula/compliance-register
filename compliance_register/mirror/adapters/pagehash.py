"""Page-hash tier: for sources with no version id, sitemap or feed. check()
has to fetch to know — it says so."""
from __future__ import annotations

import hashlib

from ...sources import Source
from .. import htmlmd, http as _http, store
from . import CheckResult, FetchResult


def _relpath(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()[:16] + ".md"


def _get_markdown(source: Source, client: _http.Http, url: str) -> str | None:
    resp = client.get(url, allowed_hosts=source.allowed_hosts)
    text = resp.body.decode("utf-8", "replace")
    if resp.status != 200 or not htmlmd.looks_like_html(text):
        return None
    return htmlmd.html_to_markdown(text, url)


def check(source: Source, client: _http.Http, *, today: str, cdir) -> CheckResult:
    urls = source.config.get("urls") or [source.url]
    manifest = store.load_manifest(cdir, source)
    changed, unreachable = [], []
    for url in urls:
        try:
            md = _get_markdown(source, client, url)
        except (_http.HttpUnreachable, _http.HttpRefused) as exc:
            unreachable.append(f"{url}: {exc}"); continue
        if md is None:
            unreachable.append(f"{url}: not html"); continue
        if store.needs_refresh(manifest.get(url), None, store.content_hash(md)):
            changed.append(url)
    if unreachable and not changed:
        return CheckResult("unreachable", None, "; ".join(unreachable))
    if changed:
        return CheckResult("moved", None, f"page-hash tier fetches to compare: {len(changed)} of {len(urls)} changed", changed)
    return CheckResult("fresh", None, f"page-hash tier fetches to compare: {len(urls)} unchanged")


def fetch(source: Source, client: _http.Http, cdir, *, today: str, force: bool = False) -> FetchResult:
    result = FetchResult()
    urls = source.config.get("urls") or [source.url]
    manifest = store.load_manifest(cdir, source)
    try:
        for url in urls:
            try:
                md = _get_markdown(source, client, url)
            except (_http.HttpUnreachable, _http.HttpRefused):
                result.refused.append(url); continue
            if md is None:
                result.refused.append(url); continue
            h = store.content_hash(md)
            if not force and not store.needs_refresh(manifest.get(url), None, h):
                result.skipped += 1; continue
            rel = _relpath(url)
            path = store.write_page(cdir, source, rel, {"source_url": url}, md, retrieved_at=today)
            manifest[url] = {"fetched": today, "lastmod": None, "hash": h, "path": rel, "version": None}
            result.written.append(str(path))
    finally:
        store.save_manifest(cdir, source, manifest)
    return result
