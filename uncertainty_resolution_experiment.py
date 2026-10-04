"""Experiment 9 runner: selftest, freeze, semantics, audit, verify.

Canonical fail-fast path:

    .venv/bin/python uncertainty_resolution_experiment.py selftest
    .venv/bin/python uncertainty_resolution_experiment.py freeze
    .venv/bin/python uncertainty_resolution_experiment.py semantics
    .venv/bin/python uncertainty_resolution_experiment.py audit
    .venv/bin/python uncertainty_resolution_experiment.py verify

``freeze`` is source-only and runs before ``semantics``. ``semantics`` is the only
stage that calls the JEV endpoint. This experiment is outcome-blind: it reads no
price, option record, payoff, ordinary-day market record, 2026 filing or judges'
sealed artifact and computes no P&L.
"""
import argparse
import json

from jev_experiment import ROOT, digest
from departure_experiment import freeze

import uncertainty_resolution_spec as spec
import uncertainty_resolution_sources as sources
import uncertainty_resolution_semantics as semantics

OUTPUT = sources.OUTPUT
PROTOCOL_MD = ROOT / 'docs/research/UNCERTAINTY_RESOLUTION_PROTOCOL.md'

LIST_FIELDS = ['dimensions_evaluated', 'valid_transitions', 'closing', 'opening',
               'unchanged', 'unknown', 'resolution_delta']


def protocol_sha():
    return digest(spec.PROTOCOL)


def custody():
    lines = [line.split('#', 1)[0].strip().rstrip('/')
             for line in (ROOT / '.gitignore').read_text().splitlines()]
    return {'raw_folders': ['uncertainty_resolution_results', '.uncertainty_resolution_cache'],
            'ignored': ('uncertainty_resolution_results' in lines
                        and '.uncertainty_resolution_cache' in lines)}


