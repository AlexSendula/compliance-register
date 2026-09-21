---
id: SPEC-011
title: "Sitemap adapter: lastmod signal with capped fan-out"
category: integration
tags: [integration, mirror, adapter, sitemap, lastmod, cap]
status: implemented
certainty: 90
created: 2026-09-20
updated: 2026-09-21
related_code:
  - compliance_register/mirror/adapters/sitemap.py
  - tests/test_adapter_sitemap.py
  - tests/fixtures/sitemap.xml
intentional_decisions:
  - "Fan-out capped at 2000 pages and 50 child sitemaps, reported not silently truncated"
  - "Index recursion is one level deep only"
  - "Page file names are the first 16 hex chars of SHA-1 of the URL"
  - "lastmod is compared as an opaque string"
behaviors:
  - behavior_id: BEH-111
    title: "check on an empty manifest reports moved with every included page and excludes URLs outside config.include"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_adapter_sitemap.py::test_check_on_empty_manifest_is_moved
  - behavior_id: BEH-112
    title: "fetch writes one .md per page with lastmod in the manifest and a following check is fresh"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_adapter_sitemap.py::test_fetch_writes_and_check_becomes_fresh
  - behavior_id: BEH-113
    title: "a 5xx on the sitemap makes check unreachable"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_adapter_sitemap.py::test_check_unreachable_when_sitemap_fails
  - behavior_id: BEH-114
    title: "a non-HTML page body is refused by URL and the other pages are still written"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_adapter_sitemap.py::test_fetch_refuses_non_html
  - behavior_id: BEH-115
    title: "a listing failure in fetch is a refusal and MANIFEST.json is still saved"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_adapter_sitemap.py::test_fetch_listing_failure_is_refused_and_manifest_still_saved
  - behavior_id: BEH-116
    title: "fan-out stops at MAX_PAGES/MAX_CHILDREN, unneeded children are never requested, and the detail names the cap and config.include"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_adapter_sitemap.py::test_fan_out_is_capped_and_the_cap_is_reported
  - behavior_id: BEH-117
    title: "check downloads no page bodies on the sitemap tier"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_adapter_sitemap.py::test_check_downloads_no_page_bodies_on_the_sitemap_tier
  - behavior_id: BEH-118
    title: "--force refetches pages whose lastmod is unchanged"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_adapter_sitemap.py::test_force_refetches_pages_whose_lastmod_is_unchanged
---

# Sitemap adapter: lastmod signal with capped fan-out

## What

`_entries` GETs the source URL under the 5 MB listing budget, parses it through the DTD guard, recurses exactly one level into a `<sitemapindex>` (at most `MAX_CHILDREN` = 50 child sitemaps), and collects `(loc, lastmod)` pairs filtered by the optional `config.include` URL-prefix list, stopping at `MAX_PAGES` = 2000; every cap is recorded as a note.

`check` compares each page's lastmod string against the manifest via `needs_refresh` and reports moved with the changed URLs, fresh otherwise, or unreachable on any HTTP/robots/XML failure; the cap note is appended to the detail. `fetch` refetches pages whose lastmod moved (or all with `--force`), converts HTML through htmlmd, refuses non-HTML bodies by URL, writes `<sha1(url)[:16]>.md` with `source_url` and `lastmod` in the frontmatter, records the page in the manifest, reports a cap as a listing refusal, and always saves the manifest in `finally`.

## Why

