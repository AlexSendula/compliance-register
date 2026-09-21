# compliance-register

A register of the laws, regulator guidance, licences and contracts that apply
to a software project — discovered from the sources themselves, quoted and
dated, kept in the repo, re-checked on command.

Coding agents guess at regulation: they know a law exists, not whether it
applies to *this* project, what it asks, or whether it changed since the model
was trained. This skill writes that down, next to the code, in a form an agent
can use during brainstorming, implementation and review — and keeps the text
it rests on local, so a quote stays checkable and a change gets noticed.

It says what applies, why, and what you must do. It does not verify
compliance and never says "compliant".

**[What you get](#what-you-get)** · **[What it refuses to do](#what-it-refuses-to-do)** ·
**[Install](#install)** · **[Quick start](#quick-start)** · **[Commands](#commands)** ·
**[How it works](#how-it-works)** · **[Store layout](#store-layout)** ·
**[Contributing](#contributing)** · **[Licence](#licence)**

## What you get

Three layers under `knowledge-base/compliance/`, each with its own reader:

| Layer | What it holds | Who reads it |
|---|---|---|
| `sources.json` | where law and terms live for your jurisdictions, and how each is watched | the engine |
| `mirror/` | the sources brought local: dated markdown with provenance, per article where the source allows | the engine; the agent only through `search` |
| `regimes/*.md` | the verdicts and the obligations, in condition form | the agent, in every phase of the dev cycle |

A regime file says whether a law or contract **binds**, is **ruled out** (with
the reason), or is **undetermined** — and, when it binds, what you must do:

```markdown
### <ID>-001 · <short title>
- **When:** <the condition in your profile that makes this apply>
- **You must:** <the obligation, in your product's terms>
- **How often:** once | continuously | on <event>
- **It says:** "<verbatim quote>" — <article>, <source>, <version>
- **You'd know by:** <what a reviewer would look at in the code or config>
```

Every "You must" traces to a quote; every quote traces to a mirrored, dated
source; nothing counts until a human sets `confirmed_by`.

## What it refuses to do

- **Ship law.** No rule, threshold, date or source address is built in. The
  skill ships fifteen questions about your project and the method for finding
  everything else; an `api` adapter carries only the endpoint it speaks.
- **Decide for you.** Code proposes with evidence; a human confirms every
  profile answer, source and regime. Detected changes go to a pending list
  and stop there until someone resolves them.
- **Say "compliant".** Whether the code meets an obligation is for tests and
  reviews. The register states the obligation.
- **Crawl where it is not welcome.** robots.txt is honoured on every hop, read
  the way the RFC says, against the tool's own name whatever User-Agent a
  source needs; a disallowed source is cited by URL instead of fetched. No
  allowlist, no bypass. https only.
- **Spend tokens on watching.** `check` and `rescan` are plain Python.

## Install

```bash
npx skills add AlexSendula/compliance-register
```

or, as a Claude Code plugin:

```
/plugin marketplace add AlexSendula/compliance-register
/plugin install compliance-register@compliance-register
```

Python 3.12+ and PyYAML. If either is missing, every command exits `2` and
names it.

## Quick start

Ask your agent which regulations apply to the project. It drives the four
stages from `SKILL.md` — profile, discover, register, watch — and asks you to
confirm at each one. Behind it, the CLI:

```bash
compliance-register init          # scaffold knowledge-base/compliance/
compliance-register status        # regimes, obligations, profile age, pending
git add knowledge-base/compliance && git commit -m "compliance register"
```

Later, whenever you want to know whether anything moved:

```bash
compliance-register check         # each source: fresh / moved / unreachable
compliance-register pending       # what was detected, waiting for a human
compliance-register resolve chg-0001 --action applied --by "you"
```

`compliance-register` here is `bin/compliance-register` inside the installed
skill; there is no install step beyond copying the directory.

## Commands

| Command | Does |
|---|---|
| `compliance-register init` | Scaffold `knowledge-base/compliance/` (idempotent) |
| `compliance-register status [--json]` | Regimes and obligations counted, profile age, pending count, last check |
| `compliance-register pending [--json]` | Open detected changes |
| `compliance-register resolve <id> --action applied\|dismissed\|deferred --by <name> [--note]` | Record what a human decided |
| `compliance-register search "<query>" [-k N] [--kind regime\|mirror\|profile]` | Ranked keyword search over regimes, mirror and profile |
| `compliance-register profile validate` · `compliance-register profile diff --against <file or git ref>` | Check the fifteen answers; what changed against an older profile |
| `compliance-register regimes validate` · `compliance-register sources validate` | Problems per file, before anything touches the network |
| `compliance-register fetch [--source ID] [--force]` | Acquire or refresh confirmed sources into `mirror/` |
| `compliance-register check [--source ID] [--json]` | Per source: fresh / moved / unreachable → `pending.jsonl` |
| `compliance-register rescan` | Profile changed since last time? → `pending.jsonl` and a new snapshot |

Exit codes are part of the contract: `0` done · `1` failure (a validator
found problems; `check` could not reach a source; `fetch` had something
refused) · `2` refused — not inside a project with `knowledge-base/`, a
missing dependency, nothing to check, or a source that is not confirmed. No
request is made on a `2`. `SKILL.md` has the per-command rules.

## How it works

Four stages. The first three are the agent's, following the method files in
`references/`; the fourth is the CLI's.

| Stage | What happens | Who |
|---|---|---|
| 1 Profile | fifteen questions about the project — where it is established, whom it serves, what is exchanged, what personal data it holds, whether it uses AI… Code proposes answers with evidence from the repo; a human confirms | agent + you |
| 2 Discover | the official sources per jurisdiction, then each regime's scope clause: does it bind, is it ruled out, or can it not be told yet | agent + you |
| 3 Register | one file per regime, obligations quoted | agent + you |
| 4 Watch | `check` for sources that moved, `rescan` for a profile that changed; both append to the pending list and stop | CLI |

Acquisition resolves in tiers, cheapest first, chosen per source when it is
confirmed:

| Tier | Change signal | What `check` costs |
|---|---|---|
| `api` | a dated version id (EUR-Lex via CELLAR) | one query for the whole basket |
| `sitemap` | per-page `lastmod` | the listing, no page bodies |
| `feed` | new entry ids | the feed |
| `page-hash` | content hash — the tool fetches to compare, and says so | the page |
| `refuse` | none — robots.txt or terms forbid it; cited by URL, watched by its `review_by` date | nothing |

Freshness is three-valued on purpose: *fresh*, *moved*, *unreachable*.
"Could not reach" is never reported as "no change".

## Store layout

```
knowledge-base/compliance/
  profile.md              the fifteen answers, with evidence and who confirmed
  profile.snapshot.json   what the last rescan saw
  sources.json            where law lives, per jurisdiction; tier and licence per source
  regimes/<ID>.md         one file per regime, obligations inside
  mirror/
    <jurisdiction>/<source-id>/
      MANIFEST.json       per-source page manifest
      *.md                the text, with provenance frontmatter (api tier: <version>/art_N.md)
    .private/             sources whose licence forbids redistribution; gitignored
  pending.jsonl           detected changes awaiting a human (append-only)
  resolutions.jsonl       what humans did (append-only)
  .last-check             when check last ran
  .search-index.json      search cache; derived, gitignored
```

Everything is committed except `mirror/.private/` and the search index.
`init` writes both `.gitignore` lines.

## Documentation

- [`SKILL.md`](SKILL.md) — the agent-facing contract
- [`references/`](references/) — the fifteen questions and the method files
  for each stage
- [`knowledge-base/principles.md`](knowledge-base/principles.md) — the rules
  every change is checked against
- [`knowledge-base/reference/`](knowledge-base/reference/) — architecture,
  CLI reference, security model, troubleshooting by message

## Contributing

Issues and pull requests welcome. Run the tests before opening one:

```bash
pip install -r requirements-dev.txt
python3 -m pytest -q
```

No test touches the network or DNS. A change that alters behaviour should
say why in the commit message; the knowledge base records decisions and
cites the commits that made them.

## Licence

[MIT](LICENSE) for the tool.

**That covers the tool and nothing it mirrors.** Mirrored text keeps its
source's licence; a source that forbids redistribution lands under
`mirror/.private/` and is never committed.
