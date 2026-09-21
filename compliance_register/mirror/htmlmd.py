"""HTML detection and HTML-to-markdown conversion, on the standard library only.

**Why this module exists.** `discover` resolves a vendor in tiers, and tier 2
— a `sitemap.xml` with no `llms.txt` beside it — hardcoded
`serves_markdown=False`. So `markdown_url` returned the page's own address,
`sync_vendor` fetched it, and the HTTP body was written **verbatim** into a
`.md` file. For any docs site that serves HTML at the addresses its sitemap
lists — which is most of them — the mirror was a directory of page source.

Measured on a real store before this module existed: a Docusaurus vendor
acquired through tier 2 was **73 of 73 pages raw HTML**, and `docs-mirror qc`
answered `ok: 0   with issues: 73`. A crawl-tier vendor in the same store was
0 of 500, because that tier converts. **Publishing a sitemap made a vendor's
docs come out worse than publishing nothing**, which is the opposite of the
tiering's intent.

`fetch.markdown_url` had already written the rule this violates, in its
argument for returning `None` rather than falling back to the plain URL:

    returning `url` would fetch the HTML page and write it into a `.md` file
    as though it were the markdown the affordance promised. That is a silent
    downgrade of exactly the kind principle 1 forbids

It refused to do that in one place and did exactly it, for every page, in
another.

**Standard library only, and that is a constraint rather than a preference.**
Principle 3: "The base install is `requests` + `PyYAML`. Anything needing
PyTorch, a browser, or a database ships as an extra, and every command except
the one that needs it works without it." Three alternatives were considered
and each is rejected for a stated reason:

  * **Add `html2text` or `markdownify` to the base install.** That argues
    directly against a standing principle, and the case is not strong enough:
    the gap between this module's output and `html2text`'s is a QUALITY gap
    (tables, definition lists, code-fence languages), not a capability gap.
    Paying a permanent dependency for polish is the trade principle 3 exists
    to refuse.
  * **Ship the converter as an optional extra.** This looks compliant and is
    the worst of the three, because it inverts principle 3's own clause —
    "every command except the one that needs it works without it". The command
    that would need it is `add`, the primary command, on an ordinary vendor.
  * **Route every HTML vendor to the crawl tier.** That is a browser, launched
    to re-render prose that is already server-rendered in bytes we have
    downloaded, at the cost of an opt-in extra the operator may not have.

**The honest price:** this project now owns an HTML-to-markdown parser, and it
is worse than `html2text` on tables and on code-fence languages. That is a
real, permanent maintenance cost, accepted deliberately rather than waved past.
"""
from __future__ import annotations

# Copied verbatim from docs-mirror (AlexSendula/docs-mirror, docs_mirror/htmlmd.py).
# Diff against upstream before editing; the only shared surface between the two skills.

import re
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urljoin

# Subtrees whose text is never page content. `nav`, `footer` and `aside` are
# site chrome; `script`, `style`, `noscript` and `template` are not prose at
# all; `svg` is markup whose text nodes are labels. A `form` is NOT dropped as
# a whole: wetten.overheid.nl wraps every act in one, and dropping it dropped
# the law — only its controls (`select`, `textarea`, `button`, `label`, and the
# void `input`) are interactive; the prose between them is content.
#
# `nav`/`footer`/`aside` are dropped here even though `crawl.py` deliberately
# does NOT strip them before link extraction — and the asymmetry is the point.
# That pass is harvesting a link frontier and must not lose an address; this
# one is producing prose for an agent to read, and a page whose every third
# line is a sidebar link is what `qc`'s `nav_only` rule exists to fail.
# Elements that never have an end tag (HTML void elements). One of these carrying
# `aria-hidden="true"` is skipped on its own; it cannot open a drop that an end
# tag would have to close.
_VOID = frozenset((
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
    "source", "track", "wbr",
))

_DROP = frozenset((
    "script", "style", "noscript", "template", "svg", "iframe",
    "nav", "footer", "aside", "head",
    "select", "textarea", "button", "label", "input",
))

# Emitted as-is, with their content escaped rather than interpreted.
_PRE = frozenset(("pre",))

# Inside `<pre>` no markdown syntax is emitted — the text is already formatted —
# but a line break still has to survive, and on a real docs site the line breaks
# are STRUCTURE rather than newline characters. Docusaurus renders a code block
# as `<pre><code><div class="token-line"><span>…</span><br></div>…` with no
# literal newline anywhere in it, so a converter that ignores every tag inside
# `<pre>` returns the whole listing on one line. Measured on the cucumber mirror
# after ADR-011 landed: 356 fenced blocks, 356 of them single-line, every
# Gherkin scenario and shell command in the vendor's docs run together.
#
# That is ADR-011's revisit condition 2 — a correctness failure rather than a
# formatting one — and it is worse than dropping the block would be, because the
# result still looks like a code example and is no longer one.
_PRE_BLOCK = frozenset(("div", "p", "li", "tr"))

