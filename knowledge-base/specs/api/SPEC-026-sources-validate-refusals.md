---
id: SPEC-026
title: 'sources.validate and refusals: the network-free gate before any request'
category: api
tags: [api, sources, validate, ssrf, https, D7, D28, D29, principle-3, principle-8]
status: implemented
certainty: 93
created: 2026-09-20
updated: 2026-09-21
related_code:
  - compliance_register/sources.py
  - compliance_register/mirror/adapters/__init__.py
  - compliance_register/mirror/adapters/eurlex.py
  - compliance_register/check.py
  - compliance_register/fetch.py
  - tests/test_sources.py
  - tests/test_check.py
  - tests/test_fetch.py
intentional_decisions:
  - "Private, loopback, link-local, reserved and unspecified addresses are refused in allowed_hosts"
  - "Only https origin URLs are accepted"
  - "api tier requires an explicit adapter and the registry is closed"
  - "validate returns a list and never raises; refusals aggregates per source"
  - "A --source that names an unconfirmed source is refused; an unnamed run silently takes only confirmed ones"
behaviors:
  - behavior_id: BEH-220
    title: 'localhost, 127.0.0.1, ::1, 10.0.0.5, 192.168.1.1, 169.254.169.254, 0.0.0.0 and fe80::1 in allowed_hosts each produce an allowed_hosts problem naming the host'
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_sources.py::test_validate_refuses_private_hosts
  - behavior_id: BEH-221
    title: 'A public IP and a public hostname in allowed_hosts validate clean'
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_sources.py::test_validate_allows_public_ip_and_names
  - behavior_id: BEH-222
    title: 'An http:// url produces a problem mentioning https'
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_sources.py::test_validate_requires_https
  - behavior_id: BEH-223
    title: 'An unknown adapter name (e.g. bwb) is refused; each registry name is accepted'
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_sources.py::test_validate_refuses_unknown_adapter
  - behavior_id: BEH-224
    title: 'api tier with no adapter is refused with a message naming eurlex; licence.redistribute ''yes'' is refused'
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_sources.py::test_validate_rules
  - behavior_id: BEH-225
    title: 'eurlex config: celex must match the base CELEX pattern and language must be a known code; language is optional'
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_sources.py::test_validate_eurlex_celex_and_language_shape
  - behavior_id: BEH-226
    title: 'allowed_hosts that is a dict, a list with a non-string, a list with an empty string, or an int is refused'
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_sources.py::test_allowed_hosts_string_is_wrapped_and_bad_shapes_refused
  - behavior_id: BEH-227
    title: 'check with a validation problem exits 2 and the fake opener records zero requests'
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_check.py::test_validation_problem_exits_2_before_any_request
  - behavior_id: BEH-228
    title: 'fetch --source naming an unconfirmed source exits 2 with ''required confirmation missing'' and no request'
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_fetch.py::test_named_unconfirmed_source_is_refused
---

# sources.validate and refusals: the network-free gate before any request

## What

`sources.validate(s)` returns a list of `<id>: <problem>` strings and never raises. It refuses:

- a tier outside `TIERS`;
- an `api` tier without an explicit adapter (message names `eurlex`);
- an adapter outside the registry `adapters.NAMES` (`eurlex`, `sitemap`, `feed`, `pagehash`);
- a kind outside `KINDS`, a status outside `STATUSES`;
- a licence whose `redistribute` is not a bool;
- a url whose scheme is not `https`;
- an `allowed_hosts` that is not a list of non-empty strings;
- any `allowed_hosts` entry that is `localhost` or an IP that is loopback, private, link-local, reserved or unspecified (IPv4 and IPv6, brackets stripped).

For adapter `eurlex` it also requires `config.celex` to match the base CELEX pattern and `config.language`, when present, to be a known two-letter EU language code (a key of `eurlex.LANG3`, e.g. `EN`; the three-letter value is what guard G4 compares).

`sources.refusals(chosen, ids)` runs `validate` on each chosen source and, when ids were named on the command line, adds `required confirmation missing (status X)` for any source not confirmed; `check` and `fetch` call it first and return exit 2 with no request when it is non-empty.

## Why

Principle 3 (confirm before it counts) and D7: a named-but-unconfirmed source is refused rather than fetched. D29: validation failure before any request is a refusal (2), distinct from a failed fetch (1).

