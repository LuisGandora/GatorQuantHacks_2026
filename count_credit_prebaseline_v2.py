"""Full-context audit corrections before any return or IV effect is computed."""
import ast
import re
import pandas as pd
import count_credit_prebaseline_candidate as base

OUT=base.ROOT/'credit_prebaseline_v2_candidate'
SPEC=dict(base.SPEC,
    id='CR-prebaseline-covered-call-v2',
    hypothesis='Covered calls entered after completed non-acquisition revolving-credit renewals add less net value over stock at21sessions than comparable calls entered five sessions before disclosure, because financing-news resolution reduces premium income without a sufficient reduction in upside surrendered.',
    arm='Actual executed revolving-credit continuation in full available context; retain original acquisition/spinoff/default/covenant-waiver exclusions. Reject proposed/process/commitment-letter cases, mixed non-facility tags, nonrevolving-only loans, and explicitly dated extensions shorterthan180days. Routine/planned investor expectations are not asserted.',
    corrections='Outcome-free complete text census flagged CMTL asset-sale refinancing, LTH launched process, TEX commitment letter, WTI one-month bridge, and bundled securities/governance disclosures. Apply global rules, not profitable/unprofitable-row deletion. Capacity/term changes remain recorded rather than presumed unchanged.',
    assignment='No unadjusted supported claim from never-assigned marks. Before P&L freeze conservative possible-assignment bounds from daily stock high/strike and cash dividends through horizon; require support robust to the resulting bounds. Historical broker assignment is unobserved.',
    current_stage='Text/calendar corrections and executable coverage only; no P&L or IV differences read')
ALLOWED_TAGS={'credit_facility','credit_facility_draw','debt_retirement','deal_termination','guarantee_or_letter_of_credit'}


def review(row):
    text=str(row.context_text).lower()
    tags=set(ast.literal_eval(row.context_tags))
    if tags-ALLOWED_TAGS:return 'mixed_nonfacility_disclosure'
    if not re.search(r'\brevolv',text):return 'no_explicit_revolving_facility'
    if re.search(r'launched.{0,80}process|commitment letter|proposed|plans? to (?:refinanc|renew)|intend.{0,40}(?:enter|amend|refinanc)|will.{0,80}replac.{0,80}closing|covenant relief',text):return 'not_completed_or_distress_review'
    dates=re.findall(r'(?:maturity|extend)[^.]{0,150}?from\s+([a-z]+\s+\d{1,2},?\s+\d{4})\s+to\s+([a-z]+\s+\d{1,2},?\s+\d{4})',text)
    for old,new in dates:
        try:
            if (pd.Timestamp(new)-pd.Timestamp(old)).days<180:return 'short_bridge_extension'
        except ValueError:return 'ambiguous_maturity_dates'
    return ''


def run():
    base.OUT=OUT;base.SPEC=SPEC;base.EXTRA_REVIEW=review;base.run()


if __name__=='__main__':run()
