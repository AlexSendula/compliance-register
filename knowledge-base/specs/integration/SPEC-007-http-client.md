---
id: SPEC-007
title: "HTTP client: judged redirects, budgets, retries, robots, politeness"
category: integration
tags: [integration, mirror, http, robots, redirects, politeness, ssrf]
status: implemented
certainty: 93
created: 2026-09-20
updated: 2026-09-21
related_code:
  - compliance_register/mirror/http.py
  - compliance_register/__init__.py
  - tests/test_http.py
  - tests/fakehttp.py
  - tests/test_check.py
intentional_decisions:
  - "A redirect to http:// is upgraded to https:// and followed; nothing is ever requested in the clear"
  - "Every hop is resolved before the request and refused if any address is not globally routable; the TTL-0 rebinding window is an accepted residual"
  - "https only: a plaintext http URL from a listing or config is refused, not fetched"
  - "robots.txt has no bypass switch; a disallow is a refusal, not a retry with another UA"
  - "robots.txt is read per RFC 9309: redirects followed even to another host, 4xx means no rules, 5xx or a network failure makes the host unreachable"
  - "robots.txt rules are matched per RFC 9309 — longest pattern wins, allow wins a tie — not by urllib.robotparser's first match"
  - "robots.txt rules are evaluated against our own product token as well as the User-Agent presented"
  - "Politeness clock is process-global mutable state and always sleeps the full delay"
  - "Over-budget bodies are refused, never truncated"
  - "A browser User-Agent policy exists per source, chosen by a human"
  - "Retries are few, fixed and only on 429/5xx or transport errors"