_HEADINGS = {"h1": "#", "h2": "##", "h3": "###",
             "h4": "####", "h5": "#####", "h6": "######"}

# Block-level elements that force a paragraph break in the output.
_BLOCK = frozenset((
    "p", "div", "section", "article", "main", "header", "ul", "ol", "li",
    "table", "tr", "blockquote", "hr", "br", "dl", "dt", "dd", "figure",
    "figcaption", "details", "summary", *_HEADINGS,
))

_WS = re.compile(r"[ \t\r\f\v]+")
_BLANKS = re.compile(r"\n{3,}")
_TICKS = re.compile(r"`+")


def _fence_for(body: str) -> str:
    """The shortest fence that the block's own content cannot close.

    A vendor page that DOCUMENTS markdown puts a literal ``` inside a code
    block, and a three-backtick fence then ends at the vendor's text instead of
    at `</pre>`: everything after it stops being code and starts being
    structure, so a heading in the sample becomes a heading in the mirror. That
    is the CommonMark rule — a fence is closed only by a run at least as long —
    and it costs one pass over the block.

    Not a security boundary, and it is worth being precise about why, because
    the shape invites the claim. The whole mirrored page is vendor-controlled
    prose; anyone who can put a heading inside a code sample can put one outside
    it, so nothing crosses a trust boundary here that was not already crossed.
    It is a fidelity bug, and it belongs to the same family as the token-line
    defect above: a code block that silently stops being one.
    """
    longest = max((len(m.group()) for m in _TICKS.finditer(body)), default=0)
    return "`" * max(3, longest + 1)


def looks_like_html(text: str) -> bool:
    """Does `text` OPEN as an HTML document?

    **Anchored to the first content, deliberately, and not a fuzzy search.**
    A substring test for `<html` or `<!doctype` would fire on a perfectly good
    markdown page that documents HTML inside a fenced block — which is a large
    share of the docs this tool exists to mirror. Verified against a real
    store: this predicate answers True for 73 of 73 pages of a tier-2 mirror,
    False for 500 of 500 pages of a crawl-tier mirror in the same store, and
    False for markdown whose body contains an ```html fence holding a full
    document.

    Leading whitespace, a BOM and any number of leading comments are skipped
    first, because a served document may carry all three before its doctype.

    **This is asked of a BODY, not of a stored file.** A file this tool wrote
    opens with its `---` frontmatter, so the doctype sits ~100 bytes in and
    this returns False for it. That is correct and is why `fetch` strips the
    frontmatter before asking about a file on disk; getting it wrong is how a
    repair pass silently does nothing.
    """
    if not text:
        return False
    s = text.lstrip("﻿").lstrip()
    # Skip any run of leading comments and XML/doctype-adjacent preamble.
    while s.startswith("<!--"):
        end = s.find("-->")
        if end == -1:
            return False
        s = s[end + 3:].lstrip()
    if s.startswith("<?xml"):
        end = s.find("?>")
        if end == -1:
            return False
        s = s[end + 2:].lstrip()
        while s.startswith("<!--"):
            end = s.find("-->")
            if end == -1:
                return False
            s = s[end + 3:].lstrip()
    head = s[:200].lower()
    return (head.startswith("<!doctype html")
            or head.startswith("<html")
            or head.startswith("<head"))


