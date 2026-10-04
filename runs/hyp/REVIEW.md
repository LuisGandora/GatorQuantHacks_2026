# Review of twelve conditional-edge hypotheses (hyp-v1, 2026-10-04)

## 1. Verdicts

Edge is vs ordinary days, mean over h=21, h=42 and expiry, per $1 of spot. No hypothesis passed BH, so none was taken to out-of-sample.

- H01_drift_after_drop: OK, n 334 / 1150, edge +0.47% (CI -0.82% to +1.73%), p 0.464, BH fail. No OOS.
- H02_reversal_after_drop: OK, n 365 / 1150, edge +0.27% (CI -0.47% to +0.91%), p 0.442, BH fail. No OOS.
- H03_inverted_term: OK, n 307 / 1102, edge +0.24% (CI -1.17% to +1.60%), p 0.705, BH fail. No OOS.
- H04_rich_put_skew: OK, n 351 / 1110, edge +0.17% (CI -0.50% to +0.77%), p 0.585, BH fail. No OOS.
- H05_sticky_vol: OK, n 299 / 1130, edge +0.32% (CI -0.91% to +1.55%), p 0.618, BH fail. No OOS.
- H06_attention_calls: OK, n 328 / 1162, edge +0.58% (CI -0.74% to +1.83%), p 0.376, BH fail. No OOS.
- H07_prefiling_put_volume: OK, n 329 / 1162, edge -0.05% (CI -1.30% to +1.20%), p 0.966, BH fail. No OOS.
- H08_negative_tone: OK, n 19 / 1289, edge -1.83% (CI -4.72% to +1.29%), p 0.224, BH fail. No OOS.
- H09_outside_successor: TOO FEW (<15 selected), n 12 / 47. Not tested.
- H10_bundled_filing: OK, n 112 / 1289, edge -1.09% (CI -2.50% to +0.51%), p 0.170, BH fail. No OOS.
- H11_dividend_raise: TOO FEW (<15 selected), n 8 / 76. Not tested.
- H12_resolution_events: OK, n 49 / 57, edge -0.71% (CI -1.54% to +0.20%), p 0.124, BH fail. No OOS.

## 2. Candidate edges

No candidate edge.

## 3. Caveats

- H01 and H02 are mirror images (same events, opposite trades), so at most one can be right.
- Small pools: H09, H11 and H12 have small samples, so wide intervals are expected. H09 and H11 were too small to test at all, and H08 has only 19 selected events.
- Net P&L is the trade's own absolute P&L, and it moves with the market. Only "edge vs ordinary days" is the test. Positive net figures (for example H06 at +1.43% net 2x) don't indicate an edge.
- A BH pass without out-of-sample confirmation is not an edge. Here nothing passed BH, so the point is moot.
- Twelve hypotheses were listed, ten were tested, and zero passed BH at q=0.10. The smallest p-value was 0.124 (H12).

## 4. What to try next

No hypothesis passed BH in-sample, so there's nothing to extend, and the well-supported result is a null across the tested set. Any follow-up, including a variant of a near miss like H12 or H10, would need a new pre-registration and new data. Re-cutting this sample to rescue one would just be the false discovery the design guards against.
