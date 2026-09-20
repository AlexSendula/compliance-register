import json
from pathlib import Path
import pytest

from compliance_register import paths, sources

EURLEX = {
    "id": "eu-eurlex-32016R0679", "jurisdiction": "EU", "kind": "legislation",
    "url": "https://eur-lex.europa.eu/eli/reg/2016/679/oj", "covers": "GDPR",
    "tier": "api", "adapter": "eurlex", "config": {"celex": "32016R0679", "language": "EN"},
    "change_signal": "consolidated CELEX suffix",
    "licence": {"redistribute": True, "attribution": "© European Union, 1998-2026, https://eur-lex.europa.eu/"},
    "robots": "honour", "allowed_hosts": ["eur-lex.europa.eu", "publications.europa.eu"],
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
    bad = dict(EURLEX, tier="api", adapter=None, licence={"redistribute": "yes"}, robots="ignore")
    problems = sources.validate(sources.Source.from_dict(bad))
    assert any("adapter" in p for p in problems)
    assert any("redistribute" in p for p in problems)
    assert any("robots" in p for p in problems)


def test_default_adapter_from_tier():
    s = sources.Source.from_dict(dict(EURLEX, tier="page-hash", adapter=None, config={"urls": ["https://x/y"]}))
    assert s.adapter == "pagehash"


def test_allowed_hosts_defaults_to_url_host():
    d = dict(EURLEX); del d["allowed_hosts"]
    assert sources.Source.from_dict(d).allowed_hosts == ["eur-lex.europa.eu"]


def test_get_unknown(project: Path):
    with pytest.raises(KeyError):
        sources.get([], "nope")
