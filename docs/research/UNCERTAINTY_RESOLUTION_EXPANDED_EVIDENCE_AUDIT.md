# Experiment 9B: expanded leadership-transition evidence audit

Outcome-blind finalization. No price, option record, payoff, ordinary-day market record, 2026 filing or judges artifact was read and no P&L was computed. This document contains aggregate metadata only: no licensed filing passage text and no raw probability value.

Protocol `541101f997b5ebf7f4c9b26f60443a1ca217576e75fea513820e3194e077e5b0`.

Taxonomy decision table `7659521f22637435b68c60871bd9903bbbe2db7154fc841b226b572f9fed3b08`.

Semantic tables `9a1f8e309fb06ffacd7363a89d5e3cb0272960e42412e829d361065bb9f94d30`.

## 1. Window and population

| Quantity | Enrolled (before source gate) | Measured (after source gate) |
|---|---:|---:|
| Events | 242 | 226 |
| Distinct issuers | 87 | 84 |
| Filing-date range | 2024-01-03 .. 2025-12-23 | 2024-01-03 .. 2025-12-23 |
| Frozen window | 2024-01-01 .. 2025-12-31 | same |
| Oversized-package exclusions | - | 16 |

The enrollment is 242 accessions across 87 issuers; 226 accessions across 84 issuers were measured, and 16 valid source exclusions were preregistered for over-ceiling packages. An explicit documented exclusion is not an automatic whole-experiment failure.

## 2. Frozen taxonomy

### Included tags (exactly six)

| Tag | Massive definition |
|---|---|
| `ceo_appointment` | New CEO appointment with background, employment terms, and compensation. |
| `ceo_departure` | CEO departure, resignation, retirement, termination, or death with circumstances and transition. |
| `cfo_appointment` | New CFO appointment with background, terms, and transition timeline. |
| `cfo_departure` | CFO departure with circumstances and transition arrangements. |
| `executive_officer_appointment` | Other named executive officer appointment with position and terms. |
| `executive_officer_departure` | Other named executive officer departure with circumstances. |

Tag precedence for an accession carrying more than one included tag: `ceo_departure`, `cfo_departure`, `executive_officer_departure`, `ceo_appointment`, `cfo_appointment`, `executive_officer_appointment`.

### Excluded near neighbors (exactly 31)

