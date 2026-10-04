"""Experiment 4B: expanded source coverage, unchanged economic hypothesis."""
from copy import deepcopy
from guidance_spec import PROTOCOL as ORIGINAL, MODEL, COMMON, UNCERTAINTY_LEVELS, STRATEGIES
from jev_experiment import digest

START, END = '2024-01-01', '2025-12-31'
TAGS = ['guidance_issuance_or_update', 'guidance_withdrawal',
        'quarterly_earnings', 'annual_earnings', 'preliminary_results']
PROTOCOL = deepcopy(ORIGINAL)
PROTOCOL.update({
    'experiment':'4B_expanded_guidance_uncertainty', 'version':1,
    'parent_protocol_sha256':digest(ORIGINAL),
    'tags':TAGS,
    'design_status':'Exploratory expansion authorized after observing only the parent source coverage failure. No parent semantic or economic results exist. Do not portray this as an independent preregistered confirmation.',
    'universe':'Unchanged original TOP_100 and 2024–2025 options window. The starter explicitly prohibits moving options windows earlier. No 2026 access or universe expansion.',
    'enrollment':'Union the five prespecified tags, deduplicate original accession, and screen every in-universe original filing. Earnings tags widen source acquisition only: a filing must still contain the original full-year bounded EPS/revenue guidance and a comparable prior forecast to enter the semantic cohort. No category performance search or treating all earnings filings as guidance.',
    'preservation':'Protect the completed 60-filing parent audit, all previous experiment artifacts and all source/report code. Separate expanded_guidance_results namespace. Reuse exact immutable successful original packages and identical cached source requests only after checksum verification; record reuse provenance explicitly. Never rewrite or reinterpret the parent gate.',
    'semantic_budget':'At most three ordered requests per potential source event: select current range and metric/unit/year; select latest comparable prior range/unit; verify pair and comparative uncertainty/evidence. Reject malformed successful responses without resampling. Persist exact requests, pinned model, distributions and transport attempts. No sampling for favorable outcomes.',
    'keyword_baseline':'Fixed lexicon, independent of outcomes: improved visibility, greater visibility, increased visibility, improved certainty, more predictable, reduced uncertainty contribute -1 each; limited visibility, reduced visibility, less visibility, uncertainty, uncertain, unpredictable, challenging, contingent, volatility contribute +1 each. Sum substring-presence counts in current minus prior candidate contexts. Generic language remains a baseline only, never a semantic changed-state label.',
    'review_sample':'Before market data, review the first three valid source pairs in each improved/unchanged/deteriorated semantic group, plus the first three rejected pairs, sorted by accession. Verify identity, fiscal horizon, numerical guidance rather than realized earnings, unit and exact evidence. Record discrepancies; do not change thresholds to pass the gate.',
})
