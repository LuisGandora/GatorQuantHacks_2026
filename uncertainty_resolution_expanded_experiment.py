"""Experiment 9B runner: selftest, freeze, enroll, source, semantics, audit, verify.

Canonical fail-fast path (each later stage requires explicit authorization):

    .venv/bin/python uncertainty_resolution_expanded_experiment.py selftest
    .venv/bin/python uncertainty_resolution_expanded_experiment.py freeze
    .venv/bin/python uncertainty_resolution_expanded_experiment.py enroll
    .venv/bin/python uncertainty_resolution_expanded_experiment.py source
    .venv/bin/python uncertainty_resolution_expanded_experiment.py semantics
    .venv/bin/python uncertainty_resolution_expanded_experiment.py audit
    .venv/bin/python uncertainty_resolution_expanded_experiment.py verify

``freeze`` is source-only and freezes the taxonomy decision table and the protocol before
any enrollment. ``enroll`` and ``source`` acquire filings; ``semantics`` is the only
stage that calls the JEV endpoint. This experiment is outcome-blind: it reads no price,
option record, payoff, ordinary-day market record, 2026 filing or judges' sealed artifact
and computes no P&L. ``economics`` is deliberately not implemented; it fails fast and
lists the required downstream gates.
"""
import argparse
import json
import tempfile
from pathlib import Path

from jev_experiment import ROOT, digest, credentials
from departure_experiment import freeze, guarded_starter

import uncertainty_resolution_expanded_spec as spec
import uncertainty_resolution_expanded_sources as sources
import uncertainty_resolution_expanded_semantics as semantics

OUTPUT = sources.OUTPUT
PROTOCOL_MD = ROOT / 'UNCERTAINTY_RESOLUTION_EXPANDED_PROTOCOL.md'
DECISION_TABLE_JSON = ROOT / 'UNCERTAINTY_RESOLUTION_EXPANDED_TAXONOMY_DECISION_TABLE.json'
EVIDENCE_AUDIT_MD = ROOT / 'UNCERTAINTY_RESOLUTION_EXPANDED_EVIDENCE_AUDIT.md'
SUMMARY_JSON = ROOT / 'UNCERTAINTY_RESOLUTION_EXPANDED_SUMMARY.json'

RAW_FOLDERS = ['uncertainty_resolution_expanded_results',
               '.uncertainty_resolution_expanded_cache',
               'uncertainty_resolution_expanded_validation']


def protocol_sha():
    return spec.protocol_sha256()


def custody():
    lines = [line.split('#', 1)[0].strip().rstrip('/')
             for line in (ROOT / '.gitignore').read_text().splitlines()]
    return {'raw_folders': RAW_FOLDERS,
            'ignored': all(folder in lines for folder in RAW_FOLDERS)}


def _freeze_decision_table():
    table = sources.taxonomy_decision_table()
    table_digest = digest(table)
    DECISION_TABLE_JSON.write_text(json.dumps(table, indent=2, allow_nan=False) + '\n')
    OUTPUT.mkdir(exist_ok=True)
    freeze(OUTPUT / 'taxonomy_decision_table.json', table)
    freeze(OUTPUT / 'taxonomy_decision_table_hash.json', {'sha256': table_digest})
    return table, table_digest


