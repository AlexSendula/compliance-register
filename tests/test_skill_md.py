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
