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
    meta["answers"]["size"]["status"] = "proposed"  # one still proposed: neither is required yet
    assert not any(p.endswith("once every answer is confirmed") for p in profile.validate(meta))


def proposed_profile(*, proposed=("size",), **fields):
    meta = profile.empty()
    for slug in profile.DIMENSIONS:
        meta["answers"][slug] = {"value": "x", "status": "confirmed", "evidence": []}
    for slug in proposed:
        meta["answers"][slug] = {"value": "guess", "status": "proposed", "evidence": ["a.py"]}
    meta.update(fields)
    return meta


def test_validate_reports_every_answer_still_proposed():
    meta = proposed_profile(proposed=("size", "sector"), confirmed_by=None, confirmed_at=None)
    problems = profile.validate(meta)
    assert "size: proposed, not confirmed" in problems
    assert "sector: proposed, not confirmed" in problems
    assert len(problems) == 2  # nothing else is wrong with it, and it still does not pass


def test_validate_reports_an_attestation_set_before_every_answer_is_confirmed():
    meta = proposed_profile(confirmed_by="Alex", confirmed_at="2026-09-22")
    problems = profile.validate(meta)
    assert "confirmed_by and confirmed_at set while 1 answer(s) are not confirmed" in problems
    meta = proposed_profile(confirmed_by="Alex")
    assert "confirmed_by set while 1 answer(s) are not confirmed" in profile.validate(meta)


def test_blocking_is_the_rescan_gate_and_ignores_proposed_and_a_premature_attestation():
    meta = proposed_profile(confirmed_by="Alex", confirmed_at="2026-09-22")
    assert profile.validate(meta)  # reported
    assert profile.blocking(meta) == []  # but a baseline is still meaningful
    meta["answers"]["users"]["status"] = "unanswered"
    assert profile.blocking(meta) == ["users: unanswered"]
    meta = proposed_profile()
    meta["answers"]["sector"]["value"] = None  # a confirmed `unknown` still blocks (D29)
    assert profile.blocking(meta) == ["sector: confirmed but value is null"]


def test_blocking_passes_an_unreadable_file_through():
    assert profile.blocking({}, ["unreadable: boom"]) == ["unreadable: boom"]


def test_validate_does_not_trip_over_an_answer_that_is_not_a_mapping():
    meta = profile.empty()
    meta["answers"]["size"] = "x"
    assert "size: missing" in profile.validate(meta)


def test_diff_does_not_trip_over_an_answer_that_is_not_a_mapping():
    """A hand-written `size: small` is reported by the validators; diff must not
    be the one command that raises on it (Principle 9)."""
    a, b = profile.empty(), profile.empty()
    a["answers"]["size"] = "small"
    b["answers"]["size"] = {"value": "x", "status": "confirmed", "evidence": []}
    assert profile.diff(a, b) == ["size"]
    assert profile.diff({"answers": "not a mapping"}, b) == ["size"]


def test_profile_diff_ignores_keys_outside_dimensions_and_reports_only_known_slugs():
    a = profile.empty()
    b = profile.empty()
    a["answers"]["bogus"] = {"value": 1, "status": "confirmed", "evidence": []}
    b["answers"]["bogus"] = {"value": 2, "status": "confirmed", "evidence": []}
    b["answers"]["sector"]["value"] = "finance"
    assert profile.diff(a, b) == ["sector"]
