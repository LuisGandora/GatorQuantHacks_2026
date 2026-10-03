"""Aggregate reporting and immutable source-audit completion for Experiment3B."""
import json
from collections import Counter

import full_source_audit as audit
import full_source_experiment as recovery
from departure_experiment import freeze, save
from jev_experiment import ROOT, digest

OUTPUT = recovery.OUTPUT


def complete_sources():
    recovery.verify()
    rows = json.loads((OUTPUT/'source_audits_draft.json').read_text())
    packets = json.loads((OUTPUT/'candidate_packets.json').read_text())
    # Recompute from the reviewed annotations, never accept hand-edited draft JSON.
    for row,packet in zip(rows,packets,strict=True):
        if row['full_officers'] != [audit.officer_fields(packet,o) for o in packet['targets']]:
            raise ValueError('Draft audit differs from canonical source adjudications.')
    gate = audit.source_gate(rows)
    groups = {
        'newly_recovered':[r['index'] for r in rows if r['coverage']['full']['joint'] and not r['coverage']['short']['joint']],
        'still_insufficient':[r['index'] for r in rows if not r['coverage']['full']['joint']],
        'exhibit99_supported':[r['index'] for r in rows if r['coverage']['full']['joint'] and not r['coverage']['OTHER_8K_SECTION']['joint'] and any(e['type'].startswith('EX-99') for e in r['relevant_exhibits'])],
        'item_only':[r['index'] for r in rows if r['coverage']['FULL_ITEM_5_02']['joint']],
        'ambiguous_multiple':[r['index'] for r in rows if len(r['targets'])>1 or r['note']],
    }
    sample = {k:v[:3] for k,v in groups.items()}
    indices = sorted({i for v in sample.values() for i in v})
    extra = [19,31,40,66,71,76,79,82,90,91,92,93,97,100,111,114,119,123,125]
    findings = {
        0:'Different-role appointment does not establish replacement of departing DCAI head.',
        1:'Same-role successor and January7 role exit explicitly supported in Item5.02.',
        2:'Exhibit names Combat Systems successor; April15 successor start differs from April30 retirement.',
        3:'Separation agreement and January31 exit do not identify a successor.',
        4:'Explicit retirement date, but succession remains unsupported.',
        5:'Separate Liu/Mulligan records; conditional search and named COO handover retained separately.',
        7:'EX99.2, not99.1, names same-role General Counsel successor.',
        12:'Role elimination does not by itself explicitly establish responsibility coverage.',
        16:'June30 role exit and December31 retirement remain separate; CIO succession explicit.',
        26:'Clark appears in attached exhibit; Martinetto duties explicitly reassigned. All original targets retained.',
    }
    import full_source_annotations as annotations
    for i in extra:
        findings.setdefault(i,annotations.NOTES.get(i,'Reviewed departure/successor identity and date binding; unrelated new-role or contract wording excluded.'))
    # Every cited span is checked against the complete normalized original document.
    spans = 0
    for row,packet in zip(rows,packets,strict=True):
        parsed = json.loads((OUTPUT/'parsed'/f'{row["accession"]}.json').read_text())
        documents = {d['filename']:d for d in parsed['documents']}
        for officer in row['full_officers']:
            for fact in [*officer['fields'].values(),officer.get('timing_evidence',audit.unknown())]:
                if fact['status']=='unsupported' and (fact['value'] is not None or fact['citations']):
                    raise ValueError('Unsupported fact acquired a value.')
                for citation in fact['citations']:
                    document = documents[citation['document']]
                    if document['text'][citation['start']:citation['end']] != citation['quote'] or digest(document['text']) != citation['normalized_document_sha256']:
                        raise ValueError('Citation does not match original normalized document.')
                    spans += 1
    validation = {'strata':sample,'sample_indices':indices,'additional_review_indices':extra,
        'findings':{str(i):findings[i] for i in sorted(set(indices+extra))},
        'all_supported_spans_verified':spans,
        'repairs':['Primary8K sequence1 rather than supplementary XBRL cover rendering.',
            'Retain SEC acceptance time separately from next-day FILED AS OF date.',
            'Officer-specific manual dates replace first-effective-date extraction.',
            'Exclude successor promotion motives and separation-contract boilerplate from departure reason.',
            'Undated Scally replacement in short excerpt does not satisfy timing; Scally absent from original package.',
            'Preserve contradictory core/exhibit dates for Duke and Texas Instruments.'],
        'thresholds_changed':False,'new_market_outcomes_inspected':False}
    inputs=[]
    for row,packet in zip(rows,packets,strict=True):
        if not row['coverage']['full']['joint']:continue
        selected = [s for s in packet['sources'] if s['source']=='FULL_ITEM_5_02' or s['document'] in {e['document'] for e in row['relevant_exhibits']}]
        text = 'TARGET DEPARTING OFFICERS: '+', '.join(packet['targets'])+'\n\n'
        refs=[]
        for source in selected:
            label=f'{source["source"]} | {source["document"]} | normalized offsets {source["start"]}:{source["end"]}'
            text += 'SOURCE: '+label+'\n'+source['quote']+'\nEND SOURCE\n\n'
            refs.append({k:source[k] for k in ['document','document_type','source','start','end','normalized_document_sha256']})
        inputs.append({'index':row['index'],'accession_number':row['accession'],'cik':row['cik'],
            'ticker':row['ticker'],'filing_date':row['filing_date'],'supporting_text':text,
            'source_references':refs,'officer_evidence':row['full_officers']})
    freeze(OUTPUT/'source_audits.json',rows)
    freeze(OUTPUT/'source_gate.json',gate)
    freeze(OUTPUT/'audit_validation.json',validation)
    freeze(OUTPUT/'jev_inputs.json',inputs)
    names=['source_audits.json','source_gate.json','audit_validation.json','jev_inputs.json','candidate_packets.json']
    paths=[OUTPUT/n for n in names]+[ROOT/n for n in ['full_source_audit.py','full_source_annotations.py','full_source_experiment.py']]
    manifest={str(p.relative_to(ROOT)):recovery.checksum(p) for p in paths}
    freeze(OUTPUT/'source_manifest.json',manifest)
    freeze(OUTPUT/'source_manifest_hash.json',{'sha256':digest(manifest)})
    summary = source_metrics(rows,gate,validation)
    freeze(OUTPUT/'source_metrics.json',summary)
    if (OUTPUT/'metrics.json').exists():
        summary=json.loads((OUTPUT/'metrics.json').read_text())
    save(ROOT/'FULL_SOURCE_METRICS.json',summary)
    report(summary)
    print('Source audit frozen:',gate['decision'],gate['eligible']['filings'],'filings;',len(inputs),'JEV inputs')


