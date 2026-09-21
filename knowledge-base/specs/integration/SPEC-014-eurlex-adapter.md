---
id: SPEC-014
title: "EUR-Lex adapter: SPARQL resolve, consolidated CELEX signal, guards, per-article chunking"
category: integration
tags: [integration, mirror, adapter, eurlex, sparql, celex, guards]
status: implemented
certainty: 94
created: 2026-09-20
updated: 2026-09-20
related_code:
  - compliance_register/mirror/adapters/eurlex.py
  - references/eurlex-resolve.sparql
  - tests/test_adapter_eurlex.py
  - tests/test_check.py
  - tests/fixtures/eurlex-consolidated.html
  - tests/fixtures/eurlex-chrome.html
  - tests/fixtures/sparql-resolve.csv
intentional_decisions:
  - "A header-only or all-malformed SPARQL response is unreachable, never 'no consolidation'"
  - "Zero rows for one CELEX is unreachable even when last_version is None"
  - "Server rows are shape-checked before becoming paths or URLs; malformed rows are dropped, never index-split"
  - "Guards G1–G5 run before any write; failure leaves version unchanged"
  - "Only article divs are mirrored; preamble, recitals and annexes are not"
  - "Basket chunked at 100 CELEXes per GET, no POST"
  - "Language availability is not pre-checked"
behaviors:
  - behavior_id: BEH-128
    title: "the SPARQL endpoint is https and every request in a resolve is https"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_adapter_eurlex.py::test_sparql_endpoint_is_https
  - behavior_id: BEH-129
    title: "resolve picks the latest consolidation dated <= today as current and the earliest future one as next"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_adapter_eurlex.py::test_resolve_applies_today_client_side
  - behavior_id: BEH-130
    title: "check is moved (with version and next_version) when last_version differs and fresh when it matches"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_adapter_eurlex.py::test_check_moved_then_fresh
  - behavior_id: BEH-131
    title: "a header-only CSV makes check unreachable"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_adapter_eurlex.py::test_header_only_csv_is_unreachable
  - behavior_id: BEH-132
    title: "fetch writes <current>/art_N.md with consolidated metadata, a CC-BY modification banner, and sets version"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_adapter_eurlex.py::test_fetch_writes_articles_and_sets_version
  - behavior_id: BEH-133
    title: "a 200 body that is site chrome is refused by G2/G3 with nothing written and version None"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_adapter_eurlex.py::test_fetch_refuses_site_chrome
  - behavior_id: BEH-134
    title: "chunk() yields ## Article / ### subtitle headings with no space-only or triple-blank lines"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_adapter_eurlex.py::test_chunk_headings_and_whitespace_on_real_markup
  - behavior_id: BEH-135
    title: "a source config without celex is unreachable naming the key, not a KeyError"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_adapter_eurlex.py::test_check_with_missing_config_is_unreachable_not_raised
  - behavior_id: BEH-136
    title: "malformed CSV rows (path-shaped CELEX, non-ISO date) are dropped and never split"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_adapter_eurlex.py::test_resolve_drops_malformed_rows_and_never_splits_them
  - behavior_id: BEH-137
    title: "a CSV whose rows are all malformed raises HttpUnreachable"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_adapter_eurlex.py::test_resolve_all_rows_malformed_is_unreachable
  - behavior_id: BEH-138
    title: "zero rows for the requested CELEX is unreachable with version None even when last_version is None"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_adapter_eurlex.py::test_zero_rows_for_this_celex_is_unreachable_even_without_last_version
  - behavior_id: BEH-139
    title: "a check run over two eurlex sources issues exactly one SPARQL request"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_adapter_eurlex.py::test_check_run_issues_one_sparql_query_for_all_eurlex_sources
  - behavior_id: BEH-140
    title: "G4 accepts the real reference line and refuses a body whose only header is the base-CELEX title or a glued digit"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_adapter_eurlex.py::test_g4_needs_the_consolidated_reference_line_not_the_title
  - behavior_id: BEH-141
    title: "fetch skips (skipped=1, nothing written) when current equals last_version and force is false"
    state: proposed
    level: unit
    adapter: pytest
  - behavior_id: BEH-142
    title: "G5 refuses a body whose article anchors are duplicated or out of order"
    state: proposed
    level: unit
    adapter: pytest
  - behavior_id: BEH-143
    title: "a basket over 100 CELEXes is resolved in more than one GET"
    state: proposed
    level: unit
    adapter: pytest
---

# EUR-Lex adapter: SPARQL resolve, consolidated CELEX signal, guards, per-article chunking

## What

