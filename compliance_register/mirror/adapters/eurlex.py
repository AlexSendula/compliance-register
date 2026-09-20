"""EUR-Lex (CELLAR) api tier. One SPARQL resolve per run for every eurlex
source; the dated consolidated CELEX suffix is the change signal. Fetch
applies five content guards before a byte is written, because EUR-Lex
returns HTTP 200 with site chrome when a language version does not exist."""
from __future__ import annotations

import csv
import io
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode

from ...sources import Source
from .. import http as _http, store
from . import CheckResult, FetchResult

SPARQL = "http://publications.europa.eu/webapi/rdf/sparql"
LANG3 = {"BG": "BUL", "CS": "CES", "DA": "DAN", "DE": "DEU", "EL": "ELL", "EN": "ENG", "ES": "SPA", "ET": "EST", "FI": "FIN", "FR": "FRA", "GA": "GLE", "HR": "HRV", "HU": "HUN", "IT": "ITA", "LT": "LIT", "LV": "LAV", "MT": "MLT", "NL": "NLD", "PL": "POL", "PT": "POR", "RO": "RON", "SK": "SLK", "SL": "SLV", "SV": "SWE"}
MARKER = "This text is meant purely as a documentation tool and has no legal effect"
# the <p class="reference"> line: consolidated CELEX (sector 0) — LANG — DD.MM.YYYY. The <title> repeats it with the base CELEX, so anchor on the leading 0.
_HEADER = re.compile(r"(0\d{4}[A-Z]\d{4}) — ([A-Z]{2}) — (\d{2})\.(\d{2})\.(\d{4})")
_ANCHOR = re.compile(r'id="art_(\d+)"')
_TEMPLATE = Path(__file__).resolve().parents[3] / "references" / "eurlex-resolve.sparql"


def _query(celexes: list[str]) -> str:
    values = " ".join(f'"{c}"^^xsd:string' for c in celexes)
    return _TEMPLATE.read_text(encoding="utf-8").replace("{{VALUES}}", values)


def resolve(client: _http.Http, celexes: list[str], *, today: str) -> dict:
    if not celexes:
        return {}
    url = SPARQL + "?" + urlencode({"query": _query(celexes), "format": "text/csv"})
    resp = client.get(url, allowed_hosts=["publications.europa.eu"])
    if resp.status != 200:
        raise _http.HttpUnreachable(f"SPARQL HTTP {resp.status}")
    rows = list(csv.DictReader(io.StringIO(resp.body.decode("utf-8", "replace"))))
    if not rows:
        raise _http.HttpUnreachable("SPARQL returned no rows for a non-empty basket (typed-literal trap?)")
    out: dict = {}
    for c in celexes:
        mine = sorted((r for r in rows if r.get("baseCelex") == c), key=lambda r: r["consolDate"], reverse=True)
        current = next((r for r in mine if r["consolDate"] <= today), None)
        future = [r for r in mine if r["consolDate"] > today]
        nxt = min(future, key=lambda r: r["consolDate"]) if future else None
        out[c] = {
            "current": current["consolCelex"] if current else None,
            "current_date": current["consolDate"] if current else None,
            "next": nxt["consolCelex"] if nxt else None,
            "next_date": nxt["consolDate"] if nxt else None,
        }
    return out


def check(source: Source, client: _http.Http, *, today: str, cdir) -> CheckResult:
    celex = None
    try:
        celex = source.config["celex"]
        r = resolve(client, [celex], today=today)[celex]
    except KeyError as exc:
        return CheckResult("unreachable", None, f"config key missing: {exc}")
    except (_http.HttpUnreachable, _http.HttpRefused, ValueError) as exc:
        return CheckResult("unreachable", None, str(exc))
    if r["current"] is None and source.last_version:
        return CheckResult("unreachable", None, f"{celex}: known instrument returned no consolidation")
    if r["current"] != source.last_version:
        return CheckResult("moved", r["current"], f"consolidation {source.last_version} → {r['current']}", [r["current"] or ""], r["next"], r["next_date"])
    return CheckResult("fresh", r["current"], "consolidated CELEX unchanged", [], r["next"], r["next_date"])


