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
    fm.save(cdir / "profile.md", confirmed_profile(automation_ai=None), "")
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
