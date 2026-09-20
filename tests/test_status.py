from pathlib import Path

from compliance_register import frontmatter as fm, paths, pending, profile, status
from tests.test_regimes import META, BODY, write


def test_report_on_empty_project(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    rep = status.report(cdir, today="2026-09-20")
    assert rep["profile"]["present"] is False
    assert rep["regimes"]["binds"] == 0
    assert rep["pending"]["open"] == 0
    assert rep["last_check"] is None


def test_report_full(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    meta = profile.empty()
    for s in profile.DIMENSIONS:
        meta["answers"][s] = {"value": "x", "status": "confirmed", "evidence": []}
    meta["confirmed_by"], meta["confirmed_at"] = "Alex", "2026-09-01"
    fm.save(cdir / "profile.md", meta, "")
    write(cdir, META)
    pending.add(cdir, "source-moved", "major", "x", now="2026-09-19")
    (cdir / ".last-check").write_text("2026-09-19T10:00:00Z")
    rep = status.report(cdir, today="2026-09-20")
    assert rep["profile"] == {"present": True, "problems": [], "confirmed_at": "2026-09-01", "age_days": 19}
    assert rep["regimes"]["obligations"] == 2
    assert rep["pending"] == {"open": 1, "by_severity": {"major": 1, "minor": 0, "info": 0}}
    assert rep["last_check"] == "2026-09-19T10:00:00Z"
    text = status.render(rep)
    assert "compliant" not in text.lower()
    assert "GDPR-002" not in text  # unclear obligations are counted, not listed
    assert "1 open" in text
