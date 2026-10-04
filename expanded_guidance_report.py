"""Verify and publish the completed experiment 4B semantic feasibility audit.

Reporting requires a failed semantic gate. It cannot open market outcomes.
"""
from collections import Counter
from functools import lru_cache
import hashlib
import json

import numpy as np

from departure_experiment import freeze, save
from expanded_guidance_sources import OUTPUT, verify_sources, checksum, validate_scope
from expanded_guidance_spec import PROTOCOL, STRATEGIES
import expanded_guidance_semantics as semantic
from jev_experiment import ROOT, digest, validate_response


def block_failed_gate(gate):
    if not gate['passed']:
        raise RuntimeError('Frozen semantic gate failed; economic analysis is blocked.')


@lru_cache(maxsize=None)
def parsed(accession):
    return json.loads((OUTPUT/'parsed'/f'{accession}.json').read_text())


def citation(candidate):
    matches=[d for d in parsed(candidate['accession_number'])['documents']
        if d['filename']==candidate['filename'] and d['type']==candidate['document_type']
        and hashlib.sha256(d['text'].encode()).hexdigest()==candidate['document_sha256']]
    if len(matches)!=1:raise ValueError('Citation does not identify a unique original document.')
    text=matches[0]['text']
    if text[candidate['start']:candidate['end']]!=candidate['quote']:
        raise ValueError('Exact citation offsets changed.')
    if 'context' in candidate and text[candidate['context_start']:candidate['context_end']]!=candidate['context']:
        raise ValueError('Exact candidate context changed.')


def verify_measurement(rows,packets):
    spec=json.loads((OUTPUT/'measurement_specification.json').read_text())
    if spec!=semantic.specification():raise ValueError('Frozen measurement specification changed.')
    if len(rows)!=len(packets):raise ValueError('Incomplete measurement cohort.')
    used=set();records=[]
    for row,packet in zip(rows,packets):
        if row['accession_number']!=packet['accession_number']:raise ValueError('Measurement enrollment mismatch.')
        payloads=[semantic.first(packet)[0]]
        if len(row['request_hashes'])>1:payloads.append(semantic.second(packet,row['current'])[0])
        if len(row['request_hashes'])>2:payloads.append(semantic.third(row['current'],row['prior'])[0])
        responses=[]
        for identifier,payload in zip(row['request_hashes'],payloads):
            wanted=digest({'specification':digest(spec),'request':payload})
            if identifier!=wanted:raise ValueError('JEV request is not the frozen source input.')
            record=json.loads((OUTPUT/'raw_jev'/f'{identifier}.json').read_text())
            if record['request']!=payload or record['record_hash']!=digest({k:v for k,v in record.items() if k!='record_hash'}):
                raise ValueError('Immutable JEV record changed.')
            responses.append(record['response']);records.append(record);used.add(identifier)
        for name in ['current','prior','evidence']:
            if row.get(name):citation(row[name])
        if len(responses)==3 and not row['malformed']:
            a,b,c=responses
            for response,payload in zip(responses,payloads):validate_response(response,payload['questions'])
            expected={'eligible':False}
            reason=semantic.features(expected,row['current'],row['prior'],a,b,c,semantic.third(row['current'],row['prior'])[1])
            if reason!=row['reason'] or any(row.get(k)!=v for k,v in expected.items()):
                raise ValueError('Derived features do not reproduce from the frozen raw answers.')
    if used!={p.stem for p in (OUTPUT/'raw_jev').glob('*.json')}:
        raise ValueError('Unaccounted JEV records; no extra probing is allowed.')
    return records


