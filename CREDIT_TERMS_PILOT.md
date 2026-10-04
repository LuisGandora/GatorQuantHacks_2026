# Credit-term source-evidence measurement pilot (fixed 12 original 8-Ks)

Decision input: **1/12 filings have a verifiable paired maturity change, 0/12 a verifiable paired capacity change, 0/12 both.** This is a measurement feasibility pilot over a fixed 12-filing set, not a population prevalence estimate and not an economic result. No market or strategy outcome was read, no classifier or semantic score was built, and no trade hypothesis was frozen. The evidence and this report are annotated by the named model `opencode-go/deepseek-v4.1-flash`, with no additional pipeline inference or runtime model call, and with no human validation.

## Provenance and annotation scope

Annotations are authored by `opencode-go/deepseek-v4.1-flash`; they are not human-authored and no human validation is claimed. `jev_or_model_calls: 0` is a runtime-instrumentation count for the deterministic pipeline, not a claim that no model was involved: the hand-authored evidence and this report were produced by that model, and no additional runtime inference or model call was made during pipeline execution. The frozen protocol's `no model call` clause is disclosed here as a limitation/ambiguity: it is satisfied only as no additional runtime inference during pipeline execution, and it is not claimed that every interpretation of that clause was met, because the annotations and this report were model-authored as the user required, with no human validation. The exact-quote bound evidence set audits the sequence-1 original 8-K body only (an audited subset); the independent audit separately extended the paired-term search to every text-bearing exhibit and found no additional explicit same-facility old/new pair beyond PM. This is not an exhaustive whole-package annotation.

## Fixed selection

Three filings per year 2022-2025 chosen from the frozen historical-coverage enrollment metadata by ascending SHA256(accession_number), skipping a repeat economic ticker within the year. The 12 accessions and field definitions were frozen in a hashed protocol before any SEC package was read.

| Year | Ticker | Accession | Filed | SEC acceptance | SHA256(accession) |
|---|---|---|---|---|---|
| 2022 | T | 0001193125-22-062961 | 2022-03-02 | 2022-03-02 16:06:07 | 0c3423b2c1f56643... |
| 2022 | TMUS | 0001193125-22-263732 | 2022-10-17 | 2022-10-17 16:15:09 | 1be5fb42c55f7ded... |
| 2022 | CAT | 0000018230-22-000199 | 2022-09-06 | 2022-09-06 17:04:23 | 1df0cbfc285f0db8... |
| 2023 | GM | 0001193125-23-250325 | 2023-10-04 | 2023-10-04 06:30:29 | 117980f466e7cc6f... |
| 2023 | BKNG | 0001075531-23-000033 | 2023-05-19 | 2023-05-19 16:12:47 | 12ad0f829bd9bbbe... |
| 2023 | ADBE | 0001193125-23-010953 | 2023-01-19 | 2023-01-19 16:06:00 | 203bf4bb6ff66e61... |
| 2024 | CAT | 0001104659-24-096572 | 2024-09-04 | 2024-09-04 06:07:48 | 01fddb9aec219b83... |
| 2024 | HON | 0001193125-24-174346 | 2024-07-02 | 2024-07-02 16:20:03 | 064465dd2d3ecb38... |
| 2024 | PM | 0001104659-24-006244 | 2024-01-24 | 2024-01-24 16:06:38 | 097b2d99ceb907e9... |
| 2025 | HON | 0001193125-25-055636 | 2025-03-17 | 2025-03-17 16:22:58 | 01ffb8c7e87b5df3... |
| 2025 | LOW | 0000060667-25-000199 | 2025-10-09 | 2025-10-09 07:32:07 | 02fcdd5fc2056f7f... |
| 2025 | AMD | 0001193125-25-067902 | 2025-03-31 | 2025-03-31 08:37:51 | 0bec173ae8425d8e... |

## Pairing result

| Quantity | Filings |
|---|---:|
| Verifiable paired **maturity** change | 1 |
| Verifiable paired **capacity** change | 0 |
| Both | 0 |
| Old and new maturity both stated but not explicitly linked (unknown pairing) | 0 |
| Old and new capacity both stated but not explicitly linked (unknown pairing) | 0 |
| No verifiable paired maturity change (missing reads as unknown, not zero) | 11 |
| No verifiable paired capacity change (missing reads as unknown, not zero) | 12 |
| Filings with a literal Item 2.02 heading | 0 |

