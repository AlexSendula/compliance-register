"""wetten.overheid.nl / BWB api tier. The per-act manifest.xml carries a
hashcode per published state (toestand); that hash is the change signal.
Element names below were read from a live manifest on the implementation
date — see tests/fixtures/bwb-manifest.xml."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from ...sources import Source
from .. import http as _http, store
from . import CheckResult, FetchResult

REPO = "https://repository.officiele-overheidspublicaties.nl/bwb"


def _local(tag: str) -> str:
    return tag.split("}", 1)[-1]


def latest_item(manifest_xml: bytes) -> dict:
    """{'hashcode', 'url', 'date'} of the newest published state.

    Real manifest shape (read 2026-09-20 from BWBR0009950/manifest.xml):
      <work label="BWBR0009950" _latestItem="2026-08-15_0/xml/BWBR0009950_2026-08-15_0.xml">
        <expression label="2026-08-15_0">
          <metadata><datum_inwerkingtreding>2026-08-15</datum_inwerkingtreding>…</metadata>
          <manifestation label="xml">
            <metadata><hashcode>…</hashcode><size>…</size></metadata>
            <item label="BWBR0009950_2026-08-15_0.xml" _deleted="false"/>
          </manifestation>
        </expression>
      </work>
    There is no URL element: the toestand URL is REPO/<work label>/<work _latestItem>,
    and _latestItem's first segment names the expression whose hashcode is the version."""
    root = ET.fromstring(manifest_xml)
    work_id, latest = root.get("label"), root.get("_latestItem")
    if not (work_id and latest):
        raise ValueError("manifest has no work label / _latestItem")
    expr_label = latest.split("/", 1)[0]
    for expr in root.iter("expression"):
        if expr.get("label") != expr_label:
            continue
        hashcode = expr.findtext("manifestation[@label='xml']/metadata/hashcode")
        date = expr.findtext("metadata/datum_inwerkingtreding")
        if hashcode:
            return {"hashcode": hashcode.strip(), "url": f"{REPO}/{work_id}/{latest}", "date": (date or "").strip()[:10] or None}
    raise ValueError(f"no expression {expr_label!r} with an xml hashcode in manifest")


def _manifest(source: Source, client: _http.Http) -> dict:
    url = f"{REPO}/{source.config['bwb_id']}/manifest.xml"
    resp = client.get(url, allowed_hosts=source.allowed_hosts)
    if resp.status != 200:
        raise _http.HttpUnreachable(f"{url}: HTTP {resp.status}")
    return latest_item(resp.body)


def check(source: Source, client: _http.Http, *, today: str, cdir) -> CheckResult:
    try:
        latest = _manifest(source, client)
    except (_http.HttpUnreachable, _http.HttpRefused, ET.ParseError, ValueError) as exc:
        return CheckResult("unreachable", None, str(exc))
    if latest["hashcode"] != source.last_version:
        return CheckResult("moved", latest["hashcode"], f"manifest hash {source.last_version} → {latest['hashcode']}", [latest["url"]])
    return CheckResult("fresh", latest["hashcode"], "manifest hash unchanged")


def _articles(xml: bytes) -> list[tuple[str, str]]:
    root = ET.fromstring(xml)
    out = []
    for art in root.iter():
        if _local(art.tag) != "artikel":
            continue
        nr = None
        for el in art.iter():
            if _local(el.tag) == "nr" and (el.text or "").strip():
                nr = el.text.strip(); break
        if not nr:
            continue
        paras = []
        for el in art.iter():
            if _local(el.tag) in ("al", "lid", "li") and el is not art:
                t = " ".join("".join(el.itertext()).split())
                if t:
                    paras.append(t)
        out.append((nr, f"## Artikel {nr}\n\n" + "\n\n".join(paras) + "\n"))
    return out


def fetch(source: Source, client: _http.Http, cdir, *, today: str, force: bool = False) -> FetchResult:
    result = FetchResult()
    try:
        latest = _manifest(source, client)
    except (_http.HttpUnreachable, _http.HttpRefused, ET.ParseError, ValueError) as exc:
        result.refused.append(f"manifest: {exc}"); return result
    if not force and latest["hashcode"] == source.last_version:
        result.skipped += 1; return result
    try:
        resp = client.get(latest["url"], allowed_hosts=source.allowed_hosts)
    except (_http.HttpUnreachable, _http.HttpRefused) as exc:
        result.refused.append(f"toestand: {exc}"); return result
    if resp.status != 200:
        result.refused.append(f"toestand: HTTP {resp.status}"); return result
    try:
        articles = _articles(resp.body)
    except ET.ParseError as exc:
        result.refused.append(f"toestand: not XML ({exc})"); return result
    manifest = store.load_manifest(cdir, source)
    version = latest["hashcode"][:16]
    try:
        for nr, md in articles:
            safe = re.sub(r"[^A-Za-z0-9.]+", "_", nr)
            rel = f"{version}/artikel_{safe}.md"
            meta = {"bwb_id": source.config["bwb_id"], "toestand": latest["url"], "valid_from": latest["date"], "article": nr, "source_url": f"{source.url}#Artikel{nr}"}
            path = store.write_page(cdir, source, rel, meta, md, retrieved_at=today)
            manifest[f"{latest['url']}#{nr}"] = {"fetched": today, "lastmod": latest["date"], "hash": store.content_hash(md), "path": rel, "version": latest["hashcode"]}
            result.written.append(str(path))
    finally:
        store.save_manifest(cdir, source, manifest)
    result.version = latest["hashcode"]
    return result
