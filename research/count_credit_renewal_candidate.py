"""A new credit-renewal mechanism: text/calendar counts before option outcomes."""
import argparse
import re
import governance_executable_coverage as g

OUT=g.engine.t.ROOT/'credit_renewal_candidate'
SPEC=dict(g.SPEC,
    id='CR-renewal-covered-call-v1',
    hypothesis='After completed renewals or refinancing of existing revolving credit facilities, starter5%OTM covered calls add more net value over stock than matched ordinary days, because continuation financing provides limited incremental upside relative to premiums collected.',
    arm='Explicit existing-credit renewal/refinancing/amend-and-restate or maturity extension in full available accession context; exclude distress, covenant breaches/waivers and acquisition/growth funding. Does not infer borrower quality from future returns.',
    rationale='A replacement liquidity backstop can remove financing uncertainty without financing a new operating expansion. This is an economic hypothesis, not an established effect; potentially lower call credits are a competing explanation.',
    tag='credit_facility',
    universe='HistoricalCS/ADRC outside starterTOP100issuers including alternate symbols, missingCIKexcluded; point-in-time identity required',
    controls='OriginalANYdisclosure±30days acrossissuer symbols; sameissuer/year/quarter/weekday within63sessions,DTE±7,RV20ratio.8..1.25; nearest3usable',
    blocks='Quarter-contained21-session event/control holds; oneeventperCIKperwindow chosen before quotes',
    pricing='Firstjointmarket09:45-10:15,bid sale/ask close,65ccommissionpercontractside; sameknownstock-reference rule as registered governance execution design',
    sampling_history='Proposed after outcome-free coverage failures; earlier TOP100 debt-related performance was inspected, so economically related hypothesis is post-discovery. Exclude those issuers; retain120-family correction. No expanded renewal P&L read.',
    current_stage='Text and calendar counts only; manual classification and executable coverage required')


def classify(text):
    text=str(text or '').lower()
    renewal=bool(re.search(r'refinanc|renew|extend.{0,80}(?:maturity|credit|facility)|amend.{0,15}restat|replac.{0,80}(?:existing|previous|prior).{0,40}(?:credit|facility|agreement)',text))
    credit=bool(re.search(r'revolv|credit (?:agreement|facility)',text))
    adverse=bool(re.search(r'bankrupt|covenant.{0,80}(?:breach|violat|waiv)|(?:breach|violat|waiv).{0,80}covenant|event of default|going concern|forbearance|distress',text))
    growth=bool(re.search(r'(?:fund|financ).{0,80}(?:acquisition|expansion|new project)|(?:acquisition|expansion).{0,80}(?:fund|financ)',text))
    return 'routine_compatible' if renewal and credit and not adverse and not growth else 'unknown_review'


def run(stage):
    g.OUT=OUT;g.SPEC=SPEC
    g.counter.OUT=OUT;g.counter.SPEC=SPEC;g.counter.TAG_SET={'credit_facility'}
    g.counter.BLOCK_MONTHS=3;g.counter.EXCLUDE_PREVIOUS_ISSUERS=True;g.counter.ISSUER_CALENDAR=True;g.counter.FULL_FILING_CONTEXT=True
    g.counter.classify=classify;g.counter.TEXT_REVIEW_PATTERN=r'bankrupt|forbearance|going concern'
    if stage=='counts':g.counter.run();return
    raise SystemExit('Counts and blinded text audit must pass before credit-renewal quote collection is implemented')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['counts']);run(p.parse_args().stage)
