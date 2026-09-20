import json
from pathlib import Path
import pytest

from compliance_register import paths, sources

EURLEX = {
    "id": "eu-eurlex-32016R0679", "jurisdiction": "EU", "kind": "legislation",
    "url": "https://eur-lex.europa.eu/eli/reg/2016/679/oj", "covers": "GDPR",
    "tier": "api", "adapter": "eurlex", "config": {"celex": "32016R0679", "language": "EN"},
    "change_signal": "consolidated CELEX suffix",
    "licence": {"name": "CC-BY-4.0", "redistribute": True, "attribution": "© European Union, 1998-2026, https://eur-lex.europa.eu/"},
    "allowed_hosts": ["eur-lex.europa.eu", "publications.europa.eu"],
    "headers": {"user_agent": "default"}, "delay_seconds": 10, "status": "confirmed",
    "evidence": ["https://eur-lex.europa.eu/content/legal-notice/legal-notice.html"],
}


def test_roundtrip(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    (cdir / "sources.json").write_text(json.dumps({"schema": 1, "sources": [EURLEX]}))
    srcs = sources.load(cdir)
    assert srcs[0].id == "eu-eurlex-32016R0679" and srcs[0].adapter == "eurlex"
    assert srcs[0].last_version is None
    srcs[0].last_version = "02016R0679-20160504"
    sources.save(cdir, srcs)
    again = sources.load(cdir)
    assert again[0].last_version == "02016R0679-20160504"


def test_validate_rules():
    bad = dict(EURLEX, tier="api", adapter=None, licence={"redistribute": "yes"})
    problems = sources.validate(sources.Source.from_dict(bad))
    assert any("adapter" in p for p in problems)
    assert any("redistribute" in p for p in problems)


def test_no_robots_field_or_posture():
    s = sources.Source.from_dict(dict(EURLEX, robots="ignore"))
    assert "robots" not in s.to_dict() and not hasattr(sources, "ROBOTS")
    assert sources.validate(s) == []


def test_default_adapter_from_tier():
    s = sources.Source.from_dict(dict(EURLEX, tier="page-hash", adapter=None, config={"urls": ["https://x/y"]}))
    assert s.adapter == "pagehash"


def test_allowed_hosts_defaults_to_url_host():
    d = dict(EURLEX); del d["allowed_hosts"]
    assert sources.Source.from_dict(d).allowed_hosts == ["eur-lex.europa.eu"]


def test_get_unknown(project: Path):
    with pytest.raises(KeyError):
        sources.get([], "nope")


def test_api_tier_adapter_is_eurlex_only():
    from compliance_register.mirror import adapters
    for name in ("eurlex", "sitemap", "feed", "pagehash"):
        adapters.get(name)
    with pytest.raises(KeyError):
        adapters.get("nl-statute")
    msg = " ".join(sources.validate(sources.Source.from_dict(dict(EURLEX, adapter=None))))
    assert "(eurlex)" in msg


@pytest.mark.parametrize("host", ["localhost", "127.0.0.1", "::1", "10.0.0.5", "192.168.1.1", "169.254.169.254", "0.0.0.0", "fe80::1"])
def test_validate_refuses_private_hosts(host):
    s = sources.Source.from_dict(dict(EURLEX, allowed_hosts=["eur-lex.europa.eu", host]))
    assert any(host in p and "allowed_hosts" in p for p in sources.validate(s))


def test_validate_allows_public_ip_and_names():
    s = sources.Source.from_dict(dict(EURLEX, allowed_hosts=["eur-lex.europa.eu", "93.184.216.34"]))
    assert sources.validate(s) == []


def test_validate_requires_https():
    s = sources.Source.from_dict(dict(EURLEX, url="http://eur-lex.europa.eu/eli/reg/2016/679/oj"))
    assert any("https" in p for p in sources.validate(s))


def test_validate_eurlex_celex_and_language_shape():
    ok = sources.Source.from_dict(EURLEX)
    assert sources.validate(ok) == []
    for celex in ("../x", "02011L0083-20220528", "3201L0083", "32011l0083", ""):
        s = sources.Source.from_dict(dict(EURLEX, config={"celex": celex, "language": "EN"}))
        assert any("celex" in p for p in sources.validate(s)), celex
    s = sources.Source.from_dict(dict(EURLEX, config={"celex": "32011L0083", "language": "XX"}))
    assert any("language" in p for p in sources.validate(s))
    s = sources.Source.from_dict(dict(EURLEX, config={"celex": "32011L0083"}))
    assert sources.validate(s) == []
    s = sources.Source.from_dict(dict(EURLEX, config={}))
    assert any("celex" in p for p in sources.validate(s))


def test_allowed_hosts_string_is_wrapped_and_bad_shapes_refused():
    s = sources.Source.from_dict(dict(EURLEX, allowed_hosts="eur-lex.europa.eu"))
    assert s.allowed_hosts == ["eur-lex.europa.eu"] and sources.validate(s) == []
    for bad in ({"a": 1}, ["eur-lex.europa.eu", 3], [""], 7):
        s = sources.Source.from_dict(EURLEX); s.allowed_hosts = bad
        assert any("allowed_hosts must be a list" in p for p in sources.validate(s)), bad


def test_validate_refuses_unknown_adapter():
    s = sources.Source.from_dict(dict(EURLEX, adapter="bwb"))
    assert any("adapter" in p and "bwb" in p for p in sources.validate(s))
    for name in ("eurlex", "sitemap", "feed", "pagehash"):
        assert not any("unknown adapter" in p for p in sources.validate(sources.Source.from_dict(dict(EURLEX, adapter=name))))
