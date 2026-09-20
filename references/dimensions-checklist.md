# Dimensions checklist — draft 2

The one fixed artifact this skill ships for scoping. It contains **questions, never
answers**: no threshold, no date, no instrument named as a fact. Those live in the
project's derived rules, quoted and dated from the source, and go suspect when the
source moves.

Each dimension has the same five lines:

- **Ask** — the question, as a fact about the project
- **Decides** — why any jurisdiction's scope article cares (generic, no law content)
- **Code may propose** — what evidence the repo can offer, if any; always cited, never decisive
- **Trap** — the inference an agent makes when it skips the question
- **Found in** — provenance: the scope articles and practice sources found to test
  this fact. It names where the *question* came from, never what the answer is.
  Currently EU/NL-derived plus international practice; a new jurisdiction's
  onboarding adds to these lines or proposes a new dimension.

Rules for editing this file: add a dimension when a scope article somewhere asks
something no dimension covers. Remove one only by showing no scope article anywhere
asks it. Never add an answer.

Dimensions 1 and 2 are asked first, alone — they decide which jurisdictions' sources
to read, and therefore which of the remaining questions matter for this project.

---

## Where obligations come from

Not only statute. ISO 19600:2014 §4.5.1 (predecessor of ISO 37301) lists the
examples this table collapses, and every register in practice mixes them. The register must be able to hold an obligation from any of these, with
the same fields:

| Mandatory | Voluntary |
|---|---|
| laws and regulations | contracts (PSP terms, processor agreements, app-store terms) |
| permits, licences and authorisations held | own policies and procedures |
| rules and guidance issued by regulators | codes and standards |
| court and tribunal judgments | agreements with customers, public bodies or communities |
| treaties and conventions | |

The dimensions below decide *which* of these reach the project. A permit or contract
that the operator has signed is an obligation source in its own right and is asked
about directly (dimension 7).

## Slugs

The answer keys in `profile.md`, in order: `establishment`, `directed_activity`,
`users`, `legal_form`, `size`, `sector`, `licences`, `exchanged`, `money_flow`,
`personal_data`, `third_parties`, `third_party_content`, `role`,
`automation_ai`, `time_change`.

---

## 1. Establishment

- **Ask** — In which country or countries — and sub-national regions where that matters — is the operating entity legally established? Group structure, if any.
- **Decides** — Which national law overlays the regional one, which regulator leads, whether a parent's obligations aggregate.
- **Code may propose** — Nothing. Statutes and the company register, not the repo.
- **Trap** — Inferring it from the domain TLD, the hosting region, or a founder's name. Relying on a parent or foreign framework instead of local rules — a named regulator finding.
- **Found in** — GDPR Art. 3(1); NQA legal-register guidance ("location/s of the organisation"); Grant Thornton regulatory-universe method (entities, jurisdictions).

## 2. Directed activity

- **Ask** — Which markets is the service deliberately aimed at, and through which channels — own web, app stores, embedded in partners, API, resellers? Asserted by the operator.
- **Decides** — Which foreign consumer and data regimes reach in beyond establishment; which channel operators' terms bind.
- **Code may propose** — Indicia only: locales shipped, currencies accepted, countries in an address form, phone prefixes, shipping destinations, store listings. Surface them, then stop.
- **Trap** — Language equals market. A locale file is evidence a court weighs, not a conclusion. A community site can serve a diaspora in their language without directing anything at their country of origin.
- **Found in** — GDPR Art. 3(2); Brussels Ia Art. 17(1)(c) and Rome I Art. 6 as read in CJEU *Pammer / Hotel Alpenhof*; ESMA CSA 2025 §66 (distribution channels).

## 3. Who the users are

