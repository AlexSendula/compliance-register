"""sources.json — where law lives for this project's jurisdictions, and how
each source is fetched and watched. Discovered by the agent, confirmed by a
human, nothing hardcoded (D17)."""
from __future__ import annotations

import ipaddress
import json
import os
import tempfile
from dataclasses import dataclass, field, asdict
from pathlib import Path
from urllib.parse import urlsplit

FILENAME = "sources.json"
TIERS = ("api", "sitemap", "feed", "page-hash", "refuse")
KINDS = ("legislation", "gazette", "regulator", "contract", "standard")
STATUSES = ("proposed", "confirmed", "unresolved")
FRESHNESS = ("fresh", "unreachable", "moved")
_DEFAULT_ADAPTER = {"sitemap": "sitemap", "feed": "feed", "page-hash": "pagehash"}


class SourcesError(Exception):
    """sources.json cannot be read as a list of sources."""


@dataclass
class Source:
    id: str
    jurisdiction: str
    kind: str
    url: str
    covers: str = ""
    tier: str = "page-hash"
    adapter: str | None = None
    config: dict = field(default_factory=dict)
    change_signal: str = ""
    licence: dict = field(default_factory=lambda: {"redistribute": False, "attribution": None})
    allowed_hosts: list[str] = field(default_factory=list)
    headers: dict = field(default_factory=lambda: {"user_agent": "default"})
    delay_seconds: int = 10
    status: str = "proposed"
    last_checked: str | None = None
    last_status: str | None = None
    last_version: str | None = None
    next_version: str | None = None   # a scheduled future consolidation check has already reported
    last_fetched: str | None = None
    evidence: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "Source":
        known = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        s = cls(**known)
        if not s.adapter:
            s.adapter = _DEFAULT_ADAPTER.get(s.tier)
        if not s.allowed_hosts:
            host = urlsplit(s.url).hostname
            s.allowed_hosts = [host] if host else []
        return s

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def redistributable(self) -> bool:
        return bool(self.licence.get("redistribute") is True)


def validate(s: Source) -> list[str]:
    p: list[str] = []
    if s.tier not in TIERS:
        p.append(f"{s.id}: tier must be one of {TIERS}")
    if s.tier == "api" and not s.adapter:
        p.append(f"{s.id}: api tier needs an explicit adapter (eurlex)")
    if s.kind not in KINDS:
        p.append(f"{s.id}: kind must be one of {KINDS}")
    if s.status not in STATUSES:
        p.append(f"{s.id}: status must be one of {STATUSES}")
    if not isinstance(s.licence, dict) or not isinstance(s.licence.get("redistribute"), bool):
        p.append(f"{s.id}: licence.redistribute must be true or false")
    if urlsplit(s.url).scheme != "https":
        p.append(f"{s.id}: url must be https")
    for h in s.allowed_hosts:
        if _is_private_host(h):
            p.append(f"{s.id}: allowed_hosts must not include local or private addresses ({h})")
    return p


def refusals(chosen: list[Source], ids: list[str] | None) -> dict[str, str]:
    """{source id: why it must not be touched} — validation problems, and a
    source named on the command line that no human has confirmed. Empty means
    every chosen source may go to the network."""
    out: dict[str, str] = {}
    for s in chosen:
        problems = validate(s)
        if ids and s.status != "confirmed":
            problems.append(f"{s.id}: required confirmation missing (status {s.status})")
        if problems:
            out[s.id] = "; ".join(problems)
    return out


def _is_private_host(host: str) -> bool:
    if host.lower() == "localhost":
        return True
    try:
        ip = ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        return False
    return ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_reserved or ip.is_unspecified


def load(cdir: Path) -> list[Source]:
    path = cdir / FILENAME
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise SourcesError(f"{FILENAME}: invalid JSON: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("sources", []), list):
        raise SourcesError(f"{FILENAME}: must be an object with a 'sources' list")
    try:
        return [Source.from_dict(d) for d in data.get("sources", [])]
    except (TypeError, ValueError, AttributeError) as exc:
        raise SourcesError(f"{FILENAME}: malformed source entry: {exc}") from exc


def save(cdir: Path, srcs: list[Source]) -> None:
    path = cdir / FILENAME
    payload = {"schema": 1, "sources": [s.to_dict() for s in srcs]}
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def get(srcs: list[Source], id: str) -> Source:
    for s in srcs:
        if s.id == id:
            return s
    raise KeyError(id)
