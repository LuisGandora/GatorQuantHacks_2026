"""Frozen constants for Experiment 9B, "Uncertainty Resolution Delta, Expanded
Leadership-Transition Cohort".

Experiment 9B asks whether Experiment 9's already-validated semantic measurement
becomes statistically testable on a broader but economically coherent population of
executive leadership-transition 8-K disclosures. The only conceptual change is the
event population. The six-dimension ontology, the JEV questions, the R1-R5 resolution
rules, the transition mapping and the filing-level ResolutionDelta are imported
*exactly* from Experiment 9 rather than redesigned.

This module is outcome-blind. It holds only frozen constants and pure functions. It
never reads a price, option record, payoff, ordinary-day market record, 2026 filing, or
judges' sealed artifact, and it never computes P&L. In this Phase 1-2 stage no semantic
count is produced and no source enrollment is performed.

Reuse contract
--------------
The following are imported from ``uncertainty_resolution_spec`` by name, so object
identity is preserved and no ontology text is retyped here:

  * ``DIMENSIONS`` / ``DIMENSION_IDS`` / ``DIMENSION_BY_ID`` / ``STATE_SETS``
  * ``PREAMBLE``, the Stage A and Stage B templates and notes, the Noul question
  * ``RESOLUTION_RULES`` and ``RULE_ORDER`` (R1-R5)
  * ``POSITIVE_TRANSITIONS`` / ``NEGATIVE_TRANSITIONS`` / ``TRANSITION_TABLE``
  * ``transition_value`` and the not-disclosed transition rule
  * ``REQUEST_MAX_BYTES``, ``PRIOR_WINDOW_DAYS``, ``WINDOW_FLOOR``, ``MAX_PRIOR_FILINGS``
  * the verified trade cell, costs, liquidity, inference and calendar-freshness baseline
"""
from pathlib import Path

from jev_experiment import ROOT, HORIZONS, digest

# Exact Experiment 9 semantic objects. Imported, never retyped.
from uncertainty_resolution_spec import (  # noqa: F401 - re-exported for exact reuse
    DIMENSIONS, DIMENSION_IDS, DIMENSION_BY_ID, STATE_SETS,
    PREAMBLE, STAGE_A_QUESTION_TEMPLATE, STAGE_B_QUESTION_TEMPLATE, NOUL_QUESTION,
    NO_MATCH, SIDE_PHRASES, STAGE_A_NOTE, STAGE_B_NOTE, EMPTY_STATE_NOTE, CLAIMS,
    CLASS_C_CUES, RESOLUTION_RULES, RULE_ORDER,
    POSITIVE_TRANSITIONS, NEGATIVE_TRANSITIONS, TRANSITION_TABLE,
    NOT_DISCLOSED_TRANSITION_NOTE, transition_value,
    NOT_DISCLOSED_ADDITION, PRIOR_WINDOW_DAYS, WINDOW_FLOOR, MAX_PRIOR_FILINGS,
    REQUEST_MAX_BYTES, FLOOR, group_feasibility,
    stage_a_instruction, stage_b_instruction, disclosure_instruction,
    MODEL, ENDPOINT, NOUL_CUTOFF, noul_yes,
    PRIMARY, COSTS, LIQUIDITY, INFERENCE,
    BASELINE_CALENDAR_FRESHNESS, BLINDED_VALIDATION,
    SUCCESS, OOS_LOCK,
)

# The frozen sensitivity grid is the established contained-shock / earnings-payoff grid.
from contained_shock_spec import SENSITIVITY  # noqa: F401 - re-exported for exact reuse


EXPERIMENT = '9B uncertainty resolution delta, expanded leadership-transition cohort'
VERSION = 1
START, END = '2024-01-01', '2025-12-31'

# ---------------------------------------------------------------------------
# Frozen taxonomy inclusion list (section 4). Frozen BEFORE any semantic count.
# ---------------------------------------------------------------------------
# The exact Massive tertiary_category names whose definitions directly denote a change
# in executive leadership, executive succession, executive appointment, executive
# departure or interim executive leadership, and for which the Experiment 9 six-dimension
# governance-state ontology is economically meaningful.
TAXONOMY_TAGS = [
    'ceo_appointment',
    'ceo_departure',
    'cfo_appointment',
    'cfo_departure',
    'executive_officer_appointment',
    'executive_officer_departure',
]

# Deterministic precedence used only to give an accession that the provider tagged under
# more than one included category a single primary tag. Departures precede appointments
# because the Experiment 9 ontology's "departing executive" referent is defined for a
# departure and because the original validated population is a departure population.
# Every accession's full tag set is retained separately (``all_tags``).
TAG_PRECEDENCE = [
    'ceo_departure',
    'cfo_departure',
    'executive_officer_departure',
    'ceo_appointment',
    'cfo_appointment',
    'executive_officer_appointment',
]

# The original Experiment 9 population, preserved as a descriptive subgroup (Baseline C).
ORIGINAL_DEPARTURE_TAG = 'executive_officer_departure'

