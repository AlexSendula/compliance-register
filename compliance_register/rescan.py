"""rescan — what changed in the profile since last time, and which regimes
that touches. Writes pending entries; edits no regime file (D18, D19)."""
from __future__ import annotations

import json
from pathlib import Path

from . import pending, profile, regimes

SNAPSHOT = "profile.snapshot.json"


def _falsy(v) -> bool:
    return v is None or v is False or v == [] or v == {} or v == ""


def _triggers(r: regimes.Regime) -> set[str]:
    out = set()
    for t in ((r.meta.get("applies") or {}).get("triggered_by") or []):
        if isinstance(t, dict):
            out.update(t.keys())
        elif isinstance(t, str):
            out.add(t.split(":")[0].strip())
    return out


def run(cdir: Path, *, today: str) -> dict:
    p = profile.load(cdir)
    if p is None:
        return {"changed": [], "entries": 0, "error": "no profile.md"}
    snap_path = cdir / SNAPSHOT
    current = {s: p.meta["answers"][s]["value"] for s in profile.DIMENSIONS if s in p.meta.get("answers", {})}
    first = not snap_path.is_file()
    previous = json.loads(snap_path.read_text(encoding="utf-8")) if not first else current
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
