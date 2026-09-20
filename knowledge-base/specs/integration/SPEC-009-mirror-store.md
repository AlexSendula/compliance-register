---
id: SPEC-009
title: "Mirror store: source directories, provenance frontmatter, per-source manifest"
category: integration
tags: [integration, mirror, store, manifest, licence, gitignore, paths]
status: implemented
certainty: 92
created: 2026-09-20
updated: 2026-09-21
related_code:
  - compliance_register/mirror/store.py
  - compliance_register/paths.py
  - compliance_register/frontmatter.py
  - tests/test_store.py
  - tests/test_poisoned_files_do_not_brick.py
intentional_decisions:
  - ".private/ routing and .gitignore maintenance on every non-redistributable write"
  - "content_hash ignores whitespace"
  - "Poisoned manifests are tolerated, not fatal"
  - "needs_refresh is conservative without a lastmod on both sides"
  - "Manifest saved atomically"
behaviors:
  - behavior_id: BEH-093
    title: "a redistributable source maps to mirror/<jur>/<id>; a non-redistributable one to mirror/.private/<jur>/<id>"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_store.py::test_source_dir_public_and_private
  - behavior_id: BEH-094
    title: "write_page adds source, content_hash, licence, licence_name and attribution to the frontmatter"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_store.py::test_write_page_adds_provenance
  - behavior_id: BEH-095
    title: "licence_name is None when the licence dict has no name"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_store.py::test_write_page_licence_name_is_optional
  - behavior_id: BEH-096
    title: "a relpath that escapes the source directory raises UnsafePath and writes nothing"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_store.py::test_write_page_refuses_escape
  - behavior_id: BEH-097
    title: "a manifest round-trips through save_manifest/load_manifest and is {} when absent"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_store.py::test_manifest_roundtrip
  - behavior_id: BEH-098
    title: "needs_refresh follows the hash-first, then both-lastmod rule"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_store.py::test_needs_refresh_rules
  - behavior_id: BEH-099
    title: "content_hash is identical for texts that differ only in whitespace"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_store.py::test_content_hash_ignores_whitespace
  - behavior_id: BEH-100
    title: "writing a private page ensures mirror/.gitignore lists .private/ exactly once and preserves existing lines; a public page does not touch it"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_store.py::test_private_page_ensures_mirror_gitignore
  - behavior_id: BEH-101
    title: "manifest rows that are not dicts are dropped on load and treated as needing refresh"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_poisoned_files_do_not_brick.py::test_manifest_rows_that_are_not_dicts_are_dropped
  - behavior_id: BEH-102
    title: "a jurisdiction or source id that is not a safe path component raises UnsafePath"
    state: confirmed
    level: unit
    adapter: pytest
---

# Mirror store: source directories, provenance frontmatter, per-source manifest

## What

`source_dir(cdir, source)` is `mirror/<jurisdiction lowercased>/<source id>`, or `mirror/.private/<jur>/<id>` when `licence.redistribute` is false; both components pass `paths.safe_component`.

`write_page` contains the relative path under that directory via `paths.contained`, ensures `mirror/.gitignore` lists `.private/` when the source is non-redistributable, and saves a markdown file whose frontmatter carries `source`, `source_url`, `retrieved_at`, `content_hash`, `licence`, `licence_name` and `attribution` plus adapter metadata. `content_hash` is SHA-256 of the text with all whitespace runs collapsed to single spaces.

`MANIFEST.json` per source is loaded tolerantly (missing, unparsable or non-dict file → `{}`; non-dict rows dropped) and saved atomically via a temp file and `os.replace`. `needs_refresh(entry, lastmod, hash)` returns True for a missing or non-dict entry, compares hashes when a hash is given, and otherwise returns True unless both sides carry a lastmod and they are equal.

## Why

