---
id: INTENT-004
behaviors:
  - BEH-006
  - BEH-304
  - BEH-305
  - BEH-306
  - BEH-307
  - BEH-308
  - BEH-309
  - BEH-310
  - BEH-311
approver: Alex
date: 2026-09-22
---
## Rationale

Alex approved this change set on 2026-09-22, after the viva-croatia trial: the
agent driving stage 1 ran `profile validate`, got exit 0 with nine answers still
`proposed`, and read that as "stage 1 complete"; it also wrote `confirmed_by:
Alex` while those nine were proposals, because `references/method-profile.md`
told it to ("Set `confirmed_by` and `confirmed_at`") where SKILL.md forbade it.

**New behaviours** were written `proposed` with passing tests and promoted to
`accepted` by Alex on 2026-09-22, in the wrap-up that follows this change; they
are listed here because the gate reads test files, not test functions, and their
tests live beside BEH-006's. `validate` now reports a `proposed` answer and an
attestation written early (BEH-304, BEH-305); `blocking` is the narrower list
`rescan` gates on (BEH-306, BEH-307); `profile validate` exit 0 therefore means
stage 1 is finished (BEH-309). `_answer` guards every read of an answer mapping
so a hand-written `size: small` is reported, not raised (BEH-308, BEH-311).
A dimension put back to `proposed` now keeps its last confirmed value in the
snapshot (BEH-310) — before, re-proposing a confirmed answer wrote `null` over
the baseline and filed a major `regime-gone` saying the dimension "is no longer
true", which is Principle 4's failure mode ("not yet confirmed" reported as
"not there"). That bug predates this change set; splitting the gate is what made
the path reachable by design, so it is fixed here.

**One existing guarantee's test changed.** BEH-006
(`tests/test_profile.py::test_validate_requires_confirmed_by_and_confirmed_at_only_once_every_answer_is_confirmed`)
is an assertion-scope edit only: its tail no longer asserts
`validate(meta) == []` with one answer still `proposed`, because that profile
now reports `size: proposed, not confirmed`. What BEH-006 pins — the attestation
is required only once every answer is confirmed — is unchanged and still
asserted; the exact problem list is pinned by BEH-304 and BEH-305.

**Not changed, decided.** A confirmed `unknown` (`value: null`) still blocks
`rescan` (D29). Alex ruled on 2026-09-22 to keep it: a baseline over a dimension
nobody can answer would put every later drift verdict on top of a hole. The cost
— no profile-change loop for that project until the answer is known — is
disclosed in `references/method-profile.md` at the point the agent records the
answer, and recorded as a decision in SPEC-001.
