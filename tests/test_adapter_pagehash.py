from pathlib import Path

from compliance_register import paths, sources
from compliance_register.mirror import http, store
from compliance_register.mirror.adapters import pagehash
from tests.fakehttp import FakeOpener

HTML = {"Content-Type": "text/html"}


def src():
    return sources.Source.from_dict({
        "id": "psp-terms", "jurisdiction": "NL", "kind": "contract", "url": "https://psp.test/terms",
        "tier": "page-hash", "config": {"urls": ["https://psp.test/terms", "https://psp.test/dpa"]},
        "licence": {"redistribute": False, "attribution": None}, "status": "confirmed", "delay_seconds": 0,
    })


def client(terms="<p>v1</p>"):
    return http.Http(user_agent="t", delay_seconds=0, sleep=lambda s: None, opener=FakeOpener({
        "https://psp.test/robots.txt": (404, {}, ""),
        "https://psp.test/terms": (200, HTML, f"<html><body>{terms}</body></html>"),
        "https://psp.test/dpa": (200, HTML, "<html><body><p>dpa</p></body></html>"),
    }))


def test_fetch_then_fresh_then_moved(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    f = pagehash.fetch(src(), client(), cdir, today="2026-09-20")
    assert len(f.written) == 2 and all("/.private/" in w for w in f.written)
    assert pagehash.check(src(), client(), today="2026-09-21", cdir=cdir).status == "fresh"
    r = pagehash.check(src(), client("<p>v2 changed</p>"), today="2026-09-22", cdir=cdir)
    assert r.status == "moved" and r.changed == ["https://psp.test/terms"]
    assert "fetches" in r.detail
