# Regime file template

One file per regime at `knowledge-base/compliance/regimes/<ID>.md`. `<ID>` is
short, stable, uppercase, and the same as the frontmatter `id` — an
instrument's usual abbreviation, or for a contract the counterparty and the
document. A contract or a licence held is a regime too.

Source ids follow `<jurisdiction>-<short-name>`, lowercase, dashes
(e.g. `eu-eurlex-<celex>`) — the `id` field of the entry in `sources.json`.

Everything in angle brackets is a placeholder. Nothing below is law: the
quotes, citations, versions and dates come from the source you read, on the
day you read it.

```markdown
---
id: EXAMPLE
title: <instrument title>
status: binds                 # binds | ruled-out | undetermined | no-longer-applies
jurisdiction: <jurisdiction>
sources:
  - id: <jurisdiction>-<short-name>   # an id from sources.json, or a URL if not mirrored
    version: <dated version id, or the date you read it>
    retrieved: <YYYY-MM-DD>
applies:
  quote: "<verbatim scope clause>"
  cite: <Art. N(M)>
  triggered_by:
    - <slug>: <value>
exempt:
  quote: null                 # the carve-out text, if one was checked
  reason: "<why no exemption clause applies, or which one does>"
confirmed_by: <name>
confirmed_at: <YYYY-MM-DD>
review_by: <YYYY-MM-DD>
---

## Why this applies to you
One paragraph in plain words. Name the profile answers that trigger it.

## Obligations

### EXAMPLE-001 · <title>
- **When:** <the condition, in profile terms>
- **You must:** <one actionable sentence>
- **How often:** <once | continuously | per event | by a date | on request>
- **It says:** <Art. N(M)> — "<verbatim quote from the version in sources>"
- **You'd know by:** <one line a verifier could use>
- **Note:** <exemptions considered, interactions with other regimes, dates>
```

Rules:
- `It says` is a verbatim quote with its citation. No quote, no obligation.
- `You must` is one sentence a developer can act on. If it takes a paragraph, split it.
- `You'd know by` is a hint for whoever verifies. It is not a test and this skill does not run it.
- A ruled-out regime keeps the frontmatter, sets `status: ruled-out`, fills `exempt.quote` and `exempt.reason`, and has no `## Obligations` section.
- `no-longer-applies` is set by whoever resolves a `regime-gone` entry (a stage 2b re-run); `rescan` only raises the entry. The file stays; history matters.
- Never write "compliant" anywhere in a regime file.