def write_protocol_markdown(decision_digest):
    boundary = spec.PROTOCOL['information_boundary']
    lines = [
        '# Experiment 9B: uncertainty-resolution delta, expanded leadership-transition '
        'cohort - protocol', '',
        'Experiment 9B asks whether Experiment 9\'s already-validated semantic measurement '
        'becomes statistically testable on a broader but economically coherent population of '
        'executive leadership-transition Form 8-K disclosures. The only conceptual change is '
        'the event population. The six-dimension ontology, the JEV questions, the R1-R5 '
        'resolution rules, the transition mapping and the filing-level ResolutionDelta are '
        'imported exactly from Experiment 9 and are not redesigned.', '',
        'This Phase 1-2 protocol is outcome-blind. It reads no price, option record, payoff, '
        'ordinary-day market record, 2026 filing or judges\' sealed artifact and computes no '
        'P&L. The frozen economic strategy is stated for a later stage and is NOT executed '
        'here.', '',
        f'Protocol SHA256: `{protocol_sha()}`.', '',
        f'Taxonomy decision-table SHA256: `{decision_digest}`.', '',
        '## Hypothesis (verbatim)', '', spec.HYPOTHESIS, '',
        '## Expansion thesis (verbatim)', '', spec.EXPANSION_THESIS, '',
        '## Primary research question', '', spec.PRIMARY_RESEARCH_QUESTION, '',
        '## Frozen taxonomy inclusion list', '',
        'Included Massive tertiary categories (frozen before any semantic count):', '',
        '| Tag | Massive definition |', '|---|---|',
    ]
    table = sources.taxonomy_decision_table()
    by_tag = {row['tertiary_category']: row for row in table['rows']}
    for tag in spec.TAXONOMY_TAGS:
        lines.append('| `%s` | %s |' % (tag, by_tag[tag]['description']))
    lines += ['', spec.NO_SEPARATE_SUCCESSION_TAG, '',
              'Tag precedence for an accession carrying more than one included tag: '
              + ', '.join('`%s`' % tag for tag in spec.TAG_PRECEDENCE) + '.', '',
              '### Excluded near neighbors', '',
              '| Tag | Massive definition | Rationale |', '|---|---|---|']
    for tag in sorted(spec.NEAR_NEIGHBOR_EXCLUSIONS):
        lines.append('| `%s` | %s | %s |' % (
            tag, by_tag[tag]['description'], spec.NEAR_NEIGHBOR_EXCLUSIONS[tag]))
    lines += ['', 'The full 119-entry decision table, including every excluded category and '
              'its rationale, is frozen as '
              '`UNCERTAINTY_RESOLUTION_EXPANDED_TAXONOMY_DECISION_TABLE.json` with digest '
              f'`{decision_digest}`.', '',
              '### Appointment applicability (not silently rewritten)', '',
              spec.APPOINTMENT_APPLICABILITY, '',
              '## Ontology (six dimensions, imported exactly from Experiment 9)', '',
              '| Dimension | States |', '|---|---|']
    for dimension in spec.DIMENSIONS:
        lines.append('| %s %s | %s |' % (
            dimension['label'], dimension['id'], ', '.join(dimension['states'])))
    lines += ['', spec.NOT_DISCLOSED_ADDITION, '',
              '## Exact JEV questions (imported exactly from Experiment 9)', '',
              'Preamble for every question (verbatim):', '', spec.PREAMBLE, '',
              'Frozen dimension locator questions:', '']
    for dimension in spec.DIMENSIONS:
        lines.append('- `%s`: %s' % (dimension['id'],
                                     spec.stage_a_instruction(dimension)))
    lines += ['', 'Stage B state descriptions are imported verbatim; no wording is changed '
              'for appointment filings.', '',
              '### Disclosure-state Noul (frozen)', '', '> ' + spec.NOUL_QUESTION, '',
              '## Code-owned state resolution rules R1-R5 (imported exactly)', '']
    for rule in spec.RULE_ORDER:
        lines.append('- **%s.** %s' % (rule, spec.RESOLUTION_RULES[rule]))
    lines += ['', '## Transition mapping (imported exactly; equal weights)', '',
              'UNKNOWN whenever either side is insufficient_evidence, not_disclosed or '
              'not_applicable, or the pair is not listed. 0 when the two states are equal. '
              'Otherwise:', '', 'Positive `+1` uncertainty-closing transitions:', '',
              '; '.join('%s: %s -> %s' % key for key in spec.POSITIVE_TRANSITIONS) + '.', '',
              'Negative `-1` uncertainty-opening transitions:', '',
              '; '.join('%s: %s -> %s' % key for key in spec.NEGATIVE_TRANSITIONS) + '.', '',
              spec.NOT_DISCLOSED_TRANSITION_NOTE, '',
              '## Frozen primary signal rule (section 9; no K/R search)', '',
              spec.PRIMARY_RULE_DESCRIPTION, '',
              '## Feasibility floor', '',
              'At least 20 qualifying events, at least 10 distinct issuers and a '
              'largest-issuer share at most 0.20. If the fixed rule cannot reach the floor, '
              'the experiment returns `no_candidate_feasibility_failure` and stops without '
              'opening any economic outcome. The floor is never lowered.', '',
              '## Information boundary', '',
              '**After-state evidence.** ' + boundary['after_state'], '',
              '**Before-state evidence.** Class P: ' + boundary['before_state']['class_P']
              + ' Class C: ' + boundary['before_state']['class_C'], '',
              '**Date-only source rule.** ' + boundary['date_only_source_rule'], '',
              '**Never-after-timestamp fence.** ' + boundary['never_after_timestamp_fence'], '',
              '**Coverage adequacy.** ' + boundary['coverage_adequacy']['rule'], '',
              '## Request ceiling', '',
              'Ceiling: %d serialized UTF-8 bytes. ' % spec.REQUEST_MAX_BYTES
              + spec.PROTOCOL['request_ceiling']['trim_rule'] + ' '
              + spec.PROTOCOL['request_ceiling']['oversized_current_package'], '',
              '## Baseline A: Massive tag alone', '',
              spec.PROTOCOL['baselines']['A_massive_tag_alone'], '',
              '## Baseline B: calendar freshness', '',
              spec.BASELINE_CALENDAR_FRESHNESS['definition'], '',
              '## Baseline C: original departures only', '',
              spec.PROTOCOL['baselines']['C_original_departures_only'], '',
              '## Category-composition check', '',
              spec.PROTOCOL['category_composition'], '',
              '## Mechanism ordering expectation', '', spec.MECHANISM_ORDERING, '',
              '## Blinded measurement validation', '',
              spec.BLINDED_VALIDATION_RULE, '',
              '## Primary trade cell (frozen, NOT executed here)', '',
              '`cash_secured_put`; expiry bucket `3-6m`; OTM 0.05; entry delay 0; max stale '
              '0; premium haircut 0.05 per side; primary horizon +21 trading sessions. '
              'Required horizons: ' + ', '.join(
                  str(h) for h in spec.PRIMARY['required_horizons']) + '.', '',
              'Costs: ' + spec.COSTS['rule'], '',
              'Liquidity: ' + spec.LIQUIDITY, '',
              '## Frozen ordinary-day controls (declared before any market read)', '',
              spec.ORDINARY_DAY_CONTROL, '',
              '## Frozen inference (declared before any market read)', '',
              'Primary analysis inference is the Experiment 9 primary inference imported '
              'exactly (`uncertainty_resolution_spec.PRIMARY["inference"]`): method '
              + spec.PRIMARY['inference']['method'] + '. Draws: '
              + str(spec.PRIMARY['inference']['draws']) + '. Seed: '
              + str(spec.PRIMARY['inference']['seed']) + '. Interval: '
              + spec.PRIMARY['inference']['interval'] + '. Minimum finite fraction: '
              + str(spec.PRIMARY['inference']['min_finite_fraction']) + '.', '',
              'The legacy common inference (`contained_shock_spec.INFERENCE`, seed '
              + str(spec.INFERENCE['seed']) + ') is retained only as a clearly secondary '
              'reference and is never the primary interval.', '',
              '## Frozen sensitivity grid (declared before any market read)', '',
              'OTM ' + ', '.join(str(value) for value in spec.SENSITIVITY['otm'])
              + '; expiry buckets ' + ', '.join(spec.SENSITIVITY['bucket'])
              + '; entry delay ' + ', '.join(str(value)
                                             for value in spec.SENSITIVITY['entry_delay'])
              + '; stale ' + ', '.join(str(value) for value in spec.SENSITIVITY['stale'])
              + '; premium haircut ' + ', '.join(str(value)
                                                 for value in spec.SENSITIVITY['haircut'])
              + '; all required horizons. '
              + 'Predeclared higher-cost numerical scenario: premium haircut each side '
              + str(spec.HIGHER_COST_SCENARIO['premium_haircut_each_side'])
              + ' with the base commission, multiplier and funding rate (see '
              'earnings_payoff_spec net_edge_positive_at_haircut10pct). These are frozen '
              'now; no design choice is deferred.', '',
              '## Downstream gates (declared, not implemented)', '',
              spec.DOWNSTREAM_GATES['note'], '']
    lines += ['- ' + item for item in spec.DOWNSTREAM_GATES['required_before_pricing']]
    lines += ['', spec.DOWNSTREAM_GATES['fail_fast'], '',
              '## Out-of-sample lock', '', spec.OOS_LOCK, '',
              '## Frozen Specification', '', '```json',
              json.dumps(spec.PROTOCOL, indent=2), '```', '']
    PROTOCOL_MD.write_text('\n'.join(lines))


