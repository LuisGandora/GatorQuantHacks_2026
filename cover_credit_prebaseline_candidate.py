"""Count quote-covered pre/post pairs, without computing trade performance."""
import json
import pandas as pd
import count_credit_prebaseline_candidate as study
import count_credit_renewal_v2 as symbols


def run():
    g=symbols.g;g.OUT=study.OUT;engine=g.engine;symbols.OUT=study.OUT
    counts=pd.read_csv(study.OUT/'coverage_counts.csv')
    if len(counts)!=2 or not counts.calendar_gate.all():raise SystemExit('Calendar gates must pass')
    engine.OUT=study.OUT;engine.quote=g.quote;engine.QUOTE_SPOT=True
    engine.RV_MATCH=True;engine.VERIFY_CIK=True;engine.BLOCK_MONTHS=3
    engine.CANONICAL_SYMBOL=symbols.symbol;engine.REQUIRE_SAME_EXPIRY=True
    implementation=dict(bootstrap_seed=20261003,execution_delay_seconds=.1,
        stock_reference_max_age_seconds=60,issuer_identity='CIK equality at event and pre-baseline dates',
        returns_read_before_freeze=False,counts_spec_id=study.SPEC['id'])
    path=study.OUT/'implementation_parameters.json'
    if path.exists() and json.loads(path.read_text())!=implementation:raise RuntimeError('Implementation parameters changed')
    engine.t.save(path,implementation)
    engine.POLICY=dict(engine.POLICY,id='CR-prebaseline-coverage-v1',
        quote='Firstjoint sizedbid/ask and fresh completedstockminute09:45-10:15;100msmodeled latency, not guaranteed fills',
        controls='Fixed5sessionpre-disclosure baseline,sameselectedexpiry,DTE±7,RV20ratio.8..1.25,originalstarterstrikealgorithm',
        stock='Known stock reference; pre-entryRV20 fromadjustedcloses; splitfactorchangeexcluded',
        identity='Historicalcommonstock resolved before quotes byCIK; controlsverifysameCIK; repeat/overlap groupsuseCIK',
        risk='Pre-entry date is a retrospectively selected baseline, not investable using a future unknown filing date; no generic ordinary-day claim. Quote availability conditions the cohort.')
    engine.run()


if __name__=='__main__':run()
