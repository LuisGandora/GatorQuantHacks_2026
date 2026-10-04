"""Experiment 7 runner: selftest, freeze, semantics, gate, verify.

Canonical fail-fast path:

    .venv/bin/python contained_shock_experiment.py selftest
    .venv/bin/python contained_shock_experiment.py freeze
    .venv/bin/python contained_shock_experiment.py semantics
    .venv/bin/python contained_shock_experiment.py gate
    .venv/bin/python contained_shock_experiment.py verify

``freeze`` is source-only and runs before ``semantics``. ``semantics`` is the only
stage that calls the JEV endpoint. This experiment is outcome-blind: it reads no price,
option, payoff, ordinary-day market record, 2026 filing, or judges' sealed artifact and
computes no P&L.
"""
import argparse
import json

from jev_experiment import ROOT, digest
from departure_experiment import freeze

import contained_shock_spec as spec
import contained_shock_sources as sources
import contained_shock_semantics as semantics

OUTPUT = sources.OUTPUT
PROTOCOL_MD = ROOT.parent / 'docs/research/CONTAINED_SHOCK_PROTOCOL.md'
AUDIT_MD = ROOT.parent / 'docs/research/CONTAINED_SHOCK_EVIDENCE_AUDIT.md'
SUMMARY_JSON = ROOT / 'CONTAINED_SHOCK_SUMMARY.json'


def protocol_sha():
    return digest(spec.PROTOCOL)


def custody():
    lines = [line.split('#', 1)[0].strip().rstrip('/')
             for line in (ROOT / '.gitignore').read_text().splitlines()]
    return {'raw_folders': ['contained_shock_results', '.contained_shock_cache'],
            'ignored': 'contained_shock_results' in lines and '.contained_shock_cache' in lines}


def question_block(name, question):
    lines = [f'`{name}` ({question["type"]}): {question["instructions"]}']
    if question['type'] == 'choice':
        lines.append('Options: ' + ', '.join(sorted(question['criteria'])))
    return lines


