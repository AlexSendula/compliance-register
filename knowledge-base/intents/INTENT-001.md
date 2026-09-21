---
id: INTENT-001
behaviors:
  - BEH-265
  - BEH-111
  - BEH-112
  - BEH-113
  - BEH-114
  - BEH-115
  - BEH-116
  - BEH-103
  - BEH-104
  - BEH-106
  - BEH-107
  - BEH-108
  - BEH-061
  - BEH-062
  - BEH-063
  - BEH-064
  - BEH-065
  - BEH-066
  - BEH-067
  - BEH-068
  - BEH-069
  - BEH-070
  - BEH-071
  - BEH-072
  - BEH-073
  - BEH-074
  - BEH-075
  - BEH-276
  - BEH-277
  - BEH-278
  - BEH-279
  - BEH-287
  - BEH-128
  - BEH-129
  - BEH-130
  - BEH-131
  - BEH-132
  - BEH-133
  - BEH-134
  - BEH-135
  - BEH-136
  - BEH-137
  - BEH-138
  - BEH-139
  - BEH-140
  - BEH-288
  - BEH-289
  - BEH-290
  - BEH-291
  - BEH-292
  - BEH-293
  - BEH-294
  - BEH-295
  - BEH-296
approver: Alex
date: 2026-09-21
---
## Rationale
Trial fixes on fix/trial-findings (0ca2807, ee259bf), approved by Alex on 2026-09-21 after the nieuwbouw-tracker review. Guarantees that actually change: BEH-064 — a redirect to http:// is now upgraded to https:// and followed, no longer refused (nothing is ever requested in the clear; test renamed to test_http_redirect_is_upgraded_to_https_and_never_requested_in_the_clear); BEH-132/BEH-133 — fetch reads the consolidated act from CELLAR (publications.europa.eu/resource/celex) by content negotiation instead of eur-lex.europa.eu, G1 accepts application/xhtml+xml, G2 is the structural class=disclaimer paragraph rather than the English sentence. Every other behaviour listed here sits in a test file that changed only in its shared helper or fixtures (client() routes a 404 robots.txt and the CELLAR 303; new tests appended); their guarantees are unchanged and their tests still pass.

BEH-288..296 are the behaviours these same commits added (new tests in the same files); listed so the gate can see they were introduced, not altered.
