"""profile.md — the 15 answers, with evidence and confirmation state.

The slugs are the dimensions from references/dimensions-checklist.md, in
order. Questions 1 and 2 come first because they choose the jurisdictions."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import frontmatter as fm

DIMENSIONS: tuple[str, ...] = (
    "establishment",
    "directed_activity",
    "users",
    "legal_form",
    "size",
    "sector",
    "licences",
    "exchanged",
    "money_flow",
    "personal_data",
    "third_parties",
    "third_party_content",
    "role",
    "automation_ai",
    "time_change",
)

STATUSES = ("unanswered", "proposed", "confirmed")
FILENAME = "profile.md"


@dataclass
class Profile:
    meta: dict
    body: str
    path: Path
    problems: list[str] = field(default_factory=list)  # non-empty only when the file could not be read


def empty() -> dict:
    return {
        "schema": 1,
        "confirmed_by": None,
        "confirmed_at": None,
        "answers": {
            slug: {"value": None, "status": "unanswered", "evidence": []}
            for slug in DIMENSIONS
        },
    }


def _answer(meta: dict, slug: str) -> dict:
    """The answer mapping, or `{}` when the file holds something else there: a
    hand-written `size: small` is reported, never raised (Principle 9)."""
    answers = meta.get("answers")
    a = answers.get(slug) if isinstance(answers, dict) else None
    return a if isinstance(a, dict) else {}


def _checks(meta: dict, problems: list[str] | None) -> list[tuple[bool, str]]:
    """Every problem, each flagged True when it also stops `rescan` writing a
    baseline. An answer still `proposed`, and a `confirmed_by` set before the
    human has confirmed all fifteen, are reported but do not block: the snapshot
    holds the last confirmed value and a proposal moves it in neither direction
    (D7, rescan.py)."""
    out: list[tuple[bool, str]] = [(True, p) for p in (problems or [])]
    if out:  # unreadable: nothing below can be judged
        return out
    answers = meta.get("answers")
    if not isinstance(answers, dict):
        return [(True, "profile has no answers mapping")]
    for slug in DIMENSIONS:
        a = answers.get(slug)
        if not isinstance(a, dict):
            out.append((True, f"{slug}: missing"))
            continue
        status = a.get("status")
        if status not in STATUSES:
            out.append((True, f"{slug}: status must be one of {STATUSES}"))
        if status == "unanswered":
            out.append((True, f"{slug}: unanswered"))
        if status == "proposed":
            # code wrote this value; until a human confirms it, it is an inference
            # presented as fact (Principle 3) and stage 1 is not done
            out.append((False, f"{slug}: proposed, not confirmed"))
        if status == "confirmed" and a.get("value") is None:
            out.append((True, f"{slug}: confirmed but value is null"))
    for extra in sorted(set(answers) - set(DIMENSIONS)):
        out.append((True, f"{extra}: not a known dimension"))
    unconfirmed = [s for s in DIMENSIONS if _answer(meta, s).get("status") != "confirmed"]
    if not unconfirmed:
        for field_name in ("confirmed_by", "confirmed_at"):
            if not meta.get(field_name):
                out.append((True, f"{field_name} is required once every answer is confirmed"))
    else:
        # the attestation claims a human signed the whole profile off; the answers say otherwise
        attested = [f for f in ("confirmed_by", "confirmed_at") if meta.get(f)]
        if attested:
            out.append((False, f"{' and '.join(attested)} set while {len(unconfirmed)} answer(s) are not confirmed"))
    return out


def validate(meta: dict, problems: list[str] | None = None) -> list[str]:
    """Everything wrong with the profile, in dimension order. Empty means all
    fifteen are confirmed and a human signed them off."""
    return [text for _, text in _checks(meta, problems)]


def blocking(meta: dict, problems: list[str] | None = None) -> list[str]:
    """The subset `rescan` refuses on: the file is unreadable or has no answers
    mapping, a dimension is missing, `unanswered`, confirmed `unknown` (D29) or
    carries a status outside STATUSES, a key is not a dimension, or — once all
    fifteen are confirmed — `confirmed_by`/`confirmed_at` is still missing.
    Only a `proposed` answer and an attestation set early are let through."""
    return [text for blocks, text in _checks(meta, problems) if blocks]


def diff(old: dict, new: dict) -> list[str]:
    changed = []
    for slug in DIMENSIONS:
        ov = _answer(old, slug).get("value")
        nv = _answer(new, slug).get("value")
        if ov != nv:
            changed.append(slug)
    return changed


def load(cdir: Path) -> Profile | None:
    path = cdir / FILENAME
    if not path.is_file():
        return None
    try:
        meta, body = fm.load(path)
    except (fm.FrontmatterError, OSError, UnicodeDecodeError) as exc:
        # a poisoned profile.md must not deny status/check to the rest (P9); rescan and
        # profile validate see the problem through validate() and refuse loudly
        return Profile(meta={}, body="", path=path, problems=[f"unreadable: {exc}"])
    return Profile(meta=meta, body=body, path=path)
