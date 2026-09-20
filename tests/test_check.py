import json
from pathlib import Path

from compliance_register import check, paths, pending, sources, frontmatter as fm, profile
from compliance_register.mirror import http
from tests.fakehttp import FakeOpener
from tests.test_regimes import META, write

HTML = {"Content-Type": "text/html"}


def setup(project: Path, lastmod="2026-01-10", last_fetched=True):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    s = sources.Source.from_dict({
        "id": "nl-reg", "jurisdiction": "NL", "kind": "regulator", "url": "https://reg.test/sitemap.xml",
        "tier": "sitemap", "licence": {"redistribute": True, "attribution": "r"}, "status": "confirmed", "delay_seconds": 0,
    })
    sources.save(cdir, [s])
    write(cdir, dict(META, id="COOKIES", sources=[{"id": "nl-reg", "version": None, "retrieved": "2026-01-01"}]))
    sm = f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://reg.test/a</loc><lastmod>{lastmod}</lastmod></url></urlset>'
    routes = {"https://reg.test/robots.txt": (404, {}, ""), "https://reg.test/sitemap.xml": (200, {"Content-Type": "application/xml"}, sm),
              "https://reg.test/a": (200, HTML, "<html><body><p>a</p></body></html>")}
    factory = lambda source: http.Http(user_agent="t", delay_seconds=0, sleep=lambda s: None, opener=FakeOpener(routes))
    return cdir, factory


def test_check_records_moved_with_affects(project: Path):
    cdir, factory = setup(project)
    rep = check.run(cdir, ids=None, today="2026-09-20", client_factory=factory)
    assert rep["moved"] == 1
    open_ = pending.list_open(cdir)
    assert open_[0]["kind"] == "source-moved" and open_[0]["affects"] == ["COOKIES"] and open_[0]["source"] == "nl-reg"
    s = sources.load(cdir)[0]
    assert s.last_status == "moved" and s.last_version is None and s.last_checked == "2026-09-20"
    assert (cdir / ".last-check").read_text().startswith("2026-09-20")


def test_check_unreachable_is_info_never_fresh(project: Path):
    cdir, _ = setup(project)
    factory = lambda source: http.Http(user_agent="t", delay_seconds=0, sleep=lambda s: None, opener=FakeOpener({"https://reg.test/robots.txt": (404, {}, ""), "https://reg.test/sitemap.xml": (503, {}, "")}))
    rep = check.run(cdir, ids=None, today="2026-09-20", client_factory=factory)
    assert rep["unreachable"] == 1 and sources.load(cdir)[0].last_status == "unreachable"
    assert pending.list_open(cdir)[0]["kind"] == "source-unreachable"


def test_check_adds_profile_stale_once(project: Path):
    cdir, factory = setup(project)
    meta = profile.empty(); meta["confirmed_at"] = "2026-01-01"
    fm.save(cdir / "profile.md", meta, "")
    check.run(cdir, ids=None, today="2026-09-20", client_factory=factory)
    check.run(cdir, ids=None, today="2026-09-21", client_factory=factory)
    kinds = [e["kind"] for e in pending.list_open(cdir)]
    assert kinds.count("profile-stale") == 1


def test_adapter_exception_is_unreachable_and_run_continues(project: Path, monkeypatch):
    cdir, factory = setup(project)
    srcs = sources.load(cdir)
    srcs.append(sources.Source.from_dict(dict(srcs[0].to_dict(), id="nl-reg-2")))  # same sitemap, second source
    sources.save(cdir, srcs)
    from compliance_register.mirror.adapters import sitemap
    real = sitemap.check
    def boom(source, client, **kw):
        if source.id == "nl-reg":
            raise RuntimeError("adapter bug")
        return real(source, client, **kw)
    monkeypatch.setattr(sitemap, "check", boom)
    rep = check.run(cdir, ids=None, today="2026-09-20", client_factory=factory)
    assert rep["unreachable"] == 1 and "RuntimeError: adapter bug" in rep["details"]["nl-reg"]
    assert rep["moved"] == 1  # the second source was still checked
    assert (cdir / ".last-check").is_file()


def test_validation_problem_exits_2_before_any_request(project: Path):
    cdir, _ = setup(project)
    srcs = sources.load(cdir); srcs[0].url = "http://reg.test/sitemap.xml"; sources.save(cdir, srcs)
    opener = FakeOpener({})
    factory = lambda source: http.Http(user_agent="t", delay_seconds=0, sleep=lambda s: None, opener=opener)
    rep = check.run(cdir, ids=None, today="2026-09-20", client_factory=factory)
    assert rep["exit"] == 2 and "https" in rep["details"]["nl-reg"] and opener.requests == []
    assert pending.list_open(cdir) == [] and not (cdir / ".last-check").exists()


def test_named_unconfirmed_source_is_refused(project: Path):
    cdir, _ = setup(project)
    srcs = sources.load(cdir); srcs[0].status = "proposed"; sources.save(cdir, srcs)
    opener = FakeOpener({})
    factory = lambda source: http.Http(user_agent="t", delay_seconds=0, sleep=lambda s: None, opener=opener)
    rep = check.run(cdir, ids=["nl-reg"], today="2026-09-20", client_factory=factory)
    assert rep["exit"] == 2 and "required confirmation missing" in rep["details"]["nl-reg"] and opener.requests == []