# No separate Massive tag denotes "executive succession" or "interim executive
# appointment"; those concepts are folded into the appointment and departure tags. This
# is recorded so the omission is explicit rather than silently assumed.
NO_SEPARATE_SUCCESSION_TAG = (
    'The cached Massive disclosure taxonomy (119 event types, taxonomy 1.0) contains no '
    'separate executive_succession or interim_executive_appointment tertiary category. '
    'Executive succession and interim executive leadership are folded into the '
    'executive_leadership appointment and departure tags. The frozen list therefore '
    'contains exactly six directly executive leadership appointment/departure tags.'
)

# Near-neighbor exclusions that could be mistaken for the executive-transition family.
# The full decision table is built from the cached taxonomy; these explicit entries fix
# the rationale a reviewer should check.
NEAR_NEIGHBOR_EXCLUSIONS = {
    'executive_compensation_change': (
        'Compensation and employment terms, not a leadership appointment or departure; '
        'the six-dimension succession ontology does not apply.'),
    'director_appointment': (
        'Director-only election or appointment with no executive-management transition; '
        'the ontology departing-executive referent is absent.'),
    'director_departure': (
        'Director-only resignation or removal with no executive-management transition; '
        'the ontology departing-executive referent is absent.'),
    'control_acquisition': (
        'Acquisition of a controlling interest: a corporate-control event, not an '
        'executive leadership transition.'),
    'control_disposition': (
        'Disposition of a controlling interest: a corporate-control event, not an '
        'executive leadership transition.'),
    'going_private_transaction': (
        'Going-private or buyout transaction: an ownership/control event, not an '
        'executive leadership transition.'),
    'reverse_merger': (
        'Reverse merger or shell status change: an M&A/control event, not an executive '
        'leadership transition.'),
    'restructuring_plan': (
        'Restructuring or cost-reduction initiative: a different economic mechanism.'),
    'workforce_reduction': (
        'Layoffs or separation programs: a different economic mechanism.'),
    'facility_closure': (
        'Facility closure or relocation: a different economic mechanism.'),
    'business_line_exit': (
        'Business-line exit: a different economic mechanism.'),
    'acquisition_agreement': (
        'M&A deal agreement: a different economic mechanism.'),
    'merger_agreement': (
        'M&A deal agreement: a different economic mechanism.'),
    'guidance_issuance_or_update': (
        'Financial guidance: a different economic mechanism.'),
    'guidance_withdrawal': (
        'Guidance withdrawal: a different economic mechanism.'),
    'quarterly_earnings': (
        'Ordinary earnings announcement: a different economic mechanism.'),
    'annual_earnings': (
        'Ordinary earnings announcement: a different economic mechanism.'),
    'preliminary_results': (
        'Preliminary financial results: a different economic mechanism.'),
    'voluntary_bankruptcy': (
        'Bankruptcy or insolvency: a different economic mechanism.'),
    'involuntary_bankruptcy': (
        'Bankruptcy or insolvency: a different economic mechanism.'),
    'debt_issuance': (
        'Financing event: a different economic mechanism.'),
    'public_offering': (
        'Equity financing event: a different economic mechanism.'),
    'private_placement': (
        'Equity financing event: a different economic mechanism.'),
    'share_repurchase_program': (
        'Shareholder-return event: a different economic mechanism.'),
    'dividend_declaration': (
        'Shareholder-return event: a different economic mechanism.'),
    'activist_investor_campaign': (
        'Shareholder activism: a different economic mechanism.'),
    'director_nomination': (
        'Shareholder director nomination: a director-level governance contest, not an '
        'executive leadership transition.'),
    'code_of_ethics_change': (
        'Code-of-ethics amendment or waiver: a governance-document change, not a '
        'leadership transition.'),
    'charter_amendment': (
        'Charter amendment: a governance-document change, not a leadership transition.'),
    'bylaw_amendment': (
        'Bylaw amendment: a governance-document change, not a leadership transition.'),
    'fiscal_year_change': (
        'Fiscal-year change: a governance-document change, not a leadership transition.'),
}

# Rationale for every non-near-neighbor secondary category, so the decision table covers
# all 119 taxonomy entries rather than only the hand-listed near neighbors.
EXCLUSION_RATIONALE_BY_SECONDARY = {
    'executive_leadership': 'Outside the executive appointment/departure set: a '
                            'compensation event, not a leadership transition.',
    'board_of_directors': 'Director-only governance event with no executive-management '
                          'transition.',
    'corporate_control': 'Corporate-control or ownership event, not an executive '
                         'leadership transition.',
    'governance_documents': 'Governance-document amendment; no leadership transition.',
    'financial_results': 'Financial-results, guidance or integrity event; a different '
                         'economic mechanism.',
    'strategic_transactions': 'M&A or deal event; a different economic mechanism.',
    'capital_and_financing': 'Financing or shareholder-return event; a different '
                             'economic mechanism.',
    'operations_and_strategy': 'Operational, restructuring or commercial-agreement '
                               'event; a different economic mechanism.',
    'risk_events': 'Risk, legal or insolvency event; a different economic mechanism.',
    'regulatory_and_compliance': 'Auditor, listing or regulatory event; a different '
                                 'economic mechanism.',
    'shareholder_activity': 'Shareholder meeting, activism or insider event; not an '
                            'executive leadership transition.',
}

