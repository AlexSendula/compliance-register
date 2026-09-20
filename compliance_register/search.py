"""Ranked keyword search over the project's compliance markdown.

BM25 over whole files. The table at .search-index.json is derived from the
markdown and keyed on (relpath, size, mtime_ns) of every .md — if that
signature differs from the one stored, the table is rebuilt before answering.
Search ranks; it does not understand (docs-mirror, ADR-012)."""
from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

TABLE_VERSION = 1
INDEX_FILE = ".search-index.json"
K1 = 1.5
B = 0.75
MIN_TERM = 2

# --- copied verbatim from docs-mirror/docs_mirror/index.py (_STOP, _WORD, tokenize) ---
_STOP = frozenset(
    "a an the of to in for on and or is are be was were it its this that with"
    " as at by from how do i my we our you your can could what when where"
    " which not no if then than there here about into over under".split()
)

_WORD = re.compile(r"\w+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    """Query and document go through the SAME function, always.

    Two tokenizers that disagree by one rule -- a stop word, a minimum length,
    whether digits count -- produce an index that cannot match its own queries,
    and the failure is silent: results simply get worse. There is one function
    so there is one rule.
    """
    return [w for w in _WORD.findall(text.casefold())
            if len(w) >= MIN_TERM and w not in _STOP]
# --- end copy ---


@dataclass
class Hit:
    path: str
    score: float
    kind: str
    snippet: str


def _kind(rel: str) -> str:
    if rel == "profile.md":
        return "profile"
    top = rel.split("/", 1)[0]
    return {"regimes": "regime", "mirror": "mirror"}.get(top, "other")


def _docs(cdir: Path) -> list[tuple[str, Path]]:
    out = []
    for p in sorted(cdir.rglob("*.md")):
        # mirror/.private/ is gitignored for committing, not hidden from search;
        # skip only dot-files (the index itself included)
        if p.name.startswith("."):
            continue
        out.append((p.relative_to(cdir).as_posix(), p))
    return out


def signature(cdir: Path) -> str:
    h = hashlib.sha256()
    for rel, p in _docs(cdir):
        st = p.stat()
        h.update(f"{rel}|{st.st_size}|{st.st_mtime_ns}\n".encode())
    return h.hexdigest()


def build_table(cdir: Path) -> dict:
    docs = []
    df: dict[str, int] = {}
    for rel, p in _docs(cdir):
        toks = tokenize(p.read_text(encoding="utf-8", errors="replace"))
        tf: dict[str, int] = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        for t in tf:
            df[t] = df.get(t, 0) + 1
        docs.append({"path": rel, "kind": _kind(rel), "len": len(toks), "tf": tf})
    avg = (sum(d["len"] for d in docs) / len(docs)) if docs else 0.0
    return {"version": TABLE_VERSION, "signature": signature(cdir), "avgdl": avg, "df": df, "docs": docs}


def load_table(cdir: Path) -> dict:
    path = cdir / INDEX_FILE
    if path.is_file():
        try:
            table = json.loads(path.read_text(encoding="utf-8"))
            if table.get("version") == TABLE_VERSION and table.get("signature") == signature(cdir):
                return table
        except (ValueError, OSError):
            pass
    table = build_table(cdir)
    path.write_text(json.dumps(table), encoding="utf-8")
    return table


def _snippet(cdir: Path, rel: str, terms: list[str]) -> str:
    text = (cdir / rel).read_text(encoding="utf-8", errors="replace")
    low = text.lower()
    pos = min((low.find(t) for t in terms if low.find(t) >= 0), default=0)
    start = max(0, pos - 60)
    return " ".join(text[start : start + 160].split())


def search(cdir: Path, query: str, k: int = 5, kind: str | None = None) -> list[Hit]:
    table = load_table(cdir)
    terms = tokenize(query)
    if not terms:
        return []
    n = len(table["docs"])
    hits: list[Hit] = []
    for d in table["docs"]:
        if kind and d["kind"] != kind:
            continue
        score = 0.0
        for t in terms:
            f = d["tf"].get(t, 0)
            if not f:
                continue
            idf = math.log(1 + (n - table["df"].get(t, 0) + 0.5) / (table["df"].get(t, 0) + 0.5))
            denom = f + K1 * (1 - B + B * d["len"] / (table["avgdl"] or 1))
            score += idf * f * (K1 + 1) / denom
        if score > 0:
            hits.append(Hit(path=d["path"], score=score, kind=d["kind"], snippet=""))
    hits.sort(key=lambda h: (-h.score, h.path))
    hits = hits[:k]
    for h in hits:
        h.snippet = _snippet(cdir, h.path, terms)
        h.path = (cdir / h.path).as_posix()
    return hits
