# Covered-call credit-renewal before/after experiment

Conclusion: **inconclusive**.

Primary prediction: mean post-disclosure minus five-session pre-disclosure incremental covered-call net value over stock is negative at 21 sessions. This is a retrospective baseline, not an ordinary-day edge.

Source: Massive credit_facility disclosures, historical identity metadata, daily/minute stock bars, option bid/ask books and original cash dividends. Discovery March 2022–December 2023; historical validation 2024–2025. Excludes starter 100 issuers.

## Primary: discovery
40 pairs, 7 dependence groups. Mean difference **-0.1037 percentage points** of entry stock notional.
Corrected component-bootstrap interval: [-1.3519, +1.1052] pp. Finite-component t interval: [-3.1147, +2.9072] pp.
Assignment lower-bound mean: -5.6976 pp; upper-bound mean: +6.4324 pp. Upper-bound bootstrap: [+2.6834, +9.8605] pp; t: [-0.3311, +13.1960] pp.
event: entry bid credit 5.371% of stock; covered-call increment -2.978%; stock-price upside 5.784%, downside magnitude 3.209%, absolute price movement 8.993%; price +10% tail 20.0%, −10% tail 15.0%. Exit intrinsic/time value 2.191%/6.114%. Plausible early-assignment share 55.0%. Total-stock-return upside/downside/absolute movement including cash dividends: 5.804%/3.156%/8.959%.
baseline: entry bid credit 5.531% of stock; covered-call increment -2.874%; stock-price upside 6.100%, downside magnitude 3.756%, absolute price movement 9.856%; price +10% tail 22.5%, −10% tail 17.5%. Exit intrinsic/time value 1.858%/6.503%. Plausible early-assignment share 47.5%. Total-stock-return upside/downside/absolute movement including cash dividends: 6.177%/3.685%/9.862%.

## Primary: validation
40 pairs, 8 dependence groups. Mean difference **-0.5128 percentage points** of entry stock notional.
Corrected component-bootstrap interval: [-2.5950, +0.9767] pp. Finite-component t interval: [-3.5742, +2.5486] pp.
Assignment lower-bound mean: -3.5692 pp; upper-bound mean: +2.6137 pp. Upper-bound bootstrap: [-0.3005, +5.1314] pp; t: [-3.5839, +8.8114] pp.
event: entry bid credit 4.896% of stock; covered-call increment -1.318%; stock-price upside 3.635%, downside magnitude 3.898%, absolute price movement 7.533%; price +10% tail 15.0%, −10% tail 17.5%. Exit intrinsic/time value 0.955%/5.222%. Plausible early-assignment share 30.0%. Total-stock-return upside/downside/absolute movement including cash dividends: 3.702%/3.787%/7.489%.
baseline: entry bid credit 5.201% of stock; covered-call increment -0.805%; stock-price upside 3.428%, downside magnitude 4.646%, absolute price movement 8.074%; price +10% tail 15.0%, −10% tail 15.0%. Exit intrinsic/time value 1.210%/4.759%. Plausible early-assignment share 27.5%. Total-stock-return upside/downside/absolute movement including cash dividends: 3.537%/4.607%/8.143%.