The private-host rule closes the SSRF path where a source's `allowed_hosts` (which bounds redirects) could point the fetcher at `169.254.169.254` or a loopback service (commit dcbc014). https-only is the plan-B invariant "never https→http" applied at the origin URL. Refusing an unknown adapter here rather than letting `adapters.get` raise `KeyError` inside the loop over sources keeps principle 9's "nothing raises inside the loop" (commit 35691ce). D28: an `api` adapter carries only its protocol endpoint, so `api` tier must name one explicitly.

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-220 localhost, 127.0.0.1, ::1, 10.0.0.5, 192.168.1.1, 169.254.169.254, 0.0.0.0 and fe80::1 in allowed_hosts each produce an allowed_hosts problem naming the host | accepted | `tests/test_sources.py::test_validate_refuses_private_hosts` |
| BEH-221 A public IP and a public hostname in allowed_hosts validate clean | accepted | `tests/test_sources.py::test_validate_allows_public_ip_and_names` |
| BEH-222 An http:// url produces a problem mentioning https | accepted | `tests/test_sources.py::test_validate_requires_https` |
| BEH-223 An unknown adapter name (e.g. bwb) is refused; each registry name is accepted | accepted | `tests/test_sources.py::test_validate_refuses_unknown_adapter` |
| BEH-224 api tier with no adapter is refused with a message naming eurlex; licence.redistribute 'yes' is refused | accepted | `tests/test_sources.py::test_validate_rules` |
| BEH-225 eurlex config: celex must match the base CELEX pattern and language must be a known code; language is optional | accepted | `tests/test_sources.py::test_validate_eurlex_celex_and_language_shape` |
| BEH-226 allowed_hosts that is a dict, a list with a non-string, a list with an empty string, or an int is refused | accepted | `tests/test_sources.py::test_allowed_hosts_string_is_wrapped_and_bad_shapes_refused` |
| BEH-227 check with a validation problem exits 2 and the fake opener records zero requests | accepted | `tests/test_check.py::test_validation_problem_exits_2_before_any_request` |
| BEH-228 fetch --source naming an unconfirmed source exits 2 with 'required confirmation missing' and no request | accepted | `tests/test_fetch.py::test_named_unconfirmed_source_is_refused` |

## Intentional Design Decisions

### Private, loopback, link-local, reserved and unspecified addresses are refused in allowed_hosts

**Decision**: `mirror.http.is_private_host` (shared with the per-hop resolution check) rejects `localhost` and any `ipaddress` literal that is not globally routable or is multicast; public IPs and hostnames pass here.

**Rationale**: `allowed_hosts` bounds where redirects may go; without this rule a `sources.json` entry could steer a fetch at a metadata service or a local daemon. Hostnames are not resolved here (no DNS in validate, which stays offline); `Http` resolves every hop before the request and applies the same test to the answers (SPEC-007, SEC-003).

**Security Scan Note**: This is the SSRF mitigation at the configuration boundary. Hostnames are resolved and checked in `compliance_register/mirror/http.py` (`_refuse_private_resolution`), not here.

### Only https origin URLs are accepted

**Decision**: `urlsplit(url).scheme != 'https'` is a validation problem; there is no allow-http flag.

**Rationale**: Plan B: never https→http, at most 5 redirect hops, hosts limited to `allowed_hosts`. Regulators publish over https; an http source would be an unauthenticated legal text.

**Security Scan Note**: n/a

### api tier requires an explicit adapter and the registry is closed

**Decision**: No default adapter for `api`; adapter names outside `NAMES` are refused at validate time.

**Rationale**: D28: the `api` adapter is the one place a protocol endpoint may live, so it must be named on purpose. A closed registry means a typo cannot silently fall back to page-hash.

**Security Scan Note**: n/a

### validate returns a list and never raises; refusals aggregates per source

**Decision**: Every problem is collected and joined with `; ` per source id.

**Rationale**: Principle 9: the operator gets every reason at once, and the CLI can print them and exit without a traceback.

**Security Scan Note**: n/a

### A --source that names an unconfirmed source is refused; an unnamed run silently takes only confirmed ones

**Decision**: `refusals` adds the confirmation problem only when ids were given; without ids, unconfirmed sources are simply not chosen.

**Rationale**: Naming a source is an explicit request, so refusing loudly is right; a bulk run must not fail because a proposed entry is still pending a human.

**Security Scan Note**: n/a

## Related Specs

- [SPEC-021: Validators: profile validate, regimes validate, sources validate](./SPEC-021-validators.md)
- [SPEC-023: Watch commands at the CLI: fetch, check, rescan](./SPEC-023-watch-commands-cli.md)
- [SPEC-025: sources.json model](./SPEC-025-sources-model.md)
- [SPEC-007: HTTP client: judged redirects, budgets, retries, robots, politeness](../integration/SPEC-007-http-client.md)
- [SPEC-010: Adapter contract, registry and shared guards](../integration/SPEC-010-adapter-contract.md)
- [SPEC-014: EUR-Lex adapter: SPARQL resolve, consolidated CELEX signal, guards, per-article chunking](../integration/SPEC-014-eurlex-adapter.md)
- [SPEC-015: fetch command: acquire confirmed sources into the mirror](../integration/SPEC-015-fetch-command.md)
- [SPEC-016: check command: three-valued freshness, pending entries, date-passed and profile-stale](../integration/SPEC-016-check-command.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Generated from codebase scan by freya-spec-manager |
| 2026-09-20 | `config.language` is a two-letter key of `eurlex.LANG3`, not a three-letter code | Cross-check against `sources.validate` and `references/method-discover-sources.md` |
| 2026-09-21 | Behaviours promoted by Alex: tested → accepted, untested → confirmed (test owed) | First behaviour review after the freya wrap-up |
| 2026-09-21 | `_is_private_host` moved to `mirror.http.is_private_host`, reused by the robots.txt redirect path | nieuwbouw-tracker trial review |
| 2026-09-21 | is_private_host is now not-global-or-multicast; hostname resolution happens per hop in Http (SEC-003) | security finding SEC-003 |
