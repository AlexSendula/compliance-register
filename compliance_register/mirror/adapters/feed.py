"""Feed tier: RSS 2.0 or Atom. A new entry id is the change signal."""
from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET

from ...sources import Source
from .. import htmlmd, http as _http, store
from . import LISTING_MAX_BYTES, CheckResult, FetchResult, parse_xml

_ATOM = "{http://www.w3.org/2005/Atom}"


def _entries(source: Source, client: _http.Http) -> list[dict]:
    resp = client.get(source.url, allowed_hosts=source.allowed_hosts, max_bytes=LISTING_MAX_BYTES)
    if resp.status != 200:
        raise _http.HttpUnreachable(f"{source.url}: HTTP {resp.status}")
    root = parse_xml(resp.body)
    out = []
    if root.tag == _ATOM + "feed":
        for e in root.findall(_ATOM + "entry"):
            link = next((l.get("href") for l in e.findall(_ATOM + "link") if l.get("rel") in (None, "alternate")), None)
            out.append({"id": e.findtext(_ATOM + "id") or link, "title": e.findtext(_ATOM + "title") or "", "published": e.findtext(_ATOM + "published") or e.findtext(_ATOM + "updated"), "link": link})
    else:
        for it in root.iter("item"):
            link = (it.findtext("link") or "").strip()
            out.append({"id": (it.findtext("guid") or link).strip(), "title": (it.findtext("title") or "").strip(), "published": (it.findtext("pubDate") or "").strip() or None, "link": link})
    return [e for e in out if e["id"] and e["link"]]


def check(source: Source, client: _http.Http, *, today: str, cdir) -> CheckResult:
    try:
        entries = _entries(source, client)
    except (_http.HttpUnreachable, _http.HttpRefused, ET.ParseError) as exc:
        return CheckResult("unreachable", None, str(exc))
    manifest = store.load_manifest(cdir, source)
    if not entries:  # a listing that yields nothing is "cannot tell", never "no change"
        return CheckResult("unreachable", None, "feed has no entries with an id and a link")
    new = [e["id"] for e in entries if e["id"] not in manifest]
    if new:
        return CheckResult("moved", None, f"{len(new)} new feed entries", new)
    return CheckResult("fresh", None, f"{len(entries)} entries, none new")


def fetch(source: Source, client: _http.Http, cdir, *, today: str, force: bool = False) -> FetchResult:
    result = FetchResult()
    manifest = store.load_manifest(cdir, source)
    try:
        for e in _entries(source, client):
            if not force and e["id"] in manifest:
                result.skipped += 1; continue
            try:
                resp = client.get(e["link"], allowed_hosts=source.allowed_hosts)
            except (_http.HttpUnreachable, _http.HttpRefused):
                result.refused.append(e["link"]); continue
            text = resp.body.decode("utf-8", "replace")
            md = htmlmd.html_to_markdown(text, e["link"]) if resp.status == 200 and htmlmd.looks_like_html(text) else None
            if md is None:
                result.refused.append(e["link"]); continue
            rel = hashlib.sha1(e["id"].encode()).hexdigest()[:16] + ".md"
            path = store.write_page(cdir, source, rel, {"source_url": e["link"], "title": e["title"], "published": e["published"]}, md, retrieved_at=today)
            manifest[e["id"]] = {"fetched": today, "lastmod": e["published"], "hash": store.content_hash(md), "path": rel, "version": None}
            result.written.append(str(path))
    except (_http.HttpUnreachable, _http.HttpRefused, ET.ParseError) as exc:
        result.refused.append(f"listing: {exc}")
    finally:
        store.save_manifest(cdir, source, manifest)
    return result