def write_protocol_markdown():
    lines = [
        '# Contained-shock earnings 8-K semantic experiment: protocol', '',
        'Experiment 7 measures, outcome-blind, whether a specific semantic pattern is present in '
        'earnings-related Form 8-K Item 2.02 disclosure packages. The model supplies typed '
        'judgments; code owns the deterministic decision rule and the group assignment. This stage '
        'reads no price, option, payoff, ordinary-day market record, 2026 filing, or judges artifact '
        'and computes no P&L. The frozen economic strategy below is stated for the later economic '
        'stage and is NOT executed here.', '',
        f'Protocol SHA256: `{protocol_sha()}`.', '',
        '## Protocol amendment (v2, pre-measurement implementation integrity)', '',
        f"This version supersedes protocol digest "
        f"`{spec.PROTOCOL['amendment']['superseded_protocol_sha256']}`. At amendment time the "
        "response cache `.contained_shock_cache/` was empty (0 files), so no measurement had ever "
        "been made under version 1; every version-1 artifact came from a mocked transport and was "
        "destroyed. The change is implementation integrity, not a research-design change:",
        '',
        '1. The Noul boundary is now an OPEN interval. A Noul condition is satisfied iff the '
        f"returned yes-probability is STRICTLY GREATER than {spec.NOUL_CUTOFF}. Exactly "
        f"{spec.NOUL_CUTOFF} (maximum uncertainty) is not satisfied. Missing answers, None, null, "
        "NaN, infinities, strings, booleans and out-of-range values are not satisfied and never "
        "raise.",
        '2. A, B, C and D each additionally require a present, non-empty evidence selection that '
        "is an actual passage id; `none`, null, None, an empty string and a missing key are absent "
        "evidence.",
        '',
        f"Reason: {spec.PROTOCOL['amendment']['reason']}", '',
        'Unchanged: ' + '; '.join(spec.PROTOCOL['amendment']['unchanged']) + '.', '',
        '## Hypothesis (verbatim)', '', spec.HYPOTHESIS, '',
        '## Economic mechanism', '', spec.PROTOCOL['economic_mechanism'], '',
        '## Source boundary', '', spec.PROTOCOL['source_boundary'], '',
        'For each of the 130 frozen events the package is the core 8-K plus every non-empty EX-99 '
        'exhibit, in ascending sequence, with the boundary marker '
        '`\\n\\n[SOURCE DOCUMENT k: <filename> (<type>)]\\n` before each document. EX-101.*, '
        'GRAPHIC, XML, EXCEL, ZIP, JSON, XSD and every other packaging type are excluded and '
        'counted; text is never truncated. The package is split into consecutive, non-overlapping, '
        'line-aligned passages targeting 2000 UTF-8 bytes and at most 3000 bytes, never splitting a '
        'line; the concatenation of all passages reproduces the package byte-for-byte. A single '
        'source line longer than 3000 bytes cannot be split without breaking line alignment, so it '
        'forms one longer passage, preserved byte-for-byte.', '',
        '## Semantic rule', '',
        "Let A = `current_adversity` Noul yes-probability strictly greater than {cutoff} (open "
        "interval) AND a non-empty `adverse_evidence` passage id. "
        "Let B = `forward_outlook_quantitative` Noul yes-probability strictly greater than {cutoff} "
        "AND `forward_outlook_direction` in {{raised, maintained}} AND a non-empty "
        "`forward_outlook_evidence` passage id. "
        "Let C = `realized_containment` Noul yes-probability strictly greater than {cutoff} AND "
        "`containment_state` in {{operational_or_completed, partially_operational}} AND a non-empty "
        "`containment_evidence` passage id. "
        "Let D = `containment_addresses_adverse_cause` strictly greater than {cutoff} AND "
        "`causal_bridge` strictly greater than {cutoff} AND a non-empty `causal_bridge_evidence` "
        "passage id."
        .format(cutoff=spec.NOUL_CUTOFF), '',
        'A filing with any missing, malformed or validator-failing required answer is never '
        'dropped: it is recorded as `invalid_or_missing_response` with A=B=C=D=False, all flags '
        'False and `UNCLASSIFIED`, and it is listed by accession in the timing artifact. It can '
        'never enter a group or help the gate.', '',
        'Level 1 is a recall-oriented locator over consecutive passages; its answers are not the '
        'measurement. Level 2 is the strict measurement: requests 2A (adversity and forward '
        'outlook) and 2B (realized containment and causal bridge), each with the level-1 selections '
        'and their immediate neighbours as context. Neighbours are context only and are never '
        'offered as evidence candidates.', '',
        '### Fixed common preamble (every level-2 question)', '', spec.PREAMBLE, '',
        '### Level-1 locator questions', '']
    for name, text in [('adverse_passage', spec.LEVEL1_ADVERSE),
                       ('outlook_passage', spec.LEVEL1_OUTLOOK),
                       ('remediation_passage', spec.LEVEL1_REMEDIATION)]:
        lines.append(f'- `{name}` (choice): {text}')
    lines += ['', 'Each question offers every passage id in the batch plus `none`.', '',
              '### Request 2A questions', '']
    import contained_shock_semantics as sem
    for name, question in sem.level2a_questions(['<supplied selection ids>']).items():
        lines += question_block(name, question)
    lines += ['', 'Options for `adverse_mechanism` are exactly: '
              + ', '.join(spec.ADVERSE_MECHANISM_OPTIONS) + '.',
              'Options for `forward_outlook_direction` are exactly: '
              + ', '.join(spec.FORWARD_OUTLOOK_DIRECTION_OPTIONS) + '.',
              'Options for `forward_outlook_metric` are exactly: '
              + ', '.join(spec.FORWARD_OUTLOOK_METRIC_OPTIONS) + '.', '',
              '### Request 2B questions', '']
    for name, question in sem.level2b_questions(['<supplied selection ids>']).items():
        lines += question_block(name, question)
    lines += ['', 'Options for `containment_state` are exactly: '
              + ', '.join(spec.CONTAINMENT_STATE_OPTIONS) + '.', '',
              '## Deterministic decision rule', '',
              'A Noul condition is satisfied iff the returned probability for yes is STRICTLY '
              f'GREATER than {spec.NOUL_CUTOFF} (an open interval; exactly {spec.NOUL_CUTOFF} is '
              'not satisfied). This is the only cutoff and is never tuned. Choice questions use '
              'the selected option and evidence questions use the selected passage id. Every '
              'condition A/B/C/D also requires a non-empty evidence selection. Code computes the '
              'flags and the exclusive group; the model never assigns a group:', '',
              '| Flag | Definition |', '|---|---|']
    for name, definition in spec.PROTOCOL['flags'].items():
        lines.append(f'| `{name}` | {definition} |')
    lines += ['', 'Exclusive precedence: ' + ' -> '.join(spec.GROUP_PRECEDENCE) + '.', '',
              f"`eligibility_reason` is a deterministic code string naming which of A, B, C or D "
              "failed and on which sub-condition.", '',
              '## Feasibility gate (outcome-blind)', '',
              f"Gate passed iff N(flag_contained_shock) >= {spec.GATE['min_contained_shock']}, "
              f"distinct CIK issuers in flag_contained_shock >= {spec.GATE['min_issuers']}, "
              f"max issuer share <= {spec.GATE['max_issuer_share']}, and every contained-shock event "
              f"has a non-empty evidence selection for A, B, C and D. Observed values are reported "
              f"whatever the outcome and the rule is never relaxed.", '',
              '## Primary trade cell (frozen but NOT executed by this stage)', '',
              f"`{spec.PRIMARY['strategy']}`; expiry bucket `{spec.PRIMARY['bucket']}`; OTM "
              f"{spec.PRIMARY['otm']}; entry delay {spec.PRIMARY['entry_delay_sessions']}; max stale "
              f"{spec.PRIMARY['max_stale_sessions']}; premium haircut {spec.PRIMARY['premium_haircut_each_side']} "
              f"per side; primary horizon {spec.PRIMARY['horizon']} trading sessions. Required "
              f"reported horizons: {spec.HORIZONS}.", '',
              '## Ordinary-day control method', '',
              'The already frozen `earnings_payoff_results/controls.json` set is reused unchanged: '
              'three issuer-matched ordinary sessions per event, frozen before market acquisition, '
              'with the existing 30-calendar-day Item 2.02 exclusion window.', '',
              '## Costs', '', spec.COSTS['rule'], '',
              '## Liquidity', '', spec.LIQUIDITY, '',
              '## Inference', '', spec.INFERENCE['method'] + f", {spec.INFERENCE['draws']} draws, seed "
              f"{spec.INFERENCE['seed']}, {spec.INFERENCE['interval']} interval, minimum finite "
              f"fraction {spec.INFERENCE['min_finite_fraction']}.", '',
              '## Sensitivity grid', '',
              'OTM {0.03, 0.05, 0.10} x bucket {1m, 2m, 3-6m} x entry delay {0, 1} x stale {0, 3} x '
              'haircut {0, 0.05, 0.10}.', '',
              '## Success and failure conditions', '', spec.SUCCESS, '']
    for item in spec.PROTOCOL['failure']:
        lines.append('- ' + item)
    lines += ['', '## Out-of-sample lock', '', spec.PROTOCOL['oos'], '',
              '## Known limitations', '']
    for item in spec.KNOWN_LIMITATIONS:
        lines.append('- ' + item)
    lines += ['', '## Frozen specification', '', '```json', json.dumps(spec.PROTOCOL, indent=2), '```', '']
    PROTOCOL_MD.write_text('\n'.join(lines))


