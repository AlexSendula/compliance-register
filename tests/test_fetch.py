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


def test_adapter_exception_is_refused_and_run_continues(project: Path, monkeypatch):
    cdir, factory = setup(project)
    from compliance_register.mirror.adapters import sitemap
    monkeypatch.setattr(sitemap, "fetch", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("adapter bug")))
    rep = fetch.run(cdir, ids=None, force=False, today="2026-09-20", client_factory=factory)
    assert rep["written"] == 0 and "RuntimeError: adapter bug" in str(rep["details"]["nl-reg"])
    assert sources.load(cdir)[0].last_fetched is None
