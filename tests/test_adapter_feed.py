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


def test_feed_with_no_usable_entries_is_unreachable_not_fresh(project: Path):
    """A listing that yields nothing is 'cannot tell', never 'no change' (P4)."""
    cdir = paths.compliance_dir(project); cdir.mkdir()
    empty = '<rss version="2.0"><channel><title>x</title><item><title>no id, no link</title></item></channel></rss>'
    r = feed.check(src(), client({"https://reg.test/feed.xml": (200, {"Content-Type": "application/rss+xml"}, empty)}), today="2026-09-20", cdir=cdir)
    assert r.status == "unreachable" and "no entries" in r.detail


ATOM = ('<feed xmlns="http://www.w3.org/2005/Atom"><title>Reg</title>'
        '<entry><id>urn:reg:1</id><title>Cookies</title><updated>2026-09-01T10:00:00Z</updated>'
        '<link rel="self" href="https://reg.test/atom/1"/><link rel="alternate" href="https://reg.test/n/1"/></entry>'
        '</feed>')


def test_an_atom_feeds_entries_are_normalised_with_the_alternate_link_and_id():
    c = client({"https://reg.test/feed.xml": (200, {"Content-Type": "application/atom+xml"}, ATOM)})
    assert feed._entries(src(), c) == [{"id": "urn:reg:1", "title": "Cookies", "published": "2026-09-01T10:00:00Z", "link": "https://reg.test/n/1"}]


def test_an_entry_without_a_guid_falls_back_to_its_link_as_id():
    rss = '<rss version="2.0"><channel><item><title>t</title><link>https://reg.test/n/1</link></item></channel></rss>'
    c = client({"https://reg.test/feed.xml": (200, {"Content-Type": "application/rss+xml"}, rss)})
    assert [e["id"] for e in feed._entries(src(), c)] == ["https://reg.test/n/1"]


def test_a_non_html_entry_page_is_refused_by_link_and_the_other_entries_are_still_written(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    c = client({"https://reg.test/n/1": (200, {"Content-Type": "application/pdf"}, b"%PDF-1.4")})
    f = feed.fetch(src(), c, cdir, today="2026-09-20")
    assert f.refused == ["https://reg.test/n/1"] and len(f.written) == 1
