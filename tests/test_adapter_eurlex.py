from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from compliance_register import frontmatter as fm, paths, sources
from compliance_register.mirror import http, store
from compliance_register.mirror.adapters import eurlex
from tests.fakehttp import FakeOpener

FIX = Path(__file__).parent / "fixtures"
HTML = {"Content-Type": "text/html; charset=UTF-8"}


def src(last_version=None):
    return sources.Source.from_dict({
        "id": "eu-eurlex-32011L0083", "jurisdiction": "EU", "kind": "legislation",
        "url": "https://eur-lex.europa.eu/eli/dir/2011/83/oj", "tier": "api", "adapter": "eurlex",
        "config": {"celex": "32011L0083", "language": "EN"},
        "licence": {"redistribute": True, "attribution": "© European Union"},
        "allowed_hosts": ["eur-lex.europa.eu", "publications.europa.eu"], "status": "confirmed",
        "delay_seconds": 0, "last_version": last_version,
    })


def sparql_route(request):
    q = parse_qs(urlsplit(request.full_url).query)
    assert "xsd:string" in q["query"][0]
    return (200, {"Content-Type": "text/csv"}, FIX.joinpath("sparql-resolve.csv").read_text())


def client(consolidated_html=None):
    return http.Http(user_agent="t", delay_seconds=0, sleep=lambda s: None, opener=FakeOpener({
        "http://publications.europa.eu/robots.txt": (404, {}, ""),
        "https://eur-lex.europa.eu/robots.txt": (404, {}, ""),
        eurlex.SPARQL + "*": sparql_route,  # prefix route: the query string is long
        "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02011L0083-20220528":
            (200, HTML, consolidated_html or FIX.joinpath("eurlex-consolidated.html").read_text()),
    }))


def test_resolve_applies_today_client_side():
    r = eurlex.resolve(client(), ["32011L0083", "32016R0679"], today="2026-09-20")
    assert r["32011L0083"] == {"current": "02011L0083-20220528", "current_date": "2022-05-28", "next": "02011L0083-20260927", "next_date": "2026-09-27"}
    assert r["32016R0679"]["current"] == "02016R0679-20160504" and r["32016R0679"]["next"] is None


def test_check_moved_then_fresh(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    r = eurlex.check(src(), client(), today="2026-09-20", cdir=cdir)
    assert r.status == "moved" and r.version == "02011L0083-20220528" and r.next_version == "02011L0083-20260927"
    r2 = eurlex.check(src(last_version="02011L0083-20220528"), client(), today="2026-09-20", cdir=cdir)
    assert r2.status == "fresh"


def test_header_only_csv_is_unreachable(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    c = client()
    c.opener = lambda req, t: (200, {"Content-Type": "text/csv"}, __import__("io").BytesIO(b'"baseCelex","consolCelex","consolDate"\n'))
    assert eurlex.check(src(), c, today="2026-09-20", cdir=cdir).status == "unreachable"


def test_fetch_writes_articles_and_sets_version(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    f = eurlex.fetch(src(), client(), cdir, today="2026-09-20")
    assert f.refused == [] and f.version == "02011L0083-20220528"
    assert any(w.endswith("/02011L0083-20220528/art_1.md") for w in f.written)
    meta, body = fm.load(Path(f.written[0]))
    assert meta["consolidated_celex"] == "02011L0083-20220528" and meta["article"] == 1
    assert body.lstrip().startswith("> This text is meant purely as a documentation tool")


def test_fetch_refuses_site_chrome(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    f = eurlex.fetch(src(), client(FIX.joinpath("eurlex-chrome.html").read_text()), cdir, today="2026-09-20")
    assert f.written == [] and f.refused and f.version is None
    assert "G2" in f.refused[0] or "G3" in f.refused[0]


def test_chunk_headings_and_whitespace_on_real_markup():
    arts = eurlex.chunk(FIX.joinpath("eurlex-consolidated.html").read_text())
    assert sorted(arts) == [1, 2, 3]
    assert arts[1].startswith("## Article 1\n\n### Subject matter\n\nThe purpose of this Directive")
    assert "\n \n" not in arts[3] and "\n\n\n" not in arts[3]


def test_check_with_missing_config_is_unreachable_not_raised(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    s = src(); s.config = {}
    r = eurlex.check(s, client(), today="2026-09-20", cdir=cdir)
    assert r.status == "unreachable" and "celex" in r.detail