def exposure_statement():
    """What was read before the freeze and what was not.

    This records honestly that earlier experiment protocols, summaries and result
    reports plus the reused source implementation were read for provenance. It does not
    claim that all prior semantic material was never read, and it confirms that no new
    Experiment 9B semantic count or economic outcome is read before the freeze.
    """
    return {
        'read_before_freeze': [
            'departure_results/taxonomy.json (cached Massive disclosure taxonomy metadata '
            'only)',
            'the prior experiment protocols, summaries and result reports (Experiments 6-9) '
            'read for design provenance',
            'the reused frozen helper modules, including uncertainty_resolution_spec/'
            'sources/semantics/validation, read for their functions and to confirm exact '
            'reuse',
        ],
        'prior_report_reads': True,
        'prior_source_implementation_reads': True,
        'selected_passage_text_read_before_freeze': False,
        'experiment_9b_semantic_counts_read_before_freeze': False,
        'experiment_9b_economic_outcomes_read_before_freeze': False,
        'market_reads': 0, 'price_reads': 0, 'option_reads': 0, 'payoff_reads': 0,
        'ordinary_day_market_reads': 0, 'out_of_sample_reads': 0,
        'financial_outcome_reads': 0, 'new_JEV_requests_before_freeze': 0,
        'semantic_counts_computed': 0,
        'note': 'Source-only protocol freeze. Earlier reports and the reused source '
                'implementation were read for provenance; no Experiment 9B semantic count '
                'or economic outcome is read before this freeze. No enrollment, semantic '
                'request, price, option record, payoff, ordinary-day market record, 2026 '
                'filing or judges artifact is read anywhere in this experiment.',
    }


