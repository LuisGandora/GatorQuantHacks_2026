"""Apply entry-evidence audit and present feasibility findings, never fabricated P&L."""
import hashlib,json,re,gzip,shutil
from pathlib import Path
import pandas as pd
import four_hypothesis_screen as s

root=Path('four_hypothesis_results');out=root/'reconciled'
board=pd.read_csv(out/'feasibility_results.csv');corrections=[];details=[]
for key in s.SPECS:
 q=pd.read_csv(out/f'{key}_event_audit.csv').fillna('')
 # Enforce the already declared seven-day board-action rule for month-only dates.
 # This is an evidence audit before any returns, not a new outcome filter.
 if key=='H1_buyback_put':
  for i,r in q[q.reason.eq('eligible')].iterrows():
   m=re.search(r'In ([A-Z][a-z]+ 20\d{2}),? .{0,120}(?:authorized|approved)',r.target_text,re.S)
   if m:
    latest=pd.Timestamp(m.group(1))+pd.offsets.MonthEnd(0)
    if (pd.Timestamp(r.filing_date)-latest).days>7:
     q.loc[i,'reason']='month_dated_board_action_more_than_seven_days_old'
     corrections.append(dict(id=key,ticker=r.ticker,accession_number=r.accession_number,reason=q.loc[i,'reason'],latest_possible_board_date=str(latest.date()),evidence=r.target_text))
 q.to_csv(out/f'{key}_audited_event_inventory.csv',index=False)
 q.groupby('reason').size().rename('company_filings').to_csv(out/f'{key}_audited_exclusion_counts.csv')
 i=board.index[board.id.eq(key)][0]
 board.loc[i,'verified_eligible']=q.reason.eq('eligible').sum()
 board.loc[i,'eligible_companies']=q[q.reason.eq('eligible')].ticker.nunique()
 details.append(dict(id=key,distinct=len(q),eligible=int(q.reason.eq('eligible').sum()),companies=int(q[q.reason.eq('eligible')].ticker.nunique())))
 assert len(q)==int(board.loc[i,'distinct_company_filings'])
 assert int(board.loc[i,'verified_eligible'])<40