def review_sample(rows):
    """Record the outcome-blind source review; never change the frozen labels."""
    selected=[]
    for group in ['improved','unchanged','deteriorated']:
        selected.extend(sorted([r for r in rows if r['eligible'] and r['group']==group],key=lambda r:r['accession_number'])[:3])
    selected.extend(sorted([r for r in rows if not r['eligible'] and r.get('prior')],key=lambda r:r['accession_number'])[:3])
    notes={
        '0000732712-24-000025':'Current April and prior January exhibits both give the 2024 adjusted EPS range 4.50–4.70. Current wording continues to expect the same guidance; no explicit visibility change is established.',
        '0000732712-24-000049':'Current July and prior April exhibits both give the 2024 adjusted EPS range 4.50–4.70. The on-track language is routine guidance reaffirmation, not explicit improved visibility.',
        '0000732712-24-000062':'Current October and prior July exhibits both give the 2024 adjusted EPS range 4.50–4.70. The slight positive continuous Score does not establish an explicit deterioration group.',
        '0001551152-24-000024':'Current July adjusted diluted EPS guidance is 10.61–10.81; selected prior April 3 range is 10.97–11.17. The current source instead references April 26 guidance, so the selected pair is not independently verified as the latest real prior forecast. The acquisition-expense uncertainty language recurs in both sources; it does not establish a new visibility change. Midpoint change also exceeds 2%.',
        '0001551152-24-000033':'Current October range is 10.67–10.87; selected prior July 3 range is 10.61–10.81. The current source references more recent August 1 guidance. The same acquisition-expense uncertainty passage is recurring, and selecting it while labeling unchanged conflicts with the frozen evidence rule.',
        '0001551152-25-000002':'Current January 2025 source updates full-year 2024 guidance to 10.02–10.06; selected October 3 prior is 10.67–10.87. The current document references more recent October 30 guidance. Both cite the same unforecast acquisition expense mechanism; midpoint change also exceeds 2%.'}
    result=[]
    for row in selected:
        if row['accession_number'] not in notes:raise ValueError('Deterministic source sample requires an explicit analyst review.')
        for name in ['current','prior','evidence']:
            if row.get(name):citation(row[name])
        result.append({'accession_number':row['accession_number'],'ticker':row['ticker'],
            'eligible':row['eligible'],'frozen_reason':row['reason'],
            'current':row['current'],'prior':row['prior'],'evidence':row.get('evidence'),
            'note':notes[row['accession_number']],
            'latest_prior_discrepancy':row['ticker']=='ABBV',
            'independent_gold_label':False,'labels_changed':False})
    freeze(OUTPUT/'source_review.json',result)
    return result


