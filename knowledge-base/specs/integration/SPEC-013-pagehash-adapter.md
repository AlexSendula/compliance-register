---
id: SPEC-013
title: "Page-hash adapter: fetch to compare, and say so"
category: integration
tags: [integration, mirror, adapter, page-hash, content-hash]
status: implemented
certainty: 88
created: 2026-09-20
updated: 2026-09-21
related_code:
  - compliance_register/mirror/adapters/pagehash.py
  - tests/test_adapter_pagehash.py
intentional_decisions:
  - "Hash the converted markdown, not the raw HTML"
  - "Some-changed-plus-some-unreachable is reported as moved"
behaviors:
  - behavior_id: BEH-124
    title: "fetch writes every URL under .private/ for a non-redistributable source; an unchanged page is fresh; a changed body is moved naming the URL and the detail says it fetched"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_adapter_pagehash.py::test_fetch_then_fresh_then_moved
  - behavior_id: BEH-125
    title: "check is unreachable when a URL fails and no other URL changed"
    state: proposed
    level: unit
    adapter: pytest
  - behavior_id: BEH-126
    title: "a non-HTML body is reported as 'not html' and counts as unreachable"
    state: proposed
    level: unit
    adapter: pytest
  - behavior_id: BEH-127
    title: "config.urls absent falls back to the source URL"
    state: proposed
    level: unit
    adapter: pytest
  - behavior_id: BEH-280
    title: "check names every unreachable URL in the detail even when another URL changed"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_adapter_pagehash.py::test_check_names_unreachable_urls_even_when_another_changed
---

# Page-hash adapter: fetch to compare, and say so

## What

For sources with no version id, sitemap or feed, `config.urls` (default: the source URL) are fetched one by one; each body must be a 200 HTML document, is converted through htmlmd and hashed with `store.content_hash` (post-conversion, whitespace-normalised).

`check` reports moved with the URLs whose hash differs from the manifest, unreachable only when at least one URL failed and none changed, and fresh otherwise; the fresh and moved detail strings begin with "page-hash tier fetches to compare" (the unreachable detail is the joined per-URL failure list). `fetch` writes `<sha1(url)[:16]>.md` for each URL whose hash moved (or all with `--force`), refuses unreachable or non-HTML URLs by name, records `{hash, lastmod: None}` in the manifest and saves it in `finally`.

## Why

workflow.md: "on page-hash sources it must fetch to compare, and says so" — the only tier where check downloads bodies, so the detail states it. D24 consequence: wetten.overheid.nl's API hosts disallow robots, so Dutch statute is watched by page-hash on the act's own page (principle 8: no bypass, so the tool uses the page it is allowed to read). Hashing the converted markdown rather than the raw HTML means a changed cookie banner or nav outside the main region is not a move. A PSP's terms are the canonical non-redistributable example, so this tier is where `.private/` routing (principle 7) is exercised.

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-124 fetch writes every URL under .private/ for a non-redistributable source; an unchanged page is fresh; a changed body is moved naming the URL and the detail says it fetched | proposed | `tests/test_adapter_pagehash.py::test_fetch_then_fresh_then_moved` |
| BEH-125 check is unreachable when a URL fails and no other URL changed | proposed | — (test owed) |
| BEH-126 a non-HTML body is reported as 'not html' and counts as unreachable | proposed | — (test owed) |
| BEH-127 config.urls absent falls back to the source URL | proposed | — (test owed) |
| BEH-280 check names every unreachable URL in the detail even when another URL changed | proposed | `tests/test_adapter_pagehash.py::test_check_names_unreachable_urls_even_when_another_changed` |

Declarative decisions that are *not* executable are recorded under **Intentional
Design Decisions** below, not here.

## Intentional Design Decisions

### Hash the converted markdown, not the raw HTML

**Decision**: `content_hash` is computed on `html_to_markdown` output (main/article region, chrome dropped, whitespace collapsed).

**Rationale**: Site chrome and re-rendering churn must not count as a legal change; the mirrored text is what the register cites (principle 3).

**Security Scan Note**: Deliberately not a byte-level integrity check.

### Some-changed-plus-some-unreachable is reported as moved

**Decision**: check returns unreachable only when nothing changed; if any URL changed it returns moved, and the detail of a moved or fresh result ends with `; unreachable: <url>: <reason>` for every URL that could not be fetched.

**Rationale**: A move is the more actionable signal for the source's status, but principle 4 says a failed fetch is always reported as such — so the status is three-valued and the failures are still named.

**Security Scan Note**: Intended precedence; `test_check_names_unreachable_urls_even_when_another_changed` pins that nothing is dropped.

## Related Specs

- [SPEC-007: HTTP client](./SPEC-007-http-client.md)
- [SPEC-008: HTML to markdown converter](./SPEC-008-html-to-markdown.md)
- [SPEC-009: Mirror store](./SPEC-009-mirror-store.md)
- [SPEC-010: Adapter contract, registry and shared guards](./SPEC-010-adapter-contract.md)
- [SPEC-012: Feed adapter](./SPEC-012-feed-adapter.md)
- [SPEC-025: sources.json model: Source dataclass, defaults, atomic load/save, typed SourcesError](../api/SPEC-025-sources-model.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Inferred from code, tests and design repo (D24); certainty 88 |
| 2026-09-20 | Only fresh/moved details carry the "fetches to compare" prefix; unreachable lists the failures | Cross-check against `pagehash.check` |
| 2026-09-21 | moved/fresh details now also name every unreachable URL; BEH-280 added | G2 principle checkpoint, principle 4 |