`resolve(client, celexes, today)` GETs CELLAR's SPARQL endpoint over https with the shipped template (`VALUES` filled as typed `"…"^^xsd:string` literals, CSV output), raises HttpUnreachable on a non-200, on a header-only CSV for a non-empty basket, or when no row is well-formed, drops any row whose consolCelex does not match `0dddd[A-Z]{1,2}dddd-dddddddd` or whose consolDate is not ISO, and applies `today` client-side to yield per CELEX the current consolidation and the next scheduled one. `prefetch` resolves the whole basket in chunks of 100 per GET, storing a chunk's exception per CELEX.

`check` reports moved when the current consolidated CELEX differs from `source.last_version`, fresh when equal, unreachable on any failure, a missing config key, or zero rows for the CELEX (never fresh with version None).

`fetch` skips when current equals last_version unless forced, GETs `https://eur-lex.europa.eu/legal-content/{LANG}/TXT/HTML/?uri=CELEX:{current}`, then applies guards G1 (200 + text/html), G2 (documentation-tool marker present), G3 (at least one `id="art_N"`), G4 (`<p class="reference">` header equals sector-0 CELEX, language and date of the requested version), G5 (anchors unique and increasing); on any failure nothing is written and version stays None. On success it splits `<div class="eli-subdivision" id="art_N">` into `<current>/art_N.md` files with a CC-BY modification banner and per-article metadata, records each in the manifest (saved in `finally`) and returns `version = current`.

## Why

D28 and principle 2: the adapter carries only the protocol (SPARQL endpoint and HTML URL template); every instrument's CELEX is discovered into sources.json. The research spec (impl-eurlex-adapter-spec.md) verified both traps: without `^^xsd:string` CELLAR returns HTTP 200 with a header-only CSV, and EUR-Lex returns 200 with site chrome (later 404) for a missing language version — so a header-only CSV is unreachable, never "no consolidation", and five content guards run before a byte is written. Commit f577c33: server rows become directory names and URL parameters, so they are shape-checked first (principle 10). Commit 5851970: a never-consolidated act is unreachable, never fresh with version None (principle 4). Commit adef55a: N sources cost one SPARQL request. Commit cb0aea0: the banner states the text was converted and split, as CC-BY 4.0 §3(a)(1)(B) requires (principle 7: licence-gated data). Commit 41f4c32: G4 anchors on the reference line because the `<title>` repeats the base CELEX, which rejected every real page.

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-128 the SPARQL endpoint is https and every request in a resolve is https | proposed | `tests/test_adapter_eurlex.py::test_sparql_endpoint_is_https` |
| BEH-129 resolve picks the latest consolidation dated <= today as current and the earliest future one as next | proposed | `tests/test_adapter_eurlex.py::test_resolve_applies_today_client_side` |
| BEH-130 check is moved (with version and next_version) when last_version differs and fresh when it matches | proposed | `tests/test_adapter_eurlex.py::test_check_moved_then_fresh` |
| BEH-131 a header-only CSV makes check unreachable | proposed | `tests/test_adapter_eurlex.py::test_header_only_csv_is_unreachable` |
| BEH-132 fetch writes <current>/art_N.md with consolidated metadata, a CC-BY modification banner, and sets version | proposed | `tests/test_adapter_eurlex.py::test_fetch_writes_articles_and_sets_version` |
| BEH-133 a 200 body that is site chrome is refused by G2/G3 with nothing written and version None | proposed | `tests/test_adapter_eurlex.py::test_fetch_refuses_site_chrome` |
| BEH-134 chunk() yields ## Article / ### subtitle headings with no space-only or triple-blank lines | proposed | `tests/test_adapter_eurlex.py::test_chunk_headings_and_whitespace_on_real_markup` |
| BEH-135 a source config without celex is unreachable naming the key, not a KeyError | proposed | `tests/test_adapter_eurlex.py::test_check_with_missing_config_is_unreachable_not_raised` |
| BEH-136 malformed CSV rows (path-shaped CELEX, non-ISO date) are dropped and never split | proposed | `tests/test_adapter_eurlex.py::test_resolve_drops_malformed_rows_and_never_splits_them` |
| BEH-137 a CSV whose rows are all malformed raises HttpUnreachable | proposed | `tests/test_adapter_eurlex.py::test_resolve_all_rows_malformed_is_unreachable` |
| BEH-138 zero rows for the requested CELEX is unreachable with version None even when last_version is None | proposed | `tests/test_adapter_eurlex.py::test_zero_rows_for_this_celex_is_unreachable_even_without_last_version` |
| BEH-139 a check run over two eurlex sources issues exactly one SPARQL request | proposed | `tests/test_adapter_eurlex.py::test_check_run_issues_one_sparql_query_for_all_eurlex_sources` |
| BEH-140 G4 accepts the real reference line and refuses a body whose only header is the base-CELEX title or a glued digit | proposed | `tests/test_adapter_eurlex.py::test_g4_needs_the_consolidated_reference_line_not_the_title` |
| BEH-141 fetch skips (skipped=1, nothing written) when current equals last_version and force is false | proposed | — (test owed) |
| BEH-142 G5 refuses a body whose article anchors are duplicated or out of order | proposed | — (test owed) |
| BEH-143 a basket over 100 CELEXes is resolved in more than one GET | proposed | — (test owed) |