pd.DataFrame(corrections).to_csv(root/'entry_evidence_corrections.csv',index=False)
board.to_csv(root/'FINAL_FEASIBILITY.csv',index=False)
core=pd.read_csv(root/'core_text_evidence_audit.csv').fillna('')
assert set(core.id)=={'H2_guidance_put','H4_refinancing_put'}
assert not core.enriched_reason.str.contains('^eligible$|candidate').any(),'Potential extra candidates need manual review before finalizing'
status={'status':'completed_feasibility','verdicts':{k:'inconclusive' for k in s.SPECS},'P_and_L_tests_run':0,'validation_outcome_looks':0,'gate':40,'final_eligible':{r['id']:r['eligible'] for r in details},'not_a_return_test':True,'reason':'all four below AGENTS Tier C pricing gate; unknown evidence is not absence of economic effect'}
(root/'FINAL_STATUS.json').write_text(json.dumps(status,indent=2))
text='''# Four hypothesis feasibility audits

**All four are inconclusive and fail the required candidate gate. No option-return tests or validation outcome looks were run.** This is an entry-evidence and sample-feasibility result, not evidence that any strategy lacks an effect.

The repository's AGENTS.md says “Don't test Tier C pairings.” pairings.json sets min_events=40. No threshold, universe, dates, strategy or hypothesis definition was broadened to obtain a trade result.

The proposed directions are positive event-minus-ordinary differences at 21 sessions: cash-secured puts after new material buybacks; protective-put incremental benefit after raised earnings/reduced cash-flow forecasts; covered-call incremental value after quantified new restructuring; cash-secured puts after refinancing without added borrowing.

## Results

- **Buybacks → cash-secured puts:** 36 distinct company filings; 17 verified materiality/freshness candidates across 13 companies. Materiality is at least 1% of historical issuer market capitalization or weighted shares, using issuer data dated before filing. Four ASR-containing filings are separately classified rather than pooled into discretionary authorizations. This secondary arm also cannot reach 40. One prior-month NFLX board action was removed in the evidence audit; the earlier automated inventory is retained.
- **Earnings/cash-flow divergence → protective puts:** 60 distinct company filings. None verifies both raised earnings guidance and lowered cash-flow guidance for the same period in the available excerpts/parsed Items. Fuller Items text still leaves the directional comparison unknown. A generic update, actual earnings growth, or cash-flow guidance increase is not the specified event.
- **Quantified new restructuring → covered calls:** 29 tag rows combine into 20 distinct company filings. Two meet the savings/costs/timetable/new-plan requirements: PFE 2024-05-22 and MRK 2025-07-29. They involve two companies and cannot support statistical inference. Ongoing extensions, retrospective charges and unquantified savings are separately excluded.
- **Refinancing without added borrowing → cash-secured puts:** 430 API tag rows combine into 293 distinct company filings. None independently verifies completed replacement plus unchanged/reduced borrowing or a valid paired-principal comparison. Repayment for optional general corporate purposes, redeemability of the newly issued notes and standard indenture provisions do not establish refinancing of existing debt. The parsed Items endpoint supplied text for 272/293 filings; 21 had no matching parsed Items. Missing exhibits and balance-sheet evidence prevent a complete economic classification.

## Data and audit

Exact taxonomy tags were verified. The API contains one C debt-issuance filing missing from the teammate CSV; it was added before the final screen. Multiple excerpts and debt/underwriting tags are combined by company/accession, not counted as independent events. JEV scores and labels are ignored. Input hashes, API coverage reconciliation, historical denominators, row-level reasons and fuller-text audits are saved.

The short-excerpt source and API-reconciled source screens are retained separately. No P&L was read when making the month-date freshness correction. The parsed 8-K endpoint returns core Items, not complete earnings exhibits; missing numeric guidance comparisons remain unknown. These results do not prove that no qualifying real-world events exist.

## Rubric assessment and next step

The economic mechanisms remain hypotheses. They cannot currently support a conclusive submission because event evidence and statistical coverage fail before trading-data exclusions. Option liquidity and matching would reduce the candidate counts further. No P&L, costs, confidence intervals, parameter sensitivity, capacity or sealed replication claims can be made from this audit.

Before another return test, obtain full contemporaneous earnings releases/prospectuses for the unverified subgroups and conduct an outcome-blind evidence audit. That may resolve guidance/refinancing classification. Buybacks and restructuring have fewer than 40 distinct source events even before filtering; full documents cannot overcome that upper bound within the same universe/windows. A broader universe/window or explicit exploratory small-sample analysis would require a separately registered scope; none was silently substituted here.

The frozen conditional test plan retains the starter universe/windows/construction, 3–6-month bucket, starter strikes, primary 21-session horizon, all fixed horizons, after-public entry, comparable same-company ordinary dates, premium costs/commission sensitivity, dependence-aware uncertainty and four-test multiplicity adjustment. No financial test is represented as executed.

Run `python four_hypothesis_api.py`, `python four_hypothesis_core_text.py`, and `python finalize_four_hypotheses.py`. The companion notebook executes these audits and displays the results. The original starter, human-owned harness and team ledger are unchanged.

Method references: [Massive point-in-time company details](https://www.massive.com/blog/announcing-our-new-point-in-time-company-details-api) and [8-K parsed Items endpoint](https://massive.com/docs/rest/stocks/filings/8-k-text).
'''
(root/'RESULTS.md').write_text(text,encoding='utf-8')
with (root/'core_text_evidence_audit.csv').open('rb') as src,gzip.open(root/'core_text_evidence_audit.csv.gz','wb') as dst:shutil.copyfileobj(src,dst)
print(board[['id','distinct_company_filings','verified_eligible','eligible_companies','pricing_gate','conclusion']].to_string(index=False))
