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
- `id`: `<jurisdiction>-<short-name>` (lowercase, dashes)
- `jurisdiction`, `url`, `covers` (one line), `kind`: `legislation | gazette | regulator | contract`
- `tier` you expect to work: `api | sitemap | feed | page-hash`, with the
  evidence (an API doc page, a sitemap you fetched, a feed URL)
- `change_signal`: what tells you it moved (version id, lastmod, feed entry,
  content hash)
- `licence`: `{redistribute: true|false, attribution: "<text or null>"}` —
  read the site's reuse terms; when you cannot find them, `redistribute:
  false` until a human says otherwise
- read the host's robots.txt for the path you would fetch. It is always
  honoured — there is no allowlist. If it disallows the path, the source
  is `tier: refuse` (cited by URL, never fetched); say so in `evidence`
- `headers`: any quirk you found (a browser User-Agent needed, or forbidden)
- `evidence`: the URLs you read to establish the above
- `status`: `proposed`

## Present and confirm
Show the list to the human grouped by jurisdiction. They confirm, drop, or
add. Set `status: confirmed` on the kept ones. Then run
`python3 "$SKILL_DIR/bin/compliance-register" fetch` (Part B) — or, until the
mirror exists, cite these URLs directly in regime files.

## Stop conditions
- A jurisdiction with no official legislative database you can find: record
  it as `status: unresolved` with what you searched. Do not substitute a
  commercial aggregator.
- A source whose terms or robots.txt forbid automated access: record it
  with `tier: refuse`. It can still be cited by URL.