behaviors:
  - behavior_id: BEH-061
    title: "a 200 response returns status, body and final URL"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_get_ok
  - behavior_id: BEH-062
    title: "a redirect to a host in allowed_hosts is followed and the final URL is reported"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_follows_same_host_redirect
  - behavior_id: BEH-063
    title: "a redirect to a host not in allowed_hosts raises HttpRefused"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_refuses_cross_host_redirect
  - behavior_id: BEH-064
    title: "a redirect to http:// is followed at https:// and the http URL is never requested"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_http_redirect_is_upgraded_to_https_and_never_requested_in_the_clear
  - behavior_id: BEH-065
    title: "a body larger than the budget raises HttpRefused instead of being truncated"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_refuses_over_budget
  - behavior_id: BEH-066
    title: "a per-call max_bytes lowers, never raises, the client budget"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_per_call_max_bytes_overrides_client_budget
  - behavior_id: BEH-067
    title: "a 5xx is retried twice (three requests total) then raised as HttpUnreachable"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_retries_then_unreachable
  - behavior_id: BEH-068
    title: "a URL disallowed by the host's robots.txt raises HttpRefused before it is requested"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_robots_disallow_refuses
  - behavior_id: BEH-069
    title: "Http exposes no constructor parameter that bypasses robots.txt"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_robots_has_no_bypass_switch
  - behavior_id: BEH-070
    title: "robots.txt is fetched from scheme://hostname[:port]/robots.txt, dropping userinfo from the netloc"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_robots_url_from_hostname_and_port_not_netloc
  - behavior_id: BEH-071
    title: "a second request to the same host sleeps delay_seconds first"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_delay_between_same_host_requests
  - behavior_id: BEH-072
    title: "the politeness clock applies across different Http instances for the same host"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_politeness_clock_is_shared_across_clients
  - behavior_id: BEH-073
    title: "a Location with CRLF, NUL or an unparseable host raises HttpRefused, not a traceback"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_hostile_location_is_refused_not_raised
  - behavior_id: BEH-074
    title: "an http.client.HTTPException from the server side becomes HttpUnreachable"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_server_side_http_exception_is_unreachable
  - behavior_id: BEH-075
    title: "the three User-Agent policies resolve to the documented strings and default carries version and contact"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_user_agent_strings
  - behavior_id: BEH-076
    title: "a robots.txt opener that raises makes the source unreachable and the run still completes"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_check.py::test_robots_opener_raising_is_unreachable_and_run_completes
  - behavior_id: BEH-276
    title: "a redirected robots.txt is followed and its rules applied"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_robots_redirect_is_followed_and_rules_applied
  - behavior_id: BEH-277
    title: "a 5xx on robots.txt makes the host unreachable and the page is never requested"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_robots_5xx_is_unreachable_not_fetched
  - behavior_id: BEH-278
    title: "a 4xx on robots.txt means no rules"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_robots_4xx_means_no_rules
  - behavior_id: BEH-279
    title: "a Disallow for the compliance-register product token holds under every User-Agent policy"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_robots_disallow_for_our_product_token_holds_under_browser_ua
  - behavior_id: BEH-077
    title: "more than MAX_HOPS (5) redirects raises HttpRefused"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_more_than_max_hops_redirects_raises_http_refused
  - behavior_id: BEH-078
    title: "a redirect without a Location header raises HttpRefused"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_a_redirect_without_a_location_header_raises_http_refused
  - behavior_id: BEH-079
    title: "a non-http(s) scheme (file:, ftp:) raises HttpRefused before any request"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_a_non_http_scheme_raises_http_refused_before_any_request
  - behavior_id: BEH-080
    title: "a 429 is retried like a 5xx"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_a_429_is_retried_like_a_5xx
  - behavior_id: BEH-081
    title: "response header keys are title-cased so Content-Type lookups are case-insensitive"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_response_header_keys_are_title_cased
  - behavior_id: BEH-287
    title: "a plaintext http URL is refused before any request, wherever it came from"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_plain_http_is_refused_even_when_a_listing_asks_for_it
  - behavior_id: BEH-288
    title: "a redirected robots.txt is followed to another host and its rules applied, while a page never leaves allowed_hosts"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_robots_redirect_to_another_host_is_followed
  - behavior_id: BEH-289
    title: "a robots.txt redirect to a private host is refused and the host is unreachable"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_robots_redirect_to_a_private_host_is_refused
  - behavior_id: BEH-290
    title: "robots rules match by longest pattern with allow winning a tie, honouring * and $"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_robots_longest_match_and_allow_on_tie
  - behavior_id: BEH-291
    title: "a robots group for our product token takes precedence over the * group, case-insensitively"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_robots_group_for_our_token_takes_precedence_over_star
  - behavior_id: BEH-292
    title: "extra request headers passed to get() are sent"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_extra_request_headers_are_sent
  - behavior_id: BEH-297
    title: "a host that resolves to a private address is refused before any request"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_host_resolving_to_a_private_address_is_refused_before_any_request
  - behavior_id: BEH-298
    title: "any non-globally-routable address among the answers (RFC 1918, link-local, CGNAT, IPv4-mapped, multicast, unspecified) refuses"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_any_private_address_among_the_answers_refuses
  - behavior_id: BEH-299
    title: "a name that does not resolve is unreachable, not refused"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_unresolvable_host_is_unreachable_not_refused
  - behavior_id: BEH-300
    title: "every hop is resolved, including a robots.txt redirect target"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_every_hop_is_resolved_including_a_robots_redirect_target
  - behavior_id: BEH-301
    title: "the default resolver is the OS resolver and returns address literals"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_default_resolver_is_the_os_resolver_and_returns_literals
  - behavior_id: BEH-302
    title: "a name that is not valid IDNA is unreachable, not a traceback"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_a_name_that_is_not_valid_idna_is_unreachable_not_a_traceback
  - behavior_id: BEH-303
    title: "a transient DNS failure is retried with backoff and then unreachable, with no request sent"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_transient_dns_failure_is_retried_with_backoff_then_unreachable
---

# HTTP client: judged redirects, budgets, retries, robots, politeness

## What

