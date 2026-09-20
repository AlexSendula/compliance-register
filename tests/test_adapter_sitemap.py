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
