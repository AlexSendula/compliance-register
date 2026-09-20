from pathlib import Path

from compliance_register import paths, sources
from compliance_register.mirror import http
from compliance_register.mirror.adapters import bwb
from tests.fakehttp import FakeOpener

FIX = Path(__file__).parent / "fixtures"
MANIFEST_URL = "https://repository.officiele-overheidspublicaties.nl/bwb/BWBR0009950/manifest.xml"


def src(last_version=None):
    return sources.Source.from_dict({
        "id": "nl-bwb-BWBR0009950", "jurisdiction": "NL", "kind": "legislation",
        "url": "https://wetten.overheid.nl/BWBR0009950", "tier": "api", "adapter": "bwb",
        "config": {"bwb_id": "BWBR0009950"}, "robots": "allowlist",
        "allowed_hosts": ["repository.officiele-overheidspublicaties.nl", "wetten.overheid.nl"],
        "licence": {"redistribute": True, "attribution": "Overheid.nl, CC0"}, "status": "confirmed",
        "delay_seconds": 0, "last_version": last_version,
    })


def client(xml_body):
    latest_xml_url = bwb.latest_item(FIX.joinpath("bwb-manifest.xml").read_bytes())["url"]
    return http.Http(user_agent="t", delay_seconds=0, sleep=lambda s: None, robots_allowlist=True, opener=FakeOpener({
        MANIFEST_URL: (200, {"Content-Type": "application/xml"}, FIX.joinpath("bwb-manifest.xml").read_bytes()),
        latest_xml_url: (200, {"Content-Type": "application/xml"}, xml_body),
    }))


TOESTAND = b"""<?xml version="1.0"?><wetgeving><wet-besluit><wettekst>
<artikel><kop><label>Artikel</label><nr>1.1</nr></kop><al>Eerste lid.</al></artikel>
<artikel><kop><label>Artikel</label><nr>1.2</nr></kop><al>Tweede.</al></artikel>
</wettekst></wet-besluit></wetgeving>"""


def test_check_and_fetch(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    latest = bwb.latest_item(FIX.joinpath("bwb-manifest.xml").read_bytes())
    r = bwb.check(src(), client(TOESTAND), today="2026-09-20", cdir=cdir)
    assert r.status == "moved" and r.version == latest["hashcode"]
    f = bwb.fetch(src(), client(TOESTAND), cdir, today="2026-09-20")
    assert f.version == latest["hashcode"] and len(f.written) == 2
    assert any(w.endswith("artikel_1.1.md") for w in f.written)
    assert bwb.check(src(last_version=latest["hashcode"]), client(TOESTAND), today="2026-09-20", cdir=cdir).status == "fresh"