`Http.get(url, allowed_hosts=..., max_bytes=None)` is the only way the mirror reaches the network. Before every hop it checks the scheme is https (plaintext http is refused outright, whether it came from a redirect, a listing or `config.urls`), the hostname is in the source's `allowed_hosts`, and robots.txt for that host (fetched once per host per client, cached) allows the URL; any failure raises `HttpRefused`. A redirect (301/302/303/307/308) is followed for at most `MAX_HOPS` = 5 hops; a Location that is missing, contains control characters, does not parse, or would move from https to http is refused. Each hop reads the body under a budget (client `max_bytes`, default 20 MB, or a smaller per-call cap) and refuses rather than truncates when exceeded. A 429 or 5xx status and any transport/`http.client` error are retried `RETRIES` = 2 times with fixed backoff (`BACKOFF` = 2 s, 6 s) and then raised as `HttpUnreachable`; other statuses (e.g. 404) are returned as a `Response` for the adapter to judge. A module-level `_LAST_BY_HOST` clock makes every client sleep `delay_seconds` before any request to a host the process already touched. The User-Agent is chosen per source from three fixed policies (`default`, `neutral`, `browser`).

The opener and the sleep function are constructor arguments, so tests drive the client with `tests/fakehttp.py`'s `FakeOpener` and never touch the network.

## Why

docs-mirror's lessons, carried over (D21, plan B Task 2): a redirect is judged before it is taken so a regulator's page can never send the tool to a host the human did not confirm, and https never silently downgrades. Principle 8 / D24: robots.txt is honoured without exception and there is no allowlist or bypass parameter, because the tool scrapes regulators and must remain a good citizen. Principle 4: a transient failure is reported as unreachable, never as "no change". The politeness clock is process-wide because check/fetch build one client per source and twenty sources on one host must still wait between requests (commit 140555f); the default 10 s comes from eur-lex.europa.eu's Crawl-delay. Principle 11: the opener and sleep are injectable so tests use a fake with no network.