class _Converter(HTMLParser):
    """Walks an HTML document and emits markdown.

    Deliberately not a general-purpose converter. It handles the shapes a
    documentation page is built from — headings, prose, lists, code, links,
    images, blockquotes — and ignores the rest rather than guessing. A shape it
    does not know contributes its text and no markup, which degrades to plain
    prose rather than to noise.
    """

    def __init__(self, page_url: str = "") -> None:
        super().__init__(convert_charrefs=True)
        self.page_url = page_url
        self._out: list[str] = []
        self._drop_depth = 0
        self._drop_tag = ""
        self._pre_depth = 0
        # Index in `_out` of the opening fence, so its width can be widened
        # once the block's content is known. See `_fence_for`.
        self._pre_fence_at = 0
        self._list_stack: list[dict] = []
        self._href: str | None = None
        self._link_text: list[str] = []
        self._in_link = 0
        self._quote_depth = 0
        # Set once <body> is seen. Until then everything outside <head> is
        # still emitted, so a fragment with no <body> converts too.
        self._seen_body = False

    # -- helpers ---------------------------------------------------------
    def _emit(self, text: str) -> None:
        if self._in_link:
            self._link_text.append(text)
        else:
            self._out.append(text)

    def _newline(self, n: int = 1) -> None:
        if self._in_link:
            return
        self._out.append("\n" * n)

    def _pre_break(self) -> None:
        """End the current line inside a `<pre>`, if it is not already ended.

        Idempotent on purpose, and that is what makes it usable from three
        callers. The markup that motivates it closes a line TWICE —
        `<div class="token-line">…<br></div>` carries both a `<br>` and a
        `</div>` — so an unconditional newline would double-space every listing
        it was added to fix. `_newline` is not usable here: it is the
        paragraph-break helper for prose, it is suppressed inside a link, and
        blank lines inside a fence are content.
        """
        for chunk in reversed(self._out):
            if not chunk:
                continue
            if not chunk.endswith("\n"):
                self._out.append("\n")
            return

    def _absolutise(self, href: str) -> str:
        """Resolve a link against the page it was found on.

        Not cosmetic. `rewrite.rewrite_links` only rewrites hrefs that begin
        with `http`, so a root-relative `/docs/bdd` — which is what a
        server-rendered docs site emits for its own pages — is invisible to it
        and stays pointing at the live web in the mirrored file. Absolutising
        here is what lets the existing rewrite pass turn those into local
        links, which is the difference between a navigable mirror and a pile
        of pages.
        """
        if not self.page_url or not href:
            return href
        if href.startswith(("#", "mailto:", "tel:", "data:", "javascript:")):
            return href
        try:
            return urljoin(self.page_url, href)
        except ValueError:
            return href

    # -- parser callbacks ------------------------------------------------
    def handle_starttag(self, tag, attrs):
        if self._drop_depth:
            if tag == self._drop_tag:
                self._drop_depth += 1
            return
        a = dict(attrs)
        # `aria-hidden` marks decorative chrome — anchor icons, separators.
        # The drop is closed by the end tag of the element that opened it, and
        # only that one: closing it on any `_DROP` end tag let a
        # `<div aria-hidden="true">` swallow the rest of the document. A void
        # element has no end tag, so it is skipped without opening a drop.
        if tag in _DROP or a.get("aria-hidden") == "true":
            if tag not in _VOID:
                self._drop_tag, self._drop_depth = tag, 1
            return
        if tag == "body":
            self._seen_body = True

        if tag in _PRE:
            # Only the OUTERMOST `<pre>` opens a fence. Nested `<pre>` is
            # invalid HTML, but a parser meets what the vendor shipped, not
            # what the spec allows, and a second opening fence there would
            # close the first one.
            if not self._pre_depth:
                self._newline(2)
                self._pre_fence_at = len(self._out)
                self._out.append("```\n")   # provisional; widened at the close
            self._pre_depth += 1
            return
        if self._pre_depth:
            # Structure-as-line-break, and ONLY that: no bullet, no heading, no
            # emphasis marker may be emitted here or it lands inside the fence
            # as literal text the vendor never wrote.
            if tag == "br" or tag in _PRE_BLOCK:
                self._pre_break()
            return

        if tag in _HEADINGS:
            self._newline(2)
            self._out.append(_HEADINGS[tag] + " ")
        elif tag in ("ul", "ol"):
            self._list_stack.append({"ordered": tag == "ol", "n": 0})
            self._newline(2 if len(self._list_stack) == 1 else 1)
        elif tag == "li":
            self._newline()
            depth = max(0, len(self._list_stack) - 1)
            self._out.append("  " * depth)
            if self._list_stack and self._list_stack[-1]["ordered"]:
                self._list_stack[-1]["n"] += 1
                self._out.append(f"{self._list_stack[-1]['n']}. ")
            else:
                self._out.append("- ")
        elif tag == "blockquote":
            self._quote_depth += 1
            self._newline(2)
            self._out.append("> ")
        elif tag == "code" and not self._pre_depth:
            self._emit("`")
        elif tag in ("strong", "b"):
            self._emit("**")
        elif tag in ("em", "i"):
            self._emit("*")
        elif tag == "br":
            self._newline()
        elif tag == "hr":
            self._newline(2)
            self._out.append("---")
            self._newline(2)
        elif tag == "a":
            href = a.get("href")
            if href:
                self._href = self._absolutise(href)
                self._in_link += 1
                self._link_text = []
        elif tag == "img":
            src = a.get("src")
            if src:
                alt = a.get("alt", "")
                self._emit(f"![{alt}]({self._absolutise(src)})")
        elif tag in _BLOCK:
            self._newline(2)

    def handle_endtag(self, tag):
        if self._drop_depth:
            if tag == self._drop_tag:
                self._drop_depth -= 1
            return
        if tag in _PRE:
            if self._pre_depth:
                self._pre_depth -= 1
            if self._pre_depth:
                return
            # `_pre_break` rather than a bare "\n": the listing usually ends
            # on a `</div>` that already closed the line, and an
            # unconditional newline put a blank line inside every fence.
            self._pre_break()
            fence = _fence_for("".join(self._out[self._pre_fence_at + 1:]))
            self._out[self._pre_fence_at] = fence + "\n"
            self._out.append(fence)
            self._newline(2)
            return
        if self._pre_depth:
            if tag in _PRE_BLOCK:
                self._pre_break()
            return

        if tag == "a" and self._in_link:
            self._in_link -= 1
            text = "".join(self._link_text).strip()
            href = self._href or ""
            self._href = None
            self._link_text = []
            if text and href:
                self._out.append(f"[{text}]({href})")
            elif text:
                self._out.append(text)
        elif tag == "code":
            self._emit("`")
        elif tag in ("strong", "b"):
            self._emit("**")
        elif tag in ("em", "i"):
            self._emit("*")
        elif tag in ("ul", "ol"):
            if self._list_stack:
                self._list_stack.pop()
            self._newline(2 if not self._list_stack else 1)
        elif tag == "blockquote":
            self._quote_depth = max(0, self._quote_depth - 1)
            self._newline(2)
        elif tag in _HEADINGS:
            self._newline(2)
        elif tag in _BLOCK:
            self._newline(2)

    def handle_data(self, data):
        if self._drop_depth:
            return
        if self._pre_depth:
            self._out.append(data)
            return
        text = _WS.sub(" ", data)
        if not text.strip():
            # Preserve a single separating space between inline elements.
            if text and self._out and not self._out[-1].endswith((" ", "\n")):
                self._emit(" ")
            return
        self._emit(text)

    def result(self) -> str:
        text = "".join(self._out)
        text = unescape(text)
        # Collapse the paragraph breaks the block rules emit generously.
        lines = [ln.rstrip() for ln in text.split("\n")]
        text = "\n".join(lines)
        text = _BLANKS.sub("\n\n", text)
        return text.strip()


