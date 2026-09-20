# Method — stage 2a, Sources

Goal: `sources.json` lists, for each jurisdiction in the profile, the
official places where law and regulator guidance are published — proposed
by you, confirmed by the human, with nothing hardcoded (D17).

## Inputs
- `profile.md`: `establishment` and `directed_activity.markets` give the
  jurisdictions; `sector`, `money_flow`, `personal_data`, `automation_ai`,
  `third_party_content` say which regulators are likely to matter.

## For each jurisdiction
Search the web (spawn one subagent per jurisdiction if you can) for:
1. The primary legislative database — where consolidated statute text is
   published by the state. Prefer a site with a stable identifier per act and
   a dated version or "valid on" concept.
2. The official gazette — where amendments are first announced.
3. The regulators the profile implicates: data protection, consumer,
   payments/financial, telecoms, tax, company register. Their guidance pages.
4. For a supranational layer (an economic union the jurisdiction belongs to):
   its legislative database and the union-level regulators.

## For each candidate source, record
One object in the `sources` list of `sources.json`. These are the fields the
engine reads; `sources validate` refuses anything that breaks the rules
below, and `check` and `fetch` make no request while it does.

- `id`: `<jurisdiction>-<short-name>` (lowercase, dashes). Regime files
  cite it literally, so it never changes once a regime names it.
- `jurisdiction`: the jurisdiction code you used in the profile.
- `kind`: one of `legislation`, `gazette`, `regulator`, `contract`, `standard`.
- `url`: the entry URL. Must be `https`.
- `covers`: one line — what this source holds for this project.
- `tier`: one of `api`, `sitemap`, `feed`, `page-hash`, `refuse`, with the
  evidence for it (an API doc page, a sitemap you fetched, a feed URL).
  `refuse` means never fetched, only cited by URL.
- `adapter`: which engine module speaks to the source. Defaults follow the
  tier (`sitemap` → `sitemap`, `feed` → `feed`, `page-hash` → `pagehash`).
  Tier `api` has no default: it needs an explicit adapter, and the only one
  shipped is `eurlex`.
- `config`: what the adapter needs —
  - `eurlex`: `celex` (the base CELEX number of the act, required) and
    `language` (a two-letter EU language code; default `EN`);
  - `pagehash`: `urls` (a list of pages to hash; defaults to `[url]`);
  - `sitemap`: `include` (a list of URL prefixes to keep; empty keeps all);
  - `feed`: nothing.
- `change_signal`: what tells you it moved — version id, lastmod, feed
  entry, content hash.
- `licence`: `{name: "<SPDX id or null>", redistribute: true|false, attribution: "<text or null>"}`.
  Read the site's reuse terms; `redistribute` must be a boolean. When you
  cannot find the terms, `redistribute: false` until a human says otherwise.
- `allowed_hosts`: the hostnames a fetch may touch, including redirect
  targets. Defaults to the host of `url`. Never a local or private address.
- `headers`: `{"user_agent": ...}` — the `user_agent` policy the host
  needs, one of `default`, `neutral`, `browser`. `default` identifies this tool;
  `neutral` is a bare generic client; `browser` is for hosts that refuse
  anything else. Say in `evidence` why you chose a non-default one.
- `delay_seconds`: seconds between requests to the same host (default 10).
  The engine does not read `Crawl-delay`: if robots.txt states a larger
  one, write it here.
- `evidence`: the URLs you read to establish the above.
- `status`: `proposed` now; `confirmed` once the human keeps it;
  `unresolved` when you could not find an official source (see below).

Leave out `last_checked`, `last_status`, `last_version`, `next_version`
and `last_fetched` — the engine writes them.

robots.txt is always honoured, on every host and every hop; there is no
allowlist. Read the host's robots.txt for the path you would fetch. If it
disallows that path, record the source with `tier: refuse` (cited by URL,
never fetched) and say so in `evidence`.

## Present and confirm
Show the list to the human grouped by jurisdiction. They confirm, drop, or
add. Set `status: confirmed` on the kept ones. Run
`python3 "$SKILL_DIR/bin/compliance-register" sources validate`, then
`fetch` — or, until the mirror exists, cite these URLs directly in regime
files.

## Stop conditions
- A jurisdiction with no official legislative database you can find: record
  it as `status: unresolved` with what you searched. Do not substitute a
  commercial aggregator.
- A source whose terms or robots.txt forbid automated access: record it
  with `tier: refuse`. It can still be cited by URL.
