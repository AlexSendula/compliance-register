from pathlib import Path

from compliance_register import paths, sources
from compliance_register.mirror import adapters, http, store
from compliance_register.mirror.adapters import sitemap
from tests.fakehttp import FakeOpener

FIX = Path(__file__).parent / "fixtures"
HTML = {"Content-Type": "text/html"}


def src():
    return sources.Source.from_dict({
        "id": "nl-reg", "jurisdiction": "NL", "kind": "regulator", "url": "https://reg.test/sitemap.xml",
        "tier": "sitemap", "config": {"include": ["https://reg.test/guidance/"]},
        "licence": {"redistribute": True, "attribution": "reg"}, "status": "confirmed",
        "allowed_hosts": ["reg.test"], "delay_seconds": 0,
    })


def client(extra=None):
    routes = {
        "https://reg.test/robots.txt": (404, {}, ""),
        "https://reg.test/sitemap.xml": (200, {"Content-Type": "application/xml"}, FIX.joinpath("sitemap.xml").read_text()),
        "https://reg.test/guidance/a": (200, HTML, "<html><title>A</title><body><h1>Guidance A</h1><p>alpha</p></body></html>"),
        "https://reg.test/guidance/b": (200, HTML, "<html><title>B</title><body><h1>Guidance B</h1><p>beta</p></body></html>"),
    }
    routes.update(extra or {})
    return http.Http(user_agent="t", delay_seconds=0, opener=FakeOpener(routes), sleep=lambda s: None)


def test_registry():
    assert adapters.get("sitemap") is sitemap


def test_check_on_empty_manifest_is_moved(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    r = sitemap.check(src(), client(), today="2026-09-20", cdir=cdir)
    assert r.status == "moved" and sorted(r.changed) == ["https://reg.test/guidance/a", "https://reg.test/guidance/b"]


def test_fetch_writes_and_check_becomes_fresh(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    f = sitemap.fetch(src(), client(), cdir, today="2026-09-20")
    assert len(f.written) == 2 and f.refused == []
    man = store.load_manifest(cdir, src())
    assert man["https://reg.test/guidance/a"]["lastmod"] == "2026-01-10"
    assert sitemap.check(src(), client(), today="2026-09-20", cdir=cdir).status == "fresh"


def test_check_unreachable_when_sitemap_fails(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    c = client({"https://reg.test/sitemap.xml": (503, {}, "")})
    assert sitemap.check(src(), c, today="2026-09-20", cdir=cdir).status == "unreachable"


def test_fetch_refuses_non_html(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    c = client({"https://reg.test/guidance/a": (200, {"Content-Type": "application/pdf"}, b"%PDF-1.4")})
    f = sitemap.fetch(src(), c, cdir, today="2026-09-20")
    assert "https://reg.test/guidance/a" in f.refused and len(f.written) == 1


def test_sitemap_with_dtd_is_unreachable(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    bomb = '<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://reg.test/guidance/&a;</loc></url></urlset>'
    c = client({"https://reg.test/sitemap.xml": (200, {"Content-Type": "application/xml"}, bomb)})
    r = sitemap.check(src(), c, today="2026-09-20", cdir=cdir)
    assert r.status == "unreachable" and "DTD" in r.detail


def test_listing_is_capped_at_5mb(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    huge = '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "<!-- x -->" * 600_000 + "</urlset>"
    c = client({"https://reg.test/sitemap.xml": (200, {"Content-Type": "application/xml"}, huge)})
    assert sitemap.check(src(), c, today="2026-09-20", cdir=cdir).status == "unreachable"


def test_fetch_listing_failure_is_refused_and_manifest_still_saved(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    c = client({"https://reg.test/sitemap.xml": (503, {}, "")})
    f = sitemap.fetch(src(), c, cdir, today="2026-09-20")
    assert f.written == [] and f.refused and "503" in f.refused[0]
    assert (store.source_dir(cdir, src()) / store.MANIFEST).is_file()


def test_fan_out_is_capped_and_the_cap_is_reported(project: Path, monkeypatch):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    monkeypatch.setattr(sitemap, "MAX_PAGES", 5)
    monkeypatch.setattr(sitemap, "MAX_CHILDREN", 3)
    ns = 'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'
    index = f"<sitemapindex {ns}>" + "".join(f"<sitemap><loc>https://reg.test/sm{i}.xml</loc></sitemap>" for i in range(10)) + "</sitemapindex>"
    child = lambda i: (200, {"Content-Type": "application/xml"}, f"<urlset {ns}>" + "".join(f"<url><loc>https://reg.test/guidance/{i}-{j}</loc></url>" for j in range(4)) + "</urlset>")
    routes = {"https://reg.test/sitemap.xml": (200, {"Content-Type": "application/xml"}, index)}
    routes.update({f"https://reg.test/sm{i}.xml": child(i) for i in range(10)})
    c = client(routes)
    r = sitemap.check(src(), c, today="2026-09-20", cdir=cdir)
    assert r.status == "moved" and len(r.changed) == 5 and "capped" in r.detail and "config.include" in r.detail
    assert sum(1 for q in c.opener.requests if q.full_url.startswith("https://reg.test/sm")) == 2  # 3rd child never needed: 5 pages reached
    assert sitemap.MAX_PAGES == 5 and sitemap.MAX_CHILDREN == 3


def test_html_served_as_a_listing_is_named_as_such(project: Path):
    """A bot-challenge or error page comes back 200 text/html with <!DOCTYPE html>;
    'DTD in XML listing' sent the operator hunting for an entity that was never there."""
    cdir = paths.compliance_dir(project); cdir.mkdir()
    c = client({"https://reg.test/sitemap.xml": (200, {"Content-Type": "text/html"}, "<!DOCTYPE html><html><body>Checking your browser</body></html>")})
    r = sitemap.check(src(), c, today="2026-09-20", cdir=cdir)
    assert r.status == "unreachable" and "HTML page, not XML" in r.detail


def test_check_downloads_no_page_bodies_on_the_sitemap_tier(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    c = client()
    assert sitemap.check(src(), c, today="2026-09-20", cdir=cdir).status == "moved"
    assert {q.full_url for q in c.opener.requests} == {"https://reg.test/robots.txt", "https://reg.test/sitemap.xml"}


def test_force_refetches_pages_whose_lastmod_is_unchanged(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    sitemap.fetch(src(), client(), cdir, today="2026-09-20")
    again = sitemap.fetch(src(), client(), cdir, today="2026-09-21")
    forced = sitemap.fetch(src(), client(), cdir, today="2026-09-21", force=True)
    assert (again.skipped, len(again.written)) == (2, 0) and (forced.skipped, len(forced.written)) == (0, 2)
