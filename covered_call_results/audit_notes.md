# Entry-evidence audit (rules unchanged)

The six usable routine in-sample appointments at the frozen 21-session primary setting were
read against the saved same-filing evidence. No rule or event was changed after pricing.

- **SCHW CEO, 2024-10-01:** President Richard Wurster succeeds Walter Bettinger on 2025-01-01;
  the same accession describes Bettinger's intended retirement. Scheduled internal succession.
- **ISRG CEO, 2025-05-15:** Current president David Rosa succeeds Gary Guthart on 2025-07-01;
  Guthart becomes executive chair and continues as director. Scheduled internal transition.
- **BRK.B CEO, 2025-05-08:** Vice-chair Greg Abel becomes CEO on 2026-01-01; Warren Buffett
  remains chair. The excerpt explicitly notes the announcement on 2025-05-03: this is a
  post-filing strategy, not entry ahead of the announcement. Prior public pricing is a limitation.
- **GD CFO, 2024-01-05:** Current SVP Kimberly Kuryea transitions to CFO on 2024-02-15.
  Internal transition disclosed over 30 days before its effective date.
- **TMO CFO, 2025-07-23:** Current VP James Meyer succeeds the incumbent on 2026-03-01.
  Long-scheduled internal succession.
- **SCHW CFO, 2024-07-25:** Deputy CFO Michael Verdeschi becomes CFO on 2024-10-01.
  Internal promotion with a disclosed future effective date.

These excerpts support the declared planned classification. They do not establish absence of
other contemporaneous adverse news or full earnings-calendar coverage. The audit is based
on the retrieved evidence, not an independent review of every page of the complete filing.
The entire event inventory and entry evidence are preserved for judges to review.

## Historical-validation audit

- **AMGN CFO, 2026-05-19:** Thomas Dittrich joins as EVP on 2026-07-01 and becomes CFO on
  2026-09-01; Peter Griffith's future retirement and continuing advisory employment are
  described in the same filing. This satisfies the frozen planned-retirement rule even
  though the incoming CFO is external.
- **CAT tagged CEO resignation, 2026-01-06 — invalid role:** the excerpt states that
  D. James Umpleby resigns **as a board member**, while describing him as a **former** CEO.
  This is not a current CEO resignation. Massive's broad `ceo_departure` tag and the older
  role-proximity regex let it through. The original frozen output is retained for traceability;
  the published audited secondary tables exclude it by text, regardless of P&L. The
  appointment tests and their frozen decisions are unaffected.

Unknown events remain excluded from the primary appointment test. The teammate's JEV-low
proxy is reported only as a predefined sensitivity; its broader sample is not a replacement
for confirmed routine changes. Role-linked resignations remain separate secondary analyses.
