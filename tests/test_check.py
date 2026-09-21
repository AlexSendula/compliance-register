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


def test_moved_entry_is_not_duplicated_while_open(project: Path):
    cdir, factory = setup(project)
    check.run(cdir, ids=None, today="2026-09-20", client_factory=factory)
    check.run(cdir, ids=None, today="2026-09-21", client_factory=factory)
    kinds = [e["kind"] for e in pending.list_open(cdir)]
    assert kinds.count("source-moved") == 1


def test_source_next_recorded_once_and_on_source(project: Path, monkeypatch):
    cdir, factory = setup(project)
    from compliance_register.mirror import adapters
    from compliance_register.mirror.adapters import sitemap
    monkeypatch.setattr(sitemap, "check", lambda *a, **k: adapters.CheckResult("fresh", "v1", "ok", [], "v2", "2026-12-01"))
    check.run(cdir, ids=None, today="2026-09-20", client_factory=factory)
    check.run(cdir, ids=None, today="2026-09-21", client_factory=factory)
    nxt = [e for e in pending.list_open(cdir) if e["kind"] == "source-next"]
    assert len(nxt) == 1 and nxt[0]["to"] == "v2"
    s = sources.load(cdir)[0]
    assert s.next_version == "v2" and "_next_seen" not in s.config


def test_date_passed_for_review_by_once(project: Path):
    cdir, factory = setup(project)
    write(cdir, dict(META, id="OLD", review_by="2026-09-01"))
    write(cdir, dict(META, id="FUTURE", review_by="2027-01-01"))
    write(cdir, dict(META, id="GONE", status="no-longer-applies", review_by="2026-09-01"))
    check.run(cdir, ids=None, today="2026-09-20", client_factory=factory)
    check.run(cdir, ids=None, today="2026-09-21", client_factory=factory)
    dp = [e for e in pending.list_open(cdir) if e["kind"] == "date-passed"]
    assert len(dp) == 1 and dp[0]["affects"] == ["OLD"] and dp[0]["severity"] == "major"


def test_date_passed_runs_even_with_nothing_to_check(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    sources.save(cdir, [])
    write(cdir, dict(META, id="OLD", review_by="2026-09-01"))
    rep = check.run(cdir, ids=None, today="2026-09-20")
    assert rep["exit"] == 2 and [e["kind"] for e in pending.list_open(cdir)] == ["date-passed"]


def test_affects_skips_ruled_out_and_no_longer_applies(project: Path):
    cdir, factory = setup(project)
    write(cdir, dict(META, id="RULED", status="ruled-out", sources=[{"id": "nl-reg", "version": None, "retrieved": "2026-01-01"}]))
    write(cdir, dict(META, id="GONE", status="no-longer-applies", sources=[{"id": "nl-reg", "version": None, "retrieved": "2026-01-01"}]))
    assert check._affects(cdir, "nl-reg") == ["COOKIES"]


def test_unreachable_source_exits_1(project: Path):
    cdir, good = setup(project)
    bad = lambda source: http.Http(user_agent="t", delay_seconds=0, sleep=lambda s: None, opener=FakeOpener({"https://reg.test/robots.txt": (404, {}, ""), "https://reg.test/sitemap.xml": (503, {}, "")}))
    assert check.run(cdir, ids=None, today="2026-09-20", client_factory=bad)["exit"] == 1
    assert check.run(cdir, ids=None, today="2026-09-20", client_factory=good)["exit"] == 0  # moved is still 0


def _eurlex_project(project: Path, routes: dict):
    from tests.test_adapter_eurlex import src
    cdir = paths.compliance_dir(project); cdir.mkdir()
    sources.save(cdir, [src()])
    opener = FakeOpener(routes)
    return cdir, lambda source: http.Http(user_agent="t", delay_seconds=0, sleep=lambda s: None, opener=opener)


def test_oversized_csv_field_in_resolve_is_unreachable_and_run_completes(project: Path):
    from compliance_register.mirror.adapters import eurlex
    from compliance_register import fetch
    csv_text = '"baseCelex","consolCelex","consolDate"\n"32011L0083","' + "x" * 200_000 + '","2022-05-28"\n'
    cdir, factory = _eurlex_project(project, {"https://publications.europa.eu/robots.txt": (404, {}, ""),
                                              eurlex.SPARQL + "*": (200, {"Content-Type": "text/csv"}, csv_text)})
    rep = check.run(cdir, ids=None, today="2026-09-20", client_factory=factory)
    assert rep["unreachable"] == 1 and "Error" in rep["details"]["eu-eurlex-32011L0083"]
    assert sources.load(cdir)[0].last_checked == "2026-09-20" and (cdir / ".last-check").is_file()
    rep = fetch.run(cdir, ids=None, force=False, today="2026-09-20", client_factory=factory)
    assert rep["exit"] == 1 and "Error" in str(rep["details"]["eu-eurlex-32011L0083"])


def test_robots_opener_raising_is_unreachable_and_run_completes(project: Path):
    """RFC 9309 §2.3.1.4: robots.txt we could not read means complete disallow —
    the source is unreachable, never fetched-anyway (P4, P8)."""
    from tests.test_adapter_eurlex import sparql_route
    from compliance_register.mirror.adapters import eurlex
    def boom(request):
        raise ValueError("Port could not be cast to integer value")
    cdir, factory = _eurlex_project(project, {"https://publications.europa.eu/robots.txt": boom, eurlex.SPARQL + "*": sparql_route})
    rep = check.run(cdir, ids=None, today="2026-09-20", client_factory=factory)
    assert rep["unreachable"] == 1 and rep["moved"] == 0 and "robots.txt" in rep["details"]["eu-eurlex-32011L0083"]
    assert sources.load(cdir)[0].last_checked == "2026-09-20" and (cdir / ".last-check").is_file()


def test_corrupt_profile_does_not_deny_the_check_report(project: Path):
    """A poisoned profile.md must not swallow the check report after every source was queried (P9)."""
    cdir, factory = setup(project)
    (cdir / "profile.md").write_text("---\nanswers: [\n", encoding="utf-8")
    rep = check.run(cdir, ids=None, today="2026-09-20", client_factory=factory)
    assert rep["moved"] == 1 and "unreadable" in rep["details"]["profile.md"]
    assert ("profile-stale", None) not in {(e["kind"], e["source"]) for e in pending.list_open(cdir)}
