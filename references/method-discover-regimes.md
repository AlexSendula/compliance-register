# Method — stage 2b, Regimes

Goal: one `regimes/<ID>.md` per regime you considered — `binds`,
`ruled-out` with the reason, or `undetermined` — each derived from the
regime's own scope clause, quoted and dated (D4, D13).

## Find candidates
For each confirmed source, search the mirrored text (or the site) for
instruments that touch the profile's answers. Use the answers' own words —
"personal data", "consumer", "direct debit", "donation", "automated
decision" — not law names you already know. Include:
- statutes and regulations
- regulator guidance the profile implicates
- contracts the profile names under `third_parties` (a PSP's terms, a
  processor agreement, an app store's terms)
- conditions attached to anything listed under `licences`

## For each candidate
1. Find the scope clause — the article or section that says whom the
   instrument binds, and any exemption or threshold clause next to it.
2. Write one **applies** question and one **exempt** question, each as a
   yes/no question about the profile, each with a verbatim quote and a
   citation to the dated version you read.
3. Evaluate them against `profile.md`:
   - applies = yes and exempt = no → `status: binds`
   - exempt = yes, or applies = no → `status: ruled-out`, with the quote and
     the reason in `exempt`
   - any answer you need is `null` or the clause does not decide → `status:
     undetermined`, and say which answer would decide it
4. Write the regime file from `references/regime-template.md`. Leave
   `## Obligations` empty for now — that is stage 3.

## Growth check
If a scope clause tests a fact that none of the fifteen questions covers,
do not guess. Write it to the regime file under `## Needs a new question`
with the quote, and tell the human. A new question is added to the
checklist only with that provenance.

## Present and confirm
Show the human three lists: binds, ruled out (with reasons), undetermined
(with what would decide each). They confirm or correct. Set `confirmed_by`
and `confirmed_at` on each file. Run
`python3 "$SKILL_DIR/bin/compliance-register" regimes validate`. Commit.

## When re-run after a profile change
Only revisit regimes whose `applies.triggered_by` or exemption reasoning
names a dimension that `rescan` reported changed. If a trigger is gone, set
`status: no-longer-applies` and write why under `## History`. Never delete
the file.
