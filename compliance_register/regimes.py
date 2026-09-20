"""regimes/<id>.md — one file per regime that binds, was ruled out, is
undetermined, or no longer applies (D22). Obligations live in the body under
`## Obligations` as `### <ID> · <title>` blocks of `- **Key:** value` bullets."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from . import frontmatter as fm

STATUSES = ("binds", "ruled-out", "undetermined", "no-longer-applies")
REQUIRED = ("id", "title", "status", "jurisdiction", "sources", "confirmed_by", "confirmed_at")
OBLIGATION_KEYS = ("When", "You must", "How often", "It says", "You'd know by", "Note")

_HEADING = re.compile(r"^### +(?P<id>[A-Za-z0-9][A-Za-z0-9._-]*) +[·-] +(?P<title>.+?)\s*$")
_BULLET = re.compile(r"^- +\*\*(?P<key>[^*]+?):\*\*\s*(?P<value>.*?)\s*$")


@dataclass
class Obligation:
    id: str
    title: str
    fields: dict = field(default_factory=dict)

    @property
    def unclear(self) -> bool:
        return not self.fields.get("You must") or not self.fields.get("It says")


@dataclass
class Regime:
    id: str
    status: str
    meta: dict
    body: str
    path: Path
    obligations: list[Obligation] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)


def parse_obligations(body: str) -> list[Obligation]:
    out: list[Obligation] = []
    current: Obligation | None = None
    for line in body.splitlines():
        h = _HEADING.match(line)
        if h:
            current = Obligation(id=h["id"], title=h["title"])
            out.append(current)
            continue
        if current is None:
            continue
        b = _BULLET.match(line)
        if b:
            current.fields[b["key"].strip()] = b["value"].strip()
    return out


def validate(meta: dict, body: str) -> list[str]:
    problems: list[str] = []
    for key in REQUIRED:
        if not meta.get(key):
            problems.append(f"{key}: required")
    status = meta.get("status")
    if status not in STATUSES:
        problems.append(f"status: must be one of {STATUSES}")
    sources = meta.get("sources")
    if not isinstance(sources, list) or not all(isinstance(s, dict) and s.get("id") for s in sources or []):
        problems.append("sources: must be a list of {id, version, retrieved}")
    obligations = parse_obligations(body)
    if status == "binds":
        applies = meta.get("applies") or {}
        if not applies.get("quote") or not applies.get("cite"):
            problems.append("applies: quote and cite are required when status is binds")
    if status == "ruled-out":
        exempt = meta.get("exempt") or {}
        if not exempt.get("reason"):
            problems.append("exempt.reason: required when status is ruled-out")
        if obligations:
            problems.append("obligations: a ruled-out regime must not list obligations")
    seen = set()
    for o in obligations:
        if o.id in seen:
            problems.append(f"obligations: duplicate id {o.id}")
        seen.add(o.id)
        for key in o.fields:
            if key not in OBLIGATION_KEYS:
                problems.append(f"{o.id}: unknown field {key!r}")
    return problems


def load_all(cdir: Path) -> list[Regime]:
    d = cdir / "regimes"
    if not d.is_dir():
        return []
    out: list[Regime] = []
    for path in sorted(d.glob("*.md")):
        try:
            meta, body = fm.load(path)
        except (fm.FrontmatterError, OSError, UnicodeDecodeError) as exc:
            # one unreadable file must not deny status/check/rescan to the rest
            out.append(Regime(id=path.stem, status="", meta={}, body="", path=path, problems=[f"unreadable: {exc}"]))
            continue
        r = Regime(id=str(meta.get("id", path.stem)), status=str(meta.get("status", "")), meta=meta, body=body, path=path)
        r.obligations = parse_obligations(body)
        r.problems = validate(meta, body)
        if meta.get("id") and path.stem != meta["id"]:
            r.problems.append(f"filename {path.name} does not match id {meta['id']}")
        out.append(r)
    return out


def counts(rs: list[Regime]) -> dict:
    by = {s: 0 for s in STATUSES}
    for r in rs:
        if r.status in by:
            by[r.status] += 1
    obligations = [o for r in rs for o in r.obligations]
    return {
        "binds": by["binds"],
        "ruled_out": by["ruled-out"],
        "undetermined": by["undetermined"],
        "no_longer_applies": by["no-longer-applies"],
        "obligations": len(obligations),
        "obligations_unclear": sum(1 for o in obligations if o.unclear),
    }
