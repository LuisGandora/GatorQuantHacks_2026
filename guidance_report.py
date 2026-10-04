"""Publish the completed, stopped guidance source audit without opening outcomes.

This run has a failed source gate. Its semantic and economic specifications are
recorded, but no inference about guidance uncertainty or an options edge exists.
"""
import argparse
from collections import Counter
import hashlib
import json

from departure_experiment import freeze, save
from guidance_sources import OUTPUT, verify_sources, checksum
from guidance_spec import PROTOCOL, STRATEGIES, START, END
from jev_experiment import ROOT, digest


def require_source_pass(gate):
    """Reject before credentials, model calls, or financial outcomes are opened."""
    if not gate['passed']:
        raise RuntimeError('Frozen guidance source gate failed; semantic and economic stages are blocked.')


def audit_citations(sources):
    counts=Counter()
    for source in sources:
        parsed=json.loads((OUTPUT/'parsed'/f'{source["accession_number"]}.json').read_text())
        for candidate in source['candidates']:
            docs=[d for d in parsed['documents'] if d['filename']==candidate['filename']
                  and d['type']==candidate['document_type']
                  and hashlib.sha256(d['text'].encode()).hexdigest()==candidate['document_sha256']]
            if len(docs)!=1:
                raise ValueError('Candidate provenance is not a unique original document.')
            text=docs[0]['text']
            if (text[candidate['start']:candidate['end']]!=candidate['quote'] or
                text[candidate['context_start']:candidate['context_end']]!=candidate['context']):
                raise ValueError('Candidate offsets no longer match source evidence.')
            if not START<=candidate['filing_timestamp'][:10]<=END:
                raise ValueError('Candidate escaped the historical source window.')
            counts['candidate_quotes']+=1
            counts['candidate_contexts']+=1
        counts['parsed_packages']+=1
    return dict(counts)


def stopped_metrics():
    verify_sources()
    gate=json.loads((OUTPUT/'source_gate.json').read_text())
    if gate['passed']:
        raise RuntimeError('Stopped-source reporting requires a failed source gate.')
    forbidden=['raw_jev','semantic_features.json','joined_outcomes.json',
               'economic_results.json','market','oos_results.json','judges_results.json']
    if any((OUTPUT/name).exists() for name in forbidden):
        raise ValueError('Later-stage artifact exists despite this stopped source audit.')
    sources=json.loads((OUTPUT/'candidate_sources.json').read_text())
    enrollment=json.loads((OUTPUT/'enrollment_counts.json').read_text())
    http=[json.loads(p.read_text()) for p in sorted((OUTPUT/'http').glob('*.json'))]
    from guidance_sources import validate_scope
    for record in http:
        req=record['request'];validate_scope(req['path'],req['params'],req['scope'])
        if record['sha256']!=digest(record['response']):raise ValueError('HTTP response integrity failure.')
    # Freeze all acquisition records as the completed audit's provenance, in
    # addition to the source manifest locked at preparation. Never rewrite it.
    paths=[OUTPUT/'protocol.json',OUTPUT/'universe.json',OUTPUT/'taxonomy.json',
           OUTPUT/'source_manifest.json',OUTPUT/'source_failures.json']
    paths+=list((OUTPUT/'http').glob('*.json'))+list(OUTPUT.glob('disclosures_*.json'))
    freeze(OUTPUT/'audit_manifest.json',{str(p.relative_to(ROOT)):checksum(p) for p in sorted(paths)})
    return {'experiment':PROTOCOL['experiment'],'protocol_sha256':digest(PROTOCOL),
        'window':[START,END],'universe_members':len(json.loads((OUTPUT/'universe.json').read_text())),
        'enrollment':enrollment,'source_gate':gate,'citations':audit_citations(sources),
        'filings_by_year':dict(sorted(Counter(s['filing_date'][:4] for s in sources).items())),
        'source_http_cache_records':len(http),
        'prior_research_files_preserved':len(json.loads((OUTPUT/'preservation.json').read_text())),
        'semantic':{'status':'not_run_source_gate_failed','requests':0,'features':None,
                    'JEV_vs_baseline':None,'latency':None,'model_usage_cost_usd':0},
        'economic':{'status':'not_run_source_gate_failed','association':None,
                    'uncertainty_intervals':None,'sensitivity':None,
                    'strategies':{name:{'status':'not_run_source_gate_failed','historical_edge':None,
                                       'after_cost_edge':None,'interval':None} for name in STRATEGIES}},
        'decision':{'status':'source_infeasible','hypothesis_tested':False,'strategy_selected':None,
                    'oos_opened':False,'judges_opened':False,
                    'reason':f'{gate["potential_pairs"]} potential numerical-range filings / {gate["companies"]} companies are below the frozen {PROTOCOL["source_gate"]["min_potential_pairs"]} / {PROTOCOL["source_gate"]["min_companies"]} feasibility floors. Even all {enrollment["filings"]} enrolled filings cannot reach {PROTOCOL["source_gate"]["min_potential_pairs"]}. This is not a null economic result.'},
        'limitations':['Massive guidance-tag coverage is not all corporate guidance disclosures.',
                       'Range candidates are unvalidated forecasts; comparability and semantic eligibility are unknown.',
                       'Sources before2024 are outside the boundary, reducing prior-guidance availability.',
                       'A static current universe can introduce survivorship bias.',
                       'Source/API subscription costs were not measured; zero model calls imply zero incremental JEV usage.']}