| Tag | Massive definition | Rationale |
|---|---|---|
| `acquisition_agreement` | Definitive agreement to acquire a business, subsidiary, or division, specifying price, financing, and conditions. | M&A deal agreement: a different economic mechanism. |
| `activist_investor_campaign` | Activist engagement including demands, proxy contests, settlements, or board nominations. | Shareholder activism: a different economic mechanism. |
| `annual_earnings` | Annual financial results with year-over-year comparisons, key metrics, and forward outlook. | Ordinary earnings announcement: a different economic mechanism. |
| `business_line_exit` | Decision to exit or discontinue a business line, product category, or market segment. | Business-line exit: a different economic mechanism. |
| `bylaw_amendment` | Bylaw amendment with nature of changes and impact on governance or shareholder rights. | Bylaw amendment: a governance-document change, not a leadership transition. |
| `charter_amendment` | Certificate or articles of incorporation amendment, including changes to shareholder voting, dividend, or liquidation rights. Use this for the governance action; use preferred_stock_modification for preferred-specific term changes. | Charter amendment: a governance-document change, not a leadership transition. |
| `code_of_ethics_change` | Code of ethics amendment or waiver for principal executive, financial, or accounting officers. | Code-of-ethics amendment or waiver: a governance-document change, not a leadership transition. |
| `control_acquisition` | Acquisition of controlling interest by new shareholder, investor group, or entity. | Acquisition of a controlling interest: a corporate-control event, not an executive leadership transition. |
| `control_disposition` | Loss of controlling interest through sale, dilution, or other transaction. | Disposition of a controlling interest: a corporate-control event, not an executive leadership transition. |
| `debt_issuance` | Bonds, notes, or debentures issuance with principal, rate, maturity, covenants, and use of proceeds. | Financing event: a different economic mechanism. |
| `director_appointment` | New director election or appointment with background, qualifications, and committee assignments. | Director-only election or appointment with no executive-management transition; the ontology departing-executive referent is absent. |
| `director_departure` | Director resignation, removal, retirement, or decision not to stand for re-election, including any disagreements causing departure. | Director-only resignation or removal with no executive-management transition; the ontology departing-executive referent is absent. |
| `director_nomination` | Shareholder director nominations under proxy access or advance notice bylaws. | Shareholder director nomination: a director-level governance contest, not an executive leadership transition. |
| `dividend_declaration` | Cash dividend, special dividend, or distribution declaration with amount, record date, and payment date. | Shareholder-return event: a different economic mechanism. |
| `executive_compensation_change` | Material executive or director compensation changes including new employment agreements, amendments, severance, change-in-control provisions, or equity awards. Consolidates all compensation-related events into a single tag. | Compensation and employment terms, not a leadership appointment or departure; the six-dimension succession ontology does not apply. |
| `facility_closure` | Facility closures, consolidations, or relocations with locations, employees, and charges. | Facility closure or relocation: a different economic mechanism. |
| `fiscal_year_change` | Fiscal year end change with old and new dates, transition period, and rationale. | Fiscal-year change: a governance-document change, not a leadership transition. |
| `going_private_transaction` | Going-private, management buyout, or similar transaction ending public trading. | Going-private or buyout transaction: an ownership/control event, not an executive leadership transition. |
| `guidance_issuance_or_update` | Issuance, revision, or reaffirmation of financial guidance including revenue projections, earnings estimates, and key metric forecasts. Consolidates all guidance-related disclosures regardless of disclosure mechanism. | Financial guidance: a different economic mechanism. |
| `guidance_withdrawal` | Withdrawal or suspension of previously issued financial guidance. | Guidance withdrawal: a different economic mechanism. |
| `involuntary_bankruptcy` | Involuntary bankruptcy petition by creditors with petitioner identity and amounts. | Bankruptcy or insolvency: a different economic mechanism. |
| `merger_agreement` | Definitive merger or business combination agreement with exchange ratios and terms. | M&A deal agreement: a different economic mechanism. |
| `preliminary_results` | Preliminary or unaudited financial results before formal statement preparation. | Preliminary financial results: a different economic mechanism. |
| `private_placement` | Private placement of unregistered equity to accredited investors or QIBs, with terms and registration rights. | Equity financing event: a different economic mechanism. |
| `public_offering` | Public equity offering or registered direct offering with underwriting terms. | Equity financing event: a different economic mechanism. |
| `quarterly_earnings` | Quarterly financial results including revenue, net income, EPS, and key operating metrics with management commentary. | Ordinary earnings announcement: a different economic mechanism. |
| `restructuring_plan` | Restructuring or cost reduction initiative with expected charges, timeline, and anticipated savings. | Restructuring or cost-reduction initiative: a different economic mechanism. |
| `reverse_merger` | Reverse merger where private operating company merges with public shell, becoming publicly traded. Includes shell company status changes. | Reverse merger or shell status change: an M&A/control event, not an executive leadership transition. |
| `share_repurchase_program` | Share buyback program authorization, expansion, or update with amount and timing. | Shareholder-return event: a different economic mechanism. |
| `voluntary_bankruptcy` | Voluntary bankruptcy filing (Chapter 7, 11, 15) with circumstances and expected impact. | Bankruptcy or insolvency: a different economic mechanism. |
| `workforce_reduction` | Significant layoffs, RIFs, or voluntary separation programs with positions, severance, and timeline. | Layoffs or separation programs: a different economic mechanism. |

The excluded near-neighbor count is 31, taken from the frozen taxonomy decision table.