The only verifiable paired change is PM (2024-01-24): the Extension Agreement extends the expiration date of one facility from January 30, 2024 to January 28, 2025 (364 days). No filing states an old and a new capacity for the same linked facility. HON (2025) shows an old $1.5 billion facility and a new $3.0 billion facility, but the 8-K does not state they are the same facility, so it is not counted as a pair.

## Source-evidence table (manually reviewed; exact quotes, offsets in the ignored JSON)

Amounts are shown in explicit USD; `null` means not stated. `pair` is the linkage kind computed only from an explicit same-facility old/new statement.

| Ticker | Facility | Old maturity | New maturity | Old cap (USD) | New cap (USD) | Currency | Effective/announce | Pair |
|---|---|---|---|---:|---:|---|---|---|
| T | Amended and Restated Term Loan Credit Agreement |  | 2022-12-31 |  | 7,350,000,000 | USD | 2022-03-02 |  |
| TMUS | Amended and Restated Credit Agreement |  | 2027-10-17 |  | 7,500,000,000 | USD | 2022-10-17 |  |
| TMUS | letter of credit sub-facility |  |  |  | 1,500,000,000 | USD |  |  |
| TMUS | swingline loan sub-facility |  |  |  | 500,000,000 | USD |  |  |
| CAT | 364-Day Facility |  | 2023-08-31 |  | 3,150,000,000 | USD | 2022-09-01 |  |
| CAT | Local Currency Addendum |  |  |  | 100,000,000 | USD |  |  |
| CAT | Japan Local Currency Addendum |  |  |  | 100,000,000 | USD |  |  |
| CAT | Three-Year Facility |  | 2025-08-29 |  |  |  | 2022-09-01 |  |
| CAT | Five-Year Facility |  | 2027-09-01 |  |  |  | 2022-09-01 |  |
| GM | 364-Day Revolving Credit Agreement |  | 2024-10-01 |  | 6,000,000,000 | USD | 2023-10-03 |  |
| BKNG | Credit Agreement |  | 2028-05-17 |  | 2,000,000,000 | USD | 2023-05-17 |  |
| BKNG | letters of credit |  |  |  | 80,000,000 | USD |  |  |
| BKNG | swingline loans |  |  |  | 100,000,000 | USD |  |  |
| BKNG | credit agreement, dated as of August 14, 2019 |  |  | 2,000,000,000 |  | USD |  |  |
| ADBE | Term Loan Credit Agreement |  |  |  | 3,500,000,000 | USD | 2023-01-19 |  |
| CAT | 364-Day Facility |  | 2025-08-28 |  | 3,150,000,000 | USD | 2024-08-29 |  |
| CAT | Local Currency Addendum |  |  |  | 100,000,000 | USD |  |  |
| CAT | Japan Local Currency Addendum |  |  |  | 100,000,000 | USD |  |  |
| CAT | Three-Year Facility |  | 2027-08-29 |  |  |  | 2024-08-29 |  |
| CAT | Five-Year Facility |  | 2029-08-29 |  |  |  | 2024-08-29 |  |
| HON | Second 364-Day Credit Agreement |  | 2025-07-01 |  | 1,500,000,000 | USD | 2024-07-02 |  |
| PM | 364-day revolving credit facility | 2024-01-30 | 2025-01-28 |  | 1,700,000,000 | USD | 2024-01-30 | maturity |
| HON | 364-Day Credit Agreement |  | 2026-03-16 |  | 3,000,000,000 | USD | 2025-03-17 |  |
| HON | 364-day credit agreement dated as of March 18, 2024 |  |  | 1,500,000,000 |  | USD |  |  |
| LOW | Term Loan Credit Agreement |  |  |  | 2,000,000,000 | USD | 2025-09-16 |  |
| AMD | ZT Credit Agreement |  | 2026-12-31 |  |  | USD |  |  |
| AMD | master receivables purchase agreement |  |  |  |  | USD |  |  |

Sub-limit rows carrying a `borrowing_currency` annotation (the CAT 2022 and CAT 2024 local-currency addenda) record a USD-equivalent ceiling of $100 million; that ceiling is not the currency borrowed, and each row is kept separate from its parent facility and never summed in.