Private/loopback *literals* are rejected in `sources.validate` (allowed_hosts) before any request; every hop is then resolved by Http itself and refused if any address is not globally routable (SEC-003, decision below). Proxy environments (`https_proxy`) are out of scope: the tool assumes direct DNS and direct connections.

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-061 a 200 response returns status, body and final URL | accepted | `tests/test_http.py::test_get_ok` |
| BEH-062 a redirect to a host in allowed_hosts is followed and the final URL is reported | accepted | `tests/test_http.py::test_follows_same_host_redirect` |
| BEH-063 a redirect to a host not in allowed_hosts raises HttpRefused | accepted | `tests/test_http.py::test_refuses_cross_host_redirect` |
| BEH-064 a redirect to http:// is followed at https:// and the http URL is never requested | accepted | `tests/test_http.py::test_http_redirect_is_upgraded_to_https_and_never_requested_in_the_clear` |
| BEH-065 a body larger than the budget raises HttpRefused instead of being truncated | accepted | `tests/test_http.py::test_refuses_over_budget` |
| BEH-066 a per-call max_bytes lowers, never raises, the client budget | accepted | `tests/test_http.py::test_per_call_max_bytes_overrides_client_budget` |
| BEH-067 a 5xx is retried twice (three requests total) then raised as HttpUnreachable | accepted | `tests/test_http.py::test_retries_then_unreachable` |
| BEH-068 a URL disallowed by the host's robots.txt raises HttpRefused before it is requested | accepted | `tests/test_http.py::test_robots_disallow_refuses` |
| BEH-069 Http exposes no constructor parameter that bypasses robots.txt | accepted | `tests/test_http.py::test_robots_has_no_bypass_switch` |
| BEH-070 robots.txt is fetched from scheme://hostname[:port]/robots.txt, dropping userinfo from the netloc | accepted | `tests/test_http.py::test_robots_url_from_hostname_and_port_not_netloc` |
| BEH-071 a second request to the same host sleeps delay_seconds first | accepted | `tests/test_http.py::test_delay_between_same_host_requests` |
| BEH-072 the politeness clock applies across different Http instances for the same host | accepted | `tests/test_http.py::test_politeness_clock_is_shared_across_clients` |
| BEH-073 a Location with CRLF, NUL or an unparseable host raises HttpRefused, not a traceback | accepted | `tests/test_http.py::test_hostile_location_is_refused_not_raised` |
| BEH-074 an http.client.HTTPException from the server side becomes HttpUnreachable | accepted | `tests/test_http.py::test_server_side_http_exception_is_unreachable` |
| BEH-075 the three User-Agent policies resolve to the documented strings and default carries version and contact | accepted | `tests/test_http.py::test_user_agent_strings` |
| BEH-076 a robots.txt opener that raises makes the source unreachable and the run still completes | accepted | `tests/test_check.py::test_robots_opener_raising_is_unreachable_and_run_completes` |
| BEH-276 a redirected robots.txt is followed and its rules applied | accepted | `tests/test_http.py::test_robots_redirect_is_followed_and_rules_applied` |
| BEH-277 a 5xx on robots.txt makes the host unreachable and the page is never requested | accepted | `tests/test_http.py::test_robots_5xx_is_unreachable_not_fetched` |
| BEH-278 a 4xx on robots.txt means no rules | accepted | `tests/test_http.py::test_robots_4xx_means_no_rules` |
| BEH-279 a Disallow for the compliance-register product token holds under every User-Agent policy | accepted | `tests/test_http.py::test_robots_disallow_for_our_product_token_holds_under_browser_ua` |
| BEH-077 more than MAX_HOPS (5) redirects raises HttpRefused | accepted | `tests/test_http.py::test_more_than_max_hops_redirects_raises_http_refused` |
| BEH-078 a redirect without a Location header raises HttpRefused | accepted | `tests/test_http.py::test_a_redirect_without_a_location_header_raises_http_refused` |
| BEH-079 a non-http(s) scheme (file:, ftp:) raises HttpRefused before any request | accepted | `tests/test_http.py::test_a_non_http_scheme_raises_http_refused_before_any_request` |
| BEH-080 a 429 is retried like a 5xx | accepted | `tests/test_http.py::test_a_429_is_retried_like_a_5xx` |
| BEH-081 response header keys are title-cased so Content-Type lookups are case-insensitive | accepted | `tests/test_http.py::test_response_header_keys_are_title_cased` |
| BEH-287 a plaintext http URL is refused before any request, wherever it came from | accepted | `tests/test_http.py::test_plain_http_is_refused_even_when_a_listing_asks_for_it` |
| BEH-288 a redirected robots.txt is followed to another host and its rules applied, while a page never leaves allowed_hosts | accepted | `tests/test_http.py::test_robots_redirect_to_another_host_is_followed` |
| BEH-289 a robots.txt redirect to a private host is refused and the host is unreachable | accepted | `tests/test_http.py::test_robots_redirect_to_a_private_host_is_refused` |
| BEH-290 robots rules match by longest pattern with allow winning a tie, honouring * and $ | accepted | `tests/test_http.py::test_robots_longest_match_and_allow_on_tie` |
| BEH-291 a robots group for our product token takes precedence over the * group, case-insensitively | accepted | `tests/test_http.py::test_robots_group_for_our_token_takes_precedence_over_star` |
| BEH-292 extra request headers passed to get() are sent | accepted | `tests/test_http.py::test_extra_request_headers_are_sent` |
| BEH-297 a host that resolves to a private address is refused before any request | accepted | `tests/test_http.py::test_host_resolving_to_a_private_address_is_refused_before_any_request` |
| BEH-298 any non-globally-routable address among the answers (RFC 1918, link-local, CGNAT, IPv4-mapped, multicast, unspecified) refuses | accepted | `tests/test_http.py::test_any_private_address_among_the_answers_refuses` |
| BEH-299 a name that does not resolve is unreachable, not refused | accepted | `tests/test_http.py::test_unresolvable_host_is_unreachable_not_refused` |
| BEH-300 every hop is resolved, including a robots.txt redirect target | accepted | `tests/test_http.py::test_every_hop_is_resolved_including_a_robots_redirect_target` |
| BEH-301 the default resolver is the OS resolver and returns address literals | accepted | `tests/test_http.py::test_default_resolver_is_the_os_resolver_and_returns_literals` |
| BEH-302 a name that is not valid IDNA is unreachable, not a traceback | accepted | `tests/test_http.py::test_a_name_that_is_not_valid_idna_is_unreachable_not_a_traceback` |
| BEH-303 a transient DNS failure is retried with backoff and then unreachable, with no request sent | accepted | `tests/test_http.py::test_transient_dns_failure_is_retried_with_backoff_then_unreachable` |