workflow.md tier table: sitemap is the tier for regulators such as EDPB and Narodne novine whose per-page lastmod is the cheapest signal, and check downloads no page bodies on this tier (D18 incremental). Commit ce80ee0: one regulator's index can fan out to tens of thousands of requests; past the caps a run is a typed report telling the human to narrow `config.include`, not a crawl. Principle 9: the manifest is saved in `finally` so a listing failure never loses the pages already written. Markdown-only store (plan B global constraint): a PDF at a sitemap URL is refused by name, never written as a `.md`. Principle 4: an unreachable listing is reported as unreachable, never as fresh.

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-111 check on an empty manifest reports moved with every included page and excludes URLs outside config.include | accepted | `tests/test_adapter_sitemap.py::test_check_on_empty_manifest_is_moved` |
| BEH-112 fetch writes one .md per page with lastmod in the manifest and a following check is fresh | accepted | `tests/test_adapter_sitemap.py::test_fetch_writes_and_check_becomes_fresh` |
| BEH-113 a 5xx on the sitemap makes check unreachable | accepted | `tests/test_adapter_sitemap.py::test_check_unreachable_when_sitemap_fails` |
| BEH-114 a non-HTML page body is refused by URL and the other pages are still written | accepted | `tests/test_adapter_sitemap.py::test_fetch_refuses_non_html` |
| BEH-115 a listing failure in fetch is a refusal and MANIFEST.json is still saved | accepted | `tests/test_adapter_sitemap.py::test_fetch_listing_failure_is_refused_and_manifest_still_saved` |
| BEH-116 fan-out stops at MAX_PAGES/MAX_CHILDREN, unneeded children are never requested, and the detail names the cap and config.include | accepted | `tests/test_adapter_sitemap.py::test_fan_out_is_capped_and_the_cap_is_reported` |
| BEH-117 check downloads no page bodies on the sitemap tier | accepted | `tests/test_adapter_sitemap.py::test_check_downloads_no_page_bodies_on_the_sitemap_tier` |
| BEH-118 --force refetches pages whose lastmod is unchanged | accepted | `tests/test_adapter_sitemap.py::test_force_refetches_pages_whose_lastmod_is_unchanged` |

Declarative decisions that are *not* executable are recorded under **Intentional
Design Decisions** below, not here.

## Intentional Design Decisions

### Fan-out capped at 2000 pages and 50 child sitemaps, reported not silently truncated

**Decision**: Beyond the caps, `_entries` stops reading and appends a note; check puts it in the detail and fetch lists it as a refusal so the exit code is 1.

**Rationale**: A regulator's sitemap index is not a crawl frontier; the human is told to set `config.include` (commit ce80ee0). Principle 9: refuse loudly.

**Security Scan Note**: The caps are a DoS/cost bound, and the visible refusal means a scanner should not read the missing pages as data loss.

### Index recursion is one level deep only

**Decision**: A `<sitemapindex>` is expanded only at depth 0; a child that is itself an index is treated as an empty urlset.

**Rationale**: Bounded request count; real regulator indexes are one level.

**Security Scan Note**: Not a bug: recursion depth is a deliberate hard limit.

### Page file names are the first 16 hex chars of SHA-1 of the URL

**Decision**: `_relpath` hashes the URL to a fixed-length safe file name rather than deriving a name from the path.

**Rationale**: URLs carry characters and lengths that are not safe path components (principle 10); the manifest, keyed by full URL, is the index.

**Security Scan Note**: SHA-1 here is a file-naming function, not an integrity or security hash; 64 bits is ample within one source.

### lastmod is compared as an opaque string

**Decision**: No date parsing: any textual difference in `<lastmod>` counts as moved; a missing lastmod on either side counts as needs refresh.

**Rationale**: Principle 4: over-reporting is the safe direction; a parse failure on an odd date format would otherwise become a silent "fresh".

**Security Scan Note**: Intended; not a missing normalisation.

## Related Specs

- [SPEC-007: HTTP client](./SPEC-007-http-client.md)
- [SPEC-008: HTML to markdown converter](./SPEC-008-html-to-markdown.md)
- [SPEC-009: Mirror store](./SPEC-009-mirror-store.md)
- [SPEC-010: Adapter contract, registry and shared guards](./SPEC-010-adapter-contract.md)
- [SPEC-025: sources.json model: Source dataclass, defaults, atomic load/save, typed SourcesError](../api/SPEC-025-sources-model.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Inferred from code, tests and design repo (D18, D21); certainty 90 |
| 2026-09-21 | Behaviours promoted by Alex: tested → accepted, untested → confirmed (test owed) | First behaviour review after the freya wrap-up |
| 2026-09-21 | Tests written for BEH-117, BEH-118; promoted confirmed → accepted | tests owed |
