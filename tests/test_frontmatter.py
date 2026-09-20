from pathlib import Path
import pytest

from compliance_register import frontmatter as fm

DOC = """---
id: GDPR
status: binds
sources:
  - id: eu-eurlex-32016R0679
    version: 02016R0679-20160504
applies:
  cite: Art. 3(1)
  triggered_by:
    - establishment: NL
---

## Why this applies to you
Because.
"""


def test_loads_roundtrip():
    meta, body = fm.loads(DOC)
    assert meta["id"] == "GDPR"
    assert meta["sources"][0]["version"] == "02016R0679-20160504"
    assert meta["applies"]["triggered_by"][0] == {"establishment": "NL"}
    assert body.startswith("## Why this applies to you")
    again, body2 = fm.loads(fm.dump(meta, body))
    assert again == meta and body2 == body


def test_loads_without_frontmatter():
    meta, body = fm.loads("just text\n")
    assert meta == {} and body == "just text\n"


def test_loads_rejects_unterminated():
    with pytest.raises(fm.FrontmatterError):
        fm.loads("---\nid: X\nno end\n")


def test_save_is_atomic(tmp_path: Path):
    target = tmp_path / "r.md"
    fm.save(target, {"id": "X"}, "body\n")
    assert target.read_text().startswith("---\nid: X\n---\n")
    assert not list(tmp_path.glob("*.tmp"))


def test_dump_keeps_key_order():
    text = fm.dump({"b": 1, "a": 2}, "")
    assert text.index("b: 1") < text.index("a: 2")


def test_loads_normalises_dates():
    import json
    meta, _ = fm.loads("---\nconfirmed_at: 2026-09-20\nsources:\n  - retrieved: 2026-09-20T10:00:00\n---\n")
    assert meta["confirmed_at"] == "2026-09-20"
    assert meta["sources"][0]["retrieved"] == "2026-09-20T10:00:00"
    json.dumps(meta)
