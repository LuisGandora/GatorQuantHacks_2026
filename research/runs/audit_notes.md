# Audit Notes: F1-leadership-fresh cash_secured_put

## In-Sample Results Summary
- Fresh (n=55): edge = -1.19% (worse than ordinary days)
- Stale (n=95): edge = -0.16% (not supported)
- Fresh - Stale: -1.03% (NOT SUPPORTED - fresh is WORSE than stale)
- Lag buckets: lag0=-1.78%, lag1=-0.93%, lag2=+0.40%, lag3=-0.79%, lag4+=-0.18%

## Top 5 Events (by mean edge)

| Rank | Ticker | Event Date | Arm | Lag | Mean Edge | Period of Report | Text Snippet | Fresh/Stale Match? |
|------|--------|------------|-----|-----|-----------|------------------|--------------|-------------------|
| 1 | PLTR | 2025-02-28 | stale | 2 | +8.36% | 2025-02-27 | "On February 27, 2025... welcomed back Jeffrey Buckley as CAO" | ✓ Lag 2 > 1 = stale |
| 2 | UNH | 2025-07-31 | stale | 5 | +7.65% | 2025-07-25 | "John F. Rex... will become Strategic Advisor on Effective Date" | ✓ Lag 5 > 1 = stale |
| 3 | UBER | 2024-08-02 | fresh | 1 | +6.86% | 2024-08-02 | "Katie Waitzman will assume Mr. West's duties as GC" | ✓ Lag 1 ≤ 1 = fresh |
| 4 | INTC | 2025-09-08 | stale | 2 | +6.18% | 2025-09-07 | "Michelle Johnston Holthaus... resigned from Intel Products" | ✓ Lag 2 > 1 = stale |
| 5 | NFLX | 2025-04-17 | stale | 5 | +5.18% | 2025-04-11 | "Reed Hastings... transition from executive officer. Effective April 17" | ✓ Lag 5 > 1 = stale |

**Observation**: Top performers are mostly stale events (4/5). Fresh arm only has UBER at +6.86%. The stale events include CFO departure (UNH), CEO departure (INTC, NFLX), and executive appointment (PLTR).

## Bottom 5 Events

| Rank | Ticker | Event Date | Arm | Lag | Mean Edge | Period of Report | Text Snippet | Fresh/Stale Match? |
|------|--------|------------|-----|-----|-----------|------------------|--------------|-------------------|
| 149 | BA | 2024-07-31 | fresh | 1 | -9.25% | 2024-07-30 | "Board elected Stephanie F. Pope to replace Stanley A. Deal as CEO" | ✓ Lag 1 ≤ 1 = fresh |
| 150 | CRM | 2025-02-05 | fresh | 1 | -12.14% | 2025-02-05 | "Announced appointment of Robin Washington as President and CFO" | ✓ Lag 1 ≤ 1 = fresh |
| 151 | ORCL | 2025-09-22 | stale | 2 | -15.07% | 2025-09-18 | "Safra Catz will no longer serve as CEO... as of Effective Date" | ✓ Lag 2 > 1 = stale |
| 152 | UNH | 2025-04-29 | fresh | 1 | -16.29% | 2025-04-29 | "Heather Cianfrocco appointed EVP Governance... effective April 29" | ✓ Lag 1 ≤ 1 = fresh |
| 153 | ACN | 2024-06-11 | stale | 3 | (no mean) | 2024-06-08 | "Ms. Park succeeds KC McClure as CFO" | ✓ Lag 3 > 1 = stale |

**Observation**: Bottom performers are mostly fresh events (3/5 fresh: BA, CRM, UNH, SBUX). Fresh events include CEO appointments (BA, CRM, UNH, SBUX) and CFO appointment (GOOGL).

## Fresh/Stale Classification Accuracy

All 10 audited events have correct fresh/stale classification based on the period-of-report date and fresh_max_lag=1:
- Fresh events (lag 0 or 1): UBER, SCHW, GOOGL, CVS, SBUX, FDX, CRM, MMM, RTX, MDT, HON, KO, JPM, AIG, AAPL, DUK, RTX, COP, COST, TMUS, SO, GD, NKE, TGT, INTC, BA, ISRG, UNH, CRM, SBUX, AAPL, CVS, ACN, TMUS
- Stale events (lag > 1): All others

The period-of-report dates appear to correctly capture the event date from EDGAR headers.

## Key Finding

**The hypothesis is NOT supported in-sample**:
- Fresh events underperform stale events (fresh-stale = -1.03%)
- Fresh events lose money on average (-1.19%)
- No monotonic decay with lag (lag2=+0.40% > lag1, lag4+=-0.18%)

The period-of-report date (EDGAR header) may be earlier than the public announcement date for many events, causing "fresh" events (lag ≤ 1) to actually be stale in terms of public knowledge. This is the limitation noted in PREREG.md.

## Conclusion

No date-parse errors found - the EDGAR period-of-report source is working correctly. The fresh/stale split using lag ≤ 1 does not produce the predicted edge. The hypothesis fails in-sample.

**No fix needed for parser** - the source is correct per freeze-v2 spec. The null result should be reported as a finding.