- **Ask** — Consumers, businesses, members, the public? Could they include minors or people in a vulnerable position? Where are they located?
- **Decides** — Whether consumer-protection regimes apply at all, age-gating and vulnerability duties, data-protection reach.
- **Code may propose** — Partially: signup flow, B2B fields, age checks, account types.
- **Trap** — "Public website" equals consumers everywhere. A members-only service is a different legal animal.
- **Found in** — CRD 2011/83 (consumer contracts only); ESMA CSA 2025 §66 (categories of investors); ISOvA screening question "Do you sell to consumers?".

## 4. Legal form and purpose

- **Ask** — Company, association, foundation, sole trader, cooperative, public body? Non-profit?
- **Decides** — Whether trader-facing regimes apply at all; charity, fundraising and tax regimes.
- **Code may propose** — Nothing.
- **Trap** — Treating a foundation taking donations as a trader selling goods, or the reverse.
- **Found in** — CRD 2011/83 trader definition; NL charity/ANBI regime; NQA ("type … of the organisation").

## 5. Size

- **Ask** — Headcount, turnover, balance sheet — and whether the entity is part of a group whose figures aggregate.
- **Decides** — Size carve-outs and size-triggered duties, which many regimes have and some deliberately lack.
- **Code may propose** — Nothing.
- **Trap** — Assuming small means exempt everywhere. Forgetting group aggregation. Reading a threshold from memory instead of from the dated source.
- **Found in** — Rec. 2003/361/EC; EAA Art. 4(5); DSA Art. 19; NIS2 size-cap rule; NQA ("size").

## 6. Sector

- **Ask** — Does the activity fall in a sector regulated in its own right — finance, health, energy, transport, telecoms, education, gambling, legal, and so on?
- **Decides** — Sector regimes, which usually bind regardless of size and gate *before* size is considered.
- **Code may propose** — Weak signals only: dependencies, API integrations. Cite and stop.
- **Trap** — Inferring sector from a word in the name or README.
- **Found in** — NIS2 Annexes I/II; NQA ("the industry the organisation operates in"); ISO 37301 §4.1.

## 7. Licences, permits and registrations held

- **Ask** — What authorisations, registrations, certifications or recognised statuses does the entity hold or rely on? Tax statuses, charity recognition, regulatory permissions, marks, memberships.
- **Decides** — Each one is an obligation source in itself, with its own conditions, reporting and publication duties; some unlock regimes, some exempt from them.
- **Code may propose** — Nothing, beyond a reference in copy or config. Cite and stop.
- **Trap** — Treating a status as a fact about the organisation rather than a bundle of continuing obligations. Starting an activity the current permission does not cover — the most common enforcement pattern in regulated sectors.
- **Found in** — ISO 19600 §4.5.1 ("permits, licences or other forms of authorization"); Grant Thornton (permissions/licences); FCA Final Notice, Charles Schwab UK 2020.

## 8. What is exchanged

- **Ask** — Money for what? Pick from a closed list: nothing, donations, memberships, event tickets, goods, digital content, subscriptions, services, accommodation, transport, travel packages, credit, insurance, investments, gambling, crypto, software or devices placed on a market.
- **Decides** — Consumer-contract regimes, withdrawal rights, distance selling, VAT, sector regimes for the riskier categories.
- **Code may propose** — Strongly: payment routes, product and order models, PSP SDKs, checkout flows.
- **Trap** — Inferring the category from the project name. The unselected categories matter as much as the selected ones — they are what rules out whole regimes.
- **Found in** — CRD Art. 16; Package Travel Directive Art. 3; VAT Directive place-of-supply rules; Grant Thornton (products/services).

## 9. How money moves

- **Ask** — PSP model: redirect, hosted fields, or handling card data yourself? Recurring mandates? Refunds and chargebacks? Do you pay out to third parties or hold funds for anyone?
- **Decides** — Payments-regulation exposure, card-data scope, mandate-scheme rules, whether you are yourself a payment or e-money service.
- **Code may propose** — Strongly: PSP SDKs, webhook handlers, mandate and subscription code, payout logic.
- **Trap** — Assuming the PSP absorbs every obligation. Some stay with the merchant by design.
- **Found in** — PSD2 Art. 97 and the SCA RTS; SEPA Regulation 260/2012 Art. 5; PCI DSS SAQ scoping.

