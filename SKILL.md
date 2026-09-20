---
name: compliance-register
description: |
  Keep a register of the laws, regulator guidance, licences and contracts that
  apply to a software project — discovered from the sources themselves,
  quoted and dated, stored in the repo, and re-checked on command. It says
  what applies, why, and what you must do. It never verifies compliance and
  never says "compliant".

  TRIGGER when: the user asks which regulations, laws or rules apply to a
  project or feature; asks to set up, update or review compliance obligations;
  asks whether any regulation changed; mentions GDPR, PSD2, SEPA, consumer
  law, accessibility law, AI rules, a payment provider's terms, or "what do we
  need to do to comply". Also consult knowledge-base/compliance/ BEFORE
  answering any regulatory question about a project that has one.
license: MIT
compatibility: Requires Python 3.12+ and PyYAML. No network needed except for fetch and check.
metadata:
  author: AlexSendula
  version: "0.1.0"
---

# Compliance register

Four stages. Stages 1–3 are yours to drive, following the method files;
the commands below are deterministic helpers.

| Stage | You do | Method |
|---|---|---|
| 1 Profile | ask the 15 questions; propose from code; the human confirms | `references/method-profile.md` |
| 2a Sources | find the official sources per jurisdiction; the human confirms | `references/method-discover-sources.md` |
| 2b Regimes | read each regime's scope clause; binds / ruled out / undetermined | `references/method-discover-regimes.md` |
| 3 Register | write this product's obligations, quoted | `references/method-register.md` |
| 4 Watch | run `check` and `rescan` when the caller wants; a human resolves | below |

The questions: `references/dimensions-checklist.md`. The file shape:
`references/regime-template.md`.

## Running it

Invoke by path — there is no install step:

```bash
python3 "$SKILL_DIR/bin/compliance-register" <command>
```

`$SKILL_DIR` is the directory containing this file. Needs Python 3.12+ and
PyYAML; if either is missing it exits 2 and names it — tell the user, do not
work around it.

## Commands

| Command | Does |
|---|---|
| `init` | scaffold `knowledge-base/compliance/` |
| `status [--json]` | regimes and obligations counted, profile age, pending count |
| `profile validate` | exit 1 with the list of unanswered or null answers |
| `profile diff --against <file or git ref>` | dimensions whose value changed |
| `regimes validate` | exit 1 with problems per regime file |
| `sources validate` | exit 1 with problems per source (`check` and `fetch` run this first and make no request while it fails) |
| `pending [--json]` | open detected changes |
| `resolve <id> --action applied\|dismissed\|deferred --by <name> [--note]` | record what a human did |
| `search "<query>" [-k N] [--kind regime\|mirror\|profile]` | ranked keyword search |
| `fetch [--source ID] [--force]` | acquire or refresh confirmed sources into `mirror/`; exit 2 for a `refuse`-tier source you asked for |
| `check [--source ID] [--json]` | for each source: fresh / unreachable / moved. Writes `pending.jsonl` and stops. Page-hash sources are fetched to compare and say so |
| `rescan` | profile changed since the last rescan? Writes `regime-gone` / `regime-new` entries. Edits nothing |

Exit codes: `0` done · `1` failure · `2` refused (not in a project with
`knowledge-base/`, missing dependency). For the watch commands precisely:

- `check` → `0` ran, every source fresh or moved · `1` ran, but at least one
  source was unreachable (drift not knowable there) · `2` nothing to check, or
  validation failed — no request was made.
- `fetch` → `0` done · `1` a guard or HTTP refused something (a
  `source-unreachable` entry names it) · `2` a `refuse`-tier source was asked
  for, validation failed, or a named source is not confirmed — no request was
  made.
- `rescan` → `0` done · `1` no profile · `2` the profile does not validate.

## Rules

- **Read the register before answering.** If `knowledge-base/compliance/`
  exists, its regime files are the project's position. Quote them.
- **Never say "compliant".** The register states obligations. Whether the
  code meets them is for tests and reviews, not this skill.
- **Nothing here is law.** Every rule and obligation comes from a dated
  source quoted in the file. If a regime file has no quote, it is not done.
- **Humans confirm.** Do not set `status: confirmed`, `confirmed_by` or
  `confirmed_at` yourself. Propose, show, wait.
- **Questions 1 and 2 first.** Where established, where aimed. A locale file
  is evidence to surface under question 2, never a market to assert.
- **Record, surface, delegate.** `check` and `rescan` write to
  `pending.jsonl` and stop. Resolving is a human's job; `resolve` records it.
- **Everything is committed** except what a source's licence forbids
  (`mirror/.private/`, gitignored by `init`).
- **When a profile answer changes**, run `profile diff`, then stage 2b for the
  listed dimensions only. Mark regimes whose trigger vanished
  `no-longer-applies`; never delete.

## The mirror

`sources.json` lists each source with its tier and change signal. Tiers, in
the order the engine prefers them: `api` (a dated version id — EUR-Lex),
`sitemap` (per-page lastmod), `feed`, `page-hash`, `refuse`. The mirrored
text is markdown with provenance frontmatter under
`mirror/<jurisdiction>/<source-id>/`. A source whose licence forbids
redistribution is written under `mirror/.private/`, which is gitignored.

robots.txt is always honoured, on every host and every hop. A source whose
robots.txt disallows the path is recorded as `tier: refuse`; the regime is
still discovered and cites it by URL, and its `review_by` is the only
signal. There is no allowlist.

Read the mirror before fetching a page from the web: if the source is in
`sources.json` and the article is under `mirror/`, quote the local file —
its frontmatter says which version and when it was retrieved.

EUR-Lex acts that have never been consolidated (nothing has amended them
yet) are not mirrored in v1: `check` reports them unreachable and they are
cited by URL. Language availability is not pre-checked: a G1/G2 refusal on a
version SPARQL says exists may mean that language expression is not
published yet.

`check` downloads nothing on `api`, `sitemap` and `feed` sources. It never
updates a version; only `fetch` does, after the source's content guards pass.
"Unreachable" means we could not tell. It is never "fresh".
