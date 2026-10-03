# Leaderboard · 2026-10-03 05:14

JEV `89552f7a`: latest check **PASS** (controls high 0%, 69 labels, balanced acc 0.80)
In-sample comparisons logged: **16** across 1 JEV versions. Expect some starred horizons by chance at this count; only out-of-sample confirms.

| pairing | tier | arm | strategy | n | in-sample edge | low−high edge | in-sample verdict | versions | OOS edge | OOS verdict | flags |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P-leadership-low | A→A (170) | low | cash_secured_put | 150 | -0.53% |  | NOT SUPPORTED | 1/3 |  |  |  |
| A1-ceo-change-low | A→B (33) | low | cash_secured_put | 31 | -1.01% |  | FRAGILE | 1/3 |  |  |  |
| A1-ceo-change-low | A→B (33) | low | covered_call | 31 | -1.78% |  | NOT SUPPORTED | 1/3 |  |  |  |
| A2-ceo-exit-abrupt | A→B (0) | high | protective_put |  |  |  | not run | 0/3 |  |  |  |
| A3-cfo-exec-low | A→A (134) | low | cash_secured_put | 116 | -0.58% |  | NOT SUPPORTED | 1/3 |  |  |  |
| A3-cfo-exec-low | A→A (134) | low | covered_call | 115 | -1.10% |  | NOT SUPPORTED | 1/3 |  |  |  |
| A4-restructuring-high | A→B (2) | high | collar |  |  |  | not run | 0/3 |  |  |  |
| B1-cyber-low | B→C (0) | low | cash_secured_put |  |  |  | not run | 0/3 |  |  |  |
| B2-cyber-high | B→C (4) | high | protective_put |  |  |  | not run | 0/3 |  |  |  |
| B3-director-exit-high | B→C (5) | high | protective_put |  |  |  | not run | 0/3 |  |  |  |
| B4-strategic-high | B→C (1) | high | long_call |  |  |  | not run | 0/3 |  |  |  |
| B4-strategic-high | B→C (1) | high | collar |  |  |  | not run | 0/3 |  |  |  |
| B5-good-news-call | B→B (119) | all | long_call | 103 | -0.15% |  | NOT SUPPORTED | 1/3 |  |  |  |
| B6-earnings | B→B (131) | all | cash_secured_put | 117 | +0.39% |  | IN-SAMPLE ONLY (better than ordinary days) | 1/3 | -0.46% | FAILED OUT-OF-SAMPLE |  |
| B6-earnings | B→B (131) | all | covered_call | 118 | +0.83% |  | IN-SAMPLE ONLY (better than ordinary days) | 1/3 | -1.59% | FAILED OUT-OF-SAMPLE |  |
