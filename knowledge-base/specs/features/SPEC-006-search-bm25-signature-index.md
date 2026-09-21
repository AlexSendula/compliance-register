---
id: SPEC-006
title: "Search: BM25 over compliance markdown with a signature-keyed derived index"
category: features
tags: [search, bm25, index, tokenizer, docs-mirror, containment, escape-at-sink]
status: implemented
certainty: 89
created: 2026-09-20
updated: 2026-09-20
related_code:
  - compliance_register/search.py
  - compliance_register/paths.py
  - compliance_register/render.py
  - compliance_register/cli.py
  - tests/test_search.py
  - tests/test_cli.py
intentional_decisions:
  - "Tokenizer is a verbatim copy of docs-mirror's, not an import"
  - "mirror/.private/ is indexed; dot-files are not"
  - "A corrupt or stale index is rebuilt silently"
  - "Index paths are containment-checked before any snippet read"
  - "search() returns raw snippets; the CLI escapes"
  - "Signature is size + mtime_ns, not a content hash"
behaviors:
  - behavior_id: BEH-050
    title: "search ranks the regime whose obligation text matches the query first and labels it kind=regime"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_search.py::test_search_finds_the_obligation
  - behavior_id: BEH-051
    title: "editing an indexed file changes the signature and the next search rebuilds the index and finds the new text"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_search.py::test_index_rebuilds_when_file_changes
  - behavior_id: BEH-052
    title: "tokenize drops stop words and terms shorter than 2 characters"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_search.py::test_stop_words_dropped
  - behavior_id: BEH-053
    title: "tokenize keeps accented and non-Latin words intact"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_search.py::test_tokenize_keeps_accented_words
  - behavior_id: BEH-054
    title: "pages under mirror/.private/ are searchable while dot-files are excluded"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_search.py::test_private_mirror_pages_are_searchable
  - behavior_id: BEH-055
    title: "a hit whose indexed path resolves outside the compliance dir is dropped before its file is read"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_search.py::test_poisoned_index_path_outside_cdir_is_skipped
  - behavior_id: BEH-056
    title: "`search <query> --json` exits 0 and returns hits with absolute paths"
    state: proposed
    level: component
    adapter: pytest
    locator: tests/test_cli.py::test_search_cli
  - behavior_id: BEH-057
    title: "`search` terminal output escapes ESC and U+202E in snippets and paths"
    state: proposed
    level: component
    adapter: pytest
    locator: tests/test_cli.py::test_search_output_escapes_terminal_controls
  - behavior_id: BEH-058
    title: "a query that tokenizes to nothing returns no hits"
    state: proposed
    level: unit
    adapter: pytest
  - behavior_id: BEH-059
    title: "--kind filters hits to profile, regime or mirror documents"
    state: proposed
    level: unit
    adapter: pytest
  - behavior_id: BEH-060
    title: "a corrupt or wrong-version .search-index.json is rebuilt rather than reported"
    state: proposed
    level: unit
    adapter: pytest
---

# Search: BM25 over compliance markdown with a signature-keyed derived index

## What

`search.search(cdir, query, k=5, kind=None)` ranks every `*.md` under `knowledge-base/compliance/` (recursively, including `mirror/.private/`, excluding files whose name starts with a dot) with BM25 (k1=1.5, b=0.75) over whole files and returns up to `k` `Hit(path, score, kind, snippet)` sorted by descending score then path.

Query and documents share one tokenizer copied verbatim from docs-mirror: casefold, `\w+` Unicode words, minimum length 2, a fixed English stop list. `kind` is derived from the relative path (`profile.md` → profile, `regimes/` → regime, `mirror/` → mirror, else other) and can filter.

The index lives at `.search-index.json` with a `version` and a `signature`, the sha256 over `relpath|size|mtime_ns` of every indexed file; `load_table` reuses the file only when both match and otherwise rebuilds and rewrites it, treating a missing, corrupt or unparsable index the same way. Before a hit's snippet is read, its recorded path is run through `paths.contained(cdir, …)`; a path resolving outside the compliance dir is dropped. The snippet is a 160-character window around the first matching term.

