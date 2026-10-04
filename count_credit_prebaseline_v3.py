"""User-approved before/after baseline, corrected before any effect testing."""
import count_credit_prebaseline_v2 as previous
from review_revolving_renewal import review

base = previous.base
OUT = base.ROOT/'credit_prebaseline_v3_candidate'
SPEC = dict(previous.SPEC,
    id='CR-prebaseline-covered-call-v3',
    benchmark_authorization='User explicitly allowed a labeled before/after baseline after broader universe/windows approval.',
    corrections=previous.SPEC['corrections']+' Full-context audit also identified term-loan-only extensions with revolver repayment. Reject this general text case; retain revolving renewals whose agreement evidence is split across related excerpts.',
    current_stage='Frozen corrected text/calendar design; count and execution coverage before effects.')


if __name__ == '__main__':
    base.OUT=OUT; base.SPEC=SPEC; base.EXTRA_REVIEW=review; base.run()