Declarative decisions that are *not* executable are recorded under **Intentional
Design Decisions** below, not here.

## Intentional Design Decisions

### https only: a plaintext http URL from a listing or config is refused, not fetched

**Decision**: `_follow` refuses any scheme other than `https` before the first request — including an `http://` entry in a sitemap, a feed link, or a page-hash `config.urls` list.

**Rationale**: `sources.validate` already requires an https origin; server-supplied listings could still name plaintext pages on the same host, and legal text read in the clear can be altered on the path. One rule at the client closes every route.

**Security Scan Note**: `test_plain_http_is_refused_even_when_a_listing_asks_for_it` pins it. A redirect to `http://` is upgraded rather than refused (see the decision above).

### Every hop is resolved before the request and refused if any address is not globally routable; the TTL-0 rebinding window is an accepted residual

**Decision**: `_refuse_private_resolution` runs on every hop — page, redirect target, robots.txt — after the scheme and `allowed_hosts` checks: `socket.getaddrinfo` (injectable as `Http(resolver=)`) must answer, and every answer must be globally routable (`is_private_host`: `not ip.is_global or ip.is_multicast`, which covers loopback, RFC 1918, link-local, CGNAT 100.64/10, IPv4-mapped, reserved, documentation and unspecified). A resolver failure gets `RETRIES`/`BACKOFF` like a 5xx and is then unreachable; a bad IDNA label is unreachable, not a traceback. The window between this lookup and urllib's own (a TTL-0 rebinding name) is accepted. Proxies are out of scope.

**Rationale**: SEC-003 — a public name a human confirmed (`localtest.me`, `127.0.0.1.nip.io`, or one rebound later) resolved to 127.0.0.1 and was fetched; `allowed_hosts` only saw the literal. Three adversarial reviews of the fix added the not-global test (CGNAT is Tailscale's range on a dev machine), the retry and the `UnicodeError` catch. The residual is accepted because the client is https-only with certificate verification: a private target would have to present a certificate valid for the confirmed name before a byte of HTTP is sent. Pinning the connection to the vetted address would close it at the cost of a custom `HTTPSConnection`; not worth it for this tool today.

**Security Scan Note**: A scanner flagging "resolve-then-connect TOCTOU" is looking at the documented residual; a scanner flagging "hostnames resolved with getaddrinfo before the request" is looking at the control. Tests: `test_host_resolving_to_a_private_address_is_refused_before_any_request`, `test_any_private_address_among_the_answers_refuses`, `test_every_hop_is_resolved_including_a_robots_redirect_target`, `test_transient_dns_failure_is_retried_with_backoff_then_unreachable`.

### A redirect to http:// is upgraded to https:// and followed; nothing is ever requested in the clear

**Decision**: When a Location names `http://`, the client rewrites it to `https://` before the hop's checks run (allowed_hosts, robots, budget) and follows that; the `http://` URL itself is never requested. If the https URL fails, the source is unreachable.

**Rationale**: CELLAR's 303 for a consolidated act names `http://publications.europa.eu/resource/cellar/…`, and the identical body is served over https. Refusing the hop (the earlier decision) made every EUR-Lex fetch fail; following it in the clear would let an on-path attacker replace legal text (docs-mirror's lesson, D21). Upgrading keeps the guarantee that matters — no plaintext request, ever — and the fetch.

**Security Scan Note**: A scanner seeing a redirect handler that rewrites `http://` to `https://` is looking at the intended policy; `test_http_redirect_is_upgraded_to_https_and_never_requested_in_the_clear` asserts every request the client made started with `https://`.

### robots.txt has no bypass switch; a disallow is a refusal, not a retry with another UA

**Decision**: Http has no parameter, flag or allowlist that skips robots.txt; a disallowed URL raises HttpRefused before any request to it.

