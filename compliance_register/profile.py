"""profile.md — the 15 answers, with evidence and confirmation state.

The slugs are the dimensions from references/dimensions-checklist.md, in
order. Questions 1 and 2 come first because they choose the jurisdictions."""
from __future__ import annotations

from dataclasses import dataclass
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


def validate(meta: dict) -> list[str]:
    problems: list[str] = []
    answers = meta.get("answers")
    if not isinstance(answers, dict):
        return ["profile has no answers mapping"]
    for slug in DIMENSIONS:
        a = answers.get(slug)
        if not isinstance(a, dict):
            problems.append(f"{slug}: missing")
            continue
        status = a.get("status")
        if status not in STATUSES:
            problems.append(f"{slug}: status must be one of {STATUSES}")
        if status == "unanswered":
            problems.append(f"{slug}: unanswered")
        if status == "confirmed" and a.get("value") is None:
            problems.append(f"{slug}: confirmed but value is null")
    for extra in set(answers) - set(DIMENSIONS):
        problems.append(f"{extra}: not a known dimension")
    if all(answers.get(s, {}).get("status") == "confirmed" for s in DIMENSIONS):
        if not meta.get("confirmed_by"):
            problems.append("confirmed_by is required once every answer is confirmed")
        if not meta.get("confirmed_at"):
            problems.append("confirmed_at is required once every answer is confirmed")
    return problems


def diff(old: dict, new: dict) -> list[str]:
    changed = []
    for slug in DIMENSIONS:
        ov = (old.get("answers") or {}).get(slug, {}).get("value")
        nv = (new.get("answers") or {}).get(slug, {}).get("value")
        if ov != nv:
            changed.append(slug)
    return changed


def load(cdir: Path) -> Profile | None:
    path = cdir / FILENAME
    if not path.is_file():
        return None
    meta, body = fm.load(path)
    return Profile(meta=meta, body=body, path=path)
