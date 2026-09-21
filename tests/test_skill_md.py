import json
import re
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, "SKILL.md must start with a frontmatter block"
    return yaml.safe_load(m.group(1))


def test_skill_md_frontmatter_matches_spec():
    text = (ROOT / "SKILL.md").read_text()
    fm = frontmatter(text)
    assert fm["name"] == ROOT.name == "compliance-register"
    assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", fm["name"]) and len(fm["name"]) <= 64
    assert 1 <= len(fm["description"]) <= 1024
    assert "TRIGGER when" in fm["description"]
    assert fm["license"] == "MIT"
    assert len(text.splitlines()) < 500


def test_skill_md_never_says_compliant_as_a_verdict():
    text = (ROOT / "SKILL.md").read_text().lower()
    assert "you are compliant" not in text and "is compliant" not in text


def test_plugin_and_marketplace_agree():
    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    assert plugin["name"] == "compliance-register" and plugin["skills"] == ["."]
    assert market["plugins"][0]["name"] == plugin["name"] and market["plugins"][0]["source"] == "."


def test_every_reference_linked_from_skill_md_exists():
    text = (ROOT / "SKILL.md").read_text()
    for rel in re.findall(r"references/[A-Za-z0-9_.-]+\.md", text):
        assert (ROOT / rel).is_file(), rel


def test_skill_md_states_eurlex_v1_narrowings():
    text = (ROOT / "SKILL.md").read_text()
    mirror = text.split("## The mirror", 1)[1].split("\n## ", 1)[0]
    assert "never been consolidated" in mirror and "cited by URL" in mirror
    assert "not pre-checked" in mirror and "G1" in mirror and "G2" in mirror
    assert not (ROOT / "references" / "eurlex-language.sparql").exists()


# --- pass 5: shipped references and docs carry the method, never the law ---

SHIPPED = [ROOT / "SKILL.md", ROOT / "README.md", *sorted((ROOT / "references").glob("*.md"))]
_CELEX = re.compile(r"\d{5}[A-Z]{1,2}\d{4}")
_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_ARTICLE = re.compile(r"\bArt\. ?\d")
_URL = re.compile(r"https?://")


def test_regime_template_ships_placeholders_not_law():
    text = (ROOT / "references" / "regime-template.md").read_text()
    assert "id: EXAMPLE" in text and "<verbatim scope clause>" in text and "<Art. N(M)>" in text
    assert "<jurisdiction>-<short-name>" in text
    assert "EXAMPLE-001" in text
    assert not _CELEX.search(text) and not _ISO_DATE.search(text)
    assert not re.search(r"\bArt\. \d", text)
    assert "## Obligations" in text and "Rules:" in text



def test_method_discover_sources_names_every_source_field():
    from compliance_register import sources
    text = (ROOT / "references" / "method-discover-sources.md").read_text()
    agent_written = [f for f in sources.Source.__dataclass_fields__ if not f.startswith(("last_", "next_"))]
    for name in agent_written:
        assert f"`{name}`" in text, name
    for value in sources.KINDS + sources.TIERS + sources.STATUSES:
        assert f"`{value}`" in text, value
    for key in ("celex", "language", "urls", "include", "user_agent", "default", "neutral", "browser"):
        assert f"`{key}`" in text, key
    assert "robots.txt" in text and "always honoured" in text


def test_method_profile_makes_rescan_the_baseline_and_bars_repo_name_as_evidence():
    text = (ROOT / "references" / "method-profile.md").read_text()
    assert "--against HEAD~1" not in text
    assert "rescan" in text
    assert "any answer" in text and "indicia" in text


def _cli_commands() -> list[str]:
    from compliance_register.cli import build_parser

    def walk(parser, prefix=""):
        subs = getattr(parser, "_subparsers", None)
        if subs is None:
            return [prefix.strip()]
        out = []
        for action in subs._group_actions:
            for name, sub in action.choices.items():
                out.extend(walk(sub, f"{prefix} {name}"))
        return out

    return walk(build_parser())