def html_to_markdown(html: str, page_url: str = "") -> str | None:
    """Convert an HTML document to markdown, or None if nothing usable came out.

    `None` rather than an empty string, and `None` rather than a raise. The
    caller is inside `sync_vendor`'s fetch loop, above `save_manifest` and
    `record_fetch`, so a raise here is the SEC-008 brick shape that this loop's
    whole structure exists to avoid. The caller reports the page and continues.

    `page_url` is used to absolutise hrefs — see `_Converter._absolutise` for
    why that is load-bearing rather than tidy.

    **The main-content slice happens first**, and it is what separates a
    readable page from a wall of navigation. A documentation page puts its
    prose in `<article>` or `<main>`; everything outside is chrome that
    `qc.check_page`'s `nav_only` rule would fail the page for. When neither
    element is present the whole document is converted and the `_DROP` set is
    the only defence, which is weaker but is never worse than what this module
    replaced.
    """
    if not html:
        return None
    body = _main_region(html)
    parser = _Converter(page_url)
    try:
        parser.feed(body)
        parser.close()
    except Exception:
        # html.parser is lenient by design and does not raise on malformed
        # input, but it is a parser over vendor-controlled bytes and this
        # function's contract is "returns None rather than raising". Anything
        # unexpected becomes a refusal the caller reports, not a crash inside
        # the fetch loop.
        return None
    out = parser.result()
    if not out.strip():
        return None
    if looks_like_html(out):
        # The conversion produced something that still opens as a document —
        # it did not convert. Refusing is honest; writing it would be the
        # silent downgrade this module exists to stop.
        return None
    return out


_ARTICLE = re.compile(r"<article[^>]*>(.*?)</article\s*>", re.I | re.S)
_MAIN = re.compile(r"<main[^>]*>(.*?)</main\s*>", re.I | re.S)


def _main_region(html: str) -> str:
    """The document's main content, or the whole document if it says nothing.

    Regex rather than a parse, and only for SLICING — the slice is handed to a
    real parser immediately after. A nested `<article>` inside another is the
    known limit; the non-greedy match takes the first one's opening tag and the
    first closing tag after it, which under-selects rather than over-selects.
    Under-selecting costs some prose; over-selecting brings back the navigation
    this exists to remove.
    """
    for pattern in (_ARTICLE, _MAIN):
        m = pattern.search(html)
        if m and m.group(1).strip():
            return m.group(1)
    return html
