"""Experiment 8 runner: selftest, freeze, semantics, gate, verify.

Canonical fail-fast path:

    .venv/bin/python adverse_intact_experiment.py selftest
    .venv/bin/python adverse_intact_experiment.py freeze
    .venv/bin/python adverse_intact_experiment.py semantics
    .venv/bin/python adverse_intact_experiment.py gate
    .venv/bin/python adverse_intact_experiment.py verify

``freeze`` is source-only and runs before ``semantics``. ``semantics`` is the only stage that
calls the JEV endpoint. This experiment is outcome-blind: it reads no price, option, payoff,
ordinary-day market record, 2026 filing or judges' sealed artifact and computes no P&L.
"""
import argparse
import json

from jev_experiment import ROOT, digest
from departure_experiment import freeze

import adverse_intact_spec as spec
import adverse_intact_sources as sources
import adverse_intact_guidance as guidance

OUTPUT = sources.OUTPUT
PROTOCOL_MD = ROOT / 'docs/research/ADVERSE_INTACT_PROTOCOL.md'
AUDIT_MD = ROOT / 'docs/research/ADVERSE_INTACT_EVIDENCE_AUDIT.md'
SUMMARY_JSON = ROOT / 'ADVERSE_INTACT_SUMMARY.json'


def protocol_sha():
    return spec.protocol_sha()


def custody():
    lines = [line.split('#', 1)[0].strip().rstrip('/')
             for line in (ROOT / '.gitignore').read_text().splitlines()]
    return {'raw_folders': ['adverse_intact_results', '.adverse_intact_cache'],
            'ignored': 'adverse_intact_results' in lines and '.adverse_intact_cache' in lines}


def question_block(name, question):
    lines = [f'`{name}` ({question["type"]}): {question["instructions"]}']
    if question['type'] == 'choice':
        lines.append('Options: ' + ', '.join(sorted(question['criteria'])))
    return lines