## Every fixed horizon
Differences below are percentage points of entry stock notional. Nonprimary horizons remain exploratory.
- discovery, 1: n=40, G=18, difference=-0.3164 pp; bootstrap [-1.5079, +0.6235] pp; t [-1.4956, +0.8629] pp.
- discovery, 2: n=40, G=12, difference=+0.0628 pp; bootstrap [-0.8223, +0.8072] pp; t [-1.1821, +1.3077] pp.
- discovery, 3: n=39, G=12, difference=-0.0136 pp; bootstrap unavailable (count/dependence gate); t unavailable (count/dependence gate).
- discovery, 5: n=39, G=10, difference=-0.2189 pp; bootstrap unavailable (count/dependence gate); t unavailable (count/dependence gate).
- discovery, 10: n=39, G=10, difference=+0.0763 pp; bootstrap unavailable (count/dependence gate); t unavailable (count/dependence gate).
- discovery, 21: n=40, G=7, difference=-0.1037 pp; bootstrap [-1.3519, +1.1052] pp; t [-3.1147, +2.9072] pp.
- discovery, 42: n=33, G=2, difference=-1.2558 pp; bootstrap unavailable (count/dependence gate); t unavailable (count/dependence gate).
- discovery, 63: n=27, G=1, difference=-2.5709 pp; bootstrap unavailable (count/dependence gate); t unavailable (count/dependence gate).
- discovery, exp: n=40, G=1, difference=-0.4017 pp; bootstrap unavailable (count/dependence gate); t unavailable (count/dependence gate).
- validation, 1: n=39, G=21, difference=-0.4192 pp; bootstrap unavailable (count/dependence gate); t unavailable (count/dependence gate).
- validation, 2: n=37, G=16, difference=-0.6217 pp; bootstrap unavailable (count/dependence gate); t unavailable (count/dependence gate).
- validation, 3: n=39, G=14, difference=-0.7231 pp; bootstrap unavailable (count/dependence gate); t unavailable (count/dependence gate).
- validation, 5: n=39, G=12, difference=-1.2978 pp; bootstrap unavailable (count/dependence gate); t unavailable (count/dependence gate).
- validation, 10: n=37, G=10, difference=-0.5363 pp; bootstrap unavailable (count/dependence gate); t unavailable (count/dependence gate).
- validation, 21: n=40, G=8, difference=-0.5128 pp; bootstrap [-2.5950, +0.9767] pp; t [-3.5742, +2.5486] pp.
- validation, 42: n=29, G=2, difference=+0.6175 pp; bootstrap unavailable (count/dependence gate); t unavailable (count/dependence gate).
- validation, 63: n=23, G=2, difference=-2.4160 pp; bootstrap unavailable (count/dependence gate); t unavailable (count/dependence gate).
- validation, exp: n=40, G=1, difference=-0.5239 pp; bootstrap unavailable (count/dependence gate); t unavailable (count/dependence gate).

## Sensitivities
- discovery baseline3: n=38, G=7, difference=+0.6274 pp, gate=False.
- discovery baseline7: n=22, G=7, difference=+0.4993 pp, gate=False.
- discovery commission1: n=40, G=7, difference=-0.1035 pp, gate=True.
- discovery slippage10pct: n=40, G=7, difference=-0.1297 pp, gate=True.
- discovery slippage25pct: n=40, G=7, difference=-0.1686 pp, gate=True.
- discovery assignment5: n=40, G=7, difference=-0.1037 pp, gate=True.
- discovery assignment15: n=40, G=7, difference=-0.1037 pp, gate=True.
- discovery cash_interest: n=40, G=7, difference=-0.1037 pp, gate=True.
- discovery same_strike: n=24, G=8, difference=-0.7229 pp, gate=False.
- validation baseline3: n=34, G=8, difference=+0.0795 pp, gate=False.
- validation baseline7: n=32, G=8, difference=-0.1631 pp, gate=False.
- validation commission1: n=40, G=8, difference=-0.5134 pp, gate=True.
- validation slippage10pct: n=40, G=8, difference=-0.5754 pp, gate=True.
- validation slippage25pct: n=40, G=8, difference=-0.6693 pp, gate=True.
- validation assignment5: n=40, G=8, difference=-0.5128 pp, gate=True.
- validation assignment15: n=40, G=8, difference=-0.5128 pp, gate=True.
- validation cash_interest: n=40, G=8, difference=-0.5128 pp, gate=True.
- validation same_strike: n=23, G=10, difference=+0.4387 pp, gate=False.

