---
id: SPEC-010
title: "Adapter contract, registry and shared guards"
category: integration
tags: [integration, mirror, adapters, registry, prefetch, xml, dtd]
status: implemented
certainty: 91
created: 2026-09-20
updated: 2026-09-21
related_code:
  - compliance_register/mirror/adapters/__init__.py
  - compliance_register/sources.py
  - tests/test_adapter_sitemap.py
  - tests/test_adapter_feed.py
  - tests/test_adapter_eurlex.py
intentional_decisions:
  - "prefetch swallows every exception into per-CELEX values"
  - "Any DTD in an XML listing is refused, even a harmless one"
  - "The registry is a closed tuple; validation, not the loop, rejects unknown adapters"
behaviors:
  - behavior_id: BEH-103
    title: "get('sitemap') returns the sitemap module"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_adapter_sitemap.py::test_registry
  - behavior_id: BEH-104
    title: "a sitemap listing with a DTD is reported unreachable with 'DTD' in the detail"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_adapter_sitemap.py::test_sitemap_with_dtd_is_unreachable
  - behavior_id: BEH-105
    title: "a feed listing with a DTD is reported unreachable with 'DTD' in the detail"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_adapter_feed.py::test_feed_with_dtd_is_unreachable
  - behavior_id: BEH-106
    title: "a listing over 5 MB is refused and reported unreachable"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_adapter_sitemap.py::test_listing_is_capped_at_5mb
  - behavior_id: BEH-107
    title: "prefetch resolves the whole eurlex basket with one SPARQL request and feeds check() and fetch()"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_adapter_eurlex.py::test_prefetch_resolves_whole_basket_in_one_request
  - behavior_id: BEH-108
    title: "a failed prefetch surfaces per source as unreachable/refused, never raised"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_adapter_eurlex.py::test_prefetch_failure_is_unreachable_per_source_not_raised
  - behavior_id: BEH-109
    title: "an oversized CSV field (csv.Error) inside prefetch is unreachable and the run still writes .last-check"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_check.py::test_oversized_csv_field_in_resolve_is_unreachable_and_run_completes
  - behavior_id: BEH-110
    title: "prefetch returns {} when no eurlex source is chosen and makes no request"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_adapter_eurlex.py::test_prefetch_returns_empty_when_no_eurlex_source_is_chosen_and_makes_no_request
  - behavior_id: BEH-296
    title: "an HTML page served as a listing is named as such, not as a DTD"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_adapter_sitemap.py::test_html_served_as_a_listing_is_named_as_such
---

# Adapter contract, registry and shared guards

## What

Every tier is a module exposing `check(source, client, *, today, cdir, **extra) -> CheckResult` and `fetch(source, client, cdir, *, today, force, **extra) -> FetchResult`. `CheckResult` carries a status that is exactly one of fresh/unreachable/moved, an optional version, a human-readable detail, the list of changed keys and an optional next_version/next_date. `FetchResult` carries written paths, a skipped count, a list of refusal strings and the version written.

`NAMES` is the closed registry (`eurlex`, `sitemap`, `feed`, `pagehash`); `get(name)` returns the module and `sources.validate` refuses any other name before the loop. `prefetch(chosen, client_factory, today)` runs once per check/fetch and resolves the whole EUR-Lex basket with one client, returning `{adapter: kwargs}`; any exception there is stored per CELEX and re-raised inside each source's own try.

`parse_xml(body)` refuses any listing containing `<!DOCTYPE` in the first 4 KB or `<!ENTITY` anywhere before expat sees it, and `LISTING_MAX_BYTES` = 5 MB caps sitemap and feed bodies below the 20 MB page budget.

## Why

