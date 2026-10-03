# Findings

## JEV Check (v89552f7a)
Controls scored high: 0% (max 5%). Labels: 69 (min 30). Balanced accuracy: 0.80 (min 0.80). **PASS**.

## Pairings

### P-leadership-low (cash_secured_put, low arm)
**Thesis**: Leadership-change headlines get priced as drama; planned, internal successions don't deliver it. Sell premium on low-JEV filings.  
**n**: 150 in-sample (170 declared, all low-JEV). High arm: 0 events.  
**In-sample edge**: -0.53% (NOT SUPPORTED).  
**Low−high edge**: N/A (no high-JEV events).  
**Out-of-sample**: Not run (in-sample failed).  
**Audit**: Top performers: PLTR CAO appt +8.4%, UNH CFO→advisor +7.7%, UBER GC transition +6.9%, INTC Products CEO resign +6.2%, NFLX Hastings transition +5.2%. Bottom: UNH Optum CEO appt -16.3%, ORCL Catz exit -15.1%, CRM Pres+CFO appt -12.1%, BA Calhoun resign -9.3%, SBUX CFO depart -9.2%. High variance; routine appointments mix planned promotions (positive) with abrupt exits labeled low-JEV (negative). JEV does not separate them. Thesis not supported.

### A1-ceo-change-low (cash_secured_put, low arm)
**Thesis**: "CEO change" gets priced as drama. Planned successions don't deliver it.  
**n**: 31 in-sample (33 declared, all low-JEV). High arm: 0 events.  
**In-sample edge**: -1.01% (FRAGILE).  
**Low−high edge**: N/A.  
**Out-of-sample**: Not run.  
**Audit**: Top: INTC Products CEO resign +6.2%, NFLX Hastings transition +5.2%, UNH Witty step down +3.9%, SCHW Bettinger intention +3.8%, USB Kedia appt +3.8%. Bottom: ORCL Catz exit -15.1%, BA Calhoun resign -9.3%, TMUS Sievert transition -4.8%, ISRG Guthart step down -5.9%, UNH Thompson passing -6.4%. Planned transitions include large negative moves (ORCL, BA, TMUS) that JEV scores 0. Thesis not supported.

### A1-ceo-change-low (covered_call, low arm)
**Thesis**: Same as above.  
**n**: 31 in-sample.  
**In-sample edge**: -1.78% (NOT SUPPORTED).  
**Low−high edge**: N/A.  
**Out-of-sample**: Not run.  
**Audit**: Top: INTC Products CEO resign +14.1%, NFLX Hastings +11.8%, SCHW Bettinger +10.7%, WMT McMillon retire +9.6%, DUK Sideris appt +9.1%. Bottom: ORCL Catz -19.0%, BA Calhoun -12.9%, TMUS Sievert -9.9%, UNH Thompson -11.2%, USB Cecere -7.0%. Same pattern; thesis not supported.

### A2-ceo-exit-abrupt (protective_put, high arm)
**Thesis**: Surprise exit has uncertain direction; market may under-price downside.  
**n**: 0 events in high arm (declared 0 after JEV split).  
**In-sample edge**: Not run.  
**Out-of-sample**: Not run.  
**Note**: No high-JEV CEO departures found in sample; pairing untestable.

### A3-cfo-exec-low (cash_secured_put, low arm)
**Thesis**: Mostly orderly promotions; post-filing implied move overstates follow-through.  
**n**: 116 in-sample (134 declared, all low-JEV). High arm: 0 events.  
**In-sample edge**: -0.58% (NOT SUPPORTED).  
**Low−high edge**: N/A.  
**Out-of-sample**: Not run.  
**Audit**: Top: PLTR CAO +8.4%, UNH CFO +7.7%, UBER GC +6.9%, NOW COO +5.1%, AMD CAO +4.6%. Bottom: UNH Optum CEO -16.3%, ORCL CFO promo -15.1%, CRM Pres+CFO -12.1%, INTC PSG CEO -5.7%, AMD CAO -6.6%. High variance; routine appointments include large negative moves (Optum CEO, ORCL CFO, CRM Pres+CFO) that JEV scores 0. Thesis not supported.

### A3-cfo-exec-low (covered_call, low arm)
**Thesis**: Same as above.  
**n**: 115 in-sample.  
**In-sample edge**: -1.10% (NOT SUPPORTED).  
**Low−high edge**: N/A.  
**Out-of-sample**: Not run.  
**Audit**: Top: UNH CFO +17.4%, PLTR CAO +12.9%, UBER GC +12.4%, GS Treasurer +10.5%, C interim CAO +10.1%. Bottom: UNH Optum CEO -22.3%, ORCL CFO promo -19.0%, CRM Pres+CFO -16.9%, TMUS CEO transition -11.3%, C CAO -12.9%. Same pattern; thesis not supported.