def test_skill_md_commands_table_covers_the_whole_cli():
    text = (ROOT / "SKILL.md").read_text()
    section = text.split("## Commands", 1)[1].split("\n## ", 1)[0]
    for name in _cli_commands():
        assert f"`{name}" in section, name
    assert "not CLI commands" in section
    for rule in ("`check` →", "`fetch` →", "`rescan` →"):
        assert rule in section
    assert "profile diff --against HEAD~1" not in text


def test_readme_matches_the_cli_and_lists_engine_files():
    text = (ROOT / "README.md").read_text()
    for name in _cli_commands():
        assert f"compliance-register {name}" in text, name
    for path in (".last-check", "profile.snapshot.json", "mirror/.private/", ".search-index.json", "MANIFEST.json"):
        assert path in text, path


def test_shipped_docs_carry_no_law_fact_or_source_address():
    """No CELEX, ISO date, article citation or URL outside the checklist's
    provenance lines. Trigger words in the SKILL.md description are names,
    not facts, and no pattern here matches them."""
    for path in SHIPPED:
        for n, line in enumerate(path.read_text().splitlines(), 1):
            if path.name == "dimensions-checklist.md" and "**Found in**" in line:
                continue
            for pat in (_CELEX, _ISO_DATE, _ARTICLE, _URL):
                assert not pat.search(line), f"{path.name}:{n}: {line.strip()}"


def test_skill_md_documents_pending_kinds_severities_and_the_api_endpoint_rule():
    from compliance_register import pending
    text = (ROOT / "SKILL.md").read_text()
    section = text.split("## Pending entries", 1)[1].split("\n## ", 1)[0]
    for kind in pending.KINDS:
        assert f"`{kind}`" in section, kind
    for sev in pending.SEVERITIES:
        assert f"`{sev}`" in section, sev
    assert "resolve" in section
    mirror = text.split("## The mirror", 1)[1].split("\n## ", 1)[0]
    assert "carries the endpoint" in mirror and "never ship" in mirror and "sources.json" in mirror
    regimes_method = (ROOT / "references" / "method-discover-regimes.md").read_text()
    assert "profile diff" not in regimes_method and "rescan" in regimes_method


def test_version_is_identical_in_all_four_places():
    from compliance_register import __version__
    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    fm = frontmatter((ROOT / "SKILL.md").read_text())
    assert {__version__, plugin["version"], pyproject["project"]["version"], fm["metadata"]["version"]} == {__version__}


def test_sparql_template_has_values_placeholder_and_no_instrument_celex():
    from compliance_register.mirror.adapters import eurlex
    text = (ROOT / "references" / "eurlex-resolve.sparql").read_text()
    assert "{{VALUES}}" in text and not _CELEX.search(text)
    query = eurlex._query(["32016R0679", "32011L0083"])
    assert "{{VALUES}}" not in query and '"32016R0679"^^xsd:string "32011L0083"^^xsd:string' in query


def test_checklist_slugs_match_profile_dimensions_in_order():
    from compliance_register import profile
    text = (ROOT / "references" / "dimensions-checklist.md").read_text()
    section = text.split("## Slugs", 1)[1].split("\n## ", 1)[0]
    assert re.findall(r"`([a-z_]+)`", section) == list(profile.DIMENSIONS) and len(profile.DIMENSIONS) == 15


def test_every_checklist_dimension_carries_the_five_fixed_lines():
    text = (ROOT / "references" / "dimensions-checklist.md").read_text()
    dims = re.split(r"\n## \d+\. ", text)[1:]
    assert len(dims) == 15
    for d in dims:
        labels = re.findall(r"^- \*\*(.+?)\*\*", d, re.M)
        assert labels == ["Ask", "Decides", "Code may propose", "Trap", "Found in"], d.splitlines()[0]