Declarative decisions that are *not* executable are recorded under **Intentional
Design Decisions** below, not here.

## Intentional Design Decisions

### A header-only or all-malformed SPARQL response is unreachable, never 'no consolidation'

**Decision**: `resolve` raises HttpUnreachable for zero rows on a non-empty basket and for responses where no row passes the shape check; check maps that to unreachable.

**Rationale**: The typed-literal trap returns HTTP 200 with zero rows; treating it as absence would declare every act unconsolidated (principle 4).

**Security Scan Note**: A 200 that is reported as unreachable is the intended reading of an empty CSV.

### Zero rows for one CELEX is unreachable even when last_version is None

**Decision**: check returns unreachable with "no consolidation in the graph" rather than fresh with version None.

**Rationale**: Commit 5851970: a source that has never been fetched must not read as fresh (principle 4); stricter than the research spec, which limited this to known instruments.

**Security Scan Note**: Intended asymmetry: fresh is only ever reported with a concrete version.

### Server rows are shape-checked before becoming paths or URLs; malformed rows are dropped, never index-split

**Decision**: consolCelex must match `_CONSOL` and consolDate `_ISO`; a row failing either is ignored.

**Rationale**: consolCelex becomes a directory name and a URL parameter (principle 10); `../../etc/passwd` in a CSV must not reach either.

**Security Scan Note**: This is the path/URL injection defence for CELLAR output; the regexes are the allowlist.

### Guards G1–G5 run before any write; failure leaves version unchanged

**Decision**: Any guard failure returns `FetchResult(refused=[guard])` with nothing written and `result.version` None, so `fetch.run` never advances last_version.

**Rationale**: EUR-Lex has returned 200 + site chrome for a missing language; the research note says server behaviour is unstable and the guards must not be weakened (principle 9: refuse loudly).

**Security Scan Note**: Refusing an HTTP 200 body is intended content validation, not a false negative.

### Only article divs are mirrored; preamble, recitals and annexes are not

**Decision**: `chunk()` collects only `id="art_N"` subdivisions; other parts of the consolidated text are not written.

**Rationale**: Per-article files are what regime obligations cite ("it says: Art. 30"; principle 1); v1 scope per plan B Task 7.

**Security Scan Note**: Missing recitals/annexes are a scope limit, not truncation; the `authentic_url` in every page points at the full instrument.

### Basket chunked at 100 CELEXes per GET, no POST

**Decision**: prefetch issues one GET per 100 CELEXes; a chunk's failure is recorded per CELEX.

**Rationale**: Ponytail comment in code: a basket over 100 has not been seen; POST is the upgrade path.

**Security Scan Note**: URL length is bounded by the chunk size; not an unbounded query string.

### Language availability is not pre-checked

**Decision**: The language SPARQL template was dropped (commit 6d0d2ec); a missing language version is caught by G1/G2/G4 on the HTML fetch.

**Rationale**: One fewer request per run; the guards already catch the failure mode.

**Security Scan Note**: Not a missing validation: `sources.validate` restricts `config.language` to the 24 known codes, and the guards refuse a wrong-language body.

## Related Specs

- [SPEC-007: HTTP client](./SPEC-007-http-client.md)
- [SPEC-008: HTML to markdown converter](./SPEC-008-html-to-markdown.md)
- [SPEC-009: Mirror store](./SPEC-009-mirror-store.md)
- [SPEC-010: Adapter contract, registry and shared guards](./SPEC-010-adapter-contract.md)
- [SPEC-015: fetch command](./SPEC-015-fetch-command.md)
- [SPEC-016: check command](./SPEC-016-check-command.md)
- [SPEC-026: sources.validate and refusals: the network-free gate before any request](../api/SPEC-026-sources-validate-refusals.md)
- [SPEC-031: Shipped references: method files, regime template, dimensions checklist and SPARQL template carry the method, never the law](../infra/SPEC-031-shipped-references-method-never-law.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Inferred from code, tests, research spec and design repo (D28); certainty 94 |