# --- chunking -------------------------------------------------------------
class _Articles(HTMLParser):
    """Collect per-article markdown from <div class="eli-subdivision" id="art_N">."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.articles: dict[int, list[str]] = {}
        self._current: int | None = None
        self._depth = 0
        self._buf: list[str] = []
        self._pclass = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "div":
            if self._current is None and "eli-subdivision" in (a.get("class") or "") and (a.get("id") or "").startswith("art_"):
                m = re.fullmatch(r"art_(\d+)", a["id"])
                if m:
                    self._current, self._depth, self._buf = int(m.group(1)), 1, []
                    return
            elif self._current is not None:
                self._depth += 1
        if self._current is None:
            return
        if tag == "p":
            self._pclass = a.get("class") or ""
            self._buf.append("\n\n")
            classes = self._pclass.split()
            if "title-article-norm" in classes:
                self._buf.append("## ")
            elif "stitle-article-norm" in classes:
                self._buf.append("### ")

    def handle_endtag(self, tag):
        if self._current is None:
            return
        if tag == "div":
            self._depth -= 1
            if self._depth == 0:
                self.articles[self._current] = self._buf
                self._current = None
        elif tag == "p":
            self._buf.append("\n")

    def handle_data(self, data):
        if self._current is not None:
            self._buf.append(data)


def chunk(html: str) -> dict[int, str]:
    p = _Articles()
    p.feed(html)
    out = {}
    for n, parts in p.articles.items():
        text = "".join(parts)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r" ?\n ?", "\n", text)  # no space-only lines
        text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
        out[n] = text
    return out


def fetch(source: Source, client: _http.Http, cdir, *, today: str, force: bool = False) -> FetchResult:
    result = FetchResult()
    celex = source.config["celex"]
    lang = (source.config.get("language") or "EN").upper()
    try:
        r = resolve(client, [celex], today=today)[celex]
    except (_http.HttpUnreachable, _http.HttpRefused) as exc:
        result.refused.append(f"resolve: {exc}"); return result
    current = r["current"]
    if not current:
        result.refused.append("resolve: no consolidation in force"); return result
    if not force and current == source.last_version:
        result.skipped += 1; return result
    url = f"https://eur-lex.europa.eu/legal-content/{lang}/TXT/HTML/?uri=CELEX:{current}"
    try:
        resp = client.get(url, allowed_hosts=source.allowed_hosts)
    except (_http.HttpUnreachable, _http.HttpRefused) as exc:
        result.refused.append(f"fetch: {exc}"); return result
    body = resp.body.decode("utf-8", "replace")
    # guards
    if resp.status != 200 or not resp.headers.get("Content-Type", "").startswith("text/html"):
        result.refused.append("G1: not an HTML 200"); return result
    if MARKER not in body:
        result.refused.append("G2: documentation-tool marker missing (site chrome?)"); return result
    anchors = [int(x) for x in _ANCHOR.findall(body)]
    if not anchors:
        result.refused.append("G3: no article anchors"); return result
    m = _HEADER.search(body)
    date = current.split("-")[1]
    if not m or m.group(1) != current.split("-")[0] or m.group(2) != lang or (m.group(5) + m.group(4) + m.group(3)) != date:
        result.refused.append("G4: header does not match requested CELEX/language/date"); return result
    if len(set(anchors)) != len(anchors) or anchors != sorted(anchors):
        result.refused.append("G5: article anchors not unique and increasing"); return result
    articles = chunk(body)
    manifest = store.load_manifest(cdir, source)
    banner = f"> {MARKER}. Only the Official Journal is authentic. Source: {url}\n\n"
    iso_date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
    try:
        for n in sorted(articles):
            rel = f"{current}/art_{n}.md"
            meta = {
                "celex": celex, "consolidated_celex": current, "consolidated_date": iso_date,
                "language": lang, "article": n, "anchor": f"art_{n}",
                "source_url": f"{url}#art_{n}", "authentic_url": source.url,
            }
            path = store.write_page(cdir, source, rel, meta, banner + articles[n], retrieved_at=today)
            manifest[f"{url}#art_{n}"] = {"fetched": today, "lastmod": iso_date, "hash": store.content_hash(articles[n]), "path": rel, "version": current}
            result.written.append(str(path))
    finally:
        store.save_manifest(cdir, source, manifest)
    result.version = current
    return result
