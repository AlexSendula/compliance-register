# Specifications

Feature specs for compliance-register: what each part does and why it was designed that way.
Managed by `freya-spec-manager`; regenerate this index with `freya-spec-manager index`.

## Search

```bash
freya spec --query "<text>"          # full-text
freya spec --tag <tag>               # by tag
freya spec --category <category>     # by category
freya spec --sort-certainty --below 100
```

## Index

| ID | Title | Category | Status | Certainty |
|----|-------|----------|--------|-----------|
| SPEC-001 | [Profile: 15 dimensions, propose/confirm lifecycle, null blocks](features/SPEC-001-profile-dimensions-propose-confirm.md) | features | implemented | 93 |
| SPEC-002 | [Regimes: one file per regime, frontmatter validation, obligation parsing and counts](features/SPEC-002-regimes-one-file-per-regime.md) | features | implemented | 91 |
| SPEC-003 | [Pending: append-only pending.jsonl and resolutions.jsonl with replay-derived state](features/SPEC-003-pending-append-only-logs.md) | features | implemented | 93 |
| SPEC-004 | [Rescan: confirmed-answer snapshot, drift detection and regime-new/regime-gone entries](features/SPEC-004-rescan-snapshot-drift.md) | features | implemented | 91 |
| SPEC-005 | [Status: counts, profile age and pending totals, never a verdict](features/SPEC-005-status-counts-never-verdict.md) | features | implemented | 91 |
| SPEC-006 | [Search: BM25 over compliance markdown with a signature-keyed derived index](features/SPEC-006-search-bm25-signature-index.md) | features | implemented | 89 |
| SPEC-007 | [HTTP client: judged redirects, budgets, retries, robots, politeness](integration/SPEC-007-http-client.md) | integration | implemented | 93 |
| SPEC-008 | [HTML to markdown converter (vendored verbatim from docs-mirror)](integration/SPEC-008-html-to-markdown.md) | integration | implemented | 90 |
| SPEC-009 | [Mirror store: source directories, provenance frontmatter, per-source manifest](integration/SPEC-009-mirror-store.md) | integration | implemented | 92 |
| SPEC-010 | [Adapter contract, registry and shared guards](integration/SPEC-010-adapter-contract.md) | integration | implemented | 91 |
| SPEC-011 | [Sitemap adapter: lastmod signal with capped fan-out](integration/SPEC-011-sitemap-adapter.md) | integration | implemented | 90 |
| SPEC-012 | [Feed adapter: RSS/Atom, new entry id as the signal](integration/SPEC-012-feed-adapter.md) | integration | implemented | 85 |
| SPEC-013 | [Page-hash adapter: fetch to compare, and say so](integration/SPEC-013-pagehash-adapter.md) | integration | implemented | 88 |
| SPEC-014 | [EUR-Lex adapter: SPARQL resolve, consolidated CELEX signal, guards, per-article chunking](integration/SPEC-014-eurlex-adapter.md) | integration | implemented | 94 |
| SPEC-015 | [fetch command: acquire confirmed sources into the mirror](integration/SPEC-015-fetch-command.md) | integration | implemented | 92 |
| SPEC-016 | [check command: three-valued freshness, pending entries, date-passed and profile-stale](integration/SPEC-016-check-command.md) | integration | implemented | 93 |
| SPEC-017 | [CLI dispatch, exit-code contract and refusal boundary (main)](api/SPEC-017-cli-dispatch-exit-codes.md) | api | implemented | 92 |
| SPEC-018 | [init: idempotent scaffold of knowledge-base/compliance/](api/SPEC-018-init-scaffold.md) | api | implemented | 93 |
| SPEC-019 | [status, pending, search: read-only reports with --json raw and text escaped](api/SPEC-019-status-pending-search.md) | api | implemented | 90 |
| SPEC-020 | [resolve: record a named human's decision on a pending entry](api/SPEC-020-resolve.md) | api | implemented | 90 |
| SPEC-021 | [Validators: profile validate, regimes validate, sources validate (exit 1 with problems, network-free)](api/SPEC-021-validators.md) | api | implemented | 90 |
| SPEC-022 | [profile diff --against <file or git ref> with --end-of-options](api/SPEC-022-profile-diff.md) | api | implemented | 92 |
| SPEC-023 | [Watch commands at the CLI: fetch, check, rescan — exit relay, --today injection, text summaries](api/SPEC-023-watch-commands-cli.md) | api | implemented | 91 |
| SPEC-024 | [render.printable: escape at the terminal sink](api/SPEC-024-render-printable.md) | api | implemented | 94 |
| SPEC-025 | [sources.json model: Source dataclass, defaults, atomic load/save, typed SourcesError](api/SPEC-025-sources-model.md) | api | implemented | 92 |
| SPEC-026 | [sources.validate and refusals: the network-free gate before any request](api/SPEC-026-sources-validate-refusals.md) | api | implemented | 93 |
| SPEC-027 | [Launcher and preflight: Python ≥ 3.12, PyYAML and a non-empty CA store, or exit 2](api/SPEC-027-launcher-preflight.md) | api | implemented | 90 |
| SPEC-028 | [Paths: project root discovery and write containment](infra/SPEC-028-paths-root-discovery-and-write-containment.md) | infra | implemented | 92 |
| SPEC-029 | [Frontmatter: YAML block read/write, atomic save, ISO date normalisation](infra/SPEC-029-frontmatter-yaml-atomic-save-date-normalisation.md) | infra | implemented | 90 |
| SPEC-030 | [Packaging: SKILL.md contract, plugin manifests, path launcher and version](infra/SPEC-030-packaging-skill-md-plugin-launcher-version.md) | infra | implemented | 88 |
| SPEC-031 | [Shipped references: method files, regime template, dimensions checklist and SPARQL template carry the method, never the law](infra/SPEC-031-shipped-references-method-never-law.md) | infra | implemented | 85 |
