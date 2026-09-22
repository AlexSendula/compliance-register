from pathlib import Path

from compliance_register import frontmatter as fm, paths, pending, profile, rescan
from tests.test_regimes import META, write


def confirmed_profile(**values):
    meta = profile.empty()
    for s in profile.DIMENSIONS:
        meta["answers"][s] = {"value": values.get(s, "x"), "status": "confirmed", "evidence": []}
    meta["confirmed_by"], meta["confirmed_at"] = "Alex", "2026-09-20"
    return meta


def test_first_rescan_snapshots_without_entries(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    fm.save(cdir / "profile.md", confirmed_profile(automation_ai={"components": ["translation"]}), "")
    rep = rescan.run(cdir, today="2026-09-20")
    assert rep["entries"] == 0 and (cdir / "profile.snapshot.json").is_file()


def test_removed_trigger_marks_regime_gone(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    fm.save(cdir / "profile.md", confirmed_profile(automation_ai={"components": ["translation"]}), "")
    write(cdir, dict(META, id="AIACT", applies={"quote": "q", "cite": "Art. 2", "triggered_by": [{"automation_ai": True}]}))
    rescan.run(cdir, today="2026-09-20")
    fm.save(cdir / "profile.md", confirmed_profile(automation_ai=False), "")
    rep = rescan.run(cdir, today="2026-10-01")
    assert rep["changed"] == ["automation_ai"]
    kinds = [(e["kind"], e["affects"]) for e in pending.list_open(cdir)]
    assert ("regime-gone", ["AIACT"]) in kinds


def test_new_answer_asks_for_discover(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    fm.save(cdir / "profile.md", confirmed_profile(third_party_content=False), "")
    rescan.run(cdir, today="2026-09-20")
    fm.save(cdir / "profile.md", confirmed_profile(third_party_content={"user_uploads": True}), "")
    rescan.run(cdir, today="2026-10-01")
    e = pending.list_open(cdir)[0]
    assert e["kind"] == "regime-new" and "third_party_content" in e["summary"]


def test_snapshot_holds_only_confirmed_values(project: Path):
    import json
    cdir = paths.compliance_dir(project); cdir.mkdir()
    meta = confirmed_profile(sector="finance")
    meta["answers"]["sector"]["status"] = "proposed"
    fm.save(cdir / "profile.md", meta, "")
    rep = rescan.run(cdir, today="2026-09-20")
    assert not rep.get("error")
    snap = json.loads((cdir / "profile.snapshot.json").read_text())
    assert snap["sector"] is None and snap["users"] == "x"
    # confirming the proposed value later is a change that gets a regime-new entry
    meta["answers"]["sector"]["status"] = "confirmed"
    fm.save(cdir / "profile.md", meta, "")
    rep = rescan.run(cdir, today="2026-10-01")
    assert rep["changed"] == ["sector"]


def test_re_proposing_a_confirmed_answer_neither_moves_the_snapshot_nor_files_an_entry(project: Path):
    """"Not yet confirmed" is never "no longer true" (Principle 4): a proposal carries
    the last confirmed value forward instead of reading as the answer going away."""
    import json
    cdir = paths.compliance_dir(project); cdir.mkdir()
    fm.save(cdir / "profile.md", confirmed_profile(personal_data={"categories": ["contact"]}), "")
    write(cdir, dict(META, id="GDPR", applies={"quote": "q", "cite": "Art. 2", "triggered_by": [{"personal_data": True}]}))
    rescan.run(cdir, today="2026-09-20")
    meta = confirmed_profile(personal_data={"categories": ["contact"]})
    meta["answers"]["personal_data"]["status"] = "proposed"  # agent re-proposes; human has not spoken
    fm.save(cdir / "profile.md", meta, "")
    rep = rescan.run(cdir, today="2026-10-01")
    assert rep["changed"] == [] and rep["entries"] == 0
    assert pending.list_open(cdir) == []
    assert json.loads((cdir / "profile.snapshot.json").read_text())["personal_data"] == {"categories": ["contact"]}


def test_invalid_profile_is_refused_with_exit_2(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    fm.save(cdir / "profile.md", profile.empty(), "")
    rep = rescan.run(cdir, today="2026-09-20")
    assert rep["exit"] == 2 and "unanswered" in rep["error"]
    assert not (cdir / "profile.snapshot.json").exists()


def test_corrupt_snapshot_is_refused_with_a_message(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    fm.save(cdir / "profile.md", confirmed_profile(), "")
    (cdir / "profile.snapshot.json").write_text("{not json", encoding="utf-8")
    rep = rescan.run(cdir, today="2026-09-20")
    assert rep["exit"] == 1 and "profile.snapshot.json" in rep["error"]
    assert (cdir / "profile.snapshot.json").read_text() == "{not json"  # never silently reset the baseline


def test_corrupt_profile_is_refused_with_a_message(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    (cdir / "profile.md").write_text("---\nanswers: [\n", encoding="utf-8")
    rep = rescan.run(cdir, today="2026-09-20")
    assert rep["exit"] == 2 and "unreadable" in rep["error"]


def test_run_returns_error_no_profile_md_when_the_profile_is_absent(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    rep = rescan.run(cdir, today="2026-09-20")
    assert rep["error"] == "no profile.md" and rep["changed"] == [] and rep["entries"] == 0
    assert not (cdir / "profile.snapshot.json").exists()


def test_ruled_out_and_no_longer_applies_regimes_never_receive_a_regime_gone_entry(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    fm.save(cdir / "profile.md", confirmed_profile(automation_ai={"components": ["translation"]}), "")
    applies = {"quote": "q", "cite": "Art. 2", "triggered_by": [{"automation_ai": True}]}
    write(cdir, dict(META, id="AIACT", applies=applies))
    write(cdir, dict(META, id="DSA", status="ruled-out", applies=applies), body="")
    write(cdir, dict(META, id="OLD", status="no-longer-applies", applies=applies), body="")
    rescan.run(cdir, today="2026-09-20")
    fm.save(cdir / "profile.md", confirmed_profile(automation_ai=False), "")
    rep = rescan.run(cdir, today="2026-10-01")
    gone = [e["affects"] for e in pending.list_open(cdir) if e["kind"] == "regime-gone"]
    assert rep["entries"] == 1 and gone == [["AIACT"]]
