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


def test_validate_rejects_an_answer_whose_status_is_not_one_of_unanswered_proposed_confirmed_and_a_key_that_is_not_a_known_dimension():
    meta = profile.empty()
    meta["answers"]["size"] = {"value": "x", "status": "maybe", "evidence": []}
    meta["answers"]["bogus"] = {"value": "x", "status": "confirmed", "evidence": []}
    problems = profile.validate(meta)
    assert any(p.startswith("size:") and "status must be one of" in p for p in problems)
    assert "bogus: not a known dimension" in problems


def test_validate_requires_confirmed_by_and_confirmed_at_only_once_every_answer_is_confirmed():
    meta = profile.empty()
    for slug in profile.DIMENSIONS:
        meta["answers"][slug] = {"value": "x", "status": "confirmed", "evidence": []}
    problems = profile.validate(meta)
    assert any(p.startswith("confirmed_by") for p in problems)
    assert any(p.startswith("confirmed_at") for p in problems)
    meta["answers"]["size"]["status"] = "proposed"  # one still proposed: nothing is required yet
    assert profile.validate(meta) == []


def test_profile_diff_ignores_keys_outside_dimensions_and_reports_only_known_slugs():
    a = profile.empty()
    b = profile.empty()
    a["answers"]["bogus"] = {"value": 1, "status": "confirmed", "evidence": []}
    b["answers"]["bogus"] = {"value": 2, "status": "confirmed", "evidence": []}
    b["answers"]["sector"]["value"] = "finance"
    assert profile.diff(a, b) == ["sector"]