TAXONOMY_CACHE = ROOT / 'departure_results' / 'taxonomy.json'
# The digest of the cached 119-entry Massive disclosure taxonomy read for this decision.
# It equals departure_results/selection.json's taxonomy_hash, so the decision table is
# built from exactly the taxonomy Experiment 2 froze.
TAXONOMY_SHA256 = '428f5757088272be3bed07c8fd3a71d003611ab41ae43a399f2abe0250b4b40d'


def assert_taxonomy_included(tag):
    """Reject any tag outside the frozen inclusion list."""
    if tag not in TAXONOMY_TAGS:
        raise ValueError('Taxonomy tag is not in the frozen Experiment 9B list: ' + str(tag))
    return tag


def load_taxonomy(path=None):
    """Load the cached Massive taxonomy and verify its frozen digest."""
    import json
    path = Path(path) if path else TAXONOMY_CACHE
    taxonomy = json.loads(path.read_text())
    if digest(taxonomy) != TAXONOMY_SHA256:
        raise ValueError('Cached Massive taxonomy digest changed; stop.')
    return taxonomy


def build_decision_table(taxonomy=None):
    """Full machine-readable decision table over all cached taxonomy entries.

    Every entry records the exact tag name, the Massive definition, INCLUDE or EXCLUDE,
    and a short economic rationale. Included tags are exactly the frozen six. The table
    is sorted by (primary_category, secondary_category, tertiary_category) so its digest
    is deterministic.
    """
    taxonomy = taxonomy if taxonomy is not None else load_taxonomy()
    rows = []
    for entry in taxonomy:
        tag = entry['tertiary_category']
        if tag in TAXONOMY_TAGS:
            decision = 'INCLUDE'
            rationale = ('Directly denotes an executive leadership appointment or departure '
                         'for which the Experiment 9 six-dimension governance-state ontology '
                         'is economically meaningful.')
        else:
            decision = 'EXCLUDE'
            rationale = NEAR_NEIGHBOR_EXCLUSIONS.get(
                tag, EXCLUSION_RATIONALE_BY_SECONDARY.get(
                    entry['secondary_category'],
                    'Not an executive leadership appointment/departure; excluded by the '
                    'frozen inclusion criterion.'))
        rows.append({
            'tertiary_category': tag,
            'primary_category': entry['primary_category'],
            'secondary_category': entry['secondary_category'],
            'description': entry['description'],
            'decision': decision,
            'rationale': rationale,
        })
    rows.sort(key=lambda row: (row['primary_category'], row['secondary_category'],
                               row['tertiary_category']))
    included = [row['tertiary_category'] for row in rows if row['decision'] == 'INCLUDE']
    if included != sorted(TAXONOMY_TAGS):
        raise ValueError('Decision table inclusion does not match the frozen tag list.')
    return {
        'taxonomy': 'Massive disclosure taxonomy 1.0 (119 event types)',
        'taxonomy_sha256': TAXONOMY_SHA256,
        'included_tags': list(TAXONOMY_TAGS),
        'tag_precedence': list(TAG_PRECEDENCE),
        'no_separate_succession_tag': NO_SEPARATE_SUCCESSION_TAG,
        'rows': rows,
    }


def taxonomy_decision_digest(taxonomy=None):
    """The frozen digest of the inclusion list and its per-tag rationales."""
    return digest(build_decision_table(taxonomy))


# ---------------------------------------------------------------------------
# Frozen hypothesis (verbatim from the Experiment 9B brief) and expansion thesis.
# ---------------------------------------------------------------------------
HYPOTHESIS = (
    "Among executive leadership-transition 8-K disclosures, filings that newly resolve "
    "material governance uncertainty that was still open immediately before the filing "
    "will subsequently realize less downside uncertainty than comparable "
    "leadership-transition filings that leave those questions unresolved or create new "
    "uncertainty. Because investors may continue paying for downside protection around a "
    "salient leadership transition after part of the underlying uncertainty has been "
    "resolved, 5%-OTM cash-secured puts entered using Massive's tradeable post-filing t0 "
    "rule with the 3-to-6-month expiry bucket should outperform issuer-matched "
    "ordinary-day cash-secured puts following positive uncertainty-resolution events. "
    "The primary evaluation horizon is +21 trading sessions."
)

EXPANSION_THESIS = (
    'The expanded event family should improve statistical feasibility without changing '
    'the economic meaning of Resolution Delta.'
)

# The brief's primary research question, recorded verbatim, with the appointment
# applicability caveat that must not be silently rewritten.
PRIMARY_RESEARCH_QUESTION = (
    'Does a leadership-transition 8-K that resolves previously open executive-governance '
    'uncertainty identify situations where downside option protection remains overpriced '
    'after the filing?'
)