def write_protocol_markdown():
    lines = [
        '# Uncertainty-resolution 8-K semantic experiment: protocol', '',
        'Experiment 9 measures, outcome-blind, whether a leadership-change Form 8-K newly '
        'resolves material governance uncertainty that was still open immediately before the '
        'filing. The model supplies typed judgments; code owns the state resolution rules, '
        'the transition mapping and the filing-level ResolutionDelta. This stage reads no '
        'price, option record, payoff, ordinary-day market record, 2026 filing or judges '
        'artifact and computes no P&L. The frozen economic strategy is stated for the later '
        'economic stage and is NOT executed here.', '',
        f'Protocol SHA256: `{protocol_sha()}`.', '',
        '## Pre-measurement amendment (protocol version 2)', '',
        'This protocol supersedes version 1 (digest `' + spec.SUPERSEDED_PROTOCOL_SHA256
        + '`). Amendment date ' + spec.AMENDMENT_DATE + '. '
        + spec.AMENDMENT['no_outcome_opened_under_version_1'], '',
    ]
    for change in spec.AMENDMENT['changes']:
        lines += [f"### {change['id']}. {change['title']}", '', change['change'], '',
                  'Reason: ' + change['reason'], '']
    lines += ['Elements left unchanged: ' + '; '.join(spec.AMENDMENT['unchanged']) + '.', '',
              '## Hypothesis (verbatim)', '', spec.HYPOTHESIS, '',
        '## Information boundary', '',
        '**After-state evidence.** ' + spec.PROTOCOL['information_boundary']['after_state'] + '.', '',
        '**Before-state evidence.** Class P: '
        + spec.PROTOCOL['information_boundary']['before_state']['class_P'] + ' Class C: '
        + spec.PROTOCOL['information_boundary']['before_state']['class_C'] + ' The fixed '
        'lexical net is: ' + '; '.join(
            spec.PROTOCOL['information_boundary']['before_state']['lexical_net']) + '.', '',
        '**Never-after-timestamp fence.** '
        + spec.PROTOCOL['information_boundary']['never_after_timestamp_fence'], '',
        '**Coverage adequacy.** window_complete = '
        + spec.PROTOCOL['information_boundary']['coverage_adequacy']['window_complete']
        + '; prior_retrieved = '
        + spec.PROTOCOL['information_boundary']['coverage_adequacy']['prior_retrieved']
        + '; coverage_adequate = window_complete AND prior_retrieved. '
        + spec.PROTOCOL['information_boundary']['coverage_adequacy']['rule'], '',
        '**Claims flag.** ' + spec.CLAIMS, '',
        '## Ontology (six frozen dimensions)', '',
        '| Dimension | States |', '|---|---|',
    ]
    for dimension in spec.DIMENSIONS:
        lines.append(f"| {dimension['label']} {dimension['id']} | "
                     + ', '.join(dimension['states']) + ' |')
    lines += ['', spec.NOT_DISCLOSED_ADDITION, '',
              'Distinction: ' + spec.PROTOCOL['ontology']['distinction'], '',
              '## Exact JEV questions', '',
              'Preamble for every question (verbatim):', '', spec.PREAMBLE, '',
              '### Stage A localization (one request per event and side)', '',
              'Each request carries the side\'s candidate passages as a numbered list of '
              '`{"id", "text"}` entries, ids unique within the request, a boundary marker '
              'preserved inside each text, and one Choice question per dimension whose criteria '
              'set is that side\'s passage ids plus `none`. Template (verbatim):', '',
              '> ' + spec.STAGE_A_QUESTION_TEMPLATE, '', 'Frozen dimension questions:', '']
    for dimension in spec.DIMENSIONS:
        lines.append(f"- `{dimension['id']}`: " + spec.stage_a_instruction(dimension))
    lines += ['', 'Ceiling: ' + str(spec.REQUEST_MAX_BYTES) + ' serialized UTF-8 bytes. '
              + spec.PROTOCOL['stage_a']['trim_rule'], '',
              '### Stage B bounded state judgment (one request per event and side)', '',
              'The state contains only the passages selected in Stage A for that side, each '
              'labelled with its id, plus the fixed note. One Choice question per dimension that '
              'received a selected passage (never a question with no evidence), criteria = that '
              "dimension's permitted states plus `no_match`. Template (verbatim):", '',
              '> ' + spec.STAGE_B_QUESTION_TEMPLATE, '', 'Frozen state descriptions:', '']
    for dimension in spec.DIMENSIONS:
        lines.append(f"- `{dimension['id']}`: " + dimension['state_description'] + '.')
    lines += ['', 'A dimension whose Stage A selection is none, whose Stage B answer is '
              '`no_match`, or whose chosen state is `insufficient_evidence` is recorded as '
              '`insufficient_evidence`. The full probability distribution, the confidence and '
              'the selected option are retained for every answer.', '',
              '### Disclosure-state Noul (one per side, frozen)', '',
              '> ' + spec.NOUL_QUESTION, '',
              'Boundary: strictly greater than ' + str(spec.NOUL_CUTOFF) + ' (open interval). '
              'Exactly ' + str(spec.NOUL_CUTOFF) + ' is maximum uncertainty and is not '
              'satisfied.', '',
              '## Code-owned state resolution rules R1-R5', '',
              'The model\'s Choice is the state; code then overrides in exactly this order and '
              'records which rule fired.', '']
    for rule in spec.RULE_ORDER:
        lines.append(f"- **{rule}.** " + spec.RESOLUTION_RULES[rule])
    lines += ['', '## Transition mapping (equal weights, never fitted to returns)', '',
              'UNKNOWN whenever either side is `insufficient_evidence`, either side is '
              '`not_disclosed`, either side is `not_applicable`, or the pair is not listed. '
              '0 whenever the two states are equal. Otherwise:', '',
              'Positive `+1` uncertainty-closing transitions:', '']
    lines.append('; '.join('%s: %s -> %s' % key for key in spec.POSITIVE_TRANSITIONS) + '.')
    lines += ['', 'Negative `-1` uncertainty-opening transitions:', '']
    lines.append('; '.join('%s: %s -> %s' % key for key in spec.NEGATIVE_TRANSITIONS) + '.')
    lines += ['', 'Any other differing pair that is not listed is UNKNOWN, and the unlisted '
              'pair is recorded so the protocol can report how often the mapping was silent.',
              '', spec.NOT_DISCLOSED_TRANSITION_NOTE, '',
              '## Filing-level ResolutionDelta', '',
              spec.PROTOCOL['resolution_delta'], '',
              '## Feasibility audit and the K and R freeze', '',
              spec.PROTOCOL['feasibility_audit']['definition'], '',
              spec.PRIMARY_RULE_SELECTION, '',
              'Primary-group floor: at least ' + str(spec.FLOOR['min_events']) + ' events, at '
              'least ' + str(spec.FLOOR['min_issuers']) + ' distinct issuers, largest-issuer '
              'share at most ' + str(spec.FLOOR['max_issuer_share']) + '. If no K and R on the '
              'grid produce a group meeting the floor, the feasibility gate FAILS and the '
              'experiment terminates without opening any economic outcome. The ontology and the '
              'rules are never weakened to manufacture N.', '',
              '## Primary trade cell (frozen but NOT executed by this stage)', '',
              '`cash_secured_put`; expiry bucket `3-6m`; OTM 0.05; entry delay 0; max stale 0; '
              'premium haircut 0.05 per side; primary horizon +21 trading sessions. Required '
              'reported horizons: ' + ', '.join(str(h) for h in spec.PRIMARY['required_horizons'])
              + '. Inference: ' + spec.PRIMARY['inference']['method'] + ', '
              + str(spec.PRIMARY['inference']['draws']) + ' draws, seed '
              + str(spec.PRIMARY['inference']['seed']) + ', '
              + spec.PRIMARY['inference']['interval'] + ' interval, minimum finite fraction '
              + str(spec.PRIMARY['inference']['min_finite_fraction']) + '.', '',
              'Costs: ' + spec.PROTOCOL['costs']['rule'], '',
              'Liquidity: ' + spec.PROTOCOL['liquidity'], '',
              '## Ordinary-day control plan', '',
              spec.PROTOCOL['ordinary_day_control'], '',
              '## Baselines', '',
              spec.BASELINE_CATEGORY_ALONE, '',
              '**' + spec.BASELINE_CALENDAR_FRESHNESS['description'] + '**', '',
              spec.BASELINE_CALENDAR_FRESHNESS['definition'], '',
              '| Class | Definition |', '|---|---|',
              f"| fresh | {spec.BASELINE_CALENDAR_FRESHNESS['fresh']} |",
              f"| stale | {spec.BASELINE_CALENDAR_FRESHNESS['stale']} |",
              f"| unknown | {spec.BASELINE_CALENDAR_FRESHNESS['unknown']} |", '',
              spec.BASELINE_CALENDAR_FRESHNESS['baseline_only'], '',
              '## Mechanism ordering expectation', '',
              spec.MECHANISM_ORDERING, '',
              '## Blinded validation and its transition-sign gate', '',
              spec.BLINDED_VALIDATION, '',
              '## Success criteria', '',
              spec.SUCCESS, '',
              '## Failure conditions', '']
    for item in spec.FAILURE:
        lines.append('- ' + item)
    lines += ['', '## Out-of-sample lock', '', spec.OOS_LOCK, '',
              '## Limitations', '']
    for item in spec.KNOWN_LIMITATIONS:
        lines.append('- ' + item)
    lines += ['', '## Frozen specification', '', '```json',
              json.dumps(spec.PROTOCOL, indent=2), '```', '']
    PROTOCOL_MD.write_text('\n'.join(lines))