## 10. Personal data

- **Ask** — What categories of personal data, about whom, where are they located, where is it stored and processed, any transfers outside the home region? Any category that is special by nature or by inference?
- **Decides** — Data-protection reach, special-category duties, transfer rules, records and impact-assessment triggers.
- **Code may propose** — Strongly: schema fields, third-party SDKs and their regions, analytics tags, consent flows.
- **Trap** — Special categories by *inference*: a diaspora membership list reveals ethnic origin; parish event RSVPs reveal religious belief. That characterisation is a human call, not a schema scan.
- **Found in** — GDPR Arts. 9, 30(5), 35 and Chapter V; NIST Privacy Framework ID.IM-P3, ID.IM-P7.

## 11. Third parties and outsourcing

- **Ask** — Which external services perform part of the operation — payments, email, hosting, analytics, identity, AI — and under what terms? Which are processors, which are independent controllers, which are critical to delivering the service?
- **Decides** — Contractual obligations that bind you; due-diligence and oversight duties; whose failure becomes your non-compliance.
- **Code may propose** — Strongly: dependencies, SDKs, environment variables, outbound endpoints.
- **Trap** — Assuming a vendor's terms are neutral. The risk allocation — breach clocks, controller status, reserves — lives in the contract, not the docs.
- **Found in** — ISO 37301 §4.6; APRA CPS 230 ¶27; CIS Controls v8 15.3; ISO/IEC 27001:2022 A.5.31 (contractual requirements).

## 12. Third-party content

- **Ask** — Do users upload or publish anything? Is it shown to the public? Do you connect users to other traders?
- **Decides** — Intermediary and platform regimes, and which tier within them.
- **Code may propose** — Strongly: upload endpoints, comment and review models, marketplace flows.
- **Trap** — Editor-curated content is the operator's own, not user content. Turning on comments changes the answer.
- **Found in** — DSA Art. 3(g) and Art. 19; Enhesa/Nimonik facility profiles (content and activity gating).

## 13. Role in the chain

- **Ask** — For each regime that binds: which hat? Controller or processor. Provider or deployer. Trader, intermediary, or organiser. Retailer or manufacturer.
- **Decides** — Which subset of a regime's duties is yours.
- **Code may propose** — Partially: who calls whom, who stores what.
- **Trap** — Assuming one role per regime. The same system wears different hats for different parties.
- **Found in** — GDPR Art. 4(7)–(8); AI Act Art. 3 (provider/deployer); NIST Privacy Framework ID.BE-P1; the FLI AI Act checker's role step.

## 14. Automation and AI

- **Ask** — Automated decisions with legal or similar effect on people? AI components, and in what role? Generated or manipulated content shown to users?
- **Decides** — AI-specific and automated-decision duties, transparency duties.
- **Code may propose** — Strongly: model SDKs, decision logic, generation endpoints.
- **Trap** — "It's just a chatbot." Transparency duties can bite at the lowest tier.
- **Found in** — AI Act Art. 50; GDPR Art. 22.

## 15. Time and change

- **Ask** — When did each of the above facts last change? What is about to change — a new product, market, licence, vendor, feature? When does each discovered regime start, stop, or change applying?
- **Decides** — Everything. Applicability is dated in both directions, and it is the *business* changes that regulators most often find unscreened.
- **Code may propose** — Partially: new dependencies, new routes, new locales, new payment code since the last profile.
- **Trap** — Stating a future-dated obligation as current. Stating a repealed one as live. Holding the correct date and never comparing it to today. Shipping a new product line without re-asking dimensions 3, 7, 8, 9 and 11.
- **Found in** — Commencement clauses of the AI Act, EAA and CRA; ISO 37301 §4.5(a) ("new and changed" obligations); BCBS 2005 ¶37 (new products, new business); FCA Final Notice, Infinox 2025.
