from pathlib import Path

from compliance_register import fetch, paths, sources
from tests.test_check import setup


def test_fetch_writes_and_updates_source(project: Path):
    cdir, factory = setup(project)
    rep = fetch.run(cdir, ids=None, force=False, today="2026-09-20", client_factory=factory)
    assert rep["written"] == 1 and rep["refused"] == []
    s = sources.load(cdir)[0]
    assert s.last_fetched == "2026-09-20"
    assert list((cdir / "mirror" / "nl" / "nl-reg").glob("*.md"))


def test_fetch_refuses_refuse_tier(project: Path):
    cdir, factory = setup(project)
    srcs = sources.load(cdir); srcs[0].tier = "refuse"; sources.save(cdir, srcs)
    rep = fetch.run(cdir, ids=["nl-reg"], force=False, today="2026-09-20", client_factory=factory)
    assert rep["refused"] == ["nl-reg"] and rep["exit"] == 2