def source_metrics(rows,gate,validation):
    tables = {tier:{k:audit.population([r for r in rows if r['coverage'][tier][k]]) for k in ['scope','timing','succession','joint']}
        for tier in ['short',*audit.TIERS,'full']}
    contributions={tier:{'abruptness_facts_recovered':0,'succession_facts_recovered':0,'filings_helped':0} for tier in audit.TIERS}
    recovered_fields=[]
    for r in rows:
        helped={tier:set() for tier in audit.TIERS}
        for short,full in zip(r['short_officers'],r['full_officers'],strict=True):
            for key,bucket in [('timing','abruptness_facts_recovered'),('succession','succession_facts_recovered')]:
                if short[key] or not full[key]:continue
                fact=full['timing_evidence'] if key=='timing' else full['fields']['succession_arrangement']
                tier=next(t for t in audit.TIERS if any(c['source']==t for c in fact['citations']))
                contributions[tier][bucket]+=1
                helped[tier].add(r['accession'])
            for name in audit.FIELDS:
                before,after=short['fields'][name],full['fields'][name]
                if before['status']=='unsupported' and after['status']=='supported':
                    sources=sorted({c['source'] for c in after['citations']})
                    recovered_fields.append({'accession':r['accession'],'officer':full['officer'],'field':name,
                        'source':sources[0] if len(sources)==1 else 'MULTIPLE_SOURCES','sources':sources})
        for tier in helped:
            if helped[tier]:contributions[tier]['filings_helped']+=1
    freeze(OUTPUT/'field_recovery.json',recovered_fields)
    return {'experiment':'3B','protocol_hash':digest(recovery.PROTOCOL),'cohort_filings':len(rows),
        'cohort_companies':audit.population(rows)['companies'],'source_gate':gate,'coverage':tables,
        'newly_recovered':audit.population([r for r in rows if r['coverage']['full']['joint'] and not r['coverage']['short']['joint']]),
        'still_insufficient':audit.population([r for r in rows if not r['coverage']['full']['joint']]),
        'prior_JEV_qualified':sum(r['experiment3_qualified'] for r in rows),
        'source_contributions':contributions,'field_recovery_counts':dict(Counter(r['source'] for r in recovered_fields)),
        'retrieved_packages':sum(r['item_5_02_recovered'] for r in rows),
        'used_relevant_exhibits_filings':sum(bool(r['relevant_exhibits']) for r in rows),
        'validation':validation,'semantic':None,'economic':None,'decision':None,
        'oos_opened':False,'judges_opened':False,'preservation_verified':True}