def metrics():
    packets=verify_sources();rows=json.loads((OUTPUT/'semantic_features.json').read_text())
    gate=json.loads((OUTPUT/'semantic_gate.json').read_text())
    if gate!=semantic.feasibility(rows):raise ValueError('Semantic gate changed.')
    if gate['passed']:raise RuntimeError('This completed failure reporter cannot stand in for an economic analysis.')
    forbidden=['market','joined_outcomes.json','economic_results.json','oos_results.json','judges_results.json']
    if any((OUTPUT/name).exists() for name in forbidden):raise ValueError('A later-stage artifact exists after a failed semantic gate.')
    source_rows=json.loads((OUTPUT/'candidate_sources.json').read_text());quote_n=0
    for source in source_rows:
        for candidate in source['candidates']:citation(candidate);quote_n+=1
    for path in (OUTPUT/'http').glob('*.json'):
        record=json.loads(path.read_text());req=record['request'];validate_scope(req['path'],req['params'],req['scope'])
        if record['sha256']!=digest(record['response']):raise ValueError('Source HTTP cache changed.')
    raw=verify_measurement(rows,packets);reviews=review_sample(rows)
    wall=np.array([r['wall_s'] for r in raw]);input_tokens=0;output_tokens=0;usage_missing=0
    for record in raw:
        usage=(record['response'] or {}).get('usage',{})
        if 'input_tokens' not in usage or 'output_tokens' not in usage:usage_missing+=1
        input_tokens+=usage.get('input_tokens',0);output_tokens+=usage.get('output_tokens',0)
    malformed=sum(r['malformed'] for r in rows)
    questions=sum(len(r['request']['questions']) for r in raw)
    # A malformed successful request invalidates every answer in that batch.
    malformed_hashes={h for row in rows if row['malformed'] for h in row['request_hashes'][-1:]}
    valid_questions=questions-sum(len(json.loads((OUTPUT/'raw_jev'/f'{h}.json').read_text())['request']['questions'])
                                  for h in malformed_hashes)
    result={'experiment':PROTOCOL['experiment'],'window':PROTOCOL['window'],
        'protocol_sha256':digest(PROTOCOL),'measurement_sha256':digest(semantic.specification()),
        'enrollment':json.loads((OUTPUT/'enrollment_counts.json').read_text()),
        'filings_by_year':dict(Counter(r['filing_date'][:4] for r in source_rows)),
        'source_gate':json.loads((OUTPUT/'source_gate.json').read_text()),
        'citations':{'packages':len(source_rows),'exact_range_quotes':quote_n,'exact_range_contexts':quote_n},
        'semantic':{'gate':gate,'source_candidates':len(rows),'request_batches':len(raw),
            'questions':questions,'valid_questions':valid_questions,'malformed_requests':malformed,
            'batches_by_question_count':dict(Counter(str(len(r['request']['questions'])) for r in raw)),
            'http_attempts':sum(len(r['attempts']) for r in raw),
            'retries':sum(len(r['attempts'])-1 for r in raw),
            'sum_request_wall_s':float(wall.sum()),'mean_request_wall_s':float(wall.mean()),
            'median_request_wall_s':float(np.median(wall)),'p95_request_wall_s':float(np.quantile(wall,.95)),
            'input_tokens':input_tokens,'output_tokens':output_tokens,'usage_missing_responses':usage_missing,
            'estimated_jev_cost_usd':input_tokens*.042/1e6 if not usage_missing else None,
            'current_abstentions':sum(r.get('current_choice')=='none' for r in rows),
            'current_below_probability_floor':sum(r.get('current_choice') not in [None,'none'] and r.get('current_choice_probability',1)<.8 for r in rows),
            'complete_pair_measurements':sum(len(r['request_hashes'])==3 and not r['malformed'] for r in rows),
            'reviewed_pairs':len(reviews),'latest_prior_review_discrepancies':sum(r['latest_prior_discrepancy'] for r in reviews)},
        'economic':{'status':'not_run_semantic_gate_failed','JEV_vs_baseline':None,'group_separation':None,
            'uncertainty_intervals':None,'sensitivity':None,
            'strategies':{s:{'status':'not_run_semantic_gate_failed','historical_edge':None,'after_cost_edge':None,'interval':None} for s in STRATEGIES}},
        'decision':{'status':'semantic_infeasible','hypothesis_tested':False,'strategy_selected':None,
            'oos_opened':False,'judges_opened':False,
            'reason':'Expanded source coverage passed, but only three eligible unchanged forecasts from one company survived. No explicit changed-state contrast exists; this is not a null economic result.'},
        'prior_research_files_preserved':len(json.loads((OUTPUT/'preservation.json').read_text())),
        'limitations':['The 30,000-byte request ceiling is conservative and excluded 33 events across the first two stages.',
            'Selected-range probabilities are not calibrated factual accuracy; one response violated the documented Choice argmax contract.',
            'The deterministic review found three rejected pairs whose current text references a later prior forecast absent from the selected source pair.',
            'The three eligible events are all Verizon 2024 adjusted EPS reaffirmations, not a representative sample of guidance disclosures.',
            'Sources before2024 are excluded, reducing prior availability; static universe selection can cause survivorship bias.',
            'Recurring contingency language is not an explicit change. No semantic superiority, economic null, or trading edge has been established.',
            'Rate-based JEV usage estimate is not an invoice. Massive subscription and SEC acquisition costs were not measured.']}
    paths=list((OUTPUT/'raw_jev').glob('*.json'))+[OUTPUT/n for n in ['measurement_specification.json','semantic_features.json','semantic_gate.json','source_review.json']]
    freeze(OUTPUT/'semantic_manifest.json',{str(p.relative_to(ROOT)):checksum(p) for p in sorted(paths)})
    return result,rows,reviews