**Rationale**: Principle 8 and D24: Alex rejected Claude's proposed allowlist for government API hosts that publish `Disallow: /`. A disallowed source becomes `tier: refuse` and the register says only `review_by` watches it.

**Security Scan Note**: `test_robots_has_no_bypass_switch` asserts by introspection that no constructor parameter mentions robots. Do not add one.

### robots.txt is read per RFC 9309: redirects followed even to another host, 4xx means no rules, 5xx or a network failure makes the host unreachable

**Decision**: robots.txt is fetched through the same per-hop guarded loop as a page (https only, `MAX_HOPS`, 200 KB budget) with one difference: its redirects may leave `allowed_hosts` — `publications.europa.eu` sends its robots.txt to `op.europa.eu` — because rules can only ever restrict us; a private or local host is still refused. A 2xx is parsed; a 4xx caches "no rules"; a 5xx, a transport error after retries, or a refused redirect caches an `HttpUnreachable` that every later request to that host re-raises — the page is never requested.

**Rationale**: RFC 9309 §2.3.1.2–2.3.1.4: a crawler follows redirects to the file, treats "unavailable" (4xx) as no rules and "unreachable" (5xx / network) as complete disallow. Principle 8 says disallows are always honoured; rules we could not read cannot be honoured, so the honest three-valued answer (principle 4) is *unreachable*, not *fetched anyway*. Commit 1d954e2 had made an unreadable robots.txt fail-open so an odd port could not abort a whole run (principle 9); the run still completes — the source is simply reported unreachable by name.

**Security Scan Note**: A scanner seeing robots.txt fetched without the robots pre-check is looking at the one fetch that cannot check itself; every other guard applies to it. `test_robots_5xx_is_unreachable_not_fetched` and `test_robots_redirect_is_followed_and_rules_applied` pin it.

### robots.txt rules are matched per RFC 9309 — longest pattern wins, allow wins a tie — not by urllib.robotparser's first match

**Decision**: `_Robots` parses groups by product token (case-insensitive, merged, `*` as fallback) and rules with `*` wildcards and a trailing `$`; for a path, the longest matching pattern decides and an allow wins a tie.

**Rationale**: `urllib.robotparser` applies the first matching rule, which turned the Autoriteit Persoonsgegevens' `Disallow: /documenten` + `Allow: /documenten/*` into a refusal of every document — the pages the register most needs. RFC 9309 §2.2.2 says most-specific wins. Being stricter than the site is not a violation of principle 8, but it is lost coverage for no reason.

**Security Scan Note**: A hand-written robots matcher is the intended replacement for the stdlib one; `test_robots_longest_match_and_allow_on_tie` and `test_robots_group_for_our_token_takes_precedence_over_star` pin it against an AP-style file.

### robots.txt rules are evaluated against our own product token as well as the User-Agent presented

**Decision**: `can_fetch` is evaluated twice — for `compliance-register` (the default product token) and for the User-Agent actually sent — and both must allow.

**Rationale**: A per-source `browser` or `neutral` policy exists for hosts that reject non-browser clients (workflow.md), never to get past a rule aimed at this tool. A site that writes `User-agent: compliance-register / Disallow: /` has refused us by name; principle 8 says that refusal holds whatever string the request carries.

**Security Scan Note**: Not a bypass in either direction: a rule for `Mozilla` still applies under the browser policy, and a rule for our token applies under every policy. `test_robots_disallow_for_our_product_token_holds_under_browser_ua` pins it.

### Politeness clock is process-global mutable state and always sleeps the full delay

**Decision**: `_LAST_BY_HOST` is a module-level dict shared by every Http instance; `_wait` sleeps `delay_seconds` whenever the host has been seen before, without subtracting elapsed time.

**Rationale**: One client per source means a per-client clock never fires between sources (commit 140555f). Sleeping the full delay is a simplification that can only over-wait, never under-wait a regulator (principle 8).

**Security Scan Note**: Global mutable state in a single-process CLI with no threads; tests clear it explicitly. Not a race condition in this program.

### Over-budget bodies are refused, never truncated