def report(summary):
    g=summary['source_gate']; t=summary['coverage']; pop=g['eligible']
    lines=['# Experiment3B: full-source evidence recovery','',
        '## 1. Objective and prior research','',
        'Experiment3 produced valid semantic outputs, but only five filings met its evidence-confidence gate. 3B tests whether the original filing package repairs that evidence bottleneck for the unchanged abruptness × succession-uncertainty hypothesis. Experiments1–3 remain byte-for-byte preserved. Prior 2024–2025 outcomes were examined in Experiment2; any subsequent economic result here is exploratory.','',
        '## 2. Cohort and temporal boundary','',
        f'The exact original {summary["cohort_filings"]} accessions cover {summary["cohort_companies"]} issuers in 2024–2025. All132 original SEC submission packages were recovered and parsed. No replacement accessions, later announcements or amended filings were acquired. Dates in 2026–2027 below are forecasts already stated in original2025 packages, never later documents. SEC acceptance timestamps are retained separately from FILED AS OF dates.','',
        '## 3. Source specification and provenance','',
        'Full Item5.02 text is preserved. Other same-filing sections qualify only if expressly incorporated; none contributed here. Attached exhibits are included only after officer-specific relevance review. EX99.2/plain EX99 count as Other exhibit, rather than being renamed99.1. Candidate exhibits are not automatically approved. Relevant-exhibit metadata records material used for a supported field; it is not a count of every attached agreement.','',
        'Every supported field has an exact quote, original package URL, document filename/type and normalized-document character offsets. These are not raw-byte offsets. Each target officer is retained separately; multi-target filings must support all targets to qualify. Missingness is null/unsupported; explicit negatives require quoted support. Fine descriptive fields are conservatively recorded and are not used to manufacture gate eligibility.','',
        'Complete per-officer records, original bytes, normalized documents and source references are in the ignored `full_source_results` directory. `source_audits.json`, `field_recovery.json`, `audit_validation.json`, `source_manifest.json` and `jev_inputs.json` are the canonical reproducibility artifacts. Raw text is not committed publicly.','',
        '## 4. Evidence coverage','',
        'Both below means timing and succession plus officer scope, consistent with the frozen source gate. Timing/succession alone are also reported separately. Raw source sufficiency is distinct from the prior JEV probability≥0.80 gate.','',
        '| Evidence state | Filings | Companies | % of cohort |','|---|---:|---:|---:|']
    labels=[('Short excerpt sufficient for both','short'),('Full Item5.02 sufficient for both','FULL_ITEM_5_02'),('+ incorporated sections','OTHER_8K_SECTION'),('+ Exhibit99.1','EXHIBIT_99_1'),('+ other relevant exhibits / final full source','full')]
    for label,key in labels:
        p=t[key]['joint'];lines.append(f'| {label} | {p["filings"]} | {p["companies"]} | {p["percent_of_cohort"]:.1f}% |')
    for label,p in [('Full sufficient AND short insufficient',summary['newly_recovered']),('Still insufficient',summary['still_insufficient'])]:
        lines.append(f'| {label} | {p["filings"]} | {p["companies"]} | {p["percent_of_cohort"]:.1f}% |')
    lines += ['','| Feature coverage | Short filings | Full filings |','|---|---:|---:|']
    for key in ['scope','timing','succession']:lines.append(f'| {key} | {t["short"][key]["filings"]} | {t["full"][key]["filings"]} |')
    lines += ['','## 5. Evidence recovery sources','',
        'Counts below are newly supported officer-level timing/succession facts relative to the short excerpt. Filings helped are unique within each source; sources can help the same filing. Cumulative cohort qualification above avoids double counting. Full per-field provenance is retained separately; descriptive-field recovery totals can include fields conservatively left unsupported in the short audit.','',
        '| Recovery source | Timing facts recovered | Succession facts recovered | Filings helped |','|---|---:|---:|---:|']
    for tier,v in summary['source_contributions'].items():lines.append(f'| {tier} | {v["abruptness_facts_recovered"]} | {v["succession_facts_recovered"]} | {v["filings_helped"]} |')
    lines += ['','## 6. Audit validation','',
        f'Deterministic first-three strata were deduplicated into {len(summary["validation"]["sample_indices"])} filings, supplemented by ambiguous officer/date cases. All {summary["validation"]["all_supported_spans_verified"]} supported citation instances were checked against the original normalized documents. This is analyst review, not an independent double-annotator reliability estimate.','',
        'The appendix in `audit_validation.json` records the exact sample and case findings. Repairs corrected supplementary XBRL cover selection, after-hours acceptance dates, cross-officer attribution and undated short-excerpt timing. Compensation dates, successor start dates and ultimate retirement dates are kept distinct. Source definitions and thresholds were not changed.','',
        'Notable exclusions: a Chief Product Officer appointment does not prove COO succession; role elimination alone does not establish coverage; the Citigroup short excerpt names Scally, who is absent from the original package, so its multi-target event remains insufficient. Duke and Texas Instruments disclose inconsistent core/exhibit transition dates, retained explicitly.','',
        '## 7. Frozen source feasibility decision','',
        f'**{g["decision"]}**: {pop["filings"]} filings / {pop["companies"]} companies; effective company N={pop["effective_company_n"]:.2f}; largest issuer share={pop["max_company_share"]:.2%}; retrieval failures={g["retrieval_failure_fraction"]:.1%}. All frozen source checks pass. Source sufficiency does not establish semantic spread, predictive usefulness or profitability.','',
        '| Underlying disclosed fact group | Filings | Companies |','|---|---:|---:|']
    for label,p in g['variation_groups'].items():lines.append(f'| {label} | {p["filings"]} | {p["companies"]} |')
    lines += ['','The protocol was frozen before retrieval; the reviewed audit and exact JEV packages were hashed before scoring. Full-text sources replace excerpts, with document delimiters and target identities; the thirteen questions, model version,0.80 evidence threshold, centering, sample/concentration/variation requirements, economic models and horizons remain unchanged. Source all-target screening is conservative; JEV still assesses the combined departure event as in Experiment3.','']
    if summary.get('semantic'):
        s=summary['semantic'];gate=s['gate'];m=gate['metrics'];lat=s['latency']
        features=json.loads((OUTPUT/'semantic_features.json').read_text())
        evidence={name:{'absent':sum(r[name]=='absent' for r in features),
            'present_below_threshold':sum(r[name]=='present' and r[name+'_probability']<.80 for r in features)}
            for name in ['timing_evidence','succession_evidence','scope_evidence']}
        lines += ['## 8. Unchanged semantic measurement','',
            f'{m["valid"]}/{m["enrolled"]} requests returned valid complete fingerprints. {m["eligible"]} filings across {m["companies"]} companies meet all three evidence Choices at probability≥0.80. Malformed responses: {lat["malformed"]}; HTTP retries: {lat["retries"]}.','',
            f'Semantic gate: **{"passed" if gate["passed"] else "failed"}**. '+('; '.join(gate['reasons']) if gate['reasons'] else 'All frozen criteria pass.')+'.','',
            '| Feature / spread | Mean | SD | IQR |','|---|---:|---:|---:|']
        for name in ['severity','abruptness','succession_uncertainty','confidence_mean','interaction']:
            d=m['distributions'][name];lines.append(f'| {name} | {d.get("mean")} | {d.get("sd")} | {d.get("iqr")} |')
        lines += ['',f'Residual interaction SD={m["residual_interaction_sd"]:.6f}; residual fraction={m["residual_sd_fraction"]:.3f}; standardized condition number={m["condition_number"]}. Evidence exclusions: `{json.dumps(m["evidence_exclusions"])}`. Full ten-dimensional distributions, correlations and raw confidence/probability vectors are retained. Confidence is distribution concentration, not verified correctness.','',
            f'Mean request={lat["request_mean_s"]:.3f}s; median={lat["request_median_s"]:.3f}s; p95={lat["request_p95_s"]:.3f}s; processing wall time={lat["processing_wall_s"]:.2f}s. {lat["valid_feature_scores"]} valid feature scores and {lat["valid_evidence_checks"]} evidence checks. Usage: `{json.dumps(s["usage"])}`. No dollar price or batching speedup is inferred from earlier runs.','']
        lines += ['| Evidence check | JEV selects absent | Selects present but probability <0.80 |','|---|---:|---:|']
        for name,d in evidence.items():lines.append(f'| {name} | {d["absent"]} | {d["present_below_threshold"]} |')
        lines += ['',
            f'All semantic requirements other than minimum eligible filings pass. Effective company N={m["company_effective_n"]:.2f}; largest issuer share={m["max_company_share"]:.2%}. The minimum remains60; it was not reduced to the observed53. Succession exclusions affect16/69 requests (23.2%);11 select absent and five select present below0.80. The one timing exclusion overlaps a succession exclusion. This disagreement with source adjudication is retained, not resolved by rescoring.','',
            'For example, the original General Dynamics exhibit explicitly names Danny Deep for Roualet’s role, but the frozen JEV succession Choice returns absent. Search/conditional-replacement and split-responsibility disclosures also lose eligibility. These are measurement observations only. Source-backed references in each output identify the supplied documents and analyst-supported passages; they are not model-generated quotations and do not prove which passage drove a score.','',
            'The full-source eligible count increased from the prior5 to53, but the cohort-wide60-filing requirement still fails. Continuous interaction spread passes; there is no permission to substitute that for the sample floor. No economic effect, confidence interval on an economic edge, strategy cost or ordinary-day payoff estimate is available from this stopped study.','']
    if summary.get('decision'):
        lines += ['## 11. Replication status and research conclusion','',
            '**'+summary['decision']['decision']+'**: '+summary['decision']['reason'],'',
            'Economic outcomes and five-strategy comparisons were not run because the required gate did not pass. No strategy was selected or OOS rule frozen. 2026 and the judges’ sealed window remain unopened. The economic hypothesis remains untested whenever semantic feasibility fails.','']
        lines += ['The defensible research conclusion is that original contemporaneous sources substantially repair the excerpt bottleneck, but the unchanged semantic qualification procedure still cannot support a valid economic test on this cohort. This is neither evidence of a profitable signal nor a rejection of the economic mechanism. A further study would require a separately registered design, such as a larger historical cohort and an outcome-blind validation of source-to-JEV evidence agreement. Do not lower the threshold, edit the rubric or rescore this experiment to make it pass.','']
    else:
        lines += ['## 11. Replication status','',
            'The source pass authorizes only the unchanged semantic measurement. Economic tests remain blocked pending the semantic gate. Strategy comparisons require a qualified association;2026 requires a separate complete immutable implementable rule. The judges window remains sealed.','']
    lines += ['## Reproduction','',
        'Use `.venv/bin/python full_source_audit.py audit` for a recomputed draft; `.venv/bin/python full_source_report.py` freezes the reviewed audit and exact inputs. `.venv/bin/python full_source_semantics.py measure` applies the frozen questions; `analyze` evaluates only authorized stages and produces aggregate results. Completed artifacts are immutable: reruns verify rather than rescore. A digest mismatch is a hard error requiring explicit investigation, not migration or fallback. Tests: `.venv/bin/python -m unittest test_full_source_experiment test_full_source_semantics test_fingerprint_experiment`.','']
    lines += [f'Protocol SHA256: `{summary["protocol_hash"]}`.',
        'Source/input manifest SHA256: `'+json.loads((OUTPUT/'source_manifest_hash.json').read_text())['sha256']+'`.','',
        'The source audit was committed before measurement. Successful response records retain exact requests, answers, usage and integrity hashes in a dedicated3B cache. Economic helpers reuse the parent frozen pure calculations with all writes confined to3B. No parent cache, artifact or protocol was modified.','']
    (ROOT/'FULL_SOURCE_EVIDENCE_AUDIT.md').write_text('\n'.join(lines))


if __name__=='__main__':
    complete_sources()
