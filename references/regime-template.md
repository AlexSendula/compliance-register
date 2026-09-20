# Regime file template

One file per regime at `knowledge-base/compliance/regimes/<ID>.md`. `<ID>` is
short, stable, and the same as the frontmatter `id` — `GDPR`, `CRD`,
`SEPA-CORE`, `MOLLIE-UA`. A contract or a licence held is a regime too.

```markdown
---
id: GDPR
title: General Data Protection Regulation
status: binds                 # binds | ruled-out | undetermined | no-longer-applies
jurisdiction: EU
sources:
  - id: eurlex-32016R0679     # an id from sources.json, or a URL if not mirrored
    version: 02016R0679-20160504
    retrieved: 2026-09-20
applies:
  quote: "…in the context of the activities of an establishment of a controller … in the Union…"
  cite: Art. 3(1)
  triggered_by:
    - establishment: NL
    - personal_data: true
exempt:
  quote: null                 # the carve-out text, if one was checked
  reason: "no exemption clause applies"
confirmed_by: Alex
confirmed_at: 2026-09-20
review_by: 2027-09-20
---

## Why this applies to you
One paragraph in plain words. Name the profile answers that trigger it.

## Obligations

### GDPR-001 · Records of processing
- **When:** you process personal data other than occasionally
- **You must:** keep a record of processing activities — purposes, categories, recipients, retention, security measures
- **How often:** continuously; produce on request
- **It says:** Art. 30(1) — "Each controller … shall maintain a record of processing activities under its responsibility."
- **You'd know by:** a record exists and names the above
- **Note:** the Art. 30(5) exemption does not apply — processing is not occasional (profile)
```

Rules:
- `It says` is a verbatim quote with its citation. No quote, no obligation.
- `You must` is one sentence a developer can act on. If it takes a paragraph, split it.
- `You'd know by` is a hint for whoever verifies. It is not a test and this skill does not run it.
- A ruled-out regime keeps the frontmatter, sets `status: ruled-out`, fills `exempt.quote` and `exempt.reason`, and has no `## Obligations` section.
- `no-longer-applies` is what `rescan` sets when a trigger disappears from the profile. The file stays; history matters.
- Never write "compliant" anywhere in a regime file.