def report():
    result,rows,reviews=metrics();freeze(OUTPUT/'metrics.json',result);save(ROOT/'EXPANDED_GUIDANCE_METRICS.json',result)
    e=result['enrollment'];s=result['semantic'];g=s['gate']
    lines=['# Expanded guidance experiment: completed results','',
        '**Decision: `semantic_infeasible`. Source coverage improved; the economic hypothesis was not tested.**','',
        'Experiment 4B added quarterly earnings, annual earnings and preliminary-results sources to the original guidance tags. The 2024–2025 window, original 100-company universe, full-year guidance metric hierarchy, 2% midpoint tolerance, feasibility floors and economic hypothesis were unchanged. This expansion followed the parent source failure and is exploratory. The parent audit remains intact.','',
        '## Frozen chronology','',
        'Source protocol commit: `f6360b8`, before acquisition. Measurement commit: `baa0488`, before the first model request. Acquisition and measurement completed October 3, 2026. Exact specifications are in `docs/research/EXPANDED_GUIDANCE_PROTOCOL.md` and `docs/research/EXPANDED_GUIDANCE_MEASUREMENT.md`.','',
        f'Protocol SHA256: `{result["protocol_sha256"]}`. Measurement SHA256: `{result["measurement_sha256"]}`.','',
        '## Coverage and attrition','',
        '| Stage | Parent | Expanded |','|---|---:|---:|',
        f'| Unique enrolled filings | 60 | {e["filings"]} |',
        f'| Enrolled companies | 27 | {e["companies"]} |',
        f'| Potential numerical-range filings | 43 | {result["source_gate"]["potential_pairs"]} |',
        f'| Companies with potential ranges | 17 | {result["source_gate"]["companies"]} |',
        f'| Original packages validated | 60/60 | {e["filings"]}/{e["filings"]} |','',
        f'The expanded acquisition retained {e["taxonomy_rows"]:,} taxonomy rows before fixed-universe filtering and accession deduplication. Enrollment contains 115 filings from 2024 and 93 from 2025. No original package failed validation. The source gate passed its 80-event/20-company floors; 81 filings had no current bounded candidate. All {result["citations"]["exact_range_quotes"]:,} extracted range quotes and contexts were verified against original normalized-document offsets and hashes. Potential ranges are not confirmed eligible forecasts.','',
        '| Semantic disposition | Filings |','|---|---:|']
    lines += [f'| {reason.replace("_"," ")} | {count} |' for reason,count in g['exclusions'].items()]
    lines += [f'| Eligible | {g["eligible"]} |','',
        f'Of the 76 current-forecast exclusions, {s["current_abstentions"]} were explicit abstentions and {s["current_below_probability_floor"]} selected a range below the 0.80 probability floor. Capacity excluded 22 initial requests and 11 prior-selection requests. The 30,000-byte ceiling is conservative: these exclusions do not prove the service could not process the filings. Successful answers were never resampled.','',
        '## What the semantic measurement found','',
        'Eight current/prior pairs reached the complete third measurement. Three were eligible, all Verizon full-year 2024 adjusted EPS reaffirmations. Five AbbVie pairs were excluded because they labeled unchanged while selecting purported changed-state evidence. Some also exceeded the 2% midpoint tolerance; attrition records the first failing condition rather than mutually overlapping failure counts.','',
        '| Eligible filing | Fiscal year | Current / prior EPS range | Group | Uncertainty Score |','|---|---:|---|---|---:|']
    lines += [f'| {r["ticker"]} {r["filing_date"]} | {r["fiscal_year"]} | $4.50–$4.70 / $4.50–$4.70 | {r["group"]} | {r["uncertainty_score"]:.3f} |' for r in rows if r['eligible']]
    lines += ['',
        f'The eligible sample has one company, effective company count {g["effective_company_n"]:.1f}, largest company share {g["max_company_share"]:.0%}, uncertainty standard deviation {g["uncertainty_sd"]:.3f}, and zero explicit changed events. It fails the frozen 80-event, 20-company, concentration, dispersion and changed-state requirements. The malformed fraction was {g["malformed_fraction"]:.2%}, below the 5% maximum; this alone does not qualify the sample.','',
        'The single malformed successful response selected a Choice that was not its reported highest-probability option. Its raw response is retained and the event excluded. This is an API-contract failure, not missing source evidence.','',
        '## Outcome-blind source review','',
        'The deterministic review covered all three eligible unchanged pairs and the first three rejected pairs. There were no eligible improved or deteriorated pairs to sample. Exact current/prior/evidence citations are archived in `expanded_guidance_results/source_review.json`; labels and thresholds remain unchanged. This is analyst review, not independent human gold-label calibration.','']
    lines += [f'- **{r["ticker"]} {r["accession_number"]}:** {r["note"]}' for r in reviews]
    lines += ['',
        'The recurring acquisition-expense language and missing more recent prior forecasts are measurement limitations. A valid structured response or high pair-selection probability cannot establish factual correctness. The rejected pairs remain rejected; no corrective rescoring or outcome search was performed.','',
        '## Model speed and usage','',
        f'The run made {s["request_batches"]} requests containing {s["questions"]} typed judgments: 105 four-question current-selection batches, 17 prior-selection requests and eight five-question pair/evidence batches. {s["valid_questions"]} judgments passed the complete response contract. There were {s["retries"]} transport retries. These judgments are not independent economic observations.','',
        f'Summed request wall time was {s["sum_request_wall_s"]:.2f} seconds, median {s["median_request_wall_s"]:.3f} seconds, and 95th percentile {s["p95_request_wall_s"]:.3f} seconds. Input usage was {s["input_tokens"]:,} tokens and output usage {s["output_tokens"]:,} tokens. At the documented $0.042 per million input tokens and free output, estimated incremental JEV usage cost was ${s["estimated_jev_cost_usd"]:.5f}. This is a rate-based estimate, not a bill or total project cost. Massive subscription and SEC acquisition costs were not measured.','',
        '## Economic evidence unavailable','',
        '| Predefined payoff structure | Historical edge / intervals / costs / sensitivity |','|---|---|']
    lines += [f'| {name.replace("_"," ")} | Not run: semantic gate failed |' for name in STRATEGIES]
    lines += ['',
        'There is no JEV-versus-baseline prediction result, meaningful semantic-group separation, horizon consistency result, ordinary-day edge, transaction-cost-adjusted edge or uncertainty interval. The economic hypothesis remains untested. No final strategy was selected or OOS rule frozen. The 2026 OOS and judges’ sealed windows remain unopened.','',
        '## Research conclusion and implementation boundary','',
        'Widening the source tags solved the initial acquisition-count shortfall but did not produce a usable comparative uncertainty cohort under this measurement design. It is not evidence that guidance uncertainty has no economic value. Increasing source coverage again, lowering thresholds or rescoring successful requests would not confirm the present hypothesis. Any redesigned extractor or semantic experiment requires a separate exploratory specification before new labels or outcomes.','',
        'The executable pipeline implements guarded in-sample source acquisition, original-package validation, exact numerical candidates, sequential JEV range/pair/evidence measurement, Decimal normalization, feasibility gates, citation review and completed-result reporting. Economic models, five-strategy evaluation and later validation stages are protocol specifications; they were not implemented or executed after the semantic failure.','',
        '## Reproduction','',
        '```bash','.venv/bin/python expanded_guidance_sources.py verify',
        '.venv/bin/python expanded_guidance_semantics.py measure',
        '.venv/bin/python expanded_guidance_report.py',
        '.venv/bin/python -m unittest discover -v','```','',
        f'The completed run verifies and reuses immutable local records without new HTTP calls. The audit protects {result["prior_research_files_preserved"]:,} prior research files against their original hashes. Original packages, requests, responses and manifests are in ignored `expanded_guidance_results/`; public aggregate evidence is `EXPANDED_GUIDANCE_METRICS.json`. A fresh uncached acquisition needs the configured Massive and TypeSafe keys. Changed frozen records fail explicitly; do not delete successful responses to rescore.','']
    (ROOT/'docs/research/EXPANDED_GUIDANCE_RESULTS.md').write_text('\n'.join(lines))
    print(json.dumps(result['decision'],indent=2))


if __name__=='__main__':report()