def stage_selftest():
    import unittest
    suite = unittest.TestLoader().loadTestsFromName('test_uncertainty_resolution')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print('selftest passed: %d tests' % result.testsRun, flush=True)


def stage_freeze():
    if not custody()['ignored']:
        raise ValueError('Append the uncertainty-resolution ignore block to .gitignore '
                         'before freezing.')
    events = sources.load_events()
    sources.load_source_filings()
    OUTPUT.mkdir(exist_ok=True)
    freeze(OUTPUT / 'protocol.json', spec.PROTOCOL)
    freeze(OUTPUT / 'protocol_hash.json', {'sha256': protocol_sha()})
    freeze(OUTPUT / 'code.json', sources.code_manifest())
    freeze(OUTPUT / 'input_manifest.json', sources.input_manifest(events))
    freeze(OUTPUT / 'protected_artifacts.json', sources.protected_artifacts())
    freeze(OUTPUT / 'exposure.json', {
        'read_before_freeze': [
            'departure_results/events.csv (event metadata and Item 5.02 supporting text only)',
            'departure_results/source_filings.json (same-issuer prior 8-K Item 5.02 text only)',
            'full_source_results/parsed/<accession>.json (the 132 recovered original 8-K '
            'packages, after-state source only)',
            'departure_results/selection.json, only to confirm the frozen category',
            'departure_results/protocol.json (Experiment 2 protocol, not a market field)',
            'the reused frozen helper modules for their functions only',
        ],
        'selected_text_read_before_freeze': True,
        'market_reads': 0, 'price_reads': 0, 'option_reads': 0, 'payoff_reads': 0,
        'ordinary_day_market_reads': 0, 'out_of_sample_reads': 0,
        'financial_outcome_reads': 0, 'new_JEV_requests_before_freeze': 0,
        'note': 'Source-only freeze. No price, option record, payoff, ordinary-day market '
                'record, 2026 filing, 2026 price or option record, or judges artifact is read '
                'anywhere in this experiment.',
    })
    write_protocol_markdown()
    print('Frozen protocol', protocol_sha(), '; events', len(events), flush=True)


