"""One report: what is registered, how old the profile is, what is pending.
It reports counts and never a verdict (D1)."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from . import pending, profile, regimes

LAST_CHECK = ".last-check"


def _age_days(iso: str | None, today: str | None) -> int | None:
    if not iso:
        return None
    t = dt.date.fromisoformat(today) if today else dt.date.today()
    return (t - dt.date.fromisoformat(str(iso)[:10])).days


def report(cdir: Path, today: str | None = None) -> dict:
    p = profile.load(cdir)
    prof = {"present": False, "problems": [], "confirmed_at": None, "age_days": None}
    if p is not None:
        prof = {
            "present": True,
            "problems": profile.validate(p.meta),
            "confirmed_at": p.meta.get("confirmed_at"),
            "age_days": _age_days(p.meta.get("confirmed_at"), today),
        }
    rs = regimes.load_all(cdir)
    open_entries = pending.list_open(cdir)
    by_sev = {s: sum(1 for e in open_entries if e.get("severity") == s) for s in pending.SEVERITIES}
    lc = cdir / LAST_CHECK
    return {
        "profile": prof,
        "regimes": regimes.counts(rs),
        "pending": {"open": len(open_entries), "by_severity": by_sev, "unreadable": pending.unreadable(cdir)},
        "last_check": lc.read_text(encoding="utf-8").strip() if lc.is_file() else None,
        "problems": [f"{r.id}: {x}" for r in rs for x in r.problems],
    }


def render(rep: dict) -> str:
    p, r, pe = rep["profile"], rep["regimes"], rep["pending"]
    lines = []
    if not p["present"]:
        lines.append("profile: none — run the profile stage first")
    else:
        age = f"{p['age_days']} days old" if p["age_days"] is not None else "not yet confirmed"
        state = "valid" if not p["problems"] else f"{len(p['problems'])} problem(s)"
        lines.append(f"profile: {state}, {age}")
    lines.append(
        f"regimes: {r['binds']} bind · {r['ruled_out']} ruled out · "
        f"{r['undetermined']} undetermined · {r['no_longer_applies']} no longer apply"
    )
    lines.append(f"obligations: {r['obligations']} registered · {r['obligations_unclear']} unclear")
    sev = pe["by_severity"]
    lines.append(f"pending: {pe['open']} open (major {sev['major']} · minor {sev['minor']} · info {sev['info']})")
    if pe.get("unreadable"):
        lines.append(f"pending: {pe['unreadable']} unreadable lines")
    lines.append(f"last check: {rep['last_check'] or 'never'}")
    for problem in rep["problems"]:
        lines.append(f"problem: {problem}")
    return "\n".join(lines) + "\n"