**Decision**: `_once` reads max_bytes + 1 bytes and raises HttpRefused if the body exceeds the budget; no partial body is ever returned.

**Rationale**: A truncated legal text stored as a page would be a silent downgrade; a refusal is reported per source and the run continues (principle 9).

**Security Scan Note**: The 20 MB default and the 5 MB listing cap bound memory per request; a scanner flagging unbounded reads should note the +1 sentinel read.

### A browser User-Agent policy exists per source, chosen by a human

**Decision**: `user_agent('browser')` returns a Firefox string; the source's `headers.user_agent` selects it. robots.txt is evaluated against both our product token and that string.

**Rationale**: workflow.md: some gazettes refuse non-browser clients outright; the policy is set per source in sources.json by the confirming human (principle 3), not chosen by code to evade a refusal.

**Security Scan Note**: Not a robots bypass: the robots check runs unchanged and also against our own product token (see the decision above). Principle 8 forbids impersonation "to get around a refusal" — a UA-based block is not a refusal in robots.txt terms, and a robots.txt refusal cannot be gotten around by any UA.

### Retries are few, fixed and only on 429/5xx or transport errors

**Decision**: `RETRIES` = 2 with `BACKOFF` = (2, 6) seconds; a 4xx other than 429 is returned to the adapter without retry.

**Rationale**: "Retried a little and then reported as unreachable" (module docstring; principle 4). A 404 is a fact for the adapter's guards (EUR-Lex returns 404 for a missing language), not a transient failure.

**Security Scan Note**: No jitter and no configurability is deliberate minimalism (ponytail); it cannot amplify load beyond three requests per URL per run.

## Related Specs

- [SPEC-010: Adapter contract, registry and shared guards](./SPEC-010-adapter-contract.md)
- [SPEC-011: Sitemap adapter](./SPEC-011-sitemap-adapter.md)
- [SPEC-012: Feed adapter](./SPEC-012-feed-adapter.md)
- [SPEC-013: Page-hash adapter](./SPEC-013-pagehash-adapter.md)
- [SPEC-014: EUR-Lex adapter](./SPEC-014-eurlex-adapter.md)
- [SPEC-015: fetch command](./SPEC-015-fetch-command.md)
- [SPEC-016: check command](./SPEC-016-check-command.md)
- [SPEC-025: sources.json model: Source dataclass, defaults, atomic load/save, typed SourcesError](../api/SPEC-025-sources-model.md)
- [SPEC-026: sources.validate and refusals: the network-free gate before any request](../api/SPEC-026-sources-validate-refusals.md)
- [SPEC-030: Packaging: SKILL.md contract, plugin manifests, path launcher and version](../infra/SPEC-030-packaging-skill-md-plugin-launcher-version.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Inferred from code, tests and design repo (D21, D24); certainty 93 |
| 2026-09-21 | robots.txt now per RFC 9309 (redirects followed, 5xx/network → unreachable) and evaluated against our product token under every UA policy; BEH-076 retitled, BEH-276..279 added; two NEEDS CLARIFICATION closed | G2 principle checkpoint, principle 8 |
| 2026-09-21 | Client is https-only (plaintext refused at every hop, not just on downgrade); BEH-287 added | Security scan SEC-001 |
| 2026-09-21 | Behaviours promoted by Alex: tested → accepted, untested → confirmed (test owed) | First behaviour review after the freya wrap-up |
| 2026-09-21 | Trial fixes (fix/trial-findings): robots.txt redirects may leave allowed_hosts; RFC 9309 matcher replaces urllib.robotparser; http:// redirects upgraded to https, not refused (BEH-064 re-titled under INTENT-001); get() takes headers; BEH-288..292 added | nieuwbouw-tracker trial review |
| 2026-09-21 | SEC-003: every hop resolved and refused if not globally routable (353e668); NEEDS CLARIFICATION closed; BEH-297..303 added | security finding SEC-003 |
| 2026-09-21 | Tests written for BEH-077, BEH-078, BEH-079, BEH-080, BEH-081; promoted confirmed → accepted | tests owed |
