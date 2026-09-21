---
id: SPEC-008
title: "HTML to markdown converter (vendored verbatim from docs-mirror)"
category: integration
tags: [integration, mirror, htmlmd, markdown, vendored, stdlib]
status: implemented
certainty: 90
created: 2026-09-20
updated: 2026-09-21
related_code:
  - compliance_register/mirror/htmlmd.py
  - tests/test_htmlmd.py
  - tests/fixtures/eurlex-consolidated.html
intentional_decisions:
  - "Vendored verbatim; edits go upstream first"
  - "Conversion failure returns None, never raises"
  - "Only the first <article> or <main> is converted when one exists"
behaviors:
  - behavior_id: BEH-082
    title: "the real EUR-Lex consolidated fixture converts to markdown with no residual tags"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_htmlmd.py::test_eurlex_fixture_converts_to_readable_markdown
  - behavior_id: BEH-083
    title: "a document opening with doctype, <html>, BOM, comments or an XML declaration is detected as HTML"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_htmlmd.py::test_a_document_is_detected
  - behavior_id: BEH-084
    title: "ordinary markdown, empty text and prose mentioning <html> mid-sentence are not HTML"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_htmlmd.py::test_ordinary_markdown_is_not
  - behavior_id: BEH-085
    title: "markdown containing a full HTML document inside an html fence is not HTML"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_htmlmd.py::test_markdown_documenting_html_is_not_html
  - behavior_id: BEH-086
    title: "script and footer content never reach the markdown; the h1 and prose do"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_htmlmd.py::test_a_page_converts_to_readable_markdown
  - behavior_id: BEH-087
    title: "root-relative hrefs are absolutised against page_url"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_htmlmd.py::test_relative_links_are_absolutised
  - behavior_id: BEH-088
    title: "an empty body or empty input returns None rather than an empty string"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_htmlmd.py::test_a_document_with_no_recoverable_text_is_refused
  - behavior_id: BEH-089
    title: "a <pre> built from token-line divs and <br> keeps one line per line"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_htmlmd.py::test_a_code_block_built_from_token_line_divs_keeps_its_lines
  - behavior_id: BEH-090
    title: "no markdown emphasis syntax is emitted inside a fence"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_htmlmd.py::test_no_markdown_syntax_is_emitted_inside_a_fence
  - behavior_id: BEH-091
    title: "a code sample containing ``` widens the fence to four backticks"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_htmlmd.py::test_a_code_sample_containing_a_fence_does_not_end_the_block
  - behavior_id: BEH-092
    title: "a nested <pre> does not open a second fence"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_htmlmd.py::test_a_nested_pre_does_not_open_a_second_fence
---

# HTML to markdown converter (vendored verbatim from docs-mirror)

## What

`looks_like_html(text)` decides whether a body opens as an HTML document: it skips a BOM, leading whitespace, leading comments and an XML declaration, then checks that the first 200 characters start with `<!doctype html`, `<html` or `<head`. It is anchored to the start, not a substring search.

`html_to_markdown(html, page_url)` slices the first `<article>` or `<main>` region if one has text, drops script/style/nav/footer/aside/form/svg/iframe/head subtrees, converts headings, paragraphs, lists, links (hrefs absolutised against `page_url`) and `<pre>` blocks (fence widened past any backtick run in the content, no markdown syntax emitted inside), and returns `None` — never raises — when the input is empty, the parser fails, nothing usable comes out, or the output still looks like HTML.

The file is a verbatim copy of docs-mirror's `htmlmd.py` and carries that provenance comment at its head. Every adapter that stores a page (sitemap, feed, page-hash) routes the body through it; EUR-Lex chunks its own article markup and uses this module for text extraction inside each article.

## Why

Principle 11: standard library only, so the skill owns its own converter rather than adding html2text; the module docstring records the three rejected alternatives and accepts the quality cost on tables and code-fence languages. Principle 9: returning None instead of raising keeps a malformed regulator page a per-page refusal inside the fetch loop. The anchored detection exists because a substring test for `<html` corrupts every page that documents HTML in a fence. D21 and plan B Task 3: copied verbatim from docs-mirror so the two skills share exactly one surface and upstream fixes can be diffed in.