APPOINTMENT_APPLICABILITY = (
    'The Experiment 9 JEV questions are stated in terms of "the departing executive" and '
    '"a successor to the departing executive". They are imported verbatim for Experiment '
    '9B and are NOT rewritten for appointment filings. For a pure appointment filing the '
    'provider-supplied text may describe the appointee and a predecessor (the departing '
    'executive) in the same Item 5.02 block, in which case the ontology applies with the '
    'predecessor as the departing executive. Whether the ontology actually applies to a '
    'given appointment filing MUST be assessed by the exact frozen questions and by fresh '
    'blinded validation; it is NOT automatically detected by R1-R5 or by the unlisted-pair '
    'rule. When no departing executive is identified the expected outcome is '
    'insufficient_evidence or not_applicable, but that is an empirical expectation to be '
    'measured and independently validated, not a code guarantee. This applicability is a '
    'measurement-validity risk that the orchestrator must accept or reject BEFORE the tag '
    'list is committed; it is flagged, never redefined in code.'
)

# ---------------------------------------------------------------------------
# Fixed primary signal rule (section 9). No K/R search.
# ---------------------------------------------------------------------------
PRIMARY_MIN_VALID_DIMENSIONS = 3
PRIMARY_MIN_RESOLUTION_DELTA = 1
PRIMARY_MIN_CLOSING = 1
PRIMARY_MAX_OPENING = 0

PRIMARY_RULE_DESCRIPTION = (
    'RESOLUTION_EVENT: at least 3 valid governance dimensions are measurable; '
    'ResolutionDelta >= +1; at least one uncertainty-closing transition exists; zero '
    'uncertainty-opening transitions exist. The three-dimension requirement prevents a '
    'filing from qualifying on one isolated semantic judgment. Fixed before Experiment '
    '9B semantic counts and before any Experiment 9B market outcome; never altered after '
    'counts.'
)


# Every filing-level count must be an integer. ``valid_transitions``, ``closing`` and
# ``opening`` are counts of transitions and must be non-negative. ``resolution_delta`` is
# signed: a net uncertainty-opening filing is a legitimate Opening event, not a data
# error, so a negative delta is retained and can never pass the primary rule. A missing,
# boolean, string (for example ``UNKNOWN``) or non-integer value is invalid and fails fast
# rather than passing or being silently coerced.
NONNEGATIVE_COUNT_FIELDS = ('valid_transitions', 'closing', 'opening')
SIGNED_COUNT_FIELDS = ('resolution_delta',)
COUNT_FIELDS = NONNEGATIVE_COUNT_FIELDS + SIGNED_COUNT_FIELDS


def _invalid_count(key, value, row):
    raise ValueError(
        'Invalid or UNKNOWN transition count %s=%r for accession %s; every filing must '
        'carry an integer count and UNKNOWN can never pass the primary rule.'
        % (key, value, row.get('accession_number')))


def assert_transition_counts(row):
    """Fail fast on missing, boolean, non-integer or negative count fields.

    ``resolution_delta`` is signed, so a negative delta is accepted as a legitimate
    Opening value. The three non-negative counts (``valid_transitions``, ``closing`` and
    ``opening``) must be non-negative integers.
    """
    for key in NONNEGATIVE_COUNT_FIELDS:
        value = row.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            _invalid_count(key, value, row)
    value = row.get('resolution_delta')
    if isinstance(value, bool) or not isinstance(value, int):
        _invalid_count('resolution_delta', value, row)
    return row


def primary_group(rows):
    """Rows passing the single frozen primary rule, with no threshold search.

    ``opening`` must be exactly zero. Any row with a missing, negative, boolean or
    non-integer count (including an ``UNKNOWN`` string) fails fast; it is never treated
    as zero and can never pass.
    """
    members = []
    for row in rows:
        assert_transition_counts(row)
        if (row['valid_transitions'] >= PRIMARY_MIN_VALID_DIMENSIONS
                and row['resolution_delta'] >= PRIMARY_MIN_RESOLUTION_DELTA
                and row['closing'] >= PRIMARY_MIN_CLOSING
                and row['opening'] == PRIMARY_MAX_OPENING):
            members.append(row)
    return members


def evaluate_primary(rows):
    """Apply the fixed rule once and evaluate the frozen floor."""
    members = primary_group(rows)
    feasibility = group_feasibility(members)
    return {'rule': 'valid_transitions >= %d, resolution_delta >= %d, closing >= %d, '
                    'opening == %d' % (PRIMARY_MIN_VALID_DIMENSIONS,
                                       PRIMARY_MIN_RESOLUTION_DELTA,
                                       PRIMARY_MIN_CLOSING, PRIMARY_MAX_OPENING),
            # The rule is fixed, not searched, so K and R are the frozen constants
            # (K=3, R=1) rather than None or an outcome-dependent selection.
            'K': PRIMARY_MIN_VALID_DIMENSIONS, 'R': PRIMARY_MIN_RESOLUTION_DELTA,
            'feasibility': feasibility,
            'feasibility_gate': 'passed' if feasibility['meets_floor'] else 'failed',
            'selection_rule': PRIMARY_RULE_DESCRIPTION}