def stage_freeze():
    if not custody()['ignored']:
        raise ValueError('Append the Experiment 9B ignore block to .gitignore before '
                         'freezing.')
    OUTPUT.mkdir(exist_ok=True)
    table, decision_digest = _freeze_decision_table()
    freeze(OUTPUT / 'protocol.json', spec.PROTOCOL)
    freeze(OUTPUT / 'protocol_hash.json', {'sha256': protocol_sha()})
    freeze(OUTPUT / 'code.json', sources.code_manifest())
    freeze(OUTPUT / 'protected_artifacts.json', sources.protected_artifacts())
    freeze(OUTPUT / 'exposure.json', exposure_statement())
    write_protocol_markdown(decision_digest)
    print('Frozen Experiment 9B protocol', protocol_sha(),
          '; taxonomy', spec.TAXONOMY_TAGS, flush=True)
    return table


def stage_dryrun(directory=None):
    """Source-only freeze dry-run that cannot obstruct the real freeze.

    It builds the taxonomy decision table and the protocol in memory, writes them only
    to a temporary directory (default under the system temp root), and returns the
    digests. It never touches ``uncertainty_resolution_expanded_results/``, never
    enrolls, never calls the network and never reads a market record, so no enrollment
    can be undertaken by accident.
    """
    table = sources.taxonomy_decision_table()
    decision_digest = digest(table)
    directory = Path(directory) if directory else Path(
        tempfile.mkdtemp(prefix='experiment9b-dryrun-'))
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'taxonomy_decision_table.json').write_text(
        json.dumps(table, indent=2, allow_nan=False) + '\n')
    (directory / 'protocol.json').write_text(
        json.dumps(spec.PROTOCOL, indent=2, allow_nan=False) + '\n')
    (directory / 'hashes.json').write_text(json.dumps({
        'protocol_sha256': protocol_sha(),
        'taxonomy_decision_table_sha256': decision_digest,
        'output_dir': str(directory),
        'enrollment_undertaken': False,
        'market_reads': 0,
    }, indent=2) + '\n')
    print('Experiment 9B freeze dry-run at', directory,
          '; protocol', protocol_sha(), '; taxonomy', decision_digest, flush=True)
    return {'protocol_sha256': protocol_sha(),
            'taxonomy_decision_table_sha256': decision_digest,
            'output_dir': str(directory), 'enrollment_undertaken': False}


