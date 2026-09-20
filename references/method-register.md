# Method — stage 3, Register

Goal: the `## Obligations` section of each `binds` regime file — what this
product must do, from the instrument's own text (D11, D22).

## Scope
Per product, not per regulation. Read the instrument for what binds the
kind of thing the profile describes; skip what binds regulators, courts,
member states, or other kinds of organisation. Tens of obligations is
normal; hundreds means you are transcribing the statute.

## For each obligation
Write a `### <ID> · <title>` block with the six bullets from the template:
- **When** — the condition, in profile terms. If the condition is always
  true for this product, say so.
- **You must** — one actionable sentence. Split if it needs "and".
- **How often** — once, continuously, per event, by a date, on request.
- **It says** — citation + verbatim quote from the dated version in
  `sources`. No quote, no obligation.
- **You'd know by** — one line a verifier could use. This skill never
  checks it (D15).
- **Note** — exemptions considered, interactions with other regimes, dates.

IDs are `<REGIME>-<NNN>`, sequential, never reused.

## Contracts and licences
Same shape. `It says` quotes the clause; `sources` names the contract
version or date you read.

## Do not
- Do not paraphrase into "you must comply with Article X". Say what to do.
- Do not write "compliant", "non-compliant", or any status. There is none.
- Do not add obligations you cannot quote.

## Present and confirm
Show the human the list per regime. They confirm, edit, or strike. Update
`confirmed_at`. Run `regimes validate`. Commit.
