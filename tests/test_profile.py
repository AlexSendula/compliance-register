from pathlib import Path
import pytest

from compliance_register import frontmatter as fm, paths, profile


def test_dimensions_are_fifteen_and_ordered():
    assert len(profile.DIMENSIONS) == 15
    assert profile.DIMENSIONS[0] == "establishment"
    assert profile.DIMENSIONS[1] == "directed_activity"
    assert profile.DIMENSIONS[-1] == "time_change"


def test_empty_has_every_dimension_unanswered():
    meta = profile.empty()
    assert set(meta["answers"]) == set(profile.DIMENSIONS)
    assert all(a["status"] == "unanswered" and a["value"] is None for a in meta["answers"].values())


def test_validate_flags_missing_and_null():
    meta = profile.empty()
    meta["answers"]["size"] = {"value": None, "status": "confirmed", "evidence": []}
    problems = profile.validate(meta)
    assert any("size" in p and "null" in p for p in problems)
    assert any("unanswered" in p for p in problems)


def test_validate_ok():
    meta = profile.empty()
    for slug in profile.DIMENSIONS:
        meta["answers"][slug] = {"value": "x", "status": "confirmed", "evidence": []}
    meta["confirmed_by"] = "Alex"
    meta["confirmed_at"] = "2026-09-20"
    assert profile.validate(meta) == []


def test_diff_lists_changed_dimensions():
    a = profile.empty()
    b = profile.empty()
    b["answers"]["automation_ai"]["value"] = {"components": ["translation"]}
    b["answers"]["automation_ai"]["status"] = "confirmed"
    assert profile.diff(a, b) == ["automation_ai"]


def test_load_returns_none_when_absent(project: Path):
    cdir = paths.compliance_dir(project)
    cdir.mkdir()
    assert profile.load(cdir) is None


def test_load_reads_file(project: Path):
    cdir = paths.compliance_dir(project)
    cdir.mkdir()
    fm.save(cdir / "profile.md", profile.empty(), "notes\n")
    p = profile.load(cdir)
    assert p is not None and p.meta["schema"] == 1 and p.body == "notes\n"