def verify():
    if json.loads((OUTPUT / 'protocol.json').read_text()) != spec.PROTOCOL:
        raise ValueError('Protocol changed; do not migrate or silently rescore.')
    if json.loads((OUTPUT / 'protocol_hash.json').read_text()) != {'sha256': protocol_sha()}:
        raise ValueError('Protocol digest changed.')
    table = sources.taxonomy_decision_table()
    if json.loads((OUTPUT / 'taxonomy_decision_table.json').read_text()) != table:
        raise ValueError('Taxonomy decision table changed.')
    if json.loads((OUTPUT / 'taxonomy_decision_table_hash.json').read_text()) != {
            'sha256': digest(table)}:
        raise ValueError('Taxonomy decision-table digest changed.')
    if json.loads((OUTPUT / 'code.json').read_text()) != sources.code_manifest():
        raise ValueError('Frozen implementation or dependency hash changed.')
    if json.loads((OUTPUT / 'protected_artifacts.json').read_text()) != \
            sources.protected_artifacts():
        raise ValueError('A protected prior frozen artifact changed; stop.')
    if not custody()['ignored']:
        raise ValueError('The private Experiment 9B folders are not ignored.')
    for name in ('state_evidence', 'transitions', 'filing_deltas', 'feasibility_audit',
                 'primary_rule', 'exclusions'):
        path = OUTPUT / (name + '.json')
        hash_path = OUTPUT / (name + '_hash.json')
        if path.exists() and hash_path.exists():
            if digest(json.loads(path.read_text())) != \
                    json.loads(hash_path.read_text())['sha256']:
                raise ValueError('Frozen artifact digest mismatch: ' + name)
    return True


def stage_enroll(workers=4):
    verify()
    ns = guarded_starter(credentials('MASSIVE_API_KEY'))
    events, enrollment = sources.run_enrollment(ns, OUTPUT)
    # The prior pool is acquired with the enrollment so the before side is reproducible.
    sources.run_prior_pool(ns, events, OUTPUT)
    print(json.dumps({'total_events': enrollment['total_events'],
                      'distinct_issuers': enrollment['distinct_issuers'],
                      'composition': enrollment['composition']}, indent=2), flush=True)
    return events


def stage_source():
    verify()
    events = sources.load_events()
    sources.run_package_recovery(events, OUTPUT)
    print('Original package recovery complete for %d enrolled accessions'
          % len(events), flush=True)


def write_evidence_audit(result, tag_lookup):
    state_rows = result['state_rows']
    delta_rows = result['delta_rows']
    audit = result['audit']
    timing = result['timing']
    lines = [
        '# Experiment 9B: expanded leadership-transition evidence audit', '',
        'Outcome-blind semantic measurement only. No price, option record, payoff, '
        'ordinary-day market record, 2026 filing or judges artifact was read and no P&L '
        'was computed.', '',
        f'Protocol `{protocol_sha()}`.', '',
        '## Population', '',
        '| Quantity | Value |', '|---|---:|',
        f'| Enrolled events measured | {len(state_rows)} |',
        f'| Oversized-package exclusions | {len(result["exclusions"])} |',
        f'| Distinct issuers | {audit["distinct_issuers"]} |', '',
        'Composition by primary tag:', '',
        '| Tag | Events | Issuers |', '|---|---:|---:|']
    for tag, stats in audit['tag_composition']['by_tag'].items():
        lines.append('| `%s` | %d | %d |' % (tag, stats['events'], stats['issuers']))
    lines += ['', '## Primary rule and feasibility', '',
              f'K = {result["primary_rule"]["K"]}, R = {result["primary_rule"]["R"]}; '
              f'gate **{result["primary_rule"]["feasibility_gate"]}**.', '']
    feasibility = result['primary_rule']['feasibility']
    if feasibility:
        lines += ['| Primary-group quantity | Value |', '|---|---:|',
                  f'| Events | {feasibility["n"]} |',
                  f'| Distinct issuers | {feasibility["issuers"]} |',
                  f'| Largest-issuer share | {feasibility["max_issuer_share"]} |', '']
    lines += [result['primary_rule']['final'], '',
              '## JEV runtime statistics', '',
              '| Statistic | Value |', '|---|---:|',
              f'| Requests (job slots) | {timing["requests"]} |',
              f'| Cache hits | {timing["cache_hits"]} |',
              f'| Live requests | {timing["live_requests"]} |',
              f'| Malformed responses | {timing["malformed_responses"]} |',
              f'| Wall time (s) | {timing["wall_s"]} |', '']
    EVIDENCE_AUDIT_MD.write_text('\n'.join(lines))
    summary = {
        'experiment': spec.EXPERIMENT,
        'decision': ('expanded_uncertainty_resolution_feasibility_passed'
                     if result['primary_rule']['feasibility_gate'] == 'passed'
                     else 'no_candidate_feasibility_failure'),
        'hypothesis': spec.HYPOTHESIS,
        'protocol_sha256': protocol_sha(),
        'taxonomy_decision_table_sha256': digest(sources.taxonomy_decision_table()),
        'audit': audit,
        'primary_rule': result['primary_rule'],
        'jev': timing,
        'economic_outcomes_computed': False, 'prices_read': 0,
        'ordinary_day_market_read': False, 'oos_opened': False, 'judges_opened': False,
    }
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')