def report():
    result=stopped_metrics()
    freeze(OUTPUT/'metrics.json',result)
    save(ROOT/'GUIDANCE_METRICS.json',result)
    e=result['enrollment'];gate=result['source_gate'];c=result['citations']
    rows=['# Guidance uncertainty: completed source audit', '',
        '**Decision: `source_infeasible`. The economic hypothesis was not tested.**', '',
        'This exploratory follow-up asked whether explicit changes in forecast visibility predict subsequent risk when the numerical guidance midpoint changes little. Numerical range changes and a fixed keyword score were specified as baselines. Neither semantic superiority nor an options edge was assumed.', '',
        '## Frozen design and chronology', '',
        'The 2024–2025 window, original starter universe, metric hierarchy, source and semantic floors, primary five-session horizon, costs, sensitivity and five allowed strategies were frozen before acquiring the guidance cohort. Protocol commit: `d8689c6`; protocol SHA256: `'+result['protocol_sha256']+'`. Acquisition and audit completed October 3, 2026.', '',
        'Enrollment uses both Massive guidance taxonomy tags. Deduplication is by original accession. Sources are the original SEC submission package, its sequence-one 8-K and financial/outlook EX-99 exhibits. The primary metric is a company-wide full-year bounded adjusted diluted EPS forecast, otherwise a bounded revenue-level forecast. Comparable fiscal year, scope, accounting basis and currency are mandatory. The planned midpoint tolerance is 2%; withdrawals are descriptive. Earlier outcome summaries from other categories make this an exploratory design.', '',
        '## Observed coverage', '',
        '| Stage | Observed | Frozen requirement |', '|---|---:|---:|',
        f'| Massive tagged disclosure rows, all issuers | {e["taxonomy_rows"]:,} | Complete pagination |',
        f'| Unique filings in the unchanged universe | {e["filings"]} | — |',
        f'| Enrolled companies | {e["companies"]} | — |',
        f'| Recovered and validated original packages | {c["parsed_packages"]}/{e["filings"]} | Failure fraction ≤5% |',
        f'| Potential numerical-range filings | {gate["potential_pairs"]} | ≥80 |',
        f'| Companies with potential numerical ranges | {gate["companies"]} | ≥20 |', '',
        f'{e["outside_universe_rows"]:,} disclosure rows fell outside the fixed universe. In-universe enrollment contains 32 filings from 2024 and 28 from 2025; all 60 are issuance/update filings and none are withdrawals. There were no same-issuer, same-date collisions. Seventeen filings had no bounded-range candidate from the deterministic extractor.', '',
        f'The audit checked {c["candidate_quotes"]} exact candidate quotes and {c["candidate_contexts"]} surrounding contexts against document hashes and normalized offsets. These are over-found numerical ranges, not 416 comparable guidance forecasts. The 43 potential filings are only an upper bound on this extractor’s primary eligible cohort; selecting a current range, identifying a comparable prior forecast and enforcing the midpoint rule can reduce it further.', '',
        'The 80-event and 20-company floors were feasibility safeguards, not a power calculation. The cohort cannot satisfy the event floor even if every enrolled filing eventually qualifies. No floor, category, metric, universe or year boundary was changed after seeing these counts.', '',
        '## Evidence that remains unavailable', '',
        'The source gate stopped the run before JEV or financial-market calls. No semantic groups were measured, no JEV-versus-baseline comparison was performed, and no realized-risk association, strategy edge, uncertainty interval or cost-adjusted sensitivity result exists.', '',
        '| Predefined structure | Historical comparison |', '|---|---|']
    rows += [f'| {name.replace("_"," ")} | Not run: source gate failed |' for name in STRATEGIES]
    rows += ['', 'There were zero JEV requests and therefore zero incremental JEV usage cost. Massive subscription and SEC acquisition costs were not measured. Planned trading-cost assumptions are specification only, not empirical transaction-cost estimates. No final strategy was selected; 2026 OOS and judges’ sealed replication were not opened.', '',
        '## Meaning and limitations', '',
        'This result identifies insufficient observable source coverage under the frozen design. It does not establish that guidance uncertainty lacks predictive value. Tagged disclosures are not the full population of guidance releases. The excluded 2023 history can prevent prior-forecast pairing, and the static universe has survivorship limitations. The filing-date entry rule also cannot capture information incorporated at an earlier earnings release.', '',
        '## Reproduction and implementation boundary', '',
        'The executable implementation covers guarded taxonomy/disclosure acquisition, complete pagination, deduplication, original-package retrieval and validation, deterministic numerical candidates, source gates, citation verification and stopped-result reporting. The later semantic and economic design is frozen in the protocol; those stages were not implemented or executed after the source gate failed. There is no OOS or sealed-window command.', '',
        'From the project environment:', '', '```bash',
        '.venv/bin/python guidance_sources.py freeze',
        '# For a fresh run, commit the frozen protocol before acquisition.',
        '.venv/bin/python guidance_sources.py acquire',
        '.venv/bin/python guidance_sources.py retrieve',
        '.venv/bin/python guidance_sources.py prepare',
        '.venv/bin/python guidance_report.py',
        '.venv/bin/python -m unittest discover -v', '```', '',
        'The completed local run reuses immutable cached records and performs no new HTTP requests. Missing credentials or network access on an uncached run fail explicitly. Do not delete records to rescore, lower thresholds, or enable the notebook’s OOS cells to bypass the gate.', '',
        f'Original packages, paginated responses, source candidates and manifests live in ignored `guidance_results/`. The completed audit checks {result["prior_research_files_preserved"]:,} prior research files against their frozen hashes. The local artifacts are needed to reproduce the provenance checks; `GUIDANCE_METRICS.json` preserves the public aggregate counts. Frozen manifests reject edits instead of migrating or replacing cached state.', '']
    (ROOT/'GUIDANCE_RESULTS.md').write_text('\n'.join(rows))
    print(json.dumps(result['decision'],indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    report()