Principle 7 / D20 and D23: data lives in the project under `knowledge-base/compliance/`, committed and licence-gated; non-redistributable text goes to `.private/` which is git-ignored. Commit 88ae9ab: the `.gitignore` is (re)asserted on every private write because a clone where `init` never ran must not commit `.private/` on the next `git add -A`. Principle 10: jurisdiction, id and relpath come from sources.json and adapters, so every path component is checked and contained. Principle 9 and docs-mirror SEC-049/050: a corrupt manifest must not deny the command; a dropped row simply means the page is refetched. Whitespace-insensitive hashing stops a re-rendered page with identical text from counting as a move. Frontmatter provenance (source, date, version, licence, attribution) is what lets a regime file cite a mirrored page (principle 3: cite, date) and lets CC-BY attribution travel with the text.

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-093 a redistributable source maps to mirror/<jur>/<id>; a non-redistributable one to mirror/.private/<jur>/<id> | accepted | `tests/test_store.py::test_source_dir_public_and_private` |
| BEH-094 write_page adds source, content_hash, licence, licence_name and attribution to the frontmatter | accepted | `tests/test_store.py::test_write_page_adds_provenance` |
| BEH-095 licence_name is None when the licence dict has no name | accepted | `tests/test_store.py::test_write_page_licence_name_is_optional` |
| BEH-096 a relpath that escapes the source directory raises UnsafePath and writes nothing | accepted | `tests/test_store.py::test_write_page_refuses_escape` |
| BEH-097 a manifest round-trips through save_manifest/load_manifest and is {} when absent | accepted | `tests/test_store.py::test_manifest_roundtrip` |
| BEH-098 needs_refresh follows the hash-first, then both-lastmod rule | accepted | `tests/test_store.py::test_needs_refresh_rules` |
| BEH-099 content_hash is identical for texts that differ only in whitespace | accepted | `tests/test_store.py::test_content_hash_ignores_whitespace` |
| BEH-100 writing a private page ensures mirror/.gitignore lists .private/ exactly once and preserves existing lines; a public page does not touch it | accepted | `tests/test_store.py::test_private_page_ensures_mirror_gitignore` |
| BEH-101 manifest rows that are not dicts are dropped on load and treated as needing refresh | accepted | `tests/test_poisoned_files_do_not_brick.py::test_manifest_rows_that_are_not_dicts_are_dropped` |
| BEH-102 a jurisdiction or source id that is not a safe path component raises UnsafePath | confirmed | — (test owed) |

Declarative decisions that are *not* executable are recorded under **Intentional
Design Decisions** below, not here.

## Intentional Design Decisions

### .private/ routing and .gitignore maintenance on every non-redistributable write

**Decision**: A source with `licence.redistribute` false is written under `mirror/.private/`; `write_page` appends `.private/` to `mirror/.gitignore` if it is not already a line there, leaving any existing content intact.

**Rationale**: Principle 7 / D20: licence enforced in code; `init` writes the `.gitignore` but a fresh clone may never have run `init` (commit 88ae9ab).

**Security Scan Note**: Writing to a `.gitignore` from library code is the intended licence gate, idempotent (one line, checked by exact line match), and touched only for private sources.

### content_hash ignores whitespace

**Decision**: The hash covers `' '.join(text.split())`, not the raw bytes.

**Rationale**: A regulator re-rendering the same text with different indentation or line wrapping is not a legal change; reporting it as "moved" would spam pending.jsonl (principle 6).

**Security Scan Note**: This is a change-detection fingerprint, not an integrity hash; SHA-256 over normalised text is deliberate.

### Poisoned manifests are tolerated, not fatal

**Decision**: `load_manifest` returns `{}` for a missing, unreadable or non-dict file and drops rows that are not dicts; `needs_refresh` treats such rows as absent (refetch).

**Rationale**: Principle 9: one bad file must not prevent check/fetch from running; the worst case is one extra fetch.

**Security Scan Note**: The silent drop is intended; the affected page is refetched on the next fetch. Not an error-swallowing bug.

### needs_refresh is conservative without a lastmod on both sides

**Decision**: If either the manifest entry or the listing lacks a lastmod (and no hash is given), the page needs refresh.

**Rationale**: "Without a timestamp on both sides we cannot prove it is unchanged" — principle 4 applied to freshness bookkeeping.

**Security Scan Note**: Over-fetching is the safe direction; a scanner should not read this as a missing cache.

### Manifest saved atomically

**Decision**: `save_manifest` writes to a `mkstemp` file in the same directory and `os.replace()`s it over `MANIFEST.json`; the temp file is unlinked on failure.

**Rationale**: A crash mid-write must not leave a half-written manifest that `load_manifest` would then treat as empty and refetch everything.

**Security Scan Note**: Temp file is created with `mkstemp` (0600) in the target directory; this is the standard atomic-write shape.

## Related Specs

- [SPEC-011: Sitemap adapter](./SPEC-011-sitemap-adapter.md)
- [SPEC-012: Feed adapter](./SPEC-012-feed-adapter.md)
- [SPEC-013: Page-hash adapter](./SPEC-013-pagehash-adapter.md)
- [SPEC-014: EUR-Lex adapter](./SPEC-014-eurlex-adapter.md)
- [SPEC-015: fetch command](./SPEC-015-fetch-command.md)
- [SPEC-006: Search: BM25 over compliance markdown with a signature-keyed derived index](../features/SPEC-006-search-bm25-signature-index.md)
- [SPEC-025: sources.json model: Source dataclass, defaults, atomic load/save, typed SourcesError](../api/SPEC-025-sources-model.md)
- [SPEC-028: Paths: project root discovery and write containment](../infra/SPEC-028-paths-root-discovery-and-write-containment.md)
- [SPEC-029: Frontmatter: YAML block read/write, atomic save, ISO date normalisation](../infra/SPEC-029-frontmatter-yaml-atomic-save-date-normalisation.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Inferred from code, tests and design repo (D20, D23); certainty 92 |
| 2026-09-21 | Behaviours promoted by Alex: tested → accepted, untested → confirmed (test owed) | First behaviour review after the freya wrap-up |