D21: one generic engine with tiers, not a scraper per site; the two-function contract keeps each adapter small and lets check/fetch stay adapter-agnostic. Principle 9 and commit 1d954e2: prefetch is the one choke point both commands route through before sources.json is saved, so it must never raise — a bad CSV or client surfaces per source as unreachable with the exception name. Commit a959ced: entity expansion is the only XML risk left on modern expat and a listing never legitimately needs a DTD, so one seam in front of `ET.fromstring` refuses it; listings get a tighter byte budget than pages because a 5 MB sitemap is not a listing the tool wants. Commit 35691ce: an unknown adapter name used to be a KeyError inside the loop; the closed `NAMES` tuple plus validation moves that to exit 2 before any request (D29). Principle 2: no plug-in loading and nothing law-specific in the registry — the adapters carry protocols, not instruments.

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-103 get('sitemap') returns the sitemap module | accepted | `tests/test_adapter_sitemap.py::test_registry` |
| BEH-104 a sitemap listing with a DTD is reported unreachable with 'DTD' in the detail | accepted | `tests/test_adapter_sitemap.py::test_sitemap_with_dtd_is_unreachable` |
| BEH-105 a feed listing with a DTD is reported unreachable with 'DTD' in the detail | accepted | `tests/test_adapter_feed.py::test_feed_with_dtd_is_unreachable` |
| BEH-106 a listing over 5 MB is refused and reported unreachable | accepted | `tests/test_adapter_sitemap.py::test_listing_is_capped_at_5mb` |
| BEH-107 prefetch resolves the whole eurlex basket with one SPARQL request and feeds check() and fetch() | accepted | `tests/test_adapter_eurlex.py::test_prefetch_resolves_whole_basket_in_one_request` |
| BEH-108 a failed prefetch surfaces per source as unreachable/refused, never raised | accepted | `tests/test_adapter_eurlex.py::test_prefetch_failure_is_unreachable_per_source_not_raised` |
| BEH-109 an oversized CSV field (csv.Error) inside prefetch is unreachable and the run still writes .last-check | accepted | `tests/test_check.py::test_oversized_csv_field_in_resolve_is_unreachable_and_run_completes` |
| BEH-110 prefetch returns {} when no eurlex source is chosen and makes no request | accepted | `tests/test_adapter_eurlex.py::test_prefetch_returns_empty_when_no_eurlex_source_is_chosen_and_makes_no_request` |
| BEH-296 an HTML page served as a listing is named as such, not as a DTD | accepted | `tests/test_adapter_sitemap.py::test_html_served_as_a_listing_is_named_as_such` |

Declarative decisions that are *not* executable are recorded under **Intentional
Design Decisions** below, not here.

## Intentional Design Decisions

### prefetch swallows every exception into per-CELEX values

**Decision**: `except Exception` in prefetch maps the exception object onto every CELEX in the basket; `check()`/`fetch()` re-raise it inside their own try and report unreachable/refused.

**Rationale**: The basket is resolved before the source loop; a raise there would abort the run before sources.json and `.last-check` are written (principle 9).

**Security Scan Note**: Broad except at a documented choke point; the exception type and message are preserved in the per-source detail, not discarded.

### Any DTD in an XML listing is refused, even a harmless one

**Decision**: `parse_xml` raises HttpRefused when `<!DOCTYPE` appears in the first 4096 bytes or `<!ENTITY` anywhere; the listing is reported as unreachable by check and as a listing refusal by fetch.

**Rationale**: Billion-laughs / entity expansion is the remaining expat risk; sitemaps and feeds never need a DTD.

**Security Scan Note**: This is the XXE/entity-expansion defence; a false positive on a sitemap with a DOCTYPE is accepted and visible in the detail.

### The registry is a closed tuple; validation, not the loop, rejects unknown adapters

**Decision**: `NAMES` lists four adapters; `get()` would KeyError on anything else, but `sources.validate` refuses such a source before check/fetch make any request.

**Rationale**: Principle 2: no plug-in loading; principle 9: an unknown name must be a refusal before network, not a traceback inside the loop.

**Security Scan Note**: `get()` has no dynamic import by user-controlled name; the import list is static.

## Related Specs

- [SPEC-007: HTTP client](./SPEC-007-http-client.md)
- [SPEC-011: Sitemap adapter](./SPEC-011-sitemap-adapter.md)
- [SPEC-012: Feed adapter](./SPEC-012-feed-adapter.md)
- [SPEC-013: Page-hash adapter](./SPEC-013-pagehash-adapter.md)
- [SPEC-014: EUR-Lex adapter](./SPEC-014-eurlex-adapter.md)
- [SPEC-015: fetch command](./SPEC-015-fetch-command.md)
- [SPEC-016: check command](./SPEC-016-check-command.md)
- [SPEC-025: sources.json model: Source dataclass, defaults, atomic load/save, typed SourcesError](../api/SPEC-025-sources-model.md)
- [SPEC-026: sources.validate and refusals: the network-free gate before any request](../api/SPEC-026-sources-validate-refusals.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Inferred from code, tests and design repo (D21, D29); certainty 91 |
| 2026-09-21 | Behaviours promoted by Alex: tested → accepted, untested → confirmed (test owed) | First behaviour review after the freya wrap-up |
| 2026-09-21 | parse_xml names an HTML page served as a listing (bot challenge / error page as 200) before the DTD check; BEH-296 added | nieuwbouw-tracker trial review |
| 2026-09-21 | Tests written for BEH-110; promoted confirmed → accepted | tests owed |