# ---------------------------------------------------------------------------
# Mechanism groups (section 17). Deterministic, code-owned, descriptive only.
# These override the parent's delta-sign description, which read the mechanism as a
# sign ordering. The ontology and the transition mapping are NOT changed.
# ---------------------------------------------------------------------------
MECHANISM_GROUPS = ['Resolution', 'Neutral', 'Opening']
MECHANISM_ORDERING_EXPECTED = ['Resolution', 'Neutral', 'Opening']
MECHANISM_ORDERING = (
    'Mechanism groups (deterministic, code-owned, among valid dimensions): Resolution = '
    'closing >= 1 and opening == 0; Neutral = closing == 0 and opening == 0; Opening = '
    'opening >= 1. A filing with zero valid dimensions has no mechanism evidence and is '
    'reported separately, never as Neutral. Expected CSP-edge ordering: Resolution > '
    'Neutral > Opening. This is a descriptive mechanism check; the trading group is '
    'never redefined if another arm performs better.')


def mechanism_group(row):
    """Classify one filing into the frozen mechanism arms, or None when unmeasured.

    Resolution and Opening take precedence; Neutral requires at least one valid
    dimension so an all-UNKNOWN filing is never called Neutral.
    """
    assert_transition_counts(row)
    if row['opening'] >= 1:
        return 'Opening'
    if row['closing'] >= 1:
        return 'Resolution'
    if row['valid_transitions'] >= 1:
        return 'Neutral'
    return None


def mechanism_composition(rows):
    """Event/issuer counts for the three frozen arms plus the unmeasured disposition."""
    composition = {group: {'events': 0, 'issuers': set()} for group in MECHANISM_GROUPS}
    unmeasured = {'events': 0, 'issuers': set()}
    for row in rows:
        group = mechanism_group(row)
        target = composition[group] if group is not None else unmeasured
        target['events'] += 1
        target['issuers'].add(row['cik'])
    out = {group: {'events': stats['events'], 'issuers': len(stats['issuers'])}
           for group, stats in composition.items()}
    out['unmeasured'] = {'events': unmeasured['events'],
                        'issuers': len(unmeasured['issuers'])}
    out['expected_csp_edge_order'] = list(MECHANISM_ORDERING_EXPECTED)
    return out


# ---------------------------------------------------------------------------
# Frozen economic inputs (section 15), declared now and executed only after every gate.
# The economics stays a gated stub, but no design choice is deferred: ordinary-day
# controls, inference (with minimum finite fraction), the sensitivity grid and the
# predeclared higher-cost numerical scenario are all frozen here.
# ---------------------------------------------------------------------------
ORDINARY_DAY_CONTROL = (
    'Reuse the project\'s already frozen ordinary-day control methodology unchanged: the '
    'earnings_payoff_results/controls.json design of 3 issuer-matched ordinary sessions per '
    'event, frozen before market acquisition, with the existing 30-calendar-day Item 2.02 '
    'exclusion window and the same session-close entry convention as the event; up to 3 '
    'distinct controls without reuse within an issuer, chosen by '
    'sha256(earnings-payoff-v1|accession|YYYY-MM-DD); each event equally weighted and its '
    'available controls averaged to one baseline; each control belongs to one event; no '
    'resampling of missing marks. This stage reads no control and constructs none.')

HIGHER_COST_SCENARIO = {
    'name': 'predeclared higher-cost numerical scenario',
    'premium_haircut_each_side': 0.10,
    'commission_per_contract_side': 0.65,
    'contract_multiplier': 100,
    'annual_funding_rate': 0.05,
    'source': 'earnings_payoff_spec: candidate requirement '
              'net_edge_positive_at_haircut10pct; sensitivity premium_haircut_each_side '
              '[0.0, 0.05, 0.10]',
    'note': 'A modeled cost scenario declared before any market read, not measured fills.',
}


# ---------------------------------------------------------------------------
# Category-composition diagnostic (section 11).
# ---------------------------------------------------------------------------
def tag_composition(delta_rows, tag_of):
    """Event/issuer composition by primary tag; flags any tag above 60%."""
    total = len(delta_rows)
    counts, issuers = {}, {}
    for row in delta_rows:
        tag = tag_of[row['accession_number']]
        counts[tag] = counts.get(tag, 0) + 1
        issuers.setdefault(tag, set()).add(row['cik'])
    composition = {}
    for tag in TAXONOMY_TAGS:
        n = counts.get(tag, 0)
        composition[tag] = {
            'events': n,
            'issuers': len(issuers.get(tag, set())),
            'share_of_primary_group': (n / total) if total else 0.0,
        }
    flagged = [tag for tag, stats in composition.items()
               if stats['share_of_primary_group'] > 0.60]
    return {'events': total, 'by_tag': composition,
            'tags_over_60_percent': flagged,
            'flag': 'tag_concentration' if flagged else None}