def write_protocol_markdown():
    lines = [
        '# Adverse-current / intact-forward earnings 8-K semantic and feasibility experiment: '
        'protocol', '',
        'Experiment 8 measures, outcome-blind, whether a specific semantic pattern is present in '
        'earnings-related Form 8-K Item 2.02 disclosure packages: a material adverse current-period '
        'operating development together with a maintained or raised quantitative forward outlook '
        'relative to the most recent comparable previously disclosed outlook. The model supplies '
        'typed judgments; code owns the deterministic direction rule and the group assignment. '
        'This stage reads no price, option, payoff, ordinary-day market record, 2026 filing or '
        'judges artifact and computes no P&L. The frozen economic strategy below is stated for a '
        'later economic stage and is NOT executed here.', '',
        f'Protocol SHA256: `{protocol_sha()}`.', '',
        '## Hypothesis (verbatim)', '', spec.HYPOTHESIS, '',
        '## Economic mechanism', '', spec.ECONOMIC_MECHANISM, '',
        '## Source boundary', '', spec.SOURCE_BOUNDARY, '',
        '### Current-guidance rule', '', spec.PROTOCOL['current_guidance_rule'] + '.', '',
        '### Prior-guidance rule and the never-after-timestamp fence', '',
        spec.PROTOCOL['prior_guidance_rule'] + '.', '',
        '## Stage 1 current passages', '',
        'The current passages are the ordered unique union of the frozen Experiment-7 '
        '`selected.outlook` passage ids and the frozen `evidence.B` passage id when it is a real '
        'passage id. When that union is empty the Experiment-7 level-1 `outlook_passage` locator '
        'is run byte-for-byte over that filing and its selected ids are used. A filing whose '
        'union is empty after this step is `NOT_CURRENT_GUIDANCE` and cannot enter any forward '
        'group.', '',
        '## Stage 2 deterministic numeric candidate extraction', '',
        'From the current passages, and separately from the prior passages of the chosen prior '
        'package, pure code extracts numeric guidance candidates with the exact source span and '
        'byte offsets, assigning ids `c0, c1, ...` in document order per side. Recognised shapes '
        'are ranges (`$A to $B`, `$A-$B`, `$A\\u2013$B`, `A% to B%`, `A%-B%`), points (`$A`, '
        '`A%`, `A basis points`) and scaled values (a bare number next to a currency symbol '
        'and/or million/billion/thousand). Endpoints are parsed by code; the model never '
        'produces a number. A side with no candidate records none.', '',
        '## Stage 3 prior source selection (deterministic, pre-event only)', '',
        'For the filing CIK, the enrollment rows with `filing_date` strictly before the current '
        '`filing_date` are sorted most-recent-first and at most the three most recent are '
        'considered. For each in order the Experiment-7 level-1 `outlook_passage` locator is run '
        'over that package; the first prior package that yields at least one selected outlook '
        'passage becomes the chosen prior source. The chosen prior accession, filing date, '
        'filing timestamp, digest, step distance and selected passage ids are recorded. The '
        'prior filing timestamp must be strictly before the current filing timestamp, else the '
        'run fails fast. A source published at or after the current filing timestamp is never '
        'considered. From the current passages only, pure code also detects explicit in-filing '
        'directional language (`reaffirm_or_maintain`, `raise`, `lower`, `withdraw`) and records '
        'every match and its exact matched text.', '',
        '## Stage 4 adjudication (one JEV request per filing)', '',
        'The fixed state note is: ' + spec.FIXED_NOTE, '',
        'The state carries the current passages, the prior passages, and the current and prior '
        'numeric candidate lists. The serialized state ceiling is 26000 UTF-8 bytes; on a breach '
        'all current passages are kept and the prior passage list is trimmed from the end, with '
        'the trim recorded. The fixed common preamble is: ' + spec.PREAMBLE, '',
        '### Adjudication questions', '']
    for name, question in sources.adjudication_questions(['c0'], ['d0']).items():
        lines += question_block(name, question)
    lines += ['', '## Stage 5 deterministic direction (code owns this)', '', spec.DIRECTION_RULES, '',
              '## Stage 6 filing-level groups', '']
    for name, definition in spec.GROUP_DEFINITIONS.items():
        lines.append(f'- `{name}`: {definition}')
    lines += ['', 'If more than one forward flag would fire the filing is `MIXED_FORWARD` and the '
              'collision is recorded. `guidance_only_intact` applies the same forward-intact test '
              'to every valid filing regardless of `A` and is a separate flag, not an exclusive '
              'group.', '',
              '## Feasibility gate (outcome-blind; evaluated and reported, never weakened)', '',
              spec.PROTOCOL['gate_rule'], '',
              'Observed values are reported whatever the outcome, including the eligible filings '
              'examined, how many had a prior package searched, how many found a comparable pair, '
              'the `NO_PRIOR_COMPARABLE_GUIDANCE` count, and the counterfactual issuer share at '
              'several N values.', '',
              '## Primary trade cell (frozen but NOT executed by this stage)', '',
              f"`{spec.PRIMARY['strategy']}`; expiry bucket `{spec.PRIMARY['bucket']}`; OTM "
              f"{spec.PRIMARY['otm']}; entry delay {spec.PRIMARY['entry_delay_sessions']}; max stale "
              f"{spec.PRIMARY['max_stale_sessions']}; premium haircut "
              f"{spec.PRIMARY['premium_haircut_each_side']} per side; primary horizon "
              f"{spec.PRIMARY['horizon']} trading sessions. Required reported horizons: "
              f"{spec.HORIZONS}.", '',
              '## Ordinary-day control method', '',
              'The already frozen `earnings_payoff_results/controls.json` set is reused unchanged: '
              'three issuer-matched ordinary sessions per event, frozen before market acquisition, '
              'with the existing 30-calendar-day Item 2.02 exclusion window.', '',
              '## Costs', '', spec.COSTS['rule'], '',
              '## Liquidity', '', spec.LIQUIDITY, '',
              '## Inference', '',
              spec.INFERENCE['method'] + f", {spec.INFERENCE['draws']} draws, seed "
              f"{spec.INFERENCE['seed']}, {spec.INFERENCE['interval']} interval, minimum finite "
              f"fraction {spec.INFERENCE['min_finite_fraction']}, floor at least "
              f"{spec.INFERENCE['floors']['min_matched_events']} matched events and at least "
              f"{spec.INFERENCE['floors']['min_issuer_clusters']} issuer clusters.", '',
              '## JEV incremental comparison', '',
              'The frozen incremental comparison is INTACT_FORWARD versus GUIDANCE_ONLY_INTACT. '
              'It is stated here and NOT executed by this stage.', '',
              '## Sensitivity grid', '',
              'OTM {0.03, 0.05, 0.10} x bucket {1m, 2m, 3-6m} x entry delay {0, 1} x stale {0, 3} '
              'x haircut {0, 0.05, 0.10}.', '',
              '## Success and failure conditions', '', spec.SUCCESS, '']
    for item in spec.FAILURE:
        lines.append('- ' + item)
    lines += ['', '## Out-of-sample lock', '', spec.PROTOCOL['oos'], '',
              '## Known limitations', '']
    for item in spec.KNOWN_LIMITATIONS:
        lines.append('- ' + item)
    lines += ['', '## Frozen specification', '', '```json', json.dumps(spec.PROTOCOL, indent=2),
              '```', '']
    PROTOCOL_MD.write_text('\n'.join(lines))


def stage_selftest():
    import unittest
    suite = unittest.TestLoader().loadTestsFromName('test_adverse_intact')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print('selftest passed: %d tests' % result.testsRun, flush=True)


