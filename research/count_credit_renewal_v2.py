"""Refined, outcome-free renewal classification and historical common-symbol mapping."""
import re
import json
import count_credit_renewal_candidate as prior

g=prior.g
OUT=g.engine.t.ROOT/'credit_renewal_v2_candidate'
SPEC=dict(prior.SPEC,
    id='CR-renewal-covered-call-v2',
    arm='Explicit actual refinancing/replacement of existing credit, maturity extension, renewal of credit, or entry into an amended-and-restated credit agreement; historical agreement titles alone do not qualify. Full available context excludes acquisitions, spin-offs/separation, new expansion projects, distress or covenant waivers.',
    selection='OneeventperCIKperwindow byfixedCIK/accession/day hash, independent of listed symbol; resolve CS first, ADRC second, then lexical symbol order at entry before any quotes. No replacement event or symbol following missing option quotes.',
    rationale=prior.SPEC['rationale']+' Capacity increases may occur in renewals; record them and do not assert financing amounts are unchanged.',
    corrections='Beforequotes: MEC historical agreement title was not evidence of a renewal; ENOV separation and USDP acquisition were mixed transactions. BCPB/RILYL are alternate securities of corporate issuers, so resolve historical common shares before pricing rather than silently substituting after a quote failure.',
    current_stage='Refined text, calendar and common-equity metadata counts; no quotes or P&L inspected for renewal population')


def classify(text):
    s=str(text or '').lower()
    entered=re.search(r'entered.{0,20}into\s+(?:(?:a|an|the)\s+)?(?:(?:first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|\d+)\s+)?amended\s+(?:and|&)\s+restated\s+(?:revolving\s+)?(?:credit|loan)',s)
    renewal=entered or re.search(r'refinanc.{0,120}(?:existing|prior|previous|original).{0,60}(?:credit|facility|agreement|obligation)|replac.{0,80}(?:existing|prior|previous|original).{0,60}(?:credit|facility|agreement)|extend.{0,60}maturity|renew.{0,60}(?:credit|facility)',s)
    credit=re.search(r'revolv|credit (?:agreement|facility)',s)
    excluded=re.search(r'acqui|spin.?off|separation|merger|expansion|new project|bankrupt|covenant.{0,80}(?:breach|violat|waiv)|(?:breach|violat|waiv).{0,80}covenant|event of default|going concern|forbearance|distress',s)
    return 'routine_compatible' if renewal and credit and not excluded else 'unknown_review'


def symbol(issuer,day):
    cik=g.engine.normalize_cik(issuer)
    if cik is None:return None
    path=OUT/'historical_symbols'/f'{cik}_{day.date()}.json'
    if path.exists():return json.loads(path.read_text())['selected']
    rows=g.engine.t.c.p.api_get_all('/v3/reference/tickers',{'cik':cik,'date':str(day.date()),'market':'stocks','active':'true','limit':1000})
    good=[r for r in rows if g.engine.normalize_cik(r.get('cik'))==cik and r.get('type') in ['CS','ADRC']]
    good.sort(key=lambda r:(r['type']!='CS',r['ticker']))
    chosen=good[0]['ticker'] if good else None
    g.engine.t.save(path,dict(cik=cik,date=str(day.date()),selected=chosen,eligible=[dict(ticker=r['ticker'],type=r['type']) for r in good],quotes_read=False))
    return chosen


def run():
    c=g.counter;c.OUT=OUT;c.SPEC=SPEC;c.TAG_SET={'credit_facility'};c.BLOCK_MONTHS=3
    c.EXCLUDE_PREVIOUS_ISSUERS=True;c.ISSUER_CALENDAR=True;c.FULL_FILING_CONTEXT=True
    c.ISSUER_ONLY_HASH=True;c.CANONICAL_SYMBOL=symbol;c.classify=classify;c.TEXT_REVIEW_PATTERN=r'bankrupt|forbearance|going concern'
    c.run()


if __name__=='__main__':run()
