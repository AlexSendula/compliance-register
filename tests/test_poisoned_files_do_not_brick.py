"""One corrupt line or file must not deny every command to the honest rest
(docs-mirror SEC-049/050 shape: skip and report, never raise at the row)."""
import json
from pathlib import Path

import pytest

from compliance_register import paths, pending, regimes, sources, status
from compliance_register.mirror import store
from tests.test_cli import run
from tests.test_regimes import META, write
from tests.test_sources import EURLEX


def test_pending_skips_unreadable_lines_and_status_counts_them(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    pending.add(cdir, "date-passed", "major", "good", now="2026-10-01")
    with (cdir / "pending.jsonl").open("a") as fh:
        fh.write("{not json\n")
        fh.write(json.dumps({"kind": "date-passed", "summary": "no id"}) + "\n")
    assert [e["summary"] for e in pending.list_open(cdir)] == ["good"]
    rep = status.report(cdir, today="2026-10-02")
    assert rep["pending"]["open"] == 1 and rep["pending"]["unreadable"] == 2
    assert "pending: 2 unreadable lines" in status.render(rep)

def test_regime_with_bad_frontmatter_is_reported_not_fatal(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    write(cdir, META)
    (cdir / "regimes" / "BAD.md").write_text("---\nid: [unterminated\n---\n\nbody\n")
    rs = regimes.load_all(cdir)
    assert [r.id for r in rs] == ["BAD", "GDPR"]
    bad = rs[0]
    assert bad.status == "" and bad.problems and not bad.obligations
    assert rs[1].problems == []

