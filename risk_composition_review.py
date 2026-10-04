"""Publish descriptive small-sample limitations without changing the frozen audit.

Wilson intervals supplement the prespecified bootstrap, whose all-correct samples
produce degenerate bounds. These intervals do not alter any gate or reference.
"""
import contextlib
import io
import json
import math

from departure_experiment import freeze
import risk_composition_audit as audit


def wilson(correct, total):
    if not total:
        return None
    z = 1.959963984540054
    p = correct / total
    denominator = 1 + z*z/total
    center = (p + z*z/(2*total)) / denominator
    half = z*math.sqrt(p*(1-p)/total + z*z/(4*total*total)) / denominator
    return [max(0,center-half), min(1,center+half)]


def main():
    # The measurement reporter verifies all original inputs and raw responses.
    # Missing records fail there before HTTP; this review does not do inference.
    with contextlib.redirect_stdout(io.StringIO()):
        audit.report()
    metrics = json.loads((audit.OUTPUT/'metrics.json').read_text())
    supplement = {'post_measurement_descriptive_supplement':True,
        'gate_or_labels_changed':False, 'agreement_wilson_95pct':{},
        'positive_citation_wilson_95pct':{},
        'pricing':{'usd_per_million_input_tokens':.042, 'output_tokens_free':True,
                   'official_source':'https://docs.typesafe.ai/models.md', 'retrieved':'2026-10-03'},
        'estimated_jev_input_cost_usd':metrics['input_tokens']*.042/1e6}
    for name, dimension in metrics['dimensions'].items():
        n = dimension['n']
        correct = sum(v for k,v in dimension['confusion_counts'].items() if k.split(' -> ')[0]==k.split(' -> ')[1])
        supplement['agreement_wilson_95pct'][name] = wilson(correct,n)
        positives = dimension['predicted_positives']
        support = dimension['positive_evidence_support']
        supplement['positive_citation_wilson_95pct'][name] = wilson(round(support*positives),positives) if support is not None else None
    freeze(audit.OUTPUT/'descriptive_review.json',supplement)
    (audit.ROOT/'RISK_COMPOSITION_REVIEW.json').write_text(json.dumps(supplement,indent=2)+'\n')
    lines = ['# What the risk-composition audit establishes', '',
        'The primary contrast is not validated. This is a source-coverage and measurement feasibility finding, not an economic null. Half of the selected filings exceeded the conservative request capacity; the 12 remaining references contained no explicit demand deterioration. No classifier performance estimate for detecting positive demand events is possible.', '',
        'Observed agreement was 12/12 for demand, margin and financing, and 10/12 for execution. Demand and financing were exclusively negative references. The three margin-positive examples were Boeing, Caterpillar and Southern Company; two execution-positive examples were Boeing and Southern Company. The two execution disagreements were analyst-ambiguous versus model-negative labels for U.S. Bancorp and Citigroup. No source references were altered after inference.', '',
        '## Small-sample uncertainty', '',
        'The frozen percentile bootstrap reports [100%, 100%] when every observed answer agrees. That degeneracy reflects a sample with no observed errors; it is not evidence of perfect population accuracy. As a clearly labeled post-measurement descriptive supplement, Wilson intervals below show finite-sample uncertainty under independent Bernoulli sampling assumptions. Those assumptions do not remove convenience-cohort, retrieval or shared-reviewer bias, and the intervals are not part of the frozen gate.', '',
        '| Dimension | Agreement | Supplemental 95% Wilson interval |',
        '|---|---:|---:|']
    for name, dimension in metrics['dimensions'].items():
        lo,hi = supplement['agreement_wilson_95pct'][name]
        lines.append(f"| {name} | {dimension['accuracy']:.1%} | {lo:.1%}–{hi:.1%} |")
    lo,hi = supplement['positive_citation_wilson_95pct']['margin']
    lines += ['', f'The three margin-positive citations all matched the frozen source references, but their supplemental support interval is {lo:.1%}–{hi:.1%}. Neither zero demand examples nor three margin examples can validate the intended economic comparison.', '',
        '## Operational evidence and costs', '',
        f"The 12 requests produced 96 valid typed answers in {metrics['wall_s']:.3f} aggregate request seconds, with no retries. At the official input rate verified on October 3, 2026 ($0.042 per million input tokens; outputs free), {metrics['input_tokens']:,} reported input tokens imply about ${supplement['estimated_jev_input_cost_usd']:.6f} of JEV input usage. This is a rate-based estimate, not an invoice or total project cost. Data access, review labor, execution spreads and financing costs are not measured here.", '',
        '## Next design problem', '',
        'A subsequent protocol should first define and verify genuine earnings-release membership, then preserve complete relevant document coverage through independently validated document-sized requests. The existing taxonomy cache includes investor days, compensation reviews and standalone operational updates. Reusing it indiscriminately leaves the sample poorly matched to the proposed demand-versus-margin earnings hypothesis.', '',
        'Freeze that source and retrieval design before new semantic labels. Require enough independently reviewed positive examples in both primary dimensions before acquiring outcomes. Any broader evaluation remains exploratory; a trading hypothesis still needs an in-sample comparison of all five strategies with numerical/severity baselines, permitted entry timing, costs, sample sizes, horizon consistency and sensitivity. Neither 2026 nor the judges window has been opened.', '',
        'Reproduce this supplement with `.venv/bin/python risk_composition_review.py`. The frozen measurement implementation and gate are unchanged. See [RISK_COMPOSITION_RESULTS.md](RISK_COMPOSITION_RESULTS.md) for the prespecified audit and [RISK_COMPOSITION_PROTOCOL.md](RISK_COMPOSITION_PROTOCOL.md) for source and reference controls.']
    (audit.ROOT/'RISK_COMPOSITION_REVIEW.md').write_text('\n'.join(lines)+'\n')
    print('Published descriptive review; frozen gate and references unchanged.')


if __name__ == '__main__':
    main()