## 3. Tag composition: multi-tag versus accession-deduplicated primary tag

An accession tagged under more than one included category is counted once under the first tag in the frozen precedence; its full tag set is retained as `all_tags`. Enrollment all-tag counts therefore sum above the accession count, and measured all-tag counts are reported separately from the accession-deduplicated primary-tag counts.

| Tag | Enrolled all-tag events | Measured all-tag events | Measured primary tag (accession-deduplicated) |
|---|---:|---:|---:|
| `ceo_appointment` | 17 | 16 | 1 |
| `ceo_departure` | 31 | 28 | 28 |
| `cfo_appointment` | 34 | 32 | 8 |
| `cfo_departure` | 31 | 28 | 27 |
| `executive_officer_appointment` | 106 | 98 | 41 |
| `executive_officer_departure` | 132 | 125 | 121 |

Measured accessions carrying more than one included tag: 91 of 226.

## 4. Primary-group composition (from actual qualifying rows)

The existing overall `tag_composition` covers all measured rows and is NOT the primary group. The table below is recomputed from the rows that actually pass the frozen RESOLUTION_EVENT rule.

| Tag | Qualifying events | Issuers | Share of primary group |
|---|---:|---:|---:|
| `ceo_appointment` | 1 | 1 | 0.0400 |
| `ceo_departure` | 1 | 1 | 0.0400 |
| `cfo_appointment` | 2 | 2 | 0.0800 |
| `cfo_departure` | 4 | 4 | 0.1600 |
| `executive_officer_appointment` | 3 | 3 | 0.1200 |
| `executive_officer_departure` | 14 | 14 | 0.5600 |

Primary group: 25 events, 22 issuers. Tags contributing more than 60%: none. Diagnostic: none.

## 5. Original departure membership using all_tags

Baseline C is the original `executive_officer_departure` population. It is measured by all_tags membership, not merely the primary tag, because an accession primarily tagged under another included category can still carry the original departure tag.

| Membership basis | Events |
|---|---:|
| Enrolled, all_tags | 132 |
| Measured primary tag | 121 |
| Measured, all_tags | 125 |

Membership uses all_tags, not merely the primary tag, because an accession whose primary tag is another included tag can still carry the original executive_officer_departure tag.

## 6. Source gate: exclusions, size policy, prior coverage, Class P/C

Request ceiling: 26000 serialized UTF-8 bytes. The oldest Class P filings are trimmed first and the trim is recorded; the current filing text is never truncated. If the current package cannot fit after all Class P trims, the event is recorded as excluded and is not measured.

Exclusions by primary tag:

| Tag | Excluded events | Excluded issuers |
|---|---:|---:|
| `ceo_departure` | 3 | 3 |
| `cfo_departure` | 3 | 3 |
| `executive_officer_appointment` | 3 | 3 |
| `executive_officer_departure` | 7 | 5 |

Full exclusion list (metadata only):

| Accession | Ticker | Filing date | Primary tag | After package bytes | Before over ceiling | After over ceiling |
|---|---|---|---:|---:|---|---|
| `0000764180-24-000007` | MO | 2024-02-01 | `executive_officer_departure` | 71263 | False | True |
| `0001613103-24-000006` | MDT | 2024-02-20 | `executive_officer_departure` | 46028 | False | True |
| `0001193125-24-139371` | CSCO | 2024-05-15 | `executive_officer_departure` | 53012 | False | True |
| `0001373715-24-000269` | NOW | 2024-07-24 | `executive_officer_departure` | 43433 | False | True |
| `0000066740-24-000088` | MMM | 2024-08-01 | `cfo_departure` | 30019 | False | True |
| `0001108524-24-000020` | CRM | 2024-08-28 | `cfo_departure` | 46314 | False | True |
| `0001373715-24-000342` | NOW | 2024-10-23 | `executive_officer_appointment` | 47199 | False | True |
| `0000050863-24-000173` | INTC | 2024-12-03 | `ceo_departure` | 21366 | False | True |
| `0000004962-25-000010` | AXP | 2025-01-30 | `executive_officer_departure` | 19955 | False | True |
| `0000773840-25-000025` | HON | 2025-04-08 | `executive_officer_appointment` | 62846 | False | True |
| `0001065280-25-000175` | NFLX | 2025-04-17 | `ceo_departure` | 39106 | False | True |
| `0001373715-25-000124` | NOW | 2025-04-23 | `executive_officer_departure` | 40273 | False | True |
| `0001613103-25-000078` | MDT | 2025-05-21 | `executive_officer_departure` | 66993 | False | True |
| `0001193125-25-209990` | TMUS | 2025-09-22 | `ceo_departure` | 43166 | False | True |
| `0000077476-25-000055` | PEP | 2025-10-09 | `cfo_departure` | 58690 | False | True |
| `0001628280-25-048526` | PM | 2025-11-04 | `executive_officer_appointment` | 19721 | False | True |