# ---------------------------------------------------------------------------
# Downstream economic gates (declared, NOT implemented or executed here).
# ---------------------------------------------------------------------------
DOWNSTREAM_GATES = {
    'status': 'not_implemented',
    'note': (
        'Experiment 9 stopped before pricing, so the Experiment 9B economic stage is a '
        'declared gated stub. Every economic design input is frozen here: ordinary-day '
        'controls, inference with its minimum finite fraction, the sensitivity grid and the '
        'predeclared higher-cost numerical scenario. The reviewer protocol may scope the '
        'full Experiment 9B research, but this gated stub introduces no new permission '
        'requirement: the whole Experiment 9B task (source, semantics, audit and the '
        'gated economic stage) is already authorized, and after every upstream gate passes '
        'this workflow continues automatically into the economic stage without any separate '
        'authorization step. Downstream economics is '
        'written in separate files so this frozen source hash does not change. No price, '
        'option, payoff, ordinary-day market record, 2026 filing or judges artifact may be '
        'read before every gate passes.'),
    'required_before_pricing': [
        'taxonomy inclusion list frozen and committed',
        'taxonomy inclusion rationales frozen and committed',
        'source manifest frozen and verified',
        'Experiment 9 ontology imported exactly and verified',
        'Experiment 9 JEV questions imported exactly and verified',
        'Experiment 9 transition mapping imported exactly and verified',
        'primary Resolution Event rule frozen (>=3 valid, delta >=1, closing >=1, opening ==0)',
        'blinded validation rule frozen',
        'feasibility floor frozen (>=20 events, >=10 issuers, max issuer share <=0.20)',
        'primary strategy, moneyness, expiry bucket, entry timing, primary horizon frozen',
        'costs, liquidity rule and ordinary-day controls frozen',
        'inference method and sensitivity grid frozen',
        'protocol written and hashed',
        'source enrollment passes the strict 2024-2025 fence and date-only prior fence',
        'blinded measurement validation passes the frozen standard',
        'primary feasibility gate passes',
    ],
    'fail_fast': (
        'Any missing gate raises NotImplementedError/SystemExit without writing an '
        'economic artifact. No price, option, payoff, ordinary-day market record, 2026 '
        'filing or judges artifact may be read before the frozen protocol hash is '
        'committed.'),
}

# ---------------------------------------------------------------------------
# Blinded validation rule (section 12): stratified by tag, dimension, transition,
# issuer; deterministic selection frozen before the run; same frozen standard as Exp9.
# ---------------------------------------------------------------------------
BLINDED_VALIDATION_RULE = (
    'A deterministic stratified blinded packet is frozen BEFORE the independent read. The '
    'selection stratifies globally over every included Massive tag, every one of the six '
    'ontology dimensions, closing transitions, opening transitions, unchanged transitions '
    'and different issuers. Every stratum that exists in the frozen measurement is covered '
    'by the deterministic primary selection; any (event, dimension) stratum it misses is '
    'added by deterministic supplementary pairs chosen in the frozen hash order. The packet '
    'target is at most 60 events. The reviewer sees before evidence, after evidence, the '
    'ontology dimension and the allowed states; the reviewer never sees the JEV answer, JEV '
    'probability, ResolutionDelta, group membership, Massive strategy outcome or market '
    'data. The same frozen validation standard and the exact Experiment 9 aggregate '
    'transition-sign gate, including its zero-sign failure, are used; the gate is neither '
    'tightened nor loosened. A failure returns no_candidate_measurement_failure and stops '
    'before P&L.'
)

