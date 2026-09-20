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


def test_validation_problem_exits_2_before_any_request(project: Path):
    cdir, _ = setup(project)
    srcs = sources.load(cdir); srcs[0].url = "http://reg.test/sitemap.xml"; sources.save(cdir, srcs)
    from compliance_register.mirror import http
    from tests.fakehttp import FakeOpener
    opener = FakeOpener({})
    factory = lambda source: http.Http(user_agent="t", delay_seconds=0, sleep=lambda s: None, opener=opener)
    rep = fetch.run(cdir, ids=None, force=False, today="2026-09-20", client_factory=factory)
    assert rep["exit"] == 2 and "https" in rep["details"]["nl-reg"] and opener.requests == []


def test_named_unconfirmed_source_is_refused(project: Path):
    cdir, _ = setup(project)
    srcs = sources.load(cdir); srcs[0].status = "proposed"; sources.save(cdir, srcs)
    from compliance_register.mirror import http
    from tests.fakehttp import FakeOpener
    opener = FakeOpener({})
    factory = lambda source: http.Http(user_agent="t", delay_seconds=0, sleep=lambda s: None, opener=opener)
    rep = fetch.run(cdir, ids=["nl-reg"], force=False, today="2026-09-20", client_factory=factory)
    assert rep["exit"] == 2 and "required confirmation missing" in rep["details"]["nl-reg"] and opener.requests == []
    assert rep["written"] == 0


def test_guard_refusal_writes_one_source_unreachable_and_exits_1(project: Path):
    from compliance_register import pending
    cdir, _ = setup(project)
    from compliance_register.mirror import http
    from tests.fakehttp import FakeOpener
    sm = '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://reg.test/a</loc><lastmod>2026-01-10</lastmod></url></urlset>'
    routes = {"https://reg.test/robots.txt": (404, {}, ""), "https://reg.test/sitemap.xml": (200, {"Content-Type": "application/xml"}, sm),
              "https://reg.test/a": (200, {"Content-Type": "application/pdf"}, "%PDF-1.4 not html")}
    factory = lambda source: http.Http(user_agent="t", delay_seconds=0, sleep=lambda s: None, opener=FakeOpener(routes))
    rep = fetch.run(cdir, ids=None, force=False, today="2026-09-20", client_factory=factory)
    assert rep["exit"] == 1 and rep["written"] == 0
    fetch.run(cdir, ids=None, force=False, today="2026-09-21", client_factory=factory)
    entries = [e for e in pending.list_open(cdir) if e["kind"] == "source-unreachable"]
    assert len(entries) == 1 and entries[0]["source"] == "nl-reg" and "https://reg.test/a" in entries[0]["summary"]
    assert entries[0]["severity"] == "info" and entries[0]["affects"] == ["COOKIES"]