[NEEDS CLARIFICATION: is there a checked-in way to diff this file against docs-mirror upstream (a pinned commit or hash), or is "diff before editing" a manual step?]

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-082 the real EUR-Lex consolidated fixture converts to markdown with no residual tags | accepted | `tests/test_htmlmd.py::test_eurlex_fixture_converts_to_readable_markdown` |
| BEH-083 a document opening with doctype, <html>, BOM, comments or an XML declaration is detected as HTML | accepted | `tests/test_htmlmd.py::test_a_document_is_detected` |
| BEH-084 ordinary markdown, empty text and prose mentioning <html> mid-sentence are not HTML | accepted | `tests/test_htmlmd.py::test_ordinary_markdown_is_not` |
| BEH-085 markdown containing a full HTML document inside an html fence is not HTML | accepted | `tests/test_htmlmd.py::test_markdown_documenting_html_is_not_html` |
| BEH-086 script and footer content never reach the markdown; the h1 and prose do | accepted | `tests/test_htmlmd.py::test_a_page_converts_to_readable_markdown` |
| BEH-087 root-relative hrefs are absolutised against page_url | accepted | `tests/test_htmlmd.py::test_relative_links_are_absolutised` |
| BEH-088 an empty body or empty input returns None rather than an empty string | accepted | `tests/test_htmlmd.py::test_a_document_with_no_recoverable_text_is_refused` |
| BEH-089 a <pre> built from token-line divs and <br> keeps one line per line | accepted | `tests/test_htmlmd.py::test_a_code_block_built_from_token_line_divs_keeps_its_lines` |
| BEH-090 no markdown emphasis syntax is emitted inside a fence | accepted | `tests/test_htmlmd.py::test_no_markdown_syntax_is_emitted_inside_a_fence` |
| BEH-091 a code sample containing ``` widens the fence to four backticks | accepted | `tests/test_htmlmd.py::test_a_code_sample_containing_a_fence_does_not_end_the_block` |
| BEH-092 a nested <pre> does not open a second fence | accepted | `tests/test_htmlmd.py::test_a_nested_pre_does_not_open_a_second_fence` |

Declarative decisions that are *not* executable are recorded under **Intentional
Design Decisions** below, not here.

## Intentional Design Decisions

### Vendored verbatim; edits go upstream first

**Decision**: `htmlmd.py` is byte-for-byte docs-mirror's module plus a two-line provenance comment; it references docs-mirror concepts (`sync_vendor`, `qc`, principle 3) that do not exist here.

**Rationale**: Plan B Task 3 and D21: one shared surface between the two skills, diffed against upstream before any edit, rather than a fork that drifts.

**Security Scan Note**: Dead references in comments (SEC-008, `qc.check_page`) are upstream vocabulary, not missing code. Do not "fix" the docstring locally.

### Conversion failure returns None, never raises

**Decision**: Any exception from `html.parser`, an empty result, or output that still opens as HTML yields `None`; the adapter reports the page as refused and continues.

**Rationale**: Principle 9: the caller is inside the per-source loop above `save_manifest`; a raise there is the brick shape the loop exists to avoid.

**Security Scan Note**: The bare `except Exception` around `parser.feed` is the documented contract "returns None rather than raising" over vendor-controlled bytes, not a swallowed error.

### Only the first <article> or <main> is converted when one exists

**Decision**: `_main_region` slices with a non-greedy regex and hands the slice to the real parser; nested articles under-select.

**Rationale**: Under-selecting loses some prose; over-selecting brings back navigation. The regex is for slicing only, never for parsing.

**Security Scan Note**: A regex over HTML here is a deliberate pre-slice; the content is parsed by `html.parser` immediately after.

## Related Specs

- [SPEC-011: Sitemap adapter](./SPEC-011-sitemap-adapter.md)
- [SPEC-012: Feed adapter](./SPEC-012-feed-adapter.md)
- [SPEC-013: Page-hash adapter](./SPEC-013-pagehash-adapter.md)
- [SPEC-014: EUR-Lex adapter](./SPEC-014-eurlex-adapter.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Inferred from code, tests and design repo (D21, plan B Task 3); certainty 90 |
| 2026-09-21 | Behaviours promoted by Alex: tested → accepted, untested → confirmed (test owed) | First behaviour review after the freya wrap-up |
