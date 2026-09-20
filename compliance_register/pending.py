"""pending.jsonl and resolutions.jsonl — record, surface, delegate (D19).

Both files are append-only. State is derived by replay so a human can read
either file top to bottom and never wonder what was edited."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

KINDS = ("source-moved", "source-unreachable", "source-next", "regime-new", "regime-gone", "date-passed", "profile-stale")
SEVERITIES = ("major", "minor", "info")
ACTIONS = ("applied", "dismissed", "deferred")
PENDING = "pending.jsonl"
RESOLUTIONS = "resolutions.jsonl"


def _today(now: str | None) -> str:
    return now or dt.date.today().isoformat()


def _read(path: Path) -> tuple[list[dict], int]:
    """(entries, unreadable). A corrupt line is skipped and counted, never
    raised — one bad line must not deny status/pending/resolve/check."""
    if not path.is_file():
        return [], 0
    out, unreadable = [], 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except ValueError:
            entry = None
        if isinstance(entry, dict) and entry.get("id"):
            out.append(entry)
        else:
            unreadable += 1
    return out, unreadable


def unreadable(cdir: Path) -> int:
    return _read(cdir / PENDING)[1] + _read(cdir / RESOLUTIONS)[1]


def _append(path: Path, entry: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def add(cdir: Path, kind: str, severity: str, summary: str, *, source: str | None = None,
        affects=(), extra: dict | None = None, now: str | None = None) -> dict:
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}")
    if severity not in SEVERITIES:
        raise ValueError(f"severity must be one of {SEVERITIES}")
    existing, skipped = _read(cdir / PENDING)
    entry = {
        "id": f"chg-{len(existing) + skipped + 1:04d}",
        "detected": _today(now),
        "kind": kind,
        "severity": severity,
        "source": source,
        "affects": list(affects),
        "summary": summary,
        "status": "pending",
    }
    if extra:
        entry.update({k: v for k, v in extra.items() if k not in entry})
    _append(cdir / PENDING, entry)
    return entry


def list_open(cdir: Path) -> list[dict]:
    resolved = {r["id"] for r in _read(cdir / RESOLUTIONS)[0]}
    return [e for e in _read(cdir / PENDING)[0] if e["id"] not in resolved]


def resolve(cdir: Path, id: str, action: str, by: str, note: str = "", now: str | None = None) -> dict:
    if action not in ACTIONS:
        raise ValueError(f"action must be one of {ACTIONS}")
    if id not in {e["id"] for e in _read(cdir / PENDING)[0]}:
        raise KeyError(id)
    if id in {r["id"] for r in _read(cdir / RESOLUTIONS)[0]}:
        raise ValueError(f"{id} is already resolved")
    entry = {"id": id, "resolved": _today(now), "by": by, "action": action, "note": note}
    _append(cdir / RESOLUTIONS, entry)
    return entry