def stage_semantics(workers=4):
    verify()
    events = sources.load_events()
    result = semantics.run_and_write(events=events, workers=workers)
    write_evidence_audit(result, sources.tag_of(events))
    print(json.dumps({
        'events': len(result['delta_rows']),
        'exclusions': len(result['exclusions']),
        'feasibility_gate': result['primary_rule']['feasibility_gate'],
        'requests': result['timing']['requests'],
    }, indent=2), flush=True)
    return result


def stage_audit():
    verify()
    state_rows = json.loads((OUTPUT / 'state_evidence.json').read_text())['rows']
    transition_rows = json.loads((OUTPUT / 'transitions.json').read_text())['rows']
    delta_rows = json.loads((OUTPUT / 'filing_deltas.json').read_text())['rows']
    exclusions = json.loads((OUTPUT / 'exclusions.json').read_text())['rows']
    events = sources.load_events()
    tag_lookup = sources.tag_of(events)
    recomputed = semantics.compute_audit(state_rows, transition_rows, delta_rows,
                                         exclusions, tag_lookup)
    recomputed = json.loads(json.dumps(recomputed, allow_nan=False))
    frozen = json.loads((OUTPUT / 'feasibility_audit.json').read_text())
    if recomputed != frozen:
        raise ValueError('Recomputed feasibility audit disagrees with the frozen audit.')
    recomputed_primary = spec.evaluate_primary(delta_rows)
    frozen_primary = json.loads((OUTPUT / 'primary_rule.json').read_text())
    if recomputed_primary['feasibility_gate'] != frozen_primary['feasibility_gate']:
        raise ValueError('Recomputed primary rule disagrees with the frozen rule.')
    output = {'feasibility_gate': frozen_primary['feasibility_gate'],
              'feasibility': recomputed_primary['feasibility'],
              'reasoning': frozen_primary['selection_rule']}
    print(json.dumps(output, indent=2), flush=True)
    return output


def stage_economics():
    raise NotImplementedError(
        'The Experiment 9B economic stage is not implemented in this repository. '
        'Experiment 9 stopped before pricing, so there is no tested Experiment 9 '
        'economic runner to reuse and no economic artifact may be invented. Before '
        'pricing, every gate must pass:\n  - '
        + '\n  - '.join(spec.DOWNSTREAM_GATES['required_before_pricing'])
        + '\n' + spec.DOWNSTREAM_GATES['fail_fast'])


def stage_selftest():
    import unittest
    suite = unittest.TestLoader().loadTestsFromName('test_uncertainty_resolution_expanded')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print('selftest passed: %d tests' % result.testsRun, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['selftest', 'dryrun', 'freeze', 'enroll',
                                          'source', 'semantics', 'audit', 'verify',
                                          'economics'])
    parser.add_argument('--workers', type=int, default=4)
    arguments = parser.parse_args()
    if not 1 <= arguments.workers <= 8:
        raise ValueError('workers must be 1..8')
    if arguments.stage == 'selftest':
        stage_selftest()
    elif arguments.stage == 'dryrun':
        stage_dryrun()
    elif arguments.stage == 'freeze':
        stage_freeze()
    elif arguments.stage == 'enroll':
        stage_enroll(arguments.workers)
    elif arguments.stage == 'source':
        stage_source()
    elif arguments.stage == 'semantics':
        stage_semantics(arguments.workers)
    elif arguments.stage == 'audit':
        stage_audit()
    elif arguments.stage == 'economics':
        stage_economics()
    else:
        verify()
        print('Verified Experiment 9B protocol', protocol_sha(), '; custody',
              custody()['ignored'], flush=True)