The CLI's `search <query> [-k N] [--kind …] [--json]` escapes path and snippet through `render.printable`, prints `no hits — try the source's own vocabulary` on an empty result, and exits 0.

## Why

The skill needs "where does it say so" over regime files and mirrored law without a dependency or a model, so it borrows docs-mirror's BM25 design (workflow.md, ADR-012: "search ranks; it does not understand"). The tokenizer is one function for query and document because two tokenizers that disagree by one rule produce an index that silently cannot match its own queries; it is copied verbatim rather than imported because the skill ships with stdlib + PyYAML only (Principle 11).

The index is a derived cache keyed on a cheap file signature so it rebuilds itself on any edit and is gitignored by `init` (workflow.md), which is also why a corrupt index is rebuilt rather than reported. `mirror/.private/` is searched even though it is gitignored: the gitignore is about redistribution, not local use, and the non-redistributable sources are the ones most worth quoting (Principle 7, D20). Mirrored text is untrusted, so the index's recorded paths pass containment before any file is opened and the terminal output passes `printable` (Principle 10).

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-050 search ranks the regime whose obligation text matches the query first and labels it kind=regime | proposed | `tests/test_search.py::test_search_finds_the_obligation` |
| BEH-051 editing an indexed file changes the signature and the next search rebuilds the index and finds the new text | proposed | `tests/test_search.py::test_index_rebuilds_when_file_changes` |
| BEH-052 tokenize drops stop words and terms shorter than 2 characters | proposed | `tests/test_search.py::test_stop_words_dropped` |
| BEH-053 tokenize keeps accented and non-Latin words intact | proposed | `tests/test_search.py::test_tokenize_keeps_accented_words` |
| BEH-054 pages under mirror/.private/ are searchable while dot-files are excluded | proposed | `tests/test_search.py::test_private_mirror_pages_are_searchable` |
| BEH-055 a hit whose indexed path resolves outside the compliance dir is dropped before its file is read | proposed | `tests/test_search.py::test_poisoned_index_path_outside_cdir_is_skipped` |
| BEH-056 `search <query> --json` exits 0 and returns hits with absolute paths | proposed | `tests/test_cli.py::test_search_cli` |
| BEH-057 `search` terminal output escapes ESC and U+202E in snippets and paths | proposed | `tests/test_cli.py::test_search_output_escapes_terminal_controls` |
| BEH-058 a query that tokenizes to nothing returns no hits | proposed | — (test owed) |
| BEH-059 --kind filters hits to profile, regime or mirror documents | proposed | — (test owed) |
| BEH-060 a corrupt or wrong-version .search-index.json is rebuilt rather than reported | proposed | — (test owed) |

Declarative decisions that are *not* executable are recorded under **Intentional
Design Decisions** below, not here.

## Intentional Design Decisions

### Tokenizer is a verbatim copy of docs-mirror's, not an import

**Decision**: `_STOP`, `_WORD` and `tokenize` are copied between `--- copied verbatim ---` markers and are the single tokenizer for both queries and documents.

**Rationale**: No new runtime dependency (Principle 11); one rule for query and document so the index can always match its own queries; verbatim so the two projects' search behaves identically.

**Security Scan Note**: Duplicate-code detectors will flag this; do not dedupe by importing docs-mirror or by "improving" the stop list independently.

### mirror/.private/ is indexed; dot-files are not

**Decision**: `_docs` walks every `*.md` under cdir and skips only files whose own name starts with a dot; `.private/` as a directory is included.

**Rationale**: gitignore governs committing, not local use (Principle 7, D20). The dot-file rule keeps the index itself and editor temp files out.

**Security Scan Note**: Non-redistributable text appearing in local search results is intended; it never leaves the machine through this path.

### A corrupt or stale index is rebuilt silently

**Decision**: `load_table` catches `ValueError`/`OSError`, and any version or signature mismatch, by rebuilding and rewriting `.search-index.json`.

**Rationale**: The index is derived from the markdown and never committed; nothing is lost by rebuilding, unlike pending.jsonl where a bad row is counted (SPEC-003).

**Security Scan Note**: Swallowed parse errors here are safe because the file is a cache; contrast with pending.py where the same shape is counted.

### Index paths are containment-checked before any snippet read

**Decision**: For each top-k hit, `paths.contained(cdir, Path(h.path))` runs before `_snippet` opens the file; an `UnsafePath` drops the hit.

**Rationale**: The index is on disk and writable; a poisoned `path` entry must not read an arbitrary file into a snippet (Principle 10, escape at the sink and containment).

**Security Scan Note**: This is the guard against index-driven file disclosure; covered by tests/test_search.py::test_poisoned_index_path_outside_cdir_is_skipped.

### search() returns raw snippets; the CLI escapes

**Decision**: `Hit.snippet` and `Hit.path` are unescaped; `cmd_search` passes both through `render.printable` before printing.

**Rationale**: Escape at the sink (Principle 10, docs-mirror ADR-008): a future non-terminal consumer (agent front end, `--json`) gets the raw text and applies its own sink rule.

**Security Scan Note**: Do not flag search.py for printing untrusted text; it prints nothing. The terminal sink is in cli.py and tested.

### Signature is size + mtime_ns, not a content hash

**Decision**: `signature` hashes `relpath|st_size|st_mtime_ns` per file, never file contents.

**Rationale**: Cheap enough to run on every search call; an edit that preserves both size and nanosecond mtime is the accepted ceiling.

**Security Scan Note**: A stale index cannot leak anything beyond what the previous build already indexed under the same dir.

## Related Specs

- [SPEC-001: Profile: 15 dimensions, propose/confirm lifecycle, null blocks](./SPEC-001-profile-dimensions-propose-confirm.md) — `profile.md` is indexed as kind `profile`
- [SPEC-002: Regimes: one file per regime, frontmatter validation, obligation parsing and counts](./SPEC-002-regimes-one-file-per-regime.md) — `regimes/*.md` are indexed as kind `regime`
- [SPEC-003: Pending: append-only pending.jsonl and resolutions.jsonl](./SPEC-003-pending-append-only-logs.md) — contrast: a bad row there is counted, a bad index here is rebuilt
- [SPEC-009: Mirror store: source directories, provenance frontmatter, per-source manifest](../integration/SPEC-009-mirror-store.md)
- [SPEC-019: status, pending, search: read-only reports with --json raw and text escaped](../api/SPEC-019-status-pending-search.md)
- [SPEC-028: Paths: project root discovery and write containment](../infra/SPEC-028-paths-root-discovery-and-write-containment.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Generated from codebase scan; certainty 89 |
