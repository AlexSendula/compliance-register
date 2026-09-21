"""check — for every confirmed source, the cheapest question: did it move?
Three-valued. Writes to pending.jsonl and stops (D19). Never writes
last_version (only fetch does, after the guards)."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from . import pending, profile, regimes, sources as srcmod
from .fetch import default_client
from .mirror import adapters

LAST_CHECK = ".last-check"


_WATCHED = ("binds", "undetermined")  # ruled-out and no-longer-applies regimes are not watched


def _affects(cdir: Path, source_id: str) -> list[str]:
    return [r.id for r in regimes.load_all(cdir)
            if r.status in _WATCHED and any(isinstance(s, dict) and s.get("id") == source_id for s in _list(r.meta.get("sources")))]


def _list(v) -> list:
    return v if isinstance(v, list) else []


def _date_passed(cdir: Path, today: str) -> None:
    """A regime whose review_by has arrived gets one open date-passed entry."""
    open_for = {a for e in pending.list_open(cdir) if e["kind"] == "date-passed" for a in e.get("affects", [])}
    for r in regimes.load_all(cdir):
        review_by = r.meta.get("review_by")
        if r.status in _WATCHED and isinstance(review_by, str) and review_by <= today and r.id not in open_for:
            pending.add(cdir, "date-passed", "major", f"{r.id}: review_by {review_by} has passed", affects=[r.id], now=today)


def run(cdir: Path, *, ids: list[str] | None, today: str, client_factory=default_client) -> dict:
    srcs = srcmod.load(cdir)
    chosen = [s for s in srcs if s.tier != "refuse" and ((ids is None and s.status == "confirmed") or (ids and s.id in ids))]
    rep = {"fresh": 0, "moved": 0, "unreachable": 0, "details": {}, "exit": 0}
    if not chosen:
        rep["exit"] = 2
        rep["details"]["_"] = "nothing to check — no confirmed sources"
        _date_passed(cdir, today)  # review_by is the only signal for a refuse-tier source
        return rep
    refused = srcmod.refusals(chosen, ids)
    if refused:  # validation before network: no request is made
        rep["details"].update(refused)
        rep["exit"] = 2
        return rep
    any_moved = False
    open_kinds = {(e["kind"], e.get("source")) for e in pending.list_open(cdir)}
    open_to = {(e["kind"], e.get("source"), e.get("to")) for e in pending.list_open(cdir)}  # dedupe key for moved/next
    resolved = adapters.prefetch(chosen, client_factory, today=today)
    for s in chosen:
        try:
            r = adapters.get(s.adapter).check(s, client_factory(s), today=today, cdir=cdir, **resolved.get(s.adapter, {}))
        except Exception as exc:  # one bad source must never abort the run for the rest
            r = adapters.CheckResult("unreachable", None, f"{type(exc).__name__}: {exc}")
        rep[r.status] += 1
        rep["details"][s.id] = r.detail
        affects = _affects(cdir, s.id)
        if r.status == "moved":
            any_moved = True
            if ("source-moved", s.id, r.version) not in open_to:
                pending.add(cdir, "source-moved", "major", r.detail, source=s.id, affects=affects,
                            extra={"from": s.last_version, "to": r.version, "changed": r.changed[:20]}, now=today)
        elif r.status == "unreachable":
            if ("source-unreachable", s.id) not in open_kinds:
                pending.add(cdir, "source-unreachable", "info", r.detail, source=s.id, affects=affects, now=today)
        if r.next_version and r.next_version != s.next_version and ("source-next", s.id, r.next_version) not in open_to:
            pending.add(cdir, "source-next", "info", f"a future consolidation is scheduled: {r.next_version}",
                        source=s.id, affects=affects, extra={"to": r.next_version, "effective": r.next_date}, now=today)
        if r.next_version:
            s.next_version = r.next_version
        s.last_checked = today
        s.last_status = r.status
    if rep["unreachable"]:
        rep["exit"] = 1  # ran, but at least one source could not be told
    srcmod.save(cdir, srcs)
    _date_passed(cdir, today)
    (cdir / LAST_CHECK).write_text(f"{today}T{dt.datetime.now(dt.timezone.utc).strftime('%H:%M:%SZ')}\n", encoding="utf-8")
    p = profile.load(cdir)
    if p is not None and p.problems:
        rep["details"]["profile.md"] = "; ".join(p.problems)
        p = None
    if any_moved and p is not None and ("profile-stale", None) not in open_kinds:
        confirmed = str(p.meta.get("confirmed_at") or "")
        if not confirmed or confirmed < today:
            pending.add(cdir, "profile-stale", "info", "a source moved since the profile was confirmed — run rescan", now=today)
    return rep