All 16 exclusions carry reason `current_package_exceeds_request_ceiling` with explicit before/after ceiling flags; source rows: 242 enrolled = 226 measured + 16 excluded.

| Prior coverage | Events |
|---|---:|
| `window_complete` | 133 |
| `prior_retrieved` | 215 |
| `coverage_adequate` | 133 |
| Events with at least one Class P prior filing | 159 |
| Events with a Class C statement | 55 |
| Class C lexical matches | 55 |
| Events trimmed to the request ceiling | 3 |

Class C passages are self-reported by the current filing and are flagged as such; they are not independent confirmation of the prior state.

## 7. Valid dimensions, transitions, ResolutionDelta and freshness

Valid dimensions per event:

| Valid dimensions | Events |
|---:|---:|
| 0 | 61 |
| 1 | 47 |
| 2 | 32 |
| 3 | 19 |
| 4 | 22 |
| 5 | 30 |
| 6 | 15 |

Transition distribution over all 1356 dimension-pairs:

| Transition | Count |
|---|---:|
| closing | 50 |
| insufficient_evidence | 860 |
| opening | 47 |
| unchanged | 399 |

ResolutionDelta distribution:

| ResolutionDelta | Events |
|---:|---:|
| -3 | 1 |
| -2 | 8 |
| -1 | 23 |
| 0 | 159 |
| 1 | 27 |
| 2 | 6 |
| 3 | 2 |

Calendar freshness (Baseline B): fresh 26, stale 158, unknown 42. Events with a lag: 184; min / median / mean / max: 0 / 56.5 / 68.36413043478261 / 248 trading sessions.

Mechanism composition (Resolution / Neutral / Opening / unmeasured):

| Group | Events | Issuers |
|---|---:|---:|
| Resolution | 33 | 27 |
| Neutral | 95 | 51 |
| Opening | 37 | 25 |
| unmeasured | 61 | 49 |

## 8. Runtime: job slots, distinct payloads, live HTTP, throughput

A payload-keyed cache can serve more job slots than there are distinct payloads, so duplicates and races are disclosed explicitly. Wall-clock throughput is the primary rate; the summed per-request latency is a serial-equivalent measure that ignores concurrency and cache hits. Runtime speed is an execution property and is never evidence of alpha.

| Statistic | Value |
|---|---:|
| Job slots (requests) | 904 |
| Stage A job slots | 452 |
| Stage B job slots | 452 |
| Distinct request payloads | 786 |
| Cache hits | 113 |
| Live HTTP requests | 791 |
| HTTP attempts (retries included) | 791 |
| Valid responses | 903 |
| Malformed responses | 1 |
| Valid rate | 0.9988938053097345 |
| Malformed rate | 0.0011061946902654867 |
| Judgments | 4810 |
| Wall time (s) | 51.91363595900475 |
| Judgments per wall second | 92.65388391979266 |
| Serial-equivalent judgments per second | 23.75213795163067 |