## Corrections applied to the audited snapshot

- **DEV-1 (closed):** the two AMD raw dollar figures (`$641,666,666.67`, ZT Credit Agreement; `$850,000,000`, master receivables purchase agreement) carry no thousands/millions/billions scaling word, so under the frozen `amounts` clause their numeric capacity is **null**; each raw figure is retained only in an off-protocol provenance note and is never scaled or counted. A fail-fast validator now rejects any numeric amount that lacks an explicit scaling word.
- **DEV-2 (closed):** the CAT 2024 filing adds the two distinct local-currency addendum sub-limits (`Local Currency Addendum`, `Japan Local Currency Addendum`) at their exact quote offsets, parallel to the CAT 2022 rows; each is a $100 million USD-equivalent sub-limit inside the 364-Day Aggregate Commitment and is never summed into the $3.15 billion parent. The CAT 2022 rows now carry the same borrowing-currency clarification.
- The original audited derived snapshot and code/report hashes are archived under the ignored `credit_terms_pilot/audit_history/` with a manifest; the archive is a static record, not a compatibility execution path. The corrected snapshot replaced by this cleanup is archived separately under `credit_terms_pilot/audit_history/final_review/` with its own manifest, also a static read-only record and not a compatibility path. Full details are in `CREDIT_TERMS_PILOT_CORRECTIONS.md`.

## Mechanism: maturity runway versus capacity

The two credit terms carry different economics. A **capacity** change alters the size of an undrawn commitment: a larger revolver is more headroom, but an unused commitment is not cash and does not remove operating, demand or litigation risk, so its link to equity downside is weak for mega-cap issuers. A **maturity** change alters the refinancing calendar: pushing a term out reduces the near-term rollover pressure and the chance that a firm must refinance into a stressed market, which is a liquidity-runway channel that can matter to equity downside even when the commitment is undrawn. On that reasoning a paired maturity extension is the more economically meaningful of the two terms, and it is the measurement that this pilot can actually verify.

## Chief objections

- The pilot is tiny and fixed by hash, not random. It cannot estimate prevalence in the 147-filing population; it can only show whether measurement is possible filing by filing.
- Most 8-Ks announce a new or replacement facility and do not recite a linked prior term, so a verifiable pair is the exception; an absent or unlinked prior term is unknown, not evidence that the new term was the whole disclosure. Verifying paired changes requires an amendment that recites both dates, which is a minority of disclosures; the 1/12 result reflects that disclosure structure, not necessarily economic rarity.
- A maturity extension may be scheduled and anticipated, and mega-cap TOP_100 issuers are rarely funding-constrained, so even a clean measurement does not imply a priced effect.
- The filing/announcement date is not the economic effective date for every facility, and a term extension changes the liability schedule rather than available capital.
- The static September-2026 TOP_100 carries survivorship and large-cap selection bias.

## Recommendation

**Recommendation: do not extend this measurement to all 147.** The pilot is a measurement-feasibility result, not a route to a priced effect, and it gives insufficient financial feasibility at scale. The paired yield is low: 1 of 12 filings carries a verifiable paired maturity change, none carries a paired capacity change, and the remaining 11 of 12 lack a verifiable paired maturity change (missing reads as unknown, not evidence that all 11 state a new term), so extending the manual annotation to all 147 would be a large effort with a low expected paired yield. More important, the authorized contestant financial window is 2024-2025, where the direct `credit_facility` cohort is only about 62 filings, too few to support a powered numerical maturity-runway test after strict marks. No option price, payoff or economic outcome is opened for this direction, no price study or trade hypothesis is frozen, and a low paired yield is not a guarantee about any other cohort.

## Boundaries

Original SEC packages only, at most 2 requests/second, with a hash-and-header cache. The historical coverage protocol hash and all six EARNINGS_PAYOFF_FREEZE.json hashes were recomputed and preserved; prior frozen experiments were not modified and nothing was committed. The older unrelated novelty cache that exposed 74 reserved 2023 dates was not read; the financial replication is unrun and the actual judges window is unknown. Private packages, parsed text and cache live in the ignored `credit_terms_pilot/` directory; exact character offsets are in the ignored `source_evidence.json` and are re-verified by the `verify` stage.
