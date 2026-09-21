"""rescan — what changed in the profile since the last rescan, and which
regimes that touches. The baseline is profile.snapshot.json, holding only
confirmed answers (D7): the first run writes the snapshot and reports
nothing. Writes pending entries; edits no regime file (D18, D19)."""
from __future__ import annotations

import json
from pathlib import Path

from . import pending, profile, regimes

SNAPSHOT = "profile.snapshot.json"


def _falsy(v) -> bool:
    return v is None or v is False or v == [] or v == {} or v == ""


def _triggers(r: regimes.Regime) -> set[str]:
    out = set()
    applies = r.meta.get("applies")
    triggered = applies.get("triggered_by") if isinstance(applies, dict) else None
    for t in (triggered if isinstance(triggered, list) else []):
        if isinstance(t, dict):
            out.update(t.keys())
        elif isinstance(t, str):
            out.add(t.split(":")[0].strip())
    return out


def run(cdir: Path, *, today: str) -> dict:
    p = profile.load(cdir)
    if p is None:
        return {"changed": [], "entries": 0, "error": "no profile.md"}
    problems = profile.validate(p.meta, p.problems)
    if problems:
        return {"changed": [], "entries": 0, "error": "profile does not validate: " + "; ".join(problems), "exit": 2}
    snap_path = cdir / SNAPSHOT
    answers = p.meta["answers"]
    # only confirmed answers count (D7): a proposed value must not advance the baseline
    current = {s: (answers[s].get("value") if answers[s].get("status") == "confirmed" else None) for s in profile.DIMENSIONS}
    first = not snap_path.is_file()
    if first:
        previous = current
    else:
        try:
            previous = json.loads(snap_path.read_text(encoding="utf-8"))
            if not isinstance(previous, dict):
                raise ValueError("not a mapping")
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            # refuse by name rather than silently resetting the baseline
            return {"changed": [], "entries": 0, "error": f"{SNAPSHOT} is unreadable: {exc}", "exit": 1}
    changed = [s for s in profile.DIMENSIONS if previous.get(s) != current.get(s)]
    entries = 0
    if not first:
        rs = regimes.load_all(cdir)
        for dim in changed:
            touched = [r for r in rs if dim in _triggers(r)]
            if _falsy(current.get(dim)):
                for r in touched:
                    if r.status in ("binds", "undetermined"):
                        pending.add(cdir, "regime-gone", "major", f"{dim} is no longer true — {r.id} may no longer apply; confirm and set status", affects=[r.id], now=today)
                        entries += 1
            else:
                pending.add(cdir, "regime-new", "info", f"{dim} changed — re-run discover for this dimension" + (f" (touches {', '.join(r.id for r in touched)})" if touched else ""), affects=[r.id for r in touched], now=today)
                entries += 1
    snap_path.write_text(json.dumps(current, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return {"changed": changed, "entries": entries}