Job slots served from cache or shared payloads: 113 of 904 slot(s); distinct payloads: 786; live HTTP requests: 791. Malformed request keys: [['B', '0000059478-24-000146', 'after']]. A payload-keyed cache can serve several job slots from one payload, so job slots exceed distinct payloads by construction; concurrent identical payloads can also race on the first cache write and one live HTTP request is recorded per cache miss. These are execution bookkeeping properties, not alpha.

## 9. Blinded measurement validation

The deterministic packet target is 60 events; the actual audited packet carries 74 events because mandatory strata and pairs can exceed the target. It contains 223 pairs with 27 truncated passage(s), transparently. The reviewer saw before/after evidence, the ontology dimension and the allowed states only, and never the JEV answer, probability, ResolutionDelta, group membership or any market data.

| Packet quantity | Value |
|---|---:|
| Target events | 60 |
| Actual audited events | 74 |
| Audited pairs | 223 |
| Truncated passages | 27 |
| Identifier redactions | 574 |
| Class C pairs | 28 |
| Reviewer verdicts | 223 |
| Strata covered | 18 |
| Strata uncovered | 0 |
| Packet bytes | 668282 |

Audited pairs per dimension:

| Dimension | Pairs |
|---|---:|
| `successor_identity` | 70 |
| `successor_permanence` | 55 |
| `search_status` | 11 |
| `effective_timing` | 25 |
| `transition_arrangement` | 33 |
| `leadership_continuity` | 29 |

Independent audit agreement (matched / total):

| Quantity | Agreement |
|---|---:|
| Exact before-state | 167/223 = 0.749 |
| Exact after-state | 186/223 = 0.834 |
| Exact both sides | 140/223 = 0.628 |
| Transition sign, all pairs (both-UNKNOWN counts as agreement) | 170/223 = 0.762 |
| Transition sign, both sides determinate | 85/129 = 0.659 |
| False closing (JEV closing, independent not) | 24/50 = 0.480 |
| False opening (JEV opening, independent not) | 20/47 = 0.426 |

Per-dimension transition-sign agreement:

| Dimension | Agreement |
|---|---:|
| `successor_identity` | 59/70 = 0.843 |
| `successor_permanence` | 54/55 = 0.982 |
| `search_status` | 10/11 = 0.909 |
| `effective_timing` | 13/25 = 0.520 |
| `transition_arrangement` | 14/33 = 0.424 |
| `leadership_continuity` | 20/29 = 0.690 |

Per-tag transition-sign agreement:

| Tag | Agreement |
|---|---:|
| `ceo_appointment` | 0/3 = 0.000 |
| `ceo_departure` | 9/9 = 1.000 |
| `cfo_appointment` | 10/15 = 0.667 |
| `cfo_departure` | 21/31 = 0.677 |
| `executive_officer_appointment` | 28/36 = 0.778 |
| `executive_officer_departure` | 102/129 = 0.791 |

Aggregate sign arithmetic (exact frozen gate):

| Read | Closing | Opening | Closing minus opening | Sign |
|---|---:|---:|---:|---:|
| Frozen JEV measurement | 50 | 47 | 3 | 1 |
| Independent blinded read | 29 | 28 | 1 | 1 |

Frozen gate verdict: **PASS**. The gate requires both aggregate signs to be non-zero and to agree; a zero sign on either read fails. An aggregate pass certifies the direction on the audited subset only and is not perfect per-pair labeling.

## 10. Custody limitation

Individual events/enrollment/source_filings/package files were written through freeze() before the live semantic calls, so their mtimes precede the semantic tables. The combined input_manifest.json is created now, after the semantic run and before any economics. No data changed. There is no pre-existing prior_source_pool_hash; the source-filings digest here is computed at finalization.

Explicit reporting-custody limitation, not a silent implementation or design alteration. The committed protocol and its digest are not revised to hide it.

## Reproduce

```
.venv/bin/python uncertainty_resolution_expanded_finalize.py
```

