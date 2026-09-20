"""fetch — acquire or refresh confirmed sources into the mirror."""
from __future__ import annotations

from pathlib import Path

from . import sources as srcmod
from .mirror import adapters, http as _http


def default_client(source: srcmod.Source) -> _http.Http:
    return _http.Http(
        user_agent=_http.user_agent(source.headers.get("user_agent", "default")),
        delay_seconds=source.delay_seconds,
    )


def run(cdir: Path, *, ids: list[str] | None, force: bool, today: str, client_factory=default_client) -> dict:
    srcs = srcmod.load(cdir)
    chosen = [s for s in srcs if (ids is None and s.status == "confirmed") or (ids and s.id in ids)]
    rep = {"written": 0, "skipped": 0, "refused": [], "details": {}, "exit": 0}
    for s in chosen:
        if s.tier == "refuse":
            rep["refused"].append(s.id)
            rep["details"][s.id] = "tier: refuse — licence or robots forbid fetching"
            if ids:
                rep["exit"] = 2
            continue
        try:
            r = adapters.get(s.adapter).fetch(s, client_factory(s), cdir, today=today, force=force)
        except Exception as exc:  # one bad source must never abort the run for the rest
            r = adapters.FetchResult(refused=[f"{type(exc).__name__}: {exc}"])
        rep["written"] += len(r.written)
        rep["skipped"] += r.skipped
        if r.refused:
            rep["details"][s.id] = r.refused
        if r.written:
            s.last_fetched = today
            if r.version:
                s.last_version = r.version
    srcmod.save(cdir, srcs)
    return rep
