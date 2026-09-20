from pathlib import Path

from compliance_register import paths, sources
from compliance_register.mirror import http
from compliance_register.mirror.adapters import feed
from tests.fakehttp import FakeOpener

FIX = Path(__file__).parent / "fixtures"
HTML = {"Content-Type": "text/html"}


def src():
    return sources.Source.from_dict({
        "id": "nl-reg-feed", "jurisdiction": "NL", "kind": "regulator", "url": "https://reg.test/feed.xml",
        "tier": "feed", "licence": {"redistribute": True, "attribution": "reg"}, "status": "confirmed", "delay_seconds": 0,
    })


def client(extra=None):
    routes = {
        "https://reg.test/robots.txt": (404, {}, ""),
        "https://reg.test/feed.xml": (200, {"Content-Type": "application/rss+xml"}, FIX.joinpath("feed.xml").read_text()),
        "https://reg.test/n/1": (200, HTML, "<html><body><h1>Cookies</h1></body></html>"),
        "https://reg.test/n/2": (200, HTML, "<html><body><h1>Report</h1></body></html>"),
    }
    routes.update(extra or {})
    return http.Http(user_agent="t", delay_seconds=0, sleep=lambda s: None, opener=FakeOpener(routes))


def test_check_then_fetch_then_fresh(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    r = feed.check(src(), client(), today="2026-09-20", cdir=cdir)
    assert r.status == "moved" and sorted(r.changed) == ["n1", "n2"]
    f = feed.fetch(src(), client(), cdir, today="2026-09-20")
    assert len(f.written) == 2
    assert feed.check(src(), client(), today="2026-09-21", cdir=cdir).status == "fresh"


def test_feed_with_dtd_is_unreachable(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    bomb = '<?xml version="1.0"?><!DOCTYPE rss [<!ENTITY a "aaaa">]><rss><channel><item><guid>&a;</guid><link>https://reg.test/n/1</link></item></channel></rss>'
    c = client({"https://reg.test/feed.xml": (200, {"Content-Type": "application/rss+xml"}, bomb)})
    r = feed.check(src(), c, today="2026-09-20", cdir=cdir)
    assert r.status == "unreachable" and "DTD" in r.detail


def test_fetch_listing_failure_is_refused_not_raised(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    c = client({"https://reg.test/feed.xml": (503, {}, "")})
    f = feed.fetch(src(), c, cdir, today="2026-09-20")
    assert f.written == [] and f.refused and "503" in f.refused[0]
