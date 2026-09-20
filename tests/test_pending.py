import json
from pathlib import Path
import pytest

from compliance_register import paths, pending


def test_add_assigns_sequential_ids(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    a = pending.add(cdir, "source-moved", "major", "new consolidation", source="eurlex-1", affects=["CRD"], now="2026-10-01")
    b = pending.add(cdir, "regime-new", "info", "AI act may apply", now="2026-10-01")
    assert a["id"] == "chg-0001" and b["id"] == "chg-0002"
    lines = (cdir / "pending.jsonl").read_text().splitlines()
    assert len(lines) == 2 and json.loads(lines[0])["affects"] == ["CRD"]


def test_list_open_excludes_resolved(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    a = pending.add(cdir, "date-passed", "major", "review_by passed", now="2026-10-01")
    pending.add(cdir, "profile-stale", "info", "profile older than last source change", now="2026-10-01")
    pending.resolve(cdir, a["id"], "applied", by="Alex", note="re-derived", now="2026-10-02")
    open_ids = [e["id"] for e in pending.list_open(cdir)]
    assert open_ids == ["chg-0002"]
    res = json.loads((cdir / "resolutions.jsonl").read_text().splitlines()[0])
    assert res == {"id": "chg-0001", "resolved": "2026-10-02", "by": "Alex", "action": "applied", "note": "re-derived"}


def test_resolve_twice_fails(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    a = pending.add(cdir, "regime-gone", "minor", "x", now="2026-10-01")
    pending.resolve(cdir, a["id"], "dismissed", by="A", now="2026-10-02")
    with pytest.raises(ValueError):
        pending.resolve(cdir, a["id"], "dismissed", by="A", now="2026-10-02")


def test_unknown_kind_rejected(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    with pytest.raises(ValueError):
        pending.add(cdir, "nonsense", "major", "x")