### A4-restructuring-high (collar, high arm)
**Thesis**: Material exit is an event you hold through; put may be cheap relative to downside.  
**n**: 2 events in high arm (declared 2 after JEV split). Below min_events (40).  
**In-sample edge**: Not run (Tier C).  
**Out-of-sample**: Not run.  
**Note**: Too few high-JEV restructuring events to test.

### B1-cyber-low (cash_secured_put, low arm)
**Thesis**: Minor incidents get over-priced.  
**n**: 0 events in low arm. Tier C. Not tested.

### B2-cyber-high (protective_put, high arm)
**Thesis**: Real breaches get under-priced downside.  
**n**: 4 events in high arm. Tier C. Not tested.

### B3-director-exit-high (protective_put, high arm)
**Thesis**: Abrupt or disputed resignations matter; most are retirements.  
**n**: 5 events in high arm. Tier C. Not tested.

### B4-strategic-high (long_call, high arm)
**Thesis**: Direction ambiguous; JEV does not score direction.  
**n**: 1 event in high arm. Tier C. Not tested.

### B4-strategic-high (collar, high arm)
**Thesis**: Same as above.  
**n**: 1 event in high arm. Tier C. Not tested.

### B5-good-news-call (long_call, all arm)
**Thesis**: "Guidance up, buy a call." JEV adds nothing unless it scores direction.  
**n**: 103 in-sample (119 declared, all low-JEV). High arm: 0 events.  
**In-sample edge**: -0.15% (NOT SUPPORTED).  
**Low−high edge**: N/A.  
**Out-of-sample**: Not run.  
**Audit**: Top: INTC Altera deconsolidation +54.7%, CAT guidance +29.2%, TMUS guidance raise +15.5%, AMD acquisition +12.9%, GM guidance +10.7%. Bottom: AVGO VMware acquisition -13.9%, AMD Sanmina acquisition -13.9%, INTU guidance -10.5%, UBER guidance -8.8%, CRM repurchase -6.6%. High variance; guidance raises mix with acquisitions that sell off. JEV doesn't score direction (all 0.0). Thesis not supported.

### B6-earnings (cash_secured_put, all arm)
**Thesis**: Earnings premium overpriced; boilerplate text (JEV adds nothing); post-filing entry misses vol crush.  
**n**: 117 in-sample (131 declared, all low-JEV). High arm: 0 events.  
**In-sample edge**: +0.39% (IN-SAMPLE ONLY).  
**Low−high edge**: N/A.  
**Out-of-sample**: n=39, edge=-0.46% (FAILED OUT-OF-SAMPLE).  
**Audit (in-sample)**: Top: LLY +11.3%, AMD +7.4%, FDX +6.1%, BKNG +5.5%, BLK +5.5%. Bottom: LLY Oct -3.1%, LLY Feb -3.4%, MRK -3.9%, MS -5.0%, FDX Dec -6.5%. Positive edge driven by few large outliers (LLY, AMD, MRK); many negative. JEV adds nothing (all 0.0). In-sample edge did not replicate out-of-sample.

### B6-earnings (covered_call, all arm)
**Thesis**: Same as above.  
**n**: 118 in-sample.  
**In-sample edge**: +0.83% (IN-SAMPLE ONLY).  
**Low−high edge**: N/A.  
**Out-of-sample**: n=39, edge=-1.59% (FAILED OUT-OF-SAMPLE).  
**Audit (in-sample)**: Top: LLY Aug +20.0%, BKNG +12.4%, MRK +11.7%, LLY Oct +11.2%, VZ +9.9%. Bottom: LLY May -10.1%, MS -9.0%, FDX Dec -8.8%, LLY Feb -6.2%, PEP -7.1%. Same pattern; in-sample edge did not replicate out-of-sample.

## Summary
- Total in-sample comparisons run: 16 (across 1 JEV version).
- No pairing produced a supported in-sample edge that replicated out-of-sample.
- JEV successfully separates abrupt/adverse events (cybersecurity, abrupt resignations) from routine/planned ones, but the resulting high-JEV arms are too sparse (0–5 events) to test.
- All low-JEV arms contain high-variance mixtures of truly routine events and adverse events that JEV scores low (e.g., ORCL Catz exit, BA Calhoun resign, UNH Optum CEO appt).
- The only pairing with positive in-sample edge (B6-earnings) failed out-of-sample.
- Well-supported null: selling premium on low-JEV leadership/earnings/good-news events does not generate consistent edge; buying calls on "good news" categories does not work; high-JEV arms are too sparse for statistical testing.