# ---------------------------------------------------------------------------
# Frozen machine-readable protocol.
# ---------------------------------------------------------------------------
PROTOCOL = {
    'experiment': EXPERIMENT,
    'version': VERSION,
    'parent_experiment': '9 uncertainty resolution delta',
    'model': MODEL,
    'endpoint': ENDPOINT,
    'window': [START, END],
    'hypothesis': HYPOTHESIS,
    'expansion_thesis': EXPANSION_THESIS,
    'primary_research_question': PRIMARY_RESEARCH_QUESTION,
    'conceptual_change': 'Event population only. The ontology, questions, resolution '
                         'rules, transition mapping and ResolutionDelta are imported '
                         'exactly from Experiment 9.',
    'taxonomy': {
        'included_tags': list(TAXONOMY_TAGS),
        'tag_precedence': list(TAG_PRECEDENCE),
        'original_departure_tag': ORIGINAL_DEPARTURE_TAG,
        'taxonomy_sha256': TAXONOMY_SHA256,
        'no_separate_succession_tag': NO_SEPARATE_SUCCESSION_TAG,
        'primary_rule': 'A tag is eligible only if its Massive definition directly denotes '
                        'a change in executive leadership, executive succession, executive '
                        'appointment, executive departure or interim executive leadership '
                        'for which the Experiment 9 governance-state ontology is '
                        'economically meaningful.',
        'excluded_near_neighbors': {
            tag: NEAR_NEIGHBOR_EXCLUSIONS[tag] for tag in sorted(NEAR_NEIGHBOR_EXCLUSIONS)},
        'multi_tag_resolution': 'An accession tagged under more than one included category '
                                'is counted once under the first tag in tag_precedence; its '
                                'full tag set is retained as all_tags.',
        'appointment_applicability': APPOINTMENT_APPLICABILITY,
    },
    'ontology': {
        'dimensions': [
            {'id': dimension['id'], 'label': dimension['label'],
             'states': dimension['states'], 'question': dimension['question'],
             'state_description': dimension['state_description']}
            for dimension in DIMENSIONS],
        'reused_exactly_from': 'uncertainty_resolution_spec.DIMENSIONS',
        'not_disclosed_addition': NOT_DISCLOSED_ADDITION,
    },
    'questions': {
        'reused_exactly_from': 'uncertainty_resolution_spec',
        'preamble': PREAMBLE,
        'stage_a_template': STAGE_A_QUESTION_TEMPLATE,
        'stage_b_template': STAGE_B_QUESTION_TEMPLATE,
        'disclosure_question': NOUL_QUESTION,
        'dimension_questions': {dimension['id']: stage_a_instruction(dimension)
                                for dimension in DIMENSIONS},
    },
    'resolution_rules': {
        'reused_exactly_from': 'uncertainty_resolution_spec.RESOLUTION_RULES',
        'rules': RESOLUTION_RULES, 'order': RULE_ORDER},
    'transition_mapping': {
        'reused_exactly_from': 'uncertainty_resolution_spec.TRANSITION_TABLE',
        'positive': [list(key) for key in POSITIVE_TRANSITIONS],
        'negative': [list(key) for key in NEGATIVE_TRANSITIONS],
        'unlisted_differing_pair': 'UNKNOWN; the unlisted pair is recorded.',
        'either_side_insufficient_evidence': 'UNKNOWN',
        'either_side_not_disclosed': 'UNKNOWN',
        'either_side_not_applicable': 'UNKNOWN',
        'equal_pair': 0,
        'not_disclosed_rule': NOT_DISCLOSED_TRANSITION_NOTE,
        'weights': 'equal; never fitted to returns',
    },
    'resolution_delta': (
        'ResolutionDelta = sum of the six transition values, counting only dimensions '
        'whose transition is +1, -1 or 0. UNKNOWN dimensions are excluded from the sum. '
        'equal weights, never fitted to returns.'),
    'primary_rule': {
        'name': 'RESOLUTION_EVENT',
        'min_valid_dimensions': PRIMARY_MIN_VALID_DIMENSIONS,
        'min_resolution_delta': PRIMARY_MIN_RESOLUTION_DELTA,
        'min_closing': PRIMARY_MIN_CLOSING,
        'max_opening': PRIMARY_MAX_OPENING,
        'description': PRIMARY_RULE_DESCRIPTION,
        'no_threshold_search': True,
    },
    'information_boundary': {
        'after_state': (
            'the event\'s own current 8-K disclosure package: the original SEC submission '
            'package parsed for the accession with the reused Experiment 7 document '
            'inclusion rule (the single core 8-K, then every non-empty EX-99* exhibit in '
            'ascending sequence, each preceded by a boundary marker), with the frozen '
            'Experiment 7 passage construction applied unchanged and document text never '
            'truncated. Experiment 9\'s recovered packages are reused for its 132 '
            'accessions; new appointment/transition accessions are recovered with the '
            'reused Experiment 3B SEC retrieval and parser. The full original package is '
            'MANDATORY. If it is missing or is not a parsed 8-K package, the event fails '
            'fast with explicit recovery instructions and is never measured from '
            'supporting_text; supporting_text is never a substitute. Missing accessions '
            'are recovered with `uncertainty_resolution_expanded_experiment.py source`; if '
            'recovery still fails they are excluded under the source gate and recorded, '
            'never silently dropped.'),
        'before_state': {
            'class_P': 'every same-issuer prior-filing row with filing_date strictly less '
                       'than T and at or after T minus 365 days whose items_text contains '
                       'Item 5.02; ordered most-recent-first, at most the three most '
                       'recent; passages built with the reused Experiment 7 passage '
                       'construction and prefixed with a boundary marker naming the '
                       'accession and its filing date.',
            'class_C': 'passages of the current filing\'s supporting_text selected by the '
                       'fixed Experiment 9 lexical net; self-reported and flagged.',
            'lexical_net': [cue for cue, _ in CLASS_C_CUES],
        },
        'date_only_source_rule': (
            'Filing metadata supplies a date and no acceptance time. A date-only source is '
            'never presented as precise timestamp evidence. The before-side fence is a '
            'strict date inequality (prior filing_date < event filing_date); a prior '
            'filing on the same date is excluded because date-only evidence cannot '
            'establish that it preceded the event within the day. Effective dates are '
            'never used as announcement dates.'),
        'never_after_timestamp_fence': (
            'No before-side source is ever at or after the event filing date. Class P '
            'requires filing_date strictly less than T and within T minus 365 days. '
            'Class C is from the current filing only. Every passage and boundary marker '
            'carries its own date. A 2026 date is rejected.'),
        'coverage_adequacy': {
            'window_complete': '(T minus 365 days) >= 2024-01-02',
            'prior_retrieved': 'at least one source_filings row exists for the CIK with '
                               'filing_date < T',
            'coverage_adequate': 'window_complete AND prior_retrieved',
            'rule': 'An event whose coverage_adequate is false may still use Class P or '
                    'Class C passages that POSITIVELY establish a state, but absence of '
                    'evidence for such an event never yields not_disclosed; it yields '
                    'insufficient_evidence.',
        },
    },
    'request_ceiling': {
        'ceiling_bytes': REQUEST_MAX_BYTES,
        'trim_rule': 'Trim the OLDEST Class P filings first and record the trim; never '
                     'trim the current filing\'s passages.',
        'oversized_current_package': 'If the current filing\'s own passages cannot fit '
                                     'within the ceiling after all Class P filings are '
                                     'trimmed, the event is recorded as excluded_oversized '
                                     'and is not measured. No semantic design is changed '
                                     'and no current text is silently truncated. Every '
                                     'exclusion is written to exclusions.json with its '
                                     'accession, tag, filing date, before/after ceiling '
                                     'flags and reason, and the audit reports the excluded '
                                     'count and composition as a source-gate impact; no '
                                     'event is silently dropped.',
    },
    'feasibility': {
        'floor': FLOOR,
        'primary_rule': 'valid_transitions >= %d, resolution_delta >= %d, closing >= %d, '
                        'opening == %d' % (PRIMARY_MIN_VALID_DIMENSIONS,
                                           PRIMARY_MIN_RESOLUTION_DELTA,
                                           PRIMARY_MIN_CLOSING, PRIMARY_MAX_OPENING),
        'failure': 'If the primary group fails any floor element, the experiment returns '
                   'no_candidate_feasibility_failure and stops without opening any '
                   'economic outcome.',
    },
    'category_composition': (
        'Before P&L: event count by tag, qualifying Resolution Event count by tag, '
        'issuers by tag, and each tag\'s percentage of the primary group. Flag any tag '
        'contributing more than 60%. Report the original executive_officer_departure '
        'subgroup separately.'),
    'blinded_validation': {
        'rule': BLINDED_VALIDATION_RULE,
        'strata': ['included Massive tag', 'ontology dimension', 'closing transition',
                   'opening transition', 'unchanged transition', 'issuer'],
        'sample_max': 60,
        'supplementary_pairs': 'Deterministic: any (event, dimension) stratum present in '
                               'the frozen measurement but absent from the primary '
                               'selection is added by the frozen hash order.',
        'gate': 'Exact Experiment 9 aggregate transition-sign gate, including its zero-sign '
                'failure; neither tightened nor loosened.',
        'reviewer_sees': ['before evidence', 'after evidence', 'ontology dimension',
                          'allowed states'],
        'reviewer_never_sees': ['JEV answer', 'JEV probability', 'ResolutionDelta',
                                'group membership', 'Massive strategy outcome',
                                'market data'],
        'failure': 'no_candidate_measurement_failure; stop before P&L.',
    },
    'baselines': {
        'A_massive_tag_alone': 'Compare outcomes across the included leadership-transition '
                               'tags without semantic filtering.',
        'B_calendar_freshness': BASELINE_CALENDAR_FRESHNESS,
        'C_original_departures_only': 'Preserve executive_officer_departure as a '
                                      'descriptive subgroup for comparison with Experiment '
                                      '9\'s source population.',
    },
    'mechanism_ordering': MECHANISM_ORDERING,
    'mechanism_groups': list(MECHANISM_GROUPS),
    'mechanism_ordering_expected': list(MECHANISM_ORDERING_EXPECTED),
    'primary_trade_cell': PRIMARY,
    'horizons': HORIZONS,
    'costs': COSTS,
    'liquidity': LIQUIDITY,
    'ordinary_day_controls': ORDINARY_DAY_CONTROL,
    # The primary analysis uses Experiment 9's primary inference exactly (PRIMARY
    # ["inference"], seed 20261009), not the legacy common inference seed 20261007. The
    # legacy object is retained below, clearly labelled secondary, only for provenance.
    'inference': PRIMARY['inference'],
    'legacy_inference_secondary': {
        'inference': INFERENCE,
        'note': 'Secondary reference only. The primary analysis uses '
                'PROTOCOL["inference"] = uncertainty_resolution_spec.PRIMARY["inference"] '
                '(seed ' + str(PRIMARY['inference']['seed']) + ') exactly; this legacy '
                'common inference (seed ' + str(INFERENCE['seed']) + ') is never the '
                'primary interval.',
    },
    'sensitivity': SENSITIVITY,
    'higher_cost_scenario': HIGHER_COST_SCENARIO,
    'success': SUCCESS,
    'failure': [
        'no_candidate_category_coherence_failure', 'no_candidate_source_failure',
        'no_candidate_measurement_failure', 'no_candidate_feasibility_failure',
        'no_candidate_economic_failure', 'no_candidate_incremental_value_failure',
        'no_candidate_integrity_failure'],
    'oos': OOS_LOCK,
    'downstream_gates': DOWNSTREAM_GATES,
    'forbidden': [
        'price, option, payoff or P&L read', 'ordinary-day market read',
        '2026 filing, price or option record', 'judges or sealed artifact',
        'P&L number', 'threshold tuning', 'weakening the 20-event, 10-issuer or 0.20 '
        'issuer-share floor', 'redefining the ontology, questions, resolution rules or '
        'transition mapping', 'monkeypatching Experiment 9 module globals',
        'editing any existing frozen script, protocol, result, report, README or .agents '
        'file', 'commit'],
}


def protocol_sha256():
    return digest(PROTOCOL)