def stage_selftest():
    import unittest
    suite = unittest.TestLoader().loadTestsFromName('test_contained_shock')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print('selftest passed: %d tests' % result.testsRun, flush=True)


def stage_freeze():
    if not custody()['ignored']:
        raise ValueError('Append the contained-shock ignore block to .gitignore before freezing.')
    events = sources.load_events()
    sources.verify_events_source(events)
    # Verify the frozen input digests and the protected prior artifacts before writing.
    sources.input_manifest(events)
    sources.protected_artifacts()
    OUTPUT.mkdir(exist_ok=True)
    manifest = sources.passages_manifest(sources.build_all_sources(events))
    freeze(OUTPUT / 'passages.json', manifest)
    freeze(OUTPUT / 'passages_hash.json', {'sha256': digest(manifest)})
    freeze(OUTPUT / 'protocol.json', spec.PROTOCOL)
    freeze(OUTPUT / 'protocol_hash.json', {'sha256': protocol_sha()})
    freeze(OUTPUT / 'code.json', sources.code_manifest())
    freeze(OUTPUT / 'input_manifest.json', sources.input_manifest(events))
    freeze(OUTPUT / 'input_manifest_hash.json', {'sha256': digest(sources.input_manifest(events))})
    freeze(OUTPUT / 'protected_artifacts.json', sources.protected_artifacts())
    freeze(OUTPUT / 'protected_artifacts_hash.json',
           {'sha256': digest(sources.protected_artifacts())})
    freeze(OUTPUT / 'exposure.json', {
        'read_before_freeze': [
            'the frozen earnings_payoff_results/events.json and lock.json (event metadata only)',
            'the 130 parsed original source packages under expanded_guidance_results/parsed/',
            'earnings_payoff_results/controls.json, read only to count parent-accession membership; '
            'no market field was read',
            'the reused frozen helper modules for their API functions only',
            'docs/research/EARNINGS_PAYOFF_PROTOCOL.md and docs/research/EARNINGS_PAYOFF_RESULTS.md for the frozen trade rule, '
            'costs and control design (no number was copied into a computed field)',
        ],
        'selected_text_read_before_freeze': True,
        'market_reads': 0, 'price_reads': 0, 'option_reads': 0, 'payoff_reads': 0,
        'ordinary_day_market_reads': 0, 'out_of_sample_reads': 0, 'financial_outcome_reads': 0,
        'new_JEV_requests_before_freeze': 0,
        'note': 'Source-only freeze. No price, option, payoff, ordinary-day market record, 2026 '
                'filing, 2026 price or option record, or judges artifact is read anywhere in this '
                'experiment.',
    })
    write_protocol_markdown()
    print('Frozen protocol', protocol_sha(), '; events', len(events), '; passages',
          manifest['totals']['passages'], '; package bytes', manifest['totals']['package_bytes'],
          flush=True)


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
    if json.loads((OUTPUT / 'input_manifest_hash.json').read_text()) != \
            {'sha256': digest(sources.input_manifest(events))}:
        raise ValueError('Input manifest digest changed.')
    if json.loads((OUTPUT / 'protected_artifacts.json').read_text()) != sources.protected_artifacts():
        raise ValueError('A protected prior frozen artifact changed; stop.')
    if json.loads((OUTPUT / 'protected_artifacts_hash.json').read_text()) != \
            {'sha256': digest(sources.protected_artifacts())}:
        raise ValueError('Protected-artifact manifest digest changed; stop.')
    if not custody()['ignored']:
        raise ValueError('The private contained-shock folders are not ignored in .gitignore.')
    if digest(json.loads((OUTPUT / 'passages.json').read_text())) != \
            json.loads((OUTPUT / 'passages_hash.json').read_text())['sha256']:
        raise ValueError('Frozen passage manifest digest mismatch.')
    if (OUTPUT / 'semantic_dataset.json').exists():
        dataset = json.loads((OUTPUT / 'semantic_dataset.json').read_text())
        if digest(dataset) != json.loads((OUTPUT / 'semantic_dataset_hash.json').read_text())['sha256']:
            raise ValueError('Frozen semantic dataset digest mismatch.')
    return events