def stage_freeze():
    if not custody()['ignored']:
        raise ValueError('Append the adverse-intact ignore block to .gitignore before freezing.')
    events = sources.load_events()
    sources.load_semantic_dataset()
    enrollment = sources.load_enrollment()
    if len(enrollment) != 208:
        raise ValueError('Prior-package pool is not the frozen 208-row enrollment.')
    manifest = sources.input_manifest()
    protected = sources.protected_artifacts()
    OUTPUT.mkdir(exist_ok=True)
    freeze(OUTPUT / 'protocol.json', spec.PROTOCOL)
    freeze(OUTPUT / 'protocol_hash.json', {'sha256': protocol_sha()})
    freeze(OUTPUT / 'code.json', sources.code_manifest())
    freeze(OUTPUT / 'input_manifest.json', manifest)
    freeze(OUTPUT / 'input_manifest_hash.json', {'sha256': digest(manifest)})
    freeze(OUTPUT / 'protected_artifacts.json', protected)
    freeze(OUTPUT / 'protected_artifacts_hash.json', {'sha256': digest(protected)})
    freeze(OUTPUT / 'exposure.json', {
        'read_before_freeze': [
            'the frozen earnings_payoff_results/events.json and lock.json (event metadata only)',
            'the frozen contained_shock_results/semantic_dataset.json and its hash (the frozen A '
            'label and the frozen current-outlook selections); A is never recomputed',
            'expanded_guidance_results/enrollment.json (the 208-row prior-package pool)',
            'the parsed original source packages under expanded_guidance_results/parsed/ for the '
            'frozen cohort and the prior pool',
            'the reused frozen Experiment 7 helper modules for their API functions only',
            'docs/research/EARNINGS_PAYOFF_PROTOCOL.md and docs/research/EARNINGS_PAYOFF_RESULTS.md for the frozen trade rule, '
            'costs and control design (no number was copied into a computed field)',
            'EARNINGS_PAYOFF_FREEZE.json for digest verification only',
        ],
        'selected_text_read_before_freeze': True,
        'market_reads': 0, 'price_reads': 0, 'option_reads': 0, 'payoff_reads': 0,
        'ordinary_day_market_reads': 0, 'out_of_sample_reads': 0, 'financial_outcome_reads': 0,
        'new_JEV_requests_before_freeze': 0,
        'forbidden_artifacts_opened': 0,
        'note': 'Source-only freeze. No price, option, payoff, ordinary-day market record, 2026 '
                'filing, 2026 price or option record, or judges artifact is read anywhere in this '
                'experiment.',
    })
    write_protocol_markdown()
    print('Frozen protocol', protocol_sha(), '; events', len(events), '; prior pool',
          len(enrollment), flush=True)


def verify():
    if json.loads((OUTPUT / 'protocol.json').read_text()) != spec.PROTOCOL:
        raise ValueError('Protocol changed; do not migrate or silently rescore.')
    if json.loads((OUTPUT / 'protocol_hash.json').read_text()) != {'sha256': protocol_sha()}:
        raise ValueError('Protocol digest changed.')
    if json.loads((OUTPUT / 'code.json').read_text()) != sources.code_manifest():
        raise ValueError('Frozen implementation or dependency hash changed.')
    manifest = sources.input_manifest()
    if json.loads((OUTPUT / 'input_manifest.json').read_text()) != manifest:
        raise ValueError('Frozen input manifest changed.')
    if json.loads((OUTPUT / 'input_manifest_hash.json').read_text()) != {'sha256': digest(manifest)}:
        raise ValueError('Input manifest digest changed.')
    protected = sources.protected_artifacts()
    if json.loads((OUTPUT / 'protected_artifacts.json').read_text()) != protected:
        raise ValueError('A protected prior frozen artifact changed; stop.')
    if json.loads((OUTPUT / 'protected_artifacts_hash.json').read_text()) != \
            {'sha256': digest(protected)}:
        raise ValueError('Protected-artifact manifest digest changed; stop.')
    if not custody()['ignored']:
        raise ValueError('The private adverse-intact folders are not ignored in .gitignore.')
    for name, hash_name in [('guidance_table.json', 'guidance_table_hash.json'),
                            ('event_table.json', 'event_table_hash.json')]:
        if (OUTPUT / name).exists():
            if digest(json.loads((OUTPUT / name).read_text())) != \
                    json.loads((OUTPUT / hash_name).read_text())['sha256']:
                raise ValueError('Frozen digest mismatch for ' + name)
    return sources.load_events()


def stage_semantics(workers=4):
    events = verify()
    dataset, timing, gate, stage1 = guidance.run_and_write(events=events, workers=workers)
    print(json.dumps({'gate': gate['passed'], 'n_intact_forward': gate['n_intact_forward'],
                      'issuers': gate['issuers_intact_forward'],
                      'max_issuer_share': gate['max_issuer_share'],
                      'foundations_complete': gate['foundations_complete'],
                      'requests': timing['requests'], 'cache_hits': timing['cache_hits'],
                      'malformed_responses': timing['malformed_responses'],
                      'wall_s': timing['wall_s']}, indent=2), flush=True)
    return dataset, timing, gate, stage1


def stage_gate():
    verify()
    event_table = json.loads((OUTPUT / 'event_table.json').read_text())
    recomputed = guidance.compute_gate(event_table['rows'])
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
