# Copied verbatim from docs-mirror (~/.claude/skills/docs-mirror/docs_mirror/render.py, ADR-008).
# Do not edit here; the sink guard is shared by design.
"""Neutralising untrusted text at an output sink. One rule, in one place.

Almost nothing this tool prints was written by this tool. Vendor page bodies,
hrefs read back out of those bodies, and the paths recorded in MANIFEST.json
and registry.json all reach the operator's terminal — and a terminal is a state
machine, so an ESC in any of them repaints it, while U+202E reverses what the
operator reads. Both attacks are content, not URLs.

WHY THIS IS ITS OWN MODULE, and not a helper inside `urls.py` or a private
function in `cli.py`:

  * `urls.py` owns the *refusal* boundary for URLs headed out. The defect this
    module closes is precisely a sink with no boundary on it at all: a vendor's
    page BODY travels `sync_vendor` -> disk -> `chunk_markdown` -> the search cache
    -> `search`, and `normalize_url` never sees one byte of it, by
    construction. Putting the neutraliser next to the refuser invites the
    reasoning SEC-006 and SEC-033 each proved wrong in turn — "safe, because
    something upstream refused it". A sink is safe because of what it does.
  * `cli.py` would make it private to one caller, and the text it handles comes
    from three different producers. Out here it is exercised against codepoints
    directly, without capturing stdout, and a future non-CLI consumer of
    `search` results (an agent front end) gets the same guarantee.

It has no imports and no knowledge of URLs, paths or vendors. That is the
point: a sink guard that depended on anything could be defeated by changing
that thing.
"""
from __future__ import annotations

# repr's mnemonics for the three whitespace controls, because `\n` reads and
# `\x0a` does not. Everything else takes repr's numeric form.
_MNEMONICS = {"\t": "\\t", "\n": "\\n", "\r": "\\r"}


def _escape(ch: str) -> str:
    codepoint = ord(ch)
    if ch in _MNEMONICS:
        return _MNEMONICS[ch]
    if codepoint <= 0xFF:
        return f"\\x{codepoint:02x}"
    if codepoint <= 0xFFFF:
        return f"\\u{codepoint:04x}"
    return f"\\U{codepoint:08x}"


def printable(text: str) -> str:
    """Return `text` with every non-printable character escaped, and nothing else.

    `str.isprintable()` is the test, and it is the whole design. Python defines
    it from the Unicode database: it is False for categories Cc, Cf, Cs, Co, Cn,
    Zl, Zp and Zs-except-ASCII-space — every control character, every bidi and
    invisible-format character, the line and paragraph separators, the
    surrogates, and the private-use and unassigned codepoints. It is True for
    every character that draws something, so `café`, `日本語`, `العربية` and
    `עברית` come back unchanged and a search result stays legible.

    A bare `!r` is the wrong tool here even though it escapes the same set.
    `repr` also wraps the string in quotes and doubles every backslash, which
    turns 160 characters of ordinary documentation into something nobody reads
    — and an unreadable search result is one whose escaping gets deleted by the
    next person who has to use the command. `!r` stays correct where the thing
    printed is one URL (`_cmd_add` and `_cmd_check`'s off-scope reports, and
    `normalize_url`'s own refusal message); it is wrong where the thing printed
    is prose.

    The category test is deliberately WIDER than the enumerated refusal set in
    `urls.py`, and the asymmetry is the point rather than an inconsistency.
    There, over-refusing means rejecting a URL a vendor legitimately published
    and refusing to mirror them at all, so U+00AD SOFT HYPHEN and the Arabic
    prefixed-format characters are excluded by name — they occur in real text.
    Here, over-escaping costs a reader `\\xad` inside one word of one preview
    line. Refusing is expensive and escaping is cheap, so the two must not share
    a set. The same asymmetry decides the Cn (unassigned) case: a codepoint
    assigned by a Unicode version newer than the running Python is escaped,
    which is a cosmetic loss and the safe direction.

    Output ambiguity, stated rather than fixed: a vendor page containing the
    six literal characters `\\x1b[2J` renders here identically to one
    containing a real ESC. Nothing in that output can move the cursor, so the
    ambiguity is cosmetic — and resolving it would mean doubling backslashes,
    i.e. becoming `repr`, whose readability cost is the reason this function
    exists. The output is for reading, not for round-tripping.
    """
    if text.isprintable():          # the overwhelmingly common case
        return text
    return "".join(c if c.isprintable() else _escape(c) for c in text)