def stage_semantics(workers=4):
    events = verify()
    dataset, timing, gate = semantics.run_and_write(events=events, workers=workers)
    print(json.dumps({'gate': gate['passed'], 'n_contained_shock': gate['n_contained_shock'],
                      'issuers': gate['issuers_contained_shock'],
                      'max_issuer_share': gate['max_issuer_share'],
                      'evidence_complete': gate['evidence_complete'],
                      'requests': timing['requests'],
                      'malformed_responses': timing['malformed_responses'],
                      'wall_s': timing['wall_s']}, indent=2), flush=True)
    return dataset, timing, gate


def stage_gate():
    verify()
    dataset = json.loads((OUTPUT / 'semantic_dataset.json').read_text())
    recomputed = semantics.compute_gate(dataset['rows'])
    frozen = json.loads((OUTPUT / 'gate.json').read_text())
    if recomputed != frozen:
        raise ValueError('Recomputed gate disagrees with the frozen gate; stop.')
    print(json.dumps(recomputed, indent=2), flush=True)
    return recomputed


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['selftest', 'freeze', 'semantics', 'gate', 'verify'])
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
    elif arguments.stage == 'gate':
        stage_gate()
    else:
        events = verify()
        print('Verified protocol', protocol_sha(), 'on', len(events), 'events; custody',
              custody()['ignored'], flush=True)