def verify():
    if json.loads((OUTPUT / 'protocol.json').read_text()) != spec.PROTOCOL:
        raise ValueError('Protocol changed; do not migrate or silently rescore.')
    if json.loads((OUTPUT / 'protocol_hash.json').read_text()) != {'sha256': protocol_sha()}:
        raise ValueError('Protocol digest changed.')
    if json.loads((OUTPUT / 'code.json').read_text()) != sources.code_manifest():
        raise ValueError('Frozen implementation or dependency hash changed.')
    events = sources.load_events()
    if json.loads((OUTPUT / 'input_manifest.json').read_text()) != sources.input_manifest(events):
        raise ValueError('Frozen input manifest changed.')
    if json.loads((OUTPUT / 'protected_artifacts.json').read_text()) != \
            sources.protected_artifacts():
        raise ValueError('A protected prior frozen artifact changed; stop.')
    if not custody()['ignored']:
        raise ValueError('The private uncertainty-resolution folders are not ignored.')
    for name in ('state_evidence', 'transitions', 'filing_deltas', 'feasibility_audit',
                 'primary_rule'):
        path = OUTPUT / (name + '.json')
        hash_path = OUTPUT / (name + '_hash.json')
        if path.exists():
            if not hash_path.exists():
                raise ValueError('Missing digest for ' + name)
            if digest(json.loads(path.read_text())) != \
                    json.loads(hash_path.read_text())['sha256']:
                raise ValueError('Frozen artifact digest mismatch: ' + name)
    return events


def stage_semantics(workers=4):
    events = verify()
    result = semantics.run_and_write(events=events, workers=workers)
    print(json.dumps({
        'primary_rule': {k: result['primary_rule'][k] for k in ('K', 'R', 'feasibility_gate')},
        'events': len(result['delta_rows']),
        'requests': result['timing']['requests'],
        'malformed_responses': result['timing']['malformed_responses'],
        'wall_s': result['timing']['wall_s'],
    }, indent=2), flush=True)
    return result


def stage_audit():
    events = verify()
    state_rows = json.loads((OUTPUT / 'state_evidence.json').read_text())['rows']
    transition_rows = json.loads((OUTPUT / 'transitions.json').read_text())['rows']
    delta_rows = json.loads((OUTPUT / 'filing_deltas.json').read_text())['rows']
    recomputed = semantics.compute_audit(state_rows, transition_rows, delta_rows)
    recomputed = json.loads(json.dumps(recomputed, allow_nan=False))
    frozen = json.loads((OUTPUT / 'feasibility_audit.json').read_text())
    if recomputed != frozen:
        raise ValueError('Recomputed feasibility audit disagrees with the frozen audit.')
    recomputed_primary = spec.select_primary_thresholds(delta_rows)
    frozen_primary = json.loads((OUTPUT / 'primary_rule.json').read_text())
    if (recomputed_primary['K'] if recomputed_primary else None) != frozen_primary['K'] or \
            (recomputed_primary['R'] if recomputed_primary else None) != frozen_primary['R']:
        raise ValueError('Recomputed K and R disagree with the frozen rule.')
    output = {'feasibility_audit': recomputed,
              'frozen_K': frozen_primary['K'], 'frozen_R': frozen_primary['R'],
              'feasibility_gate': frozen_primary['feasibility_gate'],
              'reasoning': frozen_primary['selection_rule']}
    print(json.dumps(output, indent=2), flush=True)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['selftest', 'freeze', 'semantics', 'audit', 'verify'])
    parser.add_argument('--workers', type=int, default=4)
    arguments = parser.parse_args()
    if not 1 <= arguments.workers <= 8:
        raise ValueError('workers must be 1..8')
    if arguments.stage == 'selftest':
        stage_selftest()
    elif arguments.stage == 'freeze':
        stage_freeze()
    elif arguments.stage == 'semantics':
        stage_semantics(arguments.workers)
    elif arguments.stage == 'audit':
        stage_audit()
    else:
        events = verify()
        print('Verified protocol', protocol_sha(), 'on', len(events), 'events; custody',
              custody()['ignored'], flush=True)
