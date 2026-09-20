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
        "https://publications.europa.eu/robots.txt": (404, {}, ""),
        "https://eur-lex.europa.eu/robots.txt": (404, {}, ""),
        eurlex.SPARQL + "*": sparql_route,  # prefix route: the query string is long
        "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02011L0083-20220528":
            (200, HTML, consolidated_html or FIX.joinpath("eurlex-consolidated.html").read_text()),
    }))


def test_sparql_endpoint_is_https():
    c = client()
    eurlex.resolve(c, ["32011L0083"], today="2026-09-20")
    assert eurlex.SPARQL.startswith("https://publications.europa.eu/")
    assert all(r.full_url.startswith("https://") for r in c.opener.requests)


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
    banner = body.lstrip().splitlines()[0]
    assert "converted from HTML to Markdown and split per article by compliance-register" in banner  # CC-BY 4.0 §3(a)(1)(B): say it was modified


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


def csv_client(csv_text):
    c = client()
    c.opener = FakeOpener({"https://publications.europa.eu/robots.txt": (404, {}, ""),
                           eurlex.SPARQL + "*": (200, {"Content-Type": "text/csv"}, csv_text)})
    return c


def test_resolve_drops_malformed_rows_and_never_splits_them():
    bad = ('"baseCelex","consolCelex","consolDate"\n'
           '"32011L0083","../../etc/passwd","2024-01-01"\n'         # no dash-date suffix, path-shaped
           '"32011L0083","02011L0083-20220528","28.05.2022"\n'       # date not ISO
           '"32011L0083","02011L0083-20180701","2018-07-01"\n')
    r = eurlex.resolve(csv_client(bad), ["32011L0083"], today="2026-09-20")
    assert r["32011L0083"]["current"] == "02011L0083-20180701" and r["32011L0083"]["next"] is None


def test_resolve_all_rows_malformed_is_unreachable():
    bad = '"baseCelex","consolCelex","consolDate"\n"32011L0083","garbage","2024-01-01"\n'
    import pytest
    with pytest.raises(http.HttpUnreachable):
        eurlex.resolve(csv_client(bad), ["32011L0083"], today="2026-09-20")


def test_zero_rows_for_this_celex_is_unreachable_even_without_last_version(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    only_gdpr = '"baseCelex","consolCelex","consolDate"\n"32016R0679","02016R0679-20160504","2016-05-04"\n'
    r = eurlex.check(src(), csv_client(only_gdpr), today="2026-09-20", cdir=cdir)
    assert r.status == "unreachable" and r.version is None and "no consolidation" in r.detail


def src2():
    s = src(); s.id = "eu-eurlex-32016R0679"; s.config = {"celex": "32016R0679", "language": "EN"}
    s.url = "https://eur-lex.europa.eu/eli/reg/2016/679/oj"
    return s


def test_prefetch_resolves_whole_basket_in_one_request(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    c = client()
    resolved = eurlex.prefetch([src(), src2()], c, today="2026-09-20")
    sparql = [r for r in c.opener.requests if r.full_url.startswith(eurlex.SPARQL)]
    assert len(sparql) == 1 and set(resolved) == {"32011L0083", "32016R0679"}
    assert eurlex.check(src(), c, today="2026-09-20", cdir=cdir, resolved=resolved).status == "moved"
    assert eurlex.check(src2(), c, today="2026-09-20", cdir=cdir, resolved=resolved).status == "moved"
    f = eurlex.fetch(src(), c, cdir, today="2026-09-20", resolved=resolved)
    assert f.version == "02011L0083-20220528"
    assert len([r for r in c.opener.requests if r.full_url.startswith(eurlex.SPARQL)]) == 1


def test_prefetch_failure_is_unreachable_per_source_not_raised(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    c = csv_client('"baseCelex","consolCelex","consolDate"\n')
    resolved = eurlex.prefetch([src(), src2()], c, today="2026-09-20")
    r = eurlex.check(src(), c, today="2026-09-20", cdir=cdir, resolved=resolved)
    assert r.status == "unreachable" and "no rows" in r.detail
    assert eurlex.fetch(src2(), c, cdir, today="2026-09-20", resolved=resolved).refused[0].startswith("resolve:")


def test_check_run_issues_one_sparql_query_for_all_eurlex_sources(project: Path):
    from compliance_register import check, fetch
    cdir = paths.compliance_dir(project); cdir.mkdir()
    sources.save(cdir, [src(), src2()])
    c = client()
    rep = check.run(cdir, ids=None, today="2026-09-20", client_factory=lambda s: c)
    assert rep["moved"] == 2
    assert len([r for r in c.opener.requests if r.full_url.startswith(eurlex.SPARQL)]) == 1
    rep = fetch.run(cdir, ids=None, force=False, today="2026-09-20", client_factory=lambda s: c)
    assert rep["written"] == 3  # 32016R0679's page has no fixture route → refused, no traceback
    assert len([r for r in c.opener.requests if r.full_url.startswith(eurlex.SPARQL)]) == 2


def test_g4_needs_the_consolidated_reference_line_not_the_title(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    real = FIX.joinpath("eurlex-consolidated.html").read_text()
    assert "<title>Consolidated TEXT: 32011L0083 — EN — 28.05.2022</title>" in real
    assert '<p class="reference">02011L0083 — EN — 28.05.2022' in real
    assert eurlex.fetch(src(), client(real), cdir, today="2026-09-20").refused == []
    title_only = real.replace('<p class="reference">02011L0083 — EN — 28.05.2022 — 002.001</p>', "")
    f = eurlex.fetch(src(), client(title_only), cdir, today="2026-09-20")
    assert f.written == [] and f.refused == ["G4: header does not match requested CELEX/language/date"]
    # a base CELEX glued to a leading digit is not the sector-0 form either
    glued = title_only.replace("32011L0083 — EN", "302011L0083 — EN")
    assert eurlex.fetch(src(), client(glued), cdir, today="2026-09-20").refused[0].startswith("G4")