## IV mechanism
- discovery: n=40, G=1, inversion failures=0; raw IV difference=-0.00034842975033098146, adjusted intercept=-0.024831856252154037; bootstrap unavailable (count/dependence gate), t unavailable (count/dependence gate).
- validation: n=40, G=2, inversion failures=0; raw IV difference=0.0013248062369166126, adjusted intercept=-0.019553006113402053; bootstrap unavailable (count/dependence gate), t unavailable (count/dependence gate).

## Execution-cost decomposition (descriptive audit)
These are quote diagnostics, not a newly selected tradable midpoint strategy.
- discovery: event entry spread median 30.5% of option midpoint; baseline 28.6%. Extra event round-trip bid/ask drag versus midpoint is +0.1296 pp of stock notional. Arithmetic midpoint diagnostic contrast (commissions retained) is +0.0259 pp; midpoint fills are not assumed. Event/baseline one-contract mean funded notionals $6968/$7022. Raw displayed sizes are recorded without conversion into scalable capacity.
- validation: event entry spread median 24.2% of option midpoint; baseline 22.7%. Extra event round-trip bid/ask drag versus midpoint is +0.3131 pp of stock notional. Arithmetic midpoint diagnostic contrast (commissions retained) is -0.1997 pp; midpoint fills are not assumed. Event/baseline one-contract mean funded notionals $8735/$8685. Raw displayed sizes are recorded without conversion into scalable capacity.
The spread-cost difference is larger than the discovery negative contrast and accounts for a substantial part of the validation contrast. Thus negative bid/ask P&L does not establish a financing-driven IV decline. No spread filter was introduced after observing outcomes. Quote fields and timestamps: [Massive options quotes documentation](https://massive.com/docs/rest/options/quotes). Original cash-dividend definitions: [Massive dividends documentation](https://massive.com/docs/rest/stocks/corporate-actions/dividends).

## Post-result event audit
Reviewed the five lowest and five highest primary differences in each window (20 complete available disclosure contexts). All describe completed revolving-credit continuations under the frozen arm. WRLD/REVG reduce commitments and change covenant thresholds; RIVN doubles commitments. These are not proof of routine investor expectations or unchanged financing risk. No rows were excluded or rerun after this audit.

## Influence
Discovery mean changes sign when some individual issuers or dependence groups are omitted. Validation remains negative under individual omissions, without establishing significance. Exact ranges are retained in the influence JSON files. Three/seven-session and same-strike sensitivities use smaller, different cohorts; sign changes cannot be attributed solely to the changed parameter.

## Limits and action
The before and after holds share 16 sessions and differ in maturity, moneyness and stock paths. Lower premium is not independently cheaper insurance or a financing-news effect. American IV uses trailing cash-dividend yield, a continuous approximation; historical yield curves and actual broker assignments are unobserved. Possible assignment bounds assume economically plausible exercise after stock reaches strike, not irrational OTM exercise. Baseline dates cannot be traded from a future unknown filing date.

Entry is the first qualifying sized two-sided market after 09:45 on the session after filing, with a known completed stock-minute reference and modeled 100 ms delay. Historical quotes do not prove fills. Capacity is one call/100 funded shares per issuer, not portfolio-scale liquidity. Bid/ask, commissions, spread slippage and assignment-fee sensitivities are retained. No exchange-specific fees, market impact or stock bid/ask execution data are available in this test.

Uncertainty links repeated issuers and overlapping holds; IV adds overlapping RV windows. The 120-family correction is intentionally preserved after earlier exploratory comparisons. Low group counts and wide intervals do not establish no effect. No judges' sealed window has been tested. Do not adopt this as a trading edge unless independent subsequent validation resolves these limitations.

Full exclusions and every horizon's count/dependence gate are in coverage_counts.json, original feasibility input_audit.json and the retained source text/calendar audits. Per-pair returns, assignment bounds, IV inversions and sensitivities are saved alongside this report. No favorable horizon replaces the 21-session primary result.
