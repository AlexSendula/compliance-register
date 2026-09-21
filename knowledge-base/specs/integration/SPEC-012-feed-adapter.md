---
id: SPEC-012
title: "Feed adapter: RSS/Atom, new entry id as the signal"
category: integration
tags: [integration, mirror, adapter, feed, rss, atom]
status: implemented
certainty: 92
created: 2026-09-20
updated: 2026-09-21
related_code:
  - compliance_register/mirror/adapters/feed.py
  - tests/test_adapter_feed.py
  - tests/fixtures/feed.xml
intentional_decisions:
  - "Only new entry ids are a change; edits to known entries are not detected"
  - "Entries without an id or a link are dropped; a listing left with no entries is unreachable, not fresh"
behaviors:
  - behavior_id: BEH-119
    title: "check on an empty manifest is moved with the entry ids; fetch writes one page per entry; the next check is fresh"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_adapter_feed.py::test_check_then_fetch_then_fresh
  - behavior_id: BEH-120
    title: "a 5xx on the feed makes fetch refuse the listing without raising"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_adapter_feed.py::test_fetch_listing_failure_is_refused_not_raised
  - behavior_id: BEH-121
    title: "an Atom feed's entries are normalised with the alternate link and id"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_adapter_feed.py::test_an_atom_feeds_entries_are_normalised_with_the_alternate_link_and_id
  - behavior_id: BEH-122
    title: "an entry without a guid falls back to its link as id"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_adapter_feed.py::test_an_entry_without_a_guid_falls_back_to_its_link_as_id
  - behavior_id: BEH-123
    title: "a non-HTML entry page is refused by link and the other entries are still written"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_adapter_feed.py::test_a_non_html_entry_page_is_refused_by_link_and_the_other_entries_are_still_written
  - behavior_id: BEH-285
    title: "a feed that yields no usable entries is unreachable, never fresh"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_adapter_feed.py::test_feed_with_no_usable_entries_is_unreachable_not_fresh
---

# Feed adapter: RSS/Atom, new entry id as the signal

## What

`_entries` GETs the feed under the 5 MB listing budget through the DTD guard and normalises both Atom (`<entry>` with id, title, published/updated, first `<link>` whose rel is absent or `alternate`) and RSS 2.0 (`<item>` with guid or link as id, title, pubDate, link) into `{id, title, published, link}` dicts, dropping entries without an id or a link.

`check` reports moved with the ids not yet in the manifest, fresh when every id is known, unreachable on HTTP/robots/XML failure. `fetch` fetches the link of each unknown id (or all with `--force`), converts through htmlmd, refuses non-HTML by link, writes `<sha1(id)[:16]>.md` with `source_url`, `title` and `published` in the frontmatter, records the entry in the manifest keyed by id, and always saves the manifest in `finally`.

## Why

workflow.md tier table: feed is the tier for regulators such as AZOP that publish news as RSS/Atom; the change signal is "RSS/Atom entries", i.e. a new entry, and check downloads no page bodies (D18). Principle 9: a listing failure is a refusal string and the manifest is saved regardless. Keying by id rather than link means a republished link with a new guid is a new entry, which is how feeds signal change. Principle 4: an unreachable feed is unreachable, never fresh.

Atom parsing is pinned by an inline Atom fixture (BEH-121: `rel=self` before `rel=alternate`, `<updated>` only).

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-119 check on an empty manifest is moved with the entry ids; fetch writes one page per entry; the next check is fresh | accepted | `tests/test_adapter_feed.py::test_check_then_fetch_then_fresh` |
| BEH-120 a 5xx on the feed makes fetch refuse the listing without raising | accepted | `tests/test_adapter_feed.py::test_fetch_listing_failure_is_refused_not_raised` |
| BEH-121 an Atom feed's entries are normalised with the alternate link and id | accepted | `tests/test_adapter_feed.py::test_an_atom_feeds_entries_are_normalised_with_the_alternate_link_and_id` |
| BEH-122 an entry without a guid falls back to its link as id | accepted | `tests/test_adapter_feed.py::test_an_entry_without_a_guid_falls_back_to_its_link_as_id` |
| BEH-123 a non-HTML entry page is refused by link and the other entries are still written | accepted | `tests/test_adapter_feed.py::test_a_non_html_entry_page_is_refused_by_link_and_the_other_entries_are_still_written` |
| BEH-285 a feed that yields no usable entries is unreachable, never fresh | accepted | `tests/test_adapter_feed.py::test_feed_with_no_usable_entries_is_unreachable_not_fresh` |

Declarative decisions that are *not* executable are recorded under **Intentional
Design Decisions** below, not here.

## Intentional Design Decisions

### Only new entry ids are a change; edits to known entries are not detected

**Decision**: check compares ids to manifest keys only; an entry whose body or title changed under the same id is fresh.

**Rationale**: The feed tier's signal is the entry list (workflow.md); a regulator that edits published items in place is a page-hash source for that page. Principle 3: discover records the change signal per source and the human confirms the tier.

**Security Scan Note**: Looks like a missed change but is the tier's declared contract; discover records the change signal per source so the human chooses the tier.

### Entries without an id or a link are dropped; a listing left with no entries is unreachable, not fresh

**Decision**: An entry with no usable id or link is skipped; if that leaves the feed with no entries at all, `check` returns `unreachable` with `feed has no entries with an id and a link` rather than `fresh`.

**Rationale**: There is nothing to key or fetch; reporting each would be noise on every run.

**Security Scan Note**: Not data loss: such entries cannot be mirrored at all.

## Related Specs

- [SPEC-007: HTTP client](./SPEC-007-http-client.md)
- [SPEC-008: HTML to markdown converter](./SPEC-008-html-to-markdown.md)
- [SPEC-009: Mirror store](./SPEC-009-mirror-store.md)
- [SPEC-010: Adapter contract, registry and shared guards](./SPEC-010-adapter-contract.md)
- [SPEC-013: Page-hash adapter](./SPEC-013-pagehash-adapter.md)
- [SPEC-025: sources.json model: Source dataclass, defaults, atomic load/save, typed SourcesError](../api/SPEC-025-sources-model.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Inferred from code, tests and design repo (D18, D21); certainty 85 — Atom path untested |
| 2026-09-21 | A listing with no usable entries is `unreachable`, not `fresh`; BEH-285 added | G3 contradiction check, principle 4 |
| 2026-09-21 | Behaviours promoted by Alex: tested → accepted, untested → confirmed (test owed) | First behaviour review after the freya wrap-up |
| 2026-09-21 | Tests written for BEH-121, BEH-122, BEH-123; promoted confirmed → accepted | tests owed |
