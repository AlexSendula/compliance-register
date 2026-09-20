"""htmlmd tests carried over from docs-mirror's test_html_bodies.py — only the
parts that exercise htmlmd itself (detection, conversion, <pre> handling), plus
one test against the real EUR-Lex fixture."""
from __future__ import annotations

from pathlib import Path

import pytest

from compliance_register.mirror import htmlmd
from compliance_register.mirror.htmlmd import html_to_markdown, looks_like_html

FIX = Path(__file__).parent / "fixtures"
PROSE = "Substantive prose about payments and webhooks. " * 12


def _page(title, body=PROSE):
    return (f"<!doctype html><html><head><title>{title}</title>"
            f"<script>var x=1</script></head><body>"
            f"<nav><a href='/docs/other'>Other</a></nav>"
            f"<article><h1>{title}</h1><p>{body}</p></article>"
            f"<footer>(c) x</footer></body></html>")


def test_eurlex_fixture_converts_to_readable_markdown():
    md = htmlmd.html_to_markdown(FIX.joinpath("eurlex-consolidated.html").read_text())
    assert "Article 1" in md and "Article 3" in md
    assert "documentation tool" in md
    assert "<div" not in md and "<span" not in md


@pytest.mark.parametrize("text", [
    "<!doctype html><html><body>hi</body></html>",
    "<!DOCTYPE HTML>\n<html>",
    "\n\n  <html lang='en'>",
    "﻿<!doctype html>",
    "<!-- a comment --><!doctype html>",
    "<?xml version='1.0'?><!doctype html>",
])
def test_a_document_is_detected(text):
    assert looks_like_html(text)


@pytest.mark.parametrize("text", [
    "# A page\n\nOrdinary prose.",
    "",
    "Some prose that mentions <html> in passing, mid-sentence.",
    "> quoted text\n\n<html> is not at the start",
])
def test_ordinary_markdown_is_not(text):
    assert not looks_like_html(text)


def test_markdown_documenting_html_is_not_html():
    """The false positive that matters most.

    A large share of the docs this tool mirrors ARE about HTML. A substring
    search for `<!doctype` would corrupt every one of those pages, which is
    strictly worse than the bug being fixed.
    """
    page = ("# Templating\n\nEvery page starts like this:\n\n"
            "```html\n<!doctype html>\n<html><body>hi</body></html>\n```\n\n"
            "Then add your content.\n")
    assert not looks_like_html(page)



def test_a_page_converts_to_readable_markdown():
    md = html_to_markdown(_page("Payments"), "https://docs.x.com/docs/pay")
    assert md is not None
    assert not looks_like_html(md)
    assert "# Payments" in md
    assert "Substantive prose" in md
    assert "var x=1" not in md, "script content leaked into the markdown"
    assert "(c) x" not in md, "footer chrome leaked into the markdown"


def test_relative_links_are_absolutised():
    """Not cosmetic. `rewrite_links` only rewrites hrefs starting with `http`,
    so a root-relative link is invisible to it and stays pointing at the live
    web. Absolutising here is what lets the existing rewrite pass localise it.
    """
    html = ("<!doctype html><html><body><article><h1>T</h1>"
            "<p><a href='/docs/other'>Other</a></p></article></body></html>")
    md = html_to_markdown(html, "https://docs.x.com/docs/here")
    assert "https://docs.x.com/docs/other" in md


def test_a_document_with_no_recoverable_text_is_refused():
    assert html_to_markdown("<!doctype html><html><body></body></html>", "u") is None
    assert html_to_markdown("", "u") is None


def test_code_blocks_survive():
    html = ("<!doctype html><html><body><article><h1>T</h1>"
            "<pre>def f():\n    return 1</pre></article></body></html>")
    md = html_to_markdown(html, "u")
    assert "```" in md and "def f():" in md



def test_a_code_block_built_from_token_line_divs_keeps_its_lines():
    """The shape Docusaurus emits, which is what cucumber.io serves. There is
    no literal newline anywhere in this markup: every line break is a `<br>`
    or a `</div>`, and both close the SAME line, so the naive fix
    double-spaces the listing."""
    html = (
        "<html><body><pre><code>"
        '<div class="token-line"><span>Scenario: Breaker guesses a word</span><br></div>'
        '<div class="token-line"><span>  Given the Maker has chosen a word</span><br></div>'
        '<div class="token-line"><span>  Then the Maker is asked to score</span></div>'
        "</code></pre></body></html>"
    )
    out = html_to_markdown(html)

    assert out == (
        "```\n"
        "Scenario: Breaker guesses a word\n"
        "  Given the Maker has chosen a word\n"
        "  Then the Maker is asked to score\n"
        "```"
    ), out


def test_a_pre_block_carrying_real_newlines_is_unchanged():
    """The regression guard for the fix above: a plain `<pre>` already had
    working line breaks and must not gain blank ones."""
    html = "<html><body><pre><code>a = 1\nb = 2\nc = 3</code></pre></body></html>"

    assert html_to_markdown(html) == "```\na = 1\nb = 2\nc = 3\n```"


def test_no_markdown_syntax_is_emitted_inside_a_fence():
    """Only a NEWLINE may be produced by structure inside `<pre>`. A `<strong>`
    that became `**` there would put characters inside the fence that the
    vendor never wrote, and the fence is the one place markdown is literal."""
    html = ("<html><body><pre>"
            "<div><strong>not bold</strong></div>"
            "<div><em>not italic</em></div>"
            "</pre></body></html>")
    out = html_to_markdown(html)

    assert "**" not in out and "*" not in out, out
    assert out == "```\nnot bold\nnot italic\n```", out


def test_a_fence_does_not_open_or_close_on_a_blank_line():
    """`</pre>` used to append a newline unconditionally, so a listing ending
    on `</div>` — the common case — got a blank line before its closing
    fence."""
    html = ('<html><body><pre><code><div class="token-line">'
            "<span>only line</span><br></div></code></pre></body></html>")

    assert html_to_markdown(html) == "```\nonly line\n```"


def test_a_code_sample_containing_a_fence_does_not_end_the_block():
    """A vendor page documenting markdown puts a literal ``` in a sample. With
    a fixed three-backtick fence the block ended at the vendor's text and the
    heading inside the sample became a heading in the mirror."""
    html = ("<html><body><pre>safe\n```\n# NOT A REAL HEADING\n```\nmore"
            "</pre></body></html>")
    out = html_to_markdown(html)

    assert out.startswith("````\n"), out
    assert out.endswith("\n````"), out
    assert "# NOT A REAL HEADING" in out
    # The sample's own fences survive intact rather than being escaped away.
    assert out.count("```\n") >= 2


def test_an_ordinary_block_still_uses_a_three_backtick_fence():
    """The widening is driven by content, so the common case is unchanged."""
    assert html_to_markdown("<html><body><pre>a = 1\nb = 2</pre></body></html>") == (
        "```\na = 1\nb = 2\n```")


def test_a_nested_pre_does_not_open_a_second_fence():
    """Invalid HTML, but a parser meets what the vendor shipped. A second
    opening fence would close the first one."""
    out = html_to_markdown("<html><body><pre>outer<pre>inner</pre>end</pre></body></html>")

    assert out.count("```") == 2, out
    assert "outer" in out and "inner" in out and "end" in out
