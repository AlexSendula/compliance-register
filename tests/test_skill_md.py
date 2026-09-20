import json
import re
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
